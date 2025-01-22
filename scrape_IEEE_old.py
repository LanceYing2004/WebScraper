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
import chromedriver_autoinstaller


def test_if_exists_journal(venue, venue_year):

    venue_url = 'https://dblp.org/db/conf/'+venue+'/'+venue+venue_year+'.html'
    print(venue_url)
    dois = []

    response = requests.get(venue_url)

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all the publication starting with 'li' on the page
    publication_elements = soup.find_all('li', class_='entry inproceedings')

    # Extract the DOI value from each element and add it to the list
    for publication_element in publication_elements:
        doi_element = publication_element.find('div', class_='head')
        doi = doi_element.find('a', href=True)['href'][7:]
        dois.append('https:/'+doi)

    return response, soup, dois

def scrape_doi_from_venue_journal(dois, venue, year, response):
    venue_url = f'https://dblp.org/db/conf/{venue}/{venue}{year}.html'
    dir_path = f'venue/{venue}{year}'

    # Create directories
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # write the entire webpage to HTML
    with open(f'{dir_path}/{venue}{year}.html', 'wb') as f:
        f.write(response.content)

    # write DOI web address collection
    with open(f'{venue}_{year}.txt', 'w') as file:
        for doi in dois:
            file.write(f"{doi}\n")

    return None

def setup_driver():
    chromedriver_autoinstaller.install()
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver


def scrape_pre_content_with_abstract(doi_url, venue, year, doi_index):
    driver = setup_driver()
    dir_path = f'venue/{venue}{year}'

    try:
        driver.get(doi_url)

        # Wait and click the "Cite This" button
        wait = WebDriverWait(driver, 20)
        cite_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "xpl-btn-secondary")))
        cite_button.click()

        # Wait and click the "BibTeX" tab
        bibtex_tab = wait.until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/ngb-modal-window/div/div/div/div[2]/nav/div[2]"))
        )
        bibtex_tab.click()

        # Wait for and click the checkbox, to enable abstract
        abstract_checkbox = wait.until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/ngb-modal-window/div/div/div/div[3]/div[1]/div[1]/input"))
        )
        if not abstract_checkbox.is_selected():
            abstract_checkbox.click()
            time.sleep(1)


        # Wait for the <pre> tag, and the scrape the content inside it
        pre_element = wait.until(
            EC.presence_of_element_located((By.XPATH, "/html/body/ngb-modal-window/div/div/div/div[3]/pre"))
        )

        # Extract
        pre_content = driver.execute_script("return arguments[0].innerText;", pre_element)
        print(f"BibTeX w/ abstract:\n{pre_content}")


        # Save
        file_path = f'{dir_path}/{venue}_{year}_{doi_index}.txt'
        with open(file_path, 'w') as file:
            file.write(pre_content)

        return None
    except Exception as e:
        print(f"Failed to scrape content from <pre> tag: {e}")
        return None
    finally:
        driver.quit()

def scrape_IEEE(venue):

    i_year = np.arange(2024, 1979, -1, dtype=np.int16)
    years = i_year.astype(str)
    print(years)

    for year in years:
        response, soup, dois = test_if_exists_journal(venue, year)

        print(venue,year,'has ', len(dois), 'entries')
        if len(dois) > 0:
            print("DOI'ing... Venue:",venue, "Year:",year,". Total entry:",len(dois))

            scrape_doi_from_venue_journal(dois, venue, year, response)

            doi_index = 0
            total_doi = len(dois)

            for doi in dois[doi_index:]:
                print("\n")

                print("START...DOI Index: ", doi_index, ' of ', total_doi)
                print(doi)

                scrape_pre_content_with_abstract(doi, venue, year, doi_index)

                print("END...DOI Index: ", doi_index,' of ',total_doi)

                doi_index+=1


            rand_sleep = np.random.randint(20,40)
            time.sleep(rand_sleep)
