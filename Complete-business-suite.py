__author__ = "whackadoodle"

import sqlite3
import codecs
import nltk
import string
from collections import Counter
from pprint import pprint
import yaml
import sys
import os
import re



#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxSentiment Analysisxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

class Splitter(object):

    def __init__(self):
        self.nltk_splitter = nltk.data.load('tokenizers/punkt/english.pickle')
        self.nltk_tokenizer = nltk.tokenize.TreebankWordTokenizer()

    def split(self, text):
        
        sentences = self.nltk_splitter.tokenize(text)
        tokenized_sentences = [self.nltk_tokenizer.tokenize(sent) for sent in sentences]
        return tokenized_sentences


class POSTagger(object):

    def __init__(self):
        pass
        
    def pos_tag(self, sentences):
        

        pos = [nltk.pos_tag(sentence) for sentence in sentences]
        #adapt format
        pos = [[(word, word, [postag]) for (word, postag) in sentence] for sentence in pos]
        return pos

class DictionaryTagger(object):

    def __init__(self, dictionary_paths):
        files = [open(path, 'r') for path in dictionary_paths]
        dictionaries = [yaml.load(dict_file) for dict_file in files]
        map(lambda x: x.close(), files)
        self.dictionary = {}
        self.max_key_size = 0
        for curr_dict in dictionaries:
            for key in curr_dict:
                if key in self.dictionary:
                    self.dictionary[key].extend(curr_dict[key])
                else:
                    self.dictionary[key] = curr_dict[key]
                    #self.max_key_size = max(self.max_key_size, len(key))

    def tag(self, postagged_sentences):
        return [self.tag_sentence(sentence) for sentence in postagged_sentences]

    def tag_sentence(self, sentence, tag_with_lemmas=False):
        
        tag_sentence = []
        N = len(sentence)
        if self.max_key_size == 0:
            self.max_key_size = N
        i = 0
        while (i < N):
            j = min(i + self.max_key_size, N) #avoid overflow
            tagged = False
            while (j > i):
                expression_form = ' '.join([word[0] for word in sentence[i:j]]).lower()
                expression_lemma = ' '.join([word[1] for word in sentence[i:j]]).lower()
                if tag_with_lemmas:
                    literal = expression_lemma
                else:
                    literal = expression_form
                if literal in self.dictionary:
                    #self.logger.debug("found: %s" % literal)
                    is_single_token = j - i == 1
                    original_position = i
                    i = j
                    taggings = [tag for tag in self.dictionary[literal]]
                    tagged_expression = (expression_form, expression_lemma, taggings)
                    if is_single_token: #if the tagged literal is a single token, conserve its previous taggings:
                        original_token_tagging = sentence[original_position][2]
                        tagged_expression[2].extend(original_token_tagging)
                    tag_sentence.append(tagged_expression)
                    tagged = True
                else:
                    j = j - 1
            if not tagged:
                tag_sentence.append(sentence[i])
                i += 1
        return tag_sentence

def value_of(sentiment):
    if sentiment == 'positive': return 1
    if sentiment == 'negative': return -1
    return 0

def sentence_score(sentence_tokens, previous_token, acum_score):    
    if not sentence_tokens:
        return acum_score
    else:
        current_token = sentence_tokens[0]
        tags = current_token[2]
        token_score = sum([value_of(tag) for tag in tags])
        if previous_token is not None:
            previous_tags = previous_token[2]
            if 'inc' in previous_tags:
                token_score *= 2.0
            elif 'dec' in previous_tags:
                token_score /= 2.0
            elif 'inv' in previous_tags:
                token_score *= -1.0
        return sentence_score(sentence_tokens[1:], current_token, acum_score + token_score)

def sentiment_score(review):
    return sum([sentence_score(sentence, None, 0.0) for sentence in review])

#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxOutput DBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
conn1 = sqlite3.connect('output.db')
conn1.text_factory = str
c1 = conn1.cursor()


def createTweetsTable():
    c1.execute('CREATE TABLE results (Topic TEXT, Total TEXT , Positivity TEXT,Negativity TEXT)')
    conn1.commit()

conn2 = sqlite3.connect('topics-list.db')
conn2.text_factory = str
c2 = conn2.cursor()


def createTopicTable():
    c2.execute('CREATE TABLE results (Topic TEXT)')
    conn2.commit()

conn3 = sqlite3.connect('OS-list.db')
conn3.text_factory = str
c3 = conn3.cursor()
def createOSBrandTable():
    c3.execute('CREATE TABLE OS(OS TEXT,count TEXT)')
    conn3.commit()
    c3.execute('CREATE TABLE Brand(br TEXT,count TEXT)')
    conn3.commit

#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxRankingxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OS_rank = []
Brand_rank = []
cnt = Counter()
OS = {'#android','#ios','#windows','#blackberry'}
Companies = {'#samsung','#apple','#htc','#sony','#blackberry','#microsoft','lg'}

