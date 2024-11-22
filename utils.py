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

def scrape_acm(url):

    # set up webdriver
    current_dir = os.path.dirname(os.path.abspath(__file__))
    service = Service(os.path.join(current_dir, 'chromedriver'))
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(url)
    

    # close cookie box
    try:
        cookie_close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinDeclineAll"))
        )
        cookie_close_button.click()
    except Exception as e:
        return None

    time.sleep(2)
    
    # click on citation box
    try:
        button = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-title="Export Citation"]'))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", button)  # Scroll to the element
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-title="Export Citation"]')))
        
        for _ in range(3):
            try:
                button.click()

                success_element = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.ID, 'exportCitationsPopup'))  
                )
                if success_element:
                    break  

            except Exception as e:
                time.sleep(1)
    except Exception as e:
        return None

    time.sleep(2)

    # get citation text
    try:
        # wait for citation box to pop-up
        citation_popup = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.csl-right-inline'))
        )

        # get dictionary of bibteX
        citation_text = citation_popup.text

    except Exception as e:
        return None
    

    return citation_text
