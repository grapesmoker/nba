__author__ = 'jerry'

# miscelaneous utilities

import datetime as dt
import numpy as np

from itertools import combinations

from sklearn.metrics.pairwise import euclidean_distances
from scipy.spatial.distance import euclidean

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

    # if len(times) == 1:
    #     return times
    #
    # pretty_print_times(times)
    #
    # t1_int_t2 = times_overlap(times[0], times[1])
    # print t1_int_t2
    # new_times = [t1_int_t2] + times[2:]
    # return intersect_all(new_times)


def recursive_intersect(timestream):

    #import pdb; pdb.set_trace();

    new_timestream = []
    do_not_use = []

    #for item in timestream:
    #    pretty_print_times(item)
    #print '*****'

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
        if np.shape(union) == (2,):
            print 'nondisjoint:', t0, t
            new_times.append(union)
            used.append(t0)
            used.append(t)
        elif np.shape(union) == (2, 2):
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
