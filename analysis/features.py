from __future__ import division

__author__ = 'jerry'

import datetime as dt
import numpy as np
import pymongo
import pandas as pd
import os

from pprint import pprint

from Boxscore import PlayerBoxscore, TeamBoxscore
from Player import Player
from settings import players
from clustering import compute_player_clusters, find_member_in_clusters
from tqdm import *

output_headers =                 ['home_points',
                                      'home_eff_field_goal_pct',
                                      'home_3_pt_pct',
                                      'home_def_reb_pct',
                                      'home_off_reb_pct',
                                      'home_asst_pct',
                                      'home_block_pct',
                                      'home_steal_pct',
                                      'home_off_tov_pct',
                                      'home_def_tov_pct',
                                      'home_free_throw_pct',
                                      'home_free_throw_rate',
                                      'home_def_rtg',
                                      'home_off_rtg',
                                      'home_days_rest',
    ## features for individual players
    ## 7 offensive players, ranked by minutes
                                      'home_p0_off',
                                      'home_p1_off',
                                      'home_p2_off',
                                      'home_p3_off',
                                      'home_p4_off',
                                      'home_p5_off',
                                      'home_p6_off',
    ## 7 defensive players, ranked by minutes
                                      'home_p0_def',
                                      'home_p1_def',
                                      'home_p2_def',
                                      'home_p3_def',
                                      'home_p4_def',
                                      'home_p5_def',
                                      'home_p6_def',
    ## away team
                                      'away_points',
                                      'away_eff_field_goal_pct',
                                      'away_3_pt_pct',
                                      'away_def_reb_pct',
                                      'away_off_reb_pct',
                                      'away_asst_pct',
                                      'away_block_pct',
                                      'away_steal_pct',
                                      'away_off_tov_pct',
                                      'away_def_tov_pct',
                                      'away_free_throw_pct',
                                      'away_free_throw_rate',
                                      'away_def_rtg',
                                      'away_off_rtg',
                                      'away_days_rest',
    ## features for individual players
    ## 7 offensive players, ranked by minutes
                                      'away_p0_off',
                                      'away_p1_off',
                                      'away_p2_off',
                                      'away_p3_off',
                                      'away_p4_off',
                                      'away_p5_off',
                                      'away_p6_off',
    ## 7 defensive players, ranked by minutes
                                      'away_p0_def',
                                      'away_p1_def',
                                      'away_p2_def',
                                      'away_p3_def',
                                      'away_p4_def',
                                      'away_p5_def',
                                      'away_p6_def',]

def team_ocluster_features(team, season, start_date=None, end_date=None):

    games_played = season.get_team_games_in_range(team, start_date, end_date)

    team_boxscore = TeamBoxscore()
    opp_boxscore = TeamBoxscore()
    team_pos = 0

    for i, game in enumerate(games_played):
        opponent = game.opponent(team)

        game_t_boxscore = game.team_boxscore(team)['teamStats']
        game_o_boxscore = game.team_boxscore(opponent)['teamStats']
        team_boxscore = team_boxscore + TeamBoxscore(game_t_boxscore)
        opp_boxscore = opp_boxscore + TeamBoxscore(game_o_boxscore)

        team_pos += game.possessions(team)

    if team_pos == 0:
        return [team.id, 0, 0, 0, 0, 0]

    fgm = team_boxscore.field_goals_made
    fga = team_boxscore.field_goals_attempted
    fta = team_boxscore.free_throws_attempted
    ftm = team_boxscore.free_throws_made
    tov = team_boxscore.turnovers_total
    orb = team_boxscore.rebounds_offensive
    threes = team_boxscore.three_point_field_goals_made
    opp_drb = opp_boxscore.rebounds_defensive
    points = team_boxscore.points

    ortg = season.ortg(team, start_date, end_date)

    #print fgm, fga, threes, orb, opp_drb

    efg_pct = (fgm + 0.5 * threes) / fga
    tov_pct = 100 * tov / (fga + 0.44 * fta + tov)
    orb_pct = 100 * orb / (opp_drb + orb)
    ft_fga = ftm / fga

    features = [team.id, efg_pct, tov_pct, orb_pct, ft_fga, ortg]

    return features


