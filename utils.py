__author__ = 'jerry'

# miscelaneous utilities

import datetime as dt

from sklearn.metrics.pairwise import euclidean_distances

def is_shot_three(x, y):

    if euclidean((x, y), (0, 5.25)) > 23.75:
        return True
    else:
        if abs(x) > 14.0:
            return True
        else:
            return False


def format_date(d, source='SI'):

    if source == 'NBA':
        date_format = '{0:04d}{1:02d}{2:02d}'
    elif source == 'CNN':
        date_format = '/{0:04d}/{1:02d}/{2:02d}/'
    elif source == 'SI':
        date_format = '{0:04d}-{1:02d}-{2:02d}'

    return date_format.format(d.year, d.month, d.day)

def play_time(play):

    return dt.timedelta(minutes=((4 - int(play['period'])) * 12 + int(play['time']['minutes'])),
                        seconds=int(float(play['time']['seconds'])))

def look_up_player_id (first_name, last_name):

    player = players.find_one({'firstName': first_name, 'lastName': last_name})
    player_id = str(player['id'])

    return player_id

def look_up_player_name (player_id):

    player = players.find_one({'id': int(player_id)})
    return player['firstName'], player['lastName']