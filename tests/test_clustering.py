__author__ = 'jerry'

import datetime as dt
import pymongo
import numpy as np
import os

from unittest import TestCase
from pprint import pprint

from Game import Game
from Player import Player
from Team import Team
from Season import Season

from settings import players

from analysis.features import player_ocluster_features
from analysis.clustering import compute_player_clusters

class TestClustering(TestCase):

    def test_player_offensive_cluters(self):

        file_name = os.path.join('season_data', '2013', 'player_offense_features.csv')

        result = compute_player_clusters(file_name, plot=False, method='KMeans')

        pprint(result)

        self.assertEqual(1, 1)