"""Publish Marionette's "switch package" (her body B's copy on the shared house mesh) into the game as a new body folder.

    python tools/body/publish_house.py <package_dir> [--import] [--out-root DIR]

Why: the game wears her on B (godot/art/people/body_p1, tools/body/publish_p1.py). The switch moves her to the shared mesh
(body.glb of the package, shaped like B), loaded from its own folder godot/art/people/body_p1_house/ by data/body/her_body.json
"dir" (P1Body.PickDir); B's folder stays as it is, for side by side (--p1-dir res://art/people/body_p1/). One command, re-runnable
with a newer package: it clears what it wrote before and writes again; nothing in the folders is edited by hand.

Package (a directory): body.glb (mesh node "Heroine", primitives "skin" and "eyes", no morphs, B's 124 bones), tuck/<id>.bin and
optionally cover/<id>.bin (tuck-record format: int32 count, then per record int32 x, y, z = bind position m * 1e5, float32 mark),
dressed.glb (reference only, not copied), skeleton_check.json, manifest.json (sha1 and size of every file; verified here).

Writes (derivation: what each B file is and whether it is right on the copy):
  body_p1_house/   body.glb from the package. NO play.glb: one tier on purpose, so P1Body.Load runs with no play tier.
                   Copied unchanged from body_p1: clips.res, her_clips.res, a_skeleton.json, rig_helpers.json, blend_base.json
                   (bone-space data of the same 124 bones). NOT copied: any .png, pieces.glb, pieces.json, play.glb,
                   play_rig.json, bake.json (B's UV maps or B's mesh data: wrong on the copy).
                   rig.json = B's with "correctives" removed (the copy has no corrective shapes; the owner agreed to drop B's
                   30 joint correctives in the game) and "close_meshes" [] (no head piece closes the copy).
                   publish.json: source, manifest sha1, each file's sha1, what came from B, what was dropped, B's skin block.
                   body.glb.import: made from body_p1's if absent, then set to A's glb import params (publish_p1.import_params).
  gear/out/body_p1_house/   gear_index.json: B's index, "body" and "body_hash" the copy's, every row kept; their "file" fields
                   stay B's gear files on purpose (the copy's surface is B's to the eye). A row's tuck is the package's
                   tuck/<id>.bin copied to armor_tuck/ (tuck_count from the file); none in the package: tuck null, count 0 and
                   listed. kit_helm keeps tuck null (B hides no skin under the helm). A cover is the package's cover/<id>.bin
                   copied to armor_cover/ (cover_count from it); none: cover_count dropped, no file. "house" block: the audit.
--import takes a Godot turn (tools/turn.py) and runs Godot 4.7.2's headless import. --out-root DIR writes under DIR instead of
the repo root (a self-test's scratch: DIR/godot/art/...; the B folders are still read from the repo).
"""
from __future__ import annotations

import json
import os
import shutil
import struct
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import publish_p1 as p1                      # sha1, glb_json, body_material, import_params, write_import

ROOT = p1.ROOT
B_PEOPLE = os.path.join(ROOT, "godot", "art", "people", "body_p1")
B_GEAR = os.path.join(ROOT, "godot", "art", "gear", "out", "body_p1")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.7.2-stable_mono_win64\Godot_v4.7.2-stable_mono_win64_console.exe"
TURN = p1.TURN
FROM_B = ("clips.res", "her_clips.res", "a_skeleton.json", "rig_helpers.json", "blend_base.json")
NO_TUCK = ("kit_helm",)


def fail(msg):
    raise SystemExit(f"publish_house: {msg}")


