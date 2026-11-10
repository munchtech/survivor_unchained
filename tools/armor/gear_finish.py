"""A piece's finish is data on its record, applied in the fit build (tools/armor/gear_fit.py write_unit).

The record (an authored piece's row in godot/art/armor/armor_index.json or godot/art/people/armor_index.json, a native
piece's piece.json) may carry

    "finish": {"<material name in the piece's source>": "<key of godot/art/people/outfit_materials.json>"}

and the build writes that material under the key: the game looks a surface's material NAME up in outfit_materials.json
(People.OutfitMaterials), so the key decides the shader, the zone and the finish. A new look for an existing piece is
a record edit and `gear_fit.py build --only <id>`: no Blender, no new bind (the record is read at build time, not from
the binding). A material the record does not map keeps its name. A record without the key builds as before.

The key's body: its outfit_materials.json row may name a "template" (plainsteel: steel); the material and its textures
are the template key's (the key's own when it names none). When that is the mapped source material itself, the piece's
own material is kept under the new name; otherwise it comes from the first gear source that has it (template_materials,
the one rule the natives' <id>.src.glb is written by too).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MATERIALS = os.path.join(REPO, "godot", "art", "people", "outfit_materials.json")
INDEXES = {"armor": os.path.join(REPO, "godot", "art", "armor", "armor_index.json"),
           "outfit": os.path.join(REPO, "godot", "art", "people", "armor_index.json")}
KEY = "finish"


def template_materials(want, to_dir, table, sources):
    """({key: glTF material}, tail or None) for the keys `want`: each key's material is its template's (table row
    "template", else the key itself) from the first of `sources` [(gltf path, json)] that has it, under the key's own
    name, its textures listed in tail {textures, images, samplers} with uris relative to to_dir. A key no source
    carries is absent from the result."""
    mats, tail = {}, {"textures": [], "images": [], "samplers": [{"magFilter": 9729, "minFilter": 9987}]}
    want = set(want)
    alias = {}
    for k in want:
        alias.setdefault(table.get(k, {}).get("template", k), []).append(k)
    for f, js in sources:
        for m0 in js.get("materials", []):
            todo = [k for k in alias.get(m0.get("name"), ()) if k not in mats]
            if not todo:
                continue

            def fix(o, f=f, js=js):
                if isinstance(o, dict):
                    o = {k: fix(v) for k, v in o.items()}
                    if isinstance(o.get("index"), int):
                        im = dict(js["images"][js["textures"][o["index"]]["source"]])
                        im["uri"] = os.path.relpath(os.path.join(os.path.dirname(f), im["uri"]), to_dir).replace("\\", "/")
                        tail["images"].append(im)
                        tail["textures"].append({"sampler": 0, "source": len(tail["images"]) - 1})
                        o["index"] = len(tail["textures"]) - 1
                    return o
                return [fix(v) for v in o] if isinstance(o, list) else o
            for k in todo:   # (each key its own copy: the images are listed once a copy, by uri)
                mats[k] = fix(json.loads(json.dumps(dict(m0, name=k))))
        if want <= set(mats):
            break
    return mats, (tail if tail["textures"] else None)


def record(bd):
    """The piece's live record: a native's piece.json, else its row in the armor index of its kind (the binding's
    stored row when the index has none, as for a calling's lod unit)."""
    meta = bd.meta
    stored = meta.get("row") or {}
    p = os.path.join(REPO, meta["native_dir"], "piece.json") if meta.get("native_dir") else INDEXES.get(meta.get("kind"))
    if not p or not os.path.exists(p):
        return stored
    js = json.load(open(p, encoding="utf-8"))
    if isinstance(js, dict):
        return js
    return next((r for r in js if r.get("id") == bd.id), stored)


def _merge(m, tail, texs, imgs, smps):
    """m (texture indices into tail) re-indexed into the unit's own texture, image and sampler lists."""
    if not tail:
        return m
    so, io, to = len(smps), len(imgs), len(texs)
    smps.extend(tail["samplers"])
    imgs.extend(tail["images"])
    texs.extend({"sampler": t["sampler"] + so, "source": t["source"] + io} for t in tail["textures"])

    def fix(o):
        if isinstance(o, dict):
            o = {k: fix(v) for k, v in o.items()}
            if isinstance(o.get("index"), int):
                o["index"] += to
            return o
        return [fix(v) for v in o] if isinstance(o, list) else o
    return fix(m)


def apply(bd, mats, texs, imgs, smps, meshes, out_dir, finish=None, table=None, sources=None):
    """The record's finish on a unit about to be written (the lists are write_unit's, changed in place): returns
    {source name: key} for what it renamed. Nothing is touched when the record has no finish."""
    fin = record(bd).get(KEY) if finish is None else finish
    if not fin:
        return {}
    names = [m.get("name") for m in mats]
    stray = sorted(set(fin) - set(names))
    if stray:
        raise SystemExit(f"gear_finish: {bd.id}: \"{KEY}\" maps {stray}, not a material of the piece (it has {sorted(set(names))})")
    table = json.load(open(MATERIALS, encoding="utf-8")) if table is None else table
    done = {}
    for mi, old in enumerate(names):
        key = fin.get(old)
        if key is None or key == old:
            continue
        if key not in table:
            raise SystemExit(f"gear_finish: {bd.id}: \"{KEY}\" {old} -> '{key}': no such key in outfit_materials.json")
        if table[key].get("template", key) == old:
            body = dict(mats[mi], name=key)
        else:
            if sources is None:
                import gear_native
                sources = list(gear_native.material_templates())
            got, tail = template_materials({key}, out_dir, table, sources)
            if key not in got:
                raise SystemExit(f"gear_finish: {bd.id}: \"{KEY}\" {old} -> '{key}': no gear source carries "
                                 f"'{table[key].get('template', key)}' to draw it from")
            body = _merge(got[key], tail, texs, imgs, smps)
        mats[mi] = body
        done[old] = key
        for me in meshes:
            ex = me.get("extras") or {}
            if ex.get("material") == old and any(p.get("material") == mi for p in me["primitives"]):
                me["extras"] = dict(ex, material=key)
    return done
