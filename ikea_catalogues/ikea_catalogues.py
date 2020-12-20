"""
Batch download Ikea Catalogues (1950 - 2020 years) from Ikea Museum
https://ikeamuseum.com/sv/ikea-kataloger/
"""

import os
import re
from concurrent.futures import ThreadPoolExecutor

import requests
from fake_useragent import UserAgent
from tqdm import tqdm

BASE_URL = 'https://ikeacatalogues.ikea.com/sv-{}/page/1'
BASE_NAME = 'IKEA {}.pdf'
OUT_DIR = 'pdfs'
YEAR_START = 1950
YEAR_END = 2021


def get_page(url):
    """get page from url with requests and fake user agent"""
    response = requests.get(
        url, headers={'User-Agent': UserAgent().chrome}).text
    return re.findall(r'"downloadPdfUrl":"(.+.pdf)"', response)[0]


def download_file(urls_filename):
    """download file with check for existing file"""
    url, filename = urls_filename
    filename_to_save = os.path.join(
        OUT_DIR, os.path.basename(filename))

    if os.path.exists(filename_to_save):
        return

    try:
        pdf_url = get_page(url)
        file_data = requests.get(
            pdf_url, headers={'User-Agent': UserAgent().chrome}).content
    except:
        return

    try:
        with open(filename_to_save, 'wb') as handler:
            handler.write(file_data)
    except FileExistsError:
        return


def run():
    """main function"""
    if not os.path.exists(OUT_DIR):
        os.mkdir(OUT_DIR)

    pages = [(BASE_URL.format(year), BASE_NAME.format(year))
             for year in range(YEAR_START, YEAR_END + 1)]

    with ThreadPoolExecutor() as executor:
        _ = list(tqdm(executor.map(download_file, pages), total=len(pages)))


if __name__ == '__main__':
    run()
