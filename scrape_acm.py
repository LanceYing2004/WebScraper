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


def scrape_acm(url, driver):
    driver.delete_all_cookies()
    driver.get(url)

    # close cookie box
    try:
        cookie_close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinDeclineAll"))
        )
        cookie_close_button.click()
    except Exception as e:
        pass

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
        pass

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