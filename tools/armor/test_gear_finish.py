"""gear_finish: a piece's finish key is data on its record, applied in the fit build."""
import copy
import json
import os
import sys
import types

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gear_finish as gfin  # noqa: E402

TABLE = {"steel": {"kind": "metal"}, "plainsteel": {"kind": "metal", "template": "steel"}, "gold": {"kind": "metal"},
         "darkleather": {"kind": "leather"}, "ghost": {"kind": "metal"}}


def unit():
    """write_unit's lists for a piece with a leather, a steel (one texture) and a gold material."""
    mats = [{"name": "darkleather", "doubleSided": True},
            {"name": "steel", "pbrMetallicRoughness": {"metallicFactor": 1.0, "baseColorTexture": {"index": 0}}},
            {"name": "gold", "pbrMetallicRoughness": {"metallicFactor": 1.0}}]
    texs, imgs, smps = [{"sampler": 0, "source": 0}], [{"uri": "../people/outfit_tex/steel.jpg"}], [{"magFilter": 9729}]
    meshes = [{"name": f"p.top.{m['name']}", "primitives": [{"material": i}], "extras": {"material": m["name"], "rank": 0}}
              for i, m in enumerate(mats)]
    meshes.append({"name": "p.lod1.steel", "primitives": [{"material": 1}], "extras": {"lod": "lod1", "material": "steel"}})
    return mats, texs, imgs, smps, meshes


def bd(pid="plate_test"):
    return types.SimpleNamespace(id=pid, meta={"id": pid, "kind": "armor", "row": {"id": pid}})


def source(tmp_path):
    """A gear source that carries gold with a texture of its own."""
    f = os.path.join(str(tmp_path), "src", "plate_other.gltf")
    return [(f, {"materials": [{"name": "gold", "normalTexture": {"index": 0}, "pbrMetallicRoughness": {"roughnessFactor": 0.2}}],
                 "textures": [{"source": 0}], "images": [{"uri": "tex/gold_nor.jpg"}]})]


def test_mapped_name_is_written_and_the_rest_keep_theirs():
    mats, texs, imgs, smps, meshes = u = unit()
    before = copy.deepcopy(u)
    done = gfin.apply(bd(), mats, texs, imgs, smps, meshes, "out", finish={"steel": "plainsteel"}, table=TABLE, sources=[])
    assert done == {"steel": "plainsteel"}
    assert [m["name"] for m in mats] == ["darkleather", "plainsteel", "gold"]       # (trim and leather stay)
    # (plainsteel's template is the mapped material itself: the piece's own steel body under the new name)
    assert {k: v for k, v in mats[1].items() if k != "name"} == {k: v for k, v in before[0][1].items() if k != "name"}
    assert (mats[0], mats[2], texs, imgs, smps) == (before[0][0], before[0][2], before[1], before[2], before[3])
    assert [m["extras"]["material"] for m in meshes] == ["darkleather", "plainsteel", "gold", "plainsteel"]
    assert [m["primitives"] for m in meshes] == [m["primitives"] for m in before[4]]


def test_template_body_is_copied_from_the_gear_sources(tmp_path):
    mats, texs, imgs, smps, meshes = unit()
    table = dict(TABLE, gilt={"kind": "metal", "template": "gold"})
    out = os.path.join(str(tmp_path), "out")
    gfin.apply(bd(), mats, texs, imgs, smps, meshes, out, finish={"steel": "gilt"}, table=table, sources=source(tmp_path))
    m = mats[1]
    assert m["name"] == "gilt" and m["pbrMetallicRoughness"] == {"roughnessFactor": 0.2}
    t = texs[m["normalTexture"]["index"]]
    assert m["normalTexture"]["index"] == 1 and imgs[t["source"]]["uri"] == "../src/tex/gold_nor.jpg"
    assert smps[t["sampler"]] == {"magFilter": 9729, "minFilter": 9987}
    assert mats[2]["name"] == "gold" and "normalTexture" not in mats[2]              # (the piece's own gold untouched)


