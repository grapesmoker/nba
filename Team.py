from nba_2013_14 import teams

class NoCollectionError(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class Team:

    _coll = teams

    def __init__(self, team_id=None, collection=None):
        if collection is not None:
            self.__class__._coll = collection
            self._coll = collection
        elif self._coll is None:
            if self.__class__._coll is None:
                raise NoCollectionError('Must have a collection in MongoDB!')
            else:
                self._coll = self.__class__._coll

        if team_id is not None:
            self.get_by_team_id(team_id)

    def get_by_team_id(self, team_id):

        self._data = self._coll.find_one({'id': team_id})
        
    @property
    def location(self):
        return self._data['location']

    @property
    def nickname(self):
        return self._data['nickname']

    @property
    def id(self):
        return self._data['id']

    def __str__(self):
        return ' '.join((self.location, self.nickname))

    def __repr__(self):
        return self.__str__()


    def get_team_stats(game_day, stat):

        game = Game.look_up_game(game_day, self._id)
        
        if self._id == game.home_team['id']:
            game_stats = game.home_boxscore['teamStats']
        elif self._id == game.away_team['id']:
            game_stats = game.away_boxscore['teamStats']

        #stats_data = [data_value for data_name in game_stats if data
