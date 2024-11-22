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


def scrape_chi():
    venue_url = 'https://dblp.org/db/conf/chi/index.html'

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
        if 'href' in a.attrs and re.search(r'/chi\d+\.html$', a['href'])
    ]



    all_papers = []

    # iterate through each link
    for link in links[:5]:
        print("scraping", link)

        # get name
        name = link.split("/")[-1].split(".")[0]

        # get all dois
        dois = scrape_doi_from_venue_journal(link)

        for doi in dois:
            print(doi)

        return
        
        if not dois:
            print(name, 'failed')
            continue
        print(name, "has", len(dois))
        
        # create output directory
        dir_path = Path(f"chi/{name}")
        dir_path.mkdir(parents=True, exist_ok=True)

        for doi in dois[1:5]:
            # try to scrape bibtext 10 times
            citation_text = None
            i = 0
            while not citation_text and i < 10:
                citation_text = scrape_acm(doi)
                time.sleep(3)
                i += 1

            # if not failed
            if citation_text:
                # get doi number
                doi_num = doi.rsplit('/', 1)[-1]

                # add to all papers tuple
                all_papers.append(("CHI", name, doi, citation_text))

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
    
    papers_df = pd.DataFrame(all_papers, columns=["venue", "year", "DOI", "bibtext"])

    print(papers_df)


scrape_chi()

# https://doi.org/10.1145/3613904.3642413
# https://doi.org/10.1145/3613904.3642953
# https://doi.org/10.1145/3613904.3642222
# https://doi.org/10.1145/3613904.3642189
# https://doi.org/10.1145/3613904.3642514
# https://doi.org/10.1145/3613904.3642744