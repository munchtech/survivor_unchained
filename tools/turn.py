"""Turns for heavy work, shared by every agent on this machine.

The machine has 32 GB of RAM and one GPU. ComfyUI alone holds 20-26 GB once
loaded, so two heavy jobs at once have crashed it. Take a turn before a heavy
job and give it back the moment the job ends; while you wait, do light work
(code, docs, design) instead of blocking.

  python tools/turn.py take gpu "face: MoGe batch"   # exit 0 = yours, 1 = busy (says who)
  python tools/turn.py take godot "legal: sprint clips" --wait 8
  python tools/turn.py give gpu                       # also frees ComfyUI's models
  python tools/turn.py show

gpu:   one holder. ComfyUI, TRELLIS, MoGe, and big Blender bakes or renders.
godot: three holders (each needs 5 GB of RAM free). Godot runs for pictures or clips (dotnet test needs none).

Run it from any worktree by its full path in the main checkout:
C:/Users/munch/Desktop/survivorsunchained/tools/turn.py
"""
import ctypes
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

HOME = Path.home() / ".su_turns"
SLOTS = {"gpu": 1, "godot": 3}
STALE = 3 * 3600  # a holder that never gave its turn back (crashed or forgotten)
LEAST_RAM = {"gpu": 0, "godot": 5}  # GB free needed, beyond the turn itself


def free_ram_gb():
    class M(ctypes.Structure):
        _fields_ = [("len", ctypes.c_ulong), ("load", ctypes.c_ulong),
                    ("total", ctypes.c_ulonglong), ("avail", ctypes.c_ulonglong),
                    ("pt", ctypes.c_ulonglong), ("pa", ctypes.c_ulonglong),
                    ("vt", ctypes.c_ulonglong), ("va", ctypes.c_ulonglong),
                    ("ve", ctypes.c_ulonglong)]
    m = M()
    m.len = ctypes.sizeof(M)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.avail / 2**30


def holders(kind):
    out = []
    for i in range(SLOTS[kind]):
        d = HOME / f"{kind}.{i}"
        note = d / "who.json"
        if d.exists():
            try:
                who = json.loads(note.read_text())
            except (OSError, ValueError):
                who = {"who": "?", "since": d.stat().st_mtime}
            out.append((d, who))
    return out


def try_take(kind, who):
    HOME.mkdir(exist_ok=True)
    for d, w in holders(kind):
        if time.time() - w["since"] > STALE:
            print(f"taking over a stale turn from {w['who']} ({(time.time() - w['since']) / 3600:.1f} h old)")
            (d / "who.json").unlink(missing_ok=True)
            d.rmdir()
    if free_ram_gb() < LEAST_RAM[kind]:
        return f"only {free_ram_gb():.1f} GB of RAM free"
    for i in range(SLOTS[kind]):
        d = HOME / f"{kind}.{i}"
        try:
            d.mkdir()  # atomic: only one agent can make it
        except FileExistsError:
            continue
        (d / "who.json").write_text(json.dumps({"who": who, "since": time.time()}))
        return None
    return "held by " + "; ".join(f"{w['who']} for {(time.time() - w['since']) / 60:.0f} min" for _, w in holders(kind))


def give(kind, who=None):
    hs = holders(kind)
    mine = [d for d, w in hs if w["who"] == who] or ([d for d, _ in hs] if len(hs) == 1 else [])
    if not mine and hs:
        sys.exit(f"{kind}: name the turn to give back, as you took it: " + "; ".join(w["who"] for _, w in hs))
    for d in mine[:1]:
        (d / "who.json").unlink(missing_ok=True)
        d.rmdir()
    if kind == "gpu":
        # The next holder needs the RAM ComfyUI is sitting on.
        try:
            req = urllib.request.Request("http://127.0.0.1:8188/free", method="POST",
                                         data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5)
        except OSError:
            pass


def show():
    print(f"{free_ram_gb():.1f} GB of RAM free")
    for kind in SLOTS:
        hs = holders(kind)
        print(f"{kind}: " + ("free" if not hs else "; ".join(
            f"{w['who']} for {(time.time() - w['since']) / 60:.0f} min" for _, w in hs)))


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "show":
        show()
    elif a[0] == "take":
        kind, who = a[1], (a[2] if len(a) > 2 and not a[2].startswith("--") else "someone")
        wait = float(a[a.index("--wait") + 1]) * 60 if "--wait" in a else 0
        end = time.time() + wait
        while (why := try_take(kind, who)) and time.time() < end:
            time.sleep(20)
        print(f"{kind}: yours" if not why else f"{kind}: busy, {why}. Do light work and try again.")
        sys.exit(0 if not why else 1)
    elif a[0] == "give":
        give(a[1], a[2] if len(a) > 2 else None)
        print(f"{a[1]}: given back")
