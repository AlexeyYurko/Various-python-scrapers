import sqlite3

scontext = None

count = 0

rics = sqlite3.connect('rics.sqlite')
geo = sqlite3.connect('postcodes_short.sqlite')

rics_cur = rics.cursor()

geo_cur = geo.cursor()

geo_cur.executescript('''
CREATE TABLE IF NOT EXISTS surveyor_geo (company TEXT, address TEXT, postcode TEXT, county TEXT, district TEXT,
                                        ward TEXT, country TEXT, region TEXT, telephone TEXT, mobile TEXT, fax TEXT,
                                        email TEXT, www TEXT, type_of_srv TEXT, buss_type TEXT, services TEXT,
                                        contact1 TEXT, contact2 TEXT, contact3 TEXT, contact4 TEXT, contact5 TEXT);''')

rics_cur.execute('SELECT * FROM surveyor')

for entry in rics_cur:
    company = entry[0]
    address = entry[1]
    postcode = entry[2].upper()
    if ' ' not in postcode:
        postcode = postcode[:3] + ' ' + postcode[3:]

    geo_cur.execute(
        "SELECT company, address FROM surveyor_geo WHERE company= ? AND address=? AND postcode=?",
        (company, address, postcode))
    try:
        dattest = geo_cur.fetchone()[0]
        print('Skip {} {}'.format(company, address))
        continue
    except:
        pass

    telephone = entry[3]
    mobile = entry[4]
    fax = entry[5]
    email = entry[6]
    www = entry[7]
    type_of_srv = entry[8]
    buss_type = entry[9]
    services = entry[10]
    contact1, contact2, contact3, contact4, contact5 = entry[11:]

    geo_cur.execute('SELECT * FROM pc_short WHERE Postcode = ? ', (postcode,))
    geo_info = geo_cur.fetchone()

    try:
        county = geo_info[1]
        district = geo_info[2]
        ward = geo_info[3]
        country = geo_info[4]
        region = geo_info[5]
    except:
        print(geo_info)
        print(postcode)
        print(entry)
        county = ''
        district = ''
        ward = ''
        country = ''
        region = ''

    print(geo_info, entry[1], entry[2])

    geo_cur.execute('''INSERT INTO surveyor_geo (company, address, postcode, county, district,
                                            ward, country, region,telephone, mobile, fax, email, www,
                                    type_of_srv, buss_type, services,
                                    contact1, contact2, contact3, contact4, contact5 )
                    VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?)''',
                    (company, address, postcode, county, district,
                     ward, country, region, telephone, mobile, fax, email, www,
                     type_of_srv, buss_type, services,
                     contact1, contact2, contact3, contact4, contact5))
    geo.commit()

geo.close()
