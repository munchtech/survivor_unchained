"""Turns for heavy work, shared by every agent on this machine.

The machine has 32 GB of RAM and one GPU. ComfyUI alone holds 20-26 GB once
loaded, so two heavy jobs at once have crashed it. Take a turn before a heavy
job and give it back the moment the job ends; while you wait, do light work
(code, docs, design) instead of blocking.

  python tools/turn.py take gpu "face: MoGe batch"   # exit 0 = yours, 1 = busy (says who)
  python tools/turn.py take godot "legal: sprint clips" --wait 8
  python tools/turn.py give gpu                       # also frees ComfyUI's models
  python tools/turn.py show

gpu:     one holder. ComfyUI, TRELLIS and MoGe: they share one server and most
         of the card's memory, and swapping their models thrashes 20 GB.
blender: two holders (each needs 6 GB of RAM free). Blender builds, bakes and
         renders: mostly CPU, a few GB each.
godot:   three holders (each needs 5 GB of RAM free). Godot runs for pictures or clips (dotnet test needs none).

Waiters are served in the order they first asked: whoever has asked longest
gets the next free turn, and giving a turn back then taking it again puts you
at the back. Asking again (or --wait) keeps your place; a place nobody has
asked for in 90 s lapses.

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
SLOTS = {"gpu": 1, "blender": 2, "godot": 3}
STALE = 3 * 3600  # a holder that never gave its turn back (crashed or forgotten)
LEAST_RAM = {"gpu": 0, "blender": 6, "godot": 5}  # GB free needed, beyond the turn itself
FRESH = 90  # seconds a place in the queue lasts without being asked again


def queue(kind, who):
    """Records that `who` is waiting for `kind` and returns the waiters, oldest
    first. (The fastest to ask used to win: one lead polling every few seconds
    took the GPU straight back while others waited an hour.)"""
    q = HOME / f"want_{kind}"
    q.mkdir(parents=True, exist_ok=True)
    me = q / ("".join(c if c.isalnum() else "_" for c in who)[:80] + ".json")
    now = time.time()
    try:
        first = json.loads(me.read_text())["first"]
    except (OSError, ValueError, KeyError):
        first = now
    me.write_text(json.dumps({"who": who, "first": first, "last": now}))
    out = []
    for f in q.glob("*.json"):
        try:
            w = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        if now - w.get("last", 0) > FRESH:
            f.unlink(missing_ok=True)
        else:
            out.append((w["first"], w["who"], f))
    return sorted(out)


def leave_queue(kind, who):
    q = HOME / f"want_{kind}"
    for f in q.glob("*.json") if q.exists() else []:
        try:
            if json.loads(f.read_text()).get("who") == who:
                f.unlink(missing_ok=True)
        except (OSError, ValueError):
            pass


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
        queue(kind, who)
        return f"only {free_ram_gb():.1f} GB of RAM free"
    names = [w for _, w, _ in queue(kind, who)]
    ahead = names[:names.index(who)] if who in names else []
    if len(ahead) >= SLOTS[kind] - len(holders(kind)):
        return "queued behind " + ", ".join(ahead) if ahead else "held by " + "; ".join(
            f"{w['who']} for {(time.time() - w['since']) / 60:.0f} min" for _, w in holders(kind))
    for i in range(SLOTS[kind]):
        d = HOME / f"{kind}.{i}"
        try:
            d.mkdir()  # atomic: only one agent can make it
        except FileExistsError:
            continue
        (d / "who.json").write_text(json.dumps({"who": who, "since": time.time()}))
        leave_queue(kind, who)
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
        q = HOME / f"want_{kind}"
        ws = []
        for f in q.glob("*.json") if q.exists() else []:
            try:
                w = json.loads(f.read_text())
                if time.time() - w["last"] <= FRESH:
                    ws.append((w["first"], w["who"]))
            except (OSError, ValueError, KeyError):
                pass
        if ws:
            print(f"  waiting: " + "; ".join(f"{w} ({(time.time() - t) / 60:.0f} min)" for t, w in sorted(ws)))


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
