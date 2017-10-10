"""
http://www.checkatrade.com
"""
import sqlite3
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

trades = ['Air conditioning', 'Alarms/security', 'Appliance services/Repair', 'Asbestos services',
          'Bathrooms', 'Bedrooms', 'Blacksmith/Ironwork', 'Builder', 'Carpenter',
          'Carpets/Flooring', 'Central Heating Engineer', 'Chimney Sweep', 'Cleaning services',
          'Curtains/Blinds/Shutters', 'Damp proofer', 'Drain/Sewer clearance',
          'Driveways/Patios/Paths', 'Electrician', 'Fencing/Gates', 'Fireplaces/Stoves',
          'Flood protection/defence', 'Furniture repair/Restoration', 'Garage/Vehicle services',
          'Garage doors', 'Garden services', 'Glass', 'Hire services', 'Home improvements',
          'Hot tubs/spa', 'Household Water Treatment', 'Insulation', 'Kitchens',
          'Landscaper', 'Locksmith', 'Lofts/Loft Ladders', 'Miscellaneous Services', 'Mobility',
          'Motor homes', 'Painter/decorator', 'PAT testing', 'Pest/vermin control', 'Plasterer',
          'Plumber', 'Removals/Storage', 'Renewable energy', 'Roofer', 'Rubbush/Waste/Clearance',
          'Scaffolder', 'Shop fitting', 'Stonemason', 'Swimming pools', 'Taxi services',
          'Telecommunications', 'Tiler - tiling', 'Towing/Transportation', 'Tree surgeon',
          'TV aerial/Satellite services', 'Weather coatings', 'Windows/Doors/Conservatories']

count = 0

conn = sqlite3.connect('cat.sqlite')
cur = conn.cursor()

cur.executescript('''CREATE TABLE IF NOT EXISTS cat (company_name TEXT, url TEXT, person_name TEXT,
                  email_address TEXT, landline_phone_number TEXT, mobile_phone_number TEXT,
                  trade TEXT, town TEXT, region TEXT, postcode TEXT, www TEXT);''')

cur.execute('''SELECT * FROM tcml WHERE scanned=0''')
towns = cur.fetchall()

main_url = 'http://www.checkatrade.com'

driver = webdriver.Firefox()
driver.get(main_url)

time.sleep(1)

for twn in towns:

    for trade in trades:

        search_field = driver.find_element_by_id('trade_autocomplete_input')
        search_field.clear()
        search_field.send_keys(trade)
        search_field.send_keys(Keys.ENTER)
        search_field = driver.find_element_by_id('location')
        search_field.clear()
        search_field.send_keys(twn[0])
        search_field.send_keys(Keys.ENTER)

        time.sleep(2)

        while True:

            lists = driver.find_elements_by_class_name("listing")

            for i in lists:

                basic_info = i.find_element_by_class_name('results__title')
                company_name = basic_info.text
                url = basic_info.find_elements_by_css_selector(
                    'a')[0].get_attribute('href')
                print(company_name, url)

                cur.execute(
                    "SELECT company_name, url FROM cat WHERE company_name= ? AND url=?",
                    (company_name, url))
                try:
                    dattest = cur.fetchone()[0]
                    print('[{}] With town: {} found in database company: {} at link {}'.format(
                        count, twn[0], company_name, url))
                    continue
                except:
                    pass

                curWindowHndl = driver.current_window_handle
                body = driver.find_element_by_tag_name("body")
                body.send_keys(Keys.COMMAND + 't')
                driver.get(url)
                time.sleep(1)

                email_address = ''
                www = ''
                person_name = ''
                mobile_phone_number = ''
                landline_phone_number = ''
                town = ''
                region = ''
                postcode = ''

                try:
                    contacts = driver.find_element_by_class_name(
                        'contact-card')
                except:
                    pass

                try:
                    email_address = driver.find_element_by_id(
                        'ctl00_ctl00_content_ctlEmail').text
                except:
                    pass

                try:
                    www = driver.find_element_by_id(
                        'ctl00_ctl00_content_ctlWeb').text
                except:
                    pass

                try:
                    person_name = driver.find_element_by_class_name(
                        'contact-card__contact-name').text
                except:
                    pass

                try:
                    landline_phone_number = driver.find_element_by_id(
                        'ctl00_ctl00_content_lblTelNo').text
                except:
                    pass

                try:
                    mobile_phone_number = driver.find_element_by_id(
                        'ctl00_ctl00_content_ctlMobile').text
                except:
                    pass

                try:
                    postcode = driver.find_element_by_xpath(
                        "//span[@itemprop='postalCode']").text
                except:
                    pass

                try:
                    address = driver.find_elements_by_xpath(
                        "//span[@itemprop='addressLocality']")
                    town = ', '.join(list(adr.text for adr in address))
                except:
                    pass

                try:
                    region = driver.find_element_by_xpath(
                        "//span[@itemprop='addressRegion']").text
                except:
                    pass

                body = driver.find_element_by_tag_name("body")
                body.send_keys(Keys.COMMAND + 'w')
                driver.switch_to.window(curWindowHndl)

                count += 1
                print('''[{}] Company {} of {}, with email {}, landline {}, mobile {}, trade {},
                      town {}, region {}, postcode {}'''.format(count, company_name, person_name,
                                                                email_address,
                                                                landline_phone_number,
                                                                mobile_phone_number, trade, town,
                                                                region, postcode))

                cur.execute('''INSERT INTO cat (company_name, url, person_name, email_address,
                            landline_phone_number, mobile_phone_number, trade, town, region,
                            postcode, www )
                            VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                            (company_name, url, person_name, email_address, landline_phone_number,
                             mobile_phone_number, trade, town, region, postcode, www))
                conn.commit()

            print('Moving to next page')
            try:
                next_element = driver.find_elements_by_class_name(
                    'pagination__prev-next')
                if 'Next' in next_element[-1].text:
                    next_element[-1].click()
                    time.sleep(1)
                else:
                    break
            except:
                break

    cur.execute(
        '''UPDATE tcml SET scanned = 1 WHERE Town = ?''', (twn[0],))
    conn.commit()

    print('{} done\n'.format(twn[0]))

conn.close()

print('DONE!!!')
