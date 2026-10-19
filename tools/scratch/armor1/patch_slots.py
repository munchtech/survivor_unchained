# Slots in heroine_outfits.py: the slot map helpers, per-slot tucks, the export per (slot, material), the index (CRLF kept).
import sys
p = sys.argv[1]
src = open(p, encoding="utf-8", newline="").read()
NL = "\r\n"


def sub(old, new, count=1):
    global src
    old, new = old.replace("\n", NL), new.replace("\n", NL)
    assert src.count(old) == count, (src.count(old), old[:120])
    src = src.replace(old, new)


HELPERS = r'''# ------------------------------------------------------------------ slots --
# (armor lead 1, 18 Oct: docs/handoff/armor.md section 1.) Each piece of hers is one slot's
# (tools/armor/slot_map.json): her outfits are exported a mesh per (slot, material), named
# <outfit>.<slot>.<material>, so the game can wear any outfit's pieces by slot and mix them; each
# (outfit, slot) carries its own tuck of her skin (armor_tuck/<outfit>.<slot>.bin) beside the four
# outfit channels, and armor_index.json lists them.
import hashlib
import json as _json
import struct as _struct
ARMOR_MAP = _json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "armor", "slot_map.json"), encoding="utf-8"))
ARMOR_RE = {o: [(e, [re.compile(r) for r in e["match"]]) for e in es] for o, es in ARMOR_MAP["outfits"].items()}


def slot_entry(name):
    """The slot map's entry for a built piece `<outfit>.<piece>` (None: no entry or more than one)."""
    o, _, pc = name.partition(".")
    hits = [e for e, rs in ARMOR_RE.get(o, []) if any(r.fullmatch(pc) for r in rs)]
    return hits[0] if len(hits) == 1 else None


def slot_check(objs, when):
    """The build fails naming every piece that maps to no slot, or to more than one."""
    bad = []
    for o in objs:
        out, _, pc = o.name.partition(".")
        hits = [e["slot"] for e, rs in ARMOR_RE.get(out, []) if any(r.fullmatch(pc) for r in rs)]
        if len(hits) != 1:
            bad.append("%s -> %s" % (o.name, hits or "no slot"))
    if bad:
        raise RuntimeError("SLOTS (%s): %d pieces not mapped to exactly one slot in tools/armor/slot_map.json: %s" % (when, len(bad), "; ".join(bad)))
    print("SLOTS (%s): all %d pieces mapped" % (when, len(objs)))


ARMOR_TUCK = {}      # (outfit, slot) -> her skin's tuck, a value a vertex of her body
ARMOR_TUCK_N = {}    # (outfit, slot) -> records written
ARMOR_BODY_HASH = None


def armor_tuck_write(body_obj, folder):
    """Each (outfit, slot)'s tuck, sparse: u32 count, then count records (i32 x, i32 y, i32 z: her body
    vertex's bind position, glTF Y-up metres x 1e5 rounded; f32 tuck), little-endian; only tuck > 0,
    one record a position (her split skin's copies at one point: the largest of their tucks). And
    ARMOR_BODY_HASH: sha1 of her body's bind positions so rounded, unique, sorted, as i32 little-endian."""
    global ARMOR_BODY_HASH
    me_ = body_obj.data
    bp = np.array([(body_obj.matrix_world @ v.co)[:] for v in me_.vertices])
    q = np.round(np.stack([bp[:, 0], bp[:, 2], -bp[:, 1]], 1) * 1e5).astype(np.int64)
    uq, inv = np.unique(q, axis=0, return_inverse=True)
    inv = np.asarray(inv).ravel()
    ARMOR_BODY_HASH = hashlib.sha1(uq.astype("<i4").tobytes()).hexdigest()
    os.makedirs(os.path.join(folder, "armor_tuck"), exist_ok=True)
    for (out, slot), t in sorted(ARMOR_TUCK.items()):
        assert len(t) == len(me_.vertices), "her body's vertices changed after the tuck"
        g = np.zeros(len(uq))
        np.maximum.at(g, inv, t)
        k = np.nonzero(g > 0)[0]
        rec = np.zeros(len(k), dtype=[("x", "<i4"), ("y", "<i4"), ("z", "<i4"), ("t", "<f4")])
        rec["x"], rec["y"], rec["z"], rec["t"] = uq[k, 0], uq[k, 1], uq[k, 2], g[k]
        with open(os.path.join(folder, "armor_tuck", f"{out}.{slot}.bin"), "wb") as f_:
            f_.write(_struct.pack("<I", len(k)) + rec.tobytes())
        ARMOR_TUCK_N[(out, slot)] = int(len(k))
    print("ARMOR TUCK: %d (outfit, slot) tucks written, her body %s" % (len(ARMOR_TUCK), ARMOR_BODY_HASH))


def tuck_of(name, objs, slot=None):'''
sub("def tuck_of(name, objs, slot=None):", HELPERS)

