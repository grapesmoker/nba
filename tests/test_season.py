__author__ = 'jerry'

import datetime as dt

from Season import Season
from Team import Team
from unittest import TestCase

class SeasonTest(TestCase):

    def setUp(self):
        self.season = Season(2013)

    def test_season_init(self):

        self.assertEqual(self.season.season, '2013-2014 NBA Season')
        self.assertEqual(self.season.start_date, dt.datetime(2013, 10, 29, 19, 30))
        self.assertEqual(self.season.end_date, dt.datetime(2014, 4, 15, 20, 0))

    def test_ortg_drtg(self):

        team = Team(6)

        drtg = self.season.drtg(team)
        ortg = self.season.ortg(team)

        print ortg, drtg

        self.assertAlmostEqual(ortg, 111.8, delta=0.5)
        self.assertAlmostEqual(drtg, 109.2, delta=0.5)

