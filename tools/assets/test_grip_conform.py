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


def test_conform():
    sp = gc.spec()
    for pid, args in (("dagger_b", dict(anchor=False)), ("viking_sword", dict(seat=True, round_=True))):
        pc = gc.load(pid)
        r = gc.conform(pc, sp, **args)
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / f"{pc.row['file']}.glb"; pc.g.write(f)
            k = gc.check(pid, f, moved=r["moved"])
        assert k["ok_section"], (pid, k["section"])
        assert k["stray_rows"] == 0 and k["uv_identical"] and k["other_accessors_identical"] and k["bin_same_length"], k
        assert k["mount"]["axes_deg"] < 1e-3 and k["mount"]["grip_mm"] < 0.01 and abs(k["mount"]["scale"]) < 1e-6, k


if __name__ == "__main__":
    test_reference_pieces_are_the_spec(); test_conform(); print("grip_conform: pass")
