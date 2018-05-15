"""
get job listing from "Who is hiring" HN thread
"""
import json
import codecs
import requests
from tqdm import tqdm


def get_item_url(kid_id):
    """get storyID aka kids
    :param kid_id: int, thread/comment id
    :return: dict
    """
    return 'https://hacker-news.firebaseio.com/v0/item/{}.json'.format(str(kid_id))


def get_comments(story_id):
    """get all comments
    :param story_id: int, main thread id
    :return: list of dicts
    """
    story = requests.get(get_item_url(story_id)).json()
    results = [requests.get(get_item_url(c)).json()
               for c in tqdm(story['kids'])]
    return results


thread_id = 16967543
comments = get_comments(thread_id)

with open("who-is-hiring-may-2018.json", "w") as f:
    json.dump(comments, f)

remotes = [c for c in comments if c and 'text' in c and 'REMOTE' in c['text']
           and 'crypto' not in c['text']]

with codecs.open("may-2018.html", "w", encoding="utf-8") as f:
    for c in remotes:
        f.write(c['text'])
        f.write('<hr/>')
