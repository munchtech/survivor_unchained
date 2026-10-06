"""One Godot turn for a batch of renders: python batch.py NAME "cmd1" "cmd2" ...
Each command is a scratch tool's arguments (prev.py/ho.py ...), run with --noturn while the turn is held.
The C# is built once first (the tools then skip nothing: their own build is quick when up to date)."""
import os, shlex, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
TURN = r"C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
name, cmds = sys.argv[1], sys.argv[2:]
who = f"cinematics: batch {name}"
t0 = time.time()
if subprocess.run([sys.executable, TURN, "take", "godot", who, "--wait", "90"]).returncode != 0:
    print("no turn"); sys.exit(1)
try:
    for c in cmds:
        a = shlex.split(c)
        print(f"=== {c}", flush=True)
        r = subprocess.run([sys.executable, os.path.join(HERE, a[0])] + a[1:] + ["--noturn"], capture_output=True, text=True)
        print(r.stdout[-6000:], r.stderr[-1500:], flush=True)
finally:
    subprocess.run([sys.executable, TURN, "give", "godot", who])
print(f"batch {name} done in {time.time() - t0:.0f} s")
