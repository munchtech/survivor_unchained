"""p4_parity on a small committed fixture (tools/anim/data/parity_fixture_walk_warden.json.gz: the built walk_warden clip and four
steady probed frames of the game's --pose-probe-full dump, 42 KB), no Godot needed.

    python -m pytest -q tools/anim/test_p4_parity.py
"""
import gzip
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4_parity as PP  # noqa: E402

FIX = Path(__file__).resolve().parent / "data/parity_fixture_walk_warden.json.gz"
_cache = {}


def fixture():
    if "d" not in _cache:
        d = json.loads(gzip.open(FIX, "rt").read())
        _cache["d"] = d
        _cache["py"] = PP.Py(d["clip"])
    return _cache["d"], _cache["py"]


def test_fixture_is_small():
    assert FIX.stat().st_size < 200_000


def test_time_fit_recovers_a_known_time():
    d, py = fixture()
    t0 = 7.3
    post = py.post(t0)      # (post-law world turns of the fit bones are the pre-law ones: the laws keep them)
    game = {b: post[b] for b in PP.FIT_BONES}
    t, cost = PP.fit_time(py, game)
    assert abs(t - t0) < 0.01 and cost < 0.05


def test_the_loop_wraps_at_its_last_frame():
    d, py = fixture()
    a, b = py.pre(0.0)[1], py.pre(float(py.n - 1))[1]
    assert np.abs(a - b).max() < 1e-9


def test_pieces_and_blend_base_on_the_fixture():
    d, py = fixture()
    rows, base = PP.run(d["frames"], d["clip"], py=py)
    assert len(rows) == 4 and not any(r.get("skipped") for r in rows)
    for k in PP.PIECES:
        assert max(r[f"{k}_mm"] for r in rows) < PP.TOL_MM
        assert max(r[f"{k}_deg"] for r in rows) < PP.TOL_DEG
    # (the blend-base floor measured on B is 0.12 deg on the fingers and hand_r: float32 tracks in the game; 0.15 is the pin)
    off = {b: a for b, a in base.items() if not any(b.lower().startswith(p) for p in PP.LOOK)}
    assert max(off.values()) < 0.15


def test_a_wrong_pose_is_flagged():
    d, py = fixture()
    bad = json.loads(json.dumps(d["frames"][0]))
    bad["bones"]["upperarm_l"][9] += 0.05       # 5 cm off at the shoulder: the pelvis stays, the sword rides hand_r
    bad["pieces"] = {k: {**v, "pts": [[x + 0.01, y, z] for x, y, z in v["pts"]]} for k, v in bad["pieces"].items()}
    rows, _ = PP.run([bad], d["clip"], py=py)
    assert max(rows[0]["sword_mm"], rows[0]["shield_mm"]) > 5.0
