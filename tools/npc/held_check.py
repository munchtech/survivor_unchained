"""A base-body NPC holding its own props (World.NpcHeld) in the real game: the package staged from a Marionette workshop
build on the current base body (generated/rnd/x18/w8/v1: props/idle/sock.glb and props/walk/sock.glb, the dressed body
on its OWN rest with its own clip), its manifest's "held" naming a hand lamp (left, carry lamp) and the smith's hammer
(right, carry hand), read through --npc-overlay (nothing copied into art/npc).

The base body can't stand on the game's folk clips (its rest isn't the old packages' heroine rest: on folk/f_idle she
lies on her back, as R&D's LOG rig 6 found), so the frames go through Marionette's game_frame.gd hook as R&D's own
held check does: the glb's own clip (--gf-clip), the package layers off but the carry's (NpcTorchArm, NpcHands), the
game's own PersonView.Hold(slot, "", "own") called on the shot NPC (--gf-held), the clip held at set times, each
capture's pose and held meshes dumped; Marionette's tools/npc/held_clear.py measures the props against the body (mm).
Before = the lamp carry's Reach forced to 0 (the shot's reach0), after = as built. Frames at the play camera and the
chest camera (the closest an NPC is seen), and the walk at the play camera.

    python tools/npc/held_check.py OUT --rnd DIR [--name x18_keeper_held] [--hair-colour #2a1c14] [--only shoot|measure]

The prop files' frame (NpcHeld): origin = the grip (where the fist closes), +Y out of the fist along the shaft (the
hammer's head; the lamp's hanging ring, the lamp below along -Y), +Z the face, drawn 1:1.
  hand lamp: art/props/keeper_lamp/keeper_lamp.glb (0.154 x 0.326 m), its grip the bail's top bar 0.092 above the ring;
    glass the keepers' violet, the iron's game-only mask colours dropped.
  hammer: art/weapons/smith_hammer.glb (0.397 m, shaft on +Y, head across X), its grip at its anchor_grip (0.07 up the
    shaft), turned a quarter about Y so the head's face is +Z.
Takes the godot turn (tools/turn.py) for the batch and gives it back.
"""
import argparse
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
G = ROOT / "godot"
GODOT = os.environ.get("GODOT_EXE", "C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe")
TURN = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
MAR = Path(os.environ.get("MARIONETTE", "C:/Users/munch/Desktop/Marionette"))
HOOK, HELD_CLEAR = MAR / "tools/npc/game_frame.gd", MAR / "tools/npc/held_clear.py"
LAMP, HAMMER = G / "art/props/keeper_lamp/keeper_lamp.glb", G / "art/weapons/smith_hammer.glb"
BASE = ["--quick", "warden", "--sex", "female", "--nohud", "--zone", "verge", "--facing", "0", "--seed", "1", "--time", "day", "--clock", "120"]
HELD = ["--gf-held", "handslot.l=own,handslot.r=own"]
# (shot, clip, --npc flags, extra game args, held times in s): the glb's three-quarter turn (game_frame.py's 50 degrees)
IDLE_AT = [round(16.6 * i / 12, 2) for i in range(12)]
SHOTS = [("play", "idle", ":turn50", ["--idle-after", "1000000"], IDLE_AT),
         ("chest", "idle", ":swap:chest:turn50", ["--close", "1", "--idle-after", "1"], [0.0, 5.5, 11.1]),
         ("walk", "walk", ":walk:turn50", ["--idle-after", "1000000"], [round(1.33 * i / 6, 3) for i in range(6)])]
HOLD = 30


def glb_read(p):
    b = Path(p).read_bytes()
    n = struct.unpack("<I", b[12:16])[0]
    rest = b[20 + n:]
    return json.loads(b[20:20 + n]), rest[8:8 + struct.unpack("<I", rest[:4])[0]]


