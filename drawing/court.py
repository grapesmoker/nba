__author__ = 'jerry'

from matplotlib.patches import Arc, RegularPolygon, Circle
from matplotlib.colors import Normalize, BoundaryNorm, ListedColormap
from matplotlib.colorbar import ColorbarBase
from matplotlib import gridspec

import matplotlib.pyplot as mpl

def draw_court(ax):

    ax.set_xlim(-25, 25)
    ax.set_ylim(0, 47)

    ax.vlines(-8, 0, 19)
    ax.vlines(8, 0, 19)

    ax.vlines(-6, 0, 19)
    ax.vlines(6, 0, 19)

    ax.hlines(19, -8, 8)

    ax.vlines(-22, 0, 14)
    ax.vlines(22, 0, 14)

    free_throw_circle = mpl.Circle((0, 19), radius=6, fill=False, color='k')
    ax.add_patch(free_throw_circle)

    ax.hlines(4, -3, 3)
    basket_circle = mpl.Circle((0, 5.25), 1.25, fill=False, color='k')
    ax.add_patch(basket_circle)

    ax.vlines(4, 4, 5.25)
    ax.vlines(-4, 4, 5.25)
    restricted_area = Arc((0, 5.25), 8, 8, theta1=0, theta2=180)
    ax.add_patch(restricted_area)

    three_point_arc = Arc((0, 5.25), 47.5, 47.5, theta1=22, theta2=158)
    ax.add_patch(three_point_arc)

    midcourt_circle = mpl.Circle((0, 47), radius=6, fill=False, color='k')
    jump_circle = mpl.Circle((0, 47), radius=2, fill=False, color='k')
    ax.add_patch(midcourt_circle)
    ax.add_patch(jump_circle)

    ax.set_aspect('equal')
