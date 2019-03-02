from app import app,db
#from app import create_app, db
from app.models import Comment, Mention
from app.extractTickers import extractTickers
from app.getSentiment import getSentiment

from dotenv import load_dotenv
from datetime import datetime, timezone
import os

import praw

import numpy
import alpaca_trade_api as tradeapi

APP_ROOT = os.path.join(os.path.dirname(__file__), '../')# refers to application_top
#APP_ROOT = os.path.dirname(__file__)
#print(APP_ROOT)
dotenv_path = os.path.join(APP_ROOT, '.env')
#print(dotenv_path)
load_dotenv(dotenv_path)

api = tradeapi.REST(os.getenv('ALPACA_KEY_ID'), os.getenv('ALPACA_SECRET_KEY'), base_url="https://paper-api.alpaca.markets")

def getAvgSentiment(mention):
    previous_mentions = Mention.query.filter_by(symbol=mention.symbol).all()
    if len(previous_mentions) == 0:
        avg_sentiment = mention.sentiment
    else:
        total = 0
        for prev_mention in previous_mentions:
            total += prev_mention.sentiment
        avg_sentiment = (total + mention.sentiment)/(len(previous_mentions) + 1)
    
    return avg_sentiment

def processComment(redditComment):
    comment = Comment(reddit_id = redditComment.id, reddit_link = redditComment.permalink, author = redditComment.author.name, body = redditComment.body, created_at = datetime.fromtimestamp(redditComment.created_utc, timezone.utc))
    db.session.add(comment)
    db.session.commit()
    
    mentioned_tickers = extractTickers(redditComment.body)
    if len(mentioned_tickers) > 1:
        score = getSentiment(redditComment.body)['compound'] 
        for ticker in mentioned_tickers:
            try:
                tradable = api.get_asset(ticker).tradable
            except:
                tradable = False
            if tradable and (score > 0.2 or score < -0.2):
                mention = Mention(comment_id = comment.id, symbol = ticker, sentiment = score, created_at = comment.created_at)
                mention.avg_sentiment = getAvgSentiment(mention)
                db.session.add(mention)
        db.session.commit()
    
def getRedditStream():
    reddit = praw.Reddit(client_id=os.getenv('REDDIT_CLIENT_ID'), client_secret=os.getenv('REDDIT_CLIENT_SECRET'), user_agent='Linux:WSBIndex:v0.1 (by /u/chucksaysword)')
    subreddit = reddit.subreddit('wallstreetbets')
#    for submission in subreddit.hot(limit=10):
#        if submission.link_flair_text == 'Daily Discussion':
#            id = submission.id
#            break
    for comment in subreddit.stream.comments():
        if api.get_clock().is_open:
            #if comment.parent_id == "t3_%s" % id:
            if Comment.query.filter(Comment.reddit_id == comment.id).first() is not None:
                app.logger.info("Comment already processed, skipping")
                continue
            else:
                app.logger.info("Processing comment: " + comment.id)
                processComment(comment)
        else:
            break