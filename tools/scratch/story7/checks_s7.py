"""Run every story canon check in turn (seeds, signature phrases, the body's hours, genre words)."""
import os, subprocess, sys
S = os.path.dirname(os.path.abspath(__file__))
for n in ["seed_check", "phrases", "body_hours", "genre_check"]:
    print(f"== {n}", flush=True)
    r = subprocess.run([sys.executable, os.path.join(S, f"{n}_s7.py")], capture_output=True, text=True, encoding="utf-8", cwd=S)
    out = (r.stdout + r.stderr).strip().splitlines()
    print("\n".join(out[-25:]) if out else "(no output)", flush=True)
