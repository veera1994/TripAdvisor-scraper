# Imports
from flask import Flask
from flask_restful import Resource, Api
from flask import Response
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from selenium import webdriver

# Creating the flask app
app = Flask(__name__)
api = Api(app)

# Reading the citylinks.csv file. It contains tripadvisor links for all the cities along with the page numbers
df = pd.read_csv('citylinks.csv')
df.city = df.city.str.replace(' Restaurants', '')

# Opening the webdriver for selenium to extract the website address and email information
driver = webdriver.Chrome('C:\chromedriver.exe')


# This class returns the welcome page
class helloworld(Resource):
    def get(self):
        return "Welcome to the scraper! Please type '/scrape/<city_name>/<No.of pages>' after the URL"


# This class contains the functions for scraping the restaurant details and website information
class multi(Resource):
    def get(self, nam, num):
        '''
        :param nam: Name of the city
        :param num: Number of pages you want to scrape
        :return: dataframe will download as a csv file
        '''
        dff = df[df.city == str(nam)]
        link = dff.link.values[0]
        df1 = pd.DataFrame()
        df2 = pd.DataFrame()
        counter = 0
        if num > dff.pages.values[0]:
            num = dff.pages.values[0]
        # If you specify pages greater than available it will take the maximum pages available
        for j in range(num):
            code1 = re.search('-(\w+)-', link).group(1)
            code2 = re.search('-.*?-(.*)', link).group(1)
            # URL generation for each pages
            url = 'https://www.tripadvisor.com/Restaurants' + '-' + code1 + '-oa' + str(
                30 * j) + '-' + code2 + '#EATERY_LIST_CONTENTS'
            # Get the URL and parse
            results = requests.get(url)
            soup = BeautifulSoup(results.text, "html.parser")
            # Go through each restaurant in that page
            for sec in soup.find_all('div', class_="_1llCuDZj"):
                a_link = re.findall('<a class="_15_ydu6b".+?</a>', str(sec))
                b_link = re.sub(r'<a class="_15_ydu6b" href="', '', str(a_link), flags=re.MULTILINE)
                c_link = re.sub(r'" target="_blank">.+?</a>', '', str(b_link), flags=re.MULTILINE)
                d_link = 'https://www.tripadvisor.com' + c_link.replace("'", "").replace("[", "").replace("]", "")
                counter = counter + 1
                print(counter, ' ', url)
                print(str(nam), '  ', d_link)
                df1 = df1.append(res_info(d_link, str(nam)))
                df2 = df2.append(res_website(d_link))
        # Merge and dropping the duplicates
        df1 = df1.drop(columns=['email', 'website'])
        df1 = df1[df1.Name != 'N']
        dff = pd.merge(df1, df2, how='left', on=['Name', 'TripAdvisorLink'])
        dff = dff.drop_duplicates()
        # Download the data as a csv
        return Response(
            dff.to_csv(index=False),
            mimetype="text/csv",
            headers={"Content-disposition":
                         "attachment; filename=data.csv"})


