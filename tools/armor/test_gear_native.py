"""gear_native's contract: the validator's refusals and the per-material merge (no body needed: stamps are passed in)."""
import json
import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gear_native as gn  # noqa: E402

STAMP = {"close": "abc", "play": "def"}
MATS = {"steel", "darkleather"}


def quad(name, material, y=1.0, **kw):
    P = np.array([[0, y, 0], [0.01, y, 0], [0.01, y + 0.01, 0], [0, y + 0.01, 0]], np.float32)
    return dict({"name": name, "P": P, "N": np.tile([0, 0, 1.0], (4, 1)), "T": [[0, 1, 2], [0, 2, 3]], "material": material}, **kw)


def piece_dir(root, pid="t_piece", nodes=None, **over):
    d = os.path.join(root, pid)
    os.makedirs(d, exist_ok=True)
    piece = {"id": pid, "slot": "legwear", "native": {"rest_hash": STAMP},
             "parts": {"plate_rigid": {"ride": {"thigh": 1}, "one_bone": True}, "rivets_rigid": {"with": "plate_rigid"}}}
    piece.update(over)
    json.dump(piece, open(os.path.join(d, "piece.json"), "w"))
    gn.write_glb(os.path.join(d, pid + ".glb"), nodes or [quad("plate_rigid", "steel"), quad("rivets_rigid", "steel"), quad("strap", "darkleather")])
    return d


def strip_indices(glb):
    """Rewrite a .glb with its primitives' indices removed (what an exporter set to non-indexed writes)."""
    import struct
    raw = open(glb, "rb").read()
    n = struct.unpack_from("<I", raw, 12)[0]
    js = json.loads(raw[20:20 + n])
    for m in js["meshes"]:
        for pr in m["primitives"]:
            pr.pop("indices", None)
    jb = json.dumps(js, separators=(",", ":")).encode()
    jb += b" " * (-len(jb) % 4)
    rest = raw[20 + n:]
    with open(glb, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 20 + len(jb) + len(rest)) + struct.pack("<II", len(jb), 0x4E4F534A) + jb + rest)


class Native(unittest.TestCase):
    def test_no_indices_refused(self):
        with tempfile.TemporaryDirectory() as r:
            d = piece_dir(r)
            strip_indices(os.path.join(d, "t_piece.glb"))
            why = self.check(d)
            self.assertTrue(why and all("has no indices" in w for w in why), why)

    def test_bones_rule(self):
        # an articulated lame: its blend named bone by bone, on the side its skin leans to; it leads its own group
        piece = {"parts": {"lame_rigid": {"bones": {"thigh_twist_02_{s}": 0.9, "calf_share_{s}": 0.1}},
                           "rivets_rigid": {"with": "lame_rigid"}}}
        self.assertEqual(gn.part_rule(piece, "rivets_rigid"), piece["parts"]["lame_rigid"])
        self.assertEqual(gn.lead_part(piece, "rivets_rigid"), "lame_rigid")
        names = ["pelvis", "thigh_twist_02_l", "thigh_twist_02_r", "calf_share_l", "calf_share_r"]
        D = np.array([0.1, 0.1, 0.6, 0.0, 0.2])
        np.testing.assert_allclose(gn.bones_blend(names, D, piece["parts"]["lame_rigid"]["bones"]), [0, 0, 0.9, 0, 0.1])
        with self.assertRaises(SystemExit):
            gn.bones_blend(names, D, {"knee_{s}": 1})
        with tempfile.TemporaryDirectory() as r:
            d = piece_dir(r, nodes=[quad("lame_rigid", "steel"), quad("rivets_rigid", "steel")], parts=piece["parts"])
            self.assertEqual(self.check(d), [])

    def check(self, d, **kw):
        return gn.validate(d, rest_hash=STAMP, materials=MATS, **kw)

    def test_valid(self):
        with tempfile.TemporaryDirectory() as r:
            self.assertEqual(self.check(piece_dir(r)), [])

    def test_refusals(self):
        with tempfile.TemporaryDirectory() as r:
            self.assertIn("missing rest stamp", " ".join(self.check(piece_dir(r, "a", native={}))))
            self.assertIn("another body", " ".join(self.check(piece_dir(r, "b", native={"rest_hash": {"close": "zzz"}}))))
            self.assertIn("unknown material", " ".join(self.check(piece_dir(r, "c", [quad("plate_rigid", "chrome")]))))
            self.assertIn("has no role", " ".join(self.check(piece_dir(r, "d", [quad("lame_rigid", "steel")]))))
            self.assertIn("unknown slot", " ".join(self.check(piece_dir(r, "e", slot="hat"))))
            self.assertIn("miss her body", " ".join(self.check(piece_dir(r, "f", [quad("strap", "steel", y=9.0)]))))

    def test_open_scalp(self):
        with tempfile.TemporaryDirectory() as r:
            d = piece_dir(r, "helm", [quad("cap_rigid", "steel", y=1.7)], slot="head", hair="hide",
                          parts={"cap_rigid": {"ride": {"neck": 1}, "one_bone": True}})
            head = (np.array([[0.005, 1.705, -0.004], [0.2, 1.705, -0.004]]), np.tile([0, 0, 1.0], (2, 1)))
            self.assertEqual(self.check(d, head=head, mask=np.array([0])), [])
            self.assertIn("open scalp: 1 of 2", " ".join(self.check(d, head=head, mask=np.array([0, 1]))))

    def test_merge_and_leads(self):
        with tempfile.TemporaryDirectory() as r:
            d = piece_dir(r)
            piece, glb = gn.load_piece(d)
            parts = gn.read_parts(glb)
            m = gn.merge_parts(piece, parts)
            self.assertEqual([x["name"] for x in m], ["t_piece.legwear.darkleather", "t_piece.legwear.steel"])
            self.assertEqual(len(m[1]["P"]), 8)
            self.assertEqual(m[1]["T"].max(), 7)
            self.assertEqual(gn.lead_part(piece, "rivets_rigid"), "plate_rigid")
            self.assertEqual(gn.part_rule(piece, "rivets_rigid")["ride"], {"thigh": 1})


