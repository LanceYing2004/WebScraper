from utils import scrape_conf
import pandas as pd
from scrape_acm import scrape_acm

all_papers = []
all_papers += scrape_conf("chi", scrape_acm)
all_papers += scrape_conf("sp")

papers_df = pd.DataFrame(all_papers, columns=["venue", "year", "DOI", "bibtext"])

print(papers_df)
