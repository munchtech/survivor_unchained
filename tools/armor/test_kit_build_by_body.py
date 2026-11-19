"""build.json body-keyed values (kit_build.by_body, armor-D 17 Nov): body A reads what it read before; a named body
reads its own values, in lists and nested objects too."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_build as kb  # noqa: E402


CFG = {"clear": 0.003, "plates": [
    {"name": "tasset", "tuck": 0.01},
    {"name": "hipf", "tuck": 0.01, "lames": [{"ride": {"thigh_hinge_l": 1.0}, "len": [0.065, 0.09]}],
     "by_body": {"p1": {"tuck": 0.025, "lames": [{"ride": {"hiptasset_hinge_l": 1.0}, "len": [0.19, 0.18]}],
                        "over": ["hip"]}}}]}


def test_body_a_reads_what_it_read_before():
    a = kb.by_body(CFG, "a")
    want = {k: v for k, v in CFG.items()}
    want["plates"] = [CFG["plates"][0], {k: v for k, v in CFG["plates"][1].items() if k != "by_body"}]
    assert a == want
    assert list(a["plates"][1]) == ["name", "tuck", "lames"]


def test_a_named_body_reads_its_own_values():
    b = kb.by_body(CFG, "p1")
    hipf = b["plates"][1]
    assert hipf["tuck"] == 0.025 and hipf["over"] == ["hip"]
    assert hipf["lames"] == [{"ride": {"hiptasset_hinge_l": 1.0}, "len": [0.19, 0.18]}]
    assert b["plates"][0] == CFG["plates"][0] and "by_body" not in hipf
    assert CFG["plates"][1]["tuck"] == 0.01  # (the source is not changed)


def test_shipped_recipes_keep_body_a():
    import json
    for pid in sorted(os.listdir(kb.SRC)):
        f = os.path.join(kb.SRC, pid, "build.json")
        if not os.path.exists(f):
            continue
        raw = json.load(open(f, encoding="utf-8"))
        if "by_body" not in json.dumps(raw):
            assert kb.by_body(raw, "a") == raw, pid


def _bodice_raw():
    import json
    return json.load(open(os.path.join(kb.SRC, "kit_bodice", "build.json"), encoding="utf-8"))


def test_bodice_apron_and_gem_are_body_b_only():
    """(armor-D, 18 Nov) The cup apron and the gem's lift are B's knobs: A's bodice reads no apron and no gem (its
    cups, rims and clasp are built by the code path they always were), and stripping B's knobs leaves A unchanged."""
    raw = _bodice_raw()
    a, b = kb.by_body(raw, "a"), kb.by_body(raw, "p1")
    assert "apron" not in a["cup"] and "gem" not in a["cup"]
    assert b["cup"]["apron"]["psi"][1] == 255.0 and b["cup"]["gem"]["off"] > 0
    import copy
    stripped = copy.deepcopy(raw)
    stripped["cup"]["by_body"]["p1"] = {k: v for k, v in stripped["cup"]["by_body"]["p1"].items()
                                        if k not in ("apron", "gem")}
    assert kb.by_body(stripped, "a") == a


def test_bodice_apron_corner_laps_the_side_panel():
    """(armor-D r3, 18 Nov) B's apron goes round her outer-lower corner: from a spoke before L's, its first column over
    the side panel's front edge (theta_side + step_th) by at least 4 mm at her side's girth there (about 0.129 m); its
    lap deeper at the centre front (her arms up); the side seam then starts under the apron's rim. A has none of it."""
    raw = _bodice_raw()
    a, b = kb.by_body(raw, "a"), kb.by_body(raw, "p1")
    ap, cu, co = b["cup"]["apron"], b["cup"], b["corset"]
    cn = ap["corner"]
    assert cn["psi"] < ap["psi"][0]
    import math
    lap_mm = math.radians(cn["th"] - (cu["theta_side"] + co["step_th"])) * 0.129 * 1000
    assert lap_mm >= 4.0, lap_mm
    assert ap["lap_c"] >= 0.008 and ap["lap"] >= 0.004 and ap["lap_w"] > 0
    assert cn["seam_dy"] > 0
    assert "apron" not in a["cup"]


def test_cup_slab_welds_the_apron_to_the_cup():
    """cup_slab: the apron's row 0 IS the cup's last ring at its spokes (one point each, no seam), and the rim's outline
    runs once round the joined edge."""
    import numpy as np
    K, S, R = 4, 12, 5
    ph = np.linspace(0.2, 1.0, K)[:, None]
    ps = np.radians(np.linspace(0, 360, S, endpoint=False))[None, :]
    Pin = np.stack([np.sin(ph) * np.cos(ps), np.sin(ph) * np.sin(ps), np.cos(ph) + 0 * ps], -1) * 0.05
    Nn = Pin / np.linalg.norm(Pin, axis=-1, keepdims=True)
    J = np.arange(6, 9)
    t = np.linspace(0, 1, R)[:, None, None]
    Pa = Pin[-1, J][None] + t * np.array([0.0, 0.0, -0.02])
    Na = np.broadcast_to(Nn[-1, J][None], Pa.shape).copy()
    part, loop = kb.cup_slab("cup_t", "steel", Pin, Nn, 0.0016, J, Pa, Na)
    n_face = K * S + (R - 1) * len(J)
    assert len(part.P) == 2 * n_face + 2 * len(loop)
    assert len(loop) == (S - len(J) + 2) + (R - 1) + (len(J) - 1) + (R - 2)
    inner = part.P[n_face:2 * n_face]
    assert np.allclose(inner[(K - 1) * S + J], Pa[0])
    # every inner-face edge is shared by two faces except the outline's (a closed surface with one boundary loop)
    T = part.T[(part.T >= n_face).all(1) & (part.T < 2 * n_face).all(1)] - n_face
    e = np.sort(np.r_[T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]], 1)
    _, c = np.unique(e, axis=0, return_counts=True)
    assert (c <= 2).all() and (c == 1).sum() == len(loop)
