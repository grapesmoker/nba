__author__ = 'jerry'


import requests
import json
import os
import datetime as dt
import pandas as pd

from bs4 import BeautifulSoup

from settings import si_base, teams, players, pbp, odds
from utils import format_date
from dateutil import parser as date_parser

import Team
import Game


def get_games(date, output_file=None):

    # games_url = base + '/scoreboard/' + format_date(date) + '/games.json'
    games_url = si_base + 'schedule'

    result = requests.get(games_url, params={'date': format_date(date)})

    #print games_url + format_date(date)

    soup = BeautifulSoup(result.text)

    #date_string = date.strftime('%B %d,%Y')

    games = soup.find_all('tr', 'component-scoreboard-list final')
    game_ids = []

    for game in games:
        game_date_elem = game.find('div', 'game-anchor')
        game_date_text = game_date_elem['id']
        game_date = date_parser.parse(game_date_text).date()
        if game_date == date:
            game_id = int(game['data-id'])
            game_ids.append(game_id)

    if output_file is not None:
        of = open(output_file, 'w')
        of.write(json.dumps({'game_date': format_date(date), 'game_ids': game_ids}))
        of.close()

    return game_ids


def get_all_data(start_date, end_date, season, ignore_dates=[]):

    data_dir = os.path.join(os.path.abspath('.'), 'json_data', str(season))
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)

    mongo_dir = os.path.join(os.path.abspath('.'), 'mongo_data', str(season))
    if not os.path.exists(mongo_dir):
        os.mkdir(mongo_dir)

    date_list = [start_date + dt.timedelta(days=x) for x in range(0, (end_date - start_date).days)]

    for ignore_date in ignore_dates:
        if ignore_date in date_list:
            date_list.remove(ignore_date)

    for game_day in date_list:
        print 'Processing game day', game_day

        game_ids = get_games(game_day, 'json_data/{}/game-day-{}.json'.format(season, format_date(game_day)))

        # now all the data is just contained in the boxscore...

        base_url = 'http://www.si.com/pbp/liveupdate'

        for game_id in game_ids:


            result = requests.get(base_url, params={'json': '1',
                                                    'sport': 'basketball/nba',
                                                    'id': str(game_id),
                                                    'box': 'true',
                                                    'pbp': 'true',
                                                    'linescore': 'true'})

            try:
                json_result = result.json()['apiResults'][0]
                #dict_result = json.loads(json_result)['apiResults']
                #print json_result
                output_file = 'json_data/{}/pbp_{}_{}.json'.format(season, format_date(game_day), game_id)
                with open(output_file, 'w') as of:
                    json.dump(json_result, of, indent=4)

                boxscore_data = json_result['league']['season']['eventType'][0]['events'][0]['boxscores']
                team_data = json_result['league']['season']['eventType'][0]['events'][0]['teams']

                for team in team_data:
                    filtered_team_data = {'id': team['teamId'],
                                          'location': team['location'],
                                          'nickname': team['nickname'],
                                          'abbreviation': team['abbreviation']}
                    print filtered_team_data['nickname']
                    teams.update({'id': team['teamId']}, filtered_team_data, upsert=True)

                for team in boxscore_data:
                    for player in team['playerstats']:
                        filtered_player_data = {'id': player['player']['playerId'],
                                                'firstName': player['player']['firstName'],
                                                'lastName': player['player']['lastName']}

                        players.update({'id': player['player']['playerId']}, filtered_player_data, upsert=True)


                pbp.update({'league.season.eventType.0.events.0.eventId': game_id}, json_result, upsert=True)

            except Exception as ex:
                print ex


def get_odds_from_donbest(start_date, end_date):

    dates = pd.date_range(start_date, end_date)
    base = 'http://www.donbest.com/nba/odds/'
    str_format = '%Y%m%d'

    odds_results = pd.DataFrame(columns=['game_date', 'game_id', 'home_team', 'away_team', 'home_line'])

    skip_dates = [dt.datetime(2014, 2, 14), dt.datetime(2014, 2, 15)]

    for i, date in enumerate(dates):

        print 'getting results for', date

        target = base + date.strftime(str_format) + '.html'
        res = requests.get(target)
        soup = BeautifulSoup(res.text)

        rows = soup.select('.statistics_table_row') + \
               soup.select('.statistics_table_alternateRow')

        for row in rows:
            import pdb
            pdb.set_trace()
            #try:
            team_data = extract_row_info(row)

            if team_data:
                home_team = team_data[0][1]
                away_team = team_data[1][1]
                home_line = team_data[0][0]

                game = Game.Game.look_up_game(date, home_team)

                if game:

                    data = {'game_date': game.date,
                            'game_id': game.id,
                            'home_team': home_team.id,
                            'away_team': away_team.id,
                            'home_line': home_line,
                            'actual_result': game.home_points - game.away_points}

                    odds_results = odds_results.append(data, ignore_index=True)

            #except Exception as ex:
            #    print ex
            #    print 'Something went wrong extracting odds on {}'.format(date)

    odds_results.index.name = 'game_date'

    return odds_results


def extract_row_info(row):

    matcher = '-?[\d]+\.[\d]+'

    def to_number(x):
        if x == 'PK':
            return 0.0
        else:
            try:
                val = float(x)
            except ValueError as ex:
                print ex
                val = 0.0
            return val

    odds = row.select('.oddsOpener div')[0]
    odds_nums = [c.string for c in odds.children if c.string is not None]
    odds_nums = map(to_number, odds_nums)

    team_elems = row.select('nobr span')
    team_names = [team.text for team in team_elems]

    home_team_nick = team_names[1].split()[-1]
    away_team_nick = team_names[0].split()[-1]

    #home_team_nick = home_team_nick.replace('Hornets', 'Hornets')
    #away_team_nick = away_team_nick.replace('Bobcats', 'Hornets')
    home_team_nick = home_team_nick.replace('Trailblazers', 'Trail Blazers')
    away_team_nick = away_team_nick.replace('Trailblazers', 'Trail Blazers')

    # print home_team_nick, 'vs', away_team_nick

    home_data = teams.find_one({'nickname': home_team_nick})
    away_data = teams.find_one({'nickname': away_team_nick})

    if home_data and away_data:

        home_team = Team.Team(home_data['id'])
        away_team = Team.Team(away_data['id'])

        if odds_nums[0] < 100:
            return [(odds_nums[0] * -1, home_team), (odds_nums[0], away_team)]
        elif odds_nums[1] < 100:
            return [(odds_nums[1], home_team), (odds_nums[1] * -1, away_team)]

    else:
        return None
