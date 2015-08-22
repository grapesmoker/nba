from __future__ import division

__author__ = 'jerry'

import datetime as dt
from settings import pbp

from Game import Game

from utils import recursive_intersect


class NoCollectionError(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class SeasonDataError(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class Season:

    # This is a helper class to manage a full season's worth of data

    _coll = pbp

    def __init__(self, season=None, collection=None):

        self._games = []
        self._data = []
        self._start_date = None
        self._end_date = None
        self._season = season

        self._index = 0

        if collection is not None:
            self.__class__._coll = collection
            self._coll = collection
        elif self._coll is None:
            if self.__class__._coll is None:
                raise NoCollectionError('Must have a collection in MongoDB!')
            else:
                self._coll = self.__class__._coll

        if season is not None:
            self.get_by_season(season)

    def get_by_season(self, season):

        data = self._coll.find({'league.season.season': season})
        self._data = data
        self.set_data(self._data)

    def set_data(self, data):
        self._games = []
        for game_json in data:
            event_id = game_json['league']['season']['eventType'][0]['events'][0]['eventId']
            game = Game(event_id=event_id)
            self._games.append(game)

        self._games = sorted(self._games)

        self._start_date = self._games[0].date
        self._end_date = self._games[-1].date

    def __str__(self):
        return '{}-{} NBA Season'.format(self.season, self.season + 1)

    def __iter__(self):
        self._index = 0
        return self

    def next(self):
        try:
            game = self.games[self._index]
        except IndexError:
            raise StopIteration

        self._index += 1
        return game

    @property
    def games(self):
        return self._games

    @property
    def start_date(self):
        return self._start_date

    @property
    def end_date(self):
        return self._end_date

    @property
    def season(self):
        return self._season

    def __len__(self):
        return len(self.season)

    def get_all_games_in_range(self, start_date=None, end_date=None):

        if start_date is not None and end_date is None:
            games = [game for game in self.games if start_date <= game.date]
        elif start_date is None and end_date is not None:
            games = [game for game in self.games if game.date <= end_date]
        elif start_date is not None and end_date is not None:
            games = [game for game in self.games if start_date <= game.date <= end_date]
        else:
            games = self.games

        return games

    def get_team_games_in_range(self, team, start_date=None, end_date=None):

        games = [game for game in self.get_all_games_in_range(start_date, end_date)
                 if game.is_away(team) or game.is_home(team)]

        return games

    def get_player_games_in_range(self, player, start_date=None, end_date=None):

        games = [game for game in self.get_all_games_in_range(start_date, end_date)
                 if game.player_in_game(self)]

        return games

    def drtg(self, team, start_date=None, end_date=None):

        games = self.get_team_games_in_range(team, start_date, end_date)

        pts_against = 0
        possessions = 0

        for game in games:
            opponent = game.opponent(team)
            pts_against += game.score(opponent)
            possessions += game.possessions(opponent)

        drtg = 100 * pts_against / possessions

        return drtg

    def ortg(self, team, start_date=None, end_date=None):

        games = self.get_team_games_in_range(team, start_date, end_date)

        pts_scored = 0
        possessions = 0

        for game in games:
            pts_scored += game.score(team)
            possessions += game.possessions(team)

        ortg = 100 * pts_scored / possessions

        return ortg

    def player_ortg(self, player, start_date=None, end_date=None):

        games_played = self.get_player_games_in_range(player, start_date, end_date)

        ast = 0
        fgm = 0
        fga = 0
        fta = 0
        ftm = 0
        tov = 0
        threes = 0
        orb = 0
        pts = 0
        mp = 0

        team_fgm = 0
        team_fga = 0
        team_ast = 0
        team_mp = 0
        team_ftm = 0
        team_fta = 0
        team_orb = 0
        team_pts = 0
        team_3pm = 0
        team_tov = 0

        opp_dreb = 0

        for game in games_played:

            player_data = game.player_boxscore(player)
            team = game.player_team(player)
            opponent = game.opponent(team)
            team_data = game.team_boxscore(team)['teamStats']
            opponent_data = game.team_boxscore(opponent)['teamStats']

            ast += player_data['assists']
            fgm += player_data['fieldGoals']['made']
            fga += player_data['fieldGoals']['attempted']
            fta += player_data['freeThrows']['attempted']
            ftm += player_data['freeThrows']['made']
            tov += player_data['turnovers']
            threes += player_data['threePointFieldGoals']['made']
            orb += player_data['rebounds']['offensive']
            pts += player_data['points']
            mp += player_data['totalSecondsPlayed'] / 60.0

            team_fgm += team_data['fieldGoals']['made']
            team_fga += team_data['fieldGoals']['attempted']
            team_ast += team_data['assists']
            team_mp += team_data['minutes']
            team_ftm += team_data['freeThrows']['made']
            team_fta += team_data['freeThrows']['attempted']
            team_orb += team_data['rebounds']['offensive']
            team_pts += team_data['points']
            team_3pm += team_data['threePointFieldGoals']['made']
            team_tov += team_data['turnovers']['total']
            opp_dreb += opponent_data['rebounds']['defensive']

        team_orb_pct = team_orb / (opp_dreb + team_orb)

        ft_part = (1 - (1 - (ftm / fta))**2) * 0.4 * fta
        ast_part = 0.5 * (((team_pts - team_ftm) - (pts - ftm)) / (2 * (team_fga - fga))) * ast
        q_ast = ((mp / (team_mp / 5)) * (1.14 * ((team_ast - ast) / team_fgm))) + ((((team_ast / team_mp) * mp * 5 - ast) / ((team_fgm / team_mp) * mp * 5 - fgm)) * (1 - (mp / (team_mp / 5))))
        fg_part = fgm * (1 - 0.5 * ((pts - ftm) / (2 * fga)) * q_ast)
        team_scoring_poss = team_fgm + (1 - (1 - (team_ftm / team_fta))**2) * team_fta * 0.4
        team_play_pct = team_scoring_poss / (team_fga + team_fta * 0.4 + team_tov)
        team_orb_weight = ((1 - team_orb_pct) * team_play_pct) / ((1 - team_orb_pct) * team_play_pct + team_orb_pct * (1 - team_play_pct))
        orb_part = orb * team_orb_weight * team_play_pct

        scr_poss = (fg_part + ast_part + ft_part) * (1 - (team_orb / team_scoring_poss) * team_orb_weight * team_play_pct) + orb_part

        fg_x_poss = (fga - fgm) * (1 - 1.07 * team_orb_pct)
        ft_x_poss = ((1 - (ftm / fta))**2) * 0.4 * fta

        tot_poss = scr_poss + fg_x_poss + ft_x_poss + tov

        pprod_fg_part = 2 * (fgm + 0.5 * threes) * (1 - 0.5 * ((pts - ftm) / (2 * fga)) * q_ast)
        pprod_ast_part = 2 * ((team_fgm - fgm + 0.5 * (team_3pm - threes)) / (team_fgm - fgm)) * 0.5 * (((team_pts - team_ftm) - (pts - ftm)) / (2 * (team_fga - fga))) * ast
        pprod_orb_part = orb * team_orb_weight * team_play_pct * (team_pts / (team_fgm + (1 - (1 - (team_ftm / team_fta))**2) * 0.4 * team_fta))

        pprod = (pprod_fg_part + pprod_ast_part + ftm) * (1 - (team_orb / team_scoring_poss) * team_orb_weight * team_play_pct) + pprod_orb_part

        ortg = 100 * pprod / tot_poss

        return ortg


    def player_drtg(self, player, start_date=None, end_date=None):

        games_played = self.get_player_games_in_range(player, start_date, end_date)

        drb = 0
        pf = 0
        mp = 0
        stl = 0
        blk = 0

        team_mp = 0
        team_blk = 0
        team_stl = 0
        team_drb = 0
        team_pf = 0

        team_pos = 0

        opp_fta = 0
        opp_ftm = 0
        opp_fga = 0
        opp_fgm = 0
        opp_orb = 0
        opp_pts = 0
        opp_tov = 0
        opp_mp = 0

        for game in games_played:

            player_data = game.player_boxscore(player)
            team = game.player_team(player)
            opponent = game.opponent(team)
            team_data = game.team_boxscore(team)['teamStats']
            opponent_data = game.team_boxscore(opponent)['teamStats']

            drb += player_data['rebounds']['defensive']
            pf += player_data['personalFouls']
            mp += player_data['totalSecondsPlayed'] / 60.0
            stl += player_data['steals']
            blk += player_data['blockedShots']

            team_mp += team_data['minutes']
            team_blk += team_data['blockedShots']
            team_stl += team_data['steals']
            team_drb += team_data['rebounds']['defensive']
            team_pf += team_data['personalFouls']

            team_pos += team_data['team_pos']

            opp_fta += opponent_data['freeThrows']['attempted']
            opp_ftm += opponent_data['freeThrows']['made']
            opp_fga += opponent_data['fieldGoals']['attempted']
            opp_fgm += opponent_data['fieldGoals']['made']
            opp_orb += opponent_data['rebounds']['offensive']
            opp_pts += opponent_data['points']
            opp_tov += opponent_data['turnovers']['total']
            opp_mp += opponent_data['minutes']

        team_drtg = 100 * opp_pts / team_pos

        dor_pct = opp_orb / (opp_orb + team_drb)
        dfg_pct = opp_fgm / opp_fga

        fmwt = (dfg_pct * (1 - dor_pct)) / (dfg_pct * (1 - dor_pct) + (1 - dfg_pct) * dor_pct)
        stops1 = stl + blk * fmwt * (1 - 1.07 * dor_pct) + drb * (1 - fmwt)
        stops2 = (((opp_fga - opp_fgm - team_blk) / team_mp) * fmwt * (1 - 1.07 * dor_pct) + ((opp_tov - team_stl) / team_mp)) * mp + (pf / team_pf) * 0.4 * opp_fta * (1 - (opp_ftm / opp_fta))**2

        stops_tot = stops1 + stops2

        stop_pct = (stops_tot * opp_mp) / (team_pos * mp)

        d_pts_per_scrposs = opp_pts / (opp_fgm + (1 - (1 - (opp_ftm / opp_fta))**2) * opp_fta * 0.4)

        drtg = team_drtg + 0.2 * (100 * d_pts_per_scrposs * (1 - stop_pct) - team_drtg)

        return drtg

    def player_usage(self, player, start_date=None, end_date=None):

        games_played = self.get_player_games_in_range(player, start_date, end_date)

        fga = 0
        fta = 0
        tov = 0
        mp = 0

        team_fga = 0
        team_fta = 0
        team_tov = 0
        team_mp = 0

        for game in games_played:


            team = game.player_team(player)
            player_data = game.player_boxscore(player)
            team_data = game.team_boxscore(team)

            fga += player_data['fieldGoals']['attempted']
            fta += player_data['freeThrows']['attempted']
            tov += player_data['turnovers']
            mp += player_data['totalSecondsPlayed'] / 60.0

            team_fga += team_data['fieldGoals']['attempted']
            team_fta += team_data['freeThrows']['attempted']
            team_tov += team_data['turnovers']['total']
            team_mp += team_data['minutes']

        usg = 100 * ((fga + 0.44 * fta + tov) * (team_mp / 5)) / (mp * (team_fga + 0.44 * team_fta + team_tov))

        return usg