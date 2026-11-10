"""A fitted unit carries its source's vertex data as the source stores it (gear_fit.stored): the outfit shader's baked
COLOR_0 (sky seen, piece, painted, flag) is a normalized integer accessor out of Blender and must not fall to 0."""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "anim"))
import gear_fit as gf  # noqa: E402
from skin import Gltf  # noqa: E402

REPO = Path(__file__).resolve().parents[2]


def _gltf(tmp_path, arr, comp, normalized):
    """A one-accessor gltf file: `arr` (n, 4) stored at component type `comp`."""
    b = np.ascontiguousarray(arr).tobytes()
    (tmp_path / "a.bin").write_bytes(b)
    acc = {"bufferView": 0, "componentType": comp, "count": len(arr), "type": "VEC4"}
    if normalized:
        acc["normalized"] = True
    js = {"asset": {"version": "2.0"}, "buffers": [{"uri": "a.bin", "byteLength": len(b)}],
          "bufferViews": [{"buffer": 0, "byteLength": len(b)}], "accessors": [acc]}
    (tmp_path / "a.gltf").write_text(json.dumps(js))
    return Gltf(str(tmp_path / "a.gltf"))


@pytest.mark.parametrize("comp,dt", [(5123, np.uint16), (5121, np.uint8)])
def test_normalized_accessor_comes_back_as_stored(tmp_path, comp, dt):
    top = np.iinfo(dt).max
    rng = np.random.default_rng(3)
    arr = rng.integers(0, top + 1, size=(500, 4)).astype(dt)
    arr[0], arr[1] = 0, top                                   # (both ends: 1.0 must not come back as 1 / top)
    g = _gltf(tmp_path, arr, comp, True)
    assert g.accessor(0).max() <= 1.0                         # (the reader's floats: what write_unit used to cast)
    v = gf.stored(g, 0)
    assert v.dtype == dt and np.array_equal(v, arr)


def test_float_and_unnormalized_accessors_are_untouched(tmp_path):
    arr = np.random.default_rng(4).random((64, 4)).astype(np.float32)
    g = _gltf(tmp_path, arr, 5126, False)
    v = gf.stored(g, 0)
    assert v.dtype == np.float32 and np.array_equal(v, arr)   # (a native's float COLOR_0: byte for byte as before)
    ints = np.arange(64 * 4, dtype=np.uint16).reshape(64, 4)
    d = tmp_path / "u"
    d.mkdir()
    assert np.array_equal(gf.stored(_gltf(d, ints, 5123, False), 0), ints)


OUT = REPO / "godot" / "art" / "gear" / "out" / "body_p1"
PLAIN = ["plate_top_plain", "plate_gstring_plain", "plate_cuirass_plain", "plate_pauldrons_plain"]


@pytest.mark.parametrize("pid", PLAIN)
def test_built_unit_carries_its_sources_vertex_data(pid):
    """The built authored units (git-ignored: skipped where not built): every COLOR_0 / TEXCOORD_n of every mesh equals
    its source's, value for value, and the steel's sky seen has not fallen to 0."""
    unit, src = OUT / f"{pid}.gltf", REPO / "godot" / "art" / "armor" / f"{pid}.gltf"
    if not unit.exists() or not src.exists():
        pytest.skip("unit not built here")
    u, s = Gltf(str(unit)), Gltf(str(src))
    stamp = u.js["asset"].get("extras", {}).get("gear_fit", {})
    seen = 0
    for n in u.js["nodes"]:
        if "mesh" not in n:
            continue
        sn = next((x for x in s.js["nodes"] if x.get("name") == n["name"] and "mesh" in x), None)
        if sn is None:
            continue
        ua = u.js["meshes"][n["mesh"]]["primitives"][0]["attributes"]
        sa = s.js["meshes"][sn["mesh"]]["primitives"][0]["attributes"]
        for k in sa:
            if not k.startswith(("COLOR_", "TEXCOORD_")):
                continue
            assert k in ua, (pid, n["name"], k, stamp)
            assert np.array_equal(gf.stored(u, ua[k]), gf.stored(s, sa[k])), (pid, n["name"], k)
            seen += 1
        if "COLOR_0" in ua and n["name"].endswith(".steel"):
            sky = u.accessor(ua["COLOR_0"])[:, 0]
            assert sky.mean() > 0.2, (pid, n["name"], "sky seen fell to 0")   # (the fault: every value cast to 0)
    assert seen
