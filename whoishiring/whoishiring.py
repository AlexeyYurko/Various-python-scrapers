"""
get job listing from "Who is hiring" HN thread
may 2018 - 16967543
"""
import json
import codecs
import re
import sys
import sqlite3
import requests
from tqdm import tqdm


def get_item_url(kid_id):
    """get storyID aka kids
    :param kid_id: int, thread/comment id
    :return: dict
    """
    return 'https://hacker-news.firebaseio.com/v0/item/{}.json'.format(str(kid_id))


def get_comments(kid_id):
    """get all comments
    :param story_id: int, main thread id
    :return: dict
    """
    result = requests.get(get_item_url(kid_id)).json()
    return result['text'] if 'text' in result else ''


def get_thread_name(thread_id):
    """
    extract name of the thread + month and year
    """
    story_name = requests.get(get_item_url(thread_id)).json()['title']
    month_year = re.findall(r'\(([A-Za-z]+ \d+)\)', story_name)[0].lower()
    short_name = 'whoishiring {}'.format(month_year)
    return short_name


def get_kids(thread_id):
    """
    get kids from story thread
    """
    story_kids = requests.get(get_item_url(thread_id)).json()['kids']
    return story_kids


def make_html(job_listing, filename):
    """
    create simple html from comments with (and without) keyword
    """
    remotes = [c for c in job_listing if c and ('REMOTE' in c or 'remote' in c)
               and 'crypto' not in c]

    with codecs.open(f'{filename}.html', "w", encoding="utf-8") as f:
        f.write('<meta charset="utf-8">')
        for c in remotes:
            f.write(c)
            f.write('<hr>')
    return


def load_from_json(filename):
    """
    load json file from previous session (if exist)
    """
    try:
        with open(f'{filename}.json', "r") as f:
            saved_comments = json.load(f)
    except FileNotFoundError:
        saved_comments = []
    return saved_comments


def save_to_json(comments_to_save, filename):
    """
    save all comment to json file
    """
    with open(f'{filename}.json', "w") as f:
        json.dump(comments_to_save, f)
    return


def grab_new_comments(comments, all_kids):
    """
    get saved kid_id from base, get only new id
    """
    conn = sqlite3.connect('whoishiring.sqlite')
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS kids (kid INTEGER UNIQE)''')
    cur.execute("SELECT kid FROM kids")
    try:
        kids_in_base = cur.fetchall()
    except IndexError:
        kids_in_base = []
    kids_in_base = [kid[0] for kid in kids_in_base]
    kids_to_add = [kid for kid in all_kids if kid not in kids_in_base]

    for kid in tqdm(kids_to_add):
        comments.append(get_comments(kid))
        cur.execute('''INSERT INTO kids (kid) VALUES (?)''',
                    (kid, ))
        conn.commit()
    conn.close()
    return comments


def run():
    """
    main functinon
    """
    thread_id = sys.argv[1]
    name = get_thread_name(thread_id)
    old_comments = load_from_json(name)
    kids = get_kids(thread_id)
    new_comments = grab_new_comments(old_comments, kids)
    make_html(new_comments, name)
    save_to_json(new_comments, name)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Syntax: {} <thread_id>'.format(sys.argv[0]))
        sys.exit(0)
    run()
