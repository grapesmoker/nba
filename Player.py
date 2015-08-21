from __future__ import division

import datetime as dt

from settings import players

from utils import play_time

# play_time, check_time_consistency, create_shot_chart

#from Game import Game

import Game

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

        if isinstance(game, int):
            game = Game.Game(event_id=game)
        elif isinstance(game, Game.Game):
            pass
        else:
            raise TypeError('Incorrect type for game!')


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

    def player_shot_chart(self, game_id, **kwargs):

        game = Game.Game(pbp, game_id)

        player_plays = game.events_by_player(player_id)


        made_shots = [play['shotCoordinates'] for play in player_plays if 
                      play['playEvent'].has_key('name') and play['playEvent']['name'] == 'Field Goal Made']
        missed_shots = [play['shotCoordinates'] for play in player_plays if
                        play['playEvent'].has_key('name') and play['playEvent']['name'] == 'Field Goal Missed']

        made_shots_coords = [{'x': float(shot['x']), 'y': float(shot['y']) + 5.25} for shot in made_shots]
        missed_shots_coords = [{'x': float(shot['x']), 'y': float(shot['y'])+ 5.25} for shot in missed_shots]

        #print made_shots_coords
        #print missed_shots_coords

        if 'return' in kwargs:
            if kwargs['return'] == True:
                return made_shots_coords, missed_shots_coords
            else:
                kwargs['plot'] = True
        else:
            kwargs['plot'] = True

        if 'plot' in kwargs:
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

            gd = dt.datetime.strftime(game.date, '%Y-%m-%d')
            team1_name = game.home_team['nickname']
            team2_name = game.away_team['nickname']
            
            first_name, last_name = look_up_player_name(player_id)

            create_shot_chart(made_shots_coords, missed_shots_coords,
                              'plots/players/{}_{}_shots_{}_{}_vs_{}.pdf'.format(first_name, last_name, gd, team1_name, team2_name),
                              '{} {} on {} - {} vs {}'.format(first_name, last_name, gd, team1_name, team2_name),
                              plot_type=plot_type, hex_size=hex_size, overplot_shots=overplot_shots)

    def check_sub_times_consistency(player_id):

        games_played = games_played_pbp(player_id)
        fn, ln = player_name(player_id)

        for game in games_played:
            game_id = int(game['playbyplay']['contest']['id'])
            times_subbed_in, times_subbed_out = player_time_on_court(game_id, player_id, return_type='separate')

            consistent = True

            if len(times_subbed_in) == len(times_subbed_out) or len(times_subbed_in) == len(times_subbed_out) + 1:
                for ti, to in zip(times_subbed_in, times_subbed_out):
                    if ti < to:
                        consitent = False
            else:
                consistent = False

            team1, team1_id, team2, team2_id = game_teams(game_id)

            print 'player: {}, game_id: {}, game: {}, date: {}, consistent times: {}'.format(' '.join((fn, ln)),
                                                                                             game_id,
                                                                                             ' vs '.join((team1, team2)),
                                                                                             game_day(game_id),
                                                                                             consistent)
            game_boxscore = boxscores.find_one({'boxscore.contest.id': game_id})
            player_boxscore = [pbx for pbx in game_boxscore['boxscore']['player-stats']['team'][0]['players']['player']
                               if pbx['id'] == int(player_id)] + \
                               [pbx for pbx in game_boxscore['boxscore']['player-stats']['team'][1]['players']['player']
                                if pbx['id'] == int(player_id)]

            boxscore_seconds = player_boxscore[0]['total-seconds']['seconds']
            calc_seconds = 0
            for ti, to in zip(times_subbed_in, times_subbed_out):
                td = ti - to
                calc_seconds += td.total_seconds()

            print 'Boxscore seconds: {}'.format(boxscore_seconds)
            print 'Calculated seconds: {}'.format(calc_seconds)

            if abs(boxscore_seconds - calc_seconds) > 120:
                print 'Discrepancy of {}s'.format(abs(boxscore_seconds - calc_seconds))

    def drtg(self, game):

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
        drb = box_score['rebounds']['defensive']
        pts = box_score['points']
        mp = box_score['totalSecondsPlayed'] / 60.0
        stl = box_score['steals']
        blk = box_score['blockedShots']
        pf = box_score['personalFouls']

        team_fgm = team_stats['fieldGoals']['made']
        team_fga = team_stats['fieldGoals']['attempted']
        team_ast = team_stats['assists']
        team_mp = team_stats['minutes']
        team_ftm = team_stats['freeThrows']['made']
        team_fta = team_stats['freeThrows']['attempted']
        team_orb = team_stats['rebounds']['offensive']
        team_drb = team_stats['rebounds']['defensive']
        team_pts = team_stats['points']
        team_3pm = team_stats['threePointFieldGoals']['made']
        team_tov = team_stats['turnovers']['total']
        team_blk = team_stats['blockedShots']
        team_stl = team_stats['steals']
        team_pf = team_stats['personalFouls']
        team_pos = team.possessions(game)
        team_drtg = team.drtg(game)

        print team_drtg

        opp_orb = opp_stats['rebounds']['offensive']
        opp_fga = opp_stats['fieldGoals']['attempted']
        #opp_3pa = opp_stats['3PA']
        opp_fgm = opp_stats['fieldGoals']['made']
        opp_tov = opp_stats['turnovers']['total']
        opp_ftm = opp_stats['freeThrows']['made']
        opp_fta = opp_stats['freeThrows']['attempted']
        opp_mp = opp_stats['minutes']
        opp_pts = opp_stats['points']
        opp_pos = opp.possessions(game)

        dfg_pct = opp_fgm / opp_fga
        dor_pct = opp_orb / (team_drb + opp_orb)
        team_orb_pct = team_orb / (opp_orb + team_drb)

        # FMwt = (dfg_pct * (1 - dor_pct)) / (dfg_pct * (1 - dor_pct) + (1 - dfg_pct) * dor_pct)
        # Stops1 = stl + blk * FMwt * (1 - 1.07 * dor_pct) + drb * (1 - FMwt)

        # Stops2_a = (((opp_fga - opp_fgm - team_blk) / team_mp) * FMwt * (1 - 1.07 * dor_pct) + ((opp_tov - team_stl) / team_mp)) * mp
        # Stops2_b =  (pf / team_pf) * 0.4 * opp_fta * (1 - (opp_ftm / opp_fta))**2
        # Stops2 = Stops2_a + Stops2_b

        # Stops = Stops1 + Stops2
        # Stop_pct = (Stops * opp_mp) / (team_pos * mp)

        # D_Pts_per_ScPoss = opp_pts / (opp_fgm + (1 - (1 - (opp_ftm / opp_fta))**2) * opp_fta *0.4)

        # DRtg = team_drtg + 0.2 * (100 * D_Pts_per_ScPoss * (1 - Stop_pct) - team_drtg)

        # return DRtg


        fmwt = (dfg_pct * (1 - dor_pct)) / (dfg_pct * (1 - dor_pct) + (1 - dfg_pct) * dor_pct)
        stops1 = stl + blk * fmwt * (1 - 1.07 * dor_pct) + drb * (1 - fmwt)
        stops2 = (((opp_fga - opp_fgm - team_blk) / team_mp) * fmwt * (1 - 1.07 * dor_pct) + ((opp_tov - team_stl) / team_mp)) * mp + \
                 (pf / team_pf) * 0.4 * opp_fta * (1 - (opp_ftm / opp_fta))**2

        stops_tot = stops1 + stops2

        stop_pct = (stops_tot * opp_mp) / (team_pos * mp)

        d_pts_per_scrposs = opp_pts / (opp_fgm + (1 - (1 - (opp_ftm / opp_fta))**2) * opp_fta * 0.4)

        drtg = team_drtg + 0.2 * (100 * d_pts_per_scrposs * (1 - stop_pct) - team_drtg)

        return drtg