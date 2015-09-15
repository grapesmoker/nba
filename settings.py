__author__ = 'jerry'

import pymongo

base = 'http://data.nba.com/json/cms/noseason'
cnn_base = 'http://data.sportsillustrated.cnn.com/jsonp/basketball/nba/'
si_base = 'http://www.si.com/nba/'

# hook up to mongodb
conn = pymongo.MongoClient('localhost', 27017)
db = conn.db

# set up collections
games = db.games
boxscores = db.boxscores
players = db.players
teams = db.teams
pbp = db.pbp
odds = db.odds