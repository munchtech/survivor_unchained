"""Import the worktree's new assets into its .godot cache (headless editor), in a Godot turn.
python imp.py [--wait MIN]"""
import os, subprocess, sys

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7a4c20bcfd7ccfd3\godot"
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
TURN = r"C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
HERE = os.path.dirname(os.path.abspath(__file__))
wait = sys.argv[sys.argv.index("--wait") + 1] if "--wait" in sys.argv else "0"
who = "cinematics: import new assets"
if subprocess.run([sys.executable, TURN, "take", "godot", who, "--wait", wait]).returncode != 0:
    sys.exit(1)
log = os.path.join(HERE, "imp.log")
try:
    with open(log, "w", encoding="utf-8", errors="replace") as lf:
        p = subprocess.Popen([GODOT, "--headless", "--editor", "--import", "--path", WT], stdout=lf, stderr=subprocess.STDOUT)
        try:
            p.wait(timeout=900)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
            print("TIMEOUT")
finally:
    subprocess.run([sys.executable, TURN, "give", "godot", who])
errs = [l.rstrip() for l in open(log, encoding="utf-8", errors="replace") if "ERROR" in l]
print(len(errs), "error lines"); print("\n".join(errs[:15]))
