"""The "spaulder" recipe on a plain two-armed body (no game files): rides derived from the body, the laps, the tip flare,
the two sides as mirrors, the play tier; gear_native's "carry": "part"; and the built pieces' budgets."""
import json
import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gear_native as gn        # noqa: E402
import native_build as nb       # noqa: E402
import native_spaulder as sp    # noqa: E402

NAMES = ["spine_04", "trap_l", "trap_r", "upperarm_share_l", "upperarm_share_r", "upperarm_twist_02_l", "upperarm_twist_02_r"]
CFG = {"recipe": "spaulder", "piece": {"name": "t", "slot": "pauldrons"},
       "frame": {"from": "upperarm_*", "to": "lowerarm_*"}, "theta": [45, 170], "clear": 0.003, "thick": 0.0025,
       "roll": [0.0045, 0.001], "lip": 0.0012, "step": 0.012, "step_s": 0.008,
       "lames": {"edges": [-0.044, -0.024, -0.004, 0.016, 0.036, 0.054, 0.072, 0.090],
                 "overlap": [0, 0.012, 0.009, 0.017, 0.017, 0.011, 0.011], "gap": 0.003, "rides": "mean", "carry": "part"},
       "tip_flare": {"lames": [1, 2, 3, 4], "from": 70, "to": 45, "rise": 0.007}}


def arms(shift=0.0, r=0.055, n=72, m=56):
    """Two tubes, her upper arms in an A pose, exact mirrors; her skin's weights run trap -> upperarm_share ->
    upperarm_twist_02 down each (shift: the same weights moved along the arm, a body whose weights changed)."""
    c, a = np.array([0.19, 1.48, -0.03]), nb.U(np.array([0.62, -0.78, 0.0]))
    fr = nb.Frame(c, c + 0.25 * a)
    S, TH = np.meshgrid(np.linspace(-0.09, 0.15, m), np.linspace(0, 360, n, endpoint=False), indexing="ij")
    P = fr.pt(S, TH, r).reshape(-1, 3)
    T = nb.outward(P, nb.grid_tris(m, n, close=True), fr.radial(TH).reshape(-1, 3))
    s = S.reshape(-1) - shift
    trap, tw = np.clip((-0.014 - s) / 0.006, 0, 1), np.clip((s - 0.03) / 0.03, 0, 1)
    W = np.zeros((len(P), 8))
    W[:, 0], W[:, 1], W[:, 2] = trap, 1 - trap - tw, tw
    J = np.zeros((2 * len(P), 8), np.int64)
    J[:len(P), :3], J[len(P):, :3] = [1, 3, 5], [2, 4, 6]
    V = np.vstack([P, P * [-1, 1, 1]])
    joints = {"upperarm_l": c, "lowerarm_l": c + 0.25 * a, "upperarm_r": c * [-1, 1, 1], "lowerarm_r": (c + 0.25 * a) * [-1, 1, 1]}
    return nb.Ref(V, np.vstack([T, T[:, ::-1] + len(P)]), None, joints, NAMES, J, np.vstack([W, W]), {"close": "x", "play": "y"}, "test")


