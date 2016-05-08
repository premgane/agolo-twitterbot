#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tweepy, time, sys, os, json
import tldextract
import logging
import requests
from ConfigParser import SafeConfigParser
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from tldextract.tldextract import LOG
from PIL import Image, ImageFont, ImageDraw
import textwrap

# Our name
BOT_NAME = '@agolobot'

# The length we want the summary to be
SUMMARY_LENGTH = 5

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

TWITTER_LIMIT = 140

parser = SafeConfigParser()
parser.read('secrets.cfg')

# Twitter credentials
CONSUMER_KEY = parser.get('Twitter', 'CONSUMER_KEY')
CONSUMER_SECRET = parser.get('Twitter', 'CONSUMER_SECRET')
ACCESS_KEY = parser.get('Twitter', 'ACCESS_KEY')
ACCESS_SECRET = parser.get('Twitter', 'ACCESS_SECRET')

# Agolo credentials
AGOLO_URL = parser.get('Agolo', 'URL')
AGOLO_KEY = parser.get('Agolo', 'Key')

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


def convertUrlToArticle(url):
	return {
			'type':'article',
			'metadata':{},
			'url': url
			}

def summarize(urls):
	articles = []
	for url in urls:
		articles.append(convertUrlToArticle(url))
	
	payload = {
		"summary_length": SUMMARY_LENGTH,
		'articles': articles
	}

	headers = {
		"Content-Type": "application/json",
		"Ocp-Apim-Subscription-Key": AGOLO_KEY
	}

	r = requests.post(AGOLO_URL, data = json.dumps(payload), headers = headers)
	return r.json()

# Given a summary object response from Agolo, convert to a bullet point list
def summaryToString(summaryObj):
	result = []
	for article in summaryObj['summary']:
		for sentence in article['sentences']:
			result.append(sentence)

	print '\n\n'.join(result)
	return '\n\n'.join(result)


def textToImage(text):
	image = Image.new("RGBA", (1800,1647), (255,255,255))
	draw = ImageDraw.Draw(image)
	fontsize = 72
	font = ImageFont.truetype("resources/helveticaneue-light.ttf", fontsize)

	margin = offset = 40
	for textLine in text.split('\n'):
		if textLine.lstrip().rstrip():
			textLine = u"\u2022" + ' ' + textLine

		for line in textwrap.wrap(textLine, width=50):
			draw.text((margin, offset), line, font=font, fill="#111")
			offset += font.getsize(line)[1]

	# draw.text((10, 0), text, (0,0,0), font=font)
	img_resized = image.resize((1180,1080), Image.ANTIALIAS)
	return img_resized

def parseTweet(tweet):
	urls = tweet.urls
	for urlObject in urls:
		url = urlObject['expanded_url']

		articles = []
		if not appearsInBlacklist(url):
			articles.append(url)	

		summary = summarize(articles)
		handle = '@' + tweet.full.get('user', {}).get('screen_name', '')

		summaryAsString = summaryToString(summary)

		image = textToImage(summaryAsString)
		FILENAME = 'summ.png'
		image.save(FILENAME, 'PNG')

		title =  summary.get('title', '')
		if len(title) + len(handle) + 3 > TWITTER_LIMIT:
			title = u"\u201C" + title[:TWITTER_LIMIT - len(handle) - 4] + u"\u2026" + u"\u201D"
		else:
			title = u"\u201C" + title[:TWITTER_LIMIT - len(handle) - 3] + u"\u201D"

		replyText = title + ' ' + handle
		print replyText
		# api.update_status(replyText, in_reply_to_status_id = tweet.full['id'])
		api.update_with_media(FILENAME, replyText, in_reply_to_status_id = tweet.full['id'])

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

