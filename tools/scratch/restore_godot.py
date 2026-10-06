"""Put my worktree's godot/ back from where unblock.py moved it, then bring
its tracked files to the merged head (never touching the assets junction)."""
import os, subprocess
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab82cbe99e2937ddd"
S = os.path.dirname(os.path.abspath(__file__))
old = os.path.join(S, "merge_aside", "godot", "godot")
assert os.path.isdir(os.path.join(old, "src")), "old godot not found"
new_aside = os.path.join(S, "merge_aside", "godot_from_merge")
os.rename(os.path.join(WT, "godot"), new_aside)
os.rename(old, os.path.join(WT, "godot"))
print("godot back; junction:", os.path.isdir(os.path.join(WT, "godot", "assets", "people")))
st = subprocess.run(["git", "-C", WT, "status", "--porcelain", "--", "godot"], capture_output=True, text=True).stdout.splitlines()
fix = [l[3:] for l in st if l[:2] in (" M", " D", "MM", "AM") and l[3:] != "godot/assets"]
print("tracked paths to restore:", len(fix))
for i in range(0, len(fix), 200):
    subprocess.run(["git", "-C", WT, "checkout", "--"] + fix[i:i + 200], check=True)
st = subprocess.run(["git", "-C", WT, "status", "--porcelain", "--", "godot"], capture_output=True, text=True).stdout.splitlines()
print("left changed:", [l for l in st if not l.startswith("??")][:10])
