#!/usr/bin/env python
from __future__ import division

import os
import sys
import json
import pylab
import datetime as dt
import urllib2
import pymongo
import argparse
import csv
import requests

import matplotlib.pyplot as mpl
import pylab
import numpy as np
#import statsmodels.api as sm
import dateutil

from bs4 import BeautifulSoup

from pprint import pprint
from scipy.spatial.distance import euclidean
from scipy.interpolate import spline
from itertools import izip_longest, product, combinations

from matplotlib.patches import Arc, RegularPolygon, Circle
from matplotlib.colors import Normalize, BoundaryNorm, ListedColormap
from matplotlib.colorbar import ColorbarBase
from matplotlib import gridspec

#from mpldatacursor import datacursor

from sklearn.manifold import MDS
from sklearn.cluster import AffinityPropagation, DBSCAN, KMeans, Ward
from sklearn.mixture import GMM, DPGMM
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.preprocessing import StandardScaler



start_date = dt.datetime(2012, 10, 07)

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




def safe_list_get(l, k, default=None):
    try:
        return l[k]
    except IndexError:
        return default
    
    

def get_boxscore(date, game_id, output_file=None):

    # boxscore_url = base + '/game/' + format_date(date) + '/{0}/boxscore.json'.format(game_id)
    boxscore_url = cnn_base + 'gameflash' + format_date(date) + '{0}_boxscore.json'.format(game_id)
    print boxscore_url

    try:
        if output_file is not None and os.path.exists(output_file):
            data = open(output_file, 'r').read()
        else:
            data = urllib2.urlopen(boxscore_url).read()
            # strip away some extraneous junk
            data = data[16:-2]

            if output_file is not None:
                of = open(output_file, 'w')
                of.write(data)

        boxscore_json = json.loads(data)

    except Exception as ex:
        print ex
        print 'Data not found'
        return {}

    return boxscore_json

def get_shots(date, game_id, output_file=None):
    # We need to get shot data from ESPN, which uses different ids...

    boxscore_data = get_boxscore(date, game_id)

    home_data = boxscore_data['sports_content']['game']['home']
    away_data = boxscore_data['sports_content']['game']['visitor']

    home_team = home_data['nickname']
    away_team = away_data['nickname']

    home_players = home_data['players']
    away_players = away_data['players']

    home_espn_id = team_to_espn_ids[home_team]
    away_espn_id = team_to_espn_ids[away_team]





def get_team_stats (game_day, team_id, stat):

    game_id = look_up_contest_id(game_day, team_id)
    
    game = boxscores.find_one({'boxscore.meta.contest.id': game_id})

    stat_data = [data for data in game['boxscore']['team-stats']['statistics']
                 if data['name'] == stat]

    return stat_data

def game_teams (game_id):

    game = boxscores.find_one({'boxscore.meta.contest.id': game_id})

    teams = game['boxscore']['contest']['team']
    
    return teams[0]['name'], teams[0]['id'], teams[1]['name'], teams[1]['id']

def game_day (game_id, type='str'):

    game = boxscores.find_one({'boxscore.meta.contest.id': game_id})

    if type == 'str':
        return game['boxscore']['meta']['game-date']['url']
    elif type == 'datetime':
        game_date = game['boxscore']['meta']['game-date']
        year = game_date['year']
        month = game_date['month']
        day = game_date['day']
        game_day = dt.date(year=year, month=month, day=day)

        return game_day

def player_name (player_id):

    player = players.find_one({'id': int(player_id)})

    return player['first-name'], player['last-name']

def quarter_starters(game_id):

    game = pbp.find_one({'playbyplay.contest.id': str(game_id)})
    team1, team1_id, team2, team2_id = game_teams(game_id)

    plays = game['playbyplay']['plays']['play']

    quarter_starters = {}
    
    for q in (2, 3, 4):
        quarter_plays = sorted([play for play in plays if play['quarter'] == str(q)], reverse=True, key=play_time)

        players_used = []
        subs = []
        i = 0
        done = False
        
        while i < len(quarter_plays) and not done:
            play = quarter_plays[i]
            player1_id = play['player1-id']
            player2_id = play['player2-id']
            player3_id = play['player3-id']

            if play['event-desc'] == 'Substitution':
                subs.append(player1_id)
                
            if player1_id != "" and player1_id not in players_used and player1_id not in subs:
                players_used.append(player1_id)
            if player2_id != "" and player2_id not in players_used and player2_id not in subs:
                players_used.append(player2_id)
            if player3_id != "" and player3_id not in players_used and player3_id not in subs:
                players_used.append(player3_id)

            i += 1
            
            if len(players_used) == 10:
                done = True

        quarter_starters[q] = players_used

    return quarter_starters


def player_time_on_court(game_id, player_id, return_type='timestream'):

    game = pbp.find_one({'playbyplay.contest.id': str(game_id)})

    plays = game['playbyplay']['plays']['play']

    plays_subbed_in = [play for play in plays if play['event-desc'] == 'Substitution' and play['player1-id'] == str(player_id)]
    plays_subbed_out = [play for play in plays if play['event-desc'] == 'Substitution' and play['player2-id'] == str(player_id)]

    #pprint(plays_subbed_in)
    #pprint(plays_subbed_out)
    
    times_subbed_in = [dt.timedelta(minutes=((4 - int(play['quarter'])) * 12 + int(play['time-minutes'])),
                                    seconds=int(float(play['time-seconds'])))
                        for play in plays_subbed_in]
    
    times_subbed_out = [dt.timedelta(minutes=((4 - int(play['quarter'])) * 12 + int(play['time-minutes'])),
                                     seconds=int(float(play['time-seconds'])))
                        for play in plays_subbed_out]

    time_stream = []
    q_starters = quarter_starters(game_id)

    q2 = dt.timedelta(minutes=36)
    q3 = dt.timedelta(minutes=24)
    q4 = dt.timedelta(minutes=12)

    q_end_times = [q2, q3, q4]
    
    for q in q_starters.keys():
        q_start_time = dt.timedelta(minutes=((5 - q) * 12))
        if str(player_id) in q_starters[q]:
            times_subbed_in.append(q_start_time)

    times_subbed_in = sorted(times_subbed_in, reverse=True)

    i = 0
    j = 0
    
    while not check_time_consistency(times_subbed_in, times_subbed_out) and i < len(times_subbed_in):
        ti = times_subbed_in[i]
        if i + 1 < len(times_subbed_in):
            ti_next = times_subbed_in[i + 1]
        else:
            ti_next = dt.timedelta(minutes=0)

        to_arr = [to for to in times_subbed_out if to < ti and to > ti_next]

        #print map(str, to_arr)
        #print map(str, times_subbed_in)
        #print map(str, times_subbed_out)
        #print str(ti), str(ti_next)
        
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


    #print map(str, times_subbed_in)
    #print map(str, times_subbed_out)

    time_stream = zip(times_subbed_in, times_subbed_out)

    #for pair in time_stream:
    #    print str(pair[0]), str(pair[1])
    
    if return_type == 'timestream':
        return time_stream
    elif return_type == 'separate':
        return times_subbed_in, times_subbed_out