# Per-slot tucks, after the four channels.
sub('''        vals[:, k] = tuck_of(name, objs)[0]
    col.data.foreach_set("color", vals.ravel())''', '''        vals[:, k] = tuck_of(name, objs)[0]
    # (armor lead 1: and each (outfit, slot)'s own, from its hiding pieces by the same rule)
    slot_check([o for o in made if o.name.partition(".")[0] in OUTFITS], "tuck")
    for _aout in OUTFITS:
        _ahides = [o for o in made if o.name.startswith(_aout + ".") and o.get("hides")]
        for _aslot in sorted({slot_entry(o.name)["slot"] for o in made if o.name.startswith(_aout + ".")}):
            _aobjs = [o for o in _ahides if slot_entry(o.name)["slot"] == _aslot]
            ARMOR_TUCK[(_aout, _aslot)] = tuck_of(_aout, _aobjs, _aslot)[0] if _aobjs else np.zeros(len(me.vertices))
        _ak = CHANNELS.index(_aout)
        if _ak <= 3:
            _amx = np.max([t_ for (o_, s_), t_ in ARMOR_TUCK.items() if o_ == _aout], 0)
            _afull = vals[:, _ak] > 0.973
            _alost = _afull & (_amx <= 0.973)
            _adrop = vals[:, _ak] - _amx
            print("ARMOR TUCK %s: %d vertices full in its channel, %d of them not full in any slot (largest drop %.3f); "
                  "%d tucked deeper by a slot than by the channel (largest rise %.3f), %d of them full in a slot only"
                  % (_aout, int(_afull.sum()), int(_alost.sum()), float(_adrop.max()), int((_adrop < -1e-6).sum()),
                     float(-_adrop.min()), int(((_amx > 0.973) & ~_afull).sum())))
    col.data.foreach_set("color", vals.ravel())''')

# The tuck files, from her body as exported.
sub('''    bpy.ops.export_scene.gltf(filepath=BODY_OUT, export_format="GLB", use_selection=True, export_skins=True, export_animations=False,
                              export_yup=True, export_vertex_color="ACTIVE")
''', '''    bpy.ops.export_scene.gltf(filepath=BODY_OUT, export_format="GLB", use_selection=True, export_skins=True, export_animations=False,
                              export_yup=True, export_vertex_color="ACTIVE")
    armor_tuck_write(body, os.path.dirname(OUT))
''')

