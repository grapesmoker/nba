__author__ = 'jerry'

import numpy as np
import matplotlib.pyplot as mpl
import pandas as pd
import os
import datetime as dt

from sklearn.mixture import GMM
from sklearn.cluster import AffinityPropagation, DBSCAN, KMeans, Ward
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import *
from sklearn.svm import *
from sklearn.ensemble import *
from sklearn.naive_bayes import *

from sklearn.manifold import MDS

from matplotlib.colors import Normalize, BoundaryNorm, ListedColormap

from Player import Player
from features import *
from clustering import *

features_to_use = ['home_eff_field_goal_pct',
                   # 'home_def_reb_pct',
                   # 'home_off_reb_pct',
                   # 'home_off_tov_pct',
                   # 'home_def_tov_pct',
                   # 'home_free_throw_rate',
                   'home_def_rtg',
                   'home_off_rtg',
                   'home_days_rest',
                   # 'home_p0_off',
                   # 'home_p1_off',
                   # 'home_p2_off',
                   # 'home_p3_off',
                   # 'home_p4_off',
                   # 'home_p5_off',
                   # 'home_p6_off',
                   # 'home_p0_def',
                   # 'home_p1_def',
                   # 'home_p2_def',
                   # 'home_p3_def',
                   # 'home_p4_def',
                   # 'home_p5_def',
                   # 'home_p6_def',
                   'away_eff_field_goal_pct',
                   # 'away_def_reb_pct',
                   # 'away_off_reb_pct',
                   # 'away_off_tov_pct',
                   # 'away_def_tov_pct',
                   # 'away_free_throw_rate',
                   'away_def_rtg',
                   'away_off_rtg',
                   'away_days_rest',
                   # 'away_p0_off',
                   # 'away_p1_off',
                   # 'away_p2_off',
                   # 'away_p3_off',
                   # 'away_p4_off',
                   # 'away_p5_off',
                   # 'away_p6_off',
                   # 'away_p0_def',
                   # 'away_p1_def',
                   # 'away_p2_def',
                   # 'away_p3_def',
                   # 'away_p4_def',
                   # 'away_p5_def',
                   # 'away_p6_def'
                   ]


def predict_game_outcome(data_source, game, season, start_date=None, end_date=None, method='LogReg'):

    if isinstance(data_source, str):
        data = pd.read_csv(data_source, index_col=0)
        feature_file = data_source
    elif isinstance(data_source, pd.DataFrame):
        data = data_source
        feature_file = None
    else:
        raise TypeError('Invalid type!')

    data = data[data.home_off_rtg > 0]

    training_data = data[features_to_use].values

    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(training_data)

    home_points = data['home_points']
    away_points = data['away_points']
    plus_minus = (home_points - away_points).values

    if method == 'LogReg':
        classifier = LogisticRegression()
    elif method == 'Lasso':
        classifier = Lasso()
    elif method == 'Ridge':
        classifier = Ridge()
    elif method == 'BayesRidge':
        classifier = BayesianRidge()
    elif method == 'SVM':
        classifier = SVC()
    elif method == 'RandForest':
        classifier = RandomForestClassifier()
    elif method == 'NaiveBayes':
        classifier = GaussianNB()
    else:
        classifier = LinearRegression()

    classifier.fit(scaled_data, plus_minus)

    home_team = game.home_team
    away_team = game.away_team

    game_features = construct_global_features(season, team=home_team,
                                              start_date=start_date, end_date=end_date, game_date=game.date)
    game_features = game_features[features_to_use].values
    scaled_features = scaler.transform(game_features)


    result = classifier.predict(scaled_features)
    # print classifier.classes_
    # print classifier.score(scaled_data, plus_minus)
    # print game.id, result

    return result

def predict_game_day(game_date, season, start_date=None, end_date=None, method='LogReg'):

    if start_date is None:
        start_date = season.start_date
    if end_date is None:
        end_date = season.end_date

    str_format = '%Y-%m-%d'

    features_file = os.path.join('season_data', str(season.season),
                                 'features-from-{}-to-{}'.format(start_date.strftime(str_format),
                                                                 end_date.strftime(str_format)))

    # if we've already computed the features, just load the file
    # otherwise compute the features
    if os.path.exists(features_file):
        print 'loading features from {}'.format(features_file)
        data = pd.read_csv(features_file, index_col=0)
    else:
        data = construct_global_features(season, start_date=start_date, end_date=end_date, output_file=features_file)

    data = data[data.home_off_rtg > 0]
    training_data = data[features_to_use].values

    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(training_data)
    home_points = data['home_points']
    away_points = data['away_points']
    plus_minus = (home_points - away_points).values

    if method == 'LogReg':
        classifier = LogisticRegression()
    elif method == 'Lasso':
        classifier = Lasso()
    elif method == 'Ridge':
        classifier = Ridge()
    elif method == 'BayesRidge':
        classifier = BayesianRidge()
    elif method == 'SVM':
        classifier = SVC()
    else:
        classifier = LinearRegression()

    classifier.fit(scaled_data, plus_minus)
    #import pdb; pdb.set_trace()
    game_features = construct_global_features(season, start_date=start_date, end_date=end_date, game_date=game_date)
    game_features = game_features[features_to_use].values
    game_features = scaler.transform(game_features)

    games = season.get_all_games_in_range(start_date=game_date, end_date=game_date)
    true_pm = [game.home_points - game.away_points for game in games]

    #print classifier.classes_
    print classifier.score(game_features, true_pm)

    result = classifier.predict(game_features)
    #print classifier.coef_
    for g, r, t in zip(games, result, true_pm):
        print g.id, g, round(r, 2), t

    return result


def predict_all_games(season, window_size=20, method='LogReg'):

    window = dt.timedelta(days=window_size)
    one_day = dt.timedelta(days=1)
    str_format = '%Y-%m-%d'

    prediction_results = []

    games = season.get_all_games_in_range(season.start_date + window + one_day, season.end_date)

    for game in tqdm(games):

        end_date = game.date - one_day
        start_date = end_date - window

        features_file = os.path.join('season_data', str(season.season),
                                     'features-from-{}-to-{}'.format(start_date.strftime(str_format),
                                                                     end_date.strftime(str_format)))

        result = predict_game_outcome(features_file, game, season,
                                      start_date=start_date, end_date=end_date, method=method)
        prediction_results.append((game, result))

        # print game
        # if result[0] > 0:
        #     print 'prediction: {} (home) wins by {}'.format(game.home_team, result[0])
        # elif result < 0:
        #     print 'prediction: {} (away) wins by {}'.format(game.away_team, result[0])
        # elif result == 0:
        #     print 'prediction: coin flip'
        #
        # plus_minus = game.home_points - game.away_points
        # if plus_minus > 0:
        #     print 'result: {} (home) wins by {}'.format(game.home_team, plus_minus)
        # elif result < 0:
        #     print 'result: {} (away) wins by {}'.format(game.away_team, plus_minus)

    return prediction_results