class Legwear(unittest.TestCase):
    """The legwear slot's law, and the cuisses' articulated parts as their piece.json names them."""
    HERE = os.path.dirname(os.path.abspath(__file__))
    REPO = os.path.dirname(os.path.dirname(HERE))

    def test_legwear_slot(self):
        self.assertIn("legwear", gn.SLOTS)
        rr = json.load(open(os.path.join(self.HERE, "rigid_roles.json"), encoding="utf-8"))
        law = rr["slots"]["legwear"]
        self.assertEqual(law["ride"], {"thigh": 1})
        self.assertTrue(law["one_bone"])
        so = law["standoff"]
        # (lapped lames stand 11-17 mm off her at rest: the tuck must still be full that far out, or her knee front
        # goes untucked under the lapping bands; its depth as the cuisses were measured)
        self.assertGreaterEqual(so["tuck_full_mm"], 18)
        self.assertGreater(so["tuck_zero_mm"], so["tuck_full_mm"])
        self.assertEqual(so["tuck_depth_mm"], 18)
        g = gn.gf()
        self.assertEqual(g.standoff_law("legwear", rr), so)
        # a plate of the slot with no rule of its own: one thigh bone, the strongest in the mean, whatever else is in it

        class Body:
            joint_names = ["pelvis", "thigh_l", "thigh_twist_02_l", "calf_share_l"]
            T = np.array([[0, 1, 2]])
            J = np.tile(np.arange(4), (3, 1))
            W = np.tile([0.1, 0.2, 0.5, 0.2], (3, 1))
        j, w = g.rigid_blend(Body, np.array([0]), np.array([[0.2, 0.3, 0.5]]), "legwear", roles=rr)
        self.assertEqual((int(j[0]), float(w[0])), (2, 1.0))

    def test_articulated_parts(self):
        # the cuisses' own piece.json: every rigid part resolves to a rule, the lames name their bones (shares sum to
        # 1, a calf share only on the lames, growing toward the knee), fixings ride their plate
        d = os.path.join(self.REPO, "godot", "art", "gear", "native", "plate_cuisses_plain")
        piece = json.load(open(os.path.join(d, "piece.json"), encoding="utf-8"))
        self.assertEqual(piece["slot"], "legwear")
        parts = piece["parts"]
        for sd in "lr":
            calf = []
            for nm in [f"plate_{sd}_rigid"] + sorted(k for k in parts if k.startswith("lame") and f"_{sd}_" in k):
                bones = parts[nm]["bones"]
                self.assertAlmostEqual(sum(bones.values()), 1.0)
                self.assertTrue(all("{s}" in b for b in bones), nm)
                calf.append(sum(v for b, v in bones.items() if b.startswith("calf")))
                self.assertEqual(gn.lead_part(piece, nm), nm)
            self.assertEqual(calf[0], 0)
            self.assertEqual(calf, sorted(calf))
            self.assertGreater(calf[-1], 0)
            for nm in (f"rivets_{sd}_rigid", f"tabs_{sd}_rigid"):
                self.assertEqual(gn.lead_part(piece, nm), f"plate_{sd}_rigid")
            self.assertTrue(all(gn.part_rule(piece, k) for k in parts if k.endswith("_rigid")))

    def test_named_bones_take_no_shapes(self):
        # part_blends: a part that names its bones rides that blend exactly (its weights, and none of her corrective
        # shapes: their mean over the knee lame's bound points moved it 13.8 mm into her knee at knee_flex135); a
        # part with a role rule, and a bendy one, keep what the build gave them
        g = gn.gf()

        class Body:
            joint_names = ["pelvis", "thigh_twist_02_l", "thigh_twist_02_r", "calf_share_l", "calf_share_r"]
            T = np.array([[0, 1, 2]])
            J = np.tile(np.arange(5), (3, 1))
            W = np.tile([0.1, 0.5, 0.0, 0.4, 0.0], (3, 1))

        class Bind:
            z = {"lead_close": np.array([0, 1]), "comp0": np.array([0, 0, 1, -1]), "tri0": np.zeros(4, np.int64),
                 "bw0": np.full((4, 2), 21845, np.uint16)}
            meta = {"meshes": [{"tier": "close", "i": 0, "node": "n"}],
                    "parts": [{"rule": {"bones": {"thigh_twist_02_{s}": 0.8, "calf_share_{s}": 0.2}}, "comp": 0},
                              {"rule": {"ride": {"thigh": 1}, "one_bone": True}, "comp": 1}]}
        d = np.tile([0.0, 0.0, -0.017], (4, 1))
        ev = {"n": {"inv": np.arange(4), "J": np.zeros((4, 8), np.uint16), "W": np.zeros((4, 8), np.float32),
                    "shapes": {"knee_flex135_l": d.copy()}}}
        gn.part_blends(Bind, {"close": Body}, ev)
        e = ev["n"]
        for v in (0, 1):
            got = {Body.joint_names[j]: round(float(w), 4) for j, w in zip(e["J"][v], e["W"][v]) if w > 0}
            self.assertEqual(got, {"thigh_twist_02_l": 0.8, "calf_share_l": 0.2})
        np.testing.assert_array_equal(e["shapes"]["knee_flex135_l"][:2], 0.0)
        np.testing.assert_array_equal(e["shapes"]["knee_flex135_l"][2:], d[2:])


