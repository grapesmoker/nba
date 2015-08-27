__author__ = 'jerry'


def team_ocluster_features(team_id, start_date=dt.date(2012, 10, 27), end_date=dt.date(2013, 4, 17)):

    team_data = cumul_team_ortg_drtg(team_id, start_date=start_date, end_date=end_date, return_type='full')

    fgm = team_data['fgm']
    fga = team_data['fga']
    fta = team_data['fta']
    ftm = team_data['ftm']
    pos = team_data['pos']
    tov = team_data['tov']
    orb = team_data['orb']
    threes = team_data['threes']
    opp_drb = team_data['opp_drb']
    opp_orb = team_data['opp_orb']

    ortg = team_data['ortg']

    efg_pct = (fgm + 0.5 * threes) / fga
    tov_pct = 100 * tov / (fga + 0.44 * fta + tov)
    orb_pct = 100 * orb / (opp_drb + orb)
    ft_fga = ftm / fga

    features = [team_id, efg_pct, tov_pct, orb_pct, ft_fga, ortg]

    return features

def team_dcluster_features(team_id, start_date=dt.date(2012, 10, 30), end_date=dt.date(2013, 4, 17)):

    team_data = cumul_team_ortg_drtg(team_id, start_date=start_date, end_date=end_date, return_type='full')

    opp_fta = team_data['opp_fta']
    opp_ftm = team_data['opp_ftm']
    drb  = team_data['drb']
    opp_threes = team_data['opp_threes']
    opp_drb = team_data['opp_drb']
    opp_orb = team_data['opp_orb']
    opp_tov = team_data['opp_tov']
    opp_fga = team_data['opp_fga']
    opp_fgm = team_data['opp_fgm']

    drtg = team_data['drtg']

    print opp_threes, opp_drb, opp_orb, opp_tov, opp_fga, opp_fgm

    opp_efg_pct = (opp_fgm + 0.5 * opp_threes) / opp_fga
    opp_tov_pct = 100 * opp_tov / (opp_fga + 0.44 * opp_fta + opp_tov)
    drb_pct = 100 * drb / (opp_orb + drb)
    opp_ft_fga = opp_ftm / opp_fga

    features = [team_id, opp_efg_pct, opp_tov_pct, drb_pct, opp_ft_fga, drtg]

    return features

def player_ocluster_features(player_id, start_date=dt.date(2012, 10, 27), end_date=dt.date(2013, 4, 17)):

    games_played = games_played_pbp(player_id, start_date, end_date)

    ast = 0
    fgm = 0
    fga = 0
    ftm = 0
    fta = 0
    orb = 0
    tpa = 0
    tpm = 0
    pts = 0
    tov = 0
    mp = 0

    team_orb = 0
    team_mp = 0
    team_fgm = 0
    team_pos = 0
    team_pts = 0

    opp_drb = 0

    for i, game in enumerate(games_played):
        game_id = int(game['playbyplay']['contest']['id'])

        player_data, team_data = player_ortg(game_id, player_id, return_data=True)

        ast += player_data['ast']
        fgm += player_data['fgm']
        fga += player_data['fga']
        ftm += player_data['ftm']
        fta += player_data['fta']
        tov += player_data['tov']
        tpa += player_data['threes_a']
        tpm += player_data['threes']
        orb += player_data['orb']
        pts += player_data['pts']
        mp += player_data['mp']

        team_orb += team_data['team_orb']
        team_mp += team_data['team_mp']
        team_fgm += team_data['team_fgm']
        team_pos += team_data['team_pos']
        team_pts += team_data['team_pts']
        opp_drb += team_data['opp_dreb']


    try:

        #print team_pts, team_pos

        team_ortg = 100 * team_pts / team_pos

        ast_pct = 100 * ast / (((mp / (team_mp / 5)) * team_fgm) - fgm)
        ts_pct = pts / (2 * (fga + 0.44 * fta))
        orb_pct = 100 * (orb * (team_mp / 5)) / (mp * (team_orb + opp_drb))
        mp_pct = 100 * mp / (team_mp / 5)
        usg = cumul_player_usage(player_id, start_date, end_date)
        ortg = cumul_player_ortg(player_id, start_date, end_date)

        #print team_ortg, ortg

        ortg_pct = 100 * (1 + (ortg - team_ortg)  / team_ortg)

        features = [player_id, ast_pct, ts_pct, orb_pct, usg, ortg, mp_pct]

    except Exception as ex:
        print ex

        features = [player_id, 0, 0, 0, 0, 0, 0]

    return features

