# -*- coding: UTF-8 -*-

from bs4 import BeautifulSoup
from urllib.request import urlopen
import urllib.request
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import sqlite3
import time
import re

def has_inside(block):
    if len(block) > 0:
        return block[0].strip()
    else:
        return '#N/A'

scontext = None

count = 0

conn = sqlite3.connect('naea.sqlite')
cur = conn.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS estate (company_short TEXT, company TEXT, city TEXT, address TEXT, postcode TEXT, telephone TEXT, fax TEXT, email TEXT, www TEXT, empl1T TEXT, empl1FN TEXT,
                                empl1LN TEXT, empl2T TEXT, empl2FN TEXT, empl2LN TEXT)''')

cur.execute('''SELECT * FROM ET WHERE nts=1 AND scraped=0''')
towns = cur.fetchall()

main_url = 'http://www.naea.co.uk/find-agent/'

driver = webdriver.Firefox()
driver.get(main_url)

time.sleep(1)

driver.find_element_by_xpath(
    "//select[@id='body_umbBodyContent_BranchSearch_1_ddlRadius']/option[@value='5']").click()

for town in towns:

    try:
        search_field = driver.find_element_by_id(
            'body_umbBodyContent_BranchSearch_1_txtLocation')
        search_field.clear()
        search_field.send_keys(town[0])
        search_field.send_keys(Keys.ENTER)
        time.sleep(3)
    except:
        print('Something VERY wrong with ' + town[0])
        continue

    lists = driver.find_elements_by_xpath("//div[@class='clear resulttext']")
    for i in lists:
        info = i.text.split('\n')
        company = info[0]
        city = info[1]

        cur.execute(
            "SELECT company_short, city FROM estate WHERE company_short= ? AND city= ?", (company, city))
        try:
            dattest = cur.fetchone()[0]
            print('[{}] With town: {} found in database company: {} at city: {}'.format(
                count, town[0], company, city))
            continue
        except:
            pass

        url_detail = i.find_elements_by_css_selector('a')[0].get_attribute('href')
        page = urlopen(url_detail)
        soup = BeautifulSoup(page, 'html.parser')

        company_info = soup.findAll(
            "div", {"style": "float: left; width: 299px;"})
        company_long = company_info[0].getText().strip()
        address_group = company_info[1].getText().strip().split(', ')
        address = ', '.join(address_group[:-1])
        postcode = address_group[-1]

        contacts_group = soup.find("div", {"id": "contact_points_container"})
        cg = contacts_group.getText().strip()
        phone = has_inside(re.findall('Telephone:[\s]+([\d]+.[\d]+.[\d]+)', cg))
        fax = has_inside(re.findall('Fax:[\s]+([\d]+.[\d]+.[\d]+)', cg))
        email = has_inside(re.findall('([\S]+@[\S]+)', cg))
        www = has_inside(re.findall('Website:[\s]+(www.+)', cg))

        employees_group = soup.findAll("div", {"id": "display_list_container"})
        employees = employees_group[1].findAll(href=True)

        try:
            empl1T = employees[0].getText().split()[0]
            empl1FN = employees[0].getText().split()[1]
            empl1LN = employees[0].getText().split()[2]
        except:
            empl1T = ''
            empl1FN = ''
            empl1LN = ''

        try:
            empl2T = employees[1].getText().split()[0]
            empl2FN = employees[1].getText().split()[1]
            empl2LN = employees[1].getText().split()[2]
        except:
            empl2T = ''
            empl2FN = ''
            empl2LN = ''

        count+=1
        print('[{}]'.format(count), company_long, address, postcode, phone, fax, email, www, empl1T, empl1FN, empl1LN, empl2T, empl2FN, empl2LN)

        cur.execute('''INSERT INTO estate (company_short, company, city, address, postcode, telephone, fax, email, www, empl1T, empl1FN,
                                        empl1LN, empl2T, empl2FN, empl2LN)
                        VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (company, company_long, city, address, postcode, phone, fax, email, www, empl1T, empl1FN,
                                                        empl1LN, empl2T, empl2FN, empl2LN))
        conn.commit()

    cur.execute(
        '''UPDATE ET SET scraped = 1 WHERE Town = ?''', (town[0],))
    conn.commit()

    print('{} done\n'.format(town[0]))

print('DONE!!!')
