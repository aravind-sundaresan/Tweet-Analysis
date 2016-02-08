__author__ = "whackadoodle"

#Storing the streamed tweets in a database

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import sqlite3 
import codecs
import json
import pandas as pd
import matplotlib.pyplot as plt
import re
import string
import pylab

if __name__ == '__main__':


    tweets_data_path = 'MWC.txt'
    tweets = pd.DataFrame()
    i=0
    tweets_data = []
    tweets_file = open(tweets_data_path, "r")

    conn = sqlite3.connect('MWC_tweets.db')
    conn.text_factory = str
    c = conn.cursor()    
    c.execute('CREATE TABLE mwc_tweets (tweet TEXT)')


    for line in tweets_file:
        try:
            tweet = json.loads(line)
            tweets_data.append(tweet)
            
        except:
            continue

    #print tweets_data
    print len(tweets_data)

    tweets['text'] = map(lambda tweet: tweet['text'], tweets_data)
    print len(tweets['text'])
    #print tweets['text'][1].encode('ascii','ignore')
    #tweets_file = codecs.open('MWC-tweets.txt','a','utf8')
    while(i<30991):
        c.execute("INSERT INTO mwc_tweets VALUES(?)", (tweets['text'][i],))
    	i=i+1;		
        conn.commit()

    conn.close()
    #for line in tweets['text']:
		#newline = unicodedata.normalize('NFC', line).encode('UTF-8','ignore')    	
	
