__author__ = 'jerry'

import datetime as dt

from settings import pbp
from utils import play_time

from Player import Player


class Event:

    _coll = pbp

    def __init__(self, play_data):
        self._coll = self.__class__._coll
        self._play_data = play_data

    @property
    def play_time(self):
        return dt.timedelta(minutes=((4 - int(self._play_data['period'])) * 12 + int(self._play_data['time']['minutes'])),
                        seconds=int(float(self._play_data['time']['seconds'])))

    @property
    def id(self):
        return int(self._play_data['id'])

    @property
    def players(self):
        return [Player(player['playerId']) for player in self._play_data['players']]

    @property
    def shot_coordinates(self):
        coords = self._play_data['shotCoordinates']
        if coords != {}:
            return (coords['x'], coords['y'])
        else:
            return None

    @property
    def id(self):
        return self._play_data['playId']

    @property
    def period(self):
        return self._play_data['period']

    @property
    def play_text(self):
        return self._play_data['playText']

    def is_in_interval(self, interval):

        if interval[1] <= self.play_time <= interval[0]:
            return True
        else:
            return False


    def __cmp__(self, other):
        if self.play_time == other.play_time:
            return 0
        elif self.play_time < other.play_time:
            return -1
        elif self.play_time > other.play_time:
            return 1

    def __str__(self):
        return '<{0}>'.format(str(self.play_time))

    def __repr__(self):
        return self.__str__()