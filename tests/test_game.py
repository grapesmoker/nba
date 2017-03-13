__author__ = 'jerry'

from game.Game import Game
from game.Team import Team
from game.Player import Player
from unittest import TestCase

from pprint import pprint


class GameTest(TestCase):

    def setUp(self):
        self.game = Game(1349077)

    def test_get_team_stats_by_time(self):

        team = Team(12)

        players = [Player(399725), Player(3085)]
        timestream = self.game.multiple_player_overlap(players)[0]
        stats = self.game.team_stats_by_time(team, timestream)

        pprint(stats.__dict__)

        self.assertEqual(stats.assists, 13)
        self.assertEqual(stats.field_goals_attempted, 40)
        self.assertEqual(stats.field_goals_made, 18)

