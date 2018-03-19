"""
grab list of articles, articles itself and images from filfre.net
using MongoDB

TODO: rewrite code to more readable
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


def image_load(image_url, image_name, image_text):
    image_data = requests.get(image_url).content
    print(
        '\tSaving image:\n\t{},\n\tas {}\n\twith caption "{}"'.format(
            image_url, image_name, image_text
        )
    )
    with open(image_name, 'wb') as handler:
        handler.write(image_data)
    return


def check_for_page(folder, counter, image_url):
    image_name = '{}/{}_{}'.format(
        folder, str(counter).zfill(5), image_url.split('/')[-1]
    )
    if image_name.endswith('_'):
        page = urlopen(image_url)
        image_url = BeautifulSoup(page, 'lxml').find('p', {'class': 'attachment'}).find(
            'img'
        )[
            'src'
        ]
        image_name = image_name + image_url.split('/')[-1]
    return image_name, image_url


def get_articles(folder):
    collection = DB['articles']
    try:
        pickle_in = open("image_count.pickle", "rb")
        image_count = pickle.load(pickle_in)
    except FileNotFoundError:
        image_count = 0
    page = urlopen(URL)
    articles = BeautifulSoup(page, 'lxml').find(
        'div', {'id': 'wp-realtime-sitemap-posts'}
    )
    links = articles.findAll('a')
    for link in links:
        article = link.text
        if collection.find_one({'article': article}) is None:
            article_url = link.get('href')
            print('Article "{}", link {}'.format(article, article_url))
            article_page = urlopen(article_url)
            article_raw = BeautifulSoup(article_page, 'lxml').find(
                'div', {'class': 'entry'}
            )
            article_text = article_raw.text.strip()
            inside_article_urls = article_raw.findAll('a')
            article_links = []
            images_links = []
            passed = []
            # search for images
            article_images = article_raw.findAll(
                'div', {'class': 'wp-caption aligncenter'}
            )
            for image in article_images:
                image_url = image.find('a').get('href')
                try:
                    image_text = image.find('p', {'class': 'wp-caption-text'}).text
                except:
                    image_text = ''
                passed.append(image_url)
                # check for link to page, not the image itself
                image_name, image_url = check_for_page(folder, image_count, image_url)
                image_count += 1
                image_load(image_url, image_name, image_text)
                images_links.append(
                    {
                        'image_name_local': image_name,
                        'image_url': image_url,
                        'image_text': image_text,
                    }
                )
            # search for links
            for inside_url in inside_article_urls:
                # and for images when images not in div block
                image = inside_url.find('img')
                if image:
                    image_text = inside_url.find('img').get('title')
                    if not image_text:
                        image_text = inside_url.find('img').get('alt')
                    image_url = inside_url.get('href')
                    if image_url in passed:
                        break

                    image_name, image_url = check_for_page(
                        folder, image_count, image_url
                    )
                    image_count += 1
                    image_load(image_url, image_name, image_text)
                    images_links.append(
                        {
                            'image_name_local': image_name,
                            'image_url': image_url,
                            'image_text': image_text,
                        }
                    )
                else:
                    article_links.append(
                        {
                            'inside_url': inside_url.get('href'),
                            'inside_text': inside_url.text,
                        }
                    )
            post = {
                'article': article,
                'url': article_url,
                'text': article_text,
                'links': article_links,
                'images': images_links,
            }
            collection.save(post)
            pickle_out = open("image_count.pickle", "wb")
            pickle.dump(image_count, pickle_out)
            pickle_out.close()
            print('Loaded and saved article "{}"\n'.format(article))
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
