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
        if abs(y) <= 14.0 and abs(x) >= 22.0:
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

def shared_times(times):

    class Transition():
        # type can be 'enter' or 'exit'
        def __init__(self):
            self.type = None
            self.time = None

    times_on = []
    times_off = []
    for player_time in times:
        times_on += [t[0] for t in player_time]
        times_off += [t[1] for t in player_time]

    times_on = sorted(times_on, reverse=True)
    times_off = sorted(times_off, reverse=True)

    #print map(str, times_on)
    #print map(str, times_off)

    i, j = 0, 0
    enter = 1
    max_enter = enter

    timestream = []
    while i < len(times_on) and j < len(times_off):
        #print i, j, times_on[i], times_off[j]

        if timestream == []:
            timestream.append((times_on[i], 'enter', enter))
            i += 1
            enter += 1

        elif times_on[i] > times_off[j]:
            timestream.append((times_on[i], 'enter', enter))
            i += 1
            enter += 1

        elif times_on[i] == times_off[j]:
            timestream.append((times_on[i], 'enter', enter))
            timestream.append((times_off[j], 'exit', enter))
            i += 1
            j += 1

        elif times_on[i] < times_off[j]:
            enter -= 1
            timestream.append((times_off[j], 'exit', enter))
            j += 1

        if enter > max_enter:
            max_enter = enter

    while j < len(times_off):
        enter -= 1
        timestream.append((times_off[j], 'exit', enter))
        j += 1

    max_enter -= 1

    final_times = []
    i = 0
    while i < len(timestream) - 1:
        current = timestream[i]
        next = timestream[i + 1]

        if current[1] == 'enter' and next[1] == 'exit' \
                and current[2] == next[2] \
                and current[2] == max_enter \
                and not current[0] == next[0]:
            final_times.append((current[0], next[0]))

        i += 1

    return final_times

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

def compute_ts_length(ts, unit='seconds'):

    seconds = 0
    for ti, to in ts:
        td = ti - to
        seconds += td.total_seconds()

    if unit == 'minutes':
        return seconds / 60.0
    else:
        return seconds