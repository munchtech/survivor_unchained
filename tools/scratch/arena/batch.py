"""Run several game shots in turn: python batch.py SPEC.txt
Each line of SPEC: NAME | game args (after --). Lines starting with # are skipped.
Frames land in godot/.shots of the arena worktree; a summary prints at the end."""
import subprocess, sys, os, time

HERE = os.path.dirname(os.path.abspath(__file__))
spec = open(sys.argv[1], encoding="utf-8").read().splitlines()
t0 = time.time()
for line in spec:
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    name, args = [p.strip() for p in line.split("|", 1)]
    r = subprocess.run([sys.executable, os.path.join(HERE, "play.py"), name, "--timeout", "900", "--"] + args.split(),
                       capture_output=True, text=True)
    print(r.stdout.strip().splitlines()[0] if r.stdout.strip() else name + ": no output", flush=True)
print(f"batch done in {time.time() - t0:.0f}s")
