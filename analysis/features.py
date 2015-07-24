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
