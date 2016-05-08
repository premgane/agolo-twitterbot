#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tweepy, time, sys, os
from ConfigParser import SafeConfigParser

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

line = "Test tweet!"
api.update_status(line)