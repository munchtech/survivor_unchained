"""piece_ship's stamp and install, and adorn on a followed (eight-weight) shell."""
import json
import os
import struct
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adorn  # noqa: E402
import piece_ship as ps  # noqa: E402


def _write_glb(path, P, name="Heroine"):
    P = np.asarray(P, np.float32)
    idx = np.arange(len(P), dtype=np.uint32)
    bin_ = P.tobytes() + idx.tobytes()
    js = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(bin_)}],
          "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": P.nbytes}, {"buffer": 0, "byteOffset": P.nbytes, "byteLength": idx.nbytes}],
          "accessors": [{"bufferView": 0, "componentType": 5126, "count": len(P), "type": "VEC3"},
                        {"bufferView": 1, "componentType": 5125, "count": len(idx), "type": "SCALAR"}],
          "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
          "nodes": [{"name": "Other"}, {"name": name, "mesh": 0}]}
    j = json.dumps(js).encode()
    j += b" " * (-len(j) % 4)
    b = bin_ + b"\0" * (-len(bin_) % 4)
    out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(j) + 8 + len(b))
    out += struct.pack("<II", len(j), 0x4E4F534A) + j + struct.pack("<II", len(b), 0x004E4942) + b
    open(path, "wb").write(out)


def test_glb_stamp_is_the_geometry(tmp_path):
    P = np.random.default_rng(1).normal(size=(30, 3)) * 0.3
    _write_glb(tmp_path / "a.glb", P)
    _write_glb(tmp_path / "b.glb", P[::-1])                     # (same points, another order)
    Q = P.copy()
    Q[3, 1] += 2e-5                                             # (one point moved 0.02 mm)
    _write_glb(tmp_path / "c.glb", Q)
    a, b, c = (ps.glb_body_hash(str(tmp_path / f)) for f in ("a.glb", "b.glb", "c.glb"))
    assert a == b and a != c and len(a) == 8


def test_install_stamps_row_gltf_sockets_and_keeps_other_rows(tmp_path):
    st, art = tmp_path / "stage", tmp_path / "art"
    (st / "armor_tuck").mkdir(parents=True)
    art.mkdir()
    json.dump({"asset": {"extras": {"armor_piece": "p", "body_hash": "old"}}, "images": [{"uri": "../people/outfit_tex/x.png"}]},
              open(st / "p.gltf", "w"))
    (st / "p.bin").write_bytes(b"\0" * 8)
    (st / "armor_tuck" / "p.bin").write_bytes(b"\0" * 4)
    json.dump({"id": "p", "body_hash": "old"}, open(st / "p.sockets.json", "w"))
    json.dump([{"id": "p", "slot": "top", "body_hash": "old"}], open(st / "armor_index.json", "w"))
    json.dump([{"id": "a", "body_hash": "lab"}, {"id": "p", "body_hash": "stale"}], open(art / "armor_index.json", "w"))
    files = ps.install("p", str(st), str(art), "66182af6", "lab", "7de7f07b")
    assert sorted(files) == ["armor_tuck/p.bin", "p.bin", "p.gltf", "p.sockets.json"]
    rows = json.load(open(art / "armor_index.json"))
    assert [r["id"] for r in rows] == ["a", "p"] and rows[0] == {"id": "a", "body_hash": "lab"}
    assert rows[1] == {"id": "p", "slot": "top", "body_hash": "lab", "body_glb": "66182af6", "built_on": "7de7f07b"}
    ex = json.load(open(art / "p.gltf"))["asset"]["extras"]
    assert ex["armor_piece"] == "p" and ex["body_glb"] == "66182af6" and ex["body_hash"] == "lab"
    assert json.load(open(art / "p.sockets.json"))["built_on"] == "7de7f07b"


def test_follow_ratio_reads_the_field_line():
    t = "FOLLOW field: BASE 1000 pts, BODY 990; twins 960, re-meshed away 40"
    assert ps.follow_ratio(t) == pytest.approx(0.96) and ps.follow_ratio("nothing") == 0.0


def _shell8(n=12, nb=12):
    rng = np.random.default_rng(3)
    J = np.stack([rng.permutation(nb)[:8] for _ in range(n)])
    W = rng.random((n, 8)) + 0.05
    W /= W.sum(1, keepdims=True)
    return {"name": "p.top.steel", "attrs": {
        "POSITION": [rng.random((n, 3)).astype(np.float32), False], "NORMAL": [np.tile([0, 0, 1], (n, 1)).astype(np.float32), False],
        "TEXCOORD_0": [np.zeros((n, 2), np.float32), False], "TEXCOORD_1": [np.zeros((n, 2), np.float32), False],
        "COLOR_0": [np.zeros((n, 4), np.uint16), True],
        "JOINTS_0": [J[:, :4].astype(np.uint8), False], "WEIGHTS_0": [W[:, :4].astype(np.float32), False],
        "JOINTS_1": [J[:, 4:].astype(np.uint8), False], "WEIGHTS_1": [W[:, 4:].astype(np.float32), False]},
        "tris": np.array([[0, 1, 2]]), "extras": {}}, nb


def test_adorn_keeps_all_eight_weights_of_a_followed_shell():
    m, nb = _shell8()
    d = adorn.dense(m, nb)
    assert d.sum(1) == pytest.approx(1.0) and ((d > 0).sum(1) == 8).all()
    # (adornment at each shell point, with the shell's own dense weights: written back as two sets, every weight kept)
    P = m["attrs"]["POSITION"][0].astype(np.float64)
    n = len(P)
    parts = [(P, np.tile([0, 0, 1.0], (n, 1)), np.zeros((n, 2)), np.zeros((n, 2)), np.zeros((n, 4)), d, np.array([[0, 1, 2]]))]
    assert adorn.append(m, parts, nb) == 1
    a = m["attrs"]
    assert all(len(a[k][0]) == 2 * n for k in ("JOINTS_0", "WEIGHTS_0", "JOINTS_1", "WEIGHTS_1"))
    d2 = adorn.dense(m, nb)
    assert np.abs(d2[n:] - d).max() < 1e-6
    # (a new mesh like it carries both sets too)
    model = type("M", (), {"meshes": []})()
    nm = adorn.new_mesh(model, "p.top.gold", "gold", m, {})
    assert set(adorn.weight_keys(nm["attrs"])) == {"JOINTS_0", "WEIGHTS_0", "JOINTS_1", "WEIGHTS_1"}


def test_adorn_four_weight_shell_stays_one_set():
    m, nb = _shell8()
    for k in ("JOINTS_1", "WEIGHTS_1"):
        del m["attrs"][k]
    d = adorn.dense(m, nb)
    P = m["attrs"]["POSITION"][0].astype(np.float64)
    parts = [(P, np.tile([0, 0, 1.0], (len(P), 1)), np.zeros((len(P), 2)), np.zeros((len(P), 2)), np.zeros((len(P), 4)), d, np.array([[0, 1, 2]]))]
    adorn.append(m, parts, nb)
    assert adorn.weight_sets(m["attrs"]) == 1 and m["attrs"]["JOINTS_0"][0].dtype == np.uint8
