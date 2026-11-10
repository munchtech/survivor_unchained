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
        # (its sides: past the cop's beside the cop, in to the lames' beside the lames: never a wide flap)
        self.assertLess(float(am.side(0, -0.03)), 20 - 5)
        self.assertGreater(float(am.side(1, -0.03)), 175 + 5)
        lt0, lt1 = L["theta"][1]
        self.assertTrue(lt0 - 8 < float(am.side(0, 0.1)) < lt0 - 4)
        self.assertTrue(lt1 + 4 < float(am.side(1, 0.1)) < lt1 + 8)
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
                    # ("mean" rides carry "part"; a rule naming its own bones carries what it says, l14 cop: "none")
                    self.assertIn(piece["parts"][nm]["carry"], ("part", "none"))
                    self.assertEqual(rep["sides"][sd][nm]["inside"], 0)
            parts = {p["name"]: p for p in gn.read_parts(os.path.join(d, pid + ".glb"))}
            for nm, p in parts.items():
                if "_l_" in nm:
                    self.assertLess(np.abs(p["P"] * [-1, 1, 1] - parts[nm.replace("_l_", "_r_")]["P"]).max(), 0.0005, nm)


class ShoulderTop(unittest.TestCase):
    """Round 2: the cop crowns the shoulder (a frame whose centres stay under her skin's crest line, an arched
    upper edge), and the arming cap's material is one the fit can paint."""

    def test_the_shoulder_frame_is_the_arms_own_from_the_lames_on_and_inverts(self):
        fr = nb.Frame([0.19, 1.48, -0.03], [0.35, 1.28, -0.04], hand=1)
        s = np.arange(-0.14, 0.0141, 0.002)
        r = np.where(s < -0.05, 0.035 + (s + 0.05), 0.035)          # (the crest line falls away past the joint)
        d = sp.crest_drop(s, r, 0.014)
        self.assertEqual(float(d[-1]), 0.0)
        self.assertTrue((d[s > -0.02] < 1e-4).all())
        self.assertGreater(float(np.interp(-0.09, s, d)), 0.03)
        sf = sp.ShoulderFrame(fr, s, d)
        S, TH, R = np.array([-0.09, -0.05, 0.0, 0.05]), np.array([30.0, 96.0, 150.0, 170.0]), np.array([0.03, 0.04, 0.05, 0.045])
        s2, th2, r2 = sf.cyl(sf.pt(S, TH, R))
        self.assertLess(max(np.abs(s2 - S).max(), np.abs(r2 - R).max(), np.radians(np.abs(th2 - TH)).max()), 1e-9)
        self.assertLess(np.abs(sf.pt(S[2:], TH[2:], R[2:]) - fr.pt(S[2:], TH[2:], R[2:])).max(), 1e-12)
        # (a centre keeps its depth under the crest: rho at theta 90 never under the depth, where the axis left her)
        self.assertGreater(float(np.interp(-0.09, s, r) + sf.drop(-0.09)), 0.03)

    def test_the_cops_upper_edge_is_an_arch_and_its_ride_reads_its_own_outline(self):
        cfg = json.loads(json.dumps(CFG))
        cfg["cop"] = dict(cfg.get("cop") or {}, arch={"span": 0.03, "power": 2.6})
        ref = arms()
        L = sp.layout(cfg, ref)["l"]
        t0, t1 = L["theta"][0]
        top, bot = L["top"][0], L["bot"][0]
        e0 = cfg["lames"]["edges"][0]
        self.assertAlmostEqual(float(top(0.5 * (t0 + t1))), e0, places=9)
        for te in (t0, t1):       # (its ends come down to `span` above its lower edge, or nearer)
            self.assertGreater(float(top(te)), e0 + 0.02)
            self.assertGreaterEqual(float(bot(te) - top(te)), 0.03 - 1e-9)
        th = np.linspace(t0, 0.5 * (t0 + t1), 9)
        self.assertTrue((np.diff(top(th)) < 0).all())
        s, tv, _ = L["fr"].cyl(ref.V[L["foot"][0]])
        self.assertTrue((s >= top(np.clip(tv, t0, t1)) - 1e-9).all())

    def test_a_wing_rounds_the_cops_lower_corner_and_curls_in_over_the_lames_end(self):
        cfg = json.loads(json.dumps(CFG))
        cfg["theta"] = [15, 168]          # (front: 20 degrees past the lames' end, a wing; back: 3, none)
        cfg["cop"] = dict(cfg["cop"], arch={"span": 0.03, "power": 2.2}, wing={"end": 0.008, "curl": 1.0})
        ref = arms()
        L = sp.layout(cfg, ref)["l"]
        plain = sp.layout({**cfg, "cop": {k: v for k, v in cfg["cop"].items() if k != "wing"}}, ref)["l"]
        cop, low, top, bot, pb = L["sheets"][0], L["sheets"][1], L["top"][0], L["bot"][0], plain["bot"][0]
        lt0 = float(cfg["lames"]["theta"][0])
        self.assertAlmostEqual(float(bot(15.0) - top(15.0)), 0.008, places=9)       # (its side edge is `end` long)
        th = np.linspace(lt0, 168, 9)
        self.assertLess(np.abs(bot(th) - pb(th)).max(), 1e-12)                       # (over the lames and at the back: as it was)
        self.assertTrue((np.diff(bot(np.linspace(15, lt0, 9))) > 0).all())
        tip = np.array(15.0)
        s = np.array(float(bot(15.0)) - 0.001)                                       # (curled in: on its own surface at its tip)
        self.assertLess(abs(float(cop.inner(s, tip) - cop.law(s, tip))), 1e-5)
        sp_ = np.array(float(pb(15.0)) - 0.001)
        self.assertGreater(float(plain["sheets"][0].inner(sp_, tip) - plain["sheets"][0].law(sp_, tip)), 0.002)
        s1, e = np.array(float(bot(lt0)) - 0.004), np.array(lt0)                     # (at the lame's end it still stands on it)
        self.assertGreaterEqual(float(cop.inner(s1, e) - low.outer(s1, e)), cfg["lames"]["gap"] - 1e-5)

    def test_lie_lays_the_cops_upper_edge_down_and_leaves_its_ends(self):
        cfg = json.loads(json.dumps(CFG))
        cfg["cop"] = dict(cfg["cop"], arch={"span": 0.03, "power": 2.2})
        ref = arms()
        plain = sp.layout(cfg, ref)["l"]["sheets"][0]
        lying = sp.layout({**cfg, "cop": dict(cfg["cop"], lie={"len": 0.04, "drop": 0.002})}, ref)["l"]["sheets"][0]
        mid, end = np.array(0.5 * (plain.t0 + plain.t1)), np.array(float(plain.t0))
        top = plain.top(mid)
        # at the arch's middle the upper edge sits `drop` under the plates' law (no rim stand-off, no crown) ...
        self.assertAlmostEqual(float(plain.law(top, mid) - lying.law(top, mid)), cfg["cop"].get("rim", 0.0) + 0.002, places=5)
        # ... it is the same dome from `len` down, and the same plate at the arch's ends
        self.assertAlmostEqual(float(plain.law(top + 0.041, mid)), float(lying.law(top + 0.041, mid)), places=6)
        self.assertAlmostEqual(float(plain.law(plain.top(end), end)), float(lying.law(lying.top(end), end)), places=6)

    def test_close_lands_the_cops_neck_end_on_the_arming_cap_and_leaves_its_ends(self):
        cfg = json.loads(json.dumps(CFG))
        cfg["cop"] = dict(cfg["cop"], arch={"span": 0.03, "power": 2.2})
        ref = arms()
        plain = sp.layout(cfg, ref)["l"]
        shut = sp.layout({**cfg, "cop": dict(cfg["cop"], close={"len": 0.04, "flat": 0.01, "room": 0.001, "fade": 0.03})}, ref)["l"]
        a, b, am = plain["sheets"][0], shut["sheets"][0], shut["arming"]
        mid, end = np.array(0.5 * (a.t0 + a.t1)), np.array(float(a.t0))
        top = a.top(mid)
        # at the arch's middle the upper edge's inner face lands `room` over the arming cap's own outer face, and
        # lies there for `flat` (the plate's shingle ramp alone lifts it: under a millimetre here) ...
        self.assertAlmostEqual(float(b.law(top, mid) - am.law(top, mid) - am.thick), 0.001, places=5)
        self.assertLess(float(b.inner(top + 0.009, mid) - am.law(top + 0.009, mid) - am.thick), 0.002)
        self.assertGreater(float(a.law(top, mid) - b.law(top, mid)), 0.002)
        # ... all along the edge that runs `fade` above the arch's ends ...
        for t in (50.0, 75.0, 120.0, 150.0):
            t = np.array(t)
            self.assertAlmostEqual(float(b.law(b.top(t), t) - am.law(b.top(t), t) - am.thick), 0.001, places=5)
        # ... it is the same dome from `flat` + `len` down, the same plate at the arch's ends, never higher anywhere
        self.assertAlmostEqual(float(a.law(top + 0.051, mid)), float(b.law(top + 0.051, mid)), places=6)
        self.assertAlmostEqual(float(a.law(a.top(end), end)), float(b.law(b.top(end), end)), places=6)
        S, TH = grid(a, 9, 27)
        self.assertLessEqual(float((b.law(S, TH) - a.law(S, TH)).max()), 1e-9)
        # (no arming cap: on her skin's own surface)
        bare = sp.layout({**{k: v for k, v in cfg.items() if k != "arming"},
                          "cop": dict(cfg["cop"], close={"len": 0.04, "room": 0.001})}, ref)["l"]
        self.assertAlmostEqual(float(bare["sheets"][0].law(top, mid) - bare["law"](top, mid)), 0.001 - cfg["clear"], places=5)

    def test_the_arming_caps_material_has_a_painted_template(self):
        have = {m.get("name") for _, g in gn.material_templates() for m in g.get("materials", [])
                if "baseColorTexture" in m.get("pbrMetallicRoughness", {})}
        for pid in ("plate_spaulders_plain", "plate_spaulders_warden"):
            cfg = sp.resolve(json.load(open(os.path.join(nb.NATIVE, pid, "build.json"), encoding="utf-8")))
            self.assertIn(cfg["materials"].get("arming", "darkleather"), have)


