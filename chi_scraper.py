import time                           
import numpy as np 
import pandas as pd
from pathlib import Path 

import utils

def scrape_chi():
    links = utils.scrape_dblp("chi")

    all_papers = []

    # iterate through each link
    for link in links[:5]:
        print("scraping", link)

        # get name
        name = link.split("/")[-1].split(".")[0]

        # get all dois
        dois = utils.scrape_doi_from_venue_journal(link)
        
        if not dois:
            print(name, 'failed')
            continue
        print(name, "has", len(dois))
        
        # create output directory
        dir_path = Path(f"chi/{name}")
        dir_path.mkdir(parents=True, exist_ok=True)

        for doi in dois[1:]:
            # try to scrape bibtext 10 times
            citation_text = None
            i = 0
            while not citation_text and i < 10:
                citation_text = utils.scrape_acm(doi)
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