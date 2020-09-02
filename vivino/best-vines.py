"""
JSON fields
Name of wine:   vintage.name
Image of wine:  vintage.image.variations.bottle_large
Winery:         vintage.wine.winery.name
Wine Style:     wineStyleName
Country:        vintage.wine.region.country.name
                vintage.wine.region.country.native_name
Region:         vintage.wine.region.name
Year:           vintage.year
Rating:         vintage.statistics.ratings_average
"""


import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import json
import re
from pandas.io.json import json_normalize
from pprint import pprint


url_white = 'https://www.vivino.com/awards/toplists/wine_style_awards_2019_top_white'
url_red = 'https://www.vivino.com/awards/toplists/wine_style_awards_2019_top_red'
list_urls = {'Red': url_red, 'White': url_white}


def get_page(url):
    response = requests.get(
        url, headers={"User-Agent": UserAgent().chrome}).content
    soup = BeautifulSoup(response, "lxml")
    return soup


def run():
    for wine_type, url in list_urls.items():
        soup = get_page(url)
        script = soup.findAll('script')[12]
        wines = re.findall(
            r'window.__PRELOADED_STATE__.items = (\[.+\]);', script.text)[0]
        listing = json.loads(wines)
        with open(f"{url.replace('/', '')}.json", 'w') as file:
            json.dump(listing, file)
        print(wine_type)
        fd = json_normalize(listing)
        pprint(fd)
        # add column in pandas
        for i, item in enumerate(listing, 1):
            name_of_wine = item['vintage']['name']
            image_of_wine = item['vintage']['image']['variations']['bottle_large']
            winery = item['vintage']['wine']['winery']['name']
            wine_style = item['wineStyleName']
            country = item['vintage']['wine']['region']['country']['name']
            country_native = item['vintage']['wine']['region']['country']['native_name']
            region = item['vintage']['wine']['region']['name']
            year = item['vintage']['year']
            rating = item['vintage']['statistics']['ratings_average']
            print(wine_type, i, name_of_wine, rating)
            #df = json_normalize(item)
            # print(df)


if __name__ == "__main__":
    run()