def get_tweets():
    conn = sqlite3.connect("MWC_tweets.db")
    c = conn.cursor()
    conn.text_factory = str
    c.execute("SELECT tweet FROM mwc_tweets")
    _tweets = [r[0] for r in c.fetchall()]
    conn.close()
    return _tweets

def getWordsInTweets(tweets):
    wordList = []
    for (words) in tweets:  
        if(tweets.count(words)>4):
            wordList.extend(words);
    return wordList


def getWordFeatures(wordList):
    #createTopicTable()
    #for word in wordList:
    #   cnt[word] += 1
    
    print "\nPopular topics from the event:\n"
    #for word,count in cnt.most_common(500):
    #   if "mwc" in word:
    #       word = ""

    #   if(word != ""):
    #       print '%s\n' % (word.strip('#'))
    #c2.execute("INSERT INTO results VALUES(?)", [word.strip('#')])
    #conn2.commit()

    for topic in c2.execute("SELECT * from results LIMIT 10"):
        print topic

    #l = cnt.items()
    #l.sort(key = lambda item: item[1])

    wordList = nltk.FreqDist(wordList)
    word_features = wordList.keys()
    #createOSBrandTable()
    print("\n\nOperating Systems:")
    for word in OS:
        OS_rank.append((word,wordList[word]))
    for os,count in sorted(OS_rank,key = lambda item: -item[1]):
        c2.execute("INSERT INTO OS VALUES(?,?)",[os.strip('#'),count])

    for os,count in c2.execute("SELECT * from OS"):
        print os+"\t"+str(count)


    #print OS_rank
        #print "OS\tCount"
        #print os.strip('#')+"\t"+str(count)

    print("\n\nBrands:")
    for word in Companies:
        Brand_rank.append((word,wordList[word]))
    for br,count in sorted(Brand_rank,key = lambda item: -item[1]):
        c2.execute("INSERT INTO Brand VALUES(?,?)",[br.strip('#'),count])
    for br,count in c2.execute("SELECT * from Brand"):
        print br+"\t"+str(count)

        #print Brand.strip('#')+"\t"+str(count)
    #print wordList.most_common(550)
    return word_features



tweets_data = get_tweets()
tweets = []
for (words) in tweets_data:
    words_filtered = [e.lower() for e in words.split() if ( len(e) > 3 and e[0]=='#' )]
    tweets.append(words_filtered)


word_features = getWordFeatures(getWordsInTweets(tweets))
print len(word_features)
print word_features
print topics

tweet = []
pos_count=0
neg_count=0
j = 0
conn = sqlite3.connect("MWC_tweets.db")
c = conn.cursor()
createTweetsTable();
ans='y'
while(ans=='y'):
   text = raw_input("Enter text:")
   tweet = []
   for i in c.execute('select * from mwc_tweets where tweet like ?',('%#'+text+'%',)):
       splitter = Splitter()
       postagger = POSTagger()
       dicttagger = DictionaryTagger([ 'dicts/positive.yml', 'dicts/negative.yml', 'dicts/inc.yml', 'dicts/dec.yml', 'dicts/inv.yml'])
       tweet = i
       print tweet
       splitted_sentences = splitter.split(str(tweet))
       #pprint(splitted_sentences)

       pos_tagged_sentences = postagger.pos_tag(splitted_sentences)
 #      #pprint(pos_tagged_sentences)

       dict_tagged_sentences = dicttagger.tag(pos_tagged_sentences)
        #pprint(dict_tagged_sentences)

    #print("analyzing sentiment...")
       score = sentiment_score(dict_tagged_sentences)
        #print(score)
       if(score>=0):
           pos_count=pos_count+1
       else:
           neg_count=neg_count+1
       j=j+1   
   total_tweets = j
   positive_percentage = (float(pos_count)/float(j))*100
   negative_percentage = (float(neg_count)/float(j))*100
   print "Total: "+str(total_tweets)+" Positivity: "+str(positive_percentage)+" Negativity: "+str(negative_percentage)
   c1.execute("INSERT INTO results VALUES(?, ?, ?, ?)", [text,total_tweets,positive_percentage,negative_percentage])
   conn1.commit()
   ans=raw_input("Do you want to continue:")
test = raw_input("\n\nEnter the commodity you're interested in:")

if(test=="all"):
    for val1,val2,val3,val4 in c1.execute("SELECT * from results"):
        print "\n\nCommodity:"+val1
        print "Count:"+str(val2)
        print "Positivity:"+str(val3)+"%"
        print "Negativity:"+str(val4)+"%"
else:
    for val1,val2,val3,val4 in c1.execute("SELECT * from results where Topic like ?",(test,)):
        print "\n\nCommodity:"+val1
        print "Count:"+str(val2)
        print "Positivity:"+str(val3)+"%"
        print "Negativity:"+str(val4)+"%"
c.close()
conn.close()