def team_dcluster_features(team, season, start_date=None, end_date=None):

    games_played = season.get_team_games_in_range(team, start_date, end_date)

    team_boxscore = TeamBoxscore()
    opp_boxscore = TeamBoxscore()
    team_pos = 0

    for i, game in enumerate(games_played):
        opponent = game.opponent(team)

        game_t_boxscore = game.team_boxscore(team)['teamStats']
        game_o_boxscore = game.team_boxscore(opponent)['teamStats']
        team_boxscore = team_boxscore + TeamBoxscore(game_t_boxscore)
        opp_boxscore = opp_boxscore + TeamBoxscore(game_o_boxscore)

        team_pos += game.possessions(team)

    # if there are no possessions, abort
    if team_pos == 0:
        return [team.id, 0, 0, 0, 0, 0]

    opp_fta = opp_boxscore.free_throws_attempted
    opp_ftm = opp_boxscore.free_throws_made
    drb = team_boxscore.rebounds_defensive
    opp_threes = opp_boxscore.three_point_field_goals_made
    opp_drb = opp_boxscore.rebounds_defensive
    opp_orb = opp_boxscore.rebounds_offensive
    opp_tov = opp_boxscore.turnovers_total
    opp_fga = opp_boxscore.field_goals_attempted
    opp_fgm = opp_boxscore.field_goals_made
    opp_points = opp_boxscore.points

    drtg = season.drtg(team, start_date, end_date)

    #print opp_threes, opp_drb, opp_orb, opp_tov, opp_fga, opp_fgm

    opp_efg_pct = (opp_fgm + 0.5 * opp_threes) / opp_fga
    opp_tov_pct = 100 * opp_tov / (opp_fga + 0.44 * opp_fta + opp_tov)
    drb_pct = 100 * drb / (opp_orb + drb)
    opp_ft_fga = opp_ftm / opp_fga

    features = [team.id, opp_efg_pct, opp_tov_pct, drb_pct, opp_ft_fga, drtg]

    return features

def player_ocluster_features(player, season, start_date=None, end_date=None):

    games_played = season.get_player_games_in_range(player, start_date, end_date)

    player_boxscore = PlayerBoxscore()
    team_boxscore = TeamBoxscore()
    opp_boxscore = TeamBoxscore()
    team_pos = 0
    opp_drb = 0

    for i, game in enumerate(games_played):

        game_p_boxscore = game.player_boxscore(player)
        player_boxscore = player_boxscore + PlayerBoxscore(game_p_boxscore)
        team = game.player_team(player)
        opponent = game.opponent(team)
        game_t_boxscore = game.team_boxscore(team)['teamStats']
        game_o_boxscore = game.team_boxscore(opponent)['teamStats']
        team_boxscore = team_boxscore + TeamBoxscore(game_t_boxscore)
        opp_boxscore = opp_boxscore + TeamBoxscore(game_o_boxscore)

        team_pos += game.possessions(team)

    try:
        mp = player_boxscore.total_seconds_played / 60.0

        if mp > 0:
            ast = player_boxscore.assists
            fgm = player_boxscore.field_goals_made
            fga = player_boxscore.field_goals_attempted
            ftm = player_boxscore.free_throws_made
            fta = player_boxscore.free_throws_attempted
            tov = player_boxscore.turnovers
            tpa = player_boxscore.three_point_field_goals_attempted
            tpm = player_boxscore.three_point_field_goals_made
            orb = player_boxscore.rebounds_offensive
            pts = player_boxscore.points

            team_pts = team_boxscore.points
            team_mp = team_boxscore.minutes
            team_fgm = team_boxscore.field_goals_made
            team_pts = team_boxscore.points
            team_orb = team_boxscore.rebounds_offensive
            opp_drb = opp_boxscore.rebounds_defensive

            team_ortg = 100 * team_pts / team_pos

            ast_pct = 100 * ast / (((mp / (team_mp / 5)) * team_fgm) - fgm)
            ts_pct = pts / (2 * (fga + 0.44 * fta))
            orb_pct = 100 * (orb * (team_mp / 5)) / (mp * (team_orb + opp_drb))
            mp_pct = 100 * mp / (team_mp / 5)
            usg = season.player_usage(player, start_date, end_date)
            ortg = season.player_ortg(player, start_date, end_date)

            #print team_ortg, ortg

            ortg_pct = 100 * (1 + (ortg - team_ortg) / team_ortg)

            features = [player.id, ast_pct, ts_pct, orb_pct, usg, ortg, mp_pct]
        else:
            features = [player.id, 0, 0, 0, 0, 0, 0]

    except ZeroDivisionError as ex1:
        # silently set all the features to zero
        features = [player.id, 0, 0, 0, 0, 0, 0]
    except Exception as ex2:
        # fail on anything else
        raise ex2

    return features


