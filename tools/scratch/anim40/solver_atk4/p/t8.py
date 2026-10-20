TWO_HANDS = True
L_ITER = 4
L_CLEAR = (0.10, 0.02, 0.08)
_fwd0 = _forward
def _forward(rig, clip, *a, **k):
    f = _fwd0(rig, clip, *a, **k)
    return lambda fr, pose: _left_clear(fr, f(fr, pose))
FWD = {3: (-0.04, 0.44, 0.64, 25.0, -16.0), 6: (-0.04, 0.42, 0.64, 25.0, -16.0), 9: (-0.04, 0.40, 0.62, 25.0, -16.0)}