def player_dcluster_features(player_id, start_date=dt.date(2012, 10, 27), end_date=dt.date(2013, 4, 17)):

    games_played = games_played_pbp(player_id, start_date, end_date)

    drb = 0
    pf = 0
    mp = 0
    stl = 0
    blk = 0

    team_mp = 0
    team_blk = 0
    team_stl = 0
    team_drb = 0
    team_pf = 0

    team_pos = 0

    opp_fta = 0
    opp_ftm = 0
    opp_fga = 0
    opp_fgm = 0
    opp_orb = 0
    opp_pts = 0
    opp_tov = 0
    opp_mp = 0
    opp_3pa = 0
    opp_pos = 0

    for i, game in enumerate(games_played):
        game_id = int(game['playbyplay']['contest']['id'])

        player_data, team_data = player_drtg(game_id, player_id, return_data=True)

        drb += player_data['drb']
        pf += player_data['pf']
        stl += player_data['stl']
        blk += player_data['blk']
        mp += player_data['mp']

        opp_fta += team_data['opp_fta']
        opp_ftm += team_data['opp_ftm']
        opp_fga += team_data['opp_fga']
        opp_fgm += team_data['opp_fgm']
        opp_pts += team_data['opp_pts']
        opp_orb += team_data['opp_orb']
        opp_3pa += team_data['opp_3pa']
        opp_pos += team_data['opp_pos']

        team_drb += team_data['team_drb']
        team_mp += team_data['team_mp']
        team_pf += team_data['team_pf']

    try:

        blk_pct = 100 * (blk * (team_mp / 5)) / (mp * (opp_fga - opp_3pa))
        stl_pct = 100 * (stl * (team_mp / 5)) / (mp * opp_pos)
        drb_pct = 100 * (drb * (team_mp / 5)) / (mp * (team_drb + opp_orb))
        pf_pct = 100 * pf / team_pf
        mp_pct = 100 * mp / (team_mp / 5)
        drtg = cumul_player_drtg(player_id, start_date, end_date)

        features = [player_id, blk_pct, stl_pct, drb_pct, drtg, pf_pct, mp_pct]

    except Exception as ex:

        features = [player_id, 0, 0, 0, 0, 0, 0]

    return features

def merge_team_features(off_file, def_file, output_file):

    off_data = pylab.genfromtxt(off_file, delimiter=',')
    def_data = pylab.genfromtxt(def_file, delimiter=',')

    print len(off_data[0])
    print len(def_data)

    writer = csv.writer(open(output_file, 'w'))

    off_data = sorted(off_data, key=lambda x: x[0])
    def_data = sorted(def_data, key=lambda x: x[0])

    for oline, dline in zip(off_data, def_data):
        comb_line = pylab.concatenate((oline, dline[1:]))
        writer.writerow(comb_line)

def add_team_clusters_to_csv(input_filename, output_filename):

    reader = csv.reader(open(input_filename, 'r'))
    writer = csv.writer(open(output_filename, 'w'))
    headers = reader.next()

    headers.append('home_oclass')
    headers.append('home_dclass')
    headers.append('home_tclass')
    headers.append('away_oclass')
    headers.append('away_dclass')
    headers.append('away_tclass')

    writer.writerow(headers)

    team_oclusters, off_gmm = compute_team_clusters('team_features_offense_w_id.csv')
    team_dclusters, def_gmm = compute_team_clusters('team_features_defense_w_id.csv')
    team_tclusters, tot_gmm = compute_team_clusters('team_features_combined.csv')

    for line in reader:

        home_team = int(line[3].strip())
        away_team = int(line[4].strip())

        home_oclass = find_member_in_clusters(team_oclusters, home_team)
        home_dclass = find_member_in_clusters(team_dclusters, home_team)
        home_tclass = find_member_in_clusters(team_tclusters, home_team)
        away_oclass = find_member_in_clusters(team_oclusters, away_team)
        away_dclass = find_member_in_clusters(team_dclusters, away_team)
        away_tclass = find_member_in_clusters(team_tclusters, away_team)

        writer.writerow(line + [home_oclass, home_dclass, home_tclass, away_oclass, away_dclass, away_tclass])

