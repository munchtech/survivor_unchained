TWO_HANDS = True
L_ITER = 4
L_CLEAR = (0.10, 0.02, 0.08)
_fwd0 = _forward
def _forward(rig, clip, *a, **k):
    f = _fwd0(rig, clip, *a, **k)
    return lambda fr, pose: _left_clear(fr, f(fr, pose))
L_ITER = 5
HOLD_TO, FREE_AT = 11, 15
FWD = {3: (-0.02, 0.44, 0.64, 25.0, -8.0), 6: (-0.02, 0.42, 0.64, 25.0, -8.0), 9: (-0.02, 0.41, 0.63, 25.0, -8.0)}
