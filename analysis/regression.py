__author__ = 'jerry'

import pandas as pd
import numpy as np

from utils import compute_ts_length

def regress_lineups_single_game(game, team):

    def lineup_minutes(lineup):
        lineup_times = game.time_by_lineup(lineup)
        return compute_ts_length(lineup_times) / 60.0

    lineups = game.lineup_combinations(team)
    players = game.game_players(team)

    #lineups = sorted(lineups, key=lineup_minutes, reverse=True)
    players = sorted(players, key=lambda p: p.minutes_played(game), reverse=True)

    data = pd.DataFrame(columns=players)
    i = 0
    for lineup in lineups:
        lineup_time = lineup_minutes(lineup)
        if lineup_time > 0:
            print lineup, round(lineup_time, 3)
            player_features = np.zeros(len(players))
            for player in lineup:
                player_index = players.index(player)
                player_features[player_index] = 1
            data.loc[i] = player_features
            i += 1

    print data
