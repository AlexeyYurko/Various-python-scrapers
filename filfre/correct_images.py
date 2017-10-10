"""
here we trying to correct images linked as pages not files
"""

from pymongo import MongoClient
from bs4 import BeautifulSoup
import requests

client = MongoClient()
db = client['filfre']
collection = db['articles']

for entry in collection.find():
    for image in entry['images']:
        image_name_local = image['image_name_local']
        if image_name_local.endswith('_'):
            with open(image_name_local) as f:
                page = f.read()
            image_url = BeautifulSoup(page, 'lxml').find('p', {'class': 'attachment'}).find('img')['src']
            image_name = image_name_local + image_url.split('/')[-1]
            image_data = requests.get(image_url).content
            with open(image_name, 'wb') as handler:
                    handler.write(image_data)
