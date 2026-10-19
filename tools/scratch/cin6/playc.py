"""python playc.py NAME [COUNT]: the Prologue in real play with every cinematic (--cines), the autopilot
playing; a frame every 10 s to godot/.shots/NAME_NN.png, log to logs/NAME.log. Takes and gives a godot turn."""
import os, subprocess, sys, time
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a59432fe3bfc6eb92"
G = os.path.join(W, "godot")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
HERE = os.path.dirname(os.path.abspath(__file__)); LOGS = os.path.join(HERE, "logs")
TP = os.path.join(W, "tools", "turn.py")
name = sys.argv[1]; count = sys.argv[2] if len(sys.argv) > 2 else "48"
b = subprocess.run(["dotnet", "build", os.path.join(G, "SurvivorUnchained.csproj"), "-v", "q", "-nologo"], capture_output=True, text=True)
if b.returncode != 0: print(b.stdout[-3000:]); sys.exit(1)
TURN = "cinematics: real-play " + name
if subprocess.run([sys.executable, TP, "take", "godot", TURN, "--wait", "3600", "--root", W]).returncode != 0:
    print("TURN REFUSED"); sys.exit(1)
try:
    t0 = time.time()
    args = ["--quick", "warden", "--sex", "female", "--zone", "lowford", "--auto", "--cines",
            "--shot", name, "--seconds", "3", "--every", "10", "--count", count,
            "--preset", "own", "--skin", "fair", "--eyes", "moss", "--hair", "braid"]
    with open(os.path.join(LOGS, name + ".log"), "w", encoding="utf-8", errors="replace") as lf:
        p = subprocess.Popen([GODOT, "--path", G, "--resolution", "1920x1080", "--"] + args, stdout=lf, stderr=subprocess.STDOUT)
        try: p.wait(timeout=3000)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True); print(name, "TIMEOUT")
    print(f"[{name}] {time.time()-t0:.0f} s")
finally:
    subprocess.run([sys.executable, TP, "give", "godot", TURN])
print("DONE")
