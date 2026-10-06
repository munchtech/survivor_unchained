"""A screenshot with whatever build is in place (no DLL copied):
    python gshot.py NAME [game args...]
2560x1440, --fixed-fps 60. Saves godot/.shots/NAME*.png in this lead's worktree."""
import subprocess
import sys

W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0eb8c612c94d4aa5"
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
name, rest = sys.argv[1], sys.argv[2:]
cmd = [GODOT, "--path", W + r"\godot", "--resolution", "2560x1440", "--fixed-fps", "60", "--", "--shot", name, *rest]
p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
for l in p.stdout.splitlines() + p.stderr.splitlines():
    if l.startswith("saved") or "ERROR" in l or "SHADER" in l or "error" in l.lower():
        print(l[:300])
print("exit", p.returncode)
