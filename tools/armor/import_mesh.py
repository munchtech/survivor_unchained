"""A free mesh made a piece on her (armor 9, IM1): docs/armor/PIECE_SCHEMA.md "Free meshes: the import contract".

    python tools/armor/import_mesh.py <piece dir> [--check | --install [--item ["Name"]]] [--refit] [--src <heroine_built.blend>]

<piece dir> holds piece.json ("style": "mesh", "params": {"file": "<id>.glb"}) and the mesh (.glb/.gltf preferred;
.fbx and .blend open in Blender). Marionette's generated/to_game/armor/<id>/ or an artist's folder; the game's copy
lives in godot/art/armor/src/<id>/.

Stages:
  1. check (here, before Blender): piece.json fields and slot; for a glTF: identity node transforms, units (its size),
     bounds overlapping her body (heroine.glb), every material name an outfit_materials.json entry, a skin only on her
     skeleton's bones, the slot's triangle budget. Each refusal says what it found and what to do.
  2. body: the sha1 of godot/art/people/heroine.glb (the body the contract says to model on) is stamped into the game's
     piece.json as "body_sha1"; a source stamped with another refuses unless --refit (re-fitted on purpose).
  3. copy into godot/art/armor/src/<id>/ (piece.json + the mesh).
  4. without --install: a proof build into the scratch dir only (ARMOR_SCRATCH_ONLY: numbers and tuck, nothing in
     godot/art). With --install: tools/armor/build.py's build (tools/armor/piece_blender.py, style "mesh": her weights,
     `_rigid` parts on one blend from her skin at their centre, mirror, the push-out to the slot band, her tuck, the
     post steps, sockets from named empties and rims from open edges, the glTF, the armor_index row with "rigid"),
     its LODs (piece_lod.py), then cover.py's footprint for the garment tuck; --item adds its item to items.json
     (tools/armor/drop.py's add_item; the piece's name unless one is given).
Take a blender turn first (tools/turn.py take blender ...).
"""
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import build  # noqa: E402

BODY = os.path.join(ROOT, "godot", "art", "people", "heroine.glb")
MATS = os.path.join(ROOT, "godot", "art", "people", "outfit_materials.json")
SKEL = os.path.join(ROOT, "tools", "anim", "data", "heroine_skeleton.json")
SLOTS = ["top", "bottom", "legwear", "gloves", "skirt", "belt", "collar", "bracers", "greaves", "boots", "pauldrons", "cloak", "head"]
# (the contract's budgets: 30k a large piece, 15-20k a pair, 15k head, 8k small)
BUDGET = {"top": 30000, "cloak": 30000, "skirt": 30000, "legwear": 30000, "bottom": 20000, "pauldrons": 20000, "bracers": 20000,
          "greaves": 20000, "boots": 20000, "gloves": 20000, "head": 15000, "belt": 8000, "collar": 8000}


def refuse(msg):
    print("IMPORT REFUSED: " + msg)
    sys.exit(2)


def read_gltf(path):
    raw = open(path, "rb").read()
    if raw[:4] == b"glTF":
        n = struct.unpack("<I", raw[12:16])[0]
        return json.loads(raw[20:20 + n])
    return json.loads(raw.decode("utf-8"))


def bounds(g, skinned_only=False):
    lo, hi = [9e9] * 3, [-9e9] * 3
    for m in g.get("meshes", []):
        for pr in m["primitives"]:
            if skinned_only and "JOINTS_0" not in pr["attributes"]:
                continue
            a = g["accessors"][pr["attributes"]["POSITION"]]
            lo = [min(x, y) for x, y in zip(lo, a["min"])]
            hi = [max(x, y) for x, y in zip(hi, a["max"])]
    return lo, hi


def triangles(g):
    t = 0
    for m in g.get("meshes", []):
        for pr in m["primitives"]:
            if pr.get("mode", 4) != 4:
                continue
            t += (g["accessors"][pr["indices"]]["count"] if "indices" in pr else g["accessors"][pr["attributes"]["POSITION"]]["count"]) // 3
    return t


