"""
Batch download MagPi Magazine
Issue from 1 to 68 for May 30, 2018
https://www.raspberrypi.org/magpi-issues/MagPi68.pdf
"""

import asyncio
import os
import sys

import aiofiles
import httpx
from fake_useragent import UserAgent

BASE_URL = "https://magpi.raspberrypi.com/issues/"
CHUNK_SIZE = 1024 * 1024


async def download_file(client, issue_no):
    url = "{}{:03}/pdf/download".format(BASE_URL, issue_no)
    filename = "MagPi{:03}.pdf".format(issue_no)
    headers = {"User-Agent": UserAgent().chrome}
    if os.path.exists(filename):
        print(f"File {filename} already exists. Skipping download.")
        return

    try:
        print(f"Downloading {filename}")
        html_content = (await client.get(url, headers=headers)).content
        iframe_start = html_content.find(b'<iframe src="') + len(b'<iframe src="')
        iframe_end = html_content.find(b'"', iframe_start)
        iframe_src = html_content[iframe_start:iframe_end].decode("utf-8")

        pdf_url = f"https://magpi.raspberrypi.com{iframe_src}"
        file_url = (await client.get(pdf_url, headers=headers)).headers["location"]

        async with client.stream("GET", file_url, headers=headers) as response:
            async with aiofiles.open(filename, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=CHUNK_SIZE):
                    await f.write(chunk)

    except Exception as e:
        print(f"Warning: Could not process from {url}: {e}")
        return


async def flow():
    min_issue_number = 1
    if len(sys.argv) == 1:
        max_issue_number = 147  # for 01/12/2024
    elif len(sys.argv) == 2:
        max_issue_number = int(sys.argv[1])
    else:
        min_issue_number = int(sys.argv[1])
        max_issue_number = int(sys.argv[2])

    async with httpx.AsyncClient() as client:
        tasks = []
        for issue_no in range(min_issue_number, max_issue_number + 1):
            tasks.append(download_file(client, issue_no))
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(flow())
