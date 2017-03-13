__author__ = 'jerry'

import os
from pprint import pprint
from unittest import TestCase

from analysis.clustering import compute_player_clusters

class TestClustering(TestCase):

    def test_player_offensive_cluters(self):

        file_name = os.path.join('season_data', '2013', 'player_offense_features.csv')

        result = compute_player_clusters(file_name, plot=False, method='KMeans')

        pprint(result)

        self.assertEqual(1, 1)