#!/usr/bin/env python
from __future__ import division, print_function

import datetime as dt
import argparse
import json
import pymongo
import sys
import os
import re
import dateutil.parser as dtparser
import pandas as pd
import csv

import matplotlib.pyplot as mpl

from tqdm import tqdm
from utils import compute_ts_length
from Season import Season
from Player import Player
from Game import Game

from settings import pbp, players, odds
from analysis.features import construct_global_features, construct_all_features
from analysis.prediction import predict_game_outcome, predict_game_day, predict_all_games
from network import get_odds_from_donbest

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

    print('Loading the {}-{} NBA season'.format(year, year + 1))
    season = Season(year)
    print('Loaded season')
    print('Computing lineups for all teams in all games...')

    for game in tqdm(season):

        print('Computing lineups for {}'.format(game))

        home_team = game.home_team
        away_team = game.away_team

        home_lineups = game.lineup_combinations(home_team)
        away_lineups = game.lineup_combinations(away_team)

        try:
            for lineup in home_lineups:
                home_timestream = game.time_by_lineup(lineup)
            for lineup in away_lineups:
                away_timestream = game.time_by_lineup(lineup)
            home_minutes = compute_ts_length(home_timestream)
            away_minutes = compute_ts_length(away_timestream)

            print('Home team: {} minutes, Away team: {} minutes'.format(home_minutes, away_minutes))

        except Exception as ex:
            print('Oh no, something terrible happened while computing lineups for {}'.format(game))
            print(ex)


def import_pbp(pbp_file):

    print('importing {}'.format(pbp_file))

    json_data = json.load(open(pbp_file, 'r'))
    game_id = json_data['league']['season']['eventType'][0]['events'][0]['eventId']

    print(game_id)
    pbp.update({'league.season.eventType.0.events.0.eventId': game_id}, json_data, upsert=True)


def import_pbp_files(files):

    for pbp_file in files:
        import_pbp(pbp_file)


def calc_all_player_times(year, recompute=False):

    class TimeComputationError(Exception):

        def __init__(self, msg):
            self.msg = msg
        def __str__(self):
            return self.msg

    all_players = players.find({}).sort('id', pymongo.ASCENDING)

    print('Loading the {}-{} NBA season'.format(year, year + 1))
    season = Season(year)
    print('Loaded season')
    print('Computing time on court for all players in all games...')

    for player_data in all_players:
        player = Player(player_data['id'])
        games_played = season.get_player_games_in_range(player)
        for game in games_played:
            print('Calculating time on court for {} ({}) in {} ({})'.format(player, player.id, game, game.id))
            boxscore_minutes = game.player_boxscore(player)['totalSecondsPlayed'] / 60.0
            if boxscore_minutes > 0:
                time_on_court = player.time_on_court(game, recompute=recompute)
                computed_minutes = compute_ts_length(time_on_court, unit='minutes')
            else:
                # there's never anything to calculate anyway
                computed_minutes = 0
            if not abs(computed_minutes - boxscore_minutes) <= 0.5:
                print('In computing playing time for {} ({}) in {} ({}):'.format(player, player.id, game, game.id),
                      file=sys.stderr)
                print('Discrepancy between computed time: {0:2.2f}, and boxscore time: {1:2.2f}'.format(computed_minutes, boxscore_minutes),
                      file=sys.stderr)
                #raise TimeComputationError('Discrepancy between computed time: {}, and boxscore time: {}'.format(computed_minutes, boxscore_minutes)

            else:
                print('{} played {} minutes in {}'.format(player, round(computed_minutes, 3), game))


