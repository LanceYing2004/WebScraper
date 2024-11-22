from bs4 import BeautifulSoup

import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import numpy as np
import pandas as pd
from pathlib import Path
import re
import os

def scrape_dblp(venue):
    venue_url = f'https://dblp.org/db/conf/{venue}/index.html'

    # send GET request
    response = requests.get(venue_url)

    # Check for request errors
    try:
        response.raise_for_status()
    except Exception as e:
        return None

    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # get all conference links
    links = [
        a['href'] 
        for a in soup.find_all("a", string="[contents]")
        if 'href' in a.attrs and re.search(fr'/{venue}\d+\.html$', a['href'])
    ]

    return links

def scrape_doi_from_venue_journal(url):
    # send GET request
    response = requests.get(url)

    # Check for request errors
    try:
        response.raise_for_status()
    except Exception as e:
        return None

    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')


    # Find all <a> tags that contain specific image
    dois = []
    # Find all the publication elements on the page
    publication_elements = soup.find_all('li', class_='entry inproceedings')

    # Extract the DOI value from each element and add it to the list
    for publication_element in publication_elements:
        doi_element = publication_element.find('div', class_='head')
        dois.append(doi_element.find('a', href=True)['href'])

    # for each img, get the parent link
    
    return dois



def scrape_conf(venue, scraper):
    links = scrape_dblp(venue)

    all_papers = []

    # iterate through each link
    for link in links[:4]:
        print("scraping", link)

        # get name
        name = link.split("/")[-1].split(".")[0]

        # get all dois
        dois = scrape_doi_from_venue_journal(link)
        
        if not dois:
            print(name, 'failed')
            continue
        print(name, "has", len(dois))
        
        # create output directory
        dir_path = Path(f"{venue}/{name}")
        dir_path.mkdir(parents=True, exist_ok=True)

        for doi in dois[1:3]:
            # try to scrape bibtext 10 times
            citation_text = None
            i = 0
            while not citation_text and i < 10:
                citation_text = scraper(doi)
                time.sleep(3)
                i += 1

            # if not failed
            if citation_text:
                # get doi number
                doi_num = doi.rsplit('/', 1)[-1]

                # add to all papers tuple
                all_papers.append((venue, name, doi, citation_text))

                # print to file
                file_path = dir_path / f'{doi_num}.txt'
                with file_path.open('w') as file:
                    file.write(citation_text)
            else:
                file_path = dir_path / f'failed.txt'
                with file_path.open('w') as file:
                    file.write(f"FAILED: {doi}")

            rand_sleep = np.random.randint(5,15)
            time.sleep(rand_sleep)
    
    return all_papers