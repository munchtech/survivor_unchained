"""The fourth Godot turn: the knees' choices laid out, the bosses brought on at a twentieth (--bosshp).
python batch4.py [only...]"""
import subprocess, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
base = ["--quick", "warden", "--sex", "female", "--log", "10", "--auto", "--stage", "3", "--bosshp", "0.05", "--on", "boss", "--end",
        "--seconds", "3", "--every", "20", "--count", "8", "--until", "200"]
runs = [
    ("c7d_roost", 600, ["--night", "roost"]),
    ("c7d_hollow", 600, ["--night", "hollow", "--facts", "promise.pack=true,stream.clear=true"]),
]
only = [a for a in sys.argv[1:] if not a.startswith("--")]
for name, tmo, args in runs:
    if only and name not in only: continue
    r = subprocess.run([sys.executable, os.path.join(HERE, "play.py"), name, "--timeout", str(tmo), "--", *base, *args], capture_output=True, text=True)
    print(r.stdout.strip(), flush=True)
