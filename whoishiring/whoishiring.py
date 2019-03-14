"""
get job listing from "Who is hiring" HN thread

TODO allow to store data of vacancy to make html based on month and year not on entire
    base
TODO remake job_head and job_description - for now it's a mess and generate
    a ton of crazy html-like code with incorrect close/open tags
TODO allow to modify keywords via command line arguments or config file
TODO remake block for making html entries
TODO rewrite API/BS4 block to single function

"""
import argparse
import codecs
import json
import pickle
import re
import sqlite3
import sys

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from tqdm import tqdm


def create_parser():
    """create_parser for argparse

    Returns:
        object: parser
    """

    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "-t", "--thread", action="store", help="Who is hiring thread number"
    )
    argparser.add_argument("-f", "--fast", action="store_true",
                           help="Fast scraping")
    return argparser


def get_item_url(kid_id):
    """
    make url with kid_id
    """
    return f'https://hacker-news.firebaseio.com/v0/item/{kid_id}.json'


def get_comments(kid_id):
    """
    get all comments
    """
    result = requests.get(get_item_url(kid_id)).json()
    return result["text"] if result and "text" in result else ""


def get_thread_name(from_thread_id):
    """
    extract name of the thread + month and year
    """
    story_name = ""
    try:
        story_name = requests.get(get_item_url(from_thread_id)).json()["title"]
    except TypeError:
        print(f"Thread {from_thread_id} non exist.")
        exit()
    month_year = re.findall(r'\(([A-Za-z]+ \d+)\)', story_name)[0].lower()
    short_name = f"whoishiring {month_year}"
    return short_name


def load_from_json(filename):
    """
    load json file from previous session (if exist)
    """
    try:
        with open(f"{filename}.json", "r") as file:
            saved_comments = json.load(file)
    except FileNotFoundError:
        saved_comments = []
    return saved_comments


def save_to_json(comments_to_save, filename):
    """
    save all comment to json file
    """
    with open(f"{filename}.json", "w") as file:
        json.dump(comments_to_save, file)


def get_kids(thread_id_to_get_kids):
    """
    get kids from story thread
    """
    story_kids = requests.get(get_item_url(
        thread_id_to_get_kids)).json()["kids"]
    return story_kids


def get_all_comments_from_thread(thread):
    """get_all_comments_from_thread - scrape page by page if link 'more' is
        available

    Args:
        thread (int): thread_id

    Returns:
        [list of soups]: scraped comments
    """

    url = f"https://news.ycombinator.com/item?id={thread}"
    not_a_last_page = True
    total_entries = []
    while not_a_last_page:
        print(f"Get page {url}")
        soup = get_page(url)
        entries = soup.findAll("div", {"class": "comment"})
        total_entries += entries
        have_more_link = soup.findAll("a", {"class": "morelink"})
        if have_more_link:
            url_tail = have_more_link[0].get("href")
            url = f"https://news.ycombinator.com/{url_tail}"
        else:
            not_a_last_page = False
    return total_entries


