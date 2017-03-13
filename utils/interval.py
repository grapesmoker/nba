import datetime as dt
import numpy as np

from itertools import combinations


class Interval:

    def __init__(self, start=None, end=None):
        self.start = start
        self.end = end

    def intersection(self, other):

        if self.end < other.start or other.end < self.start:
            return None
        elif self.start <= other.start and self.end >= other.end:
            return Interval(other.start, other.end)
        elif self.start <= other.start and self.end <= other.end:
            return Interval(other.start, self.end)
        elif self.start >= other.start and self.end >= other.end:
            return Interval(self.start, other.end)
        elif self.start >= other.start and self.end <= other.end:
            return Interval(self.start, self.end)
        else:
            return None

    def union(self, other):

        if self.end < other.start or other.end < self.start:
            return TimeStream([self, other])
        elif self.start <= other.start and self.end >= other.end:
            return Interval(self.start, self.end)
        elif self.start <= other.start and self.end <= other.end:
            return Interval(self.start, other.end)
        elif self.start >= other.start and self.end >= other.end:
            return Interval(other.start, self.end)
        elif self.start >= other.start and self.end <= other.end:
            return Interval(other.start, other.end)
        else:
            raise ValueError('Invalid intervals!')

    def __len__(self):
        return self.end.seconds - self.start.seconds

    def __str__(self):
        start = '{0:02d}:{1:02d}'.format(self.start.seconds // 60, self.start.seconds % 60)
        end = '{0:02d}:{1:02d}'.format(self.end.seconds // 60, self.end.seconds % 60)
        return '<{} - {}>'.format(start, end)


class TimeStream:

    def __init__(self, intervals):
        self._times = intervals

    def __getitem__(self, item):
        return self._times[item]

    def __len__(self):
        return np.sum([len(interval) for interval in self])

    def __str__(self):
        return '[' + ', '.join([str(t) for t in self]) + ']'

    def __add__(self, other):
        return TimeStream(self._times + other._times)

    # def recursive_intersect(self, timestream):
    #
    #     #import pdb;
    #     #pdb.set_trace();
    #
    #     new_timestream = []
    #     do_not_use = []
    #
    #     # for item in timestream:
    #     #    pretty_print_times(item)
    #     # print '*****'
    #
    #     if len(timestream) == 1:
    #         return timestream
    #
    #     t1 = timestream[0]
    #     t2 = timestream[1]
    #
    #     t1_int_t2 = intersect_all(t1 + t2)
    #
    #     new_timestream.append(t1_int_t2)
    #     for t in timestream[2:]:
    #         new_timestream.append(t)
    #
    #     return recursive_intersect(new_timestream)

    # def intersect_all(self):
    #
    #     remaining_times = self._times
    #     current_time_index = 0
    #     done = False
    #     while not done:
    #         current_time = remaining_times[0]
    #         remaining_times = remaining_times[1:]
    #         remaining_times = [current_time.intersection(interval) for interval in remaining_times
    #                            if current_time.intersection(interval) is not None]
    #         if len(remaining_times) == 1 or len(remaining_times) == 0 or\
    #                         current_time_index == len(self) - 1:
    #             done = True
    #         else:
    #             current_time_index += 1
    #
    #     return TimeStream(remaining_times)

    def intersection(self, other):

        new_times = []
        for t1, t2 in combinations(self + other, 2):
            t = t1.intersection(t2)
            if t is not None and t.start != t.end:
                new_times.append(t)
        return TimeStream(new_times)


def recursive_intersect(timestreams):

    new_timestream = []

    if len(timestreams) == 1:
        return TimeStream(timestreams)

    ts1 = timestreams[0]
    ts2 = timestreams[1]

    t1_int_t2 = ts1.intersection(ts2)

    new_timestream.append(t1_int_t2)
    for t in timestreams[2:]:
        new_timestream.append(t)

    return recursive_intersect(new_timestream)