def player_starts_quarter(times_subbed_in, times_subbed_out, quarter):
    ## Player starts quarter iff player's first exit from the game during that quarter occurs
    ## between the quarter's start and end times, and without a previous entrance into the game.

    q_start = dt.timedelta(minutes=((5 - quarter) * 12))
    q_end = dt.timedelta(minutes=((4 - quarter) * 12))

    q_in_times = sorted([ti for ti in times_subbed_in if ti > q_end and ti <= q_start], reverse=True)
    q_out_times = sorted([to for to in times_subbed_out if to > q_end and to <= q_start], reverse=True)

    if q_out_times != [] and q_in_times != []:
        if q_out_times[0] > q_in_times[0]:
            return True
        else:
            return False
    elif q_out_times != [] and q_in_times == []:
        return True
    elif q_out_times == [] and q_in_times != []:
        return False
    elif q_out_times == [] and q_in_times == []:
        subs_in_before_q = sorted([ti for ti in times_subbed_in if ti > q_start])
        subs_out_before_q = sorted([to for to in times_subbed_out if to > q_start])
        

def player_ends_quarter(game_id, player_id, quarter):
    ## player ends quarter iff player's last entrance into the game during that quarter
    ## is not followed by a substitution
    pass

def player_times_on_court (player_id):

    games_played = pbp.find({'playbyplay.plays.play.player1-id': player_id})

    for game in games_played:
        game_id = int(game['playbyplay']['contest']['id'])
        # print player_time_on_court(game_id, player_id)

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


def game_players(game_id, team_id):

    game = boxscores.find_one({'boxscore.contest.id': game_id})
    player_stats = [team for team in game['boxscore']['player-stats']['team'] if team['id'] == team_id][0]
    players_and_minutes = [(float(player['total-seconds']['seconds']), player['id']) for player in player_stats['players']['player'] if player['total-seconds']['seconds'] > 0]
    sorted_pm = sorted(players_and_minutes, key=lambda x: x[0], reverse=True)

    player_ids = list(zip(*sorted_pm)[1])

    return player_ids

def lineup_combinations(game_id, team_id):

    player_ids = game_players(game_id, team_id)
    
    return combinations(player_ids, 5)

def game_stats_by_lineup(game_id, team_id, stats_team_id, stats):

    lineups = lineup_combinations(game_id, team_id)

    stats_by_lineup = []
    
    for i, lineup in enumerate(lineups):
        time_on_floor = multiple_player_overlap_improved(game_id, lineup)[0]
        if time_on_floor != []:
            stat_dict = {}
            for stat in stats:
                if stat == 'efg':
                    efg, total_made, total_threes, total_attempts = game_stats_by_time(game_id, stats_team_id, time_on_floor, stat)
                    stat_dict['efg'] = efg
                    stat_dict['total_made'] = total_made
                    stat_dict['total_threes'] = total_threes
                    stat_dict['total_attempts'] = total_attempts

            stats_by_lineup.append({'lineup': lineup, 'tof': time_on_floor, 'stats': stat_dict})

    return stats_by_lineup

def used_lineup(lineup, used_lineups):

    for used in used_lineups:
        if identical_lineups(used, lineup):
            return True

    return False

def identical_lineups(l1, l2):

    if len(l1) != len(l2):
        return False
    
    for i in l1:
        if i not in l2:
            return False

    for j in l2:
        if j not in l2:
            return False

    return True

def regress_lineups_team_efg_single_game(game_id, team_id):

    game_stats = game_stats_by_lineup(game_id, team_id, ['efg'])

    players = sorted(game_players(game_id, team_id))

    efgs = pylab.zeros(len(game_stats))
    X = pylab.zeros((len(game_stats), len(players) + 1))
    w = pylab.zeros(len(game_stats))
    
    for i, item in enumerate(game_stats):
        lineup = item['lineup']
        for player in lineup:
            ind = players.index(player)
            X[i][ind] = 1
        X[i][len(players)] = compute_ts_length(item['tof'])
        #w[i] = compute_ts_length(item['tof'])
        efgs[i] = item['stats']['efg']

    #print players
    
    result = sm.OLS(efgs, X).fit()

    #return [(player, param) for player, param in zip(players, result.params)]

    return result, players

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

def compute_ts_length(ts):

    seconds = 0
    for ti, to in ts:
        td = ti - to
        seconds += td.total_seconds()

    return seconds

def cumul_opp_efg_model(player_id):

    pass

def multiple_player_overlap_improved(game_id, players_on, players_off=None):

    player_times = []
    for player in players_on:
        t = player_time_on_court(game_id, player)
        player_times.append(t)

    shared_times = recursive_intersect(player_times)

    #if shared_times != []:
    #    print shared_times

    return shared_times

def multiple_player_overlap(game_id, players_on, players_off=None):

    # returns the times during which the players in players_on are on court
    # and the players in players_off are off court

    player_times_on = []

    used_pairs = []
    for player1, player2 in product(players_on, players_on):
        if player1 != player2 and (player1, player2) not in used_pairs:
            t = player_overlap(player1, player2, game_id)
            player_times_on.append(t)

            #fn1, ln1 = look_up_player_name(player1)
            #fn2, ln2 = look_up_player_name(player2)
            #print fn1, ln1, 'and', fn2, ln2
            #for i in t:
            #    print map(str, i)
                
            used_pairs.append((player1, player2))
            used_pairs.append((player2, player1))

    print player_times_on

    used_pairs = []
    shared_times = []

    
    #for ts1, ts2 in product(player_times_on, player_times_on):
    #    if ts1 != ts2 and (ts1, ts2) not in used_pairs:
    #        t = timestream_overlap(ts1, ts2)
    #        shared_times += t
    #        used_pairs.append((ts1, ts2))
    #        used_pairs.append((ts2, ts1))

    shared_times = merge_timestream(player_times_on)
    for i in range(len(players_on) - 3):
        shared_times = merge_timestream(shared_times)

    shared_times = [item for sublist in shared_times for item in sublist]
    shared_times = sorted(map(tuple, pylab.unique(shared_times).tolist()), reverse=True)

    return shared_times