def grab_new_comments_html(comments, entrys):
    """grab_new_comments_html Get comments from html scrapes via BeautifulSoup.
                              It's way faster than API, but not very accurate

    Args:
        comments (list): list of old comments from json file
        entrys (list): list of comments from thread
    TODO rewrite db connection
    """
    conn = sqlite3.connect("whoishiring.sqlite")
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS kids(kid INTEGER UNIQE,
                                                 head BLOB,
                                                 description BLOB)"""
    )
    cur.execute("SELECT kid FROM kids")
    try:
        kids_in_base = cur.fetchall()
    except IndexError:
        kids_in_base = []
    stored_kids = list(kid[0] for kid in kids_in_base) if kids_in_base else []

    for entry in entrys:
        try:
            text = entry.findAll('span', {'class': 'commtext'})[0]
        except IndexError:
            continue
        try:
            kid = int(re.findall(r'reply\?id=(\d+)', entry.__str__())[0])
        except IndexError:
            kid = 0
        if kid in stored_kids:
            continue

        try:
            job_head = re.findall(
                r'.+c00">(.+)', text.__str__().split("<p>")[0])[0]
            job_description = "<br><p>".join(text.__str__().split(
                "<p>")[1:]).rstrip("</span>")
        except IndexError:
            continue
        if job_description:
            if 'We detached' in job_description:
                continue
            else:
                comments.append(
                    {"kid": kid,
                     "head": job_head,
                     "description": job_description})
                cur.execute(
                    """INSERT INTO kids
                        (kid, head, description)
                        VALUES (?, ?, ?)""",
                    (kid, job_head, job_description),
                )
                conn.commit()
        else:
            continue
    conn.close()
    return comments


def grab_new_comments(comments, all_kids):
    """
    get saved kid_id from base, get only new id
    """
    conn = sqlite3.connect("whoishiring.sqlite")
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS kids(kid INTEGER UNIQE,
                                                 head BLOB,
                                                 description BLOB)"""
    )
    cur.execute("SELECT kid FROM kids")
    try:
        kids_in_base = cur.fetchall()
    except IndexError:
        kids_in_base = []
    kids_in_base = [kid[0] for kid in kids_in_base]
    kids_to_add = set(all_kids) - set(kids_in_base)

    for kid in tqdm(kids_to_add):
        next_comment = get_comments(kid)
        job_head = ''
        job_description = ''
        if next_comment:
            job_head = next_comment.split("<p>")[0]
            job_description = "<br><p>".join(next_comment.split("<p>")[1:])
            comments.append({"kid": kid,
                             "head": job_head,
                             "description": job_description})
        cur.execute(
            """INSERT INTO kids
                        (kid, head, description)
                        VALUES (?, ?, ?)""",
            (kid, job_head, job_description),
        )
        conn.commit()
    conn.close()
    return comments


def make_html(job_listing, filename):
    """
    create simple html from comments with (and without) keyword
    """
    counter = 0
    with open("template.html", "r") as file:
        template = file.read()
    jobs_block = ''
    for i, entry in enumerate(job_listing, 1):
        entry_text = f"{entry['head']} {entry['description']}"
        if "remote" in entry_text.lower():
            block_start = "<div class='job_entry'>"
            first_line = f"""<div class='job_head'><em># {i}</em>
                             {entry['head']}</div>"""
            jobs_block += f"""{block_start}{first_line}
                              {entry['description']}</a></div>"""
            counter += 1
    with codecs.open(f"{filename}.html", "w", encoding="utf-8") as file:
        file.write(template.format(filename, jobs_block))
    print(f"Written to html: {counter} job postings.")


def write_thread_id(thread_id_to_save):
    """write_thread_id Saves last used thread_id in pickle

    Args:
        thread_id_to_save (int): thread_id to save

    Warning: No check if thread doesn't exist
    TODO make check for thread
    """

    with open("last_thread.pickle", "wb") as pickle_out:
        pickle.dump(thread_id_to_save, pickle_out)


def get_page(url):
    """get_page get page via requests and throw it to beautiful soup

    Args:
        url (string): address

    Returns:
        [soup]: beautiful soup object
    """

    response = requests.get(
        url, headers={"User-Agent": UserAgent().chrome}).content
    soup = BeautifulSoup(response, "lxml")
    return soup


def scrape(thread):
    """
    main block for getting data with BeautifulSoup and a little bit of API ;)
    """
    name = get_thread_name(thread)
    entries = get_all_comments_from_thread(thread)
    print(f'In thread {thread} with name "{name}" are {len(entries)} records')
    comments = load_from_json(name)
    new_comments = grab_new_comments_html(comments, entries)
    make_html(new_comments, name)
    save_to_json(new_comments, name)


def run(thread):
    """
    main block for getting data with API
    """
    name = get_thread_name(thread)
    old_comments = load_from_json(name)
    kids = get_kids(thread)
    print(f'In thread {thread} with name "{name}" are {len(kids)} records')
    new_comments = grab_new_comments(old_comments, kids)
    make_html(new_comments, name)
    save_to_json(new_comments, name)


if __name__ == "__main__":
    PARSER = create_parser()
    ARGS = PARSER.parse_args(sys.argv[1:])

    if not ARGS.thread:
        try:
            # get last used thread_id
            with open("last_thread.pickle", "rb") as pickle_in:
                THREAD_ID = pickle.load(pickle_in)
        except FileNotFoundError:
            sys.exit(f"Syntax: {sys.argv[0]} -t <thread_id>")
    else:
        THREAD_ID = ARGS.thread

    write_thread_id(THREAD_ID)

    if ARGS.fast:
        scrape(THREAD_ID)
    else:
        run(THREAD_ID)
