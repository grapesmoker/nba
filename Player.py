from __future__ import division

import datetime as dt
import numpy as np

from settings import players
from drawing.player_shot_charts import create_shot_chart
from Boxscore import PlayerBoxscore

class Player:

    _coll = players

    def __init__(self, player_id):
        self._coll = self.__class__._coll
        self._player = self._coll.find_one({'id': player_id})

        self._first_name = self._player['firstName']
        self._last_name = self._player['lastName']
        self._id = self._player['id']

    @property
    def first_name(self):
        return self._first_name
        
    @property
    def last_name(self):
        return self._last_name

    @property
    def id(self):
        return self._id

    def __str__(self):
        return '{0} {1}'.format(self._first_name, self._last_name)

    def __repr__(self):
        return self.__str__()

    def __cmp__(self, other):
        if self.id == other.id and self.first_name == other.first_name and self.last_name == other.last_name:
            return 0
        elif self.last_name < other.last_name:
            return -1
        elif self.last_name == other.last_name and self.first_name < self.last_name:
            return -1
        elif self.last_name == other.last_name and self.first_name == other.last_name:
            return self.id < other.id
        else:
            return 1

    def __hash__(self):

        return hash('{}{}{}'.format(self.first_name, self.last_name, self._id))

    def check_time_consistency(self, times_subbed_in, times_subbed_out):

        consistent = True

        if len(times_subbed_in) == len(times_subbed_out) or len(times_subbed_in) == len(times_subbed_out) + 1:
            correct = True
            for to in times_subbed_out:
                for i, ti in enumerate(times_subbed_in[:-1]):
                    ti_next = times_subbed_in[i + 1]
                    if not (to < ti and to >= ti_next):
                        correct = False

            consistent = correct
        else:
            consistent = False

        return consistent

    def time_on_court(self, game):

        plays_subbed_in = [event for event in game.events if event.play_text.find('Substitution:') > -1
                           and event.players[0] == self]

        plays_subbed_out = [event for event in game.events if event.play_text.find('Substitution:') > -1
                            and event.players[1] == self]

        times_subbed_in = [event.play_time for event in plays_subbed_in]
        times_subbed_out = [event.play_time for event in plays_subbed_out]

        q_starters = game.quarter_starters()
        
        q2 = dt.timedelta(minutes=36)
        q3 = dt.timedelta(minutes=24)
        q4 = dt.timedelta(minutes=12)

        q_end_times = [q2, q3, q4]
        
        for q, starters in q_starters.items():
            q_start_time = dt.timedelta(minutes=((5 - q) * 12))

            if self in starters and q > 1:
                last_sub_in = sorted([t for t in times_subbed_in if t > q_start_time], reverse=True)
                last_sub_out = sorted([t for t in times_subbed_out if t > q_start_time], reverse=True)

                if last_sub_in != [] and last_sub_out != []:
                    last_sub_in, last_sub_out = last_sub_in[-1], last_sub_out[-1]
                    if last_sub_in > last_sub_out:
                        times_subbed_in.append(q_start_time)
            elif self in starters and q == 1:
                times_subbed_in.append(q_start_time)


        times_subbed_in = sorted(times_subbed_in, reverse=True)

        #print map(str, times_subbed_in), map(str, times_subbed_out)

        i = 0

        while not self.check_time_consistency(times_subbed_in, times_subbed_out) and i < len(times_subbed_in):
            ti = times_subbed_in[i]
            if i + 1 < len(times_subbed_in):
                ti_next = times_subbed_in[i + 1]
            else:
                ti_next = dt.timedelta(minutes=0)

            to_arr = [to for to in times_subbed_out if ti_next < to < ti]
            
            if len(to_arr) == 0:
                if q2 < ti and q2 >= ti_next:
                    times_subbed_out.append(q2)
                elif q3 < ti and q3 >= ti_next:
                    times_subbed_out.append(q3)
                elif q4 < ti and q4 >= ti_next:
                    times_subbed_out.append(q4)

                times_subbed_out = sorted(times_subbed_out, reverse=True)

            i += 1

        if len(times_subbed_out) == len(times_subbed_in) - 1:
            times_subbed_out.append(dt.timedelta(minutes=0))

        time_stream = zip(times_subbed_in, times_subbed_out)

        return time_stream

    def minutes_played(self, game):

        box_score = PlayerBoxscore(game.player_boxscore(self))
        return box_score.total_seconds_played / 60.0

    def made_shots(self, game):

        return [event for event in game.events
                if event.is_field_goal_made and event.players[0] == self]

    def missed_shots(self, game):

        return [event for event in game.events
                if event.is_field_goal_missed and event.players[0] == self]


    def shot_chart(self, game, **kwargs):

        made_shots = self.made_shots(game)
        missed_shots = self.missed_shots(game)

        if 'plot_type' in kwargs:
            plot_type = kwargs['plot_type']
        else:
            plot_type = 'hexbin'
        if 'hex_size' in kwargs:
            hex_size = kwargs['hex_size']
        else:
            hex_size = 1
        if 'overplot_shots' in kwargs:
            overplot_shots = kwargs['overplot_shots']
        else:
            overplot_shots = False

        gd = game.date
        team1_name = game.home_team.nickname
        team2_name = game.away_team.nickname
        first_name, last_name = self.first_name, self.last_name

        create_shot_chart(made_shots, missed_shots,
                          'plots/players/{}_{}_shots_{}_{}_vs_{}.pdf'.format(first_name, last_name, gd, team1_name, team2_name),
                          '{} {} on {} - {} vs {}'.format(first_name, last_name, gd, team1_name, team2_name),
                          plot_type=plot_type, hex_size=hex_size, overplot_shots=overplot_shots)

    def multi_game_shot_chart(self, games, **kwargs):

        made_shots = []
        missed_shots = []

        start_date = None
        end_date = None
        for game in games:
            if game.player_in_game(self):
                if not start_date:
                    start_date = game.date
                end_date = game.date
                made_shots = np.concatenate((made_shots, self.made_shots(game)))
                missed_shots = np.concatenate((missed_shots, self.missed_shots(game)))

        if 'plot_type' in kwargs:
            plot_type = kwargs['plot_type']
        else:
            plot_type = 'hexbin'
        if 'hex_size' in kwargs:
            hex_size = kwargs['hex_size']
        else:
            hex_size = 1
        if 'overplot_shots' in kwargs:
            overplot_shots = kwargs['overplot_shots']
        else:
            overplot_shots = False

        first_name, last_name = self.first_name, self.last_name

        create_shot_chart(made_shots, missed_shots,
                          'plots/players/{}_{}_shots_from_{}_to_{}.pdf'.format(first_name, last_name, start_date, end_date),
                          '{} {} from {} to {}'.format(first_name, last_name, start_date, end_date),
                          plot_type=plot_type, hex_size=hex_size, overplot_shots=overplot_shots)

    def plot_cumul_charts(player_id, hex_sizes, output_types):

        for hex_size in hex_sizes:
            for output_type in output_types:
                cumul_team_shot_chart_with_player(player_id, hex_size=hex_size, output_type=output_type, scale_factor=128)
                cumul_team_shot_chart_without_player(player_id, hex_size=hex_size, output_type=output_type, scale_factor=128)
                cumul_opp_shot_chart_with_player(player_id, hex_size=hex_size, output_type=output_type, scale_factor=128)
                cumul_opp_shot_chart_without_player(player_id, hex_size=hex_size, output_type=output_type, scale_factor=128)

    def drtg(self, game):

        box_score = game.player_boxscore(self)
        team = game.player_team(self)
        opp = game.opponent(team)

        team_stats = team.stats(game)['teamStats']
        opp_stats = opp.stats(game)['teamStats']

        drb = box_score['rebounds']['defensive']
        mp = box_score['totalSecondsPlayed'] / 60.0
        stl = box_score['steals']
        blk = box_score['blockedShots']
        pf = box_score['personalFouls']

        team_mp = team_stats['minutes']
        team_drb = team_stats['rebounds']['defensive']
        team_blk = team_stats['blockedShots']
        team_stl = team_stats['steals']
        team_pf = team_stats['personalFouls']
        team_pos = team.possessions(game)
        team_drtg = team.drtg(game)

        opp_orb = opp_stats['rebounds']['offensive']
        opp_fga = opp_stats['fieldGoals']['attempted']
        opp_fgm = opp_stats['fieldGoals']['made']
        opp_tov = opp_stats['turnovers']['total']
        opp_ftm = opp_stats['freeThrows']['made']
        opp_fta = opp_stats['freeThrows']['attempted']
        opp_mp = opp_stats['minutes']
        opp_pts = opp_stats['points']

        dfg_pct = opp_fgm / opp_fga
        dor_pct = opp_orb / (team_drb + opp_orb)


        fmwt = (dfg_pct * (1 - dor_pct)) / (dfg_pct * (1 - dor_pct) + (1 - dfg_pct) * dor_pct)
        stops1 = stl + blk * fmwt * (1 - 1.07 * dor_pct) + drb * (1 - fmwt)
        stops2 = (((opp_fga - opp_fgm - team_blk) / team_mp) * fmwt * (1 - 1.07 * dor_pct) + ((opp_tov - team_stl) / team_mp)) * mp + \
                 (pf / team_pf) * 0.4 * opp_fta * (1 - (opp_ftm / opp_fta))**2

        stops_tot = stops1 + stops2

        stop_pct = (stops_tot * opp_mp) / (team_pos * mp)

        d_pts_per_scrposs = opp_pts / (opp_fgm + (1 - (1 - (opp_ftm / opp_fta))**2) * opp_fta * 0.4)

        drtg = team_drtg + 0.2 * (100 * d_pts_per_scrposs * (1 - stop_pct) - team_drtg)

        return drtg

    def ortg(self, game):

        box_score = game.player_boxscore(self)
        team = game.player_team(self)
        opp = game.opponent(team)

        team_stats = team.stats(game)['teamStats']
        opp_stats = opp.stats(game)['teamStats']

        ast = box_score['assists']
        fgm = box_score['fieldGoals']['made']
        fga = box_score['fieldGoals']['attempted']
        ftm = box_score['freeThrows']['made']
        fta = box_score['freeThrows']['attempted']
        tov = box_score['turnovers']
        threes = box_score['threePointFieldGoals']['made']
        orb = box_score['rebounds']['offensive']
        pts = box_score['points']
        mp = box_score['totalSecondsPlayed']/ 60.0

        team_fgm = team_stats['fieldGoals']['made']
        team_fga = team_stats['fieldGoals']['attempted']
        team_ast = team_stats['assists']
        team_mp = team_stats['minutes']
        team_ftm = team_stats['freeThrows']['made']
        team_fta = team_stats['freeThrows']['attempted']
        team_orb = team_stats['rebounds']['offensive']
        team_pts = team_stats['points']
        team_3pm = team_stats['threePointFieldGoals']['made']
        team_tov = team_stats['turnovers']['total']
        opp_drb = opp_stats['rebounds']['defensive']

        team_orb_pct = team_orb / (opp_drb + team_orb)

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

    def usage(self, game):

        box_score = game.player_boxscore(self)
        team = game.player_team(self)
        team_stats = team.stats(game)['teamStats']

        fga = box_score['fieldGoals']['attempted']
        fta = box_score['freeThrows']['attempted']
        tov = box_score['turnovers']
        mp = box_score['totalSecondsPlayed'] / 60.0

        team_fga = team_stats['fieldGoals']['attempted']
        team_fta = team_stats['freeThrows']['attempted']
        team_tov = team_stats['turnovers']['total']
        team_mp = team_stats['minutes']

        usg = 100 * ((fga + 0.44 * fta + tov) * (team_mp / 5)) / (mp * (team_fga + 0.44 * team_fta + team_tov))

        return usg