import os
import numpy as np
import requests
from bs4 import BeautifulSoup
import numpy
import chromedriver_autoinstaller
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_if_exists_journal(venue, venue_year):

    venue_url = 'https://dblp.org/db/journals/'+venue+'/'+venue+venue_year+'.html'  # Replace 'venue' with the desired venue name
    print(venue_url)
#     if os.path.isdir('venue/'+venue+year)==False:
#         os.mkdir('venue/'+venue+year)
    dois = []

    # Send a GET request to the venue URL
    response = requests.get(venue_url)
#     with open('venue/'+venue+year+'/'+venue+year+'.html', 'wb') as f:
#         f.write(response.content)
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all the publication elements on the page
    publication_elements = soup.find_all('li', class_='entry article')

    # Extract the DOI value from each element and add it to the list
    for publication_element in publication_elements:
        doi_element = publication_element.find('div', class_='head')
        doi = doi_element.find('a', href=True)['href'][7:]
        dois.append('https:/'+doi)

    return response, soup, dois

def scrape_doi_from_venue_journal(venue, year):
    venue_url = f'https://dblp.org/db/journals/{venue}/{venue}{year}.html'  # Replace 'venue' with the desired venue name
    dir_path = f'venue/{venue}{year}'

    # Create directories, including intermediate ones if they don't exist
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    dois = []

    # Send a GET request to the venue URL
    response = requests.get(venue_url)
    with open(f'{dir_path}/{venue}{year}.html', 'wb') as f:
        f.write(response.content)

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all the publication elements on the page
    publication_elements = soup.find_all('li', class_='entry article')

    # Extract the DOI value from each element and add it to the list
    for publication_element in publication_elements:
        doi_element = publication_element.find('div', class_='head')
        doi = doi_element.find('a', href=True)['href'][7:]
        dois.append('https:/' + doi)

    with open(f'{venue}_{year}.txt', 'w') as file:
        for doi in dois:
            file.write(f"{doi}\n")

    return response, soup, dois


venue = 'access'
i_year = np.arange(1, 12, 1, dtype=np.int16)
years = i_year.astype(str)
# years=['2018']
print(years)
for year in years:
    response, soup, dois = test_if_exists_journal(venue, year)

# response, soup, dois = scrape_doi_from_venue(venue, year)
    print(venue,year,'has ', len(dois))
    if len(dois) > 0:
        print("DOI'ing ",venue,year, "Total entry:",len(dois))
        response, soup, dois = scrape_doi_from_venue_journal(venue, year)
        doi_index=0
        total_doi = len(dois)
        for doi in dois[doi_index:]:
            print(doi)
            doi_index+=1
            rand_sleep = np.random.randint(5,10)
            print('Sleep time:',rand_sleep, "DOI Index: ", doi_index,' of ',total_doi)
            time.sleep(rand_sleep)
        rand_sleep = np.random.randint(20,60)
        time.sleep(rand_sleep)