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
import tempfile
import shutil

def initialize_driver():
    # fix mkdtemp arguments are other function
    tmpdir = "./cache/"
    service = Service('./chromedriver')
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument(f"--user-data-dir={tmpdir}")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver, tmpdir

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

def scrape_journal(venue):
    venue_url = f'https://dblp.org/db/journals/{venue}/index.html'

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
    link_tags = soup.find_all('a', string=lambda text: text and "Volume" in text)
    
    links = [link['href'] for link in link_tags if 'href' in link.attrs]
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

    if not publication_elements:
        publication_elements = soup.find_all('li', class_='entry article')

    # Extract the DOI value from each element and add it to the list
    for publication_element in publication_elements:
        doi_element = publication_element.find('div', class_='head')
        link = doi_element.find('a', href=True)
        if link:
            dois.append(link['href'])

    # for each img, get the parent link
    
    return dois



def scrape_conf(venue, scraper):
    links = scrape_dblp(venue)
    if not links:
        links = scrape_journal(venue)
    all_papers = []
    
    # iterate through each link
    for link in links:
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

        cur_papers = []

        papers_scraped = 1
        driver, tmpdir = initialize_driver()
        try:
            for doi in dois[1:]:
                if papers_scraped % 20 == 0:
                    driver.quit()
                    shutil.rmtree(tmpdir, ignore_errors=True)
                    driver, tmpdir = initialize_driver()

                print(doi)
                # try to scrape bibtext 10 times
                citation_text = None
                i = 0
                while not citation_text and i < 10:
                    try:
                        citation_text = scraper(doi, driver)
                    except Exception as e:
                        pass
                    
                    time.sleep(3)
                    i += 1

                # if not failed
                if citation_text:
                    # get doi number
                    doi_num = doi.rsplit('/', 1)[-1]

                    # add to all papers tuple
                    all_papers.append((venue, name, doi, citation_text))
                    cur_papers.append((venue, name, doi, citation_text))

                    # print to file
                    file_path = dir_path / f'{doi_num}.txt'
                    with file_path.open('w') as file:
                        file.write(citation_text)
                else:
                    file_path = dir_path / f'failed.txt'
                    with file_path.open('w') as file:
                        file.write(f"FAILED: {doi}")

                papers_scraped += 1
                rand_sleep = np.random.randint(5,15)
                time.sleep(rand_sleep)
        except Exception as e:
            file_path = f'error.txt'
            with file_path.open('a') as file:
                file.write(f"ERROR SCRAPING: {link}")
        finally:
            driver.quit()
            shutil.rmtree(tmpdir, ignore_errors=True)
            papers_df = pd.DataFrame(cur_papers, columns=["venue", "year", "DOI", "bibtext"])
            file_path = dir_path / f'papers'

            papers_df.to_pickle(file_path)
            
    
    return all_papers

def check_papers(venue, scraper):
    pickle_file = Path(f"./{venue}/verified_papers.pkl")
    if not pickle_file.exists():
        pickle_file = Path(f"./{venue}/combined_dataframe.pkl")
    df = pd.read_pickle(pickle_file)

    links = scrape_dblp(venue)
    total_failed = 0
    failed_papers = []
    # iterate through each link
    for link in links:
        print("scraping", link)

        # get name
        name = link.split("/")[-1].split(".")[0]

        # get all dois
        dois = scrape_doi_from_venue_journal(link)

        if not dois:
            print(name, 'failed')
            continue

        # create output directory
        dir_path = Path(f"{venue}/{name}")
        dir_path.mkdir(parents=True, exist_ok=True)
        failed = 0
        try:
            for doi in dois:
                print(doi)
                if doi not in df['DOI'].values:
                    print("SCRAPING", doi)
                    # try to scrape bibtext 10 times
                    citation_text = None
                    i = 0
                    try:
                        driver, tmpdir = initialize_driver()
                        while not citation_text and i < 10:
                            try:
                                citation_text = scraper(doi, driver)
                            except Exception as e:
                                pass

                            time.sleep(3)
                            i += 1
                    finally:
                        driver.quit()
                        shutil.rmtree(tmpdir, ignore_errors=True)

                    # if not failed
                    if citation_text:
                        # get doi number
                        doi_num = doi.rsplit('/', 1)[-1]

                        # add to all papers tuple
                        new_row = (venue, name, doi, citation_text)
                        df.loc[len(df)] = new_row

                        # print to file
                        file_path = dir_path / f'{doi_num}.txt'
                        with file_path.open('w') as file:
                            file.write(citation_text)
                    else:
                        file_path = dir_path / f'failed.txt'
                        if failed == 0:
                            with file_path.open('w') as file:
                                file.write(f"FAILED: {doi}\n")
                        else:
                            with file_path.open('a') as file:
                                file.write(f"FAILED: {doi}\n")
                        failed_papers.append(doi)
                        failed += 1
                        total_failed += 1
                        rand_sleep = np.random.randint(5,15)
                        time.sleep(rand_sleep)
        except Exception as e:
            file_path = f'error.txt'
            with file_path.open('a') as file:
                file.write(f"ERROR SCRAPING: {link}")

    print(f"Failed: {total_failed}")
    print(failed_papers)
    file_path = Path(f"./{venue}/verified_papers.pkl")
    df.to_pickle(file_path)