def game_stats_by_time(game_id, team_id, timestream, stat):

    game = pbp.find_one({'playbyplay.contest.id': str(game_id)})
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

def pretty_print_times(times):

    for t in times:
        print map(str, t)
    print '-----'

def all_times_disjoint(list_of_times):

    for t1, t2 in combinations(list_of_times, 2):
        if times_overlap(t1, t2) is not None:
            return False

    return True

def intersect_all(times):

    new_times = []
    for t1, t2 in combinations(times, 2):
        t = times_overlap(t1, t2)
        if t is not None:
            new_times.append(t)
    return new_times

def recursive_intersect(timestream):

    new_timestream = []
    do_not_use = []

    #for item in timestream:
    #    pretty_print_times(item)
    #print '-----'
    
    if len(timestream) == 1:
        return timestream

    t1 = timestream[0]
    t2 = timestream[1]

    t1_int_t2 = intersect_all(t1 + t2)

    new_timestream.append(t1_int_t2)
    for t in timestream[2:]:
        new_timestream.append(t)
    
    return recursive_intersect(new_timestream)


def merge_timestream(ts):

    shared_times = []
    used_pairs = []
    for t1, t2 in product(ts, ts):
        if t1 != t2 and (t1, t2) not in used_pairs:
            t = timestream_overlap(t1, t2)
            shared_times.append(t)
            used_pairs.append((t1, t2))
            used_pairs.append((t2, t1))

    return shared_times
    #return sorted(map(tuple, pylab.unique(shared_times).tolist()), reverse=True)
    
def recursive_union(times, used, i):

    new_times = []

    if len(times) == 1:
        return times
   
    t0 = times[0]
    #used = []
    disjoint = 0
    for t in times[i:]:
        union = times_union(t0, t)
        if pylab.shape(union) == (2,):
            print 'nondisjoint:', t0, t
            new_times.append(union)
            used.append(t0)
            used.append(t)
        elif pylab.shape(union) == (2, 2):
            print 'disjoint'
            disjoint += 1
            
    print new_times

    for t in times:
        if t not in used:
            new_times.append(t)
            
    print len(times), len(new_times), len(used), disjoint

    if disjoint == len(new_times) + 1 or i > 5:
        print 'foo'
        return times

    return new_times + recursive_union(new_times, used, i+1)

def times_union(t1, t2):

    t1_start = t1[0]
    t1_end = t1[1]
    t2_start = t2[0]
    t2_end = t2[1]

    if t2_start <= t1_start and t2_start > t1_end:
        if t1_end > t2_end:
            return (t1_start, t2_end)
        elif t1_end <= t2_end:
            return (t1_start, t1_end)
    elif t1_start <= t2_start and t1_start > t2_end:
        if t2_end > t1_end:
            return (t2_start, t1_end)
        elif t2_end <= t1_end:
            return (t2_start, t2_end)
    else:
        return (t1, t2)
        

def times_overlap(t1, t2):

    # td1 and td2 are timedelta 2-tuples
    t1_start = t1[0]
    t1_end = t1[1]
    t2_start = t2[0]
    t2_end = t2[1]
    
    if t2_start <= t1_start and t2_start > t1_end:
        if t1_end > t2_end:
            return (t2_start, t1_end)
        elif t1_end <= t2_end:
            return (t2_start, t2_end)
    elif t1_start <= t2_start and t1_start > t2_end:
        if t2_end > t1_end:
            return (t1_start, t2_end)
        elif t2_end <= t1_end:
            return (t1_start, t1_end)
    else:
        return None

def timestream_overlap(ts1, ts2):

    overlap_time = []
    
    for t1 in ts1:
        for t2 in ts2:
            overlap = times_overlap(t1, t2)
            if overlap is not None:
                overlap_time.append(overlap)

    return overlap_time
            
def player_overlap (player1_id, player2_id, game_id):

    p1_times = player_time_on_court(game_id, player1_id)
    p2_times = player_time_on_court(game_id, player2_id)

    return timestream_overlap(p1_times, p2_times)

def get_plays_in_one_interval (plays, interval):

    return [play for play in plays if play_time(play) < interval[0] and play_time(play) > interval[1]]

def get_plays_in_intervals (plays, intervals):

    all_plays = []
    for interval in intervals:
        all_plays += get_plays_in_one_interval(plays, interval)

    return sorted(all_plays, key=play_time)

def is_play_in_interval(play, interval):

    pt = play_time(play)
    if pt < interval[0] and pt > interval[1]:
        return True
    else:
        return False

def is_play_in_some_interval(play, intervals):

    for interval in intervals:
        if is_play_in_interval(play, interval):
            return True

    return False

def get_plays_not_in_intervals (plays, intervals):

    return [play for play in plays if not is_play_in_some_interval(play, intervals)]

def team_stats_with_player (game_id, player_id):

    pass

def team_stats_without_player (game_id, player_id):

    pass

def cumul_team_stats_with_player (player_id):

    pass

def cumul_team_stats_without_player (player_id):

    pass

def filter_missed_made(plays):

    shooting_plays = [play for play in plays
                      if 'Shot' in play['detail-desc'] 
                      and play['x-coord'] != '' 
                      and play['y-coord'] != '']
    made_shots = [play for play in shooting_plays if 'Made' in play['event-desc']]
    missed_shots = [play for play in shooting_plays if 'Missed' in play['event-desc']]

    made_shots_coords = [{'x': float(shot['x-coord']), 'y': float(shot['y-coord']) + 5.25} for shot in made_shots]
    missed_shots_coords = [{'x': float(shot['x-coord']), 'y': float(shot['y-coord'])+ 5.25} for shot in missed_shots]

    return made_shots_coords, missed_shots_coords


def cumulative_team_stats (team_id):

    pass

def plot_all_game_charts(game_id):

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

def plot_cumul_charts(player_id, hex_sizes, output_types):

    for hex_size in hex_sizes:
        for output_type in output_types:
            cumul_team_shot_chart_with_player(player_id, hex_size=hex_size, output_type=output_type, scale_factor=128)
            cumul_team_shot_chart_without_player(player_id, hex_size=hex_size, output_type=output_type, scale_factor=128)
            cumul_opp_shot_chart_with_player(player_id, hex_size=hex_size, output_type=output_type, scale_factor=128)
            cumul_opp_shot_chart_without_player(player_id, hex_size=hex_size, output_type=output_type, scale_factor=128)

