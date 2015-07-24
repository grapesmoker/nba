__author__ = 'jerry'

from matplotlib.patches import Arc, RegularPolygon, Circle
from matplotlib.colors import Normalize, BoundaryNorm, ListedColormap
from matplotlib.colorbar import ColorbarBase
from matplotlib import gridspec

def create_hexes(s=2):

    # overkill, only creates the coordinates of the hexes
    xf = range(-30, 30)
    yf = range(-30, 30)

    r = s * pylab.sqrt(3) / 2.0
    h = 0.5 * s

    grid_points = [(x, y) for x in xf for y in yf]

    hexes = []

    for n, coord in enumerate(grid_points):
        cx = 3 * coord[1] * h
        cy = (coord[1] + 2 * coord[0]) * r
        hexes.append({'id': n, 'x': cx, 'y': cy, 'patch': None, 'made': 0, 'missed': 0, 'threes': 0, 'efg': 0})

    return hexes

def find_hex_from_xy(hexes, x, y, r=1.732):

    # not a good way of doing things
    # if you are within a distance r of the center, you're good
    nearest_dist = 10
    nearest_cell = None

    for cell in hexes:
        dist = euclidean((x, y), (cell['x'], cell['y']))
        if dist < r:
            return cell
        else:
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_cell = cell

    return nearest_cell

def find_hex_from_xy_improved(hexes, x, y, s=2):

    r = s * pylab.sqrt(3) / 2.0

    candidates = [cell for cell in hexes if abs(cell['x'] - x) < s and abs(cell['y'] - y) < s]

    nearest_dist = 10
    nearest_cell = None

    for cell in candidates:
        dist = euclidean((x, y), (cell['x'], cell['y']))
        if dist < r:
            return cell
        else:
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_cell = cell

    return nearest_cell
