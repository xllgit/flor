#!/usr/bin/env python3
import pandas as pd
import numpy as np
import os, pickle
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.externals import joblib
from shared import params, relevant_attributes

abspath = os.path.dirname(os.path.abspath(__file__))

tweet_df = pd.read_csv(abspath + '/training_tweets.csv', **params)

# Select a relevant subset of features
tweet_df = tweet_df[relevant_attributes]

# Convert string country code to integer country code
country_codes = set([i for i in tweet_df["code"]])
country_dict = {}
for idx, code in enumerate(country_codes):
    country_dict[code] = idx

with open(abspath + '/country_dict.pkl', 'wb') as f:
	pickle.dump(country_dict, f)
    
def convert_to_int(country_string):
    return country_dict[country_string]

tweet_df["code"] = tweet_df["code"].apply(convert_to_int)

## Convert tweet to bag of words for learning

# Tokenize Text
count_vect = CountVectorizer()
X_train = count_vect.fit_transform(tweet_df["tweet"])

with open(abspath + '/vectorizer.pkl', 'wb') as f:
	pickle.dump(count_vect, f)

X_train_label = np.array(tweet_df["code"].data)

# Train a classifier
clf = MultinomialNB().fit(X_train, X_train_label)
joblib.dump(clf, abspath + '/classifier.pkl')