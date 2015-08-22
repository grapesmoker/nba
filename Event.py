__author__ = 'jerry'

import datetime as dt

from settings import pbp
from utils import play_time

from Player import Player


class Event:

    _coll = pbp

    _event_ids = {
        'Starting Lineup': 0,
        'Free Throw Made': 1,
        'Free Throw Missed': 2,
        'Field Goal Made': 3,
        'Field Goal Missed': 4,
        'Offensive Rebound': 5,
        'Defensive Rebound': 6,
        'Turnover': 7,
        'Foul': 8,
        'Violation': 9,
        'Substitution': 10,
        'Timeout': 11,
        'Jump Ball': 12,
        'Start Period': 14,
        'End Period': 15,
    }

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
            return coords['x'], coords['y']
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

    @property
    def play_type(self):
        if 'name' in self._play_data['playEvent']:
            return self._play_data['playEvent']['name']
        else:
            return self.play_text

    @property
    def play_type_id(self):
        return self._play_data['playEvent']['playEventId']

    @property
    def is_field_goal_made(self):
        return self.play_type_id == self.__class__._event_ids['Field Goal Made']

    @property
    def is_field_goal_missed(self):
        return self.play_type_id == self.__class__._event_ids['Field Goal Missed']

    @property
    def is_turnover(self):
        return self.play_type_id == self.__class__._event_ids['Turnover']

    @property
    def is_dreb(self):
        return self.play_type_id == self.__class__._event_ids['Defensive Rebound']

    @property
    def is_oreb(self):
        return self.play_type_id == self.__class__._event_ids['Offensive Rebound']

    @property
    def is_free_throw_made(self):
        return self.play_type_id == self.__class__._event_ids['Free Throw Made']

    @property
    def is_free_throw_missed(self):
        return self.play_type_id == self.__class__._event_ids['Free Throw Missed']

    @property
    def is_foul(self):
        return self.play_type_id == self.__class__._event_ids['Foul']

    @property
    def is_violation(self):
        return self.play_type_id == self.__class__._event_ids['Violation']

    @property
    def is_substitution(self):
        return self.play_type_id == self.__class__._event_ids['Substitution']

    @property
    def is_timeout(self):
        return self.play_type_id == self.__class__._event_ids['Timeout']

    @property
    def shot_made_by(self):
        if self.is_field_goal_made:
            return self.players[0]
        else:
            return None

    @property
    def shot_missed_by(self):
        if self.is_field_goal_missed:
            return self.players[0]
        else:
            return None

    @property
    def assisted_by(self):
        if self.is_field_goal_made and len(self.players) == 2:
            return self.players[1]
        else:
            return None

    @property
    def stolen_by(self):
        if self.is_turnover and len(self.players) == 2:
            return self.players[1]
        else:
            return None

    @property
    def rebounded_by(self):
        if self.is_dreb or self.is_oreb:
            return self.players[0]
        else:
            return None

    @property
    def free_throw_made_by(self):
        if self.is_free_throw_made:
            return self.players[0]
        else:
            return None

    @property
    def free_throw_made_by(self):
        if self.is_free_throw_missed:
            return self.players[0]
        else:
            return None




