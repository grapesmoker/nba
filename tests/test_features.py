__author__ = 'jerry'

import datetime as dt

from unittest import TestCase

from Game import Game
from Player import Player
from Team import Team
from Season import Season

from analysis.features import player_ocluster_features

class TestFeatures(TestCase):

    def test_player_ocluster_features(self):

        season = Season(2013)
        player = Player(399725)

        features = player_ocluster_features(player, season)

        print features

        self.assertEqual(1, 1)