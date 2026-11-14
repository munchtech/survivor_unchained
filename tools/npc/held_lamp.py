"""A test package holding its own hand lamp (World.NpcHeld): the keeper's lamp-iron at its made size (0.154 x 0.326 m,
art/props/keeper_lamp/keeper_lamp.glb), re-framed for a manifest "held" entry, beside a copy of a woman package's
manifest naming it. Read in the game through --npc-overlay NAME=OUT (NpcPackage.Overlay): nothing copied into art/npc.

    python tools/npc/held_lamp.py OUT [--package npc_folk_w] [--slot handslot.r] [--carry lamp]

The prop file's frame (NpcHeld): origin = the grip, the middle of the bail's top bar where the fist closes (made at
(0, 0.092, 0) from the ring); +Y up out of the fist; the lamp hangs below along -Y; +Z its front. The glTF is already
Y-up, so the re-frame is one root node lifting it 0.092 down. Its glass glows the keepers' violet (#a77bff, as
Arms.KeeperLamp lights Corvane's), and the iron's mask colours (COLOR_0/1, read only by the game's keeper_iron shader)
are left off, so a plain import draws it as its iron and glass.
"""
import argparse
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAMP = ROOT / "godot" / "art" / "props" / "keeper_lamp" / "keeper_lamp.glb"
GRIP_Y = 0.092
FILE = "props/hand_lamp.glb"


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def glb_read(path):
    b = path.read_bytes()
    n = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + n])
    rest = b[20 + n:]
    bn = struct.unpack("<I", rest[:4])[0]
    return j, rest[8:8 + bn]


def glb_write(path, j, binary):
    js = json.dumps(j, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    binary += b"\0" * (-len(binary) % 4)
    out = b"glTF" + struct.pack("<II", 2, 12 + 8 + len(js) + 8 + len(binary))
    out += struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binary)) + b"BIN\0" + binary
    path.write_bytes(out)


def lamp(out):
    j, binary = glb_read(LAMP)
    for m in j["meshes"]:
        for p in m["primitives"]:
            for k in ("COLOR_0", "COLOR_1"):
                p["attributes"].pop(k, None)
    violet = [srgb_to_linear(int("#a77bff"[i:i + 2], 16) / 255) for i in (1, 3, 5)]
    for mat in j["materials"]:
        if mat["name"] == "keeper_glass":
            mat["pbrMetallicRoughness"]["baseColorFactor"] = [*(c * 0.5 for c in violet), 1]
            mat["emissiveFactor"] = violet
        if mat["name"] == "keeper_iron":
            mat["pbrMetallicRoughness"].update(metallicFactor=0.6, roughnessFactor=0.6)
    scene = j["scenes"][j.get("scene", 0)]
    root = len(j["nodes"])
    j["nodes"].append({"name": "HandLamp", "translation": [0, -GRIP_Y, 0], "children": list(scene["nodes"])})
    scene["nodes"] = [root]
    out.parent.mkdir(parents=True, exist_ok=True)
    glb_write(out, j, binary)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--package", default="npc_folk_w")
    ap.add_argument("--slot", default="handslot.r")
    ap.add_argument("--carry", default="lamp")
    a = ap.parse_args()
    out = Path(a.out).resolve()
    lamp(out / FILE)
    m = json.loads((ROOT / "godot" / "art" / "npc" / a.package / "manifest.json").read_text(encoding="utf-8"))
    m["held"] = {a.slot: {"file": FILE, "carry": a.carry}}
    (out / "manifest.json").write_text(json.dumps(m, indent=1), encoding="utf-8")
    print(f"--npc-overlay {a.package}={out.as_posix()}")


if __name__ == "__main__":
    main()