def verify_manifest(pkg):
    mp = os.path.join(pkg, "manifest.json")
    if not os.path.exists(mp):
        fail(f"{pkg} has no manifest.json")
    man = json.load(open(mp, encoding="utf-8"))
    print(f"publish_house: manifest keys: {sorted(man.keys()) if isinstance(man, dict) else type(man).__name__}")
    # layouts tolerated: {"files": {name: sha1 | {"sha1", "size"}}}, {"files": [{"path"|"name", "sha1", "size"}]}, or the map itself
    ent = man.get("files", man) if isinstance(man, dict) else man
    rows = []
    if isinstance(ent, dict):
        for k, v in ent.items():
            if isinstance(v, dict):
                rows.append((k, v.get("sha1"), v.get("size")))
            elif isinstance(v, str) and len(v) == 40:
                rows.append((k, v, None))
    elif isinstance(ent, list):
        for v in ent:
            if isinstance(v, dict):
                rows.append((v.get("path") or v.get("name") or v.get("file"), v.get("sha1"), v.get("size")))
    rows = [r for r in rows if r[0] and r[1]]
    if not rows:
        fail("manifest.json names no file with a sha1 (layout unknown; keys printed above)")
    for name, h, size in rows:
        p = os.path.join(pkg, name)
        if not os.path.exists(p):
            if name.endswith("manifest.json"):
                continue
            fail(f"manifest names {name}, not in the package")
        if p1.sha1(p) != h:
            fail(f"SHA1 MISMATCH {name}: manifest {h}, file {p1.sha1(p)}")
        if size is not None and os.path.getsize(p) != int(size):
            fail(f"SIZE MISMATCH {name}: manifest {size}, file {os.path.getsize(p)}")
    print(f"publish_house: manifest verified ({len(rows)} files)")
    return p1.sha1(mp)


def check_glb(path):
    g = p1.glb_json(path)
    node = next((n for n in g.get("nodes", []) if n.get("name") == "Heroine" and "mesh" in n), None)
    if node is None:
        fail("body.glb has no node 'Heroine' with a mesh")
    prims = g["meshes"][node["mesh"]]["primitives"]
    m = g["materials"][prims[0]["material"]]
    if "baseColorTexture" not in m.get("pbrMetallicRoughness", {}):
        fail("body.glb's first primitive's material has no baseColorTexture")
    if "normalTexture" not in m:
        print("publish_house: WARNING: body.glb's skin material has no normalTexture")
    counts = [g["accessors"][p["attributes"]["POSITION"]]["count"] for p in prims]
    morphs = max((len(p.get("targets", [])) for p in prims), default=0)
    names = [g["materials"][p["material"]].get("name") for p in prims]
    print(f"publish_house: body.glb primitives {list(zip(names, counts))}, morph targets {morphs}")


def record_count(path):
    with open(path, "rb") as f:
        b = f.read(4)
    return struct.unpack("<i", b)[0] if len(b) == 4 else 0


def clear_files(folder, keep_ext=(".import",)):
    """Remove the files an earlier run wrote (not *.import); the folder is this tool's own."""
    if os.path.isdir(folder):
        for f in os.listdir(folder):
            p = os.path.join(folder, f)
            if os.path.isfile(p) and not f.endswith(keep_ext):
                os.remove(p)


def rewrite_gear_index(b_index, pkg, gear_out, body_hash, manifest_sha1):
    """B's gear index for the copy: a new dict (the input untouched); copies the tuck and cover files under gear_out."""
    ix = json.loads(json.dumps(b_index))
    ix["body"] = "body_p1_house"
    ix["body_hash"] = body_hash
    for sub in ("armor_tuck", "armor_cover"):
        d = os.path.join(gear_out, sub)
        if os.path.isdir(d):
            shutil.rmtree(d)
    os.makedirs(os.path.join(gear_out, "armor_tuck"), exist_ok=True)
    tucked, untucked, covered = [], [], []
    for row in ix["rows"]:
        rid = row["id"]
        cov = os.path.join(pkg, "cover", rid + ".bin")
        if os.path.exists(cov):
            os.makedirs(os.path.join(gear_out, "armor_cover"), exist_ok=True)
            shutil.copy2(cov, os.path.join(gear_out, "armor_cover", rid + ".bin"))
            row["cover_count"] = record_count(cov)
            covered.append(rid)
        else:
            row.pop("cover_count", None)
        if not row.get("tuck"):
            continue
        tk = os.path.join(pkg, "tuck", rid + ".bin")
        if rid not in NO_TUCK and os.path.exists(tk):
            shutil.copy2(tk, os.path.join(gear_out, "armor_tuck", rid + ".bin"))
            row["tuck"] = f"armor_tuck/{rid}.bin"
            row["tuck_count"] = record_count(tk)
            tucked.append(rid)
        else:
            row["tuck"] = None
            row["tuck_count"] = 0
            untucked.append(rid)
    ix["house"] = {"package": pkg.replace("\\", "/"), "manifest_sha1": manifest_sha1, "rows_tucked": tucked,
                   "rows_untucked": untucked, "rows_covered": covered}
    return ix


