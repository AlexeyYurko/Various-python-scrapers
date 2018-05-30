"""
Batch download MagPi Magazine
Issue from 1 to 68 for May 30, 2018
https://www.raspberrypi.org/magpi-issues/MagPi68.pdf
"""

import multiprocessing
import os
import sys
from fake_useragent import UserAgent
import requests

BASE_URL = 'https://www.raspberrypi.org/magpi-issues/MagPi'


def download_file(urls_filename):
    """download file with check for existing file"""
    url, filename = urls_filename

    if os.path.exists(filename):
        print(f'File {filename} already exists. Skipping download.')
        return

    try:
        print(f'Downloading {filename}')
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


def Run():
    """main function"""
    if len(sys.argv) == 1:
        max_issue_number = 68  # for 05/30/2018
    else:
        max_issue_number = int(sys.argv[1])

    urls_for_download = [('{}{:02}.pdf'.format(
        BASE_URL, x), 'MagPi{:02}.pdf'.format(x)) for x in range(1, max_issue_number + 1)]
    pool = multiprocessing.Pool(processes=30)
    pool.map(download_file, urls_for_download)


if __name__ == '__main__':
    Run()
