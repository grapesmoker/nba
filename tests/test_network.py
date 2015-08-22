__author__ = 'jerry'

import datetime as dt

from unittest import TestCase
from network import get_games

class NetworkTest(TestCase):

    def test_get_games(self):

        date = dt.date(2013, 10, 29)
        game_ids = get_games(date)

        self.assertEqual(len(game_ids), 3)
        self.assertEqual(game_ids, [1349077, 1349547, 1349074])