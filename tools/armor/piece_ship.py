"""One armor piece built, carried onto the body the game ships, and installed: one recorded step (P2 l15, 10 Nov 2026).

    python tools/armor/piece_ship.py <id> [<id> ...] [--src <blend>] [--body <glb>]
    python tools/armor/piece_ship.py --check            every installed piece's body stamp against the shipped body

Take a blender turn first (tools/turn.py take blender ...) when any id is a Blender build (no `base`).

The pieces are built on a body blend (build.py's SRC, heroine_built_armroot.blend) that is not the body the game
ships: the shipped heroine.glb is that body plus body-only post-steps (the shoulder rig's helpers and eight weights,
the 18 shoulder shapes, the pit re-mesh, the arm rest moves). So, for each id, in a stage folder
(.shots/armor2/ship/<id>/<time>/, git-ignored; godot/art/armor is never written until the install):
  1. build: piece_blender.py with ARMOR_STAGE (the piece into <stage>/armor, the body it was built on as
     <stage>/base.glb), then its LODs (piece_lod), its adornment Blender doesn't make (adorn --post) and its fans
     filled (fan_fill), as build.py does. A variant (piece.json `base`) instead takes its base's last staged build
     before the follow (<base stage>/pre) and runs adorn + fan_fill on it there (adorn keeps no morph targets, so a
     variant is adorned before the follow, never after).
  2. follow: tools/assets/body_follow_post.py base.glb <body> <stage> --parts armor (rest moves, eight weights, helper
     joints, shoulder shapes, rigid shells, the tuck re-keyed). Refused when fewer than FOLLOW_MIN of base.glb's skin
     points found their twin on the body (a different paint layout: nothing would follow).
  3. install: the piece's files into godot/art/armor, its armor_index row merged, stamped with
       body_hash  the shipped body's label (art/people/armor_index.json's, as every reader expects),
       body_glb   glb_body_hash(<body>): a stamp any tool can check against the file itself (--check),
       built_on   the blend body's hash it was built on.
"""
import glob
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
ART = os.path.join(ROOT, "godot", "art", "armor")
BODY = os.path.join(ROOT, "godot", "art", "people", "heroine.glb")
PEOPLE_INDEX = os.path.join(ROOT, "godot", "art", "people", "armor_index.json")
SHIP = os.path.join(ROOT, ".shots", "armor2", "ship")
FOLLOW = os.path.join(ROOT, "tools", "assets", "body_follow_post.py")
FOLLOW_MIN = 0.95


def say(*a):
    print("SHIP", *a, flush=True)


# ---------------------------------------------------------------------------------------- the stamp --
def _glb(path):
    b = open(path, "rb").read()
    assert b[:4] == b"glTF", path
    off, js, bin_ = 12, None, None
    while off < len(b):
        ln, ty = struct.unpack("<II", b[off:off + 8])
        ch = b[off + 8:off + 8 + ln]
        if ty == 0x4E4F534A:
            js = json.loads(ch)
        elif ty == 0x004E4942:
            bin_ = ch
        off += 8 + ln
    return js, bin_


def _acc(js, bin_, i):
    a = js["accessors"][i]
    bv = js["bufferViews"][a["bufferView"]]
    n = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
    dt = np.dtype({5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a["componentType"]])
    o = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    st = bv.get("byteStride", 0) or n * dt.itemsize
    raw = np.frombuffer(bin_, np.uint8, count=st * (a["count"] - 1) + n * dt.itemsize, offset=o)
    return np.lib.stride_tricks.as_strided(raw, (a["count"], n * dt.itemsize), (st, 1)).copy().view(dt).reshape(a["count"], n)


def glb_body_hash(path, node="Heroine"):
    """Her body's geometry as 8 hex: the Heroine node's indexed points (every primitive), x 1e5 rounded, unique, sha1
    of the <i4 rows. Equal stamps are the same rest points, whatever else the file holds (heroine.glb at 4ff1b1d51
    and after: 66182af6)."""
    js, bin_ = _glb(path)
    n = next(x for x in js["nodes"] if x.get("name") == node and "mesh" in x)
    P = []
    for p in js["meshes"][n["mesh"]]["primitives"]:
        pos = _acc(js, bin_, p["attributes"]["POSITION"])
        idx = _acc(js, bin_, p["indices"]).ravel() if "indices" in p else np.arange(len(pos))
        P.append(pos[np.unique(idx)])
    q = np.unique(np.round(np.concatenate(P).astype(np.float64) * 1e5).astype(np.int64), axis=0)
    return hashlib.sha1(q.astype("<i4").tobytes()).hexdigest()[:8]


