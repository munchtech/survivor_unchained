"""python frames.py ROUND VARIANTS SETS ["try=k=v,..."] [stale]: the style frames, in one godot turn.

VARIANTS, comma-separated: g (as built, with --grade-dump: the live table, for relighting her in the
paint-overs), r (--grade off: the raw frame the paint-overs start from), t (--grade-try SPEC: direction A).
SETS, comma-separated: town (the square, the east road, the north street by day), ford (Low Ford by
night: camp, road A, road B, the ford, the wood road, two ford lamps), close (the close view at camp,
closest zoom, twice facing away from the fire and twice facing it).
Frames land in godot/.shots/ as ROUND_SET_VARIANT_*.png; tables as godot/.shots/ROUND_SET_g.bin.
"""
import os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
G = os.path.join(W, "godot")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
TP = r"C:\Users\munch\Desktop\survivorsunchained\tools\turn.py"
HER = ["--quick", "warden", "--sex", "female", "--preset", "own", "--skin", "fair", "--eyes", "moss", "--hair", "braid", "--seed", "7", "--nohud", "--no-labels"]
NIGHT = ["--zone", "lowford", "--facts", "prologue.woke=true", "--auto", "idle"]
SETS = {
    "town": (["--zone", "waystation", "--time", "day", "--auto", "idle", "--spots", "3,3;24,0;0,-24"], 3),
    "ford": (NIGHT + ["--spots", "-7.5,87.5;3,64;9,40;0,-38;-2,-72;0,-37;-7,-46"], 7),
    "close": (NIGHT + ["--spots", "-8.6,88.6,1,0;-8.6,88.6,1,0;-9.5,92.5,1,0;-9.5,92.5,1,0"], 4),
}
rnd, variants, sets = sys.argv[1], sys.argv[2].split(","), sys.argv[3].split(",")
spec = next((a[4:] for a in sys.argv[4:] if a.startswith("try=")), None)
# try.SET=SPEC: that set's own spec (the day and the night want their own shadow colour)
specs = {a[4:].split("=", 1)[0]: a[4:].split("=", 1)[1] for a in sys.argv[4:] if a.startswith("try.")}
stale = "stale" in sys.argv[4:]
if "t" in variants and not (spec or all(s in specs for s in sets)): sys.exit("variant t needs try=SPEC or try.SET=SPEC per set")
shots = os.path.join(G, ".shots"); os.makedirs(shots, exist_ok=True)
logs = os.path.join(HERE, "logs"); os.makedirs(logs, exist_ok=True)
b = subprocess.run(["dotnet", "build", os.path.join(G, "SurvivorUnchained.csproj"), "-v", "q", "-nologo"], capture_output=True, text=True)
if b.returncode != 0: print(b.stdout[-3000:]); sys.exit(1)
TURN = "art-style: frames " + rnd
if subprocess.run([sys.executable, TP, "take", "godot", TURN, "--wait", "3600"] + (["--stale-ok"] if stale else [])).returncode != 0:
    print("TURN REFUSED"); sys.exit(1)
try:
    for s in sets:
        extra, n = SETS[s]
        for v in variants:
            name = f"{rnd}_{s}_{v}"; t0 = time.time()
            va = {"g": ["--grade-dump", os.path.join(shots, f"{rnd}_{s}_g.bin")], "r": ["--grade", "off"], "t": ["--grade-try", specs.get(s, spec) or ""]}[v]
            args = HER + extra + va + ["--spots-from", "10", "--spots-every", "6", "--shot", name, "--seconds", "15", "--every", "6", "--count", str(n)]
            with open(os.path.join(logs, name + ".log"), "w", encoding="utf-8", errors="replace") as lf:
                p = subprocess.Popen([GODOT, "--path", G, "--resolution", "1920x1080", "--"] + args, stdout=lf, stderr=subprocess.STDOUT)
                try: p.wait(timeout=600)
                except subprocess.TimeoutExpired:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True); print(name, "TIMEOUT")
            print(f"[{name}] {time.time()-t0:.0f} s, exit {p.returncode}")
finally:
    subprocess.run([sys.executable, TP, "give", "godot", TURN])
print("DONE")
