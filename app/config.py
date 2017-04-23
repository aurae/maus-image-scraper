from app.http.requests import RequestsHttpClient
from app.scrapers.bing import BingScraper

# The Scraper implementation to use
SCRAPER_IMPL = BingScraper(RequestsHttpClient())

DEBUG = False
