"""One armor piece built, carried onto the body the game ships, and installed: one recorded step (P2 l15, 10 Nov 2026).

    python tools/armor/piece_ship.py <id> [<id> ...] [--src <blend>] [--body <glb>] [--min <twin share, 0.95>] [--max-move <mm, 15>] [--max-strain <mm, 5>]
    python tools/armor/piece_ship.py --check            every installed piece's body stamp against the shipped body
    python tools/armor/piece_ship.py <id> --no-exact     a free mesh (style mesh) by the follow, as any other piece

A free mesh (piece.json style "mesh") is modelled at the SHIPPED body's rest, so it is installed EXACTLY by default
(lane D, 16 Nov): built with ARMOR_EXACT=1 (no push-out against the blend's skin), followed onto the body only for the
tuck re-key and her helper joints, then pin_shipped.pin: every point back on its authored place, her own weights at the
closest place on her skin (a rigid shell on one blend of them), her bind; then the follow once more with the body as
both bodies (the identity: twins 100%, no move) for her shoulder shapes at those points. Gated on the largest move off
the authored points (pin_shipped.EXACT_MAX_MM, 0.5 mm) instead of the follow's twins and move.

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
     joints, shoulder shapes, rigid shells, the tuck re-keyed). Refused when fewer than --min of base.glb's skin
     points found their twin on the body, or the piece's own max move / strain pass --max-move / --max-strain (the
     lost points go by the closest place on the body's surface). Socket points move by the same rest move.
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
FOLLOW_MIN = 0.95          # --min: the share of base.glb's skin points that found a UV twin on the body
MAX_MOVE = 15.0            # --max-move (mm): the piece's own largest rest move
MAX_STRAIN = 5.0           # --max-strain (mm): the piece's largest "off its neighbours" figure


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


def tex_uris(js, art):
    """The shared outfit textures (art/people/outfit_tex) named from where the piece is installed. piece_blender writes
    A's "../people/outfit_tex/"; a piece shipped one folder deeper (art/armor/body_p1, B) kept it, which names no file
    there, so Godot imported its materials with no albedo, normal or roughness map and the shader's gold mask (its
    albedo's mean colour) read 0 on every trim (armor-D l7 finish, 17 Nov). A's own stays byte-identical."""
    ptex = os.path.join(ROOT, "godot", "art", "people", "outfit_tex")
    rel = os.path.relpath(ptex, os.path.abspath(art)).replace("\\", "/")
    for im in js.get("images", []):
        u = im.get("uri", "")
        if "people/outfit_tex/" in u and os.path.exists(os.path.join(ptex, os.path.basename(u))):
            im["uri"] = rel + "/" + os.path.basename(u)
    return js


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
    tex_uris(js, art)
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


def piece_numbers(text, pid):
    """(max move mm, off-neighbours mm) of the piece's own FOLLOW line, or None when it printed none."""
    m = re.search(r"FOLLOW %s\.gltf .*?max ([\d.]+) mm, off its neighbours ([\d.]+)" % re.escape(pid), text)
    return (float(m.group(1)), float(m.group(2))) if m else None


def follow_verdict(ratio, nums, fmin=FOLLOW_MIN, max_move=MAX_MOVE, max_strain=MAX_STRAIN):
    """None when the follow is acceptable, else the reason. The twin share only has to reach `fmin` (a re-meshed body
    loses twins by design: the lost points go by the closest place on its surface); the piece's own move and strain
    are the gates that matter."""
    if ratio < fmin:
        return f"twins {ratio:.1%} of base.glb's skin, {fmin:.0%} needed"
    if nums is None:
        return "no FOLLOW line for the piece"
    if nums[0] > max_move:
        return f"piece max move {nums[0]:.2f} mm over {max_move:g}"
    if nums[1] > max_strain:
        return f"piece strain (off neighbours) {nums[1]:.2f} mm over {max_strain:g}"
    return None


def latest_stage(pid):
    st = sorted(glob.glob(os.path.join(SHIP, pid, "*", "pre")))
    if not st:
        raise SystemExit(f"SHIP: no staged build of {pid} (ship it first)")
    return os.path.dirname(st[-1])


