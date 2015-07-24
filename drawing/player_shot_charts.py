__author__ = 'jerry'

def plot_player_shots(first_name, last_name, plot_type='hexbin', start_date=dt.date(2012, 11, 22), end_date = dt.date(2013, 4, 13), hex_size=2):

    player = players.find_one({'first-name': first_name, 'last-name': last_name})
    player_id = str(player['id'])

    games_played = pbp.find({'playbyplay.plays.play.player1-id': player_id})

    made_shots_coords = []
    missed_shots_coords = []

    for i, game in enumerate(games_played):
        gd = game_day(int(game['playbyplay']['contest']['id']), type='datetime')
        if gd > start_date and gd < end_date:
            plays = game['playbyplay']['plays']['play']
            player_plays = [play for play in plays if play['player1-id'] == player_id]
            shooting_plays = [play for play in player_plays
                              if 'Shot' in play['detail-desc']
                              and play['x-coord'] != ''
                              and play['y-coord'] != '']
            made_shots = [play for play in shooting_plays if 'Made' in play['event-desc']]
            missed_shots = [play for play in shooting_plays if 'Missed' in play['event-desc']]

            made_shots_coords = pylab.concatenate((made_shots_coords,
                                                   [{'x': float(shot['x-coord']), 'y': float(shot['y-coord']) + 5.25}
                                                    for shot in made_shots]))

            missed_shots_coords = pylab.concatenate((missed_shots_coords,
                                                    [{'x': float(shot['x-coord']), 'y': float(shot['y-coord']) + 5.25}
                                                     for shot in missed_shots]))

    create_shot_chart(made_shots_coords, missed_shots_coords,
                      'plots/players/{0}_{1}_shots.pdf'.format(first_name, last_name),
                      '{0} {1}'.format(first_name, last_name), hex_size=hex_size)



def player_shot_chart(game_id, player_id, **kwargs):

    game = None #GameEvent(pbp, game_id)

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

