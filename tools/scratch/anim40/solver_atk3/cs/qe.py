TWO_HANDS = True
FWD = {3: (-0.06, 0.60, 0.62, 50.0, -8.0), 6: (-0.06, 0.60, 0.62, 50.0, -8.0), 9: (-0.06, 0.58, 0.62, 50.0, -8.0)}
FWD_BODY = {"clav_l": (10, 10), "clav_r": (10, 14), "spine": (0, -12, 0), "hips": (0, -12, 0)}
FWD_POLES = {"hand_r": (-1.0, -0.3, -0.3), "hand_l": (0.6, -0.6, 0.3)}
PSI = 0
import math as _m
_orig_left = _left_on_haft
def _left_on_haft():
    R, o = _orig_left()
    C, H, N, Wd = _haft()
    ax = H / np.linalg.norm(H); t = _m.radians(PSI)
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    Q = np.eye(3) + _m.sin(t) * K + (1 - _m.cos(t)) * K @ K
    return Q @ R, C + Q @ (o - C)
