"""One Godot turn: pack her and his libraries, then run the game for frames.
python gamerun.py NAME [game args...]  (frames land in godot/.shots/NAME_XX.png)"""
import subprocess
import sys
from pathlib import Path

WT = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
TURN = r"C:\Users\munch\Desktop\survivorsunchained\tools\turn.py"
sys.path.insert(0, str(WT / "tools" / "anim"))
name, rest = sys.argv[1], [a for a in sys.argv[2:] if a != "--pack"]
who = f"animation: game {name}"
if subprocess.run([sys.executable, TURN, "take", "godot", who, "--wait", "900"]).returncode:
    sys.exit(1)
try:
    if "--pack" in sys.argv:
        import build
        build.pack()
        build.pack(WT / "tools" / "anim" / "out" / "hero", "hero")
    args = [GODOT, "--path", str(WT / "godot"), "--resolution", "1920x1080", "--fixed-fps", "30", "--", "--shot", name] + rest
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1200)
    lines = (r.stdout + r.stderr).splitlines()
    print("\n".join(l[:240] for l in lines if "saved" in l.lower() or "ERROR" in l or "Exception" in l)[:4000])
finally:
    subprocess.run([sys.executable, TURN, "give", "godot", who])