class Reach(unittest.TestCase):
    """The reach rule (cop.reach) and the yoke (arming.yoke) on her own body and clips."""

    @classmethod
    def setUpClass(cls):
        import hashlib
        import tempfile
        cls.sha = lambda cls, f: hashlib.sha256(open(f, "rb").read()).hexdigest()
        cls.ref = nb.Ref.her()
        # (10 Nov: the plain spaulders became the split, articulated one; the reach rule and the yoke are tested on
        # the one-cop recipe they were made for, frozen here: it also holds that the old keys build what they built)
        cls.cfg = sp.resolve(json.load(open(os.path.join(os.path.dirname(__file__), "testdata", "spaulder_one_cop.json"), encoding="utf-8")))
        cls.tmp = tempfile.mkdtemp()

    REACH = {"sink_max": 0.005, "clips": ["daggers_heavy", "run_reaver", "sword_heavy", "cast_flick"], "margin": 0.004, "start": -0.016}
    YOKE = {"to": -0.112, "strap": {"theta": 100}}

    def plain(self, reach=None, yoke=None):
        """The plain recipe (no reach, no yoke); with `reach` / `yoke`: those keys in, cop.close out."""
        c = json.loads(json.dumps(self.cfg))
        if reach:
            c["cop"].pop("close", None)
            c["cop"]["reach"] = dict(reach)
        if yoke:
            c["arming"]["yoke"] = dict(yoke)
        return c

    def test_no_key_builds_what_it_built_before(self):
        d = os.path.join(self.tmp, "plain")
        sp.spaulder("plate_spaulders_plain", self.plain(), out=d, ref=self.ref)
        self.assertTrue(self.sha(os.path.join(d, "plate_spaulders_plain.glb")).startswith("fd5b39002a33c79c"))
        self.assertTrue(self.sha(os.path.join(d, "plate_spaulders_plain.lod1.glb")).startswith("848c4f6ad8714113"))

    def test_a_higher_limit_moves_the_line_toward_her_neck(self):
        c = self.plain()
        lay = sp.layout(c, self.ref)
        fr = {sd: L["fr"] for sd, L in lay.items()}
        laws = {sd: L["law"] for sd, L in lay.items()}
        t0, t1 = c["theta"]
        rc = dict(self.REACH, passes=1)
        arch, bot = lay["l"]["top"][0], lay["l"]["bot"][0]
        a = sp.reach_line(self.ref, fr, laws, arch, bot, t0, t1, dict(rc, sink_max=0.003))
        b = sp.reach_line(self.ref, fr, laws, arch, bot, t0, t1, dict(rc, sink_max=0.009))
        self.assertTrue((b["line"] <= a["line"] + 1e-9).all())
        self.assertLess(b["line"].min(), a["line"].min() - 0.003)
        self.assertTrue((a["line"] >= a["arch"] - 1e-9).all())     # (never past the uncut edge)

    def test_a_plate_past_its_line_fails_the_build_with_its_name(self):
        # (10 Nov: at 5 mm over the four clips the plain cop's back end still sinks past the limit on its cut ride:
        # the state the rule was left in; when the recipes carry a passing reach, give this test a tighter limit)
        c = self.plain(self.REACH, self.YOKE)
        d = os.path.join(self.tmp, "past")
        with self.assertRaises(SystemExit) as e:
            sp.spaulder("plate_spaulders_plain", c, out=d, ref=self.ref)
        self.assertIn("cop.reach", str(e.exception))
        self.assertIn("cop_l_rigid", str(e.exception))
        rep = json.load(open(os.path.join(d, "build_report.json")))
        self.assertTrue(rep["reach"]["past"])
        self.assertFalse(os.path.exists(os.path.join(d, "plate_spaulders_plain.glb")))


if __name__ == "__main__":
    unittest.main()
