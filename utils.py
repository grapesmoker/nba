__author__ = 'jerry'

# miscelaneous utilities

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