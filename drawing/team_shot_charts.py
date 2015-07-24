__author__ = 'jerry'

def team_shot_chart_with_player (game_id, player_id, plot_type='hexbin', hex_size=1, **kwargs):

    game = pbp.find_one({'playbyplay.contest.id': str(game_id)})
    plays = game['playbyplay']['plays']['play']
    player_times = player_time_on_court(game_id, player_id)
    player_plays = get_plays_in_intervals(plays, player_times)
    player_team_id = look_up_player_team(game_id, player_id)

    if 'include_player' in kwargs and kwargs['include_player'] == True:
        non_player_plays = [play for play in player_plays if play['team-id-1'] == str(player_team_id)]
    else:
        non_player_plays = [play for play in player_plays if play['player1-id'] != str(player_id)
                            and play['team-id-1'] == str(player_team_id)]

    made_shots_coords, missed_shots_coords = filter_missed_made(non_player_plays)

    fn, ln = look_up_player_name(player_id)
    gd = game_day(game_id).replace('/', '-')
    team1_name, team1_id, team2_name, team2_id = game_teams(game_id)

    print 'Processing {} vs {} on {}'.format(team1_name, team2_name, gd)

    if 'return_data' in kwargs:
        if kwargs['return_data'] == True:
            return made_shots_coords, missed_shots_coords

    if 'output_type' in kwargs:
        output_type = kwargs['output_type']
    else:
        output_type = 'pdf'

    create_shot_chart(made_shots_coords, missed_shots_coords,
                      'plots/teams/team_shots_with_{}_{}_{}_{}_vs_{}_pt_{}_hx_{}.{}'.format(fn, ln, gd, team1_name, team2_name, plot_type, hex_size, output_type),
                      'Team shots with {} {} on {} - {} vs {}'.format(fn, ln, gd, team1_name, team2_name),
                      plot_type=plot_type, hex_size=hex_size, **kwargs)

def team_shot_chart_without_player (game_id, player_id, plot_type='hexbin', hex_size=1, **kwargs):

    game = pbp.find_one({'playbyplay.contest.id': str(game_id)})
    plays = game['playbyplay']['plays']['play']
    player_times = player_time_on_court(game_id, player_id)
    player_team_id = look_up_player_team(game_id, player_id)

    non_player_plays = [play for play in get_plays_not_in_intervals(plays, player_times)
                        if play['team-id-1'] == str(player_team_id)]

    made_shots_coords, missed_shots_coords = filter_missed_made(non_player_plays)

    gd = game_day(game_id).replace('/', '-')
    team1_name, team1_id, team2_name, team2_id = game_teams(game_id)
    fn, ln = look_up_player_name(player_id)

    print 'Processing {} vs {} on '.format(team1_name, team2_name, gd)

    if 'return_data' in kwargs:
        if kwargs['return_data'] == True:
            return made_shots_coords, missed_shots_coords

    if 'output_type' in kwargs:
        output_type = kwargs['output_type']
    else:
        output_type = 'pdf'

    create_shot_chart(made_shots_coords, missed_shots_coords,
                      'plots/teams/team_shots_without_{}_{}_{}_{}_vs_{}_pt_{}_hx_{}.{}'.format(fn, ln, gd, team1_name, team2_name, plot_type, hex_size, output_type),
                      'Team shots without {} {} on {} - {} vs {}'.format(fn, ln, gd, team1_name, team2_name),
                      plot_type=plot_type, hex_size=hex_size, **kwargs)

def cumul_team_shot_chart_with_player (player_id, plot_type='hexbin', hex_size=1, **kwargs):

    games_played = games_played_pbp(player_id)
    fn, ln = look_up_player_name(player_id)

    print 'Generating cumulative team shot chart for {} {} on'.format(fn, ln)

    cumul_made_shots_coords = []
    cumul_missed_shots_coords = []

    for game in games_played:
        game_id = int(game['playbyplay']['contest']['id'])
        made_shots_coords, missed_shots_coords = team_shot_chart_with_player(game_id, player_id, return_data=True)
        cumul_made_shots_coords = pylab.concatenate((cumul_made_shots_coords, made_shots_coords))
        cumul_missed_shots_coords = pylab.concatenate((cumul_missed_shots_coords, missed_shots_coords))

    if 'return_data' in kwargs:
        if kwargs['return_data'] == True:
            return cumul_made_shots_coords, cumul_missed_shots_coords

    if 'output_type' in kwargs:
        output_type = kwargs['output_type']
    else:
        output_type = 'pdf'

    create_shot_chart(cumul_made_shots_coords, cumul_missed_shots_coords,
                      'plots/teams/cumul_team_shots_with_{}_{}_pt_{}_hx_{}.{}'.format(fn, ln, plot_type, hex_size, output_type),
                      'Cumulative team shots with {} {}'.format(fn, ln),
                      plot_type=plot_type, hex_size=hex_size, **kwargs)

