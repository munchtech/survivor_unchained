"""Lookdev render helper: python ld.py out.png [WxH] [clip] KEY=VAL ...
Runs godot/tools_scenes/lookdev.gd in my worktree with the given environment."""
import os, subprocess, sys
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab82cbe99e2937ddd"
G = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
S = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
out = args.pop(0)
if not os.path.isabs(out):
    out = os.path.join(S, "r", out)
os.makedirs(os.path.dirname(out), exist_ok=True)
res = "1920x1080"
clip = "Idle"
env = dict(os.environ)
env.setdefault("BODY", "hero")
for a in args:
    if "=" in a:
        k, v = a.split("=", 1)
        env[k] = v
    elif "x" in a and a.replace("x", "").isdigit():
        res = a
    else:
        clip = a
p = subprocess.run([G, "--path", os.path.join(WT, "godot"), "--resolution", res, "-s", "res://tools_scenes/lookdev.gd", "--", clip, out],
                   env=env, capture_output=True, text=True, errors="replace")
for line in (p.stdout + p.stderr).splitlines():
    if ("ERROR" in line or "SCRIPT" in line) and not any(k in line for k in ("leaked", "never freed", "Pages in use", "still in use")):
        print(line[:300])
print(out, os.path.exists(out))
