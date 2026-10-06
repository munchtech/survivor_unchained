"""Runs of the game in this lead's worktree, one after another (inside a Godot turn).
    python shoot.py RUNSFILE
RUNSFILE: one run per line, "NAME | RES | FPS | game args..." (FPS 0: real time, no --fixed-fps).
Prints each run's saved/probe/perf/error lines and its time."""
import subprocess
import sys
import time

W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad57a6dd0798688d7"
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
KEEP = ("saved", "probe:", "perf ", "ERROR", "SHADER", "Unhandled", "Exception", "flip")

for line in open(sys.argv[1], encoding="utf-8"):
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    name, res, fps, args = [s.strip() for s in line.split("|", 3)]
    cmd = [GODOT, "--path", W + r"\godot", "--resolution", res]
    if fps != "0":
        cmd += ["--fixed-fps", fps]
    cmd += ["--"] + args.split()
    if "--shot" not in args and "--perf" not in args:
        pass
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
        out = p.stdout.splitlines() + p.stderr.splitlines()
        code = p.returncode
    except subprocess.TimeoutExpired as e:
        out, code = (e.stdout or "").splitlines() if isinstance(e.stdout, str) else [], "timeout"
    saved = [l for l in out if l.startswith("saved")]
    print(f"== {name} ({res}, fps {fps}): exit {code}, {time.time() - t0:.0f} s, {len(saved)} saved")
    noise = ("Unable to open file", "Failed loading", "Error loading", "Cannot open file", "were leaked", "get_singleton()")
    for l in out:
        if any(k in l for k in KEEP) and not l.startswith("saved") and not any(n in l for n in noise):
            print("   " + l[:260])
    # Where she was in each picture (for crops), kept beside the pictures.
    with open(W + r"\godot\.shots\her_at.txt", "a", encoding="utf-8") as f:
        for l in saved:
            f.write(l + "\n")
    sys.stdout.flush()
