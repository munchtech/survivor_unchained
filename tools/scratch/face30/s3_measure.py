"""Face 30 S3: the game's hair dump at creation's Look (face own, warden) for ponytail and braid: idle turn 0, idle
turn 180, spin 90, spin 360. Holds a godot turn. Then posed_clip.py on the runs.
    python s3_measure.py <out dir> [styles...]"""
import os, subprocess, sys, time
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0"
G = os.path.join(W, "godot")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
TP = os.path.join(W, "tools", "turn.py")
OUT = os.path.abspath(sys.argv[1]); STY = sys.argv[2:] or ["ponytail", "braid"]
os.makedirs(OUT, exist_ok=True)
def look(s, d, secs):
    return ["--seconds", str(secs), "--turn", str(d), "--hair", s, "--new", "--sex", "female", "--step", "1", "--part", "0",
            "--open-eyes", "--preset", "own", "--skin", "fair", "--eyes", "moss"]
RUNS = [("idle0", 0, 7, []), ("idle180", 180, 7, []), ("spin90", 0, 9, ["--spin", "90"]), ("spin180", 0, 7, ["--spin", "180"]), ("spin360", 0, 5.5, ["--spin", "360"])]
if os.environ.get("NOTURN") != "1" and subprocess.run([sys.executable, TP, "take", "godot", "face30: s3 measure", "--wait", "3600", "--root", W]).returncode != 0:
    print("TURN REFUSED"); sys.exit(1)
dirs = []
try:
    for s in STY:
        for tag, d, secs, extra in RUNS:
            rd = os.path.join(OUT, f"{s}_{tag}"); os.makedirs(rd, exist_ok=True)
            for f in os.listdir(rd): os.remove(os.path.join(rd, f))
            t0 = time.time()
            with open(rd + ".log", "w", encoding="utf-8", errors="replace") as lf:
                p = subprocess.Popen([GODOT, "--path", G, "--resolution", "1280x720", "--", "--shot", f"s3m_{s}_{tag}"] + look(s, d, secs) + extra + ["--hairdump", rd],
                                     stdout=lf, stderr=subprocess.STDOUT)
                try: p.wait(timeout=240)
                except subprocess.TimeoutExpired:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True); print(tag, "TIMEOUT")
            print(f"[{s}_{tag}] {len(os.listdir(rd))} files, {time.time()-t0:.0f} s", flush=True)
            dirs.append(rd)
finally:
    if os.environ.get("NOTURN") != "1": subprocess.run([sys.executable, TP, "give", "godot", "face30: s3 measure"])
r = subprocess.run([sys.executable, os.path.join(W, "tools", "scratch", "face29", "posed_clip.py")] + dirs, capture_output=True, text=True)
open(os.path.join(OUT, "report.txt"), "w", encoding="utf-8").write(r.stdout + r.stderr)
print(r.stdout[-6000:], r.stderr[-2000:])
