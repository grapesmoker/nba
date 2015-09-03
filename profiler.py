#!/usr/bin/env python

import pymongo
import numpy as np

from Game import Game
from Player import Player
from Team import Team
from Season import Season

from pprint import pprint
from utils import compute_ts_length, pretty_print_times
from analysis import regression
from analysis.features import player_ocluster_features
from settings import players

def test_single_game_rapm():

    game = Game(1349547)
    team = game.home_team
    
    print game

    regression.regress_lineups_single_game(game, team)

def test_single_lineup():

    game = Game(1349077)

    jcrawford = Player(3388)
    mbarnes = Player(168051)
    jjredick = Player(172643)
    rhollins = Player(177575)
    bgriffin = Player(399725)
    jdudley = Player(241712)
    djordan = Player(398142)
    cpaul = Player(229598)

    players = [jjredick, cpaul, bgriffin, djordan, jdudley]

    timestream = game.time_by_lineup(players)
    box_score = game.stats_by_lineup(players)

    print timestream
    pprint(box_score.__dict__)

def test_player_time():

    game = Game(1349050)

    quarter_plays = sorted([ev for ev in game.events if ev.period == 1], reverse=True)
    for play in quarter_plays:
        print play, play.event_id
    game.quarter_enders()[1]

    ev1 = quarter_plays[5]
    ev2 = quarter_plays[7]
    #import pdb; pdb.set_trace();
    # print ev1, ev1.id
    # print ev2, ev2.id
    #
    # print ev1 > ev2
    # print ev1.__cmp__(ev2)

    player = Player(3102)

    sh = player.time_on_court(game, recompute=True)
    print '{} in {}'.format(player, game)
    print 'minutes played: {0:2.3f}'.format(compute_ts_length(sh) / 60.0)
    pretty_print_times(sh)

def test_features():

    season = Season(2013)
    player = Player(399725)

    features = player_ocluster_features(player, season)

def test_all_player_features(self):

    season = Season(2013)

    all_players = players.find({}).sort('id', pymongo.ASCENDING)
    offensive_features = []

    for player_data in all_players:
        player = Player(player_data['id'])
        print 'Extracting offensive features for {} from the {}'.format(player, season)
        features = player_ocluster_features(player, season)
        offensive_features.append(features)

    offensive_features = np.array(offensive_features)

if __name__ == '__main__':
    #test_single_lineup()
    test_features()