def follow_env(piece):
    """The follow's environment: params.shoulder_shapes false -> BF_PAUL_SHAPES=0 (no shoulder shapes on its plates)."""
    env = dict(os.environ)
    if piece and piece.get("params", {}).get("shoulder_shapes", True) is False:
        env["BF_PAUL_SHAPES"] = "0"
        # (params.shoulder_shapes_meshes [material, ..]: those meshes still carry them, the leather under the plates)
        if piece["params"].get("shoulder_shapes_meshes"):
            env["BF_PAUL_SHAPES_MESHES"] = ",".join(piece["params"]["shoulder_shapes_meshes"])
    return env


def _follow(base, body, stage, piece=None):
    r = subprocess.run([sys.executable, FOLLOW, base, body, stage, "--parts", "armor"], cwd=ROOT, capture_output=True, text=True,
                       env=follow_env(piece))
    return r, r.stdout + r.stderr


def ship(pid, src, body, fmin=FOLLOW_MIN, max_move=MAX_MOVE, max_strain=MAX_STRAIN, exact=None):
    import build as bd
    piece = json.load(open(os.path.join(ART, "src", pid, "piece.json"), encoding="utf-8"))
    exact = piece.get("style") == "mesh" if exact is None else (exact and piece.get("style") == "mesh")
    stage = os.path.join(SHIP, pid, time.strftime("%Y%m%d_%H%M%S"))
    sa = os.path.join(stage, "armor")
    os.makedirs(sa, exist_ok=True)
    os.environ["ARMOR_STAGE"] = stage
    os.environ["ARMOR_EXACT"] = "1" if exact else "0"
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
            r2 = subprocess.run([sys.executable, os.path.join(HERE, "piece_lod.py"), gl_, "--numbers", os.path.join(scratch, "numbers.json")]
                                + (["--budget", str(piece["lod_budget"])] if piece.get("lod_budget") else []),
                                cwd=ROOT, capture_output=True, text=True)
            say((r2.stdout + r2.stderr).strip()[-400:])
            ok = r2.returncode == 0
            if ok and any(not (a["kind"] == "row" and a.get("mesh", "rivet") == "rivet") for a in piece.get("adorn", [])):
                ok = bd.adorn(pid, post=True)
            ok = ok and bd.fan_fill(pid, gl_)
    del os.environ["ARMOR_STAGE"]
    del os.environ["ARMOR_EXACT"]
    if not ok:
        say(f"{pid}: BUILD FAILED (stage {stage}, log {log}); nothing installed")
        return False
    shutil.copytree(sa, os.path.join(stage, "pre"), dirs_exist_ok=True)      # (before the follow: its variants adorn this)
    r, text = _follow(os.path.join(stage, "base.glb"), body, stage, piece)
    open(os.path.join(stage, "follow.log"), "w", encoding="utf-8").write(text)
    if exact:
        return _ship_exact(pid, piece, stage, sa, body, r, text)
    for l in text.splitlines():
        if l.startswith(("FOLLOW", "Traceback")):
            say(l[:300])
    ratio = follow_ratio(text)
    nums = piece_numbers(text, pid)
    say(f"{pid}: follow twins {ratio:.1%}, max move {nums[0] if nums else float('nan'):.2f} mm, strain {nums[1] if nums else float('nan'):.2f} mm")
    why = f"exit {r.returncode}" if r.returncode != 0 else follow_verdict(ratio, nums, fmin, max_move, max_strain)
    if why:
        say(f"{pid}: FOLLOW REFUSED ({why}); nothing installed")
        return False
    built_on = json.load(open(os.path.join(stage, "built_on.json")))["body_hash"]
    files = install(pid, sa, ART, glb_body_hash(body), shipped_label(), built_on)
    say(f"{pid}: INSTALLED {len(files)} files into godot/art/armor (built on {built_on}, followed onto {glb_body_hash(body)}, twins {ratio:.1%}); stage {stage}")
    return True


