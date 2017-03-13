from __future__ import division

__author__ = 'jerry'

import numpy as np
import os
import matplotlib.pyplot as mpl

from scipy.spatial.distance import euclidean
from scipy.interpolate import spline

from matplotlib import gridspec
from matplotlib.patches import Arc, RegularPolygon, Circle
from matplotlib.colors import Normalize, BoundaryNorm, ListedColormap
from matplotlib.colorbar import ColorbarBase

from court import draw_court
from hexes import create_hexes, find_hex_from_xy
from utils.misc import is_shot_three

def plot_player_shots(player, games, plot_type='hexbin', hex_size=2):

    made_shots_coords = []
    missed_shots_coords = []

    for i, game in enumerate(games):

        shooting_plays = [event for event in game.events
                          if event.is_field_goal_made or event.is_field_goal_missed]

        made_shots = [play for play in shooting_plays if 'Made' in play['event-desc']]
        missed_shots = [play for play in shooting_plays if 'Missed' in play['event-desc']]

        made_shots_coords = np.concatenate((made_shots_coords,
                                                   [{'x': float(shot['x-coord']), 'y': float(shot['y-coord']) + 5.25}
                                                    for shot in made_shots]))

        missed_shots_coords = np.concatenate((missed_shots_coords,
                                                    [{'x': float(shot['x-coord']), 'y': float(shot['y-coord']) + 5.25}
                                                     for shot in missed_shots]))

    create_shot_chart(made_shots_coords, missed_shots_coords,
                      'plots/players/{0}_{1}_shots.pdf'.format(first_name, last_name),
                      '{0} {1}'.format(first_name, last_name), hex_size=hex_size)


def create_shot_chart(made_shots, missed_shots, filename, title, plot_type='hexbin', hex_size=2, **kwargs):

    made_x = np.array([shot.shot_x for shot in made_shots])
    made_y = np.array([shot.shot_y for shot in made_shots])
    missed_x = np.array([shot.shot_x for shot in missed_shots])
    missed_y = np.array([shot.shot_y for shot in missed_shots])

    num_made = float(len(made_shots))
    num_missed = float(len(missed_shots))

    frac_made = 100 * (num_made / (num_made + num_missed))
    frac_missed = 100 - frac_made

    shot_distances_made = [euclidean(shot.shot_x, shot.shot_y) for shot in made_shots]
    shot_distances_missed = [euclidean(shot.shot_x, shot.shot_y) for shot in missed_shots]

    bins = np.linspace(0, 50, 26)

    frac_made_arr = np.zeros(len(bins))
    shots_taken = np.zeros(len(bins))
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

        smooth_x = np.linspace(0, 40, 300)
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
        ax = mpl.subplot(gs[0,1])

        draw_court(ax)

        for x, y in zip(made_x, made_y):
            cell = find_hex_from_xy(hexes, x, y, s=hex_size)
            if cell is not None:
                if is_shot_three(x, y):
                    #print x, y, euclidean((x, y), (0, 0))
                    cell['threes'] += 1
                cell['made'] += 1
            else:
                ## this should never happen
                print 'made shot not in cell: ({}, {})'.format(x, y)

        for x, y in zip(missed_x, missed_y):
            cell = find_hex_from_xy(hexes, x, y, s=hex_size)
            if cell is not None:
                #if is_shot_three(x, y):
                #    print x, y, euclidean((x, y), (0, 0))
                cell['missed'] += 1
            else:
                ## this should never happen
                print 'missed shot not in cell: ({}, {})'.format(x, y)

        max_attempts = max([cell['made'] + cell['missed'] for cell in hexes])
        min_attempts = min([cell['made'] + cell['missed'] for cell in hexes if cell['made'] + cell['missed'] > 0])
        total_attempts = sum([cell['made'] + cell['missed'] for cell in hexes])

        max_attempts_frac = 100.0 * max_attempts / total_attempts
        min_attempts_frac = 100.0 * min_attempts / total_attempts

        #print 'max_attempts: {}, min_attempts: {}, total_attempts: {}'.format(max_attempts, min_attempts, total_attempts)
        #print 'max_attempts_frac: {}, min_attempts_frac: {}'.format(max_attempts_frac, min_attempts_frac)

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
            m = max_size / max_attempts_frac
            b = 0

        #print 'm: {}, b: {}, max_size: {}, min_size: {}'.format(m, b, max_size, min_size)

        cm = mpl.cm.YlOrBr
        norm = Normalize(0, 1.5)

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
                    cell['patch'] = RegularPolygon((cell['x'], cell['y']), 6, size, orientation=np.pi/6, color=cm(norm(efg)), alpha=0.75)
                    outline = RegularPolygon((cell['x'], cell['y']), 6, hex_size, orientation=np.pi/6, fill=False, color='y', linestyle='dotted')
                    ax.add_patch(cell['patch'])
                    ax.add_patch(outline)
                    if 'print_pct' in kwargs and kwargs['print_pct'] == True:
                        ax.text(cell['x'] - 1, cell['y'] - 1, '{0:2.2f}'.format(attempts_frac))

        if return_cells:
            return hexes

        if plot_type == 'hexbin':
            cb = ColorbarBase(ax_cb, cmap=cm, norm=norm, orientation='vertical')
            cb.set_label('Effective Field Goal Percentage')
            mpl.tight_layout()

        if plot_type == 'hexbin_contour':
            efg = []
            bin_x = [cell['x'] for cell in hexes]
            bin_y = [cell['y'] for cell in hexes]
            efg = [cell['efg'] for cell in hexes]

            xi = np.linspace(-25, 25, 200)
            yi = np.linspace(0, 47.5, 200)
            zi = np.griddata(bin_x, bin_y, efg, xi, yi)

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

    plot_dir = os.path.split(filename)
    if not os.path.exists(plot_dir[0]):
        os.makedirs(plot_dir[0])
    mpl.savefig(filename)
