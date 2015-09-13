from __future__ import division

__author__ = 'jerry'

import pandas as pd
import numpy as np
import re

from utils import compute_ts_length

from sklearn_pandas import DataFrameMapper
from patsy import dmatrices
from sklearn.linear_model import Ridge, LinearRegression, LogisticRegression
import statsmodels.api as sm


def regress_lineups_single_game(game, team):

    def lineup_minutes(lineup):
        lineup_times = game.time_by_lineup(lineup)
        return compute_ts_length(lineup_times) / 60.0

    lineups = game.lineup_combinations(team)
    players = game.game_players(team)

    cleanup = "([\s]|\.|')"

    players = sorted(players, key=lambda p: p.minutes_played(game), reverse=True)
    columns = [re.sub(cleanup, '', str(player))for player in players] + ['plus_minus']

    data = pd.DataFrame(columns=columns)
    i = 0
    total_minutes = 0

    for lineup in lineups:
        lineup_time = lineup_minutes(lineup)
        total_minutes += lineup_time
        if lineup_time > 0:
            print lineup, round(lineup_time, 3)
            #print [player.id for player in lineup]
            player_features = np.zeros(len(columns))
            box_score = game.stats_by_lineup(lineup)
            for player in lineup:
                player_index = players.index(player)
                player_features[player_index] = 1
                player_features[-1] = box_score.plus_minus
            data.loc[i] = player_features
            i += 1
        if lineup_time < 0:
            print lineup, lineup_time


    player_formula = ' + '.join(columns[:-1])
    formula_str = 'plus_minus ~ ' + player_formula
    print 'total minutes played: {}'.format(total_minutes)

    y, X = dmatrices(formula_str, data=data, return_type='dataframe')

    mod = sm.OLS(y, X)
    res = mod.fit()

    return res

def regress_lineups_team_efg_mult_games(game_ids, team_id, self_or_opp='self'):

    all_game_stats = []
    all_players = []

    for game in game_ids:
        team1_name, team1_id, team2_name, team2_id = game_teams(game)
        print 'Processing {} vs {}'.format(team1_name, team2_name)

        if self_or_opp == 'self':
            game_stats = game_stats_by_lineup(game, team_id, team_id, ['efg'])
        if self_or_opp == 'opp':
            if team_id == team1_id:
                opp_id = team2_id
            elif team_id == team2_id:
                opp_id = team1_id

            game_stats = game_stats_by_lineup(game, team_id, opp_id, ['efg'])
        players = sorted(game_players(game, team_id))

        all_players += players
        all_game_stats += game_stats

    all_players = sorted(pylab.unique(all_players))

    efgs = [ [] for i in range(len(all_game_stats))]
    X = pylab.zeros((len(all_game_stats), len(all_players)))
    w = pylab.zeros(len(all_game_stats))

    used_lineups = []
    sample_counter = 0
    total_gt = 0
    for i, item in enumerate(all_game_stats):
        lineup = item['lineup']
        efgs[sample_counter].append(item['stats'])
        total_gt += compute_ts_length(item['tof'])
        #print used_lineups
        if used_lineup(lineup, used_lineups):
            w[sample_counter] += compute_ts_length(item['tof'])
        else:
            w[sample_counter] += compute_ts_length(item['tof'])
            used_lineups.append(lineup)
            for player in lineup:
                ind = all_players.index(player)
                X[sample_counter][ind] = 1
            sample_counter += 1

        print i, sample_counter

        #X[i][len(all_players)] = compute_ts_length(item['tof'])
        #w[i] = compute_ts_length(item['tof'])
        #efgs[i] = item['stats']['efg']

    y = []

    for i, item in enumerate(efgs):
        #if i < len(used_lineups):
        total_threes = sum([stat['total_threes'] for stat in item])
        total_made = sum([stat['total_made'] for stat in item])
        total_attempts = sum([stat['total_attempts'] for stat in item])

        if total_attempts > 0:
            efg = (total_threes * 0.5 + total_made) / total_attempts
        else:
            efg = 0
        y.append(efg)

    y = pylab.array(y)
    w = pylab.array(w)

    #result = sm.WLS(efgs, X, w).fit()

    #return [(player, param) for player, param in zip(players, result.params)]

    return y, X, w, all_players