def calc_drtg(game_day, team_id):

    game_id = look_up_contest_id(game_day, team_id)
    team1, team1_id, team2, team2_id = game_teams(game_id)

    if home_or_visitor(game_day, team_id) == 'home':
        team_stats, other_team_stats = boxscore_stats(game_day, team_id)
    else:
        if team_id == team1_id:
            team_stats, other_team_stats = boxscore_stats(game_day, team2_id)
        else:
            team_stats, other_team_stats = boxscore_stats(game_day, team1_id)
            
    pass

def cumul_team_ortg_drtg(team_id, start_date=None, end_date=None, return_type='simple'):

    if start_date is None:
        start_date = dt.date(2012, 10, 27)
    if end_date is None:
        end_date = dt.date(2013, 4, 17)

    games = games_played_by_team(team_id)

    fta = 0
    tov = 0
    fga = 0
    fgm = 0
    ftm = 0
    orb = 0
    drb = 0
    pts = 0
    pos = 0
    threes = 0
    mp = 0
    
    opp_fta = 0
    opp_ftm = 0
    opp_fgm = 0
    opp_tov = 0
    opp_fga = 0
    opp_drb = 0
    opp_orb = 0
    opp_pts = 0
    opp_pos = 0
    opp_threes = 0
    opp_mp = 0
    
    for game in games:
        gd = game_day(game, type='datetime')
        if home_or_visitor(gd, team_id) == 'home':
            team_stats, opp_stats = boxscore_stats(gd, team_id)
        else:
            opp_id = look_up_opponent(game, team_id)
            opp_stats, team_stats = boxscore_stats(gd, opp_id)

        fga += team_stats['FGA']
        fta += team_stats['FTA']
        tov += team_stats['TOV']
        orb += team_stats['ORB']
        drb += team_stats['DRB']
        pts += team_stats['PTS']
        pos += team_stats['POS']
        ftm += team_stats['FTM']
        fgm += team_stats['FGM']
        mp += team_stats['MP']
        threes += team_stats['3PM']
        
        opp_pts += opp_stats['PTS']
        opp_drb += opp_stats['DRB']
        opp_orb += opp_stats['ORB']
        opp_fga += opp_stats['FGA']
        opp_fgm += opp_stats['FGM']
        opp_ftm += opp_stats['FTM']
        opp_pos += opp_stats['POS']
        opp_tov += opp_stats['TOV']
        opp_threes += opp_stats['3PM']

    #print pos, pts

    #pos = 0.96 * (fga + tov + 0.44 * fta - orb)
    ortg = 100 * pts / pos
    drtg = 100 * opp_pts / pos
    
    if return_type == 'simple':
        return ortg, drtg
    elif return_type == 'full':

        return {'fga': fga,
                'fta': fta,
                'tov': tov,
                'orb': orb,
                'drb': drb,
                'pts': pts,
                'ftm': ftm,
                'fgm': fgm,
                'pos': pos,
                'threes': threes,
                'ortg': ortg,
                'drtg': drtg,
                'opp_pts': opp_pts,
                'opp_fga': opp_fga,
                'opp_fta': opp_fta,
                'opp_tov': opp_tov,
                'opp_orb': opp_orb,
                'opp_drb': opp_drb,
                'opp_pts': opp_pts,
                'opp_ftm': opp_ftm,
                'opp_fgm': opp_fgm,
                'opp_pos': opp_pos,
                'opp_threes': opp_threes}
                

def cumul_player_usage(player_id, start_date=None, end_date=None):

    if start_date is None:
        start_date = dt.date(2012, 10, 27)
    if end_date is None:
        end_date = dt.date(2013, 4, 17)

    games_played = games_played_pbp(player_id, start_date=start_date, end_date=end_date)

    fga = 0
    fta = 0
    tov = 0
    mp = 0

    team_fga = 0
    team_fta = 0
    team_tov = 0
    team_mp = 0

    for game in games_played:
        
        game_id = int(game['playbyplay']['contest']['id'])

        player_data, team_data = player_ortg(game_id, player_id, return_data=True)

        fga += player_data['fga']
        fta += player_data['fta']
        tov += player_data['tov']
        mp += player_data['mp']

        team_fga += team_data['team_fga']
        team_fta += team_data['team_fta']
        team_tov += team_data['team_tov']
        team_mp += team_data['team_mp']

    usg = 100 * ((fga + 0.44 * fta + tov) * (team_mp / 5)) / (mp * (team_fga + 0.44 * team_fta + team_tov))

    return usg

def player_usage(game_id, player_id):

    player_data, team_data = player_ortg(game_id, player_id, return_data=True)

    fga = player_data['fga']
    fta = player_data['fta']
    tov = player_data['tov']
    mp = player_data['mp']

    team_fga = team_data['team_fga']
    team_fta = team_data['team_fta']
    team_tov = team_data['team_tov']
    team_mp = team_data['team_mp']

    usg = 100 * ((fga + 0.44 * fta + tov) * (team_mp / 5)) / (mp * (team_fga + 0.44 * team_fta + team_tov))

    return usg
    

def cumul_player_ortg(player_id, start_date=None, end_date=None):

    if start_date is None:
        start_date = dt.date(2012, 10, 27)
    if end_date is None:
        end_date = dt.date(2013, 4, 17)

    games_played = games_played_pbp(player_id, start_date=start_date, end_date=end_date)

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
    team_orb_pct = 0
    team_orb = 0
    team_pts = 0
    team_3pm = 0
    team_tov = 0
    team_pos = 0

    opp_dreb = 0
    
    for game in games_played:
        
        game_id = int(game['playbyplay']['contest']['id'])

        player_data, team_data = player_ortg(game_id, player_id, return_data=True)

        ast += player_data['ast']
        fgm += player_data['fgm']
        fga += player_data['fga']
        fta += player_data['fta']
        ftm += player_data['ftm']
        tov += player_data['tov']
        threes += player_data['threes']
        orb += player_data['orb']
        pts += player_data['pts']
        mp += player_data['mp']

        team_fgm += team_data['team_fgm']
        team_fga += team_data['team_fga']
        team_ast += team_data['team_ast']
        team_mp += team_data['team_mp']
        team_ftm += team_data['team_ftm']
        team_fta += team_data['team_fta']
        team_orb += team_data['team_orb']
        team_pts += team_data['team_pts']
        team_3pm += team_data['team_3pm']
        team_tov += team_data['team_tov']
        opp_dreb += team_data['opp_dreb']

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

