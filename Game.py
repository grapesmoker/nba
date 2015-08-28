from __future__ import division

import datetime as dt
import numpy as np

from settings import pbp

from itertools import combinations

from Team import Team
from Player import Player
from Event import Event
from Boxscore import TeamBoxscore, PlayerBoxscore

from utils import shared_times, recursive_intersect

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
        self._id = self._core_data['eventId']
        self._game_type = data['league']['season']['eventType'][0]['name']
        self._date = dt.datetime.strptime(self._core_data['startDate'][0]['full'], '%Y-%m-%dT%H:%M:%S')
        self._teams = self._core_data['teams']
        self._home_team = self._teams[0]
        self._away_team = self._teams[1]
        self._home_boxscore = self._core_data['boxscores'][0]
        self._away_boxscore = self._core_data['boxscores'][1]
        self._pbp = self._core_data['pbp']
        self._events = [Event(play_data) for play_data in self._pbp]

        self._add_custom_fields()
        self._pre_cache_lineups()

    def _add_custom_fields(self):

        id_str = 'league.season.eventType.0.events.0.eventId'
        update_str = 'league.season.eventType.0.events.0.boxscores.'

        if 'lineups' not in self._core_data['boxscores'][0]:
            self._coll.update_one({id_str: self._id}, {'$set': {update_str + '0.lineups': []}})
            self._coll.update_one({id_str: self._id}, {'$set': {update_str + '1.lineups': []}})
            self._core_data['boxscores'][0]['lineups'] = []
            self._core_data['boxscores'][1]['lineups'] = []

    def _pre_cache_lineups(self):

        # pre-cache lineups on load
        self._non_empty_lineups = {}
        self._empty_lineups = {}

        self._non_empty_lineups[0] = [lineup for lineup in self._core_data['boxscores'][0]['lineups']
                                      if lineup['times'] != []]
        self._non_empty_lineups[1] = [lineup for lineup in self._core_data['boxscores'][1]['lineups']
                                      if lineup['times'] != []]

        self._empty_lineups[0] = [lineup for lineup in self._core_data['boxscores'][0]['lineups']
                                  if lineup['times'] == []]
        self._empty_lineups[1] = [lineup for lineup in self._core_data['boxscores'][1]['lineups']
                                  if lineup['times'] == []]

    def __str__(self):
        home_team_name = self._home_team['location'] + ' ' + self._home_team['nickname']
        away_team_name = self._away_team['location'] + ' ' + self._away_team['nickname']
        return '{0} vs {1} on {2!s}'.format(home_team_name, away_team_name, self._date)

    def __repr__(self):
        return self.__str__()

    @property
    def id(self):
        return self._id

    @property
    def game_type(self):
        return self._game_type

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

    def game_players(self, team):
        if self.home_team == team:
            return self.home_players
        elif self.away_team == team:
            return self.away_players
        else:
            raise GameDataError('No such team: ({0}) for this game!'.format(team))

    @property
    def pbp(self):
        return self._pbp

    @property
    def date(self):
        return self._date

    @property
    def periods(self):
        return self._core_data['eventStatus']['period']

    @property
    def home_boxscore(self):
        return self._core_data['boxscores'][0]

    @property
    def away_boxscore(self):
        return self._core_data['boxscores'][1]

    def team_boxscore(self, team):
        if self.is_home(team):
            return self.home_boxscore
        elif self.is_away(team):
            return self.away_boxscore
        else:
            raise GameDataError('{} did not participate in {}'.format(team, self))

    def is_home(self, team):
        if self.home_team == team:
            return True
        else:
            return False

    def is_away(self, team):
        if self.away_team == team:
            return True
        else:
            return False

    def score(self, team):
        if self.is_home(team):
            return self.home_boxscore['teamStats']['points']
        elif self.is_away(team):
            return self.away_boxscore['teamStats']['points']
        else:
            raise GameDataError('{} did not participate in {}'.format(team, self))

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

    def possessions(self, team):
        if self.is_home(team):
            return self.home_possessions
        elif self.is_away(team):
            return self.away_possessions
        else:
            raise GameDataError('{} did not participate in {}'.format(team, self))

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

    def __contains__(self, player_or_team):

        if isinstance(player_or_team, Player):
            return self.player_in_game(player_or_team)
        elif isinstance(player_or_team, Team):
            return self.is_home(player_or_team) or self.is_away(player_or_team)
        else:
            raise TypeError('{} is neither Player nor Team!'.format(repr(player_or_team)))

    def player_in_game(self, player):

        home = [self.home_boxscore['teamId']
                for stat in self.home_boxscore['playerstats']
                if stat['player']['playerId'] == player.id]

        away = [self.away_boxscore['teamId']
                for stat in self.away_boxscore['playerstats']
                if stat['player']['playerId'] == player.id]

        if home != [] or away != []:
            return True
        else:
            return False

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

    def lineup_combinations(self, team):
        players = [player for player in self.game_players(team) if player.minutes_played(self) > 0]
        return combinations(players, 5)

    def _find_empty_lineup(self, lineup_hash, team_index):
        lineups = [lineup for lineup in self._empty_lineups[team_index]
                   if 'hash' in lineup and lineup['hash'] == lineup_hash]
        if lineups != []:
            return lineups[0]
        else:
            return None

    def _find_non_empty_lineup(self, lineup_hash, team_index):
        lineups = [lineup for lineup in self._non_empty_lineups[team_index]
                   if 'hash' in lineup and lineup['hash'] == lineup_hash]
        if lineups != []:
            return lineups[0]
        else:
            return None

    def _lineup_hash(self, players):
        """Hash the lineup by taking the hash of the sum of the player IDs.
        Used to keep track of which lineups have already been computed on a
        per-game basis."""
        return hash(np.sum([player.id for player in players]))

    def time_by_lineup(self, players):

        team = self.player_team(players[0])
        for player in players[1:]:
            if not team.is_player_on_team(player, self):
                raise GameDataError('All players must be on the same team!')

        team = self.player_team(players[0])

        if self.is_home(team):
            team_index = 0
        elif self.is_away(team):
            team_index = 1
        else:
            raise GameDataError('{} did not participate in {}'.format(team, self))

        timestream = []
        ts_empty = False

        lineup_hash = self._lineup_hash(players)

        non_empty = self._find_non_empty_lineup(lineup_hash, team_index)
        empty = self._find_empty_lineup(lineup_hash, team_index)

        if empty and not non_empty:
            #print 'no timestream for lineup: {}'.format(players)
            timestream = []

        elif non_empty and not empty:
            #print 'retrieving cached timestream for lineup: {}'.format(players)
            for interval in non_empty['times']:
                start = dt.timedelta(seconds=interval['start'])
                end = dt.timedelta(seconds=interval['end'])
                timestream.append((start, end))

        elif not empty and not non_empty:

            #print 'calculating timestream for lineup: {}'.format(players)

            timestream = self.multiple_player_overlap(players)

            # this is expensive to compute so cache it in the db because it doesn't change
            # on a per-game basis

            id_str = 'league.season.eventType.0.events.0.eventId'
            update_str = 'league.season.eventType.0.events.0.boxscores.{}.lineups'.format(team_index)

            player_data = [player.id for player in players]
            time_data = []
            lineup_hash = hash(np.sum(player_data))

            for interval in timestream:
                time_data.append({'start': interval[0].seconds, 'end': interval[1].seconds})

            lineup_data = {'players': player_data, 'times': time_data, 'hash': lineup_hash}
            self._coll.update_one({id_str: self._id},
                {'$addToSet': {update_str: lineup_data}})

            # update the in-memory data
            self._core_data['boxscores'][team_index]['lineups'].append(lineup_data)

        return timestream

    def events_by_player(self, player):

        player_events = [event for event in self.events if player in event.players]

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

    def quarter_enders(self):

        quarter_enders = {}

        for q in [1, 2, 3, 4]:

            quarter_plays = sorted([ev for ev in self._events if ev.period == q])

            players_used = []
            subs_used = []
            i = 0
            done = False

            while i < len(quarter_plays) and not done:
                event = quarter_plays[i]
                players = event.players

                if event.play_text.find('Substitution:') > -1:
                    subbed_in_player = players[0]
                    subbed_out_player = players[1]
                    if subbed_in_player not in players_used:
                        players_used.append(subbed_in_player)
                    if subbed_out_player not in subs_used:
                        subs_used.append(subbed_out_player)
                else:
                    for player in players:
                        if player not in subs_used and player not in players_used:
                            players_used.append(player)

                i += 1
                if len(players_used) == 10:
                    done = True

            quarter_enders[q] = players_used

        return quarter_enders

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

        #import time
        #start = time.clock()
        player_times = [player.time_on_court(self) for player in players_on]
        #end = time.clock()
        #print 'took {}s to calculate player times on court'.format(end - start)
        shared_times = recursive_intersect(player_times)[0]
        #print player_times

        return shared_times


    def events_in_interval(self, interval):

        return sorted([event for event in self.events if interval[0] <= event.play_time <= interval[1]])

    def events_not_in_interval(self, interval):

        return sorted([event for event in self.events if not interval[0] <= event.play_time <= interval[1]])

    def events_in_intervals(self, intervals):

        all_plays = []
        for interval in intervals:
            all_plays += self.events_in_interval(interval)

        return sorted(all_plays, reverse=True)

    def __cmp__(self, other):
        if self.date == other.date:
            return 0
        elif self.date < other.date:
            return -1
        elif self.date > other.date:
            return 1

    def team_stats_by_time(self, team, timestream):

        events = self.events_in_intervals(timestream)

        team_box_score = TeamBoxscore()
        for event in events:
            # we only care about plays that actually accrue counting stats
            if event.is_field_goal_made:
                player = event.shot_made_by
                opponent = self.opponent(team)
                if team.is_player_on_team(player, self):
                    assister = event.assisted_by
                    if event.is_three_pointer:
                        team_box_score.points += 3
                        team_box_score.three_point_field_goals_attempted += 1
                        team_box_score.three_point_field_goals_made += 1
                    else:
                        team_box_score.points += 2

                    team_box_score.field_goals_made += 1
                    team_box_score.field_goals_attempted += 1
                    if assister:
                        team_box_score.assists += 1
                elif opponent.is_player_on_team(player, self):
                    if event.is_three_pointer:
                        team_box_score.points_against += 3
                    else:
                        team_box_score.points_against += 2

            elif event.is_field_goal_missed:
                player = event.shot_missed_by
                if team.is_player_on_team(player, self):
                    if event.is_three_pointer:
                        team_box_score.three_point_field_goals_attempted += 1
                    team_box_score.field_goals_attempted += 1

            elif event.is_free_throw_made:
                player = event.free_throw_made_by
                opponent = self.opponent(team)
                if team.is_player_on_team(player, self):
                    team_box_score.points += 1
                    team_box_score.free_throws_made += 1
                    team_box_score.free_throws_attempted += 1
                elif opponent.is_player_on_team(player, self):
                    team_box_score.points_against += 1

            elif event.is_free_throw_missed:
                player = event.free_throw_missed_by
                if team.is_player_on_team(player, self):
                    team_box_score.points += 1
                    team_box_score.free_throws_made += 1
                    team_box_score.free_throws_attempted += 1

            elif event.is_oreb:
                player = event.rebounded_by
                if player and team.is_player_on_team(player, self):
                    team_box_score.rebounds_offensive += 1

            elif event.is_dreb:
                player = event.rebounded_by
                if player and team.is_player_on_team(player, self):
                    team_box_score.rebounds_defensive += 1

            elif event.is_turnover:
                player = event.turned_over_by
                stolen_by = event.stolen_by
                if player and team.is_player_on_team(player, self):
                    team_box_score.turnovers_total += 1
                elif stolen_by and team.is_player_on_team(stolen_by, self):
                    team_box_score.steals += 1
                else:
                    # shot clock turnover
                    if team.nickname in event.play_text:
                        team_box_score.turnovers_total += 1

        return team_box_score

    def stats_by_lineup(self, players):
        # all players are assumed to be on the same team
        # if this is not the case, bail
        team = self.player_team(players[0])
        for player in players[1:]:
            if not team.is_player_on_team(player, self):
                raise GameDataError('All players must be on the same team!')

        timestream = self.time_by_lineup(players)

        box_score = self.team_stats_by_time(team, timestream)

        return box_score

    def plot_all_game_charts(self):

        home_players, away_players = get_player_boxscores(game_id)

        for player in home_players:
            print 'Processing ', player['first-name'], player['last-name']
            player_id = player['id']
            player_shot_chart(game_id, player_id)
            team_shot_chart_with_player(game_id, player_id)
            team_shot_chart_without_player(game_id, player_id)

        for player in away_players:
            print 'Processing ', player['first-name'], player['last-name']
            player_id = player['id']
            player_shot_chart(game_id, player_id)
            team_shot_chart_with_player(game_id, player_id)
            team_shot_chart_without_player(game_id, player_id)


