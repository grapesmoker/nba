__author__ = 'jerry'

import re

from pprint import pprint

empty_team_boxscore = {
    'three_point_field_goals': {
        'attempted': 0,
        'percentage': 0.0,
        'made': 0,
    },
    'points_in_paint': 0,
    'jumpshots': 0,
    'free_throws': {
        'attempted': 0,
        'percentage': 0.0,
        'made': 0
    },
    'hooks': 0,
    'field_goals': {
        'attempted': 0,
        'percentage': 0.0,
        'made': 0,
    },
    'ejections': {
        'player':0,
        'coach': 0,
    },
    'defensive_3_seconds': 0,
    'disqualifications': 0,
    'personal_fouls': 0,
    'technical_fouls': {
        'player': 0,
        'coach': 0,
        'bench': 0,
        'team': 0,
    },
    'timeouts_remaining': {},
    'second_chance_points': 0,
    'tipins': 0,
    'dunks': 0,
    'layups': 0,
    'assists': 0,
    'blockedShots': 0,
    'rebounds': {
        'offensive': 0,
        'defensive': 0,
        'team_defensive': 0,
        'team_offensive': 0,
        'team': 0,
        'total': 0,
        'dead_ball': 0,
    },
    'fast_break_points': 0,
    'steals': 0,
    'turnovers': {
        'total': 0,
        'team': 0,
    },
    'points_off_turnovers': 0,
    'flagrant_fouls': 0,
    'biggest_lead': 0,
    'points': 0,
    'points_against': 0,
    'minutes': 0,
}

empty_player_boxscore = {
    'three_point_fieldGoals': {
        'attempted': 0,
        'percentage': 0.0,
        'made': 0,
    },
    'free_throws': {
        'attempted': 0,
        'percentage': 0.0,
        'made': 0
    },
    'field_goals': {
        'attempted': 0,
        'percentage': 0.0,
        'made': 0,
    },
    'player': {
        'id': 0,
        'last_name': '',
        'first_name': '',
        'uniform': 0,
    },
    'is_disqualification': False,
    'plus_minus': 0,
    'is_ejected': False,
    'is_game_played': True,
    'is_game_started': False,
    'personal_fouls': 0,
    'technical_fouls': 0,
    'assists': 0,
    'blocked_shots': 0,
    'rebounds': {
        'offensive': 0,
        'defensive': 0,
        'total': 0,
    },
    'fast_break_points': 0,
    'steals': 0,
    'turnovers': 0,
    'points_off_turnovers': 0,
    'flagrant_fouls': 0,
    'total_seconds_played': 0,
    'minutes_played': 0,
    'points': 0,
}

class Boxscore(dict):

    def __init__(self, data):
        super(Boxscore, self).__init__()

        def lowercase_and_uscore(match):
            return '_' + match.group(0).lower()

        for key, value in data.items():
            if key != 'lineups':
                if isinstance(value, int) or isinstance(value, float) or isinstance(value, str) or isinstance(value, bool):
                    new_key = re.sub('([A-Z]|[0-9])', lowercase_and_uscore, key)
                    setattr(self, new_key, value)
                elif isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        new_key = re.sub('[A-Z]', lowercase_and_uscore, key) + '_' + \
                                  re.sub('[A-Z]', lowercase_and_uscore, subkey)
                        setattr(self, new_key, subvalue)
                else:
                    pprint(data)
                    raise TypeError('Unknown type encountered in JSON!')

    def add_dicts(self_dict, other_dict):
        pass


class PlayerBoxscore(Boxscore):

    def __init__(self, data=None):

        if not data:
            data = empty_player_boxscore

        super(PlayerBoxscore, self).__init__(data)

    def __add__(self, other):

        if isinstance(self, PlayerBoxscore) and isinstance(other, PlayerBoxscore):
            retval = PlayerBoxscore(empty_player_boxscore)
            for key in self.__dict__:
                newval = getattr(self, key)
                if key in other.__dict__:
                    if key == 'player_player_id':
                        setattr(retval, key, newval)
                    elif isinstance(newval, int) or isinstance(newval, float):
                        newval += float(getattr(other, key))
                        setattr(retval, key, newval)
                    elif isinstance(newval, str):
                        setattr(retval, key, newval)
                else:
                    setattr(retval, key, newval)
            return retval
        else:
            raise NotImplementedError()


class TeamBoxscore(Boxscore):

    def __init__(self, data=None):

        if not data:
            data = empty_team_boxscore

        super(TeamBoxscore, self).__init__(data)

    def __add__(self, other):

        if isinstance(self, TeamBoxscore) and isinstance(other, TeamBoxscore):
            retval = TeamBoxscore(empty_team_boxscore)
            for key in self.__dict__:
                newval = getattr(self, key)
                if key in other.__dict__:
                    if key == 'player_player_id':
                        setattr(retval, key, newval)
                    elif isinstance(newval, int) or isinstance(newval, float):
                        newval += float(getattr(other, key))
                        setattr(retval, key, newval)
                    elif isinstance(newval, str):
                        setattr(retval, key, newval)
                else:
                    setattr(retval, key, newval)
            return retval
        else:
            raise NotImplementedError()

    @property
    def plus_minus(self):
        return self.points - self.points_against