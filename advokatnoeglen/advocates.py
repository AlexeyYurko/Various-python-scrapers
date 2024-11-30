"""
Python script & data contains information about all Danish lawyers.
Some of the data are duplicated in csv (due to geographical zones), in Excel duplicates removed.
Python code may be a little silly, but it works
"""
# -*- coding: UTF-8 -*-

import re
from urllib.request import urlopen

from bs4 import BeautifulSoup


def comma(block):
    """
    Check for comma (for csv)
    """
    if ',' in block:
        block = '"' + block + '"'
    return block


def has_inside(block):
    """
    Check for something inside
    """
    return comma(block[0]) if block else '#N/A'


def check_mail(eml):
    """
    Check for email inside
    """
    return eml[::-1] if eml != '#N/A' else '#N/A'


DATA = open('Advokater.csv', 'w')
DATA.write('''Page, URL, Name, Name2, Surname, Title, Title 2, Area, 
Beskikkelsesår, Fødselsår, Møderet landsret, Møderet højesteret, Email, 
Mobile, Firma, Gade, Postnummer, By, Land, Telefon, Email, CVR, WWW, 
Retskreds, Ansatte\n''')

for page in range(0, 246):  # 246

    print('Getting data for ' + str(page) + ' page')
    url = f"http://www.advokatnoeglen.dk/sog.aspx?s=1&t=1&zf=0000&zt=999999" \
          f"&p={page}"
    urlDetail = "http://www.advokatnoeglen.dk"
    page_adv = urlopen(url)
    soup = BeautifulSoup(page_adv, 'html.parser')
    table = soup.findAll('tr')

    for line in table[1:]:  # 1:
        cut = urlDetail + re.findall(r"href='([\S]+)'", line.__str__())[0]
        print('Scraping ', cut)

        pageDetail = urlopen(cut)
        soupDetail = BeautifulSoup(pageDetail, 'html.parser')

        names = soupDetail.findAll(r'h1')[1].getText().split(' ')  # navn

        if len(names) > 2:
            name = names[0]
            name2 = names[1]
            surname = names[2]
        else:
            name = names[0]
            name2 = ''
            surname = names[1]

        status = soupDetail.findAll(r'h2')[0].getText().split(',')  # Advokat

        if len(status) > 1:
            title = status[0]
            title2 = status[1]
        else:
            title = status[0]
            title2 = ''

        workspaces = ' '.join(soupDetail.findAll(r'h2')[1].getText().split())
        print(workspaces)
        # cut intro Arbejdsområder
        workspaces2 = has_inside(re.findall(
            r'Arbejdsområder: ([\S\s]+)', workspaces))

        area = workspaces2

        works = soupDetail.findAll('p')  # [0].getText() #all in Arbejdsområder
        firm = comma(' '.join(soupDetail.findAll(
            r'h2')[2].getText().split()))  # firma
        print('Name: {}, status: {}, workspaces: {}, firm: {}'.format(
            name, status, workspaces2, firm))

        # works[1] - work
        work = works[1].__str__()
        start = has_inside(re.findall(
            r'Beskikkelsesår: ([\S]+)<', work))  # Beskikkelsesår
        birth = has_inside(re.findall(
            r'Fødselsår: ([\S]+)<', work))  # Fødselsår
        # Møderet for landsret
        highcourt = has_inside(re.findall(r'landsret: ([\S]+)<', work))
        # Møderet for højesteret
        supremecourt = has_inside(re.findall(r'højesteret: ([\S]+)<', work))
        liame = has_inside(re.findall(r'e=([\S]+@[\S]+)"', work))  # reversed
        email = check_mail(liame)  # email
        mobile = has_inside(re.findall(r'\.: ([+0-9]+)', work))  # mobile phone
        print('''Start: {}, birth: {}, @ highcourt: {}, @ supremecourt {}, email: {},
              mobile: {}'''.format(start, birth, highcourt, supremecourt,
                                   email, mobile))

        # works[2] - address
        dats = ' '.join(works[2].__str__().split())
        adr1 = has_inside(
            re.findall(r'p>(.+?)<b', dats)).lstrip().rstrip()  # adr1
        adr2 = has_inside(
            re.findall(r'/>(.+?)<b', dats)).lstrip().rstrip()  # adr2

        adrwork = adr2.split()
        postnumm = adrwork[0]
        by = ' '.join(adrwork[1:])

        country = has_inside(
            re.findall(r'<p>[\S\s]+<br */>[\S\s]+<br */>([\S\s]+).+</p',
                       dats)).lstrip().rstrip()
        print('Address1: {}, address2: {}, country: {}'.format(adr1, adr2,
                                                               country))

        # works[3] - contacts
        cnt = works[3].__str__()
        phone = has_inside(re.findall(r'Tlf\.: ([\d]+)<', cnt))  # tlf
        fax = has_inside(re.findall(r'Fax: ([\d]+)<', cnt))  # fax
        liame2 = has_inside(re.findall(r'e=([\S]+@[\S]+)"', cnt))
        email2 = check_mail(liame2)  # email2
        cvr = has_inside(re.findall(r'Cvr-nr\.: ([\d]+)<', cnt))  # cvr
        print('Phone: {}, fax: {}, email2: {}, CVR: {}'.format(
            phone, fax, email2, cvr))

        # works[4] - staff
        staff = ' '.join(works[4].__str__().split())
        www = has_inside(re.findall(r'>(www.[\S]+)<', staff))  # www
        stafflawyers = has_inside(re.findall(
            r'advokater: ([\S\s]+?)<', staff))  # Ansatte advokater
        retskreds = has_inside(re.findall(
            r'Retskreds: ([\S\s]+)<', staff))  # Retskreds
        print("WWW: {}, staff: {}, retskreds: {}".format(
            www, stafflawyers, retskreds))
        print()

        stringToWrite = '''{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},
        {},{},{},{},{},{},{},{}, {}\n'''.format(str(page), cut, name, name2,
                                                surname,
                                                title, title2, area,
                                                start, birth, highcourt,
                                                supremecourt,
                                                email, mobile, firm,
                                                adr1, postnumm, by, country,
                                                phone,
                                                email2, cvr, www,
                                                retskreds, stafflawyers)

        DATA.write(stringToWrite)

DATA.close()
print("\nDONE!!!")
