"""
download pdf files from https://www.myharvardclassics.com/categories/20120212
Free Volumes of Harvard Classics
"""

import multiprocessing
import os
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests

BASE_URL = 'https://www.myharvardclassics.com/categories/20120212'


def get_page(url):
    """get page from url with requests and fake user agent"""
    response = requests.get(
        url, headers={'User-Agent': UserAgent().chrome}).content
    return BeautifulSoup(response, 'lxml')


def download_file(url_filename):
    """download file with check for existing file"""
    url, filename = url_filename

    if os.path.exists(filename):
        print(f'File: {filename} already exists. Skipping download.')
        return

    try:
        file_data = requests.get(
            url, headers={'User-Agent': UserAgent().chrome}).content
    except:
        print(f'Warning: Could not download from {url}')
        return

    try:
        with open(filename, 'wb') as handler:
            handler.write(file_data)
    except:
        print(f'Warning: Failed to save file {filename}')
        return


def get_urls_and_names(links):
    """extract URL and filename from links list. Due to 'double' urls organization looks weird"""
    urls = []
    name = ''
    url = ''
    for link in links:
        if 'Volume' in link.text:
            name = link.text
            url = link['href']
        elif '- ' in link.text:
            name += ' ' + link.text + '.pdf'
            urls.append((url, name))
            name, url = '', ''
    return urls


def Run():
    """main block"""
    soup = get_page(BASE_URL)
    links = soup.find_all('a', href=True)
    urls_files = get_urls_and_names(links)
    pool = multiprocessing.Pool(processes=30)
    pool.map(download_file, urls_files)


if __name__ == '__main__':
    Run()
