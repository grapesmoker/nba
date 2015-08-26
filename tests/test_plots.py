__author__ = 'jerry'

import os

from unittest import TestCase

from Player import Player
from Game import Game
from Season import Season

class PlotsTest(TestCase):

    def test_player_plot(self):

        player1 = Player(399725)
        player2 = Player(172643)
        game = Game(1349077)

        player1.shot_chart(game, overplot_shots=True)
        player2.shot_chart(game, overplot_shots=True)

        player1_plotfile = os.path.join('plots', 'players', 'Blake_Griffin_shots_2013-10-29 19:30:00_Lakers_vs_Clippers.pdf')
        player2_plotfile = os.path.join('plots', 'players', 'J.J._Redick_shots_2013-10-29 19:30:00_Lakers_vs_Clippers.pdf')

        self.assertEqual(os.path.exists(player1_plotfile), True)
        self.assertEqual(os.path.exists(player2_plotfile), True)

    def test_player_multi_game_plot(self):

        player1 = Player(399725)
        season = Season(2013)

        player1.multi_game_shot_chart(season.games)

        self.assertEqual(1, 1)