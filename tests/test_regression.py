__author__ = 'jerry'

from unittest import TestCase

from Game import Game
from Player import Player
from Team import Team

from analysis import regression


class TestRegression(TestCase):

    def test_single_game_rapm(self):

        #player1 = Player(399725)
        game = Game(1349077)
        team = Team(12)

        regression.regress_lineups_single_game(game, team)

        self.assertEqual(1, 1)