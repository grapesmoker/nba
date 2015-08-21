from network import teams

class NoCollectionError(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

class TeamDataError(Exception):

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

    def possessions(self, game):

        if game.is_home(self):
            return game.home_possessions
        elif game.is_away(self):
            return game.away_possessions
        else:
            raise TeamDataError('{} did not participate in {}'.format(self, game))

    def stats(self, game):

        if game.is_home(self):
            return game.home_boxscore
        elif game.is_away(self):
            return game.away_boxscore
        else:
            raise TeamDataError('{} did not participate in {}'.format(self, game))

    def drtg(self, game):

        if game.is_home(self):
            return game.home_drtg
        elif game.is_away(self):
            return game.away_drtg
        else:
            raise TeamDataError('{} did not participate in {}'.format(self, game))

    def ortg(self, game):

        if game.is_home(self):
            return game.home_ortg
        elif game.is_away(self):
            return game.away_ortg
        else:
            raise TeamDataError('{} did not participate in {}'.format(self, game))