def cumul_team_shot_chart_without_player (player_id, plot_type='hexbin', hex_size=1, **kwargs):

    games_played = games_played_pbp(player_id)
    fn, ln = look_up_player_name(player_id)

    print 'Generating cumulative team shot chart for {} {} off'.format(fn, ln)

    cumul_made_shots_coords = []
    cumul_missed_shots_coords = []

    for game in games_played:
        game_id = int(game['playbyplay']['contest']['id'])
        made_shots_coords, missed_shots_coords = team_shot_chart_without_player(game_id, player_id, return_data=True)
        cumul_made_shots_coords = pylab.concatenate((cumul_made_shots_coords, made_shots_coords))
        cumul_missed_shots_coords = pylab.concatenate((cumul_missed_shots_coords, missed_shots_coords))

    if 'return_data' in kwargs:
        if kwargs['return_data'] == True:
            return cumul_made_shots_coords, cumul_missed_shots_coords

    if 'output_type' in kwargs:
        output_type = kwargs['output_type']
    else:
        output_type = 'pdf'

    create_shot_chart(cumul_made_shots_coords, cumul_missed_shots_coords,
                      'plots/teams/cumul_team_shots_without_{}_{}_pt_{}_hx_{}.{}'.format(fn, ln, plot_type, hex_size, output_type),
                      'Cumulative team shots without {} {}'.format(fn, ln),
                      plot_type=plot_type, hex_size=hex_size, **kwargs)

