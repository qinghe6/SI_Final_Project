import requests
import json
import matplotlib.pyplot as plt
import matplotlib
import random as random
from matplotlib.path import Path
import numpy as np
import matplotlib.colors as colors
import matplotlib.cm as cmx
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import datetime
import re
from dateutil.parser import *
import plotly
import plotly.graph_objs as go
from tabulate import tabulate
import secrets  # file that contains your API key
CACHE_FILENAME = "cache.json"


def open_cache():
    ''' opens the cache file if it exists and loads the JSON into the FIB_CACHE dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    Parameters
    ----------
    None

    Returns
    -------
    The opened cache
    '''

    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    ''' saves the current state of the cache to disk
    Parameters
    ----------
    cache_dict: dict
    The dictionary to save
    Returns
    -------
    None
    '''

    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME, "w")
    fw.write(dumped_json_cache)
    fw.close()


def make_request(baseurl, headers):
    '''Make a request to the Web API using the url
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    Returns
    -------
    string
        the results of the query as a Python object loaded from JSON
    '''

    response = requests.get(baseurl, headers=headers)
    return response.json()


def make_request_with_cache(baseurl, headers):
    '''Check the cache for a saved result for this url.
    If the result is found, return it. Otherwise send a new
    request, save it, then return it.
    Parameters
    ----------
    url: string
        The URL for the API endpoint
    Returns
    -------
    string
        the results of the query as a Python object loaded from JSON
    '''

    CACHE_DICT = open_cache()
    if baseurl in CACHE_DICT.keys():
        print("Using cache")
        return CACHE_DICT[baseurl]
    else:
        print("Fetching")
        CACHE_DICT[baseurl] = make_request(baseurl, headers)
        save_cache(CACHE_DICT)
        return CACHE_DICT[baseurl]


def scarp_a_single_webpage(url):
    '''Scraping a single page based on the given url

    Parameters
    ----------
    url: str
        The url link

    Returns
    -------
    dic
        a dictionary to store all the information that we scrap from one page
    '''

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    searching_div = soup.find_all('table')[0]
    list1 = searching_div.text.split('\n')
    list1.pop(0)
    list2 = []
    for i in list1:
        if len(i) != 0:
            list2.append(i)
    list3 = []
    list4 = []
    listx = []
    for i in list2:
        list3.append(i.split(',')[0])
        listx.append(i.split(',')[1])
        list4.append(i.split(',')[2])
    list5 = []
    for i in list4:
        for j in range(len(i)):
            if i[j].isdigit():
                list5.append(i[j:])
                break
    lon = []
    lat = []
    for i in list5:
        lat.append(float(i.split('-')[0]))
        lon.append(-float(i.split('-')[1]))
    for i in range(100):
        listx[i] = listx[i].strip()

    listy = []
    for i in range(100):
        listy.append("USA")

    dic = {}
    dic["City"] = list3
    dic["State"] = listx
    dic["Country"] = listy
    dic["Latitude"] = lat
    dic["Longitude"] = lon
    return dic


def get_Yelp_Api(lat, lon):
    '''Obtain web API based on the latitude and longitude

    Parameters
    ----------
    lat: float
        The latitude of a city
    lon: float
        The longitude of a city

    Returns
    -------
    dic
        a dictionary to store the Json file
    '''

    url = 'https://api.yelp.com/v3/transactions/delivery/search?latitude=' + str(lat) + "&longitude=" + str(lon) + ''
    res = make_request_with_cache(url, headers)
    with open('data.json', 'w') as fp:
        json.dump(res, fp)
    with open('data.json') as json_file:
        dic = json.load(json_file)
    return dic


def get_data(city):
    '''Obtain the data from the given city

    Parameters
    ----------
    city: str
        The name of a city

    Returns
    --------
    dic
        A dictionary to store the name and rating
    name
        A restaurant's name
    avg_rating
        The average rating of a certain restaurant type

    '''

    connection = sqlite3.connect("choc.sqlite")
    cursor = connection.cursor()
    query = "SELECT Categories, Rating FROM Yelp1 WHERE (City = '%s')" % (city)
    result = cursor.execute(query).fetchall()
    connection.close()

    dic = {}
    for i in result:
        list1 = i[0].split(',')
        for j in list1:
            if len(j) != 0:
                if j not in dic:
                    dic[j] = [i[1]]
                else:
                    dic[j].append(i[1])
    name = []
    avg_rating = []
    for i in dic:
        name.append(i)
        avg_rating.append(sum(dic[i])/len(dic[i]))
    return dic, name, avg_rating