def player_ortg(game_id, player_id, return_data=False):

    player = player_boxscore(game_id, player_id)

    team_id = look_up_player_team(game_id, player_id)
 
    gd = game_day(game_id, type='datetime')
    if home_or_visitor(gd, team_id) == 'home':
        team_stats, opp_stats = boxscore_stats(gd, team_id)
    else:
        opp_id = look_up_opponent(game_id, team_id)
        opp_stats, team_stats = boxscore_stats(gd, opp_id)
 
    ast = float(player['assists']['assists'])
    fgm = float(player['field-goals']['made'])
    fga = float(player['field-goals']['attempted'])
    ftm = float(player['free-throws']['made'])
    fta = float(player['free-throws']['attempted'])
    tov = float(player['turnovers']['turnovers'])
    threes = float(player['three-point-field-goals']['made'])
    threes_a = float(player['three-point-field-goals']['attempted'])
    orb = float(player['rebounds']['offensive'])
    pts = float(player['points']['points'])
    mp = float(player['total-seconds']['seconds']) / 60.0

    team_fgm = team_stats['FGM']
    team_fga = team_stats['FGA']
    team_ast = team_stats['AST']
    team_mp = team_stats['MP'] * 5
    team_ftm = team_stats['FTM']
    team_fta = team_stats['FTA']
    team_orb_pct = team_stats['ORB%']
    team_orb = team_stats['ORB']
    team_pts = team_stats['PTS']
    team_3pm = team_stats['3PM']
    team_tov = team_stats['TOV']
    team_pos = team_stats['POS']

    if return_data == True:
        player_data = {'ast': ast,
                       'fgm': fgm,
                       'fga': fga,
                       'ftm': ftm,
                       'fta': fta,
                       'tov': tov,
                       'threes': threes,
                       'threes_a': threes_a,
                       'orb': orb,
                       'pts': pts,
                       'mp': mp}
        team_data = {'team_fgm': team_fgm,
                     'team_fga': team_fga,
                     'team_ast': team_ast,
                     'team_mp': team_mp,
                     'team_ftm': team_ftm,
                     'team_fta': team_fta,
                     'team_orb_pct': team_orb_pct,
                     'team_orb': team_orb,
                     'team_pts': team_pts,
                     'team_3pm': team_3pm,
                     'team_tov': team_tov,
                     'team_pos': team_pos,
                     'opp_dreb': opp_stats['DRB']}

        return player_data, team_data
    
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

def cumul_player_drtg(player_id, start_date=None, end_date=None):

    if start_date is None:
        start_date = dt.date(2012, 10, 27)
    if end_date is None:
        end_date = dt.date(2013, 4, 17)

    games_played = games_played_pbp(player_id, start_date=start_date, end_date=end_date)

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
        
        game_id = int(game['playbyplay']['contest']['id'])

        player_data, team_data = player_drtg(game_id, player_id, return_data=True)

        drb += player_data['drb']
        pf += player_data['pf']
        mp += player_data['mp']
        stl += player_data['stl']
        blk += player_data['blk']

        team_mp += team_data['team_mp']
        team_blk += team_data['team_blk']
        team_stl += team_data['team_stl']
        team_drb += team_data['team_drb']
        team_pf += team_data['team_pf']

        team_pos += team_data['team_pos']

        opp_fta += team_data['opp_fta']
        opp_ftm += team_data['opp_ftm']
        opp_fga += team_data['opp_fga']
        opp_fgm += team_data['opp_fgm']
        opp_orb += team_data['opp_orb']
        opp_pts += team_data['opp_pts']
        opp_tov += team_data['opp_tov']
        opp_mp += team_data['opp_mp']

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
    
def player_drtg(game_id, player_id, return_data=False):

    #(((Opponent_FGA - Opponent_FGM - Team_BLK) / Team_MP) * FMwt * (1 - 1.07 * DOR%) + ((Opponent_TOV - Team_STL) / Team_MP)) * MP + (PF / Team_PF) * 0.4 * Opponent_FTA * (1 - (Opponent_FTM / Opponent_FTA))^2
    #Opponent_PTS / (Opponent_FGM + (1 - (1 - (Opponent_FTM / Opponent_FTA))^2) * Opponent_FTA*0.4)
    player = player_boxscore(game_id, player_id)

    team_id = look_up_player_team(game_id, player_id)
 
    gd = game_day(game_id, type='datetime')
    if home_or_visitor(gd, team_id) == 'home':
        team_stats, opp_stats = boxscore_stats(gd, team_id)
    else:
        opp_id = look_up_opponent(game_id, team_id)
        opp_stats, team_stats = boxscore_stats(gd, opp_id)
 
    ast = float(player['assists']['assists'])
    fgm = float(player['field-goals']['made'])
    fga = float(player['field-goals']['attempted'])
    ftm = float(player['free-throws']['made'])
    fta = float(player['free-throws']['attempted'])
    tov = float(player['turnovers']['turnovers'])
    threes = float(player['three-point-field-goals']['made'])
    orb = float(player['rebounds']['offensive'])
    drb = float(player['rebounds']['defensive'])
    pts = float(player['points']['points'])
    mp = float(player['total-seconds']['seconds']) / 60.0
    stl = float(player['steals']['steals'])
    blk = float(player['blocked-shots']['blocked-shots'])
    pf = float(player['personal-fouls']['personal-fouls'])
    
    team_fgm = team_stats['FGM']
    team_fga = team_stats['FGA']
    team_ast = team_stats['AST']
    team_mp = team_stats['MP'] * 5
    team_ftm = team_stats['FTM']
    team_fta = team_stats['FTA']
    team_orb_pct = team_stats['ORB%']
    team_orb = team_stats['ORB']
    team_drb = team_stats['DRB']
    team_pts = team_stats['PTS']
    team_3pm = team_stats['3PM']
    team_tov = team_stats['TOV']
    team_blk = team_stats['BLK']
    team_stl = team_stats['STL']
    team_pf = team_stats['PFL']
    team_pos = team_stats['POS']
    team_drtg = team_stats['DRTG']
    
    opp_orb_pct = opp_stats['ORB%']
    dor_pct = opp_stats['ORB%'] #opp_stats['ORB'] / (opp_stats['ORB'] + team_drb)
    dfg_pct = opp_stats['FG%']
    opp_fga = opp_stats['FGA']
    opp_3pa = opp_stats['3PA']
    opp_fgm = opp_stats['FGM']
    opp_tov = opp_stats['TOV']
    opp_ftm = opp_stats['FTM']
    opp_fta = opp_stats['FTA']
    opp_mp = opp_stats['MP'] * 5
    opp_pts = opp_stats['PTS']
    opp_pos = opp_stats['POS']

    if return_data == True:
        player_data = {'blk': blk,
                       'stl': stl,
                       'pf': pf,
                       'drb': drb,
                       'orb': orb,
                       'pts': pts,
                       'mp': mp}
        team_data = {'opp_fgm': team_fgm,
                     'opp_fga': team_fga,
                     'opp_mp': opp_mp,
                     'opp_ftm': team_ftm,
                     'opp_fta': team_fta,
                     'opp_pts': opp_pts,
                     'opp_orb': opp_stats['ORB'],
                     'opp_tov': opp_tov,
                     'opp_3pa': opp_3pa,
                     'opp_pos': opp_pos,
                     'team_mp': team_mp,
                     'team_drb': team_drb,
                     'team_blk': team_blk,
                     'team_stl': team_stl,
                     'team_pf': team_pf,
                     'team_pos': team_pos}

        return player_data, team_data

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
    stops2 = (((opp_fga - opp_fgm - team_blk) / team_mp) * fmwt * (1 - 1.07 * dor_pct) + ((opp_tov - team_stl) / team_mp)) * mp + (pf / team_pf) * 0.4 * opp_fta * (1 - (opp_ftm / opp_fta))**2

    stops_tot = stops1 + stops2

    stop_pct = (stops_tot * opp_mp) / (team_pos * mp)

    d_pts_per_scrposs = opp_pts / (opp_fgm + (1 - (1 - (opp_ftm / opp_fta))**2) * opp_fta * 0.4)
    
    drtg = team_drtg + 0.2 * (100 * d_pts_per_scrposs * (1 - stop_pct) - team_drtg)

    return drtg