def glb_write(p, j, binary):
    js = json.dumps(j, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    binary += b"\0" * (-len(binary) % 4)
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_bytes(b"glTF" + struct.pack("<II", 2, 28 + len(js) + len(binary)) + struct.pack("<I", len(js)) + b"JSON" + js
                        + struct.pack("<I", len(binary)) + b"BIN\0" + binary)


def reframe(src, out, translation, rotation=(0, 0, 0, 1), edit=None):
    """The glb under one root node that moves its grip to the origin (and turns its face to +Z)."""
    j, binary = glb_read(src)
    if edit:
        edit(j)
    scene = j["scenes"][j.get("scene", 0)]
    j["nodes"].append({"name": "Held", "translation": list(translation), "rotation": list(rotation), "children": list(scene["nodes"])})
    scene["nodes"] = [len(j["nodes"]) - 1]
    glb_write(out, j, binary)


def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lamp_edit(j):
    for m in j["meshes"]:
        for p in m["primitives"]:
            for k in ("COLOR_0", "COLOR_1"):
                p["attributes"].pop(k, None)
    violet = [lin(int("a77bff"[i:i + 2], 16) / 255) for i in (0, 2, 4)]
    for mat in j["materials"]:
        if mat["name"] == "keeper_glass":
            mat["pbrMetallicRoughness"]["baseColorFactor"] = [*(c * 0.5 for c in violet), 1]
            mat["emissiveFactor"] = violet
        if mat["name"] == "keeper_iron":
            mat["pbrMetallicRoughness"].update(metallicFactor=0.6, roughnessFactor=0.6)


def stage(out, glb, name, hair):
    pk = out / ("pkg_" + name)
    pk.mkdir(parents=True, exist_ok=True)
    body = pk / "body.glb"
    if not body.exists():
        try:
            os.link(glb, body)   # (a hard link: the 200 MB glb not copied; removing it leaves the source)
        except OSError:
            shutil.copyfile(glb, body)
    j, _ = glb_read(glb)
    joints = [j["nodes"][i].get("name", "") for i in j["skins"][0]["joints"]]
    acc = [j["accessors"][p["attributes"]["POSITION"]] for m in j["meshes"] for p in m["primitives"]]
    lo, hi = min(a["min"][1] for a in acc if "min" in a), max(a["max"][1] for a in acc if "max" in a)
    reframe(LAMP, pk / "props/hand_lamp.glb", (0, -0.092, 0), edit=lamp_edit)
    s = math.sqrt(0.5)
    reframe(HAMMER, pk / "props/hammer.glb", (0, -0.07, 0), (0, -s, 0, s))
    man = {"name": name, "sex": "female", "height": round(hi - lo, 4), "joints": len(joints), "baked": True, "body": "body.glb",
           "pieces": [], "from": str(Path(glb).resolve()).replace("\\", "/"), "hair": {"colour": hair},
           "held": {"handslot.l": {"file": "props/hand_lamp.glb", "carry": "lamp"},
                    "handslot.r": {"file": "props/hammer.glb", "carry": "hand"}}}
    (pk / "manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    return pk


def run(cmd, log, env=None):
    r = subprocess.run(cmd, cwd=G, capture_output=True, text=True, timeout=600, stdin=subprocess.DEVNULL, env=env)
    Path(log).write_text((r.stdout or "") + (r.stderr or ""), encoding="utf-8")
    return r.returncode


def shoot(out, pkgs):
    for tag, flags in (("before", ":reach0"), ("after", "")):
        for shot, clip, f, extra, at in SHOTS:
            if tag == "before" and shot == "walk":
                continue
            name, pk = pkgs[clip]
            d = out / tag
            d.mkdir(parents=True, exist_ok=True)
            for x in d.glob(f"{shot}_*"):
                x.unlink()
            labels = [f"t{i:02d}" for i in range(len(at))]
            secs = 6 + len(at) * HOLD / 60 + 3
            gf = ["--gf-clip", clip, "--gf-mods", "all", *HELD, "--gf-solo", "--gf-at", ",".join(f"{l}={t:g}" for l, t in zip(labels, at)),
                  "--gf-start", "6", "--gf-hold", str(HOLD), "--gf-save", (d / shot).as_posix()]
            rc = run([GODOT, "--path", ".", "--fixed-fps", "60", "--resolution", "1920x1080", "-s", HOOK.as_posix(), "--", *BASE,
                      "--npc-overlay", f"{name}={pk.as_posix()}", *extra, "--seconds", f"{secs:g}", "--npc", name + f + flags,
                      "--npc-debug", "--shot", f"held_{tag}_{shot}", *gf], out / f"log_{tag}_{shot}.txt")
            got = sorted(d.glob(f"{shot}_t*.png"))
            print(f"{tag} {shot}: {len(got)}/{len(at)} frames (exit {rc})")


def measure(out, pkgs):
    for tag in ("before", "after"):
        for shot, clip, *_ in SHOTS:
            d = out / tag
            if not (d / f"{shot}_held_mesh.json").exists():
                continue
            r = subprocess.run([sys.executable, str(HELD_CLEAR), str(pkgs[clip][1] / "body.glb"), str(d), "--cam", shot],
                               capture_output=True, text=True, cwd=MAR)
            (out / f"clear_{tag}_{shot}.txt").write_text(r.stdout + r.stderr, encoding="utf-8")
            print(f"clearance {tag} {shot} (exit {r.returncode}): {out / f'clear_{tag}_{shot}.txt'}")


def sheets(out, label="t00"):
    from PIL import Image, ImageDraw
    for shot in ("play", "chest"):
        a, b = out / "before" / f"{shot}_{label}.png", out / "after" / f"{shot}_{label}.png"
        if not (a.exists() and b.exists()):
            continue
        A, B = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
        s = Image.new("RGB", (A.width + B.width + 8, A.height + 28), (16, 16, 16))
        d = ImageDraw.Draw(s)
        s.paste(A, (0, 28))
        s.paste(B, (A.width + 8, 28))
        d.text((8, 8), f"BEFORE (lamp carry Reach 0) - {shot} camera, {label}, 1:1", fill=(230, 230, 230))
        d.text((A.width + 16, 8), f"AFTER (as built) - {shot} camera, {label}, 1:1", fill=(230, 230, 230))
        s.save(out / f"sheet_{shot}_{label}.png")
        print(f"sheet: {out / f'sheet_{shot}_{label}.png'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--rnd", required=True, help="a workshop build folder (props/idle/sock.glb, props/walk/sock.glb)")
    ap.add_argument("--name", default="x18_keeper_held")
    ap.add_argument("--hair-colour", default="#2a1c14")
    ap.add_argument("--only", choices=["shoot", "measure"])
    a = ap.parse_args()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rnd = Path(a.rnd)
    pkgs = {clip: (nm, stage(out, rnd / "props" / clip / "sock.glb", nm, a.hair_colour))
            for clip, nm in (("idle", a.name), ("walk", a.name + "_walk"))}
    print(f"staged {[str(p) for _, p in pkgs.values()]}")
    who = f"npc held: {a.name}"
    if subprocess.run([sys.executable, TURN, "take", "godot", who, "--wait", "30"]).returncode:
        sys.exit("no godot turn")
    try:
        if a.only != "measure":
            shoot(out, pkgs)
        if a.only != "shoot":
            measure(out, pkgs)
    finally:
        subprocess.run([sys.executable, TURN, "give", "godot", who])
    sheets(out)


if __name__ == "__main__":
    main()