def test_template_materials_is_the_natives_rule(tmp_path):
    got, tail = gfin.template_materials({"gold", "gilt", "ghost"}, str(tmp_path), dict(TABLE, gilt={"template": "gold"}), source(tmp_path))
    assert sorted(got) == ["gilt", "gold"] and got["gilt"]["name"] == "gilt"         # (a key no source carries is absent)
    assert got["gilt"]["normalTexture"]["index"] != got["gold"]["normalTexture"]["index"]
    assert [i["uri"] for i in tail["images"]] == ["src/tex/gold_nor.jpg"] * 2
    assert gfin.template_materials({"ghost"}, str(tmp_path), TABLE, source(tmp_path)) == ({}, None)


def test_unknown_key_fails_naming_the_piece():
    mats, texs, imgs, smps, meshes = unit()
    with pytest.raises(SystemExit) as e:
        gfin.apply(bd("plate_x_plain"), mats, texs, imgs, smps, meshes, "out", finish={"steel": "nosuch"}, table=TABLE, sources=[])
    assert "plate_x_plain" in str(e.value) and "nosuch" in str(e.value)
    with pytest.raises(SystemExit) as e:   # (a key in the table that no gear source can draw)
        gfin.apply(bd("plate_x_plain"), mats, texs, imgs, smps, meshes, "out", finish={"steel": "ghost"}, table=TABLE, sources=[])
    assert "plate_x_plain" in str(e.value) and "ghost" in str(e.value)
    with pytest.raises(SystemExit) as e:   # (a mapped name the piece does not have: a typo is not silent)
        gfin.apply(bd("plate_x_plain"), mats, texs, imgs, smps, meshes, "out", finish={"stel": "plainsteel"}, table=TABLE, sources=[])
    assert "plate_x_plain" in str(e.value) and "stel" in str(e.value)


def test_no_key_is_identical():
    for fin in ({}, {"steel": "steel"}):
        u = unit()
        before = json.dumps(u)
        assert gfin.apply(bd(), *u, "out", finish=fin, table=TABLE, sources=[]) == {}
        assert json.dumps(u) == before
    # (the record itself: a row without "finish", read from the binding's stored row when no index has the piece)
    u = unit()
    before = json.dumps(u)
    assert gfin.apply(types.SimpleNamespace(id="x.lod", meta={"kind": "outfit_lod", "row": {"id": "x.lod"}}), *u, "out") == {}
    assert json.dumps(u) == before


def test_record_is_read_live(tmp_path, monkeypatch):
    ip = tmp_path / "armor_index.json"
    ip.write_text(json.dumps([{"id": "a"}, {"id": "plate_test", "finish": {"steel": "plainsteel"}}]))
    monkeypatch.setitem(gfin.INDEXES, "armor", str(ip))
    assert gfin.record(bd())["finish"] == {"steel": "plainsteel"}          # (the index, not the binding's stored row)
    nd = tmp_path / "native" / "n1"
    nd.mkdir(parents=True)
    (nd / "piece.json").write_text(json.dumps({"id": "n1", "finish": {"plainsteel": "gold"}}))
    monkeypatch.setattr(gfin, "REPO", str(tmp_path))
    nat = types.SimpleNamespace(id="n1", meta={"kind": "native", "native_dir": "native/n1", "row": {"id": "n1"}})
    assert gfin.record(nat)["finish"] == {"plainsteel": "gold"}            # (a native: its piece.json wins over its source's name)


def test_the_plain_authored_pieces_ask_for_bare_steel():
    rows = {r["id"]: r for r in json.load(open(gfin.INDEXES["armor"], encoding="utf-8"))}
    table = json.load(open(gfin.MATERIALS, encoding="utf-8"))
    for pid in ("plate_top_plain", "plate_gstring_plain", "plate_cuirass_plain", "plate_pauldrons_plain"):
        assert rows[pid].get("finish") == {"steel": "plainsteel"}, pid
    for pid, r in rows.items():
        assert all(k in table for k in (r.get("finish") or {}).values()), pid
        if not pid.endswith("_plain"):
            assert "finish" not in r, pid
