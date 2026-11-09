"""Is this checkout rendering the current game? Run before a judged shot.

  python tools/freshness.py            # report; exit 1 if stale
  (tools/turn.py take godot|blender runs it on the caller's checkout, or --root <path>,
   and refuses a stale one unless --stale-ok)

Two checks, local and free (no model tokens):
1. Behind integration: commits on claude/vigilant-galileo-l6jqyx that touch her body, outfits,
   shaders, clips or weapons and aren't in HEAD. Fix: git merge claude/vigilant-galileo-l6jqyx
2. Godot's import cache: a model whose .godot/imported md5 no longer matches the file
   (14 Oct: a judge saw the old body after a merge). Fix: Godot_console.exe --headless --path godot --import
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

INTEGRATION = "claude/vigilant-galileo-l6jqyx"
WATCHED = ["godot/art/people", "godot/art/npc", "godot/art/anim", "godot/shaders", "public/assets/weapons", "godot/tools_scenes"]
MODELS = ["art/people", "art/npc", "assets/weapons"]  # res:// folders whose .glb/.gltf imports are checked


def git(*a, cwd):
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True).stdout.strip()


def behind(root):
    if git("rev-parse", "--verify", "-q", INTEGRATION, cwd=root) == "":
        return []
    out = git("log", "--oneline", f"HEAD..{INTEGRATION}", "--", *WATCHED, cwd=root)
    return out.splitlines() if out else []


def stale_imports(root):
    g = root / "godot"
    imp = g / ".godot" / "imported"
    bad = []
    if not imp.is_dir():
        return bad
    for folder in MODELS:
        d = g / folder
        if not d.is_dir():
            continue
        for f in list(d.rglob("*.glb")) + list(d.rglob("*.gltf")):
            res = "res://" + f.relative_to(g).as_posix()
            m = imp / f"{f.name}-{hashlib.md5(res.encode()).hexdigest()}.md5"
            if not m.is_file():
                continue
            src = next((l.split('"')[1] for l in m.read_text().splitlines() if l.startswith("source_md5")), "")
            h = hashlib.md5()
            with open(f, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 22), b""):
                    h.update(chunk)
            if src and src != h.hexdigest():
                bad.append(res)
    return bad


TEX_EXT = {".png", ".jpg", ".jpeg", ".webp", ".exr", ".hdr", ".tga", ".svg"}
GODOT_CONSOLE = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"


def _stored_md5(m):
    return next((l.split('"')[1] for l in m.read_text().splitlines() if l.startswith("source_md5")), "")


def stale_textures(root):
    """res:// paths of textures under godot/art whose file changed since Godot imported them (also texture arrays)."""
    root = Path(root)
    g = root / "godot"
    imp = g / ".godot" / "imported"
    bad = []
    if not imp.is_dir() or not (g / "art").is_dir():
        return bad
    for dp, _, names in os.walk(g / "art"):
        for n in names:
            if os.path.splitext(n)[1].lower() not in TEX_EXT:
                continue
            f = Path(dp) / n
            if not (Path(dp) / (n + ".import")).is_file():
                continue
            res = "res://" + f.relative_to(g).as_posix()
            m = imp / f"{n}-{hashlib.md5(res.encode()).hexdigest()}.md5"
            if not m.is_file() or f.stat().st_mtime <= m.stat().st_mtime:
                continue
            src = _stored_md5(m)
            h = hashlib.md5()
            with open(f, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 22), b""):
                    h.update(chunk)
            if src and src != h.hexdigest():
                bad.append(res)
    return bad


def reimport_if_stale(root):
    """Re-import when models or textures are stale, so a shoot never draws old .ctex. True if clean afterwards."""
    root = Path(root)
    n = len(stale_imports(root)) + len(stale_textures(root))
    if not n:
        return True
    exe = os.environ.get("GODOT_CONSOLE", GODOT_CONSOLE)
    print(f"freshness: {n} stale import(s); running Godot --import (up to 20 min)", flush=True)
    try:
        subprocess.run([exe, "--headless", "--path", str(root / "godot"), "--import"], timeout=1200)
    except subprocess.TimeoutExpired:
        print("freshness: --import timed out", flush=True)
    left = len(stale_imports(root)) + len(stale_textures(root))
    print(f"freshness: {left} stale after re-import", flush=True)
    return left == 0


def toplevel(path):
    """The checkout (main or worktree) holding path, or '' outside one."""
    return git("rev-parse", "--show-toplevel", cwd=path)


def check(root=None, imports=True):
    """Returns a list of problem lines for the checkout at root (default: the caller's); empty means fresh."""
    root = Path(root or toplevel(Path.cwd()) or ".")
    probs = []
    b = behind(root)
    if b:
        probs.append(f"{len(b)} integration commit(s) touching her art/shaders/clips are not merged here "
                     f"(newest: {b[0]}). Fix: git merge {INTEGRATION}")
    if imports:
        s = stale_imports(root)
        if s:
            probs.append(f"Godot import cache is stale for {len(s)} model(s) ({', '.join(s[:4])}"
                         f"{'...' if len(s) > 4 else ''}). Fix: Godot_console.exe --headless --path godot --import")
        t = stale_textures(root)
        if t:
            probs.append(f"Godot import cache is stale for {len(t)} texture(s) ({', '.join(t[:10])}"
                         f"{'...' if len(t) > 10 else ''}). Fix: Godot_console.exe --headless --path godot --import")
    return probs


if __name__ == "__main__":
    p = check()
    print("\n".join("STALE: " + x for x in p) if p else "fresh: this checkout renders the current game")
    sys.exit(1 if p else 0)