class Spaulder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.ref = arms()
        cls.rep = sp.spaulder("t_spaulder", CFG, out=os.path.join(cls.tmp.name, "t_spaulder"), ref=cls.ref)
        cls.dir = os.path.join(cls.tmp.name, "t_spaulder")
        cls.piece = json.load(open(os.path.join(cls.dir, "piece.json")))
        cls.parts = {p["name"]: p for p in gn.read_parts(os.path.join(cls.dir, "t_spaulder.glb"))}
        cls.lay = sp.layout(CFG, cls.ref)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_rides_are_derived_from_the_body(self):
        rules = self.piece["parts"]
        for sd in "lr":
            names = sp.part_names(7, sd)
            for nm in names:
                self.assertEqual(rules[nm]["carry"], "part")
                self.assertAlmostEqual(sum(rules[nm]["bones"].values()), 1.0, places=3)
                self.assertTrue(all(b.endswith("_" + sd) for b in rules[nm]["bones"]), rules[nm])
            # down the arm: the collar on her trap, the middle on upperarm_share, the last on the twist bone
            self.assertGreater(rules[names[0]]["bones"][f"trap_{sd}"], 0.9)
            self.assertGreater(rules[names[2]]["bones"][f"upperarm_share_{sd}"], 0.9)
            self.assertGreater(rules[names[6]]["bones"][f"upperarm_twist_02_{sd}"], 0.9)
            tw = [rules[nm]["bones"].get(f"upperarm_twist_02_{sd}", 0.0) for nm in names]
            self.assertEqual(tw, sorted(tw))
        # the same recipe on a body whose weights changed: other rides (never a table)
        moved = sp.layout(CFG, arms(shift=0.03))
        ref2 = arms(shift=0.03)
        for k in (1, 3, 4, 5):
            a = rules[f"lame{k}_l_rigid"]["bones"]
            b = sp.mean_ride(ref2, moved["l"]["foot"][k])
            self.assertGreater(max(abs(a.get(n, 0.0) - b.get(n, 0.0)) for n in set(a) | set(b)), 0.1, (k, a, b))

    def test_ride_is_the_area_weighted_mean_of_the_footprint(self):
        ref, L = self.ref, self.lay["l"]
        vs = L["foot"][4]
        s, th, _ = L["fr"].cyl(ref.V[vs])
        self.assertTrue((s >= 0.036 - 0.006 - 1e-9).all() and (s <= 0.054 + 1e-9).all() and (th >= 45).all() and (th <= 170).all())
        A = sp.vertex_area(ref.V, ref.T)[vs]
        want = {n: 0.0 for n in NAMES}
        for j, w in zip(ref.J[vs].T, ref.W[vs].T):
            for jj, ww, aa in zip(j, w, A):
                want[NAMES[jj]] += ww * aa
        tot = sum(want.values())
        got = sp.mean_ride(ref, vs)
        for n, v in got.items():
            self.assertAlmostEqual(v, want[n] / tot, places=3)

    def test_rims_ride_their_lame_and_every_rigid_part_has_a_rule(self):
        for sd in "lr":
            for k in range(7):
                lame = sp.part_names(7, sd)[k]
                self.assertEqual(self.piece["parts"][f"rim{k}_{sd}_rigid"], {"with": lame})
                self.assertEqual(gn.lead_part(self.piece, f"rim{k}_{sd}_rigid"), lame)
        self.assertTrue(all(gn.part_rule(self.piece, n) for n in self.parts))
        self.assertEqual(gn.validate(self.dir, rest_hash={"close": "x"}, materials={"steel"}), [])
        bad = json.loads(json.dumps(self.piece))
        bad["parts"]["lame2_l_rigid"]["carry"] = "sideways"
        d = os.path.join(self.tmp.name, "bad", "t_spaulder")
        os.makedirs(d)
        json.dump(bad, open(os.path.join(d, "piece.json"), "w"))
        with open(os.path.join(d, "t_spaulder.glb"), "wb") as f:
            f.write(open(os.path.join(self.dir, "t_spaulder.glb"), "rb").read())
        self.assertTrue(any("carry" in w for w in gn.validate(d, rest_hash={"close": "x"}, materials={"steel"})))

    def test_the_two_sides_are_mirrors(self):
        self.assertLess(self.rep["mirror_mm_max"], 0.5)
        for nm, p in self.parts.items():
            if "_l_" in nm:
                q = self.parts[nm.replace("_l_", "_r_")]
                self.assertLess(np.abs(p["P"] * [-1, 1, 1] - q["P"]).max(), 0.0005, nm)
                self.assertGreater(p["P"][:, 0].min(), 0)

    def test_upper_over_lower_with_room(self):
        L = self.lay["l"]
        sheets, th = L["sheets"], np.linspace(45, 170, 26)
        for k in range(1, 6):   # lame k over lame k + 1, along the whole band it laps
            up, low = sheets[k], sheets[k + 1]
            s = np.linspace(L["spans"][k + 1][0], L["spans"][k][1], 9)
            S, TH = np.meshgrid(s, th, indexing="ij")
            room = up.inner(S, TH) - low.outer(S, TH)
            self.assertGreater(room.min(), 0.003 - 0.0005, k)
            self.assertLess(room.max(), 0.003 + 0.0015, k)
            self.assertAlmostEqual(L["spans"][k][1] - L["spans"][k + 1][0], CFG["lames"]["overlap"][k + 1], places=9)
            self.assertNotIn("t", low.roll_on)      # (a hidden edge takes no roll and no wall)
            self.assertIn("b", up.roll_on)
        s = np.linspace(L["spans"][1][0], L["spans"][0][1], 7)   # the collar seam: lame 1 over the collar
        S, TH = np.meshgrid(s, th, indexing="ij")
        self.assertGreater((sheets[1].inner(S, TH) - sheets[0].outer(S, TH)).min(), 0.003 - 0.0005)
        self.assertEqual(sheets[0].roll_on, "t01")

    def test_inner_faces_stand_clear_and_the_tips_flare(self):
        L = self.lay["l"]
        for k, sh in enumerate(L["sheets"]):
            s = np.linspace(*L["spans"][k], 7)
            S, TH = np.meshgrid(s, np.linspace(45, 170, 26), indexing="ij")
            X = L["fr"].pt(S, TH, sh.inner(S, TH)).reshape(-1, 3)
            q, n, _ = self.ref.closest(X)
            c = ((X - q) * n).sum(1).reshape(S.shape)
            self.assertGreater(c.min(), 0.003 - 0.0004, k)
            if k in (0, 6):     # nothing under them, no flare: `clear` off her everywhere
                self.assertLess(c.max(), 0.003 + 0.0006, k)
            tip = float(sh.law(np.array(s[0]), np.array(45.0)) - L["law"](np.array(s[0]), np.array(45.0)))
            self.assertAlmostEqual(tip, 0.007 if k in (1, 2, 3, 4) else 0.0, places=6)
            self.assertAlmostEqual(float(sh.law(np.array(s[0]), np.array(70.0)) - L["law"](np.array(s[0]), np.array(70.0))), 0.0, places=9)

    def test_tiers_and_parts(self):
        self.assertEqual(self.rep["tris"], sum(len(p["T"]) for p in self.parts.values()))
        lod = gn.read_parts(os.path.join(self.dir, "t_spaulder.lod1.glb"))
        self.assertEqual(self.rep["play_tris"], sum(len(p["T"]) for p in lod))
        self.assertLess(self.rep["play_tris"], 0.3 * self.rep["tris"])
        self.assertEqual({p["name"] for p in lod}, {n for sd in "lr" for n in sp.part_names(7, sd)})
        for nm, p in self.parts.items():       # a rim is the rolled edge alone; a lame holds no rolled edge
            flag = p["col"][:, 3]
            if nm.startswith("rim"):
                self.assertTrue((flag < 0.5).all(), nm)
            elif nm.startswith(("collar", "lame6")):     # (no rivets on these two)
                self.assertTrue((flag[p["T"]] > 0.5).any(1).all(), nm)


