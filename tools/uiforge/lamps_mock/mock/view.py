"""Projection: board units (y up) -> 1080 screen px."""
FIELD = (0, 84, 1920, 960)
FIELD_C = (960.0, 522.0)
STOPS = {'valley': 0.337, 'road': 0.80, 'lamp': 1.25}


class View:
    def __init__(self, center=(0.0, 0.0), scale=0.80, screen_c=FIELD_C, stop='road'):
        self.cx, self.cy = center
        self.s = scale
        self.sx, self.sy = screen_c
        self.stop = stop

    def __call__(self, x, y):
        return self.sx + (x - self.cx) * self.s, self.sy - (y - self.cy) * self.s

    def visible(self, x, y, pad=60):
        X, Y = self(x, y)
        return -pad < X < 1920 + pad and -pad < Y < 1080 + pad

# lamp diameters (px at 1080), brief §5: (w, h) for the link
SIZE_ROAD = dict(start=34, entry=24, ultimate=26, ultimateMod=12, flareLamp=16, blue=28, notable=20, rite=18, link=22,
                 hand=18, form=14, reflex=16, reflexUp=12, small=12, attribute=10, wick=22, turn=34)
SIZE_VALLEY = dict(start=14, blue=10, entry=9, ultimate=9, notable=7, link=7, rite=6)
FLARE_KINDS = ('ultimate', 'ultimateMod', 'flareLamp')


SHAPE_K = [1.0]          # Road-stop shapes scale with a continuous zoom (scale / 0.80); set by a frame, reset after


def lamp_d(kind, stop):
    if stop == 'valley':
        return SIZE_VALLEY.get(kind, 4)
    d = SIZE_ROAD[kind] * (SHAPE_K[0] if kind not in ('wick', 'turn') else 1.0)
    return d * 1.3 if stop == 'lamp' else d


def lamp_r_toward(kind, stop, dx, dy):
    """the lamp's rim radius toward a direction (roads stop 2 px short of it)"""
    d = lamp_d(kind, stop)
    if kind == 'link' and stop != 'valley':
        import math
        hw, hh = d / 2, d * 14 / 22 / 2
        n = math.hypot(dx, dy) or 1
        c, s = abs(dx) / n, abs(dy) / n
        # stadium support toward (c, s), close enough for the gap
        return min(hw, (hw - hh) * c + hh) if c > 1e-3 else hh
    return d / 2
