__author__ = 'jerry'

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
        return play_time(self._play_data)

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
    def play_text(self):
        return self._play_data['playText']