def create_shot_chart(made_shots_coords, missed_shots_coords, filename, title, plot_type='hexbin', hex_size=2, **kwargs):

    made_x = pylab.array([shot['x'] for shot in made_shots_coords])
    made_y = pylab.array([shot['y'] for shot in made_shots_coords])
    missed_x = pylab.array([shot['x'] for shot in missed_shots_coords])
    missed_y = pylab.array([shot['y'] for shot in missed_shots_coords])

    num_made = float(len(made_shots_coords))
    num_missed = float(len(missed_shots_coords))

    frac_made = 100 * (num_made / (num_made + num_missed))
    frac_missed = 100 - frac_made

    shot_distances_made = [euclidean(shot['x'], shot['y']) for shot in made_shots_coords]
    shot_distances_missed = [euclidean(shot['x'], shot['y']) for shot in missed_shots_coords]

    bins = pylab.linspace(0, 50, 26)

    frac_made_arr = pylab.zeros(len(bins))
    shots_taken = pylab.zeros(len(bins))
    for i, bin in enumerate(bins[:-1]):
        bin_made = [loc for loc in shot_distances_made if loc > bin and loc < bins[i + 1]]
        bin_missed = [loc for loc in shot_distances_missed if loc > bin and loc < bins[i + 1]]
        if len(bin_made) != 0 and len(bin_missed) != 0:
            frac_made_arr[i] = (float(len(bin_made)) / float(len(bin_made) + len(bin_missed)))
        shots_taken[i] = len(bin_made) + len(bin_missed)

    if plot_type == 'distance':
        mpl.clf()
        ax1 = mpl.subplot(111)
        # l1 = ax1.plot(bins, frac_made_arr * 100, 'go-', label='% made')
        ax2 = ax1.twinx()
        # l2 = ax2.plot(bins, shots_taken, 'rs-', label='shots taken')

        smooth_x = pylab.linspace(0, 40, 300)
        smooth_made = spline(bins, frac_made_arr * 100, smooth_x)
        smooth_taken = spline(bins, shots_taken, smooth_x)

        l1 = ax1.plot(smooth_x, smooth_made, 'g-', label='% made')
        l2 = ax2.plot(smooth_x, smooth_taken, 'r-', label='# shots taken')

        ax1.set_xlabel('Distance from basket')
        ax1.set_ylabel('Percentage made')
        ax2.set_ylabel('Number of shots taken')

        lns = l1 + l2
        labels = [l.get_label() for l in lns]

        ax1.set_xlim(0, 40)
        ax2.set_ylim(0, 40)

        mpl.title(title)
        mpl.legend(lns, labels)
        ax1.grid(True)

    if plot_type == 'hexbin' or plot_type == 'hexbin_contour':

        return_cells = False
        if 'return_cells' in kwargs:
            return_cells = kwargs['return_cells']

        hexes = create_hexes(hex_size)
        fig = mpl.figure()

        gs = gridspec.GridSpec(1, 2, width_ratios=[1, 10])

        ax_cb = mpl.subplot(gs[0,0])
        #ax_dist = mpl.subplot(gs[1, 0:])
        ax = mpl.subplot(gs[0,1])


        #ax_cb = mpl.subplot2grid((2, 1), (1, 0))
        #ax = mpl.subplot2grid((2, 1), (0, 0))

        #ax_cb = fig.add_axes([0.05, 0.05, 0.5, 0.025])
        #ax = fig.add_axes([0.1, 0.1, 0.9, 0.8])

        draw_court(ax)

        for x, y in zip(made_x, made_y):
            cell = find_hex_from_xy_improved(hexes, x, y, s=hex_size)
            if cell is not None:
                if is_shot_three(x, y):
                    cell['threes'] += 1
                cell['made'] += 1
            else:
                ## this should never happen
                print 'made shot not in cell: ({}, {})'.format(x, y)

        for x, y in zip(missed_x, missed_y):
            cell = find_hex_from_xy_improved(hexes, x, y, s=hex_size)
            if cell is not None:
                cell['missed'] += 1
            else:
                ## this should never happen
                print 'missed shot not in cell: ({}, {})'.format(x, y)

        max_attempts = max([cell['made'] + cell['missed'] for cell in hexes])
        min_attempts = min([cell['made'] + cell['missed'] for cell in hexes if cell['made'] + cell['missed'] > 0])
        total_attempts = sum([cell['made'] + cell['missed'] for cell in hexes])

        max_attempts_frac = 100.0 * max_attempts / total_attempts
        min_attempts_frac = 100.0 * min_attempts / total_attempts

        print max_attempts_frac, min_attempts_frac

        if 'scale_factor' in kwargs:
            max_attempts_frac = max_attempts_frac * kwargs['scale_factor']
        else:
            # default scale factor
            # max_attempts_frac = min_attempts_frac * 64
            pass

        max_size = hex_size
        min_size = hex_size / 8.0

        if max_attempts > 1:
            m = (float(max_size) - min_size) / (max_attempts_frac - 1)
            b = min_size - m
        else:
            m = max_size
            b = 0

        #print m, b, max_size, max_attempts_frac

        cm = mpl.cm.YlOrBr
        norm = Normalize(0, 1.5)
        #color_scale = pylab.linspace(0, 1.5, 25) / 1.5
        #colors = cm(color_scale)
        #cmap = ListedColormap(colors)

        #total_attempts = 0
        total_made = 0
        total_threes = 0
        for cell in hexes:
            attempts = cell['made'] + cell['missed']
            #total_attempts += attempts
            if attempts > 0:
                attempts_frac = 100.0 * attempts / total_attempts
                total_made += cell['made']
                total_threes += cell['threes']
                efg = (cell['made'] + 0.5 * cell['threes']) / attempts
                cell['efg'] = efg
                scaled_attempts = min(attempts_frac, max_attempts_frac)
                size = scaled_attempts * m + b
                #print size, scaled_attempts, attempts_frac, max_attempts_frac
                #print size
                if plot_type == 'hexbin' and not return_cells:
                    cell['patch'] = RegularPolygon((cell['x'], cell['y']), 6, size, orientation=pylab.pi/6, color=cm(norm(efg)), alpha=0.75)
                    outline = RegularPolygon((cell['x'], cell['y']), 6, hex_size, orientation=pylab.pi/6, fill=False, color='y', linestyle='dotted')
                    ax.add_patch(cell['patch'])
                    ax.add_patch(outline)
                    if 'print_pct' in kwargs and kwargs['print_pct'] == True:
                        ax.text(cell['x'] - 1, cell['y'] - 1, '{0:2.2f}'.format(attempts_frac))

        if return_cells:
            return hexes

        box = ax.get_position()

        # smooth_x = pylab.linspace(0, 40, 300)
        # smooth_made = spline(bins, frac_made_arr * 100, smooth_x)
        # smooth_taken = spline(bins, shots_taken, smooth_x)

        # l1 = ax_dist.plot(smooth_x, smooth_made, 'g-', label='% made')
        # l2 = ax_dist.plot(smooth_x, smooth_taken, 'r-', label='# shots taken')

        # ax_dist2 = ax_dist.twinx()
        # ax_dist.set_xlabel('Distance from basket')
        # ax_dist.set_ylabel('Percentage made')
        # ax_dist2.set_ylabel('Number of shots taken')

        # lns = l1 + l2
        # labels = [l.get_label() for l in lns]

        # ax_dist.set_xlim(0, 40)
        # ax_dist2.set_ylim(0, 40)

        # ax_dist.legend(lns, labels)
        # ax_dist.grid(True)

        #gs.update(left=0.01, right=0.65, wspace=0.05)
        #ax.set_position([box.x0 - box.width * 0.1,
        #                 box.y0 + box.height * 0.1,
        #                 box.width * 0.75,
        #                 box.height * 0.9])
        #ax_cb.set_position([box.x0 - box.width * 0.1,
        #                    0.01,
        #                    box.width * 0.75,
        #                    0.05])
        #box = ax.get_position()

        if plot_type == 'hexbin':
            #efg_max = 1.0 #max([cell['efg'] for cell in hexes])
            #efg_min = 0
            #unique_efg = pylab.array(sorted(pylab.unique([cell['efg'] for cell in hexes])))

            #if efg_max > 1:
            #    color_scale = unique_efg / efg_max
            #else:
            #    color_scale = unique_efg

            #colors = cm(color_scale)
            #cmap = ListedColormap(colors)
            #norm = Normalize(vmin=efg_min, vmax=efg_max)
            #norm = BoundaryNorm(color_scale, cmap.N)

            cb = ColorbarBase(ax_cb, cmap=cm, norm=norm, orientation='vertical')
            #cb.ax.set_yticklabels(unique_efg)
            cb.set_label('Effective Field Goal Percentage')
            mpl.tight_layout()

        if plot_type == 'hexbin_contour':
            efg = []
            bin_x = [cell['x'] for cell in hexes]
            bin_y = [cell['y'] for cell in hexes]
            efg = [cell['efg'] for cell in hexes]

            xi = pylab.linspace(-25, 25, 200)
            yi = pylab.linspace(0, 47.5, 200)
            zi = pylab.griddata(bin_x, bin_y, efg, xi, yi)

            mpl.contourf(xi, yi, zi, 5, cmap=mpl.cm.YlOrBr)
            mpl.colorbar()

        if 'overplot_shots' in kwargs:
            if kwargs['overplot_shots'] == True:
                mpl.plot(made_x, made_y, 'go')
                mpl.plot(missed_x, missed_y, 'rs')

        ax.text(0.02, 0.96, 'Total attempts: {}'.format(total_attempts), transform=ax.transAxes)
        ax.text(0.02, 0.93, 'Total made: {}'.format(total_made), transform=ax.transAxes)
        ax.text(0.02, 0.90, 'Total threes made: {}'.format(total_threes), transform=ax.transAxes)
        ax.text(0.02, 0.87, 'Total twos made: {}'.format(total_made - total_threes), transform=ax.transAxes)
        if total_attempts > 0:
            efg = 100 * (total_made + 0.5 * total_threes) / total_attempts
        else:
            efg = 0
        ax.text(0.02, 0.84, 'eFG%: {0:2.2f}'.format(efg),
                    transform=ax.transAxes)

        ax.set_title(title, fontsize='small')

    if plot_type == 'xo':

        mpl.plot(made_x, made_y, 'go')
        mpl.plot(missed_x, missed_y, 'rd')

        mpl.title(title)

    if plot_type == '3d':

        from mpl_toolkits.mplot3d import Axes3D

        fig = mpl.figure()
        ax = fig.gca(projection='3d')
        surf = ax.plot_surface(X, Y, frac_counts, cmap=mpl.cm.coolwarm)

        mpl.show()

    mpl.savefig(filename)