def res_info(res_url, name):
    '''
    :param res_url: Restaurant URL
    :param name: City of the restaurant
    :return: Dataframe with restaurant details
    '''
    column_names = ['Name', 'TripAdvisorLink', 'status', 'pricestatus', 'adress', 'city', 'phone', 'email', 'website',
                    'rating', 'reviews', 'subcat', 'detail', 'Thuisbezorgd', 'TheFork']
    res_info = pd.DataFrame(columns=column_names)
    user_agent_old_phone = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'
    res_header = {'User-Agent': user_agent_old_phone}
    results_res = ''
    # If TripAdvisor kicks you out this piece of code will put the script to sleep
    while results_res == '':
        try:
            results_res = requests.get(res_url, headers=res_header)
            break
        except:
            print("Connection refused by the server..")
            print("Let me sleep for 5 seconds")
            print("ZZzzzz...")
            time.sleep(5)
            print("Was a nice sleep, now let me continue...")
            continue
    # Scraping part
    soup_res = BeautifulSoup(results_res.text, "html.parser")
    link = res_url
    Name = status = priceStatus = address = phone = overallRating = reviews = delivery = reserve = ''
    try:
        Name = soup_res.find('h1', class_="_3a1XQ88S").text
        status = soup_res.find('div', class_="_1NXh105y").text
        priceStatus = soup_res.find('a', class_="_2mn01bsa").text
        address = soup_res.find('a', href="#MAPVIEW").text
        a = soup_res.find_all('span', class_="_13OzAOXO _2VxaSjVD")
        b = re.findall('<a class="_3S6pHEQs".+?</a>', str(a))
        c = re.sub(r'<a class="_3S6pHEQs" href=.+?">', '', str(b), flags=re.MULTILINE)
        phone = re.sub(r'</a>', '', str(c), flags=re.MULTILINE)
        overallRating = soup_res.find('span', class_="r2Cf69qf").text
        reviews = soup_res.find('a', class_="_10Iv7dOs").text
        aa = soup_res.find_all('img', class_="_3KMxQ_rq")
        delivery = re.findall('thuisbezorgd', str(aa))
        reserve = re.findall('TheFork', str(aa))
    except:
        pass
    subcat = detail = detail1 = ''
    subtext = soup_res.find_all('div', class_="jT_QMHn2")
    at = soup_res.find_all('div', class_="o3o2Iihq")
    bt = soup_res.find_all('div', class_="_2170bBgV")
    at1 = soup_res.find_all('div', class_="_14zKtJkz")
    bt1 = soup_res.find_all('div', class_="_1XLfiSsv")
    for i in range(len(subtext)):
        a = re.findall('<span class="_2vS3p6SS">.+?</span>', str(subtext[i]))
        a_sub = re.sub(r'</span>', '', re.sub(r'<span class="_2vS3p6SS">', '', str(a), flags=re.MULTILINE),
                       flags=re.MULTILINE)
        b = re.findall('<span class="ui_bubble_rating bubble_.+?"></span>', str(subtext[i]))
        b_sub = re.sub(r'"></span>', '',
                       re.sub(r'<span class="ui_bubble_rating bubble_', '', str(b), flags=re.MULTILINE),
                       flags=re.MULTILINE)
        subcat = subcat + a_sub + ':' + b_sub + ','
    for k in range(len(at)):
        a = re.findall('<div class="o3o2Iihq">.+?</div>', str(at[k]))
        a_sub = re.sub(r'</div>', '', re.sub(r'<div class="o3o2Iihq">', '', str(a), flags=re.MULTILINE),
                       flags=re.MULTILINE)
        b = re.findall('<div class="_2170bBgV">.+?</div>', str(bt[k]))
        b_sub = re.sub(r'</div>', '', re.sub(r'<div class="_2170bBgV">', '', str(b), flags=re.MULTILINE),
                       flags=re.MULTILINE)
        detail = detail + a_sub + ':' + b_sub + ','
    for m in range(len(at1)):
        a = re.findall('<div class="_14zKtJkz">.+?</div>', str(at1[m]))
        a_sub = re.sub(r'</div>', '', re.sub(r'<div class="_14zKtJkz">', '', str(a), flags=re.MULTILINE),
                       flags=re.MULTILINE)
        b = re.findall('<div class="_1XLfiSsv">.+?</div>', str(bt1[m]))
        b_sub = re.sub(r'</div>', '', re.sub(r'<div class="_1XLfiSsv">', '', str(b), flags=re.MULTILINE),
                       flags=re.MULTILINE)
        detail1 = detail1 + a_sub + ':' + b_sub + ','
    res_info = res_info.append(
        {'Name': Name if Name else 'N', 'TripAdvisorLink': link, 'status': status if status else 'N',
         'adress': address if address else 'N', 'city': str(name), 'phone': phone if phone else 'N', 'email': ' ',
         'website': ' ',
         'pricestatus': priceStatus if priceStatus else 'N', 'rating': overallRating if overallRating else 'N',
         'reviews': reviews if reviews else 'N', 'subcat': subcat if subcat else 'N',
         'detail': detail if detail else detail1,
         'Thuisbezorgd': 'True' if delivery else 'False', 'TheFork': 'True' if reserve else 'False'}, ignore_index=True)
    print("details done")
    return res_info


def res_website(res_url):
    '''
    :param res_url: Restaurant URL
    :return: Dataframe with restaurant website and email address
    '''
    column_names = ['Name', 'TripAdvisorLink', 'website', 'email']
    user_agent_old_phone = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'
    res_header = {'User-Agent': user_agent_old_phone}

    res_web = pd.DataFrame(columns=column_names)
    results_res = ''
    while results_res == '':
        try:
            results_res = requests.get(res_url, headers=res_header)
            break
        except:
            print("Connection refused by the server..")
            print("Let me sleep for 5 seconds")
            print("ZZzzzz...")
            time.sleep(5)
            print("Was a nice sleep, now let me continue...")
            continue
    # results_res = requests.get(res_url, headers=res_header)
    soup_res = BeautifulSoup(results_res.text, "html.parser")
    link = res_url
    website1 = email = Name = ''
    try:
        Name = soup_res.find('h1', class_="_3a1XQ88S").text
        driver.get(res_url)
        time.sleep(2)  # If you don't sleep here sometimes it moves fast and miss scraping
        website1 = driver.find_element_by_xpath('//a[@target="_blank" and @class="_2wKz--mA _15QfMZ2L"]').get_attribute(
            "href")
        a = soup_res.find_all('div', class_="_36TL14Jn _3jdfbxG0")
        b = re.findall('<a href="mailto:.+?>', str(a))
        c = re.sub(r'<a href="mailto:', '', str(b), flags=re.MULTILINE)
        email = re.sub(r'subject=.+?">', '', str(c), flags=re.MULTILINE)
    except:
        pass
    res_web = res_web.append(
        {'Name': Name if Name else 'N', 'TripAdvisorLink': link, 'website': website1 if website1 else 'N',
         'email': email if email else 'N'}, ignore_index=True)
    print("website done")

    return res_web


api.add_resource(helloworld, '/')  # Homepage
api.add_resource(multi, '/scrape/<string:nam>/<int:num>')  # Scraping page

if __name__ == '__main__':
    app.run(debug=True)
