from utils import scrape_conf
import pandas as pd
from scrape_acm import scrape_acm
from scrape_IEEE import scrape_IEEE

all_papers = []
conf = [("chi", scrape_acm)]
# conf += ("sp", scrape_IEEE)
for c, scraper in conf:
    all_papers += scrape_conf(c, scraper)
    # all_papers += scrape_IEEE("sp")

papers_df = pd.DataFrame(all_papers, columns=["venue", "year", "DOI", "bibtext"])

papers_df.to_csv('papers.csv', index=False)
