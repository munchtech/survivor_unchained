"""Quick look at a run: python sum.py NAME [fight] [--wait]
NAME is godot/balance/out/NAME.jsonl in the combat worktree; --wait waits for NAME.md (the run's end)."""
import sys, os, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a427a874da78cba8b\godot\balance\out"
name = sys.argv[1]
fight = next((a for a in sys.argv[2:] if not a.startswith("--")), None)
f = os.path.join(OUT, name + ".jsonl")
if "--wait" in sys.argv:
    while not os.path.exists(os.path.join(OUT, name + ".md")): time.sleep(5)
def run(*a): print(subprocess.run([sys.executable, *a], capture_output=True, text=True).stdout, end="")
run(os.path.join(HERE, "an.py"), f, "--by", "fight,policy")
run(os.path.join(HERE, "an.py"), f, "--by", "fight,tier,policy")
run(os.path.join(HERE, "an.py"), f, "--by", "fight,calling", "--hurt", "boss")
run(os.path.join(HERE, "falls.py"), f, *([fight] if fight else []))
