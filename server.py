#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tweepy, time, sys, os, json
import tldextract
import logging
from ConfigParser import SafeConfigParser
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from tldextract.tldextract import LOG


# Our name
BOT_NAME = '@agolobot'

# A list of sites never to summarize
# Needs to be kept synchronized with https://github.com/premgane/agolo-slackbot/blob/master/blacklisted-sites.js
BLACKLISTED_SITES = set([
  'agolo.com',
  'youtube',
  'twitter.com',
  'mail.google',
  'imgur.com',
  'bit.ly',
  'tinyurl',
  'vine'
])

logging.basicConfig(level=logging.WARN)

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

# Given a string, which is presumably a URL, check whether it appears in the blacklist
def appearsInBlacklist(url):
	extracted = tldextract.extract(url)._asdict()

	subd = ''
	if 'subdomain' in extracted:
		subd = extracted['subdomain']

	dom = ''
	if 'domain' in extracted:
		dom = extracted['domain']

	tld = ''
	if 'suffix' in extracted:
		tld = extracted['suffix']

	if (dom in BLACKLISTED_SITES
		or url in BLACKLISTED_SITES
		or '.'.join([subd, dom, tld]) in BLACKLISTED_SITES
		or '.'.join([subd, dom]) in BLACKLISTED_SITES
		or '.'.join([dom, tld]) in BLACKLISTED_SITES
		or '.'.join([dom]) in BLACKLISTED_SITES):
		return True

	return False


def parseTweet(tweet):
	urls = tweet.urls
	for urlObject in urls:
		url = urlObject['expanded_url']

		if not appearsInBlacklist(url):
			handle = '@' + tweet.full.get('user', {}).get('screen_name', '')
			api.update_status(url + ' ' + handle, in_reply_to_status_id = tweet.full['id'])
			#api.update_status(url)

#Tweet class with all the information we need for this program (Hashtags and the actual tweet text)
class Tweet:
	text = str()
	hashtags = []
	urls = []
	full = {}

	def __init__(self, json):
		self.text = json.get('text', '')
		self.hashtags = json.get('entities', {}).get('hashtags', [])
		self.urls = json.get('entities', {}).get('urls', [])
		self.full = json

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
	stream.filter(track=[BOT_NAME])

