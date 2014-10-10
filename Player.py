import datetime as dt

from nba_2013_14 import players, play_time, check_time_consistency
from GameEvent import GameEvent

class Player:

    _coll = players

    def __init__(self, player_id):
        self._coll = self.__class__._coll
        self._player = self._coll.find_one({'id': player_id})

        self._first_name = self._player['firstName']
        self._last_name = self._player['lastName']
        self._id = self._player['id']

    @property
    def first_name(self):
        return self._first_name
        
    @property
    def last_name(self):
        return self._last_name

    @property
    def id(self):
        return self._id

    def __str__(self):
        return '{0} {1}'.format(self._first_name, self._last_name)

    def __repr__(self):
        return self.__str__()

    def time_on_court(self, game_id):

        game = GameEvent(event_id=game_id)

        plays_subbed_in = [play for play in game.pbp if play['playText'].find('Substitution:') > -1
                           and play['players'][0]['playerId'] == self._id]

        plays_subbed_out = [play for play in game.pbp if play['playText'].find('Substitution:') > -1
                            and play['players'][1]['playerId'] == self._id]

        times_subbed_in = [play_time(play) for play in plays_subbed_in]
        times_subbed_out = [play_time(play) for play in plays_subbed_out]

        q_starters = game.quarter_starters()
        
        q2 = dt.timedelta(minutes=36)
        q3 = dt.timedelta(minutes=24)
        q4 = dt.timedelta(minutes=12)

        q_end_times = [q2, q3, q4]
        
        for q, starters in q_starters.items():
            q_start_time = dt.timedelta(minutes=((5 - q) * 12))
            if self._id in starters:
                times_subbed_in.append(q_start_time)

        times_subbed_in = sorted(times_subbed_in, reverse=True)

        i = 0

        while not check_time_consistency(times_subbed_in, times_subbed_out) and i < len(times_subbed_in):
            ti = times_subbed_in[i]
            if i + 1 < len(times_subbed_in):
                ti_next = times_subbed_in[i + 1]
            else:
                ti_next = dt.timedelta(minutes=0)

            to_arr = [to for to in times_subbed_out if to < ti and ti > ti_next]
            
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

        time_stream = zip(times_subbed_in, times_subbed_out)

        return time_stream
