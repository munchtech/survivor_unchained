"""grip_conform: the reference pieces measure as their types' spec; a conform meets the spec, keeps every other byte and the
mount.  python tools/assets/test_grip_conform.py   (or pytest)"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grip_conform as gc  # noqa: E402


def test_reference_pieces_are_the_spec():
    sp = gc.spec()
    for pid in ("mage_staff", "chevalier_sword", "daggers"):
        pc = gc.load(pid); s = gc.measure_piece(pc, sp)
        q = gc.type_of(pc.row["kind"], sp)[1]["section"]
        assert abs(s["half_w"] - q["half_w"]) < 0.05, (pid, s)
        assert abs(s["half_d"] - q["half_d"]) < (0.05 if q["shape"] == "flat" else 0.3), (pid, s)


ORIG = "a4df6f89"     # the weapons as they came (viking_sword's flat oval grip): conformed from the original


def test_cylinder_rings():
    """--cylinder: every ring of the band (its beads and the sag between long quads included) on the type's radius."""
    import numpy as np
    sp = gc.spec(); pc = gc.load("viking_sword", ORIG)
    r = gc.conform(pc, sp, seat=True, cylinder=True)
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "viking_sword.glb"; pc.g.write(f)
        b = gc.load("viking_sword", path=f)
        t0, t1 = r["band"]; m, cl, e1, e2, t, R = b.frame(t0 - r["moved"], t1 - r["moved"])
        rr = np.linalg.norm(R[m], axis=1) * b.mm
        target = gc.type_of(b.row["kind"], sp)[1]["section"]["half_w"]
        assert np.abs(rr - target).max() < gc.TOL, (rr.min(), rr.max())


def test_conform():
    sp = gc.spec()
    for pid, args, rev in (("dagger_b", dict(anchor=False), None), ("viking_sword", dict(seat=True, round_=True), ORIG),
                           ("viking_sword", dict(seat=True, cylinder=True), ORIG)):
        pc = gc.load(pid, rev)
        r = gc.conform(pc, sp, **args)
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / f"{pc.row['file']}.glb"; pc.g.write(f)
            k = gc.check(pid, f, rev, moved=r["moved"])
        assert k["ok_section"], (pid, k["section"])
        assert k["stray_rows"] == 0 and k["uv_identical"] and k["other_accessors_identical"] and k["bin_same_length"], k
        assert k["mount"]["axes_deg"] < 1e-3 and k["mount"]["grip_mm"] < 0.01 and abs(k["mount"]["scale"]) < 1e-6, k


if __name__ == "__main__":
    test_reference_pieces_are_the_spec(); test_conform(); test_cylinder_rings(); print("grip_conform: pass")
