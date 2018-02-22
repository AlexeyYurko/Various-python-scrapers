"""
grab list of articles, articles itself and images from filfre.net
using MongoDB
"""
import pickle
import os
import sys
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
from pymongo import MongoClient

CLIENT = MongoClient()
DB = CLIENT['filfre']
URL = 'http://www.filfre.net/sitemap/'


def get_articles(folder):
    collection = DB['articles']

    try:
        pickle_in = open("image_count.pickle", "rb")
        image_count = pickle.load(pickle_in)
    except FileNotFoundError:
        image_count = 0

    page = urlopen(URL)
    articles = BeautifulSoup(page, 'lxml').find(
        'div', {'id': 'wp-realtime-sitemap-posts'})
    links = articles.findAll('a')

    for link in links:
        article = link.text
        if collection.find_one({'article': article}) is None:
            article_url = link.get('href')
            print('Article "{}", link {}'.format(article, article_url))
            article_page = urlopen(article_url)
            print('Loaded article "{}"'.format(article))
            article_raw = BeautifulSoup(article_page, 'lxml').find(
                'div', {'class': 'entry'})
            article_text = article_raw.text.strip()
            inside_article_urls = article_raw.findAll('a')
            article_links = []
            images_links = []
            for inside_article_url in inside_article_urls:
                inside_url = inside_article_url.get('href')
                images = inside_article_url.find('img')
                if images:
                    image_data = requests.get(inside_url).content
                    image_name = '{}/{}_{}'.format(folder,
                                                   str(image_count).zfill(4),
                                                   inside_url.split('/')[-1])

                    # check for link to page, not the image itself
                    if image_name.endswith('_'):
                        page = urlopen(inside_url)
                        image_url = BeautifulSoup(page, 'lxml').find(
                            'p', {'class': 'attachment'}).find('img')['src']
                        image_name = image_name + image_url.split('/')[-1]
                        image_data = requests.get(image_url).content
                    image_count += 1
                    with open(image_name, 'wb') as handler:
                        handler.write(image_data)
                    images_links.append(
                        {'image_name_local': image_name, 'image_url': inside_url,
                         'image_text': inside_article_url.text})
                else:
                    article_links.append({'inside_url': inside_url,
                                          'inside_text': inside_article_url.text})
            post = {
                'article': article,
                'url': article_url,
                'text': article_text,
                'links': article_links,
                'images': images_links
            }
            collection.save(post)
            pickle_out = open("image_count.pickle", "wb")
            pickle.dump(image_count, pickle_out)
            pickle_out.close()
    return


def run():
    """main functinon"""
    if len(sys.argv) != 2:
        print('Syntax: %s <folder>' % sys.argv[0])
        sys.exit(0)

    to_folder = sys.argv[1]

    if not os.path.exists(to_folder):
        os.mkdir(to_folder)

    get_articles(to_folder)


if __name__ == '__main__':
    run()
