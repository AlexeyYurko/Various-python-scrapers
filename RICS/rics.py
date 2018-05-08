# -*- coding: UTF-8 -*-

import re
import sqlite3
import time
from urllib.request import urlopen

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys


def has_inside(block):
    if len(block) > 0:
        return block[0].strip()
    else:
        return ''


def type_of_surveyor(data):
    if data == '':
        return ''
    types_list = data.split('•')
    type_list = []
    for type_entry in types_list:
        type_name = type_entry.lstrip().rstrip()
        cur.execute('''INSERT OR IGNORE INTO tos (name)
            VALUES ( ? )''', (type_name,))
        cur.execute(
            'SELECT id FROM tos WHERE name = ? ', (type_name,))
        type_id = cur.fetchone()[0]
        type_list.append(type_id)
    conn.commit()
    return ', '.join(map(str, type_list))


def list_of_services(data):
    service_list = []
    for service_entry in data:
        service_name = service_entry.getText()
        cur.execute('''INSERT OR IGNORE INTO services (name)
            VALUES ( ? )''', (service_name,))
        cur.execute(
            'SELECT id FROM services WHERE name = ? ', (service_name,))
        service_id = cur.fetchone()[0]
        service_list.append(service_id)
    conn.commit()
    return ', '.join(map(str, service_list))


def get_detail_data(url_detail):
    time.sleep(2)
    page = urlopen(url_detail)
    soup = BeautifulSoup(page, 'html.parser')

    company_info = soup.findAll(
        "div", {"class": "detail_intro"}).__str__()

    mobile = has_inside(re.findall(
        r'Mobile.+"([0-9\s]+)"', company_info))
    fax = has_inside(re.findall(r'Fax.+"([0-9\s]+)"', company_info))

    services = list_of_services(soup.findAll(
        "a", {"class": "servicesglossary"}))

    # type of surveyor extraction
    tos = soup.findAll("div", {"class": "rCol"})[
        0].__str__().replace('\n', '')
    buss_type = has_inside(re.findall(
        r'<h4>Business type<\/h4><p>(.+?)<', tos))

    tos = soup.__str__().replace('\n', '')
    type_of_srv = type_of_surveyor(has_inside(
        re.findall(r'<h4>Type of surveyor<\/h4><p>(.+?)<', tos)))

    # managers
    tos = soup.findAll("p")
    for t in tos:
        if 'Mr' in t.getText() or 'Mrs' in t.getText():
            mng_list = list(mng.rstrip().lstrip()
                            for mng in t.getText().split('•'))
            for _ in range(5 - len(mng_list)):
                mng_list.append('')
            break
        else:
            mng_list = []
    contact1, contact2, contact3, contact4, contact5 = mng_list[:5]
    return mobile, fax, services, buss_type, type_of_srv, contact1, contact2, contact3, contact4, contact5


count = 0

conn = sqlite3.connect('rics.sqlite')
cur = conn.cursor()

cur.executescript('''
CREATE TABLE IF NOT EXISTS surveyor (company TEXT, address TEXT, postcode TEXT, telephone TEXT, mobile TEXT, fax TEXT, email TEXT, www TEXT,
                                type_of_srv TEXT, buss_type TEXT, services TEXT,
                                contact1 TEXT, contact2 TEXT, contact3 TEXT, contact4 TEXT, contact5 TEXT);
CREATE TABLE IF NOT EXISTS services (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, name TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS tos (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, name TEXT UNIQUE);''')

cur.execute('''SELECT * FROM tcml WHERE scanned=0''')
towns = cur.fetchall()

main_url = 'http://www.ricsfirms.com/'

driver = webdriver.Firefox()
driver.get(main_url)

time.sleep(1)

for town in towns:

    try:
        search_field = driver.find_element_by_id('searchBox')
        search_field.clear()
        search_field.send_keys(town[0] + ',UK')
        search_field.send_keys(Keys.ENTER)
        time.sleep(3)
    except:
        print('Something VERY wrong with ' + town[0])
        continue

    while True:

        lists = driver.find_elements_by_class_name("item")
        for i in lists:

            basic_info = i.find_elements_by_tag_name('p')
            info = i.text.split('\n')
            company = info[0]

            address_long = basic_info[
                0].text.strip().replace('\n', ' ').split(', ')
            postcode = address_long[-1]
            address = ', '.join(address_long[:-1])

            cur.execute(
                "SELECT company, address FROM surveyor WHERE company= ? AND address=? AND postcode=?",
                (company, address, postcode))
            try:
                dattest = cur.fetchone()[0]
                print('[{}] With town: {} found in database company: {} at {}'.format(
                    count, town[0], company, address))
                continue
            except:
                pass

            try:
                www = basic_info[1].find_elements_by_css_selector(
                    'a')[0].get_attribute('href')
            except:
                www = ''

            try:
                inner_html = basic_info[1].get_attribute('innerHTML')
                email = has_inside(re.findall(
                    r':([\S]+@[\S]+)[?]', inner_html))
                telephone = has_inside(re.findall(
                    r'<span>([\S\s]+)<\/span>', inner_html))
            except:
                email = ''
                telephone = ''

            try:
                url_detail = i.find_elements_by_css_selector(
                    'a')[0].get_attribute('href')
                mobile, fax, services, buss_type, type_of_srv, contact1, contact2, contact3, contact4, contact5 = get_detail_data(
                    url_detail)
            except:
                mobile, fax, services, buss_type, type_of_srv, contact1, contact2, contact3, contact4, contact5 = '', '', '', '', '', '', '', '', '', '',

            count += 1
            print(
                '[{}] Company {} at {}, {} with phone {}, mobile {}, fax {}, email {}, web {},\ntypes of service {}, business type {} and services {},\nwith contacts: {}, {}, {}, {}, {}'.format(
                    count, company, address, postcode, telephone, mobile, fax, email, www, type_of_srv, buss_type,
                    services, contact1, contact2, contact3, contact4, contact5))

            cur.execute('''INSERT INTO surveyor (company, address, postcode, telephone, mobile, fax, email, www,
                                            type_of_srv, buss_type, services,
                                            contact1, contact2, contact3, contact4, contact5 )
                            VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (company, address, postcode, telephone, mobile, fax, email, www,
                         type_of_srv, buss_type, services,
                         contact1, contact2, contact3, contact4, contact5))
            conn.commit()

        end_of_town = driver.find_elements_by_xpath(
            "//a[@class='next disabled']")
        if len(end_of_town) > 0:
            break
        else:
            print('Moving to next page')
            try:
                next_element = driver.find_element_by_class_name(
                    'next').click()
            except:
                break

    cur.execute(
        '''UPDATE tcml SET scanned = 1 WHERE Town = ?''', (town[0],))
    conn.commit()

    print('{} done\n'.format(town[0]))

conn.close()

print('DONE!!!')
