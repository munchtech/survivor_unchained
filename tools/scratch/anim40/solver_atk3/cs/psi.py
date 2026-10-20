import math as _m
_orig_left = _left_on_haft
def _left_on_haft():
    R, o = _orig_left()
    C, H, N, Wd = _haft()
    ax = H / np.linalg.norm(H); t = _m.radians(PSI)
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    Q = np.eye(3) + _m.sin(t) * K + (1 - _m.cos(t)) * K @ K
    return Q @ R, C + Q @ (o - C)
