import nltk
from pprint import pprint

#nltk.download('vader_lexicon')

from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA

sia = SIA()

def getSentiment(text):
    pol_score = sia.polarity_scores(text)
    #pol_score['comment'] = comment.body
    #results.append(pol_score)

    return pol_score

#pprint(results[:10], width=100)
