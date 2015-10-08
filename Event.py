__author__ = 'jerry'

import datetime as dt

from settings import pbp

from Player import Player
from scipy.spatial.distance import euclidean


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
        self._id = int(self._play_data['playId'])

    @property
    def play_time(self):

        minutes = int(self._play_data['time']['minutes'])
        seconds = float(self._play_data['time']['seconds'])
        period = int(self._play_data['period'])

        if period < 5:
            q_start_time = dt.timedelta(minutes=(period - 1) * 12)
            time_in_quarter = dt.timedelta(minutes=12) - dt.timedelta(minutes=minutes, seconds=seconds)
        else:
            q_start_time = dt.timedelta(minutes=48 + (period - 5) * 5)
            time_in_quarter = dt.timedelta(minutes=5) - dt.timedelta(minutes=minutes, seconds=seconds)

        return q_start_time + time_in_quarter

    @property
    def time_remaining(self):
        return 0
        #return dt.timedelta(minutes=((4 - int(self._play_data['period'])) * 12 + int(self._play_data['time']['minutes'])),
        #                seconds=int(float(self._play_data['time']['seconds'])))

    @property
    def id(self):
        return int(self._id)

    @property
    def event_id(self):
        return self._id

    @property
    def players(self):
        result = []
        for player in self._play_data['players']:
            event_player = Player(player['playerId'])
            if event_player.id is not None:
                result.append(event_player)
        return result

    @property
    def shot_coordinates(self):
        coords = self._play_data['shotCoordinates']
        if coords != {}:
            return coords['x'], coords['y'] + 5.25
        else:
            return None

    @property
    def shot_x(self):
        coords = self._play_data['shotCoordinates']
        if coords != {}:
            return coords['x']

    @property
    def shot_y(self):
        coords = self._play_data['shotCoordinates']
        if coords != {}:
            return coords['y'] + 5.25

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

        if interval[1] >= self.play_time >= interval[0]:
            return True
        else:
            return False

    def __cmp__(self, other):

        if self.play_time == other.play_time:
            if self.id == other.id:
                return 0
            elif self.is_substitution and not other.is_substitution:
                return 1
            elif other.is_substitution and not self.is_substitution:
                return -1
            elif self.id < other.id:
                return -1
            elif self.id > other.id:
                return 1

        elif self.play_time < other.play_time:
            return -1
        elif self.play_time > other.play_time:
            return 1

        # if self.event_id == other.event_id:
        #     return 0
        # elif self.event_id < other.event_id:
        #     return -1
        # elif self.event_id > other.event_id:
        #     return 1

    def __str__(self):
        return '<{0}: {1}>'.format(str(self.play_time), self.play_text)

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
    def is_technical(self):
        if self.is_foul and self._play_data['playEvent']['playDetail']['name'].find('Technical') > -1:
            return True
        else:
            return False

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
    def is_jump_ball(self):
        return self.play_type_id == self.__class__._event_ids['Jump Ball']

    @property
    def is_start_period(self):
        return self.play_type_id == self.__class__._event_ids['Start Period']

    def reset_clock(self, current_shot_clock):
        if self.is_dreb or self.is_field_goal_made or self.is_oreb or self.is_turnover:
            return 24.0
        elif self.is_foul and current_shot_clock < 14.0 and self.play_time < dt.timedelta(minutes=11, seconds=46):
            return 14.0
        else:
            return

    @property
    def is_three_pointer(self):
        x, y = self.shot_coordinates
        if euclidean((x, y), (0, 5.25)) > 23.75:
            return True
        else:
            if abs(y) <= 14.0 and abs(x) >= 22.0:
                return True
            else:
                return False


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
    def turned_over_by(self):
        if self.is_turnover and len(self.players) >= 1:
            return self.players[0]
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
        if (self.is_dreb or self.is_oreb) and len(self.players) >= 1:
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
    def free_throw_missed_by(self):
        if self.is_free_throw_missed:
            return self.players[0]
        else:
            return None


