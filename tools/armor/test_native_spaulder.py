"""The "spaulder" recipe on a plain two-armed body (no game files): the cop's dome, rides derived from the body, the
laps, the tip flare, the arming cap under the plates, the two sides as mirrors, the play tier; gear_native's "carry":
"part"; and the built pieces' budgets."""
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
EDGES, LAP = [-0.066, 0.036, 0.076, 0.116, 0.154], [0, 0.016, 0.014, 0.014]
CFG = {"recipe": "spaulder", "piece": {"name": "t", "slot": "pauldrons"},
       "frame": {"from": "upperarm_*", "to": "lowerarm_*"}, "theta": [20, 175], "clear": 0.004, "thick": 0.004,
       "roll": [0.006, 0.0018], "lip": 0.003, "ease": 1.5, "grid": [0.004, 4.0], "step": 0.012, "step_s": 0.009,
       "materials": {"plate": "steel", "rim": "steel", "arming": "leather"},
       "cop": {"apex": 0.016, "rim": 0.0015, "shape": [2.4, 2.4], "roll": [0.008, 0.0024]},
       "lames": {"edges": EDGES, "theta": [35, 165], "arc": 0.010, "overlap": LAP, "gap": 0.002, "margin": 0.002,
                 "last_flare": 0.004, "rides": "mean", "carry": "part"},
       "arming": {"clear": 0.0012, "thick": 0.0012, "roll": [0.004, 0.0008], "past": [0.006, 0.010, 6], "step": 0.012},
       "rivet": {"r": 0.003, "h": 0.0016, "in": 0.013},
       "tip_flare": {"lames": [0, 1], "from": 60, "to": 20, "rise": 0.006}}
N = len(EDGES) - 1


def arms(shift=0.0, r=0.055, n=72, m=72):
    """Two tubes, her upper arms in an A pose, exact mirrors; her skin's weights run trap -> upperarm_share ->
    upperarm_twist_02 down each (shift: the same weights moved along the arm, a body whose weights changed)."""
    c, a = np.array([0.19, 1.48, -0.03]), nb.U(np.array([0.62, -0.78, 0.0]))
    fr = nb.Frame(c, c + 0.25 * a)
    S, TH = np.meshgrid(np.linspace(-0.11, 0.20, m), np.linspace(0, 360, n, endpoint=False), indexing="ij")
    P = fr.pt(S, TH, r).reshape(-1, 3)
    T = nb.outward(P, nb.grid_tris(m, n, close=True), fr.radial(TH).reshape(-1, 3))
    s = S.reshape(-1) - shift
    trap, tw = np.clip((-0.03 - s) / 0.02, 0, 1), np.clip((s - 0.03) / 0.06, 0, 1)
    W = np.zeros((len(P), 8))
    W[:, 0], W[:, 1], W[:, 2] = trap, 1 - trap - tw, tw
    J = np.zeros((2 * len(P), 8), np.int64)
    J[:len(P), :3], J[len(P):, :3] = [1, 3, 5], [2, 4, 6]
    V = np.vstack([P, P * [-1, 1, 1]])
    joints = {"upperarm_l": c, "lowerarm_l": c + 0.25 * a, "upperarm_r": c * [-1, 1, 1], "lowerarm_r": (c + 0.25 * a) * [-1, 1, 1]}
    return nb.Ref(V, np.vstack([T, T[:, ::-1] + len(P)]), None, joints, NAMES, J, np.vstack([W, W]), {"close": "x", "play": "y"}, "test")


def grid(sh, ns=9, nt=27, x0=0.0, x1=1.0):
    """(S, TH) over a sheet, edge to edge (its edges are curves)."""
    X, TH = np.meshgrid(np.linspace(x0, x1, ns), np.linspace(sh.t0, sh.t1, nt), indexing="ij")
    return sh.top(TH) + X * (sh.bot(TH) - sh.top(TH)), TH