class Carry(unittest.TestCase):
    def test_carry_part_is_one_rigid_motion_of_the_whole_part(self):
        ang = np.radians(20.0)
        R = np.array([[np.cos(ang), -np.sin(ang), 0], [np.sin(ang), np.cos(ang), 0], [0, 0, 1.0]])
        t = np.array([0.004, -0.012, 0.02])
        rng = np.random.default_rng(3)

        class Body:
            joint_names = ["spine_04", "upperarm_share_l", "upperarm_share_r", "trap_l", "trap_r"]
            V = np.array([[0.2, 1.4, 0.0], [0.24, 1.4, 0.0], [0.2, 1.44, 0.01], [0.24, 1.45, 0.02], [0.28, 1.42, 0.03], [0.5, 1.0, 0.0]])
            T = np.array([[0, 1, 2], [1, 3, 2], [1, 4, 3], [0, 2, 5]])
            J = np.tile(np.arange(5), (6, 1))
            W = np.tile([0.1, 0.6, 0.0, 0.3, 0.0], (6, 1))
        Body.shapes = {"arm_hang_a_l": Body.V @ R.T + t - Body.V, "elbow_flex90_l": np.tile([0.0, 0.003, 0.0], (6, 1)),
                       "knee_flex90_l": np.tile([0.0, 0.0, 0.01], (6, 1)), "arm_hang_b_l": np.zeros((6, 3))}
        Body.shapes["arm_hang_a_l"][5] = [0.3, 0.3, 0.3]     # (her skin elsewhere: not under the part, never read)

        # points 0-3: the lame (on triangles 0-2), 4-5: its rim, 6: a part with a role rule, 7: a bendy point
        class Bind:
            z = {"lead_close": np.array([0, 0, 2]), "comp0": np.array([0, 0, 0, 0, 1, 1, 2, -1]),
                 "tri0": np.array([0, 1, 2, 2, 3, 3, 3, 3], np.int64), "bw0": np.full((8, 2), 21845, np.uint16)}
            meta = {"meshes": [{"tier": "close", "i": 0, "node": "n"}],
                    "parts": [{"rule": {"bones": {"upperarm_share_{s}": 0.75, "trap_{s}": 0.25}, "carry": "part"}, "comp": 0},
                              {"rule": {"ride": {"upperarm": 1}, "one_bone": True}, "comp": 2}]}
        X = rng.normal(size=(8, 3)) * 0.02 + [0.22, 1.45, 0.02]
        junk = rng.normal(size=(8, 3))
        ev = {"n": {"inv": np.arange(8), "Xu": X, "J": np.zeros((8, 8), np.uint16), "W": np.zeros((8, 8), np.float32),
                    "shapes": {"arm_hang_a_l": junk.copy(), "knee_flex90_l": junk.copy()}}}
        gn.part_blends(Bind, {"close": Body}, ev)
        e = ev["n"]
        # the lame and its rim: her arm shape as the rigid motion of her skin under the lame, exactly, on every point
        np.testing.assert_allclose(e["shapes"]["arm_hang_a_l"][:6], X[:6] @ R.T + t - X[:6], atol=1e-9)
        Rf, tf = gn.rigid_fit(X[:6], X[:6] + e["shapes"]["arm_hang_a_l"][:6])
        np.testing.assert_allclose(X[:6] @ Rf.T + tf, X[:6] + e["shapes"]["arm_hang_a_l"][:6], atol=1e-9)
        # a shape the build had not given the mesh is added; one that is not her arm's is not carried
        np.testing.assert_allclose(e["shapes"]["elbow_flex90_l"][:6], np.tile([0.0, 0.003, 0.0], (6, 1)), atol=1e-9)
        np.testing.assert_array_equal(e["shapes"]["elbow_flex90_l"][6:], 0.0)
        np.testing.assert_array_equal(e["shapes"]["knee_flex90_l"][:6], 0.0)
        self.assertNotIn("arm_hang_b_l", e["shapes"])
        # the other parts keep what the build gave them
        np.testing.assert_array_equal(e["shapes"]["arm_hang_a_l"][6:], junk[6:])
        np.testing.assert_array_equal(e["shapes"]["knee_flex90_l"][6:], junk[6:])
        got = {Body.joint_names[j]: round(float(w), 4) for j, w in zip(e["J"][4], e["W"][4]) if w > 0}
        self.assertEqual(got, {"upperarm_share_l": 0.75, "trap_l": 0.25})

    def test_carry_none_is_what_named_bones_did(self):
        class Body:
            joint_names = ["spine_04", "upperarm_share_l", "upperarm_share_r"]
            T = np.array([[0, 1, 2]])
            J = np.tile(np.arange(3), (3, 1))
            W = np.tile([0.2, 0.8, 0.0], (3, 1))

        for rule in ({"bones": {"upperarm_share_{s}": 1}}, {"bones": {"upperarm_share_{s}": 1}, "carry": "none"}):
            class Bind:
                z = {"lead_close": np.array([0]), "comp0": np.array([0, 0, -1]), "tri0": np.zeros(3, np.int64),
                     "bw0": np.full((3, 2), 21845, np.uint16)}
                meta = {"meshes": [{"tier": "close", "i": 0, "node": "n"}], "parts": [{"rule": rule, "comp": 0}]}
            d = np.tile([0.0, 0.01, 0.0], (3, 1))
            ev = {"n": {"inv": np.arange(3), "J": np.zeros((3, 8), np.uint16), "W": np.zeros((3, 8), np.float32),
                        "shapes": {"arm_hang_a_l": d.copy()}}}
            gn.part_blends(Bind, {"close": Body}, ev)     # (no body shapes, no points read: nothing is carried)
            np.testing.assert_array_equal(ev["n"]["shapes"]["arm_hang_a_l"][:2], 0.0)
            np.testing.assert_array_equal(ev["n"]["shapes"]["arm_hang_a_l"][2:], d[2:])


