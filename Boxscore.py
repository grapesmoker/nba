__author__ = 'jerry'

import re

empty_team_boxscore = {
    'threePointFieldGoals': {
        'attempted': 0,
        'percentage': 0.0,
        'made': 0,
    },
    'points_in_paint': 0,
    'jumpshots': 0,
    'freeThrows': {
        'attempted': 0,
        'percentage': 0.0,
        'made': 0
    },
    'hooks': 0,
    'fieldGoals': {
        'attempted': 0,
        'percentage': 0.0,
        'made': 0,
    },
    'ejections': {
        'player':0,
        'coach': 0,
    },
    'defensive3seconds': 0,
    'disqualifications': 0,
    'personalFouls': 0,
    'technicalFouls': {
        'player': 0,
        'coach': 0,
        'bench': 0,
        'team': 0,
    },
    'timeoutsRemaining': {},
    'secondChancePoints': 0,
    'tipins': 0,
    'dunks': 0,
    'layups': 0,
    'assists': 0,
    'blockedShots': 0,
    'rebounds': {
        'offensive': 0,
        'defensive': 0,
        'teamDefensive': 0,
        'teamOffensive': 0,
        'team': 0,
        'total': 0,
        'deadBall': 0,
    },
    'fastBreakPoints': 0,
    'steals': 0,
    'turnovers': {
        'total': 0,
        'team': 0,
    },
    'pointsOffTurnovers': 0,
    'flagrantFouls': 0,
    'biggestLead': 0,
    'points': 0,
    'pointsAgainst': 0,
    'minutes': 0,
}

empty_player_boxscore = {
    'threePointFieldGoals': {
        'attempted': 0,
        'percentage': 0.0,
        'made': 0,
    },
    'freeThrows': {
        'attempted': 0,
        'percentage': 0.0,
        'made': 0
    },
    'fieldGoals': {
        'attempted': 0,
        'percentage': 0.0,
        'made': 0,
    },
    'player': {
        'playerId': 0,
        'lastName': '',
        'firstName': '',
        'uniform': 0,
    },
    'isDisqualification': False,
    'plusMinus': 0,
    'isEjected': False,
    'isGamePlayed': True,
    'isGameStarted': False,
    'personalFouls': 0,
    'technicalFouls': 0,
    'assists': 0,
    'blockedShots': 0,
    'rebounds': {
        'offensive': 0,
        'defensive': 0,
        'total': 0,
    },
    'fastBreakPoints': 0,
    'steals': 0,
    'turnovers': 0,
    'pointsOffTurnovers': 0,
    'flagrantFouls': 0,
    'totalSecondsPlayed': 0,
    'minutesPlayed': 0,
    'points': 0,
}

class Boxscore(dict):

    def __init__(self, data):
        super(Boxscore, self).__init__()

        def lowercase_and_uscore(match):
            return '_' + match.group(0).lower()

        for key, value in data.items():
            if isinstance(value, int) or isinstance(value, float) or isinstance(value, str) or isinstance(value, bool):
                new_key = re.sub('([A-Z]|[0-9])', lowercase_and_uscore, key)
                setattr(self, new_key, value)
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    new_key = re.sub('[A-Z]', lowercase_and_uscore, key) + '_' + \
                              re.sub('[A-Z]', lowercase_and_uscore, subkey)
                    setattr(self, new_key, subvalue)
            else:
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
                if key == 'player_player_id':
                    setattr(retval, key, newval)
                elif isinstance(newval, int) or isinstance(newval, float):
                    newval += getattr(other, key)
                    setattr(retval, key, newval)
                elif isinstance(newval, str):
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
                if key == 'player_player_id':
                    setattr(retval, key, newval)
                elif isinstance(newval, int) or isinstance(newval, float):
                    newval += getattr(other, key)
                    setattr(retval, key, newval)
                elif isinstance(newval, str):
                    setattr(retval, key, newval)
            return retval
        else:
            raise NotImplementedError()

    @property
    def plus_minus(self):
        return self.points - self.points_against