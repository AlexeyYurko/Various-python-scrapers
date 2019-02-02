"""
get job listing from "Who is hiring" HN thread
"""
import codecs
import json
import pickle
import re
import sqlite3
import sys

import requests
from tqdm import tqdm


def get_item_url(kid_id):
    """
    make url with kid_id
    """
    return 'https://hacker-news.firebaseio.com/v0/item/{}.json'.format(str(kid_id))


def get_comments(kid_id):
    """
    get all comments
    """
    result = requests.get(get_item_url(kid_id)).json()
    return result['text'] if result and 'text' in result else ''


def get_thread_name(from_thread_id):
    """
    extract name of the thread + month and year
    """
    story_name = ''
    try:
        story_name = requests.get(get_item_url(from_thread_id)).json()['title']
    except TypeError:
        print(f'Thread {from_thread_id} non exist.')
        exit()
    month_year = re.findall(r'\(([A-Za-z]+ \d+)\)', story_name)[0].lower()
    short_name = f'whoishiring {month_year}'
    return short_name


def load_from_json(filename):
    """
    load json file from previous session (if exist)
    """
    try:
        with open(f'{filename}.json', "r") as file:
            saved_comments = json.load(file)
    except FileNotFoundError:
        saved_comments = []
    return saved_comments


def get_kids(thread_id_to_get_kids):
    """
    get kids from story thread
    """
    story_kids = requests.get(get_item_url(thread_id_to_get_kids)).json()['kids']
    return story_kids


def grab_new_comments(comments, all_kids):
    """
    get saved kid_id from base, get only new id
    """
    conn = sqlite3.connect('whoishiring.sqlite')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS kids(kid INTEGER UNIQE,
                                                 head BLOB,
                                                 description BLOB)''')
    cur.execute('SELECT kid FROM kids')
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
            job_head = next_comment.split('<p>')[0]
            job_description = '<br>'.join(next_comment.split('<p>')[1:])
            comments.append({'head': job_head, 'description': job_description})
        cur.execute('''INSERT INTO kids
                        (kid, head, description)
                        VALUES (?, ?, ?)''',
                    (kid, job_head, job_description,))
        conn.commit()
    conn.close()
    return comments


def make_html(job_listing, filename):
    """
    create simple html from comments with (and without) keyword
    TODO:
    - allow to modify keywords via command line arguments or config file
    - remake block for making html entries
    """
    counter = 0
    with open('template.html', 'r') as file:
        template = file.read()
    jobs_block = ''
    for i, entry in enumerate(job_listing, 1):
        entry_text = f"{entry['head']} {entry['description']}"
        if 'remote' in entry_text or 'REMOTE' in entry_text:
            block_start = "<div class='job_entry'>"
            first_line = f"<div class='job_head'><em>#{i}</em> {entry['head']}</div>"
            jobs_block += f"{block_start}{first_line}{entry['description']}</div>"
            counter += 1
    with codecs.open(f'{filename}.html', "w", encoding="utf-8") as file:
        file.write(template.format(filename, jobs_block))
    print(f'Written to html: {counter} job postings.')


def save_to_json(comments_to_save, filename):
    """
    save all comment to json file
    """
    with open(f'{filename}.json', "w") as file:
        json.dump(comments_to_save, file)


def write_thread_id(thread_id_to_save):
    with open('last_thread.pickle', 'wb') as pickle_out:
        pickle.dump(thread_id_to_save, pickle_out)


def run(thread):
    """
    main block
    """
    write_thread_id(thread)
    name = get_thread_name(thread)
    old_comments = load_from_json(name)
    kids = get_kids(thread)
    print(f'In thread {thread_id} by name "{name}" are {len(kids)} records')
    new_comments = grab_new_comments(old_comments, kids)
    make_html(new_comments, name)
    save_to_json(new_comments, name)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        try:
            # get last used thread_id
            with open('last_thread.pickle', 'rb') as pickle_in:
                thread_id = pickle.load(pickle_in)
        except FileNotFoundError:
            sys.exit(f'Syntax: {sys.argv[0]} <thread_id>')
    else:
        thread_id = sys.argv[1]
    run(thread_id)