def construct_odds_csv(input_filename, output_filename):

    reader = csv.reader(open(input_filename, 'r'))
    stat_cats = ['PTS', 'FG%', '3P%', 'DRB%', 'ORB%', 'AST', 'BLK', 'STL',
                 'TOV', 'FT%', 'PIP', 'PTO', '2CP', 'FBP', 'PFL', 'DRTG', 'ORTG', 'REST']

    stat_headers = {'PTS': 'points',
                    'FG%': 'field_goal_pct',
                    '3P%': '3_pt_pct',
                    'DRB%': 'def_reb_pct',
                    'ORB%': 'off_reb_pct',
                    'AST': 'assists',
                    'BLK': 'blocks',
                    'STL': 'steals',
                    'TOV': 'turnovers',
                    'FT%': 'free_throw_pct',
                    'PIP': 'pts_in_paint',
                    'PTO': 'pts_off_tov',
                    '2CP': '2nd_chance_pts',
                    'FBP': 'fast_break_pts',
                    'PFL': 'fouls',
                    'DRTG': 'def_rtg',
                    'ORTG': 'off_rtg'}

    output_headers = reader.next() + ['home_points',
                                      'home_field_goal_pct',
                                      'home_3_pt_pct',
                                      'home_def_reb_pct',
                                      'home_off_reb_pct',
                                      'home_assists',
                                      'home_blocks',
                                      'home_steals',
                                      'home_turnovers',
                                      'home_free_throw_pct',
                                      'home_pts_in_paint',
                                      'home_pts_off_tov',
                                      'home_2nd_chance_pts',
                                      'home_fast_break_pts',
                                      'home_fouls',
                                      'home_def_rtg',
                                      'home_off_rtg',
                                      'home_days_rest',
    ## features for individual players
    ## 7 offensive players, ranked by minutes
                                      'home_p1_off',
                                      'home_p2_off',
                                      'home_p3_off',
                                      'home_p4_off',
                                      'home_p5_off',
                                      'home_p6_off',
                                      'home_p7_off',
    ## 7 defensive players, ranked by minutes
                                      'home_p1_def',
                                      'home_p2_def',
                                      'home_p3_def',
                                      'home_p4_def',
                                      'home_p5_def',
                                      'home_p6_def',
                                      'home_p7_def',
    ## away team
                                      'away_points',
                                      'away_field_goal_pct',
                                      'away_3_pt_pct',
                                      'away_def_reb_pct',
                                      'away_off_reb_pct',
                                      'away_assists',
                                      'away_blocks',
                                      'away_steals',
                                      'away_turnovers',
                                      'away_free_throw_pct',
                                      'away_pts_in_paint',
                                      'away_pts_off_tov',
                                      'away_2nd_chance_pts',
                                      'away_fast_break_pts',
                                      'away_fouls',
                                      'away_def_rtg',
                                      'away_off_rtg',
                                      'away_days_rest',
    ## features for individual players
    ## 7 offensive players, ranked by minutes
                                      'away_p1_off',
                                      'away_p2_off',
                                      'away_p3_off',
                                      'away_p4_off',
                                      'away_p5_off',
                                      'away_p6_off',
                                      'away_p7_off',
    ## 7 defensive players, ranked by minutes
                                      'away_p1_def',
                                      'away_p2_def',
                                      'away_p3_def',
                                      'away_p4_def',
                                      'away_p5_def',
                                      'away_p6_def',
                                      'away_p7_def',]

    off_data = pylab.genfromtxt('offense_clusters_w_id.csv', delimiter=',')
    def_data = pylab.genfromtxt('defense_clusters_w_id.csv', delimiter=',')

    print 'Clustering offense...'
    player_oclusters, off_gmm = compute_player_clusters('offense_clusters_w_id.csv', clusters=10, method='GMM')
    print 'Clustering defense...'
    player_dclusters, def_gmm = compute_player_clusters('defense_clusters_w_id.csv', clusters=10, method='GMM')

    print 'Constructing odds data...'
    output_lines = [output_headers]

    writer = csv.writer(open(output_filename, 'w'))
    writer.writerow(output_headers)

    for line in reader:
        year = int(line[0].strip())
        month = int(line[1].strip())
        day = int(line[2].strip())
        game_day = dt.date(year=year, month=month, day=day)
        home_team = int(line[3].strip())
        away_team = int(line[4].strip())

        print game_day, home_team, away_team

        try:
            game_id = look_up_contest_id(game_day, home_team)

            home_players = game_players(game_id, home_team)[0:7]
            away_players = game_players(game_id, away_team)[0:7]



            home_box, away_box = boxscore_stats(game_day, home_team)

            # insert the home stats
            for stat in stat_cats:
                line.append(home_box[stat])

            for hp in home_players:
                player_oclass = find_member_in_clusters(player_oclusters, hp)
                line.append(player_oclass)

            for hp in home_players:
                player_dclass = find_member_in_clusters(player_dclusters, hp)
                line.append(player_dclass)

            # insert the away stats
            for stat in stat_cats:
                line.append(away_box[stat])

            for ap in away_players:
                player_oclass = find_member_in_clusters(player_oclusters, ap)
                line.append(player_oclass)

            for ap in away_players:
                player_dclass = find_member_in_clusters(player_dclusters, ap)
                line.append(player_dclass)

        except Exception as ex:
            print ex
            print 'Game not found... possibly a game was postponed/canceled'

        writer.writerow(line)
        output_lines.append(line)