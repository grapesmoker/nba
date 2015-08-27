#!/usr/bin/env python
from __future__ import division

import datetime as dt
import argparse

from tqdm import tqdm
from utils import compute_ts_length
from Season import Season


team_to_espn_ids = {'Hawks': 1,
                    'Celtics': 2,
                    'Hornets': 3,
                    'Bulls': 4,
                    'Cavaliers': 5,
                    'Mavericks': 6,
                    'Nuggets': 7,
                    'Pistons': 8,
                    'Warriors': 9,
                    'Rockets': 10,
                    'Pacers': 11,
                    'Clippers': 12,
                    'Lakers': 13,
                    'Heat': 14,
                    'Bucks': 15,
                    'Timberwolves': 16,
                    'Nets': 17,
                    'Knicks': 18,
                    'Magic': 19,
                    '76ers': 20,
                    'Suns': 21,
                    'Trail Blazers': 22,
                    'Kings': 23,
                    'Spurs': 24,
                    'Thunder': 25,
                    'Jazz': 26,
                    'Wizards': 27,
                    'Raptors': 50,
                    'Grizzlies': 51,
                    'Bobcats': 74}

def compute_all_season_lineups(year):

    print 'Loading the {}-{} NBA season'.format(year, year + 1)
    season = Season(year)
    print 'Loaded season'
    print 'Computing lineups for all teams in all games...'

    for game in tqdm(season):

        print 'Computing lineups for {}'.format(game)

        home_team = game.home_team
        away_team = game.away_team

        home_lineups = game.lineup_combinations(home_team)
        away_lineups = game.lineup_combinations(away_team)

        try:
            home_timestream = game.time_by_lineup(home_lineups)
            away_timestream = game.time_by_lineup(away_lineups)
            home_minutes = compute_ts_length(home_timestream)
            away_minutes = compute_ts_length(away_timestream)

            print 'Home team: {} minutes, Away team: {} minutes'.format(home_minutes, away_minutes)

        except Exception as ex:
            print 'Oh no, something terrible happened while computing lineups for {}'.format(game)
            print ex


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--operation', dest='operation')
    parser.add_argument('-fn', '--firstname', dest='player_firstname')
    parser.add_argument('-ln', '--lastname', dest='player_lastname')
    parser.add_argument('-pt', '--plot_type', dest='plot_type', default='hexbin')
    parser.add_argument('-gid', '--game_id', dest='game_id', type=int)
    parser.add_argument('-if', '--input_file', dest='input_file')
    parser.add_argument('-of', '--output_file', dest='output_file')
    
    args = parser.parse_args()

    if args.operation == 'compute_timelines':

        compute_all_season_lineups(2013)

    if args.operation == 'scrape_data':
        season_start_date = dt.datetime(2013, 10, 29)
        season_end_date = dt.datetime(2014, 04, 17)
    
        get_all_data(season_start_date, season_end_date)

    if args.operation == 'plot_player_shots':

        plot_player_shots(args.player_firstname, args.player_lastname, args.plot_type)

    if args.operation == 'times_played':

        player_id = look_up_player_id(args.player_firstname, args.player_lastname)
        player_times_on_court(player_id)

    if args.operation == 'check_consistency':

        player_id = look_up_player_id(args.player_firstname, args.player_lastname)
        check_sub_times_consistency(player_id)

    if args.operation == 'quarter_starters' and args.game_id is not None:

        q_starters = quarter_starters(args.game_id)
        team1, team1_id, team2, team2_id = game_teams(args.game_id)
        print '{} vs {}'.format(team1, team2)

        for q in q_starters.keys():
            player_ids = q_starters[q]
            print 'Quarter {} starters:'.format(q)
            for player_id in player_ids:
                fn, ln = look_up_player_name(player_id)
                print fn, ln

    if args.operation == 'construct_odds_csv' and args.input_file is not None and args.output_file is not None:

        construct_odds_csv(args.input_file, args.output_file)

    if args.operation == 'plot_all_game_charts' and args.game_id is not None:

        plot_all_game_charts(args.game_id)


    if args.operation == 'cluster_players_defense' and args.output_file is not None:

        cluster_players_defense(args.output_file)

    if args.operation == 'cluster_teams_defense' and args.output_file is not None:
            
        cluster_teams_defense(args.output_file)