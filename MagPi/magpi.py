"""
Batch download MagPi Magazine
Issue from 1 to 147 for Dec 01 2024
https://www.raspberrypi.org/magpi-issues/MagPi68.pdf
"""

import asyncio
import os
from pathlib import Path
import sys

import aiofiles
import httpx
from fake_useragent import UserAgent

BASE_URL = "https://magpi.raspberrypi.com/issues/"
CHUNK_SIZE = 1024 * 1024
MAX_CONCURRENT_DOWNLOADS = 10

TOO_MANY_REQUESTS = 429


async def download_file(client, semaphore, issue_no):
    async with semaphore:
        url = "{}{:03}/pdf/download".format(BASE_URL, issue_no)
        filename = Path("MagPi{:03}.pdf".format(issue_no))
        headers = {"User-Agent": UserAgent().chrome}
        if filename.exists():
            print(f"File {filename} already exists. Skipping download.")
            return

        max_retries = 5
        retry_delay = 15

        for attempt in range(max_retries):
            try:
                print(f"Downloading {filename}")
                response = await client.get(url, headers=headers)

                if response.status_code == TOO_MANY_REQUESTS:
                    wait_time = int(response.headers.get("Retry-After", retry_delay))
                    print(
                        f"{url} Rate limited. Waiting {wait_time} seconds before retry..."
                    )
                    await asyncio.sleep(wait_time)
                    continue

                html_content = response.content
                iframe_start = html_content.find(b'<iframe src="') + len(
                    b'<iframe src="'
                )
                iframe_end = html_content.find(b'"', iframe_start)
                iframe_src = html_content[iframe_start:iframe_end].decode("utf-8")

                pdf_url = f"https://magpi.raspberrypi.com{iframe_src}"
                pdf_response = await client.get(pdf_url, headers=headers)

                if pdf_response.status_code == TOO_MANY_REQUESTS:
                    wait_time = int(
                        pdf_response.headers.get("Retry-After", retry_delay)
                    )
                    print(
                        f"{pdf_url} Rate limited. Waiting {wait_time} seconds before retry..."
                    )
                    await asyncio.sleep(wait_time)
                    continue

                file_url = pdf_response.headers["location"]

                async with client.stream("GET", file_url, headers=headers) as response:
                    if response.status_code == TOO_MANY_REQUESTS:
                        wait_time = int(
                            response.headers.get("Retry-After", retry_delay)
                        )
                        print(
                            f"Rate limited. Waiting {wait_time} seconds before retry..."
                        )
                        await asyncio.sleep(wait_time)
                        continue

                    async with aiofiles.open(filename, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=CHUNK_SIZE):
                            await f.write(chunk)
                break

            except Exception as e:
                print(f"Attempt {attempt + 1}/{max_retries} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
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

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
    async with httpx.AsyncClient() as client:
        tasks = []
        for issue_no in range(min_issue_number, max_issue_number + 1):
            tasks.append(download_file(client, semaphore, issue_no))
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(flow())
