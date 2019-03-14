# Python script to extracting job listing from "Who is hiring" HN thread

## Usage

whoishiring.py -t thread_id -f

-t for thread_id. If empty - used last saved thread number.

-f for "fast" scrape with Beautiful Soup (with a little API usage).
Recommended in case then you start following thread with vacancies after
some days.

By default scrape goes through API.

## TODO

- DONE argument parsing;
- DONE sqlite integration;
- DONE intermediate recording of vacancy texts in the database;
- allow to modify keywords via command line arguments or config file
- allow to store data of vacancy to make html based on month not on entire
    base!
- remake job_head and job_description - for now it's a mess and generate
    a ton of crazy html-like code with incorrect close/open tags
- remake block for making html entries
- rewrite API/BS4 block to single function