def player_boxscore(game_id, player_id):
 
    game = boxscores.find_one({'boxscore.contest.id': game_id})
 
    home_players, away_players = get_player_boxscores(game_id)
    
    all_players = home_players + away_players
 
    player_stats = [player_data for player_data in all_players if player_data['id'] == player_id][0]

    return player_stats

def calc_days_rest(this_game_day, team_id):

    games_played = games_played_by_team(team_id, end_date=this_game_day)

    if len(games_played) < 2:
        return 5

    last_game_played = game_day(games_played[-2], type='datetime')

    days_rest = (this_game_day - last_game_played).days

    return days_rest

def boxscore_stats(game_day, home_team_id):

    game_id = look_up_contest_id(game_day, home_team_id)
    game = boxscores.find_one({'boxscore.contest.id': game_id})
    teams = game['boxscore']['contest']['team']
    stats = game['boxscore']['team-stats']['statistics']
    home_boxscore = {}
    away_boxscore = {}

    home_boxscore['FGM'] = stats[0]['category'][0]['home-value']
    home_boxscore['FGA'] = stats[0]['category'][1]['home-value']
    home_boxscore['FG%'] = stats[0]['category'][2]['home-value']
    home_boxscore['FTM'] = stats[1]['category'][0]['home-value']
    home_boxscore['FTA'] = stats[1]['category'][1]['home-value']
    home_boxscore['FT%'] = stats[1]['category'][2]['home-value']
    home_boxscore['3PM'] = stats[2]['category'][0]['home-value']
    home_boxscore['3PA'] = stats[2]['category'][1]['home-value']
    home_boxscore['3P%'] = stats[2]['category'][2]['home-value']
    home_boxscore['PTS'] = stats[3]['category']['home-value']
    periods_played =  game['boxscore']['gamestate']['period']
    home_boxscore['MP'] = 48 + (periods_played - 4) * 5

    away_boxscore['FGM'] = stats[0]['category'][0]['visitor-value']
    away_boxscore['FGA'] = stats[0]['category'][1]['visitor-value']
    away_boxscore['FG%'] = stats[0]['category'][2]['visitor-value']
    away_boxscore['FTM'] = stats[1]['category'][0]['visitor-value']
    away_boxscore['FTA'] = stats[1]['category'][1]['visitor-value']
    away_boxscore['FT%'] = stats[1]['category'][2]['visitor-value']
    away_boxscore['3PM'] = stats[2]['category'][0]['visitor-value']
    away_boxscore['3PA'] = stats[2]['category'][1]['visitor-value']
    away_boxscore['3P%'] = stats[2]['category'][2]['visitor-value']
    away_boxscore['PTS'] = stats[3]['category']['visitor-value']
    away_boxscore['MP'] = home_boxscore['MP']
    
    # rebounds

    total_oreb = stats[4]['category'][1]['visitor-value'] + stats[4]['category'][1]['home-value']
    total_dreb = stats[4]['category'][2]['visitor-value'] + stats[4]['category'][2]['home-value']
    home_oreb = stats[4]['category'][1]['home-value']
    away_oreb = stats[4]['category'][1]['visitor-value']
    home_dreb = stats[4]['category'][2]['home-value']
    away_dreb = stats[4]['category'][2]['visitor-value']

    home_boxscore['ORB'] = float(home_oreb)
    home_boxscore['DRB'] = float(home_dreb)
    away_boxscore['ORB'] = float(away_oreb)
    away_boxscore['DRB'] = float(away_dreb)
    
    home_boxscore['DRB%'] = float(home_dreb) / (home_dreb + away_oreb)
    home_boxscore['ORB%'] = float(home_oreb) / (home_oreb + away_dreb)

    away_boxscore['DRB%'] = float(away_dreb) / (home_oreb + away_dreb)
    away_boxscore['ORB%'] = float(away_oreb) / (home_dreb + away_oreb)
    
    home_boxscore['AST'] = stats[5]['category']['home-value']
    home_boxscore['STL'] = stats[6]['category']['home-value']
    home_boxscore['BLK'] = stats[7]['category']['home-value']
    home_boxscore['PFL'] = stats[8]['category']['home-value']
    home_boxscore['TOV'] = stats[9]['category']['home-value']

    away_boxscore['AST'] = stats[5]['category']['visitor-value']
    away_boxscore['STL'] = stats[6]['category']['visitor-value']
    away_boxscore['BLK'] = stats[7]['category']['visitor-value']
    away_boxscore['PFL'] = stats[8]['category']['visitor-value']
    away_boxscore['TOV'] = stats[9]['category']['visitor-value']

    home_boxscore['PTO'] = stats[21]['category']['home-value']
    home_boxscore['PIP'] = stats[22]['category']['home-value']
    home_boxscore['2CP'] = stats[23]['category']['home-value']
    home_boxscore['FBP'] = stats[24]['category']['home-value']
    
    away_boxscore['PTO'] = stats[21]['category']['visitor-value']
    away_boxscore['PIP'] = stats[22]['category']['visitor-value']
    away_boxscore['2CP'] = stats[23]['category']['visitor-value']
    away_boxscore['FBP'] = stats[24]['category']['visitor-value']

    # as long as we're here, let's compute the ORTG and DRTG for each team

    home_pos = 0.5 * ((home_boxscore['FGA'] + 0.4 * home_boxscore['FTA'] - 1.07 * \
                       (home_boxscore['ORB'] / (home_boxscore['ORB'] + away_boxscore['DRB'])) * \
                       (home_boxscore['FGA'] - home_boxscore['FGM']) + home_boxscore['TOV']) + \
                      (away_boxscore['FGA'] + 0.4 * away_boxscore['FTA'] - 1.07 * \
                       (away_boxscore['ORB'] / (away_boxscore['ORB'] + home_boxscore['DRB'])) * \
                       (away_boxscore['FGA'] - away_boxscore['FGM']) + away_boxscore['TOV']))

    away_pos = 0.5 * ((away_boxscore['FGA'] + 0.4 * away_boxscore['FTA'] - 1.07 * \
                       (away_boxscore['ORB'] / (away_boxscore['ORB'] + home_boxscore['DRB'])) * \
                       (away_boxscore['FGA'] - away_boxscore['FGM']) + away_boxscore['TOV']) + \
                      (home_boxscore['FGA'] + 0.4 * home_boxscore['FTA'] - 1.07 * \
                       (home_boxscore['ORB'] / (home_boxscore['ORB'] + away_boxscore['DRB'])) * \
                       (home_boxscore['FGA'] - home_boxscore['FGM']) + home_boxscore['TOV']))

    # home_pos = 0.96 * (home_boxscore['FGA'] -
    #                    home_boxscore['ORB'] +
    #                    home_boxscore['TOV'] +
    #                    0.44 * home_boxscore['FTA'])

    # print home_pos
    
    # away_pos = 0.96 * (away_boxscore['FGA'] -
    #                    away_boxscore['ORB'] +
    #                    away_boxscore['TOV'] +
    #                    0.44 * away_boxscore['FTA'])

    home_drtg = away_boxscore['PTS'] * 100 / away_pos
    away_drtg = home_boxscore['PTS'] * 100 / home_pos

    home_ortg = 100 * home_boxscore['PTS'] / home_pos
    away_ortg = 100 * away_boxscore['PTS'] / away_pos

    home_boxscore['POS'] = home_pos
    away_boxscore['POS'] = away_pos
    home_boxscore['DRTG'] = home_drtg
    home_boxscore['ORTG'] = home_ortg
    away_boxscore['DRTG'] = away_drtg
    away_boxscore['ORTG'] = away_ortg

    home_boxscore['REST'] = calc_days_rest(game_day, home_team_id)
    away_boxscore['REST'] = calc_days_rest(game_day, look_up_opponent(game_id, home_team_id))
    
    return home_boxscore, away_boxscore

