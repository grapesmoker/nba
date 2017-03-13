__author__ = 'jerry'

from unittest import TestCase

from game import Player
from game import Game

from utils.misc import compute_ts_length


class TestPlayer(TestCase):

    def test_player_time_on_court(self):

        player = Player.Player(399725)
        game = Game.Game(1349077)

        time_on_court = player.time_on_court(game, recompute=True)

        print compute_ts_length(time_on_court)

        self.assertEqual(int(round(compute_ts_length(time_on_court))), 2409)