def player_dcluster_features(player, season, start_date=None, end_date=None):

    games_played = season.get_player_games_in_range(player, start_date=start_date, end_date=end_date)

    player_boxscore = PlayerBoxscore()
    team_boxscore = TeamBoxscore()
    opp_boxscore = TeamBoxscore()
    team_pos = 0
    opp_pos = 0

    for i, game in enumerate(games_played):

        game_p_boxscore = game.player_boxscore(player)
        player_boxscore = player_boxscore + PlayerBoxscore(game_p_boxscore)
        team = game.player_team(player)
        opponent = game.opponent(team)
        game_t_boxscore = game.team_boxscore(team)['teamStats']
        game_o_boxscore = game.team_boxscore(opponent)['teamStats']
        team_boxscore = team_boxscore + TeamBoxscore(game_t_boxscore)
        opp_boxscore = opp_boxscore + TeamBoxscore(game_o_boxscore)

        team_pos += game.possessions(team)
        opp_pos += game.possessions(opponent)

    try:
        mp = player_boxscore.total_seconds_played / 60.0

        if mp > 0:

            drb = player_boxscore.rebounds_defensive
            pf = player_boxscore.personal_fouls
            stl = player_boxscore.steals
            blk = player_boxscore.blocked_shots

            team_mp = team_boxscore.minutes
            team_blk = team_boxscore.blocked_shots
            team_stl = team_boxscore.steals
            team_drb = team_boxscore.rebounds_defensive
            team_pf = team_boxscore.personal_fouls

            opp_fta = opp_boxscore.free_throws_attempted
            opp_ftm = opp_boxscore.free_throws_made
            opp_fga = opp_boxscore.field_goals_attempted
            opp_fgm = opp_boxscore.field_goals_made
            opp_orb = opp_boxscore.rebounds_offensive
            opp_pts = opp_boxscore.points
            opp_tov = opp_boxscore.turnovers_total
            opp_mp = opp_boxscore.minutes
            opp_3pa = opp_boxscore.three_point_field_goals_attempted

            blk_pct = 100 * (blk * (team_mp / 5)) / (mp * (opp_fga - opp_3pa))
            stl_pct = 100 * (stl * (team_mp / 5)) / (mp * opp_pos)
            drb_pct = 100 * (drb * (team_mp / 5)) / (mp * (team_drb + opp_orb))
            pf_pct = 100 * pf / team_pf
            mp_pct = 100 * mp / (team_mp / 5)
            drtg = season.player_drtg(player, start_date, end_date)

            features = [player.id, blk_pct, stl_pct, drb_pct, drtg, pf_pct, mp_pct]
        else:
            features = [player.id, 0, 0, 0, 0, 0, 0]

    except ZeroDivisionError as ex1:
        # silently set all the features to zero
        features = [player.id, 0, 0, 0, 0, 0, 0]
    except Exception as ex2:
        # fail on anything else
        raise ex2

    return features


