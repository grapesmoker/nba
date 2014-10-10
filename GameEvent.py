# class for the play-by-play object

import datetime as dt
from nba_2013_14 import pbp, play_time

class NoCollectionError(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

class GameEvent:

    _coll = pbp

    def __init__(self, collection=None, event_id=None):
        if collection is not None:
            self.__class__._coll = collection
            self._coll = collection
        elif self._coll is None:
            if self.__class__._coll is None:
                raise NoCollectionError('Must have a collection in MongoDB!')
            else:
                self._coll = self.__class__._coll

        if event_id is not None:
            self.get_by_event_id(event_id)

    def get_by_event_id(self, event_id):

        data = self._coll.find_one({'league.season.eventType.0.events.0.eventId': event_id})
        self._data = data
        self.set_data(self._data)

    def set_data(self, data):


        # all the actual data is contained in here, so let's just throw away the outer
        # shells of the json
        self._core_data = data['league']['season']['eventType'][0]['events'][0]
        self._date = dt.datetime.strptime(self._core_data['startDate'][0]['full'], '%Y-%m-%dT%H:%M:%S')
        self._teams = self._core_data['teams']
        self._home_team = self._teams[0]
        self._away_team = self._teams[1]
        self._home_boxscore = self._core_data['boxscores'][0]
        self._away_boxscore = self._core_data['boxscores'][1]
        self._pbp = self._core_data['pbp']

    def __str__(self):
        home_team_name = self._home_team['location'] + ' ' + self._home_team['nickname']
        away_team_name = self._away_team['location'] + ' ' + self._away_team['nickname']
        return '{0} vs {1} on {2!s}'.format(home_team_name, away_team_name, self._date)

    def __repr__(self):
        return self.__str__()

    @property
    def teams(self):
        return self._teams
        
    @property
    def home_team(self):
        return self._home_team
        
    @property
    def away_team(self):
        return self._away_team

    @property
    def pbp(self):
        return self._pbp

    @property
    def date(self):
        return self._date

    def events_by_player(self, player_id):
        
        def is_player_involved(event, player_id):
            for player in event['players']:
                if player['playerId'] == player_id:
                    return True
            return False

        player_events = [event for event in self._pbp if is_player_involved(event, player_id)]

        return player_events

    def quarter_starters(self):

        starting_lineup = [play['players'][0]['playerId'] for play in self._pbp if play['playText'] == 'Starting Lineup']

        quarter_starters = {}
        quarter_starters[1] = starting_lineup

        for q in (2, 3, 4):

            quarter_plays = sorted([play for play in self._pbp if play['period'] == q], reverse=True, key=play_time)

            players_used = []
            subs_used = []
            i = 0
            done = False

            while i < len(quarter_plays) and not done:
                play = quarter_plays[i]
                players = play['players']

                if play['playText'].find('Substitution:') > -1:
                    subbed_in_player = players[0]['playerId']
                    subs_used.append(subbed_in_player)
                    subbed_out_player = players[1]['playerId']
                    if subbed_out_player not in players_used:
                        players_used.append(subbed_out_player)
                else:
                    for player in players:
                        #print player
                        if player['playerId'] not in subs_used and player['playerId'] not in players_used:
                            players_used.append(player['playerId'])

                i += 1
                if len(players_used) == 10:
                    done = True

            quarter_starters[q] = players_used

        return quarter_starters

                    