def home_or_visitor (game_day, team_id):

    game_id = look_up_contest_id(game_day, team_id)

    game = boxscores.find_one({'boxscore.meta.contest.id': game_id})

    if game['boxscore']['contest']['team'][0]['id'] == team_id:
        return 'home'
    else:
        return 'visitor'

def games_played_by_team(team_id, start_date=None, end_date=None):

    if start_date is None:
        start_date = dt.date(2012, 10, 27)
    if end_date is None:
        end_date = dt.date(2013, 4, 17)

    games = boxscores.find({'$or': [{'boxscore.meta.team.0.id': team_id},
                                    {'boxscore.meta.team.1.id': team_id}]})

    games_filtered = [game for game in games
                      if game_day(int(game['boxscore']['contest']['id']), type='datetime') >= start_date
                      and game_day(int(game['boxscore']['contest']['id']), type='datetime') <= end_date]

    def game_day_key(game_id):
        return game_day(game_id, type='datetime')
    
    games = pylab.unique([game['boxscore']['contest']['id'] for game in games_filtered]).tolist()
    chron_games = sorted(games, key=game_day_key)

    return chron_games


def look_up_team_name (team_id):

    team = teams.find_one({'id': int(team_id)})
    return team['city'], team['name']

def look_up_player_team (game_id, player_id):

    game = boxscores.find_one({'boxscore.contest.id': game_id})

    teams = game['boxscore']['player-stats']['team']

    for team in teams:
        for player in team['players']['player']:
            if player['id'] == player_id:
                return team['id']

    return None

def games_played_pbp (player_id, start_date=dt.date(2012, 10, 27), end_date=dt.date(2013, 4, 17)):

    games_played = pbp.find({'$or': [{'playbyplay.plays.play.player1-id': str(player_id)},
                                     {'playbyplay.plays.play.player2-id': str(player_id)},
                                     {'playbyplay.plays.play.player3-id': str(player_id)}]})

    games_filtered = [game for game in games_played
                      if game_day(int(game['playbyplay']['contest']['id']), type='datetime') >= start_date
                      and game_day(int(game['playbyplay']['contest']['id']), type='datetime') <= end_date]

    return games_filtered

def games_played_boxscore(player_id, start_date=dt.date(2012, 10, 27), end_date=dt.date(2013, 4, 17)):

    
    #games_played = boxscores.find({'$or':

    pass

def look_up_contest_id (game_day, team_id):

    game = boxscores.find_one({'boxscore.meta.game-date.year': game_day.year,
                               'boxscore.meta.game-date.month': game_day.month,
                               'boxscore.meta.game-date.day': game_day.day,
                               '$or': [{'boxscore.meta.team.0.id': team_id},
                               {'boxscore.meta.team.1.id': team_id}]})


    return game['boxscore']['meta']['contest']['id']

def look_up_opponent (game_id, team_id):

    game = boxscores.find_one({'boxscore.contest.id': game_id})

    team1_id = game['boxscore']['contest']['team'][0]['id']
    team2_id = game['boxscore']['contest']['team'][1]['id']
    
    if team_id == team1_id:
        return team2_id
    else:
        return team1_id

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


def get_player_boxscores(game_id):

    game = boxscores.find_one({'boxscore.meta.contest.id': game_id})

    home_players = game['boxscore']['player-stats']['team'][0]['players']['player']
    away_players = game['boxscore']['player-stats']['team'][1]['players']['player']

    return home_players, away_players

