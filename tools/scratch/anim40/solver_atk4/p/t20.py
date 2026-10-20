TWO_HANDS = True
L_ITER = 4
L_CLEAR = (0.10, 0.02, 0.08)
_fwd0 = _forward
def _forward(rig, clip, *a, **k):
    f = _fwd0(rig, clip, *a, **k)
    return lambda fr, pose: _left_clear(fr, f(fr, pose))
_sk0 = _strike_keys
def _strike_keys():
    ks = _sk0()
    out = []
    for t, p, e in ks:
        if t == 9:
            p = dict(p); p['hand_l'] = {**p['hand_l'], 'arc': arc_of(K9_L)}
        out.append((t, p, e))
    return out
K9_L = (0.30, -0.10, 0.16)
HOLD_TO, FREE_AT = 9, 13
FWD_OUT = 15
FWD = {3: (-0.07, 0.44, 0.64, 25.0, -9.0), 6: (-0.07, 0.41, 0.615, 21.0, -9.0), 9: (-0.07, 0.38, 0.585, 17.5, -9.0), 11: (-0.07, 0.39, 0.59, 18.5, -9.0)}