def construct_global_features(season, team=None, start_date=None, end_date=None, game_date=None, output_file=None):

    if output_file is not None and os.path.exists(output_file):
        data = pd.read_csv(output_file, index_col=0)
        return data

    # off_player_file = os.path.join('season_data', str(season.season), 'player_offense_features.csv')
    # def_player_file = os.path.join('season_data', str(season.season), 'player_defense_features.csv')

    # off_player_data = pd.read_csv(off_player_file, delimiter=',', index_col=0)
    # def_player_data = pd.read_csv(def_player_file, delimiter=',', index_col=0)


    # print 'Extracting all player features...'
    # player_features = get_all_player_features(season, start_date, end_date)
    # player_features = player_features[player_features.mp_pct > 0]
    #
    # player_ofeatures = player_features[['ast_pct', 'ts_pct', 'orb_pct', 'usg', 'ortg', 'mp_pct']]
    # player_dfeatures = player_features[['blk_pct', 'stl_pct', 'drb_pct', 'drtg', 'pf_pct', 'mp_pct']]
    #
    # print 'Clustering offense...'
    # player_oclusters, off_model = compute_player_clusters(player_ofeatures, clusters=7, method='KMeans')
    # print 'Clustering defense...'
    # player_dclusters, def_model = compute_player_clusters(player_dfeatures, clusters=7, method='KMeans')
    #
    # o_cluster_labels = player_oclusters.keys()
    # d_cluster_labels = player_dclusters.keys()

    one_day = dt.timedelta(days=1)

    # import pdb; pdb.set_trace()

    if team and game_date:
        games = season.get_team_games_in_range(team, game_date, game_date)
    elif game_date:
        games = season.get_all_games_in_range(game_date, game_date)
    else:
        games = season.get_all_games_in_range(start_date, end_date)
    game_ids = [game.id for game in games]

    data = pd.DataFrame(index=game_ids, columns=output_headers)

    for i, game in enumerate(games):

        #print 'Computing features for {} in {}'.format(game, season)
        # player features

        home_team = game.home_team
        away_team = game.away_team

        # home_players = sorted(game.home_players, key=lambda p: p.time_played(game), reverse=True)
        # away_players = sorted(game.away_players, key=lambda p: p.time_played(game), reverse=True)

        # for player in home_players:
        #
        #     player_oclass = find_member_in_clusters(player_oclusters, player)
        #     player_dclass = find_member_in_clusters(player_dclusters, player)
        #
        #     if player_oclass is not None and player_dclass is not None:
        #
        #         o_label = 'home_p{}_off'.format(int(player_oclass))
        #         d_label = 'home_p{}_def'.format(int(player_dclass))
        #
        #         # print o_label, d_label
        #
        #         data.iloc[i][o_label] = 1
        #         data.iloc[i][d_label] = 1
        #
        # for player in away_players:
        #
        #     player_oclass = find_member_in_clusters(player_oclusters, player)
        #     player_dclass = find_member_in_clusters(player_dclusters, player)
        #
        #     if player_oclass is not None and player_dclass is not None:
        #
        #         o_label = 'away_p{}_off'.format(int(player_oclass))
        #         d_label = 'away_p{}_def'.format(int(player_dclass))
        #
        #         # print o_label, d_label
        #
        #         data.iloc[i][o_label] = 1
        #         data.iloc[i][d_label] = 1

        # team features

        data.iloc[i]['home_days_rest'] = home_team.days_rest(season, game)
        data.iloc[i]['away_days_rest'] = away_team.days_rest(season, game)

        # import pdb; pdb.set_trace()

        home_ofeatures = team_ocluster_features(home_team, season, start_date, game.date - one_day)
        home_dfeatures = team_dcluster_features(home_team, season, start_date, game.date - one_day)
        away_ofeatures = team_ocluster_features(away_team, season, start_date, game.date - one_day)
        away_dfeatures = team_dcluster_features(away_team, season, start_date, game.date - one_day)

        if all(i > 0 for i in home_ofeatures[1:]) and all(j > 0 for j in away_ofeatures[1:]):

            data.iloc[i]['home_points'] = game.home_points
            data.iloc[i]['home_free_throw_rate'] = home_ofeatures[4]
            data.iloc[i]['home_eff_field_goal_pct'] = home_ofeatures[1]
            data.iloc[i]['home_def_reb_pct'] = home_dfeatures[3]
            data.iloc[i]['home_off_reb_pct'] = home_ofeatures[3]
            data.iloc[i]['home_off_tov_pct'] = home_ofeatures[2]
            data.iloc[i]['home_def_tov_pct'] = home_dfeatures[2]
            data.iloc[i]['home_def_rtg'] = home_dfeatures[5]
            data.iloc[i]['home_off_rtg'] = home_ofeatures[5]

            data.iloc[i]['away_points'] = game.away_points
            data.iloc[i]['away_free_throw_rate'] = away_ofeatures[4]
            data.iloc[i]['away_eff_field_goal_pct'] = away_ofeatures[1]
            data.iloc[i]['away_def_reb_pct'] = away_dfeatures[3]
            data.iloc[i]['away_off_reb_pct'] = away_ofeatures[3]
            data.iloc[i]['away_off_tov_pct'] = away_ofeatures[2]
            data.iloc[i]['away_def_tov_pct'] = away_dfeatures[2]
            data.iloc[i]['away_def_rtg'] = away_dfeatures[5]
            data.iloc[i]['away_off_rtg'] = away_ofeatures[5]

    data.fillna(0, inplace=True)
    data.index.name = 'game_id'

    if output_file is not None:
        data.to_csv(output_file)

    return data


