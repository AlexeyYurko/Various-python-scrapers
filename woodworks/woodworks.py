"""
Batch download all pdf from woodworks library
http://www.evenfallstudios.com/woodworks_library/woodworks_library.html
"""

import multiprocessing
import os
import re

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

BASE_URL = 'http://www.evenfallstudios.com/woodworks_library/woodworks_library.html'
OUT_DIR = 'pdfs'


def get_page(url):
    """get page from url with requests and fake user agent"""
    response = requests.get(
        url, headers={'User-Agent': UserAgent().chrome}).content
    return BeautifulSoup(response, 'lxml')


def download_file(urls_filename):
    """download file with check for existing file"""
    url, filename = urls_filename
    filename_to_save = os.path.join(
        OUT_DIR, os.path.basename(f'{filename}.pdf'))

    if os.path.exists(filename_to_save):
        print(f'File {filename_to_save} already exists. Skipping download.')
        return

    try:
        print(f'Downloading {filename}')
        file_data = requests.get(
            url, headers={'User-Agent': UserAgent().chrome}).content
    except:
        print(f'Warning: Could not download from {url}')
        return

    try:
        with open(filename_to_save, 'wb') as handler:
            handler.write(file_data)
    except FileExistsError:
        print(f'Warning: Failed to save file {filename_to_save}')
        return


def get_urls_and_names(links):
    """extract URL and filename from links list"""
    urls = []
    for link in links:
        if 'pdf' in link.text:
            line = str(link).replace('<br/>', ' ').replace(' pdf', '')
            name = re.findall(r'>(.+)<', line)[0]
            url = link['href']
            urls.append((url, name))
    return urls


def run():
    """main function"""
    page = get_page(BASE_URL)
    links = page.find_all('a', href=True)
    urls_files = get_urls_and_names(links)
    if not os.path.exists(OUT_DIR):
        os.mkdir(OUT_DIR)

    pool = multiprocessing.Pool(processes=30)
    pool.map(download_file, urls_files)


if __name__ == '__main__':
    run()
