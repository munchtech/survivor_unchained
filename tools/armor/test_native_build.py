"""native_build's primitives on a plain cylinder body (no game files): frame, rays, the envelope law, sheets, fixings."""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import native_build as nb  # noqa: E402


def cylinder(r=0.08, y0=0.2, y1=1.0, n=48, m=40):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    y = np.linspace(y1, y0, m)
    P = np.array([[r * np.sin(t), yy, r * np.cos(t)] for yy in y for t in a])
    return nb.Ref(P, nb.outward(P, nb.grid_tris(m, n, close=True), P * [1, 0, 1]))


class Build(unittest.TestCase):
    def setUp(self):
        self.ref = cylinder()
        self.fr = nb.Frame([0, 0.95, 0], [0, 0.25, 0])

    def test_frame_round_trip_and_mirror(self):
        s, th, rho = np.array([0.1, 0.3]), np.array([-20.0, 100.0]), np.array([0.05, 0.09])
        np.testing.assert_allclose(self.fr.cyl(self.fr.pt(s, th, rho)), (s, th, rho), atol=1e-9)
        left, right = self.fr.pt(0.2, 90.0, 0.1), nb.Frame([0, 0.95, 0], [0, 0.25, 0], hand=-1).pt(0.2, 90.0, 0.1)
        self.assertGreater(left[0], 0)
        np.testing.assert_allclose(right, left * [-1, 1, 1], atol=1e-9)

    def test_grid_tris_are_quads_of_neighbours(self):
        T = nb.grid_tris(4, 5)
        self.assertEqual(len(T), 2 * 3 * 4)
        r, c = np.divmod(T, 5)
        self.assertTrue(((r.max(1) - r.min(1) == 1) & (c.max(1) - c.min(1) == 1)).all())

    def test_rays_and_envelope(self):
        S, TH = np.meshgrid(np.linspace(0.1, 0.5, 12), np.linspace(-40, 120, 14), indexing="ij")
        rho, _ = nb.radial(self.ref.V, self.ref.T, self.fr, S, TH)
        self.assertLess(np.abs(rho - 0.08).max(), 0.001)
        bump = rho + 0.004 * np.exp(-((S - 0.3) / 0.03) ** 2)
        law = nb.Law.envelope(S, TH, bump, deg=(6, 4))
        self.assertGreaterEqual((law(S, TH) - bump).min(), -1e-9)
        self.assertLess((law(S, TH) - bump).max(), 0.004)

    def test_sheet(self):
        law = nb.Law(0.0, 0.7, -60, 140, np.array([[0.083]]))
        sh = nb.Sheet(self.fr, law, -35, 115, lambda th: 0.1 + 0 * th, lambda th: 0.45 + 0 * th, 0.0025,
                      ridge={"theta": 0, "h": 0.002, "w": 0.016, "fade": 0.02})
        p = sh.build("plate_l_rigid", "steel")
        self.assertEqual(nb.seat(p, self.ref), 0)                       # nothing under the skin
        S, TH, idx = p.grid
        out = (p.N[idx.reshape(-1)] * self.fr.radial(TH.reshape(-1))).sum(1)
        self.assertGreater(out.min(), 0.3)                              # the outer face looks out
        self.assertAlmostEqual(float(sh.height(0.3, 0.0)), 0.0045, 6)   # thickness + the ridge on its crest
        self.assertAlmostEqual(float(sh.height(0.3, 60.0)), 0.0025, 6)
        edge = p.uv1[:, 0] <= 0.0045 + 2e-6
        self.assertTrue((p.col[edge, 3] == 0).all() and (p.col[~edge, 3] == 1).all())   # flag: 0 on the rolled edge
        self.assertLess(len(p.T), 8000)

    def test_strap_and_fixings(self):
        th = np.linspace(120, 320, 40)
        a, b = nb.skin_band(self.ref, self.fr.pt(np.full(40, 0.3), th, np.full(40, 0.08)), 0.018, 0.0018, "straps_l", "darkleather",
                            tab=th < 130)
        rho = self.fr.cyl(a.P)[2]
        self.assertTrue(rho.min() > 0.0795 and rho.max() < 0.0835)      # it lies on the skin
        self.assertTrue(b.name.endswith("_tab") and len(b.T) > 0)
        rv = nb.rivet(np.array([0, 0.5, 0.08]), np.array([0, 0, 1.0]))
        self.assertAlmostEqual(rv.P[:, 2].max(), 0.0812, 6)
        self.assertEqual(len(nb.buckle(np.array([0, 0.5, 0.08]), [0, 0, 1.0], [0, 1.0, 0]).T), 60)


if __name__ == "__main__":
    unittest.main()