def construct_all_features(season, window_size=20):

    window = dt.timedelta(days=window_size)
    one_day = dt.timedelta(days=1)
    date = season.start_date

    while date <= (season.end_date - window):

        start_date = date
        end_date = date + window

        print 'Computing features for {} from {} to {}'.format(season, start_date, end_date)

        str_format = '%Y-%m-%d'
        file_name = 'features-from-{}-to-{}'.format(start_date.strftime(str_format), end_date.strftime(str_format))
        path = os.path.join('season_data', str(season.season), file_name)

        construct_global_features(season, start_date=start_date, end_date=end_date, output_file=path)

        date = date + one_day


def merge_team_features(off_file, def_file, output_file):

    off_data = pylab.genfromtxt(off_file, delimiter=',')
    def_data = pylab.genfromtxt(def_file, delimiter=',')

    print len(off_data[0])
    print len(def_data)

    writer = csv.writer(open(output_file, 'w'))

    off_data = sorted(off_data, key=lambda x: x[0])
    def_data = sorted(def_data, key=lambda x: x[0])

    for oline, dline in zip(off_data, def_data):
        comb_line = pylab.concatenate((oline, dline[1:]))
        writer.writerow(comb_line)

def add_team_clusters_to_csv(input_filename, output_filename):

    reader = csv.reader(open(input_filename, 'r'))
    writer = csv.writer(open(output_filename, 'w'))
    headers = reader.next()

    headers.append('home_oclass')
    headers.append('home_dclass')
    headers.append('home_tclass')
    headers.append('away_oclass')
    headers.append('away_dclass')
    headers.append('away_tclass')

    writer.writerow(headers)

    team_oclusters, off_gmm = compute_team_clusters('team_features_offense_w_id.csv')
    team_dclusters, def_gmm = compute_team_clusters('team_features_defense_w_id.csv')
    team_tclusters, tot_gmm = compute_team_clusters('team_features_combined.csv')

    for line in reader:

        home_team = int(line[3].strip())
        away_team = int(line[4].strip())

        home_oclass = find_member_in_clusters(team_oclusters, home_team)
        home_dclass = find_member_in_clusters(team_dclusters, home_team)
        home_tclass = find_member_in_clusters(team_tclusters, home_team)
        away_oclass = find_member_in_clusters(team_oclusters, away_team)
        away_dclass = find_member_in_clusters(team_dclusters, away_team)
        away_tclass = find_member_in_clusters(team_tclusters, away_team)

        writer.writerow(line + [home_oclass, home_dclass, home_tclass, away_oclass, away_dclass, away_tclass])