def check_gltf(path, piece):
    g = read_gltf(path)
    name = os.path.basename(path)
    out = {}
    # transforms applied
    for nd in g.get("nodes", []):
        bad = (nd.get("translation", [0, 0, 0]) != [0, 0, 0] and any(abs(x) > 1e-6 for x in nd["translation"])) or \
              ("rotation" in nd and any(abs(x - y) > 1e-6 for x, y in zip(nd["rotation"], [0, 0, 0, 1]))) or \
              ("scale" in nd and any(abs(x - 1) > 1e-6 for x in nd["scale"])) or \
              ("matrix" in nd and any(abs(x - y) > 1e-6 for x, y in zip(nd["matrix"], [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1])))
        if bad and "mesh" in nd:
            refuse("%s: node %r has a transform (%s); apply all transforms (identity objects) and export again"
                   % (name, nd.get("name"), {k: nd[k] for k in ("translation", "rotation", "scale", "matrix") if k in nd}))
    lo, hi = bounds(g)
    size = [h - l for l, h in zip(lo, hi)]
    if max(size) > 3.0 or max(size) < 0.005:
        refuse("%s: %.3f x %.3f x %.3f m across; the contract is metres (a piece is 0.5 cm to 3 m): check the export's units"
               % (name, *size))
    blo, bhi = bounds(read_gltf(BODY), skinned_only=True)
    if any(h < bl or l > bh for l, h, bl, bh in zip(lo, hi, blo, bhi)):
        off = [round((l + h) / 2 - (bl + bh) / 2, 3) for l, h, bl, bh in zip(lo, hi, blo, bhi)]
        refuse("%s: its bounds %s..%s miss her body %s..%s (centre offset %s m, glTF axes: +Y up, front +Z, her left +X, "
               "feet on y = 0); model it on heroine.glb as it stands" % (name, [round(x, 3) for x in lo], [round(x, 3) for x in hi],
                                                                          [round(x, 3) for x in blo], [round(x, 3) for x in bhi], off))
    valid = sorted(json.load(open(MATS, encoding="utf-8")))
    used = sorted({g["materials"][pr["material"]].get("name") if "material" in pr else None
                   for m in g.get("meshes", []) for pr in m["primitives"]}, key=str)
    unknown = [u for u in used if u not in valid]
    if unknown:
        refuse("%s: material name(s) %s are not entries of outfit_materials.json; name each material slot one of: %s"
               % (name, unknown, ", ".join(valid)))
    if g.get("skins"):
        bones = set(json.load(open(SKEL, encoding="utf-8"))["bones"])
        names = {g["nodes"][j].get("name") for s in g["skins"] for j in s["joints"]}
        alien = sorted(n for n in names if n not in bones and n not in ("Armature", "root"))
        if alien:
            refuse("%s: skinned to bones that are not hers (%s); skin it to tools/anim/data/heroine_skeleton.json's bones, "
                   "or leave it unskinned (the import gives it her weights)" % (name, alien[:8]))
    tri = triangles(g)
    cap = BUDGET[piece["slot"]] * (1 if not piece.get("params", {}).get("mirror") else 0.5)
    if tri > cap:
        refuse("%s: %d triangles, over the %s slot's budget of %d%s" % (name, tri, piece["slot"], cap, " (mirrored: half)" if cap != BUDGET[piece["slot"]] else ""))
    out.update(triangles=tri, materials=used, bounds=[[round(x, 3) for x in lo], [round(x, 3) for x in hi]],
               rigid=sorted(nd["name"] for nd in g.get("nodes", []) if "mesh" in nd and nd.get("name", "").endswith("_rigid")),
               bending=sorted(nd.get("name", "?") for nd in g.get("nodes", []) if "mesh" in nd and not nd.get("name", "").endswith("_rigid")),
               sockets=sorted(nd["name"] for nd in g.get("nodes", []) if "mesh" not in nd and "children" not in nd and "skin" not in nd and nd.get("name")),
               body_sha1=(g.get("asset", {}).get("extras") or {}).get("body_sha1"))
    return out


