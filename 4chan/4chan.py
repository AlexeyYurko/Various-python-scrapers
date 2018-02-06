import sys
import os
import multiprocessing
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests

BASE_URL = 'https://boards.4chan.org/'


def download_image(url):
    out_dir = sys.argv[1]
    filename = os.path.join(out_dir, os.path.basename(url))

    if os.path.exists(filename):
        print('Image %s already exists. Skipping download.' % filename)
        return

    try:
        image_data = requests.get(
            url, headers={'User-Agent': UserAgent().chrome}).content
    except:
        print('Warning: Could not download from %s' % url)
        return

    try:
        with open(filename, 'wb') as handler:
            handler.write(image_data)
    except:
        print('Warning: Failed to save image %s' % filename)
        return


def parse_boards(board):
    urls = []
    for page in range(1, 2):
        page_number = '/' + str(page) if page > 1 else ''
        url = (BASE_URL + board + page_number)
        print('Extracting images URL from %s' % url)
        response = requests.get(
            url, headers={'User-Agent': UserAgent().chrome}).content
        soup = BeautifulSoup(response, 'lxml')
        links = soup.find_all('a', target="_blank", href=True)
        for link in links:
            address = link['href'][2:]
            if address.startswith('i.4cdn.org'):
                urls.append('http://%s' % address)

        # going through threads
        threads = soup.find_all('a', string='View Thread')
        if threads:
            for thread in threads:
                thread_url = (BASE_URL + board + page_number +
                              '/' + thread['href'])
                response = requests.get(
                    thread_url, headers={'User-Agent': UserAgent().chrome}).content
                soup = BeautifulSoup(response, 'lxml')
                links = soup.find_all('a', target="_blank", href=True)
                for link in links:
                    address = link['href'][2:]
                    if address.startswith('i.4cdn.org'):
                        urls.append('http://%s' % address)
    return set(urls)


def Run():
    if len(sys.argv) != 2:
        print('Syntax: %s <board>' % sys.argv[0])
        sys.exit(0)

    board = sys.argv[1]

    if not os.path.exists(board):
        os.mkdir(board)

    images_list = parse_boards(board)
    pool = multiprocessing.Pool(processes=50)
    pool.map(download_image, images_list)


if __name__ == '__main__':
    Run()
