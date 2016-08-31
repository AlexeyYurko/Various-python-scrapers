# -*- coding: UTF-8 -*-

from bs4 import BeautifulSoup
from urllib.request import urlopen
import re
from selenium import webdriver


def comma(block):
    if ',' in block:
        block = '"' + block + '"'
    return block


def has_inside(block):
    if len(block) > 0:
        return comma(block[0])
    else:
        return '#N/A'


def check_mail(eml):
    if eml != '#N/A':
        return eml[::-1]
    else:
        return '#N/A'


data = open('parl.csv', 'w')
data.write("Name, e-mail\n")

driver = webdriver.Firefox()


url = ("http://www.parliament.uk/mps-lords-and-offices/mps/")
page = urlopen(url)
soup = BeautifulSoup(page, 'html.parser')
table = soup.findAll('tr')

for line in table[2:]:
    link = line.find('a').get('href')
    print(link)
    if link == '#top':
        continue

    driver.get(link)
    nm = driver.find_element_by_id('breadcrumb')
    name = re.findall('You are here: Parliament home pageMPs, Lords & officesMPs([\\s\\S]+)', nm.text)[0]
    print(name)
    try:
        eml = driver.find_element_by_id('ctl00_ctl00_FormContent_SiteSpecificPlaceholder_PageContent_addParliamentaryAddress_rptAddresses_ctl00_pnlEmail')
        email = eml.text[7:]
    except:
        email = 'none'
    print(email)
    stringToWrite = (
        str(name) + ',' + str(email) + '\n')

    data.write(stringToWrite)

data.close()
print("\nDONE!!!")
