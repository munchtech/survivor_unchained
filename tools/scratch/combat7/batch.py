"""One Godot turn: import, then each story fight whole at 1920x1080 on the autopilot, one after another.
python batch.py [--no-import] [only...]
A frame every 10 s, each boss move tagged (--on boss), the choice at his knee (tag 'choice'), the result
(tag 'result'); the run ends at the night's result (--end)."""
import subprocess, sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a427a874da78cba8b\godot"
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
base = ["--quick", "warden", "--sex", "female", "--auto", "--log", "10", "--seconds", "8", "--every", "10", "--count", "90", "--on", "boss", "--until", "900", "--end"]
runs = [
    # Where she promised and the stream is clean, his end is her choice: finished, here.
    ("c7_hollow", 1800, ["--night", "hollow", "--facts", "promise.pack=true,stream.clear=true", "--knee", "finish"]),
    # Redcowl's knee: spared, here.
    ("c7_roost", 1800, ["--night", "roost"]),
    ("c7_dig", 1800, ["--night", "dig"]),
]
only = [a for a in sys.argv[1:] if not a.startswith("--")]
if "--no-import" not in sys.argv:
    t0 = time.time()
    os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    with open(os.path.join(HERE, "logs", "import.log"), "w", encoding="utf-8", errors="replace") as fh:
        subprocess.run([GODOT, "--headless", "--path", WT, "--import"], stdout=fh, stderr=subprocess.STDOUT, timeout=1800)
    print(f"import {time.time() - t0:.0f}s", flush=True)
for name, tmo, args in runs:
    if only and name not in only: continue
    r = subprocess.run([sys.executable, os.path.join(HERE, "play.py"), name, "--timeout", str(tmo), "--", *base, *args], capture_output=True, text=True)
    print(r.stdout.strip(), flush=True)
