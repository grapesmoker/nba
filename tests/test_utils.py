import datetime as dt

from utils.interval import Interval, TimeStream, recursive_intersect
from unittest import TestCase

from pprint import pprint


class UtilsTest(TestCase):

    def test_intervals_intersection(self):
        i1 = Interval(dt.timedelta(seconds=0), dt.timedelta(seconds=249))
        i2 = Interval(dt.timedelta(seconds=0), dt.timedelta(seconds=589))

        result = i1.intersection(i2)
        self.assertEqual(result.start, dt.timedelta(seconds=0))
        self.assertEqual(result.end, dt.timedelta(seconds=249))

        i2 = Interval(dt.timedelta(seconds=0), dt.timedelta(seconds=249))
        i1 = Interval(dt.timedelta(seconds=0), dt.timedelta(seconds=589))

        result = i1.intersection(i2)
        self.assertEqual(result.start, dt.timedelta(seconds=0))
        self.assertEqual(result.end, dt.timedelta(seconds=249))

        i1 = Interval(dt.timedelta(seconds=0), dt.timedelta(seconds=249))
        i2 = Interval(dt.timedelta(seconds=200), dt.timedelta(seconds=589))

        result = i1.intersection(i2)
        self.assertEqual(result.start, dt.timedelta(seconds=200))
        self.assertEqual(result.end, dt.timedelta(seconds=249))

        i1 = Interval(dt.timedelta(seconds=0), dt.timedelta(seconds=249))
        i2 = Interval(dt.timedelta(seconds=250), dt.timedelta(seconds=589))

        result = i1.intersection(i2)
        self.assertIsNone(result)

    def test_intervals_union(self):
        i1 = Interval(dt.timedelta(seconds=0), dt.timedelta(seconds=249))
        i2 = Interval(dt.timedelta(seconds=0), dt.timedelta(seconds=589))

        result = i1.union(i2)
        self.assertEqual(result.start, dt.timedelta(seconds=0))
        self.assertEqual(result.end, dt.timedelta(seconds=589))

        i2 = Interval(dt.timedelta(seconds=0), dt.timedelta(seconds=249))
        i1 = Interval(dt.timedelta(seconds=0), dt.timedelta(seconds=589))

        result = i1.union(i2)
        self.assertEqual(result.start, dt.timedelta(seconds=0))
        self.assertEqual(result.end, dt.timedelta(seconds=589))

        i1 = Interval(dt.timedelta(seconds=0), dt.timedelta(seconds=249))
        i2 = Interval(dt.timedelta(seconds=200), dt.timedelta(seconds=589))

        result = i1.union(i2)
        self.assertEqual(result.start, dt.timedelta(seconds=0))
        self.assertEqual(result.end, dt.timedelta(seconds=589))

        i1 = Interval(dt.timedelta(seconds=0), dt.timedelta(seconds=249))
        i2 = Interval(dt.timedelta(seconds=250), dt.timedelta(seconds=589))

        result = i1.union(i2)
        self.assertIsInstance(result, TimeStream)
        self.assertEqual(result[0], i1)
        self.assertEqual(result[1], i2)
        self.assertEqual(len(result), 588)

    def test_timestream_intersection(self):

        i1 = Interval(dt.timedelta(seconds=0), dt.timedelta(seconds=200))
        i2 = Interval(dt.timedelta(seconds=240), dt.timedelta(seconds=1000))
        i3 = Interval(dt.timedelta(seconds=230), dt.timedelta(seconds=800))
        i4 = Interval(dt.timedelta(seconds=900), dt.timedelta(seconds=1700))

        ts1 = TimeStream([i1, i2])
        ts2 = TimeStream([i3, i4])

        result = ts1.intersection(ts2)

        self.assertEqual(len(result), 660)
        self.assertEqual(result[0].start, i2.start)
        self.assertEqual(result[0].end, i3.end)
        self.assertEqual(result[1].start, i4.start)
        self.assertEqual(result[1].end, i2.end)