def cumul_team_differential(player_id, plot_type='hexbin', hex_size=1, **kwargs):

    made_shots_with_player, missed_shots_with_player = cumul_team_shot_chart_with_player(player_id, return_data=True)
    made_shots_without_player, missed_shots_without_player = cumul_team_shot_chart_without_player(player_id, return_data=True)

    with_player_cells = create_shot_chart(made_shots_with_player, missed_shots_with_player, '', '', hex_size=hex_size, return_cells=True, **kwargs)
    wout_player_cells = create_shot_chart(made_shots_without_player, missed_shots_without_player, '', '', hex_size=hex_size, return_cells=True, **kwargs)

    diff_hexes = create_hexes(hex_size)
    fig = mpl.figure()

    gs = gridspec.GridSpec(1, 2, width_ratios=[1, 10])

    ax_cb = mpl.subplot(gs[0,0])
    ax = mpl.subplot(gs[0,1])

    draw_court(ax)
    cm = mpl.cm.jet
    norm = Normalize(-1.5, 1.5)

    total_with_attempts = sum([cell['made'] + cell['missed'] for cell in with_player_cells])
    total_wout_attempts = sum([cell['made'] + cell['missed'] for cell in wout_player_cells])

    max_with_attempts = max([cell['made'] + cell['missed'] for cell in with_player_cells])
    min_with_attempts = min([cell['made'] + cell['missed'] for cell in with_player_cells if cell['made'] + cell['missed'] > 0])

    max_wout_attempts = max([cell['made'] + cell['missed'] for cell in wout_player_cells])
    min_wout_attempts = min([cell['made'] + cell['missed'] for cell in wout_player_cells if cell['made'] + cell['missed'] > 0])


    max_attempts_frac = 100.0 * max(max_with_attempts, max_wout_attempts) / total_with_attempts
    min_attempts_frac = 100.0 * min(min_with_attempts, min_wout_attempts) / total_wout_attempts

    if 'scale_factor' in kwargs:
        max_attempts_frac = min_attempts_frac * kwargs['scale_factor']
    else:
        # default scale factor
        max_attempts_frac = min_attempts_frac * 64

    max_size = hex_size
    min_size = hex_size / 8.0

    if max_with_attempts > 1 and max_wout_attempts > 1:
        m = (float(max_size) - min_size) / (max_attempts_frac - 1)
        b = min_size - m
    else:
        m = max_size
        b = 0

    for cell_with, cell_wout in zip(with_player_cells, wout_player_cells):
        with_attempts = cell_with['made'] + cell_with['missed']
        wout_attempts = cell_wout['made'] + cell_wout['missed']
        #total_attempts += attempts

        with_attempts_frac = 100.0 * with_attempts / total_with_attempts
        wout_attempts_frac = 100.0 * wout_attempts / total_wout_attempts
        diff_attempts_frac = with_attempts_frac - wout_attempts_frac

        if with_attempts > 0:
            with_efg = (cell_with['made'] + 0.5 * cell_with['threes']) / with_attempts
        else:
            with_efg = 0

        if wout_attempts > 0:
            wout_efg = (cell_wout['made'] + 0.5 * cell_wout['threes']) / wout_attempts
        else:
            wout_efg = 0

        diff_efg = with_efg - wout_efg
        scaled_attempts = min(diff_attempts_frac, max_attempts_frac)
        size = scaled_attempts * m + b

        print with_efg, wout_efg, diff_efg, size

        patch = RegularPolygon((cell_with['x'], cell_with['y']), 6, size, orientation=pylab.pi/6, color=cm(norm(diff_efg)), alpha=0.75)
        outline = RegularPolygon((cell_with['x'], cell_with['y']), 6, hex_size, orientation=pylab.pi/6, fill=False, color='y', linestyle='dotted')
        ax.add_patch(patch)
        ax.add_patch(outline)
        #if hex_size >= 4:
        #    ax.text(cell['x'], cell['y'], '{0:2.2f}'.format(attempts_frac))

    if plot_type == 'hexbin':
        cb = ColorbarBase(ax_cb, cmap=cm, norm=norm, orientation='vertical')
        cb.set_label('Differential Effective Field Goal Percentage', fontsize='small')
        mpl.tight_layout()

    mpl.show()


def opp_shot_chart_with_player (game_id, player_id, plot_type='hexbin', hex_size=1, **kwargs):

    game = pbp.find_one({'playbyplay.contest.id': str(game_id)})
    plays = game['playbyplay']['plays']['play']
    player_times = player_time_on_court(game_id, player_id)
    player_plays = get_plays_in_intervals(plays, player_times)
    player_team_id = look_up_player_team(game_id, player_id)

    non_player_plays = [play for play in player_plays if play['player1-id'] != str(player_id)
                        and play['team-id-1'] != str(player_team_id)]

    made_shots_coords, missed_shots_coords = filter_missed_made(non_player_plays)

    fn, ln = look_up_player_name(player_id)
    gd = game_day(game_id).replace('/', '-')
    team1_name, team1_id, team2_name, team2_id = game_teams(game_id)

    print 'Processing {} vs {} on {}'.format(team1_name, team2_name, gd)

    if 'return_data' in kwargs:
        if kwargs['return_data'] == True:
            return made_shots_coords, missed_shots_coords

    if 'output_type' in kwargs:
        output_type = kwargs['output_type']
    else:
        output_type = 'pdf'

    create_shot_chart(made_shots_coords, missed_shots_coords,
                      'plots/teams/opp_shots_with_{}_{}_{}_{}_vs_{}_pt_{}_hx_{}.{}'.format(fn, ln, gd, team1_name, team2_name, plot_type, hex_size, output_type),
                      'Opponent shots with {} {} on {} - {} vs {}'.format(fn, ln, gd, team1_name, team2_name),
                      plot_type=plot_type, hex_size=hex_size, **kwargs)