def shipped_label(people_index=PEOPLE_INDEX):
    labels = {r.get("body_hash") for r in json.load(open(people_index, encoding="utf-8"))} - {None}
    if len(labels) != 1:
        raise SystemExit("SHIP: art/people/armor_index.json has %d body labels (%s), one expected" % (len(labels), sorted(labels)))
    return labels.pop()


# ------------------------------------------------------------------------------------------ install --
def piece_files(armor_dir, pid):
    """The piece's own files in an armor dir (relative): gltf, bin, sockets, tuck, cover, and the textures its gltf
    names beside it (tex/)."""
    out = [f"{pid}.gltf", f"{pid}.bin", f"{pid}.sockets.json", f"armor_tuck/{pid}.bin", f"armor_cover/{pid}.bin"]
    js = json.load(open(os.path.join(armor_dir, f"{pid}.gltf"), encoding="utf-8"))
    out += [im["uri"] for im in js.get("images", []) if im.get("uri", "").startswith("tex/")]
    return [f for f in out if os.path.exists(os.path.join(armor_dir, f))]


def install(pid, stage_armor, art, body_glb, label, built_on):
    """The staged piece into `art`, its row merged into art/armor_index.json and stamped (body_hash = label,
    body_glb, built_on) on the row, the gltf's asset extras and the sockets."""
    files = piece_files(stage_armor, pid)
    for f in files:
        os.makedirs(os.path.dirname(os.path.join(art, f)), exist_ok=True)
        shutil.copyfile(os.path.join(stage_armor, f), os.path.join(art, f))
    stamp = {"body_hash": label, "body_glb": body_glb, "built_on": built_on}
    gp = os.path.join(art, f"{pid}.gltf")
    js = json.load(open(gp, encoding="utf-8"))
    js.setdefault("asset", {}).setdefault("extras", {}).update(stamp)
    json.dump(js, open(gp, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    sp = os.path.join(art, f"{pid}.sockets.json")
    if os.path.exists(sp):
        s = json.load(open(sp, encoding="utf-8"))
        s.update(stamp)
        json.dump(s, open(sp, "w", encoding="utf-8"), indent=1)
    row = next(r for r in json.load(open(os.path.join(stage_armor, "armor_index.json"), encoding="utf-8")) if r["id"] == pid)
    row.update(stamp)
    ix = os.path.join(art, "armor_index.json")
    rows = [r for r in (json.load(open(ix, encoding="utf-8")) if os.path.exists(ix) else []) if r.get("id") != pid]
    rows.append(row)
    rows.sort(key=lambda r: r["id"])
    json.dump(rows, open(ix, "w", encoding="utf-8"), indent=1)
    imp = gp + ".import"
    ref = os.path.join(ROOT, "godot", "art", "people", "heroine_outfit_warden.gltf.import")
    if not os.path.exists(imp) and os.path.exists(ref):
        keep = [l for l in open(ref, encoding="utf-8").read().splitlines() if not l.startswith(("uid=", "path=", "dest_files=", "source_file="))]
        open(imp, "w", encoding="utf-8", newline="\n").write("\n".join(keep) + "\n")
    return files


def check(art=ART, body=BODY):
    """Each installed row against the shipped body: body_glb equal to glb_body_hash(body), or none (an older stamp)."""
    want = glb_body_hash(body)
    bad = []
    for r in json.load(open(os.path.join(art, "armor_index.json"), encoding="utf-8")):
        g = r.get("body_glb")
        state = "ok" if g == want else ("no glb stamp" if g is None else "STALE (%s)" % g)
        if g != want:
            bad.append(r["id"])
        say("CHECK %-28s %s" % (r["id"], state))
    say("CHECK body %s: %d of the rows not stamped on it" % (want, len(bad)))
    return bad


# --------------------------------------------------------------------------------------------- ship --
def follow_ratio(text):
    m = re.search(r"FOLLOW field: BASE (\d+) pts, BODY (\d+); twins (\d+)", text)
    return (int(m.group(3)) / max(int(m.group(1)), 1)) if m else 0.0


def latest_stage(pid):
    st = sorted(glob.glob(os.path.join(SHIP, pid, "*", "pre")))
    if not st:
        raise SystemExit(f"SHIP: no staged build of {pid} (ship it first)")
    return os.path.dirname(st[-1])


def ship(pid, src, body):
    import build as bd
    piece = json.load(open(os.path.join(ART, "src", pid, "piece.json"), encoding="utf-8"))
    stage = os.path.join(SHIP, pid, time.strftime("%Y%m%d_%H%M%S"))
    sa = os.path.join(stage, "armor")
    os.makedirs(sa, exist_ok=True)
    os.environ["ARMOR_STAGE"] = stage
    log = os.path.join(stage, "ship.log")
    if piece.get("base"):
        bs = latest_stage(piece["base"])
        shutil.copytree(os.path.join(bs, "pre"), sa, dirs_exist_ok=True)
        shutil.copyfile(os.path.join(bs, "base.glb"), os.path.join(stage, "base.glb"))
        json.dump(json.load(open(os.path.join(bs, "built_on.json"))), open(os.path.join(stage, "built_on.json"), "w"))
        ok = bd.adorn(pid) and bd.fan_fill(pid, os.path.join(sa, pid + ".gltf"))
    else:
        scratch = os.path.join(stage, "scratch")
        with open(log, "w", encoding="utf-8") as fh:
            r = subprocess.run([bd.BLENDER, "-b", src, "--python", os.path.join(HERE, "piece_blender.py"), "--",
                                os.path.join(ART, "src", pid, "piece.json"), scratch],
                               cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        text = open(log, encoding="utf-8", errors="replace").read()
        ok = r.returncode == 0 and "ARMOR NUMBERS" in text and os.path.exists(os.path.join(stage, "base.glb"))
        for l in text.splitlines():
            if l.startswith(("ARMOR REFUSED", "Traceback", "ARMOR TEXTURES")):
                say(l)
        if ok:
            num = json.load(open(os.path.join(scratch, "numbers.json"), encoding="utf-8"))
            json.dump({"body_hash": num["body_hash"], "src": src}, open(os.path.join(stage, "built_on.json"), "w"))
            gl_ = os.path.join(sa, pid + ".gltf")
            r2 = subprocess.run([sys.executable, os.path.join(HERE, "piece_lod.py"), gl_, "--numbers", os.path.join(scratch, "numbers.json")],
                                cwd=ROOT, capture_output=True, text=True)
            say((r2.stdout + r2.stderr).strip()[-400:])
            ok = r2.returncode == 0
            if ok and any(not (a["kind"] == "row" and a.get("mesh", "rivet") == "rivet") for a in piece.get("adorn", [])):
                ok = bd.adorn(pid, post=True)
            ok = ok and bd.fan_fill(pid, gl_)
    del os.environ["ARMOR_STAGE"]
    if not ok:
        say(f"{pid}: BUILD FAILED (stage {stage}, log {log}); nothing installed")
        return False
    shutil.copytree(sa, os.path.join(stage, "pre"), dirs_exist_ok=True)      # (before the follow: its variants adorn this)
    r = subprocess.run([sys.executable, FOLLOW, os.path.join(stage, "base.glb"), body, stage, "--parts", "armor"],
                       cwd=ROOT, capture_output=True, text=True)
    text = r.stdout + r.stderr
    open(os.path.join(stage, "follow.log"), "w", encoding="utf-8").write(text)
    for l in text.splitlines():
        if l.startswith(("FOLLOW", "Traceback")):
            say(l[:300])
    ratio = follow_ratio(text)
    if r.returncode != 0 or ratio < FOLLOW_MIN:
        say(f"{pid}: FOLLOW REFUSED (exit {r.returncode}, twins {ratio:.1%} of base.glb's skin, {FOLLOW_MIN:.0%} needed); nothing installed")
        return False
    built_on = json.load(open(os.path.join(stage, "built_on.json")))["body_hash"]
    files = install(pid, sa, ART, glb_body_hash(body), shipped_label(), built_on)
    say(f"{pid}: INSTALLED {len(files)} files into godot/art/armor (built on {built_on}, followed onto {glb_body_hash(body)}, twins {ratio:.1%}); stage {stage}")
    return True


def main(argv):
    if "--check" in argv:
        sys.exit(1 if check() else 0)
    import build as bd
    src = argv[argv.index("--src") + 1] if "--src" in argv else bd.SRC
    body = os.path.abspath(argv[argv.index("--body") + 1]) if "--body" in argv else BODY
    ids = [a for i, a in enumerate(argv) if not a.startswith("--") and argv[i - 1] not in ("--src", "--body")]
    bad = [p for p in ids if not ship(p, src, body)]
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
