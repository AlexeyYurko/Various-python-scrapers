"""
get job listing from "Who is hiring" HN topic
"""
import json
import codecs
import requests
from tqdm import tqdm


def getItemUrl(id):
    """get storyID aka kids"""
    return 'https://hacker-news.firebaseio.com/v0/item/{}.json'.format(str(id))


def getComments(storyID):
    """get all comments"""
    story = requests.get(getItemUrl(storyID)).json()
    comments = [requests.get(getItemUrl(c)).json()
                for c in tqdm(story['kids'])]
    return comments


storyID = 16967543
comments = getComments(storyID)

with open("who-is-hiring-may-2018.json", "w") as f:
    json.dump(comments, f)

remotes = [c for c in comments if c and 'text' in c and 'REMOTE' in c['text']
           and 'crypto' not in c['text']]

with codecs.open("may-2018.html", "w", encoding="utf-8") as f:
    for c in remotes:
        f.write(c['text'])
        f.write('<hr/>')
