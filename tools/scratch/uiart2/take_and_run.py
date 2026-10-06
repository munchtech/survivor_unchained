"""Wait for a turn, run a script inside it, always give the turn back.
    python take_and_run.py KIND "who: job" WAIT_MINUTES script.py [args...]"""
import subprocess
import sys

TURN = r"C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
kind, who, wait, script = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
r = subprocess.run([sys.executable, TURN, "take", kind, who, "--wait", wait])
if r.returncode != 0:
    print("no turn", flush=True)
    sys.exit(1)
try:
    rc = subprocess.run([sys.executable, script] + sys.argv[5:]).returncode
finally:
    subprocess.run([sys.executable, TURN, "give", kind, who])
print("done", rc, flush=True)