def cluster_teams_offense(output_filename):

    all_teams = teams.find(timeout=False)
    writer = csv.writer(open(output_filename, 'w'))
    
    all_features = []
    
    for team in all_teams:
        print 'Generating features for {0} {1}'.format(team['city'], team['name'])

        features = team_ocluster_features(team['id'])
        writer.writerow(features)

def cluster_teams_defense(output_filename):

    all_teams = teams.find(timeout=False)
    writer = csv.writer(open(output_filename, 'w'))
    
    all_features = []
    
    for team in all_teams:
        print 'Generating features for {0} {1}'.format(team['city'], team['name'])

        features = team_dcluster_features(team['id'])
        writer.writerow(features)


def compare_players_offense(p1, p2, weights=None):

    if type(p1) == str and type(p2) == str:
        fn1, ln1 = p1.split()
        fn2, ln2 = p2.split()

        p1_id = int(look_up_player_id(fn1, ln1))
        p2_id = int(look_up_player_id(fn2, ln2))
    
    elif type(p1) == int and type(p2) == int:
        p1_id = p1
        p2_id = p2

        fn1, ln1 = look_up_player_name(p1_id)
        fn2, ln2 = look_up_player_name(p2_id)
        
    else:
        return None

    p1_f = player_ocluster_features(p1_id)
    p2_f = player_ocluster_features(p2_id)

    sim = player_feature_sim(p1_f, p2_f, weights)
    dist = euclidean(p1_f[1:], p2_f[1:])

    print '{:25}{:>10}{:>10}{:>10}{:>10}{:>10}{:>10}'.format('Player', 'AST%', 'TS%', 'ORB%', 'USG%', 'ORTG%', 'MP%')
    print '{:->85}'.format('')
    print '{:25}{:10.3}{:10.3}{:10.3}{:10.3}{:10.3f}{:10.3}'.format(' '.join((fn1, ln1)), p1_f[1], p1_f[2], p1_f[3], p1_f[4], p1_f[5], p1_f[6])
    print '{:25}{:10.3}{:10.3}{:10.3}{:10.3}{:10.3f}{:10.3}'.format(' '.join((fn2, ln2)), p2_f[1], p2_f[2], p2_f[3], p2_f[4], p2_f[5], p2_f[6])
    #print '{:->85}'.format('')
    #print '{:25}{:10.3}'.format('Euclidean distance:', dist)

def compare_players_defense(p1, p2, weights=None):

    if type(p1) == str and type(p2) == str:
        fn1, ln1 = p1.split()
        fn2, ln2 = p2.split()

        p1_id = int(look_up_player_id(fn1, ln1))
        p2_id = int(look_up_player_id(fn2, ln2))
    
    elif type(p1) == int and type(p2) == int:
        p1_id = p1
        p2_id = p2

        fn1, ln1 = look_up_player_name(p1_id)
        fn2, ln2 = look_up_player_name(p2_id)
        
    else:
        return None

    p1_f = player_dcluster_features(p1_id)
    p2_f = player_dcluster_features(p2_id)

    sim = player_feature_sim(p1_f, p2_f, weights)
    dist = euclidean(p1_f[1:], p2_f[1:])

    print '{:25}{:>10}{:>10}{:>10}{:>10}{:>10}{:>10}'.format('Player', 'BLK%', 'STL%', 'DRB%', 'DRTG', 'PF%', 'MP%')
    print '{:->85}'.format('')
    print '{:25}{:10.3}{:10.3}{:10.3}{:10.3f}{:10.3f}{:10.3}'.format(' '.join((fn1, ln1)), p1_f[1], p1_f[2], p1_f[3], p1_f[4], p1_f[5], p1_f[6])
    print '{:25}{:10.3}{:10.3}{:10.3}{:10.3f}{:10.3f}{:10.3}'.format(' '.join((fn2, ln2)), p2_f[1], p2_f[2], p2_f[3], p2_f[4], p2_f[5], p2_f[6])
    #print '{:->85}'.format('')
    #print '{:25}{:10.3}'.format('Euclidean distance:', dist)

def player_feature_sim(p1, p2, weights=None):

    if p1[0] > 1000:
        p1 = p1[1:]
    if p2[0] > 1000:
        p2 = p2[1:]

    if weights is None:
        weights = pylab.ones(len(p1))
    
    s = pylab.array([w * ((abs(x - y) / abs(x + y)))**2 for x, y, w in zip(p1, p2, weights)])
    #s = pylab.array([w * (x + y) / (x * y) for x, y, w in zip(p1, p2, weights)])

    d = pylab.sqrt(pylab.sum(s))

    if pylab.isnan(d):
        d = 0

    return d

def player_feature_sim_matrix(feature_matrix, feature_weights=None):

    shape = feature_matrix.shape
    sims = pylab.zeros((shape[0], shape[0]))

    for i, p1 in enumerate(feature_matrix):
        for j, p2 in enumerate(feature_matrix):
            sims[i][j] = player_feature_sim(p1, p2, weights=None)

    return sims


# for i in range(len(test_subset)):
#     team1 = test_subset[i]['home_team']
#     team2 = test_subset[i]['away_team']
#     margin = test_subset[i]['home_points'] - test_subset[i]['away_points']
#     pred_margin = test_pred[i]
#     line = test_line[i]
#     t1_name = ' '.join(nba.look_up_team_name(team1))
#     t2_name = ' '.join(nba.look_up_team_name(team2))
#     if line > 0:
#         # home are favored
#         if pred_margin > line:
#             # I have bet on home
#             if line > margin:
#                 status = 'lose'
#             if line < margin:
#                 status = 'win'
#             if line == margin:
#                 status = 'tie'
#         if pred_margin < line:
#             # I have bet on away
#             if line > margin:
#                 status = 'win'
#             if line < margin:
#                 status = 'lose'
#             if line == margin:
#                 status = 'tie'
#     if line < 0:
#         # away are favored
#         if pred_margin < line:
#             # I have bet on away
#             if line < margin:
#                 status = 'lose'
#             if line > margin:
#                 status = 'win'
#             if line == margin:
#                 status = 'tie'
#         if pred_margin > line:
#             # I have bet on home
#             if line < margin:
#                 status = 'win'
#             if line > margin:
#                 status = 'lose'
#             if line == margin:
#                 status = 'tie'
#     print '{:50} {:>15} {:>25} {:>15} {:>15}'.format(' vs '.join((t1_name, t2_name)), 'line: {: 2.1f}'.format(line), 'predicted: {: 2.1f}'.format(pred_margin), 'actual: {: 2.1f}'.format(margin), status)

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
