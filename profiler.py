#!/usr/bin/env python

from Game import Game
from Player import Player
from Team import Team

from pprint import pprint

from analysis import regression

def test_single_game_rapm():

    game = Game(1349547)
    team = game.home_team
    
    print game

    regression.regress_lineups_single_game(game, team)

def test_single_lineup():

    game = Game(1349077)

    jcrawford = Player(3388)
    mbarnes = Player(168051)
    jjredick = Player(172643)
    rhollins = Player(177575)
    bgriffin = Player(399725)
    jdudley = Player(241712)
    djordan = Player(398142)
    cpaul = Player(229598)

    players = [jjredick, cpaul, bgriffin, djordan, jdudley]

    timestream = game.time_by_lineup(players)
    box_score = game.stats_by_lineup(players)

    print timestream
    pprint(box_score.__dict__)

if __name__ == '__main__':
    #test_single_lineup()
    test_single_game_rapm()
