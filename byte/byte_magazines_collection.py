"""
Batch download Byte Magazines (1950 - 2020 years) from Vintage Apple Museum
https://vintageapple.org/byte/
"""

import os
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup

import requests

from tqdm import tqdm

BASE_URL = "https://vintageapple.org/byte/"
OUT_DIR = "pdfs"


def download_file(urls_filename):
    """download file with check for existing file"""
    url, filename = urls_filename
    filename_to_save = os.path.join(OUT_DIR, os.path.basename(filename))
    if os.path.exists(filename_to_save):
        return

    try:
        file_data = requests.get(url).content
    except Exception:
        return

    try:
        with open(filename_to_save, "wb") as handler:
            handler.write(file_data)
    except FileExistsError:
        return


def get_page(url):
    response = requests.get(url).content
    return BeautifulSoup(response, "lxml")


def run():
    """main function"""
    if not os.path.exists(OUT_DIR):
        os.mkdir(OUT_DIR)

    page = get_page(BASE_URL)
    table = page.find("table", attrs={"class": "border-table"})
    links = table.find_all("a", href=True)
    urls = [
        (BASE_URL + (link["href"]), link["href"].lstrip("pdf/"))
        for link in links
        if link["href"].endswith(".pdf")
    ]

    with ThreadPoolExecutor() as executor:
        _ = list(tqdm(executor.map(download_file, urls), total=len(urls)))


if __name__ == "__main__":
    run()