def _ship_exact(pid, piece, stage, sa, body, r, text):
    """The free mesh's exact install (the module doc): after the blend -> body follow (tuck, helpers) in `stage`."""
    import pin_shipped as pn
    if r.returncode != 0:
        say(f"{pid}: FOLLOW FAILED (exit {r.returncode}, {stage}/follow.log); nothing installed")
        return False
    say(f"{pid}: exact: blend -> body follow twins {follow_ratio(text):.1%} (its moves undone; kept: the tuck re-key, her helper joints)")
    gp, pre = os.path.join(sa, pid + ".gltf"), os.path.join(stage, "pre", pid + ".gltf")
    B = pn.bf.Body(body)
    src0 = os.path.join(ART, "src", pid, piece.get("params", {}).get("file", ""))
    res = pn.pin(gp, pre, body, B, drop=tuple(piece.get("params", {}).get("rigid_drop") or ()),
                 ride=tuple(piece.get("params", {}).get("rigid_ride") or ()),
                 authored=src0 if src0.endswith((".glb", ".gltf")) and os.path.exists(src0) else None,
                 bend=piece.get("params", {}).get("bend_ride"))
    say(f"{pid}: exact pin: {json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in res.items()})}")
    ps_ = os.path.join(stage, "pre", pid + ".sockets.json")
    if os.path.exists(ps_):
        shutil.copyfile(ps_, os.path.join(sa, pid + ".sockets.json"))      # (sockets at their authored place too)
    r2, text2 = _follow(body, body, stage, piece)      # (params.shoulder_shapes holds here too: this follow carries the shapes)
    open(os.path.join(stage, "follow_identity.log"), "w", encoding="utf-8").write(text2)
    for l in text2.splitlines():
        if l.startswith(("FOLLOW", "Traceback")):
            say(l[:300])
    ratio = follow_ratio(text2)
    src_glb = os.path.join(ART, "src", pid, piece.get("params", {}).get("file", ""))
    m = pn.measure(gp, pre, body, src_glb if src_glb.endswith((".glb", ".gltf")) and os.path.exists(src_glb) else None, B)
    m["identity_twins"] = ratio
    json.dump({"pin": res, "measure": m}, open(os.path.join(stage, "exact.json"), "w"), indent=1)
    say(f"{pid}: exact measure: {json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items()})}")
    why = exact_verdict(r2.returncode, ratio, m)
    if why:
        say(f"{pid}: EXACT REFUSED ({why}); nothing installed")
        return False
    built_on = json.load(open(os.path.join(stage, "built_on.json")))["body_hash"]
    files = install(pid, sa, ART, glb_body_hash(body), shipped_label(), built_on)
    say(f"{pid}: INSTALLED EXACT {len(files)} files into godot/art/armor (on {glb_body_hash(body)}, max move {m['move_max_mm']:.3f} mm); stage {stage}")
    return True


def exact_verdict(code, ratio, m, max_mm=None):
    """None when the exact install holds, else the reason: the identity follow ran with every twin, and no point of the
    piece is more than max_mm (pin_shipped.EXACT_MAX_MM) off its authored place."""
    if max_mm is None:
        import pin_shipped as pn
        max_mm = pn.EXACT_MAX_MM
    if code != 0:
        return f"identity follow exit {code}"
    if ratio < 0.999:
        return f"identity follow twins {ratio:.1%}"
    mv = max(m["move_max_mm"], m.get("installed_to_authored_mm", 0.0))
    if mv > max_mm:
        return f"moved {mv:.3f} mm off its authored points, {max_mm} allowed"
    return None


def use_body(argv):
    """`--body a|p1` (bodies.py; a path after --body is still the body glb to follow onto). For p1: ART, SHIP and BODY
    point at its body-keyed places, and --src (the body blend the pieces are built on, a body-B twin of
    heroine_built_armroot.blend) must be named, else stop: there is none yet."""
    global ART, SHIP, BODY
    import bodies
    b = bodies.take(argv)
    if b.name == "a":
        return
    ART, BODY = b.art, b.need(b.glb, "body.glb")
    SHIP = os.path.join(ROOT, ".shots", "armor2", "ship", b.ship_sub)
    if "--src" not in argv:
        raise bodies.Missing("BODY p1: missing input: --src, the body-B build blend (heroine_built_armroot.blend's twin with "
                             "body_p1's body: piece_blender builds on it, and its ARMOR_BODY_HASH stamps the piece) "
                             "(lane G / body pipeline owes it)")


def main(argv):
    use_body(argv)
    if "--check" in argv:
        sys.exit(1 if check() else 0)
    import build as bd
    opt = {"--src": bd.SRC, "--body": BODY, "--min": FOLLOW_MIN, "--max-move": MAX_MOVE, "--max-strain": MAX_STRAIN}
    for k in opt:
        if k in argv:
            opt[k] = argv[argv.index(k) + 1]
    body = os.path.abspath(opt["--body"])
    ids = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] not in opt)]
    exact = False if "--no-exact" in argv else None
    bad = [p for p in ids if not ship(p, opt["--src"], body, float(opt["--min"]), float(opt["--max-move"]), float(opt["--max-strain"]), exact)]
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
