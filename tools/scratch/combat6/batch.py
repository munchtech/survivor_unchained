"""One Godot turn: import, then every fight's frames at 1920x1080, one after another.
python batch.py [--no-import] [only...]"""
import subprocess, sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a739d6792d21f5efd\godot"
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
base = ["--quick", "warden", "--sex", "female", "--auto"]
runs = [
    ("h_way", 900, ["--night", "hollow", "--stage", "2", "--every", "4", "--count", "30"]),
    ("h_boss", 900, ["--night", "hollow", "--stage", "3", "--on", "boss", "--until", "260"]),
    ("r_way", 900, ["--night", "roost", "--every", "5", "--count", "45"]),
    ("r_boss", 900, ["--night", "roost", "--stage", "3", "--on", "boss", "--until", "240"]),
    ("d_way", 900, ["--night", "dig", "--every", "5", "--count", "54"]),
    ("d_boss", 900, ["--night", "dig", "--stage", "3", "--on", "boss", "--until", "280"]),
]
only = [a for a in sys.argv[1:] if not a.startswith("--")]
if "--no-import" not in sys.argv:
    t0 = time.time()
    with open(os.path.join(HERE, "logs", "import.log"), "w", encoding="utf-8", errors="replace") as fh:
        subprocess.run([GODOT, "--headless", "--path", WT, "--import"], stdout=fh, stderr=subprocess.STDOUT, timeout=1800)
    print(f"import {time.time() - t0:.0f}s", flush=True)
for name, tmo, args in runs:
    if only and name not in only: continue
    r = subprocess.run([sys.executable, os.path.join(HERE, "play.py"), name, "--timeout", str(tmo), "--", *base, *args], capture_output=True, text=True)
    print(r.stdout.strip(), flush=True)