if __name__ == "__main__":
    unittest.main()


def test_plain_natives_name_bare_steel_and_it_has_a_template():
    """The plain plate natives' plate is `plainsteel` (bare steel, provisional: outfit_materials.json's note), never
    `steel` (the Warden's navy enamel, metal_finishes.json), and write_src gives it a painted material: its row's
    "template" key's glTF material from a gear source, under its own name. The Warden's spaulders keep `steel`."""
    import json
    import os
    import tempfile
    import numpy as np
    import gear_native as gn
    table = json.load(open(gn.MATERIALS, encoding="utf-8"))
    row = table["plainsteel"]
    assert (row["kind"], row["zone"], row["template"]) == ("metal", "metal", "steel") and "template" not in table["steel"]
    fin = json.load(open(os.path.join(os.path.dirname(gn.MATERIALS), "metal_finishes.json"), encoding="utf-8"))
    assert "plainsteel" not in fin and fin["steel"] == "enamel"
    nat = os.path.join(gn.REPO, "godot", "art", "gear", "native")
    for pid in ("plate_spaulders_plain", "plate_cuisses_plain"):
        names = {p["material"] for p in gn.read_parts(os.path.join(nat, pid, pid + ".glb"))}
        assert "plainsteel" in names and "steel" not in names, (pid, names)
    names = {p["material"] for p in gn.read_parts(os.path.join(nat, "plate_spaulders_warden", "plate_spaulders_warden.glb"))}
    assert "steel" in names and "plainsteel" not in names, names
    tri = {"P": np.eye(3, dtype=np.float32), "N": np.tile(np.float32([0, 0, 1]), (3, 1)), "T": np.array([[0, 1, 2]], np.uint32),
           "uv0": None, "uv1": None, "col": None, "material": "plainsteel", "name": "t"}
    piece = {"id": "t_plain", "slot": "legwear"}
    with tempfile.TemporaryDirectory(dir=os.path.join(gn.REPO, "godot", "art", "gear")) as td:
        out = os.path.join(td, "t.src.glb")
        gn.write_src(out, piece, gn.merge_parts(piece, [tri]))
        js = gn.gf().read_glb(out)[0] if hasattr(gn.gf(), "read_glb") else None
        if js is None:
            import struct
            b = open(out, "rb").read()
            js = json.loads(b[20:20 + struct.unpack("<I", b[12:16])[0]])
    m = [m for m in js["materials"] if m["name"] == "plainsteel"]
    assert len(m) == 1 and "baseColorTexture" in m[0]["pbrMetallicRoughness"] and "normalTexture" in m[0], js["materials"]
    assert any("outfit_steel_diff" in im["uri"] for im in js["images"])