class Spaulder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.ref = arms()
        cls.lay = sp.layout(CFG, cls.ref)
        cls.laws = {sd: {"law": L["law"], "arm_law": L["arm_law"]} for sd, L in cls.lay.items()}   # (read once)
        cls.rep = sp.spaulder("t_spaulder", CFG, out=os.path.join(cls.tmp.name, "t_spaulder"), ref=cls.ref, laws=cls.laws)
        cls.dir = os.path.join(cls.tmp.name, "t_spaulder")
        cls.piece = json.load(open(os.path.join(cls.dir, "piece.json")))
        cls.parts = {p["name"]: p for p in gn.read_parts(os.path.join(cls.dir, "t_spaulder.glb"))}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_the_parts_are_a_cop_wide_lames_and_an_arming_cap(self):
        for sd in "lr":
            self.assertEqual(sp.part_names(N, sd), [f"cop_{sd}_rigid", f"lame1_{sd}_rigid", f"lame2_{sd}_rigid", f"lame3_{sd}_rigid"])
            want = set(sp.part_names(N, sd)) | {f"rim{k}_{sd}_rigid" for k in range(N)} | {sp.arming_name(sd)}
            self.assertEqual({n for n in self.parts if f"_{sd}_" in n}, want)
            self.assertEqual(self.parts[sp.arming_name(sd)]["material"], "leather")
        for k in range(1, N):      # wide lames: 35 mm or more exposed each
            self.assertGreaterEqual(EDGES[k + 1] - EDGES[k], 0.035)

    def test_the_cop_is_a_dome_standing_off_her(self):
        L = self.lay["l"]
        cop, base = L["sheets"][0], L["law"]
        S, TH = grid(cop, 21, 41)
        off = cop.law(S, TH) - base(S, TH)      # its own surface over her skin's law (the lap's rise aside)
        mid = off[10, 20]
        self.assertGreater(mid, 0.016)          # the crown: the apex and the rim's own stand-off
        self.assertLess(off[0, 12:].max(), 0.0016)       # its top edge (behind the front tip's flare): the rim alone
        # curved both ways: down the arm and round it the crown falls away from the middle on either side
        for line in (off[:, 20], off[10, 12:]):
            k = int(np.argmax(line))
            self.assertTrue(0 < k < len(line) - 1)
            self.assertTrue((np.diff(line[:k + 1]) >= -1e-9).all() and (np.diff(line[k:]) <= 1e-9).all())
        self.assertLess(off[10, -2], 0.4 * mid)
        self.assertLess(off[1, 20], 0.4 * mid)
        # her skin under its inner face: the rim clears her by `clear`, the crown stands 15 mm and more off her
        X = L["fr"].pt(S, TH, cop.inner(S, TH)).reshape(-1, 3)
        q, n, _ = self.ref.closest(X)
        c = ((X - q) * n).sum(1).reshape(S.shape)
        self.assertGreater(c.min(), 0.004 - 0.0004)
        self.assertGreater(c[10, 20], 0.015)
        self.assertEqual(cop.roll_on, "tb01")   # a rolled rim all round

    def test_rides_are_derived_from_the_body(self):
        rules = self.piece["parts"]
        for sd in "lr":
            names = sp.part_names(N, sd)
            for nm in names:
                self.assertEqual(rules[nm]["carry"], "part")
                self.assertAlmostEqual(sum(rules[nm]["bones"].values()), 1.0, places=3)
                self.assertTrue(all(b.endswith("_" + sd) for b in rules[nm]["bones"]), rules[nm])
            # down the arm: the cop on her trap and upperarm_share, the last lame on the twist bone
            self.assertGreater(rules[names[0]]["bones"][f"trap_{sd}"], 0.15)
            self.assertGreater(rules[names[0]]["bones"][f"upperarm_share_{sd}"], 0.5)
            self.assertGreater(rules[names[3]]["bones"][f"upperarm_twist_02_{sd}"], 0.9)
            tw = [rules[nm]["bones"].get(f"upperarm_twist_02_{sd}", 0.0) for nm in names]
            self.assertEqual(tw, sorted(tw))
            self.assertNotIn(sp.arming_name(sd), rules)      # (a bendy part: it follows her skin, no rule)
        # the same recipe on a body whose weights changed: other rides (never a table)
        ref2 = arms(shift=0.03)
        moved = sp.layout(CFG, ref2, laws=self.laws)      # (the same skin, other weights)
        for k in (0, 1):
            a = rules[sp.part_names(N, "l")[k]]["bones"]
            b = sp.mean_ride(ref2, moved["l"]["foot"][k])
            self.assertGreater(max(abs(a.get(n, 0.0) - b.get(n, 0.0)) for n in set(a) | set(b)), 0.1, (k, a, b))
        # the cop's ride may read a band of its footprint alone
        band = sp.layout({**CFG, "cop": {**CFG["cop"], "ride_band": [-0.02, 0.02]}}, self.ref, laws=self.laws)
        self.assertGreater(sp.mean_ride(self.ref, band["l"]["foot"][0])["upperarm_share_l"], 0.95)

    def test_ride_is_the_area_weighted_mean_of_the_footprint(self):
        ref, L = self.ref, self.lay["l"]
        vs = L["foot"][2]
        s, th, _ = L["fr"].cyl(ref.V[vs])
        self.assertTrue((s >= 0.076 - 0.006 - 1e-9).all() and (s <= 0.116 + 1e-9).all() and (th >= 35).all() and (th <= 165).all())
        A = sp.vertex_area(ref.V, ref.T)[vs]
        want = {n: 0.0 for n in NAMES}
        for j, w in zip(ref.J[vs].T, ref.W[vs].T):
            for jj, ww, aa in zip(j, w, A):
                want[NAMES[jj]] += ww * aa
        tot = sum(want.values())
        got = sp.mean_ride(ref, vs)
        for n, v in got.items():
            self.assertAlmostEqual(v, want[n] / tot, places=3)

    def test_rims_ride_their_plate_and_every_rigid_part_has_a_rule(self):
        for sd in "lr":
            for k in range(N):
                lame = sp.part_names(N, sd)[k]
                self.assertEqual(self.piece["parts"][f"rim{k}_{sd}_rigid"], {"with": lame})
                self.assertEqual(gn.lead_part(self.piece, f"rim{k}_{sd}_rigid"), lame)
        self.assertTrue(all(gn.part_rule(self.piece, n) for n in self.parts if n.endswith("_rigid")))
        self.assertEqual(gn.validate(self.dir, rest_hash={"close": "x"}, materials={"steel", "leather"}), [])
        bad = json.loads(json.dumps(self.piece))
        bad["parts"]["lame2_l_rigid"]["carry"] = "sideways"
        d = os.path.join(self.tmp.name, "bad", "t_spaulder")
        os.makedirs(d)
        json.dump(bad, open(os.path.join(d, "piece.json"), "w"))
        with open(os.path.join(d, "t_spaulder.glb"), "wb") as f:
            f.write(open(os.path.join(self.dir, "t_spaulder.glb"), "rb").read())
        self.assertTrue(any("carry" in w for w in gn.validate(d, rest_hash={"close": "x"}, materials={"steel", "leather"})))

    def test_the_two_sides_are_mirrors(self):
        self.assertLess(self.rep["mirror_mm_max"], 0.5)
        for nm, p in self.parts.items():
            if "_l_" in nm:
                q = self.parts[nm.replace("_l_", "_r_")]
                self.assertLess(np.abs(p["P"] * [-1, 1, 1] - q["P"]).max(), 0.0005, nm)
                self.assertGreater(p["P"][:, 0].min(), 0)

    def test_seat_lifts_both_sides_as_one(self):
        # her left skin alone stands proud under a plate: both sides' points move, and stay mirrors
        ref = arms()
        fr = nb.Frame(ref.joints["upperarm_l"], ref.joints["lowerarm_l"])
        s, th, rho = fr.cyl(ref.V)
        ref.V = ref.V + (fr.radial(th) * (0.004 * ((np.abs(s - 0.1) < 0.02) & (np.abs(th - 90) < 25)))[:, None])
        built = {sd: nb.Part("p", "steel", fr.pt(np.array([0.1, 0.1, 0.1]), np.array([80.0, 90.0, 140.0]), 0.0585) * [h, 1, 1],
                             [[0, 1, 2]]) for sd, h in (("l", 1), ("r", -1))}
        self.assertEqual(sp.seat_sides(built, ref, 0.0012), 2)
        np.testing.assert_allclose(built["l"].P * [-1, 1, 1], built["r"].P, atol=1e-12)
        q, n, _ = ref.closest(built["l"].P)
        self.assertGreater(((built["l"].P - q) * n).sum(1).min(), 0.0012 - 2e-4)

    def test_upper_over_lower_with_room(self):
        L = self.lay["l"]
        sheets = L["sheets"]
        for k in range(N - 1):   # part k over lame k + 1, along the whole band it laps
            up, low = sheets[k], sheets[k + 1]
            X, TH = np.meshgrid(np.linspace(0, 1, 9), np.linspace(low.t0, low.t1, 27), indexing="ij")
            S = low.top(TH) + X * (up.bot(TH) - low.top(TH))
            room = up.inner(S, TH) - low.outer(S, TH)
            self.assertGreater(room.min(), 0.002 - 0.0005, k)
            if k:               # (the cop's crown stands higher still over lame 1's top band)
                self.assertLess(room.max(), 0.002 + 0.0015, k)
            np.testing.assert_allclose(up.bot(TH[0]) - low.top(TH[0]), LAP[k + 1], atol=1e-9)
            self.assertNotIn("t", low.roll_on)      # (a hidden edge takes no roll and no wall)
            self.assertIn("b", up.roll_on)
        # the lames' edges are curves: their two ends rise `arc` toward the shoulder; the last lame's edge flares
        low = sheets[-1]
        self.assertAlmostEqual(float(low.bot(np.array(100.0)) - low.bot(np.array(35.0))), 0.010, places=9)
        self.assertAlmostEqual(float(low.inner(low.bot(np.array(100.0)), np.array(100.0)) - low.law(low.bot(np.array(100.0)), np.array(100.0))), 0.004, places=6)

    def test_inner_faces_stand_clear_and_the_tips_flare(self):
        L = self.lay["l"]
        for k, sh in enumerate(L["sheets"]):
            S, TH = grid(sh, 7, 26)
            X = L["fr"].pt(S, TH, sh.inner(S, TH)).reshape(-1, 3)
            q, n, _ = self.ref.closest(X)
            c = ((X - q) * n).sum(1).reshape(S.shape)
            self.assertGreater(c.min(), 0.004 - 0.0004, k)
            s0 = np.array(float(sh.top(np.array(40.0))) + 0.001)
            rim = 0.0015 if k == 0 else 0.0
            tip = float(sh.law(s0, np.array(20.0)) - L["law"](s0, np.array(20.0)))
            self.assertAlmostEqual(tip, (0.006 if k in (0, 1) else 0.0) + rim, places=6)
            self.assertAlmostEqual(float(sh.law(s0, np.array(60.0)) - L["law"](s0, np.array(60.0))),
                                   rim + (float(sp.dome(L["top"][0], L["bot"][0], 20, 175, 0.016)(s0, np.array(60.0))) if k == 0 else 0.0), places=9)

    def test_the_arming_cap_lies_under_every_plate_and_beyond_their_outline(self):
        L = self.lay["l"]
        am = L["arming"]
        for sh in L["sheets"]:
            S, TH = grid(sh, 9, 27)
            self.assertGreater((sh.inner(S, TH) - am.outer(S, TH)).min(), 0.001)
        self.assertLess(am.t0, 20 - 5)
        self.assertGreater(am.t1, 175 + 5)
        th = np.linspace(35, 165, 9)
        self.assertTrue((am.top(th) < L["sheets"][0].top(th) - 0.005).all())
        self.assertTrue((am.bot(th) > L["sheets"][-1].bot(th) + 0.009).all())
        p = self.parts[sp.arming_name("l")]
        q, n, _ = self.ref.closest(p["P"])
        c = ((p["P"] - q) * n).sum(1)
        self.assertGreater(c.min(), 0.0004)      # never under her skin
        self.assertLess(c.max(), 0.0045)         # ... and a few mm off it
        none = sp.layout({k: v for k, v in CFG.items() if k != "arming"}, self.ref, laws=self.laws)
        self.assertIsNone(none["l"]["arming"])

    def test_tiers_and_parts(self):
        self.assertEqual(self.rep["tris"], sum(len(p["T"]) for p in self.parts.values()))
        lod = gn.read_parts(os.path.join(self.dir, "t_spaulder.lod1.glb"))
        self.assertEqual(self.rep["play_tris"], sum(len(p["T"]) for p in lod))
        self.assertLess(self.rep["play_tris"], 0.4 * self.rep["tris"])
        self.assertEqual({p["name"] for p in lod}, {n for sd in "lr" for n in sp.part_names(N, sd) + [sp.arming_name(sd)]})
        for nm, p in self.parts.items():       # a rim is the rolled edge alone; a plate holds no rolled edge
            flag = p["col"][:, 3]
            if nm.startswith("rim"):
                self.assertTrue((flag < 0.5).all(), nm)
            elif nm.startswith("lame3"):       # (no rivets on the last lame)
                self.assertTrue((flag[p["T"]] > 0.5).any(1).all(), nm)
        # the articulation rivets: two a lap a side, on the plate that laps (the cop, lames 1 and 2)
        for nm in ("cop_l_rigid", "lame1_l_rigid", "lame2_l_rigid"):
            p = self.parts[nm]
            self.assertEqual(int((np.abs(p["uv1"][:, 1] - 0.85) < 1e-3).sum()), 2 * 25, nm)


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
                for nm in sp.part_names(len(rep["sides"][sd]) - 2, sd):
                    self.assertEqual(piece["parts"][nm]["carry"], "part")
                    self.assertEqual(rep["sides"][sd][nm]["inside"], 0)
            parts = {p["name"]: p for p in gn.read_parts(os.path.join(d, pid + ".glb"))}
            for nm, p in parts.items():
                if "_l_" in nm:
                    self.assertLess(np.abs(p["P"] * [-1, 1, 1] - parts[nm.replace("_l_", "_r_")]["P"]).max(), 0.0005, nm)


if __name__ == "__main__":
    unittest.main()