def construct_odds_csv(input_filename, output_filename):

    reader = csv.reader(open(input_filename, 'r'))
    stat_cats = ['PTS', 'FG%', '3P%', 'DRB%', 'ORB%', 'AST', 'BLK', 'STL',
                 'TOV', 'FT%', 'PIP', 'PTO', '2CP', 'FBP', 'PFL', 'DRTG', 'ORTG', 'REST']

    stat_headers = {'PTS': 'points',
                    'FG%': 'field_goal_pct',
                    '3P%': '3_pt_pct',
                    'DRB%': 'def_reb_pct',
                    'ORB%': 'off_reb_pct',
                    'AST': 'assists',
                    'BLK': 'blocks',
                    'STL': 'steals',
                    'TOV': 'turnovers',
                    'FT%': 'free_throw_pct',
                    'PIP': 'pts_in_paint',
                    'PTO': 'pts_off_tov',
                    '2CP': '2nd_chance_pts',
                    'FBP': 'fast_break_pts',
                    'PFL': 'fouls',
                    'DRTG': 'def_rtg',
                    'ORTG': 'off_rtg'}

    output_headers = reader.next() + ['home_points',
                                      'home_field_goal_pct',
                                      'home_3_pt_pct',
                                      'home_def_reb_pct',
                                      'home_off_reb_pct',
                                      'home_assists',
                                      'home_blocks',
                                      'home_steals',
                                      'home_turnovers',
                                      'home_free_throw_pct',
                                      'home_pts_in_paint',
                                      'home_pts_off_tov',
                                      'home_2nd_chance_pts',
                                      'home_fast_break_pts',
                                      'home_fouls',
                                      'home_def_rtg',
                                      'home_off_rtg',
                                      'home_days_rest',
    ## features for individual players
    ## 7 offensive players, ranked by minutes
                                      'home_p1_off',
                                      'home_p2_off',
                                      'home_p3_off',
                                      'home_p4_off',
                                      'home_p5_off',
                                      'home_p6_off',
                                      'home_p7_off',
    ## 7 defensive players, ranked by minutes
                                      'home_p1_def',
                                      'home_p2_def',
                                      'home_p3_def',
                                      'home_p4_def',
                                      'home_p5_def',
                                      'home_p6_def',
                                      'home_p7_def',
    ## away team
                                      'away_points',
                                      'away_field_goal_pct',
                                      'away_3_pt_pct',
                                      'away_def_reb_pct',
                                      'away_off_reb_pct',
                                      'away_assists',
                                      'away_blocks',
                                      'away_steals',
                                      'away_turnovers',
                                      'away_free_throw_pct',
                                      'away_pts_in_paint',
                                      'away_pts_off_tov',
                                      'away_2nd_chance_pts',
                                      'away_fast_break_pts',
                                      'away_fouls',
                                      'away_def_rtg',
                                      'away_off_rtg',
                                      'away_days_rest',
    ## features for individual players
    ## 7 offensive players, ranked by minutes
                                      'away_p1_off',
                                      'away_p2_off',
                                      'away_p3_off',
                                      'away_p4_off',
                                      'away_p5_off',
                                      'away_p6_off',
                                      'away_p7_off',
    ## 7 defensive players, ranked by minutes
                                      'away_p1_def',
                                      'away_p2_def',
                                      'away_p3_def',
                                      'away_p4_def',
                                      'away_p5_def',
                                      'away_p6_def',
                                      'away_p7_def',]

    off_data = pylab.genfromtxt('offense_clusters_w_id.csv', delimiter=',')
    def_data = pylab.genfromtxt('defense_clusters_w_id.csv', delimiter=',')

    print 'Clustering offense...'
    player_oclusters, off_gmm = compute_player_clusters('offense_clusters_w_id.csv', clusters=10, method='GMM')
    print 'Clustering defense...'
    player_dclusters, def_gmm = compute_player_clusters('defense_clusters_w_id.csv', clusters=10, method='GMM')

    print 'Constructing odds data...'
    output_lines = [output_headers]

    writer = csv.writer(open(output_filename, 'w'))
    writer.writerow(output_headers)

    for line in reader:
        year = int(line[0].strip())
        month = int(line[1].strip())
        day = int(line[2].strip())
        game_day = dt.date(year=year, month=month, day=day)
        home_team = int(line[3].strip())
        away_team = int(line[4].strip())

        print game_day, home_team, away_team

        try:
            game_id = look_up_contest_id(game_day, home_team)

            home_players = game_players(game_id, home_team)[0:7]
            away_players = game_players(game_id, away_team)[0:7]



            home_box, away_box = boxscore_stats(game_day, home_team)

            # insert the home stats
            for stat in stat_cats:
                line.append(home_box[stat])

            for hp in home_players:
                player_oclass = find_member_in_clusters(player_oclusters, hp)
                line.append(player_oclass)

            for hp in home_players:
                player_dclass = find_member_in_clusters(player_dclusters, hp)
                line.append(player_dclass)

            # insert the away stats
            for stat in stat_cats:
                line.append(away_box[stat])

            for ap in away_players:
                player_oclass = find_member_in_clusters(player_oclusters, ap)
                line.append(player_oclass)

            for ap in away_players:
                player_dclass = find_member_in_clusters(player_dclusters, ap)
                line.append(player_dclass)

        except Exception as ex:
            print ex
            print 'Game not found... possibly a game was postponed/canceled'

        writer.writerow(line)
        output_lines.append(line)


