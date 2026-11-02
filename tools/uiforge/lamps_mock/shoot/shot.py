"""python shot.py NAME [game args]: one Godot run in ui-25 (her args added), shot to godot/.shots, inside a held godot turn."""
import os, subprocess, sys, time
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\ui-25"
G = os.path.join(W, "godot")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
HERE = os.path.dirname(os.path.abspath(__file__)); LOGS = os.path.join(HERE, "logs"); os.makedirs(LOGS, exist_ok=True)
name = sys.argv[1]
t0 = time.time()
args = ["--sex", "female", "--preset", "own", "--skin", "fair", "--eyes", "moss", "--hair", "braid", "--shot", name] + sys.argv[2:]
with open(os.path.join(LOGS, name + ".log"), "w", encoding="utf-8", errors="replace") as lf:
    p = subprocess.Popen([GODOT, "--path", G, "--resolution", "1920x1080", "--"] + args, stdout=lf, stderr=subprocess.STDOUT)
    try: p.wait(timeout=600)
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True); print(name, "TIMEOUT")
print(f"[{name}] {time.time()-t0:.0f} s, exit {p.returncode}", flush=True)
