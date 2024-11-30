"""
Batch download Byte Magazines (1950 - 2020 years) from Vintage Apple Museum
https://vintageapple.org/byte/
"""

import asyncio
import os

import aiofiles
import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://vintageapple.org/byte/"
OUT_DIR = "pdfs"
MAX_CONCURRENT_DOWNLOADS = 20
CHUNK_SIZE = 1024 * 1024


async def download_file(client, url, filename, semaphore):
    async with semaphore:
        print(f"Processing {url}")
        """download file with check for existing file"""
        filename_to_save = os.path.join(OUT_DIR, os.path.basename(filename))
        if os.path.exists(filename_to_save):
            print(f"Skipping already existing file {filename}")
            return

        try:
            async with client.stream("GET", url) as response:
                async with aiofiles.open(filename_to_save, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=CHUNK_SIZE):
                        await f.write(chunk)
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return


def get_page(url):
    response = httpx.get(url).content
    return BeautifulSoup(response, "lxml")


async def flow():
    if not os.path.exists(OUT_DIR):
        os.mkdir(OUT_DIR)

    page = get_page(BASE_URL)
    table = page.find("table", attrs={"class": "border-table"})
    links = table.find_all("a", href=True)
    urls = [
        (BASE_URL + link["href"], link["href"].lstrip("pdf/"))
        for link in links
        if link["href"].endswith(".pdf")
    ]

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

    async with httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(max_keepalive_connections=MAX_CONCURRENT_DOWNLOADS),
    ) as client:
        tasks = [
            download_file(client, url, filename, semaphore) for url, filename in urls
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(flow())
