"""The second Godot turn: the knees' choices (the bosses from their openings, the autopilot drafting as a
player does), and the Vault whole and from its boss. python batch2.py [only...]"""
import subprocess, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
base = ["--quick", "warden", "--sex", "female", "--auto", "--log", "10", "--on", "boss", "--end"]
boss = ["--stage", "3", "--seconds", "3", "--every", "5", "--count", "84", "--until", "420"]
whole = ["--seconds", "8", "--every", "10", "--count", "90", "--until", "900"]
runs = [
    ("c7b_roost", 1200, ["--night", "roost", *boss]),
    ("c7b_hollow", 1200, ["--night", "hollow", "--facts", "promise.pack=true,stream.clear=true", "--knee", "finish", *boss]),
    ("c7b_vboss", 1200, ["--night", "vault", *boss]),
    ("c7b_vault", 1800, ["--night", "vault", *whole]),
]
only = [a for a in sys.argv[1:] if not a.startswith("--")]
for name, tmo, args in runs:
    if only and name not in only: continue
    r = subprocess.run([sys.executable, os.path.join(HERE, "play.py"), name, "--timeout", str(tmo), "--", *base, *args], capture_output=True, text=True)
    print(r.stdout.strip(), flush=True)
