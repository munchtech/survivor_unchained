import numpy as np, math
def rotv(v, axis, deg):
    a = np.asarray(axis, float); a /= np.linalg.norm(a); t = math.radians(deg)
    return v * math.cos(t) + np.cross(a, v) * math.sin(t) + a * np.dot(a, v) * (1 - math.cos(t))
def arm(th, abd, el, rot, lu=0.253, lf=0.266):
    """Left arm, chest frame x out(left) y up z fwd. th: upper arm forward of hanging; abd: out; el: interior elbow angle;
    rot: humeral internal rotation (forearm swung toward the midline). Returns elbow, hand."""
    u = np.array([0.0, -1.0, 0.0])
    u = rotv(u, [1, 0, 0], -th)        # forward: rotate about x so -y goes to +z
    u = rotv(u, [0, 0, 1], abd)        # out (+x) about z
    h0 = rotv(rotv(np.array([1.0, 0, 0]), [1, 0, 0], -th), [0, 0, 1], abd)
    hinge = rotv(h0, u, rot)   # internal rotation turns the hinge about the upper arm
    # forearm: from the upper arm's extension, bent forward by (180-el) about the hinge
    f = rotv(u, hinge, -(180 - el))
    E = u * lu; H = E + f * lf
    return E, H
if __name__ == "__main__":
    L = 0.519
    for th, ab, el, want in ((3.3, 16.4, 67.1, (-0.39, -0.07, 0.39)), (-13.4, 17.5, 75.5, (-0.55, -0.03, 0.28))):
        for rot in range(-30, 61, 10):
            E, H = arm(th, ab, el, rot)
            print(th, rot, "H/L y%+.2f x%+.2f z%+.2f" % (H[1]/L, H[0]/L, H[2]/L), "want", want)
