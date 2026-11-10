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


class Native(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