def main(argv):
    if not argv or argv[0].startswith("--"):
        print(__doc__)
        sys.exit(1)
    src_dir = os.path.abspath(argv[0])
    pj = os.path.join(src_dir, "piece.json")
    if not os.path.exists(pj):
        refuse("%s has no piece.json" % src_dir)
    piece = json.load(open(pj, encoding="utf-8"))
    import re
    for k in ("id", "name", "slot", "style", "params"):
        if k not in piece:
            refuse("piece.json has no %r" % k)
    pid = piece["id"]
    if not re.fullmatch(r"[a-z0-9_]+", pid):
        refuse("id %r: [a-z0-9_]+ only" % pid)
    if piece["style"] != "mesh":
        refuse("style %r: a free mesh's piece.json has \"style\": \"mesh\" (procedural styles build with tools/armor/build.py)" % piece["style"])
    if piece["slot"] not in SLOTS:
        refuse("slot %r is not one of %s" % (piece["slot"], SLOTS))
    if piece.get("base"):
        refuse("a free mesh has no base (base is for a tier variant of a built shell)")
    mesh = os.path.join(src_dir, piece["params"].get("file", ""))
    if not os.path.isfile(mesh):
        refuse("params.file %r is not beside piece.json" % piece["params"].get("file"))
    ext = os.path.splitext(mesh)[1].lower()
    if ext not in (".glb", ".gltf", ".fbx", ".blend"):
        refuse("%s: the mesh is .glb (preferred), .gltf, .fbx or .blend" % os.path.basename(mesh))
    info = check_gltf(mesh, piece) if ext in (".glb", ".gltf") else {"note": "fbx/blend: checked in Blender (materials, budget by the build)"}
    # body: the file she is modelled on
    sha = hashlib.sha1(open(BODY, "rb").read()).hexdigest()
    stamped = piece.get("body_sha1") or info.get("body_sha1")
    if stamped and stamped != sha and "--refit" not in argv:
        refuse("made on body %s, the current heroine.glb is %s: re-fit it on the current body (then --refit)" % (stamped[:12], sha[:12]))
    print("IMPORT CHECK %s: %s" % (pid, json.dumps(info)))
    # the game's copy
    dst = os.path.join(ROOT, "godot", "art", "armor", "src", pid)
    os.makedirs(dst, exist_ok=True)
    if os.path.abspath(dst) != src_dir:
        shutil.copyfile(mesh, os.path.join(dst, os.path.basename(mesh)))
    piece["body_sha1"] = sha
    json.dump(piece, open(os.path.join(dst, "piece.json"), "w", encoding="utf-8", newline="\n"), indent=1)
    src_blend = argv[argv.index("--src") + 1] if "--src" in argv else build.SRC
    if "--check" in argv:
        return
    num = os.path.join(ROOT, ".shots", "armor2", "build", pid, "numbers.json")
    if "--install" in argv:
        ok = build.build(pid, src_blend)
    else:
        # (a proof: piece_blender with ARMOR_SCRATCH_ONLY, numbers and her tuck into the scratch dir, nothing in godot/art)
        scratch = os.path.dirname(num)
        os.makedirs(scratch, exist_ok=True)
        if os.path.exists(num):
            os.remove(num)
        with open(os.path.join(scratch, "build.log"), "w", encoding="utf-8") as fh:
            subprocess.run([build.BLENDER, "-b", src_blend, "--python", os.path.join(HERE, "piece_blender.py"), "--",
                            os.path.join(dst, "piece.json"), scratch], cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT,
                           stdin=subprocess.DEVNULL, env=dict(os.environ, ARMOR_SCRATCH_ONLY="1"))
        ok = os.path.exists(num)
        print("PROOF %s: %s (log %s)" % (pid, "ok" if ok else "FAILED", os.path.join(scratch, "build.log")))
    if ok and "--install" in argv:
        r = subprocess.run([sys.executable, os.path.join(HERE, "cover.py"), "--pieces", pid], cwd=ROOT, capture_output=True, text=True)
        print((r.stdout + r.stderr).strip()[-600:])
        ok = r.returncode == 0
        if ok and "--item" in argv:
            # (its item in items.json, as tools/armor/drop.py --item adds one; skipped if an item already wears it)
            import drop
            nxt = argv[argv.index("--item") + 1] if argv.index("--item") + 1 < len(argv) else ""
            drop.add_item(piece, nxt if nxt and not nxt.startswith("--") else piece["name"])
    if os.path.exists(num):
        n = json.load(open(num, encoding="utf-8"))
        im = n.get("import", {})
        print("IMPORT NUMBERS %s: %s" % (pid, json.dumps({"triangles": n.get("triangles"), "materials": n.get("materials"),
                                                          "push_to_band_mm": im.get("push_to_band_mm"), "band_mm": im.get("band_mm"),
                                                          "pose_push_mm": (n.get("push_out") or {}).get("total_mm"),
                                                          "rigid_parts": im.get("rigid_parts"), "bending_parts": im.get("bending_parts"),
                                                          "rigid": im.get("rigid"), "sockets": im.get("sockets"), "rims": im.get("rims"),
                                                          "tuck_records": n.get("tuck_records")})))
    print("IMPORT %s: %s" % (pid, "ok" if ok else "FAILED"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
