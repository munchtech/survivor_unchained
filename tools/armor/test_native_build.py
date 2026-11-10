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


class Lames(unittest.TestCase):
    """An articulated lame: an edge through its measured points, its top lapping OVER the plate above it."""

    def sheet(self, **kw):
        fr = nb.Frame([0, 1.0, 0], [0, 0.5, 0])
        law = nb.Law(0.0, 0.5, -90, 90, np.array([[0.08]]))
        top, bot = (lambda th: 0.30 + 0 * np.asarray(th, float)), (lambda th: 0.35 + 0 * np.asarray(th, float))
        return nb.Sheet(fr, law, -30, 60, top, bot, 0.002, **kw), fr

    def test_edge_points(self):
        th, s = np.array([-35, 5, 45, 72, 115.0]), np.array([0.232, 0.180, 0.100, 0.079, 0.078])
        f = nb.edge_points(th, s)
        np.testing.assert_allclose(f(th), s, atol=1e-12)
        x = f(np.linspace(-35, 115, 400))
        self.assertTrue((np.diff(x) <= 1e-12).all())            # monotone data: no overshoot between the points
        np.testing.assert_allclose(f(np.array([-60.0, 140.0])), [0.232, 0.078])   # clamped outside

    def test_lapping_lame(self):
        lift = {"band": 0.014, "h": 0.003, "ease": 0.010}
        sh, fr = self.sheet(roll_on="t01", lift_top=lift)
        th = np.array([10.0])
        # the top band stands the lift further out, the bottom (hidden under the next lame) is plain steel: no bead
        self.assertAlmostEqual(float(sh.height(np.array([0.310]), th)[0]), 0.002 + 0.003, places=6)
        self.assertAlmostEqual(float(sh.height(np.array([0.3478]), th)[0]), 0.002, places=6)
        full, _ = self.sheet()
        self.assertGreater(float(full.height(np.array([0.3478]), th)[0]), 0.0025)   # (rolled on every edge: a bead)
        p = sh.build("lame_rigid", "steel")
        S, TH, idx = p.grid
        nr, nc = S.shape
        self.assertEqual(nr, 7 + (nr - 8) + 1)                  # rows cluster on the rolled top edge only
        wall = p.P[S.size:]
        s_w, th_w, rho = fr.cyl(wall)
        # the lifted edge's wall and lip stay over the plate beneath (they never run down to her skin through it)
        self.assertGreater(float(rho[(s_w < 0.305) & (th_w > -25) & (th_w < 55)].min()), 0.08 + 0.002)
        # the hidden bottom edge has no wall: nothing stands between her skin and the lame that laps over it
        self.assertEqual(int(((s_w > 0.345) & (th_w > -25) & (th_w < 55)).sum()), 0)
        full_p = full.build("lame_rigid", "steel")
        s_f, th_f, rho_f = fr.cyl(full_p.P[full_p.grid[0].size:])
        self.assertLess(float(rho_f[(s_f > 0.345) & (th_f > -25) & (th_f < 55)].min()), 0.08)   # a rolled edge: down to her
        used = np.zeros(len(p.P), bool)
        used[p.T] = True
        self.assertTrue(used.all())                             # no point without a face
        fn = np.cross(p.P[p.T[:, 1]] - p.P[p.T[:, 0]], p.P[p.T[:, 2]] - p.P[p.T[:, 0]])
        self.assertGreater(float(np.linalg.norm(fn, axis=1).min()), 1e-12)          # no degenerate faces

    def test_tapered_side(self):
        # a side edge as a line theta(s): the plate's side runs into the lames' below it, no step in the outline
        side = lambda s: -30 + 10 * nb.smooth((np.asarray(s, float) - 0.31) / 0.03)  # noqa: E731
        sh, fr = self.sheet()
        sh.t0 = side
        p = sh.build("plate_rigid", "steel")
        S, TH, idx = p.grid
        np.testing.assert_allclose(TH[:, 0], side(S[:, 0]), atol=1e-6)              # its first column IS the line
        self.assertAlmostEqual(float(TH[0, 0]), -30.0, places=5)
        self.assertAlmostEqual(float(TH[-1, 0]), -20.0, places=5)
        self.assertLess(float(sh.edge_d(np.array([0.345]), np.array([-25.0]))[0]), 0)   # outside the tapered side
        self.assertGreater(float(sh.edge_d(np.array([0.302]), np.array([-25.0]))[0]), 0)

    def test_bottom_dip(self):
        # the cuisses' knee lame runs lower under the cop at the front only (build.json bottom "dip", limb_plate): in
        # full across the front, eased to nothing before the outer side, never past its points, the edge smooth
        import json
        repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cfg = json.load(open(os.path.join(repo, "godot", "art", "gear", "native", "plate_cuisses_plain", "build.json"), encoding="utf-8"))
        pts = np.array(cfg["bottom"]["dip"]["points"], float)
        f = nb.edge_points(pts[:, 0], pts[:, 1])
        lt0, lt1 = cfg["lames"]["theta"]
        self.assertLessEqual(pts[0, 0], lt0)
        self.assertGreaterEqual(pts[-1, 0], lt1)
        th = np.linspace(lt0, lt1, 600)
        d = f(th)
        np.testing.assert_allclose(d[th <= 45], 0.020, atol=1e-12)
        np.testing.assert_allclose(d[th >= 72], 0.0, atol=1e-12)
        self.assertTrue((np.diff(d) <= 1e-12).all())
        self.assertLess(float(np.abs(np.diff(d)).max() / np.radians(th[1] - th[0]) / 0.06), 1.5)   # (slope of the edge on a 60 mm limb)


if __name__ == "__main__":
    unittest.main()
