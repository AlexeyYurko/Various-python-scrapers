"""
Batch download Ikea Catalogues (1950 - 2020 years) from Ikea Museum
https://ikeamuseum.com/sv/ikea-kataloger/
"""

import asyncio
import os
import re

import aiofiles
import httpx
from fake_useragent import UserAgent

BASE_URL = "https://ikeacatalogues.ikea.com/sv-{}/page/1"
BASE_NAME = "IKEA {}.pdf"
OUT_DIR = "pdfs"
YEAR_START = 1950
YEAR_END = 2022
CHUNK_SIZE = 1024 * 1024
MAX_CONCURRENT_DOWNLOADS = 20


async def download_file(client, url, filename, semaphore):
    async with semaphore:

        print(f"Processing {url}")
        filename_to_save = os.path.join(OUT_DIR, os.path.basename(filename))

        if os.path.exists(filename_to_save):
            return
        headers = {"User-Agent": UserAgent().chrome}
        try:
            response = (await client.get(url, headers=headers)).text
            pdf_url = re.findall(r'"downloadPdfUrl":"(.+.pdf)"', response)[0]

            async with client.stream("GET", pdf_url) as response:
                async with aiofiles.open(filename_to_save, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=CHUNK_SIZE):
                        await f.write(chunk)
        except Exception as e:
            print(f"Error while processing {url} {e}")
            return


async def flow():
    if not os.path.exists(OUT_DIR):
        os.mkdir(OUT_DIR)

    url_filenames = [
        (BASE_URL.format(year), BASE_NAME.format(year))
        for year in range(YEAR_START, YEAR_END + 1)
    ]

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

    async with httpx.AsyncClient() as client:
        tasks = [
            download_file(client, url, filename, semaphore)
            for url, filename in url_filenames
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(flow())
