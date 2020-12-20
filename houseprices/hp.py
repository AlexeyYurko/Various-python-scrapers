"""
get selling price of houses from http://www.zoopla.co.uk

"""
# -*- coding: UTF-8 -*-

import sqlite3
import time
from urllib.request import urlopen

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

conn = sqlite3.connect('hp.sqlite')
cur = conn.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS hp (address TEXT, postcode TEXT, price TEXT, agent TEXT)''')

cur.execute('''SELECT * FROM hp_rd''')
houses = cur.fetchall()

urlsearch = 'http://www.zoopla.co.uk/house-prices/'

driver = webdriver.Firefox()

for house in houses:
    cur.execute("SELECT address FROM hp WHERE address= ?", (house[0],))

    try:
        dattest = cur.fetchone()[0]
        print("Found in database address {}, postcode {}".format(
            house[0], house[1]))
        continue
    except:
        pass

    driver.get(urlsearch)
    time.sleep(1)

    try:
        search_field = driver.find_element_by_id('search-input-location')
        search_field.send_keys(house[0])
        search_field.send_keys(Keys.ENTER)
        time.sleep(1)
    except:
        print('Something VERY wrong with ' + house[0])
        continue

    res = driver.find_elements_by_tag_name('tr')
    try:
        if 'result' in res[1].text:
            links = res[1].find_elements_by_css_selector('a')
        else:
            print('Something wrong with ' + house[0])
            continue
    except:
        print('Something VERY wrong with ' + house[0])
        continue

    info_url = 'none'
    if 'history' in links[2].text:
        info_url = links[2].get_attribute('href')
    else:
        price = '?'
        agent = 'Private Sale'

    if info_url != 'none':
        page = urlopen(info_url)
        soup = BeautifulSoup(page, 'html.parser')

        try:
            prc = soup.find("strong", {"class": "buyers"}).getText().strip()
            price = ' '.join(
                prc[1:].replace(',', '').split()) if '£' in prc else ' '.join(
                prc.replace(',', '').split())
        except:
            price = '-000'

        try:
            agent_long = soup.find("div", {"class": "sidebar sbt"})
            agent = agent_long.find("strong").getText().strip()
        except:
            agent = '#N/A'

    address = house[0]
    postcode = house[1]
    print(address, postcode, price, agent)

    cur.execute('''INSERT INTO hp (address, postcode, price, agent)
                VALUES ( ?, ?, ?, ?)''', (address, postcode, price, agent))

    conn.commit()

conn.close()
print("\nDONE!!!")