if __name__ == "__main__":
    dic1 = scarp_a_single_webpage('https://www.latlong.net/category/cities-236-15.html')

    listID = []
    for i in range(100):
        listID.append(i + 1)

    conn = sqlite3.connect('choc.sqlite')
    c = conn.cursor()

    c.execute('''
            CREATE TABLE "Location1" (
                    "Id"        INT  NOT NULL,
                    "City"      TEXT NOT NULL,
                    "State"     TEXT NOT NULL,
                    "Country"   TEXT NOT NULL,
                    "Latitude"  NUMERIC NOT NULL,
                    "Longitude" NUMERIC NOT NULL,
                    PRIMARY KEY("Id")
                )
                ''')
    for i in range(len(dic['City'])):
        insert = '''
            INSERT OR IGNORE INTO Location1
            VALUES (?, ?, ?, ?, ?, ?)
    '''
        list1 = [listID[i], dic['City'][i], dic['State'][i], dic['Country'][i], dic['Latitude'][i], dic['Longitude'][i]]
        c.execute(insert, list1)
    conn.commit()
    conn.close()

    lat = dic1["Latitude"]
    lon = dic1["Longitude"]
    headers = {'Authorization': 'Bearer {}'.format(secrets.Yelp_KEY)}
    name = []
    city1 = []
    rating = []
    categories = []
    phone = []
    for i in range(40):
        dic = get_Yelp_Api(lat[i], lon[i])
        if 'businesses' in dic:
            for j in range(len(dic['businesses'])):
                name.append(dic['businesses'][j]['name'])
                rating.append(dic['businesses'][j]['rating'])
                phone.append(dic['businesses'][j]['phone'][1:])
                city1.append(dic['businesses'][j]['location']['city'])
                str1 = ''
                for z in range(len(dic['businesses'][j]['categories'])):
                    str1 += dic['businesses'][j]['categories'][z]['alias'] + ","
                categories.append(str1)

    conn = sqlite3.connect('choc.sqlite')
    c = conn.cursor()

    c.execute('''
            CREATE TABLE "Yelp1" (
                    "City"         TEXT NOT NULL,
                    "Name"         TEXT NOT NULL,
                    "Categories"   TEXT NOT NULL,
                    "Rating"       NUMERIC NOT NULL,
                    "Phone"        NUMERIC NOT NULL,
                    PRIMARY KEY ("Name")
                    FOREIGN KEY ("City") REFERENCES Location1("City")
                );
                ''')

    for i in range(len(name)):
        insert = '''
            INSERT OR IGNORE INTO Yelp1
            VALUES (?, ?, ?, ?, ?)
        '''
        list1 = [city1[i], name[i], categories[i], rating[i], phone[i]]
        c.execute(insert, list1)
    conn.commit()
    conn.close()

    list_C = ['Hoboken', 'Jersey City', 'Union City', 'Cleveland', 'Stuart', 'Woodbridge Township', 'Woodbridge',
              'Avenel', 'Iselin', 'Edison', 'Vista', 'Sparks', 'Green Bay', 'San Mateo', 'League City', 'Lewisville',
              'Waterbury',
              'West Palm Beach', 'Palm Beach', 'Antioch', 'High Point', 'Miami Gardens', 'Opa Locka', 'Miami Lakes',
              'Murrieta',
              'Springfield', 'El Monte', 'College Station', 'Boston', 'Allston', 'Brookline', 'Somerville', 'Cambridge',
              'Richardson',
              'Berkeley', 'Columbia', 'Athens', 'Garland']
    a = 1
    while True:
        if a == 1:
            input1 = input(
                "Enter a city's name from the following cities: Hoboken, Jersey City, Union City, Cleveland, Stuart, "
                "Woodbridge Township, Woodbridge, Avenel, Iselin, Edison, Vista, Sparks, Green Bay, "
                "San Mateo, League City, "
                "Lewisville, Waterbury, West Palm Beach, Palm Beach, Antioch, High Point, "
                "Miami Gardens, Opa Locka, Miami Lakes, "
                "Murrieta, Springfield, El Monte, College Station, Boston, Allston, Brookline, "
                "Somerville, Cambridge, Richardson, "
                "Berkeley, Columbia, Athens, Garland or 'exit':")
            input2 = input1.lower()
            input3 = input2[0].upper() + input2[1:]
            if input2 == 'exit':
                print("Bye!")
                break
            if input3 in list_C:
                dic, xvals, yvals = get_data(input3)
                print(
                    '-----------------------------------------------------'
                    '-------------------------------------------------')
                print(
                    'Four options to visualize the average rating for different '
                    'restaurant types from Yelp in ' + input3)
                print(
                    '------------------------------------------------------'
                    '------------------------------------------------')
                print('(1): Print the name and average rating in the selected city in a neat format.')
                print('(2): Use bar plot to visualize the average rating in the selected city.')
                print('(3): Use Scatter plot to visualize the average rating in the selected city.')
                print('(4): Use line graph to visualize the average rating in the selected city.')
                a = 0
            else:
                print("[Error] Enter the required city's name")
                a = 1
        else:
            input4 = input('Please enter the correspond number or "exit" or "back":')
            if input4.lower() == 'back':
                a = 1
            elif input4.lower() == 'exit':
                print("Bye!")
                break
            elif not input4.isdigit():
                print("[Error] Invalid input")
                a = 0
            elif input4.isdigit():
                if int(input4) < 1 or int(input4) > 4:
                    print("[Error] Invalid input")
                    a = 0
                else:
                    if int(input4) == 1:
                        data = {'Name': xvals, 'Rating': yvals}
                        df = pd.DataFrame(data)
                        print(tabulate(df, floatfmt=",.2f", showindex=False, tablefmt='psql', numalign='decimal',
                                       colalign=("center",)))
                        a = 0
                    elif int(input4) == 2:
                        bar_data = go.Bar(x=xvals, y=yvals)
                        basic_layout = go.Layout(title="A Bar Graph")
                        fig = go.Figure(data=bar_data, layout=basic_layout)
                        fig.show()
                        a = 0
                    elif int(input4) == 3:
                        scatter_data = go.Scatter(x=xvals, y=yvals, mode='markers',
                                                  marker={'symbol': 'star', 'size': 30, 'color': 'magenta'})
                        basic_layout = go.Layout(title="A Scatter Plot")
                        fig = go.Figure(data=scatter_data, layout=basic_layout)
                        fig.show()
                        a = 0
                    elif int(input4) == 4:
                        line_data = go.Scatter(x=xvals, y=yvals)
                        basic_layout = go.Layout(title="A Line Plot")
                        fig = go.Figure(data=line_data, layout=basic_layout)
                        fig.show()
                        a = 0
                        
