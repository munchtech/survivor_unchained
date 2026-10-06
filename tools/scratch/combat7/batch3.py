"""The third Godot turn: the fixes seen. The knee's choice laid out, a night let go standing down, and the
Vault's standards and cover. python batch3.py [only...]"""
import subprocess, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
base = ["--quick", "warden", "--sex", "female", "--log", "10"]
runs = [
    ("c7c_roost", 1200, ["--auto", "--night", "roost", "--stage", "3", "--on", "boss", "--end", "--seconds", "3", "--every", "30", "--count", "14", "--until", "420"]),
    ("c7c_letgo", 600, ["--auto", "idle", "--night", "hollow", "--stage", "3", "--die", "10", "--choose", "letgo", "--seconds", "9", "--every", "0.5", "--count", "16", "--until", "40", "--end"]),
    ("c7c_vstd", 600, ["--auto", "--night", "vault", "--stage", "2", "--seconds", "3", "--every", "4", "--count", "6"]),
]
only = [a for a in sys.argv[1:] if not a.startswith("--")]
for name, tmo, args in runs:
    if only and name not in only: continue
    r = subprocess.run([sys.executable, os.path.join(HERE, "play.py"), name, "--timeout", str(tmo), "--", *base, *args], capture_output=True, text=True)
    print(r.stdout.strip(), flush=True)
