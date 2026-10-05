"""Godot .import files for new pictures and sounds, written as the editor would write them, so
what is added ships without waiting for someone's next Godot import. Each copies a sibling's
settings (a shipped icon's for a .png, a shipped take's for a .wav), names the imported file
by the md5 of its res path, and gets a fresh uid in Godot's alphabet, checked against every
uid the project already uses. A file that already has its .import is left alone.

    python tools/uiforge/imports.py godot/art/ui/coal/coal_0.png godot/art/sound/chainLink_0.wav ...
"""
from __future__ import annotations

import hashlib
import os
import re
import secrets
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GODOT = os.path.join(ROOT, "godot")
TEMPLATES = {".png": ("art/ui/icons/item/pelt.png.import", "ctex"), ".wav": ("art/sound/anvil_0.wav.import", "sample")}


def taken_uids():
    taken = set()
    for root, dirs, files in os.walk(GODOT):
        dirs[:] = [d for d in dirs if d != ".godot"]
        for f in files:
            if f.endswith((".import", ".uid", ".tscn", ".tres")):
                try:
                    taken.update(re.findall(r"uid://([a-z0-9]+)", open(os.path.join(root, f), encoding="utf-8", errors="ignore").read()))
                except OSError:
                    pass
    return taken


def new_uid(taken):
    """ResourceUID::id_to_text: base 34 ('a'..'y' then '0'..'8') of a 63-bit id, unused."""
    while True:
        n = secrets.randbits(63)
        s = ""
        while True:
            c = n % 34
            s = (chr(ord("a") + c) if c < 25 else chr(ord("0") + c - 25)) + s
            n //= 34
            if not n:
                break
        if s not in taken:
            taken.add(s)
            return s


def write(paths):
    taken = taken_uids()
    made = []
    for p in paths:
        p = os.path.abspath(p)
        ext = os.path.splitext(p)[1].lower()
        if ext not in TEMPLATES or os.path.exists(p + ".import"):
            continue
        tpl, kind = TEMPLATES[ext]
        text = open(os.path.join(GODOT, tpl), encoding="utf-8").read()
        rel = os.path.relpath(p, GODOT).replace("\\", "/")
        res = "res://" + rel
        dest = f"res://.godot/imported/{os.path.basename(p)}-{hashlib.md5(res.encode()).hexdigest()}.{kind}"
        text = re.sub(r'uid="uid://[a-z0-9]+"', f'uid="uid://{new_uid(taken)}"', text)
        text = re.sub(r'path="res://\.godot/imported/[^"]+"', f'path="{dest}"', text)
        text = re.sub(r'source_file="[^"]+"', f'source_file="{res}"', text)
        text = re.sub(r'dest_files=\["[^"]+"\]', f'dest_files=["{dest}"]', text)
        with open(p + ".import", "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        made.append(p + ".import")
    return made


if __name__ == "__main__":
    for m in write(sys.argv[1:]):
        print(m)