def opp_shot_chart_without_player (game_id, player_id, plot_type='hexbin', hex_size=1, **kwargs):

    game = pbp.find_one({'playbyplay.contest.id': str(game_id)})
    plays = game['playbyplay']['plays']['play']
    player_times = player_time_on_court(game_id, player_id)
    player_team_id = look_up_player_team(game_id, player_id)

    non_player_plays = [play for play in get_plays_not_in_intervals(plays, player_times)
                        if play['team-id-1'] != str(player_team_id)]

    made_shots_coords, missed_shots_coords = filter_missed_made(non_player_plays)

    gd = game_day(game_id).replace('/', '-')
    team1_name, team1_id, team2_name, team2_id = game_teams(game_id)
    fn, ln = look_up_player_name(player_id)

    print 'Processing {} vs {} on {}'.format(team1_name, team2_name, gd)

    if 'return_data' in kwargs:
        if kwargs['return_data'] == True:
            return made_shots_coords, missed_shots_coords

    if 'output_type' in kwargs:
        output_type = kwargs['output_type']
    else:
        output_type = 'pdf'

    create_shot_chart(made_shots_coords, missed_shots_coords,
                      'plots/teams/opp_shots_without_{}_{}_{}_{}_vs_{}_pt_{}_hx_{}.{}'.format(fn, ln, gd, team1_name, team2_name, plot_type, hex_size, output_type),
                      'Opponent shots without {} {} on {} - {} vs {}'.format(fn, ln, gd, team1_name, team2_name),
                      plot_type=plot_type, hex_size=hex_size, **kwargs)

def cumul_opp_shot_chart_with_player (player_id, plot_type='hexbin', hex_size=1, start_date=dt.date(2012, 10, 27), **kwargs):

    games_played = games_played_pbp(player_id)
    fn, ln = look_up_player_name(player_id)

    print 'Generating cumulative opponent shot chart for {} {} on'.format(fn, ln)

    cumul_made_shots_coords = []
    cumul_missed_shots_coords = []

    for game in games_played:
        game_id = int(game['playbyplay']['contest']['id'])
        made_shots_coords, missed_shots_coords = opp_shot_chart_with_player(game_id, player_id, return_data=True)
        cumul_made_shots_coords = pylab.concatenate((cumul_made_shots_coords, made_shots_coords))
        cumul_missed_shots_coords = pylab.concatenate((cumul_missed_shots_coords, missed_shots_coords))

    if 'return_data' in kwargs:
        if kwargs['return_data'] == True:
            return cumul_made_shots_coords, cumul_missed_shots_coords

    if 'output_type' in kwargs:
        output_type = kwargs['output_type']
    else:
        output_type = 'pdf'

    create_shot_chart(cumul_made_shots_coords, cumul_missed_shots_coords,
                      'plots/teams/cumul_opp_shots_with_{}_{}_pt_{}_hx_{}.{}'.format(fn, ln, plot_type, hex_size, output_type),
                      'Cumulative opponent shots with {} {}'.format(fn, ln),
                      plot_type=plot_type, hex_size=hex_size, **kwargs)


def cumul_opp_shot_chart_without_player (player_id, plot_type='hexbin', hex_size=1, **kwargs):

    games_played = games_played_pbp(player_id)
    fn, ln = look_up_player_name(player_id)

    print 'Generating cumulative opponent shot chart for {} {} off'.format(fn, ln)

    cumul_made_shots_coords = []
    cumul_missed_shots_coords = []

    for game in games_played:
        game_id = int(game['playbyplay']['contest']['id'])
        made_shots_coords, missed_shots_coords = opp_shot_chart_without_player(game_id, player_id, return_data=True)
        cumul_made_shots_coords = pylab.concatenate((cumul_made_shots_coords, made_shots_coords))
        cumul_missed_shots_coords = pylab.concatenate((cumul_missed_shots_coords, missed_shots_coords))

    if 'return_data' in kwargs:
        if kwargs['return_data'] == True:
            return cumul_made_shots_coords, cumul_missed_shots_coords

    if 'output_type' in kwargs:
        output_type = kwargs['output_type']
    else:
        output_type = 'pdf'

    create_shot_chart(cumul_made_shots_coords, cumul_missed_shots_coords,
                      'plots/teams/cumul_opp_shots_without_{}_{}_pt_{}_hx_{}.{}'.format(fn, ln, plot_type, hex_size, output_type),
                      'Cumulative opponent shots without {} {}'.format(fn, ln),
                      plot_type=plot_type, hex_size=hex_size, **kwargs)
