"""Face 30 r3: debug shots (H1DBG modes) in one godot turn.  python dbg.py <logs> name:face:style:turn:mode[:extra+args] ..."""
import os, subprocess, sys, time
sys.argv, rest = sys.argv[:2], sys.argv[2:]
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0"
G = os.path.join(W, "godot"); TP = os.path.join(W, "tools", "turn.py")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
PZ = {"own": ("fair", "moss"), "saffron": ("warm", "peat"), "sunborn": ("brown", "sloe")}
LOGS = sys.argv[1]; os.makedirs(LOGS, exist_ok=True)
if subprocess.run([sys.executable, TP, "take", "godot", "face30: r3 dbg", "--wait", "3600", "--root", W, "--stale-ok"]).returncode != 0: sys.exit(1)
try:
    for spec in rest:
        name, f, s, d, mode, *ex = spec.split(":")
        sk, ey = PZ[f]
        a = ["--seconds", "10", "--turn", d, "--hair", s, "--new", "--sex", "female", "--step", "1", "--part", "0", "--open-eyes", "--preset", f, "--skin", sk, "--eyes", ey] + (ex[0].split("+") if ex else [])
        env = dict(os.environ); env["H1DBG"] = mode.replace("+", ",")
        with open(os.path.join(LOGS, name + ".log"), "w") as lf:
            subprocess.run([GODOT, "--path", G, "--resolution", "1920x1080", "--", "--shot", name] + a, stdout=lf, stderr=subprocess.STDOUT, env=env, timeout=300)
        print(name, "done", flush=True)
finally:
    subprocess.run([sys.executable, TP, "give", "godot", "face30: r3 dbg"])
