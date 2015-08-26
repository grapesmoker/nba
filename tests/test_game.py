__author__ = 'jerry'

from Game import Game
from Team import Team
from unittest import TestCase

from pprint import pprint

class GameTest(TestCase):

    def setUp(self):
        self.game = Game(1349077)

    def test_game_init(self):

        pass

    def test_get_team_stats_by_time(self):

        team = Team(12)

        players = self.game.quarter_starters()[1][0:2]
        timestream = self.game.multiple_player_overlap(players)
        stats = self.game.team_stats_by_time(team, timestream)

        pprint(stats.__dict__)

        self.assertEqual(stats.assists, 13)
        self.assertEqual(stats.field_goals_attempted, 40)
        self.assertEqual(stats.field_goals_made, 18)