def get_all_player_features(season, start_date=None, end_date=None, recompute=False):

    all_players = players.find({}).sort('id', pymongo.ASCENDING)

    o_header = ['ast_pct', 'ts_pct', 'orb_pct', 'usg', 'ortg', 'mp_pct']
    d_header = ['blk_pct', 'stl_pct', 'drb_pct', 'drtg', 'pf_pct']

    str_format = '%Y-%m-%d'
    feature_file = 'player-features-from-{}-to-{}.csv'.format(start_date.strftime(str_format), end_date.strftime(str_format))
    path = os.path.join('season_data', str(season.season), feature_file)

    if os.path.exists(path) and not recompute:
        player_features = pd.read_csv(path, index_col=0)
    else:

        feature_headers = o_header + d_header

        index = []
        all_features = []

        for i, player_data in enumerate(all_players):
            player = Player(player_data['id'])
            index.append(player.id)
            #print 'Extracting offensive features for {} from the {}'.format(player, season)
            o_features = player_ocluster_features(player, season, start_date, end_date)
            #print 'Extracting defensive features for {} from the {}'.format(player, season)
            d_features = player_dcluster_features(player, season, start_date, end_date)

            # drop the id in d_features
            all_features.append(o_features[1:] + d_features[1:-1])

        player_features = pd.DataFrame(data=all_features, columns=feature_headers, index=index)
        player_features.index.name = 'id'
        player_features.to_csv(path)

    return player_features

