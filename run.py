#NEED TO UPDATE
#from scrapers.reddit_scraper import RedditScraper
#from app import db
from app.reddit import getRedditStream
from app.trade import rebalancePortfolio, getOrderUpdates

#app = create_app()
#app.app_context().push()

def run_inverse_wsb():
    #code that process WSB comments
    getRedditStream()
    
def run_rebalance():
    #rebalances portfolio based on # of mentions
    rebalancePortfolio()
    
def run_orderupdates():
    getOrderUpdates()