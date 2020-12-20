import sqlite3
import time

from bs4 import BeautifulSoup
from googleplaces import GooglePlaces

scontext = None
conn = sqlite3.connect('vape.db')
cur = conn.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS places (name TEXT, Lat REAL, Lon REAL, adr TEXT, city TEXT, postcode TEXT, phone_loc TEXT, phone_int TEXT, www TEXT)''')

cur.execute('''SELECT place FROM cities WHERE scanned=0''')
cities = cur.fetchall()

YOUR_API_KEY = '...'
google_places = GooglePlaces(YOUR_API_KEY)

exc = 0

for city in cities:
    print('\nGoing through {}'.format(city[0]))
    catch = city[0] + ', UK'
    try:
        time.sleep(1)
        query_result = google_places.text_search(
            location=catch, query='vape shop', radius=50000)
        time.sleep(1)
    except:
        print('Due to exception skipping {}'.format(catch))
        exc += 1
        if exc > 50:
            break
        continue

    if query_result.has_attributions:
        print(query_result.html_attributions)

    exc = 0
    for place in query_result.places:
        name = place.name
        lat = float(place.geo_location.get('lat'))
        lon = float(place.geo_location.get('lng'))

        cur.execute(
            '''SELECT name, Lat, Lon FROM places WHERE name=? AND Lat=? AND Lon=?''',
            (name, lat, lon,))

        try:
            dattest = cur.fetchone()[0]
            print("Found in database shop - {} in {}".format(name, city[0]))
            continue
        except:
            pass

        time.sleep(1)
        place.get_details()
        time.sleep(1)
        try:
            phone_loc = place.local_phone_number
        except:
            phone_loc = ''
        try:
            phone_int = place.international_phone_number
        except:
            phone_int = ''
        try:
            www = place.website
        except:
            www = ''

        address_to_parce = place.details.get('adr_address')
        q = BeautifulSoup(address_to_parce, 'html.parser')
        try:
            cit = q.find('span', {'class': 'locality'}).getText()
        except:
            cit = ''
        address_form = place.formatted_address
        adr = address_form[:address_form.find(cit) - 2]
        try:
            post = q.find('span', {'class': 'postal-code'}).getText()
        except:
            post = ''

        print('Writing {} at {}, {}, {}'.format(name, adr, cit, post))

        cur.execute('''INSERT INTO places (name, Lat, Lon, adr, city, postcode, phone_loc, phone_int, www)
                    VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
            name, lat, lon, adr, cit, post, phone_loc, phone_int, www))

        conn.commit()

    cur.execute(
        '''UPDATE cities SET scanned = 1 WHERE place = ?''', (city[0],))
    conn.commit()

conn.close()
print("\nDONE!!!")