def publish(pkg, root):
    pkg = os.path.abspath(pkg)
    msha = verify_manifest(pkg)
    body = os.path.join(pkg, "body.glb")
    if not os.path.exists(body):
        fail(f"{pkg} has no body.glb")
    check_glb(body)
    pub = os.path.join(root, "godot", "art", "people", "body_p1_house")
    gear_out = os.path.join(root, "godot", "art", "gear", "out", "body_p1_house")
    os.makedirs(pub, exist_ok=True)
    os.makedirs(gear_out, exist_ok=True)
    clear_files(pub)
    shutil.copy2(body, os.path.join(pub, "body.glb"))
    files = {"body.glb": p1.sha1(os.path.join(pub, "body.glb"))}
    for f in FROM_B:
        shutil.copy2(os.path.join(B_PEOPLE, f), os.path.join(pub, f))
        files[f] = p1.sha1(os.path.join(pub, f))
    rig = json.load(open(os.path.join(B_PEOPLE, "rig.json"), encoding="utf-8"))
    rows = rig.pop("correctives", [])
    shapes = sum(len(r.get("shapes", [])) for r in rows)
    rig["close_meshes"] = []
    with open(os.path.join(pub, "rig.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(rig, f, indent=1)
    files["rig.json"] = p1.sha1(os.path.join(pub, "rig.json"))
    bpub = json.load(open(os.path.join(B_PEOPLE, "publish.json"), encoding="utf-8"))
    # body.glb.import: from B's when absent
    gi = os.path.join(pub, "body.glb.import")
    if not os.path.exists(gi):
        src = os.path.join(B_PEOPLE, "body.glb.import")
        if os.path.exists(src):
            lines = open(src, encoding="utf-8").read().split("\n")
            lines = [l.replace("body_p1/", "body_p1_house/") for l in lines if not l.startswith("uid=")]
            with open(gi, "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(lines))
    params = p1.import_params()
    out = {"source": pkg.replace("\\", "/"), "manifest_sha1": msha, "files": files, "from_b": list(FROM_B),
           "dropped": {"correctives": {"rows": len(rows), "shapes": shapes},
                       "why": "the copy has no corrective shapes (0 morphs); the owner agreed to drop B's joint correctives in the game"},
           "skin": bpub.get("skin"),
           "import": {"from": "godot/art/people/heroine.glb.import", "params": params, "changed": {}}}
    ch = p1.write_import(gi, params)
    if ch:
        out["import"]["changed"]["body.glb"] = ch
    elif not os.path.exists(gi):
        out["import"]["note"] = "no body.glb.import yet: Godot writes it on the first import; the next publish sets it"
    with open(os.path.join(pub, "publish.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1)
    # gear
    clear_files(gear_out)
    b_index = json.load(open(os.path.join(B_GEAR, "gear_index.json"), encoding="utf-8"))
    ix = rewrite_gear_index(b_index, pkg, gear_out, files["body.glb"], msha)
    with open(os.path.join(gear_out, "gear_index.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(ix, f, indent=1)
    h = ix["house"]
    print(f"publish_house: {len(files)} files -> {os.path.relpath(pub, root)}; correctives dropped {len(rows)} rows, {shapes} shapes")
    print(f"publish_house: gear rows tucked {len(h['rows_tucked'])}, covered {len(h['rows_covered'])}, untucked {len(h['rows_untucked'])}")
    if h["rows_untucked"]:
        print("publish_house: no tuck for the copy: " + ", ".join(h["rows_untucked"]))
    return out


def godot_import():
    if subprocess.call([sys.executable, TURN, "take", "godot", "body-switch: import", "--wait", "90", "--stale-ok"]) != 0:
        raise SystemExit("publish_house: no godot turn")
    try:
        r = subprocess.call([GODOT, "--headless", "--path", os.path.join(ROOT, "godot"), "--import"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1800)
        print("godot import exit", r)
    finally:
        subprocess.call([sys.executable, TURN, "give", "godot", "body-switch: import"])


if __name__ == "__main__":
    argv = sys.argv[1:]
    root = ROOT
    if "--out-root" in argv:
        i = argv.index("--out-root")
        root = os.path.abspath(argv[i + 1])
        del argv[i:i + 2]
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        raise SystemExit(__doc__)
    publish(args[0], root)
    if "--import" in argv:
        godot_import()
