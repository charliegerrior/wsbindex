import re
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize

false_pos = ["ATH", "WSB", "FD", "ER", "YOLO", "ETF", "SEC", "GDP", "OTM", "ITM", "PPT", "FOMO", "RH", "EOD", "IMO", "FUD", "IMHO", "LOW", "CEO", "EPS", "BUY", "HOLD", "SELL", "IPO", "PM", "EOD", "USA", "MAGA", "USD", "DOW"]
stop_words = set(stopwords.words('english'))
#re1 = r'\b\$*[A-Z]{1,5}\b'
#re2 = r'\${1}[a-zA-Z]{1,5}'

def extractTickers(text):
    #pre-processing to remove stop words

#    tokens = word_tokenize(text)
#    words = [word for word in tokens if word.isalpha()]
#    words = [w for w in words if not w.lower() in stop_words]
#    final_words = []
#    for word in words:
#        if not word in false_pos:
#            final_words.append(word)
    #print(filtered_text)
    #regex to pull out tickers
    #need to modify so that $amd and $Snap (for example) are also caught
    #tickers = re.compile("(%s|%s)" % (re1, re2)).findall(" ".join(final_words)) #
    #tickers = re.findall(r'\b$[A-Za-z]{1,5}\b'," ".join(final_words))
    #tickers = re.findall(r'\b\$*[A-Z]{1,5}\b',text)
    #tickers = re.findall(r"\${1}[a-zA-Z]{1,5}|\b\$*[A-Z]{2,5}\b", text)
    #temp = re.findall("(?:(?<=\A)|(?<=\s)|(?<=[$]))([A-Z]{1,5})(?=\s|$|[^a-zA-z])", text)
    temp = re.findall(r'\b\$*[A-Z]{2,5}\b|(?<=\$)[a-zA-Z]{1,5}', text)#re.findall("(?:(?<=\A)|(?<=\s)|(?<=[$]))([a-zA-Z]{1,5})(?=\s|$|[^a-zA-z])", text)
    tickers = []
    #remove WSB, ETF, FD, etc.
    for x in temp:
        if x.upper() not in false_pos and x.lower() not in stop_words:
            tickers.append(x.upper())
    #compare to list of stock tickers
    return list(set(tickers))