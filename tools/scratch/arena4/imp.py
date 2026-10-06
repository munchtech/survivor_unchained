"""Godot's incremental import in the arena worktree (only what changed): python imp.py
Takes a godot turn (tools/turn.py) and gives it back."""
import subprocess, sys, time
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0b61c278bdd5c994\godot"
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
TURN = r"C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
WHO = "arena art: import"
r = subprocess.run([sys.executable, TURN, "take", "godot", WHO, "--wait", "60"], capture_output=True, text=True)
print(r.stdout.strip())
if r.returncode != 0:
    sys.exit(1)
try:
    t0 = time.time()
    r = subprocess.run([GODOT, "--headless", "--path", WT, "--import"], capture_output=True, text=True, errors="replace", timeout=1200)
    lines = [l for l in (r.stdout + r.stderr).splitlines() if "reimport" in l or "ERROR" in l]
    print(f"import done in {time.time() - t0:.0f}s, {sum('reimport' in l for l in lines)} reimported")
    for l in [l for l in lines if "ERROR" in l][:10]:
        print(l[:200])
finally:
    subprocess.run([sys.executable, TURN, "give", "godot", WHO], capture_output=True)