class Built(unittest.TestCase):
    """The two piece dirs as built on her (skipped where a checkout has none)."""

    def test_budgets_mirror_and_rules(self):
        for pid in ("plate_spaulders_plain", "plate_spaulders_warden"):
            d = os.path.join(nb.NATIVE, pid)
            if not os.path.exists(os.path.join(d, "build_report.json")):
                self.skipTest(f"{pid} is not built here")
            rep = json.load(open(os.path.join(d, "build_report.json")))
            piece = json.load(open(os.path.join(d, "piece.json")))
            self.assertLessEqual(rep["tris"], 16000, pid)
            self.assertLessEqual(rep["play_tris"], 4000, pid)
            self.assertLess(rep["mirror_mm_max"], 0.5, pid)
            self.assertEqual(piece["slot"], "pauldrons")
            for sd in "lr":
                for nm in sp.part_names(7, sd):
                    self.assertEqual(piece["parts"][nm]["carry"], "part")
                    self.assertEqual(rep["sides"][sd][nm]["inside"], 0)
            parts = {p["name"]: p for p in gn.read_parts(os.path.join(d, pid + ".glb"))}
            for nm, p in parts.items():
                if "_l_" in nm:
                    self.assertLess(np.abs(p["P"] * [-1, 1, 1] - parts[nm.replace("_l_", "_r_")]["P"]).max(), 0.0005, nm)


if __name__ == "__main__":
    unittest.main()
