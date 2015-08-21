from __future__ import division

import datetime as dt
from settings import pbp

from itertools import combinations

from Team import Team
from Player import Player
from Event import Event

from utils import recursive_intersect

class NoCollectionError(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

class GameDataError(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

class Game:

    _coll = pbp

    def __init__(self, event_id=None, collection=None):
        if collection is not None:
            self.__class__._coll = collection
            self._coll = collection
        elif self._coll is None:
            if self.__class__._coll is None:
                raise NoCollectionError('Must have a collection in MongoDB!')
            else:
                self._coll = self.__class__._coll

        if event_id is not None:
            self.get_by_event_id(event_id)

    def get_by_event_id(self, event_id):

        data = self._coll.find_one({'league.season.eventType.0.events.0.eventId': event_id})
        self._data = data
        self.set_data(self._data)

    def set_data(self, data):

        # all the actual data is contained in here, so let's just throw away the outer
        # shells of the json
        self._core_data = data['league']['season']['eventType'][0]['events'][0]
        self._date = dt.datetime.strptime(self._core_data['startDate'][0]['full'], '%Y-%m-%dT%H:%M:%S')
        self._teams = self._core_data['teams']
        self._home_team = self._teams[0]
        self._away_team = self._teams[1]
        self._home_boxscore = self._core_data['boxscores'][0]
        self._away_boxscore = self._core_data['boxscores'][1]
        self._pbp = self._core_data['pbp']
        self._events = [Event(play_data) for play_data in self._pbp]

    def __str__(self):
        home_team_name = self._home_team['location'] + ' ' + self._home_team['nickname']
        away_team_name = self._away_team['location'] + ' ' + self._away_team['nickname']
        return '{0} vs {1} on {2!s}'.format(home_team_name, away_team_name, self._date)

    def __repr__(self):
        return self.__str__()

    @property
    def teams(self):
        return self._teams
        
    @property
    def home_team(self):
        return Team(self._home_team['teamId'])
        
    @property
    def away_team(self):
        return Team(self._away_team['teamId'])

    @property
    def home_players(self):
        home_player_ids = [player['player']['playerId'] for player in self._home_boxscore['playerstats']]
        home_players = [Player(id) for id in home_player_ids]
        return home_players

    @property
    def away_players(self):
        away_player_ids = [player['player']['playerId'] for player in self._away_boxscore['playerstats']]
        away_players = [Player(id) for id in away_player_ids]
        return away_players

    def game_players(self, team_id):
        if self._home_team['teamId'] == team_id:
            return self.home_players
        elif self._away_team['teamId'] == team_id:
            return self.away_players
        else:
            raise GameDataError('No such teamId ({0}) for this game!'.format(team_id))

    @property
    def pbp(self):
        return self._pbp

    @property
    def date(self):
        return self._date

    @property
    def home_boxscore(self):
        return self._core_data['boxscores'][0]

    @property
    def away_boxscore(self):
        return self._core_data['boxscores'][1]

    def is_home(self, team):
        if self.home_boxscore['teamId'] == team.id:
            return True
        else:
            return False

    def is_away(self, team):
        if self.away_boxscore['teamId'] == team.id:
            return True
        else:
            return False

    @property
    def home_lineup_combinations(self):
        players = self.home_players
        return combinations(players, 5)

    @property
    def away_lineup_combinations(self):
        players = self.away_players
        return combinations(players, 5)

    @property
    def events(self):
        return self._events

    @property
    def home_possessions(self):

        home_fga = self.home_boxscore['teamStats']['fieldGoals']['attempted']
        home_fgm = self.home_boxscore['teamStats']['fieldGoals']['made']
        home_fta = self.home_boxscore['teamStats']['freeThrows']['attempted']
        home_orb = self.home_boxscore['teamStats']['rebounds']['offensive']
        home_drb = self.home_boxscore['teamStats']['rebounds']['defensive']
        home_tov = self.home_boxscore['teamStats']['turnovers']['total']

        away_fga = self.away_boxscore['teamStats']['fieldGoals']['attempted']
        away_fgm = self.away_boxscore['teamStats']['fieldGoals']['made']
        away_fta = self.away_boxscore['teamStats']['freeThrows']['attempted']
        away_orb = self.away_boxscore['teamStats']['rebounds']['offensive']
        away_drb = self.away_boxscore['teamStats']['rebounds']['defensive']
        away_tov = self.away_boxscore['teamStats']['turnovers']['total']

        home_pos = 0.5 * ((home_fga + 0.4 * home_fta - 1.07 * (home_orb / (home_orb + away_drb)) *
                           (home_fga - home_fgm) + home_tov) +
                          (away_fga + 0.4 * away_fta - 1.07 * (away_orb / (away_orb + home_drb)) *
                           (away_fga - away_fgm) + away_tov))

        return home_pos

    @property
    def away_possessions(self):

        home_fga = self.home_boxscore['teamStats']['fieldGoals']['attempted']
        home_fgm = self.home_boxscore['teamStats']['fieldGoals']['made']
        home_fta = self.home_boxscore['teamStats']['freeThrows']['attempted']
        home_orb = self.home_boxscore['teamStats']['rebounds']['offensive']
        home_drb = self.home_boxscore['teamStats']['rebounds']['defensive']
        home_tov = self.home_boxscore['teamStats']['turnovers']['total']

        away_fga = self.away_boxscore['teamStats']['fieldGoals']['attempted']
        away_fgm = self.away_boxscore['teamStats']['fieldGoals']['made']
        away_fta = self.away_boxscore['teamStats']['freeThrows']['attempted']
        away_orb = self.away_boxscore['teamStats']['rebounds']['offensive']
        away_drb = self.away_boxscore['teamStats']['rebounds']['defensive']
        away_tov = self.away_boxscore['teamStats']['turnovers']['total']

        away_pos = 0.5 * ((away_fga + 0.4 * away_fta - 1.07 * \
                           (away_orb / (away_orb + home_drb)) * \
                           (away_fga - away_fgm) + away_tov) + \
                          (home_fga + 0.4 * home_fta - 1.07 * \
                           (home_orb / (home_orb + away_drb)) * \
                           (home_fga - home_fgm) + home_tov))

        return away_pos

    @property
    def home_drtg(self):
        return 100 * self.away_boxscore['teamStats']['points'] / self.away_possessions

    @property
    def home_ortg(self):
        return 100 * self.home_boxscore['teamStats']['points'] / self.home_possessions

    @property
    def away_drtg(self):
        return 100 * self.home_boxscore['teamStats']['points'] / self.home_possessions

    @property
    def away_ortg(self):
        return 100 * self.away_boxscore['teamStats']['points'] / self.away_possessions

    def player_team(self, player):

        home = [self.home_boxscore['teamId']
                for stat in self.home_boxscore['playerstats']
                if stat['player']['playerId'] == player.id]

        away = [self.away_boxscore['teamId']
                for stat in self.away_boxscore['playerstats']
                if stat['player']['playerId'] == player.id]

        if home != [] and away == []:
            return Team(home[0])
        elif home == [] and away != []:
            return Team(away[0])
        elif home == [] and away == []:
            raise GameDataError('No such player in this game: {}'.format(player))
        elif home != [] and away != []:
            raise GameDataError('Same player {} on two different teams! Something is terribly wrong!'.format(player))

    def player_boxscore(self, player):

        player_stats = [stat for stat in self.home_boxscore['playerstats'] if stat['player']['playerId'] == player.id] + \
                       [stat for stat in self.away_boxscore['playerstats'] if stat['player']['playerId'] == player.id]

        if player_stats != []:
            return player_stats[0]
        else:
            raise GameDataError('No such player in this game: {0}'.format(str(player)))

    def opponent(self, team):

        if self.is_home(team):
            return self.away_team
        elif self.is_away(team):
            return self.home_team
        else:
            raise GameDataError('{} did not participate in {}'.format(team, self))

    def lineup_combinations(self, team_id):
        players = self.game_players(team_id)
        return combinations(players, 5)

    def events_by_player(self, player_id):
        
        def is_player_involved(event, player_id):
            for player in event['players']:
                if player['playerId'] == player_id:
                    return True
            return False

        player_events = [event for event in self._pbp if is_player_involved(event, player_id)]

        return player_events

    def quarter_starters(self):

        starting_lineup = [player[0] for player in
                           [event.players for event in self._events if event.play_text == 'Starting Lineup']]

        quarter_starters = {1: starting_lineup}

        for q in (2, 3, 4):

            quarter_plays = sorted([ev for ev in self._events if ev.period == q], reverse=True)

            players_used = []
            subs_used = []
            i = 0
            done = False

            while i < len(quarter_plays) and not done:
                event = quarter_plays[i]
                players = event.players

                if event.play_text.find('Substitution:') > -1:
                    subbed_in_player = players[0]
                    subs_used.append(subbed_in_player)
                    subbed_out_player = players[1]
                    if subbed_out_player not in players_used:
                        players_used.append(subbed_out_player)
                else:
                    for player in players:
                        if player not in subs_used and player not in players_used:
                            players_used.append(player)

                i += 1
                if len(players_used) == 10:
                    done = True

            quarter_starters[q] = players_used

        return quarter_starters

    @classmethod
    def look_up_game(cls, game_day, team_id):

        game = cls._coll.find_one({'league.season.eventType.0.events.0.startDate.0.month': game_day.month,
                                   'league.season.eventType.0.events.0.startDate.0.year': game_day.year,
                                   'league.season.eventType.0.events.0.startDate.0.date': game_day.day,
                                   '$or': [{'league.season.eventType.0.events.0.teams.0.teamId': team_id},
                                           {'league.season.eventType.0.events.0.teams.1.teamId': team_id}]})
    
        if game is not None:
            return Game(game['league']['season']['eventType'][0]['events'][0]['eventId'])
        else:
            return None

    def multiple_player_overlap(self, players_on, players_off=None):

        player_times = [player.time_on_court(self) for player in players_on]

        shared_times = recursive_intersect(player_times)

        return shared_times

    def events_in_interval(self, interval):

        return [event for event in self.events if interval[1] < event.play_time < interval[0]]

    def events_in_intervals(self, intervals):

        all_plays = []
        for interval in intervals:
            all_plays += self.events_in_interval(interval)

        return sorted(all_plays)


    def boxscore_stats(self):

        home_boxscore['POS'] = home_pos
        away_boxscore['POS'] = away_pos
        home_boxscore['DRTG'] = home_drtg
        home_boxscore['ORTG'] = home_ortg
        away_boxscore['DRTG'] = away_drtg
        away_boxscore['ORTG'] = away_ortg

        home_boxscore['REST'] = calc_days_rest(game_day, home_team_id)
        away_boxscore['REST'] = calc_days_rest(game_day, look_up_opponent(game_id, home_team_id))

        return home_boxscore, away_boxscore

    def game_stats_by_time(self, team_id, timestream, stat):

        plays = [play for play in game['playbyplay']['plays']['play'] if play['team-id-1'] == str(team_id)]

        int_plays = get_plays_in_intervals(plays, timestream)

        if stat == 'efg':
            made_shots_coords, missed_shots_coords = filter_missed_made(int_plays)
            total_made = len(made_shots_coords)
            total_missed = len(missed_shots_coords)
            total_attempts = total_made + total_missed
            total_threes = len([shot for shot in made_shots_coords if is_shot_three(shot['x'], shot['y'])])
            if total_attempts > 0:
                efg = 100 * (total_made + 0.5 * total_threes) / total_attempts
            else:
                efg = 0

            return efg, total_made, total_threes, total_attempts
    