# The export: a mesh per (slot, material).
sub('''pieces_of = {name: [o for o in made if o.name.startswith(name + ".")] for name in OUTFITS}
for name in OUTFITS:''', '''pieces_of = {name: [o for o in made if o.name.startswith(name + ".")] for name in OUTFITS}
slot_check([o for v_ in pieces_of.values() for o in v_], "export")
ARMOR_ROWS = []
for name in OUTFITS:''')
sub('''    joined = []
    for key, objs in by_mat.items():
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        if len(objs) > 1:
            # (her corrective shapes kept through the join: heroine_rig)
            rig_helpers.share_keys(objs)
            bpy.ops.object.join()
        objs[0].name = objs[0].data.name = f"{name}.{key}"
        joined.append(objs[0])
    print("MERGED", name, len(mine), "pieces into", len(joined), "meshes")''', '''    joined = []
    ranks = {}
    for key, objs in by_mat.items():
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        # (armor lead 1: a mesh per (slot, material), <outfit>.<slot>.<material>. Each slot's pieces are
        # joined in the order one join of the material's took them, the active piece and then the rest as
        # the view layer lists them, so the slots' meshes laid end to end in rank order are that one mesh:
        # heroine_lod.py joins them back so)
        order = [objs[0]] + [o for o in bpy.context.view_layer.objects if o.select_get() and o is not objs[0]]
        assert len(order) == len(objs)
        by_slot = {}
        for o in order:
            by_slot.setdefault(slot_entry(o.name)["slot"], []).append(o)
        seq = [slot_entry(o.name)["slot"] for o in order]
        runs = sum(1 for i_ in range(len(seq)) if i_ == 0 or seq[i_] != seq[i_ - 1])
        if runs != len(by_slot):
            print("SLOT ORDER %s.%s: its slots interleave in the join (%d runs of %d slots): the LOD's join differs" % (name, key, runs, len(by_slot)))
        for rank, (slot, sobjs) in enumerate(by_slot.items()):
            bpy.ops.object.select_all(action="DESELECT")
            for o in sobjs:
                o.select_set(True)
            bpy.context.view_layer.objects.active = sobjs[0]
            if len(sobjs) > 1:
                # (her corrective shapes kept through the join: heroine_rig)
                rig_helpers.share_keys(sobjs)
                bpy.ops.object.join()
            sobjs[0].name = sobjs[0].data.name = f"{name}.{slot}.{key}"
            joined.append(sobjs[0])
            ranks[sobjs[0].name] = {"outfit": name, "slot": slot, "material": key, "rank": rank}
    print("MERGED", name, len(mine), "pieces into", len(joined), "meshes")''')
sub('''        heroine_neck.match_pieces(path, heroine_neck.field())
    print("OUTFIT", name, len(mine), "pieces,", sum(len(o.data.polygons) for o in mine), "faces ->", path)''', '''        heroine_neck.match_pieces(path, heroine_neck.field())
    # (each mesh's slot, material and rank in its material's join, as glTF extras: heroine_lod.py and the game read them)
    g_ = _json.load(open(path, encoding="utf-8"))
    for m_ in g_["meshes"]:
        if m_["name"] in ranks:
            m_["extras"] = dict(m_.get("extras", {}), **ranks[m_["name"]])
    _json.dump(g_, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    slots_ = {}
    for mn_, r_ in ranks.items():
        slots_.setdefault(r_["slot"], []).append(mn_)
    for slot, meshes_ in sorted(slots_.items()):
        e_ = next(e for e in ARMOR_MAP["outfits"][name] if e["slot"] == slot)
        tk_ = (name, slot) in ARMOR_TUCK_N
        ARMOR_ROWS.append({"id": f"{name}.{slot}", "outfit": name, "slot": slot, "layer": ARMOR_MAP["layers"][slot],
                           "covers": e_.get("covers", [slot]), "meshes": sorted(meshes_),
                           "tuck": f"armor_tuck/{name}.{slot}.bin" if tk_ else None,
                           "tuck_count": ARMOR_TUCK_N.get((name, slot)), "body_hash": ARMOR_BODY_HASH})
    print("OUTFIT", name, len(mine), "pieces,", sum(len(o.data.polygons) for o in mine), "faces ->", path)''')
src = src.rstrip(NL) + NL + '''# (armor lead 1: one row per (outfit, slot); body_hash as armor_tuck_write has it)
_json.dump(ARMOR_ROWS, open(os.path.join(os.path.dirname(OUT), "armor_index.json"), "w", encoding="utf-8"), indent=1)
print("ARMOR INDEX: %d (outfit, slot) rows -> %s" % (len(ARMOR_ROWS), os.path.join(os.path.dirname(OUT), "armor_index.json")))
'''.replace("\n", NL)
open(p, "w", encoding="utf-8", newline="").write(src)
print("patched")
