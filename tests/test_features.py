__author__ = 'jerry'

import datetime as dt
import pymongo
import numpy as np
import os

from unittest import TestCase

from Game import Game
from Player import Player
from Team import Team
from Season import Season

from settings import players

from analysis.features import *
from analysis.clustering import *

class TestFeatures(TestCase):

    def test_player_ocluster_features(self):

        season = Season(2013)
        player = Player(399725)

        features = player_ocluster_features(player, season)

        self.assertEqual(len(features), 7)
        self.assertEqual(int(features[0]), 399725)
        self.assertAlmostEqual(round(features[1], 2), 19.2, delta=0.05)
        self.assertAlmostEqual(round(features[2], 3), 0.583, delta=0.05)
        self.assertAlmostEqual(round(features[3], 2), 7.7, delta=0.05)
        self.assertAlmostEqual(round(features[4], 2), 29.0, delta=0.5)
        self.assertAlmostEqual(round(features[5], 2), 114, delta=0.5)

    def test_player_dcluster_features(self):

        season = Season(2013)
        player = Player(399725)

        features = player_dcluster_features(player, season)
        print features
        self.assertEqual(1, 1)

    def test_all_player_features(self):

        season = Season(2013)

        all_players = players.find({}).sort('id', pymongo.ASCENDING)
        offensive_features = []
        defensive_features = []

        for player_data in all_players:
            player = Player(player_data['id'])
            print 'Extracting offensive features for {} from the {}'.format(player, season)
            o_features = player_ocluster_features(player, season)
            print 'Extracting defensive features for {} from the {}'.format(player, season)
            d_features = player_dcluster_features(player, season)
            offensive_features.append(o_features)
            defensive_features.append(d_features)

        offensive_features = np.array(offensive_features)
        defensive_features = np.array(defensive_features)

        o_features_file = os.path.join('season_data', '2013', 'player_offense_features.csv')
        d_features_file = os.path.join('season_data', '2013', 'player_defense_features.csv')

        o_header = 'id,ast_pct,ts_pct,orb_pct,usg,ortg,mp_pct'
        d_header = 'id,blk_pct,stl_pct,drb_pct,drtg,pf_pct,mp_pct'

        np.savetxt(o_features_file, offensive_features, delimiter=',', header=o_header)
        np.savetxt(d_features_file, defensive_features, delimiter=',', header=d_header)

        self.assertTrue(os.path.exists(o_features_file))
        self.assertTrue(os.path.exists(d_features_file))

    def test_team_ocluster_features(self):

        season = Season(2013)
        team = Team(12)

        features = team_ocluster_features(team, season)
        print features
        self.assertEqual(1, 1)

    def test_team_dcluster_features(self):

        season = Season(2013)
        team = Team(12)

        features = team_dcluster_features(team, season)
        print features
        self.assertEqual(1, 1)

    def test_construct_global_features(self):

        season = Season(2013)

        construct_global_features(season)

        self.assertEqual(1, 1)