def fix_broken_times(err_file):

    with open(err_file, 'r') as f:
        for line in f:
            matches = re.findall('\([\d]+\)', line)
            if matches and matches != []:
                ids = map(lambda x: int(x.replace('(', '').replace(')', '')), matches)
                player_id, game_id = ids[0], ids[1]
                player = Player(player_id)
                game = Game(game_id)
                print('Calculating time on court for {} ({}) in {} ({})'.format(player, player.id, game, game.id))
                time_on_court = player.time_on_court(game, recompute=True)
                computed_minutes = compute_ts_length(time_on_court, unit='minutes')
                boxscore_minutes = game.player_boxscore(player)['totalSecondsPlayed'] / 60.0
                if not abs(computed_minutes - boxscore_minutes) <= 1.0:
                    print('In computing playing time for {} ({}) in {} ({}):'.format(player, player.id, game, game.id), file=sys.stderr)
                    print('Discrepancy between computed time: {0:2.2f}, and boxscore time: {1:2.2f}'.format(computed_minutes, boxscore_minutes), file=sys.stderr)
                else:
                    print('{} played {} minutes in {}'.format(player, round(computed_minutes, 3), game))


def compute_global_features(season, start_date=None, end_date=None, output_file=None):

    pass


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--operation', dest='operation')
    parser.add_argument('-fn', '--firstname', dest='player_firstname')
    parser.add_argument('-ln', '--lastname', dest='player_lastname')
    parser.add_argument('-pt', '--plot_type', dest='plot_type', default='hexbin')
    parser.add_argument('-gid', '--game_id', dest='game_id', type=int)
    parser.add_argument('-if', '--input_file', dest='input_file', nargs='*')
    parser.add_argument('-of', '--output_file', dest='output_file')
    parser.add_argument('--game-date', dest='game_date')
    parser.add_argument('--start-date', dest='start_date', type=lambda x: dt.datetime.strptime(x, '%Y-%m-%d'))
    parser.add_argument('--end-date', dest='end_date', type=lambda x: dt.datetime.strptime(x, '%Y-%m-%d'))
    parser.add_argument('--season', dest='season', type=int)
    parser.add_argument('--method', dest='method', default='LogReg', nargs='*')
    parser.add_argument('--window', dest='window', type=int, default=20)
    
    args = parser.parse_args()

    if args.operation == 'compute_timelines':

        compute_all_season_lineups(2013)

    if args.operation == 'import_pbp' and args.input_file:

        import_pbp_files(args.input_file)

    if args.operation == 'compute_player_times':

        calc_all_player_times(2013)

    if args.operation == 'fix_broken_times' and args.input_file:

        fix_broken_times(args.input_file[0])

    if args.operation == 'construct_global_features' and args.season:

        season = Season(args.season)

        if args.start_date:
            start_date = dtparser.parse(args.start_date)
        else:
            start_date = season.start_date

        if args.end_date:
            end_date = dtparser.parse(args.end_date)
        else:
            end_date = season.end_date

        str_format = '%Y-%m-%d'

        if args.output_file:
            output_file = args.output_file
        else:
            path = 'features-from-{}-to-{}'.format(start_date.strftime(str_format), end_date.strftime(str_format))
            output_file = os.path.join('season_data', str(season.season), path)

        print('Constructing global features for {}'.format(season))

        construct_global_features(season, start_date=start_date, end_date=end_date, output_file=output_file)

    if args.operation == 'construct_all_features' and args.season:

        season = Season(args.season)

        if args.window:
            window = args.window
        else:
            window = 20

        construct_all_features(season, window_size=window)

    if args.operation == 'predict_game' and args.season and args.game_id:

        season = Season(args.season)
        game = Game(args.game_id)

        if args.start_date:
            start_date = dtparser.parse(args.start_date)
        else:
            start_date = season.start_date

        if args.end_date:
            end_date = dtparser.parse(args.end_date)
        else:
            end_date = season.end_date

        str_format = '%Y-%m-%d'

        if args.input_file:
            input_file = args.input_file
        else:
            path = 'features-from-{}-to-{}'.format(start_date.strftime(str_format), end_date.strftime(str_format))
            input_file = os.path.join('season_data', str(season.season), path)

        if os.path.exists(input_file):
            predict_game_outcome(input_file, game, season)
        else:
            print('Only precomputed features currently supported!')

    if args.operation == 'predict_game' and args.season and args.game_date:

        season = Season(args.season)
        game_date = dtparser.parse(args.game_date)

        if args.start_date:
            start_date = dtparser.parse(args.start_date)
        else:
            start_date = season.start_date

        if args.end_date:
            end_date = dtparser.parse(args.end_date)
        else:
            end_date = season.end_date

        if args.method:
            method = args.method
        else:
            method = 'LogReg'

        predict_game_day(game_date, season, start_date, end_date, method=method)

    if args.operation == 'predict_season' and args.season:

        season = Season(args.season)
        odds_file = 'odds/{}/odds-from-{}-to-{}.csv'.format(args.season,
                                                            season.start_date.strftime('%Y-%m-%d'),
                                                            season.end_date.strftime('%Y-%m-%d'))
        odds_data = pd.read_csv(odds_file)

        for method in args.method:

            print('Generating predictions using {}'.format(method))
            results = predict_all_games(season, args.window, method=method)

            game_ids = [res['game'].id for res in results]

            data = pd.DataFrame(columns=['game_date',
                                         'home_team',
                                         'away_team',
                                         'spread',
                                         'prediction',
                                         'prob_home_cover',
                                         'prob_away_cover',
                                         'prob_tie',
                                         'actual_margin'],
                                index=game_ids)
            data.index.name = 'game_id'

            # import pdb; pdb.set_trace();

            for i, result in enumerate(results):

                game = result['game']
                scores = result['classes']
                score_distribution = result['probabilities']
                prediction = result['prediction']

                odds_for_game = odds_data[odds_data.game_id == game.id]
                spread = odds_for_game.spread.values[0]

                prob_home_cover = 0
                prob_away_cover = 0
                prob_tie = 0

                probs_file = os.path.join('predictions', str(season.season), 'probabilities', str(game.id))
                writer = csv.writer(open(probs_file, 'w'))

                for score, prob in zip(scores, score_distribution):
                    if score < spread:
                        prob_away_cover += prob
                    elif score > spread:
                        prob_home_cover += prob
                    elif score == spread:
                        prob_tie += prob
                    writer.writerow([score, prob])

                data.iloc[i]['game_date'] = game.date.strftime('%Y-%m-%d')
                data.iloc[i]['home_team'] = game.home_team.id
                data.iloc[i]['away_team'] = game.away_team.id
                data.iloc[i]['spread'] = spread
                data.iloc[i]['prediction'] = prediction
                data.iloc[i]['prob_home_cover'] = prob_home_cover
                data.iloc[i]['prob_away_cover'] = prob_away_cover
                data.iloc[i]['prob_tie'] = prob_tie
                data.iloc[i]['actual_margin'] = game.home_points - game.away_points

            data.to_csv('predictions/{0}/predictions_{1}.csv'.format(season.season, method))

    if args.operation == 'get-odds' and args.start_date and args.end_date and args.season:

        #print(args.start_date, args.end_date)
        game_odds = get_odds_from_donbest(args.start_date, args.end_date)
        game_odds.to_csv('odds/{}/odds-from-{}-to-{}.csv'.format(args.season,
                                                                 args.start_date.strftime('%Y-%m-%d'),
                                                                 args.end_date.strftime('%Y-%m-%d')))

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
        print('{} vs {}'.format(team1, team2))

        for q in q_starters.keys():
            player_ids = q_starters[q]
            print('Quarter {} starters:'.format(q))
            for player_id in player_ids:
                fn, ln = look_up_player_name(player_id)
                print(fn, ln)

    if args.operation == 'construct_odds_csv' and args.input_file is not None and args.output_file is not None:

        construct_odds_csv(args.input_file, args.output_file)

    if args.operation == 'plot_all_game_charts' and args.game_id is not None:

        plot_all_game_charts(args.game_id)


    if args.operation == 'cluster_players_defense' and args.output_file is not None:

        cluster_players_defense(args.output_file)

    if args.operation == 'cluster_teams_defense' and args.output_file is not None:
            
        cluster_teams_defense(args.output_file)
