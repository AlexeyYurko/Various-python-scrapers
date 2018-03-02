# -*- coding: UTF-8 -*-

from bs4 import BeautifulSoup
from urllib.request import urlopen
import urllib.request
import re
import sqlite3


def comma(block):
    if ',' in block:
        block = '"' + block + '"'
    return block


def has_inside(block):
    if len(block) > 0:
        return comma(block[0])
    else:
        return '#N/A'


def get_social(block):
    if block:
        return urllib.request.unquote(block.find('a').get('href'))
    else:
        return '#N/A'


conn = sqlite3.connect('spa_data.sqlite')
cur = conn.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS spa (url TEXT, name DATE, address TEXT, phone TEXT, email TEXT, www TEXT, facebook TEXT, twitter)''')

urlbase = 'http://www.spaweek.com/spas/all-spas/0/?keywords=spa&t=&results=50&sort=&treatment=&p='
urldetail = "http://www.spaweek.com"

start_page = 1
end_page = 70  # 70

for page in range(start_page, end_page + 1):

    print('Getting data for {} page'.format(page))
    url = (urlbase + str(page))
    page_adv = urlopen(url)
    soup = BeautifulSoup(page_adv, 'html.parser')
    table = soup.findAll("div", {"class": "content"})

    for row in table:
        link = row.find('a').get('href')
        name = comma(row.find('a').contents[0].strip())
        print()
        print(name, link)

        cut = urldetail + link

        cur.execute("SELECT name FROM spa WHERE url= ?", (cut,))

        try:
            dattest = cur.fetchone()[0]
            print("Found in database URL {}".format(cut))
            continue
        except:
            pass

        print('Scraping ', cut)
        pageDetail = urlopen(cut)
        soupDetail = BeautifulSoup(pageDetail, 'html.parser')

        try:
            to_extract = soupDetail.find("div", {"id": "map-info"})
        except:
            print('Something wrong with {}'.format(cut))
            continue

        try:
            adr = comma(' '.join(to_extract.find(
                'h2').getText().replace('\n', '').strip().split()))
        except:
            print('Something wrong with {}'.format(cut))
            continue

        facebook = get_social(soupDetail.find("li", {"class": "facebook"}))
        twitter = get_social(soupDetail.find("li", {"class": "twitter"}))

        try:
            phone = has_inside(soupDetail.findAll(
                "li", {"class": "phone"})).getText().strip()
        except:
            phone = '#N/A'

        www = get_social(soupDetail.find("li", {"class": "online"}))
        wwwF = has_inside(re.findall('(www.[\S]+)', www))
        eml = get_social(soupDetail.find("li", {"class": "email"}))
        email = has_inside(re.findall('mailto:(.+)', eml))

        print("Address: {}, phone: {}, www: {}, email: {}, facebook: {}, twitter: {}".format(
            adr, phone, wwwF, email, facebook, twitter))

        cur.execute('''INSERT INTO spa (url, name, address, phone, email, www, facebook, twitter)
                    VALUES ( ?, ?, ?, ?, ?, ?, ?, ?)''', (cut, name, adr, phone, email, wwwF, facebook, twitter))

        conn.commit()

conn.close()
print("\nDONE!!!")
