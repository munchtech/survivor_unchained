"""Face 30 round 3: install the built ponytail, braid and pixie (gltf, bin, chain.json) from a build dir and reimport (godot turn).
    python s3_install.py <build dir>"""
import os, shutil, subprocess, sys
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0"
G = os.path.join(W, "godot"); ART = os.path.join(G, "art", "people")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
TP = os.path.join(W, "tools", "turn.py")
for s in ("ponytail", "braid", "pixie"):
    for ext in (".gltf", ".bin", ".chain.json"):
        if os.path.exists(os.path.join(sys.argv[1], f"heroine_hair_{s}{ext}")): shutil.copy2(os.path.join(sys.argv[1], f"heroine_hair_{s}{ext}"), os.path.join(ART, f"heroine_hair_{s}{ext}"))
if subprocess.run([sys.executable, TP, "take", "godot", "face30: r3 import", "--wait", "3600", "--root", W, "--stale-ok"]).returncode != 0: sys.exit(1)
try:
    r = subprocess.run([GODOT, "--headless", "--path", G, "--import"], capture_output=True, text=True, timeout=1200)
    print("import exit", r.returncode)
finally:
    subprocess.run([sys.executable, TP, "give", "godot", "face30: r3 import"])
