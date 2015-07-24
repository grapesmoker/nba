import datetime as dt

from settings import players
from utils import play_time

# play_time, check_time_consistency, create_shot_chart

import Game
import Player

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

    def check_time_consistency(self, times_subbed_in, times_subbed_out):

        consistent = True

        if len(times_subbed_in) == len(times_subbed_out) or len(times_subbed_in) == len(times_subbed_out) + 1:
            correct = True
            for to in times_subbed_out:
                for i, ti in enumerate(times_subbed_in[:-1]):
                    ti_next = times_subbed_in[i + 1]
                    if not (to < ti and to >= ti_next):
                        correct = False

            consistent = correct
        else:
            consistent = False

        return consistent

    def time_on_court(self, game_id):

        game = Game.Game(event_id=game_id)

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

        while not self.check_time_consistency(times_subbed_in, times_subbed_out) and i < len(times_subbed_in):
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

    def player_shot_chart(self, game_id, **kwargs):

        game = Game.Game(pbp, game_id)

        player_plays = game.events_by_player(player_id)


        made_shots = [play['shotCoordinates'] for play in player_plays if 
                      play['playEvent'].has_key('name') and play['playEvent']['name'] == 'Field Goal Made']
        missed_shots = [play['shotCoordinates'] for play in player_plays if
                        play['playEvent'].has_key('name') and play['playEvent']['name'] == 'Field Goal Missed']

        made_shots_coords = [{'x': float(shot['x']), 'y': float(shot['y']) + 5.25} for shot in made_shots]
        missed_shots_coords = [{'x': float(shot['x']), 'y': float(shot['y'])+ 5.25} for shot in missed_shots]

        #print made_shots_coords
        #print missed_shots_coords

        if 'return' in kwargs:
            if kwargs['return'] == True:
                return made_shots_coords, missed_shots_coords
            else:
                kwargs['plot'] = True
        else:
            kwargs['plot'] = True

        if 'plot' in kwargs:
            if 'plot_type' in kwargs:
                plot_type = kwargs['plot_type']
            else:
                plot_type = 'hexbin'
            if 'hex_size' in kwargs:
                hex_size = kwargs['hex_size']
            else:
                hex_size = 1
            if 'overplot_shots' in kwargs:
                overplot_shots = kwargs['overplot_shots']
            else:
                overplot_shots = False

            gd = dt.datetime.strftime(game.date, '%Y-%m-%d')
            team1_name = game.home_team['nickname']
            team2_name = game.away_team['nickname']
            
            first_name, last_name = look_up_player_name(player_id)

            create_shot_chart(made_shots_coords, missed_shots_coords,
                              'plots/players/{}_{}_shots_{}_{}_vs_{}.pdf'.format(first_name, last_name, gd, team1_name, team2_name),
                              '{} {} on {} - {} vs {}'.format(first_name, last_name, gd, team1_name, team2_name),
                              plot_type=plot_type, hex_size=hex_size, overplot_shots=overplot_shots)
