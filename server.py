#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tweepy, time, sys, os, json
from ConfigParser import SafeConfigParser
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

# Our name
BOT_NAME = '@agolobot'

# A list of sites never to summarize
# Needs to be kept synchronized with https://github.com/premgane/agolo-slackbot/blob/master/blacklisted-sites.js
SITE_BLACKLIST = [
  'agolo.com',
  'youtube',
  'twitter.com',
  'mail.google',
  'imgur.com',
  'bit.ly',
  'tinyurl',
  'vine'
]

parser = SafeConfigParser()
parser.read('secrets.cfg')

#enter the corresponding information from your Twitter application:
CONSUMER_KEY = parser.get('Twitter', 'CONSUMER_KEY')
CONSUMER_SECRET = parser.get('Twitter', 'CONSUMER_SECRET')
ACCESS_KEY = parser.get('Twitter', 'ACCESS_KEY')
ACCESS_SECRET = parser.get('Twitter', 'ACCESS_SECRET')


auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

# line = "Test tweet!"
# api.update_status(line)

def parseTweet(tweet):
	print 'yipee!'

#Tweet class with all the information we need for this program (Hashtags and the actual tweet text)
class Tweet:
    text = str()
	hashtags = []

    def __init__(self, json):
		self.text = json["text"] 
		self.hashtags = json["entities"]["hashtags"]

#Basic listener which parses the json, creates a tweet, and sends it to parseTweet
class TweetListener(StreamListener):
	def on_data(self, data):
		jsonData = json.loads(data)
		tweet = Tweet(jsonData)
		parseTweet(tweet)
		return True

	def on_error(self, status):
		print status


if __name__ == '__main__':
	parsedTweets = 0
	listener = TweetListener()
	stream = Stream(auth, listener)	
	stream.filter(track=[BOT_NAME]) #This will start the stream and make callbacks to the listener for all tweets containing "android"


