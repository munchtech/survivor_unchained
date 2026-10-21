"""python frames.py ROUND VARIANTS SETS ["try=k=v,..."] ["x=--flag v ..."] [stale]: the style frames, in one godot turn.

VARIANTS, comma-separated: g (as built, with --grade-dump: the live table, for relighting her in the
paint-overs), r (--grade off: the raw frame the paint-overs start from), t (--grade-try SPEC: direction A), b (t plus the extra flags: x="--brush r=3" for
every set, or x.SET="..." for one; e.g. the painterly post-filter on top of A).
o (as built: our own flora, the default since E4h, plus x= flags); g is the kit's flora (--flora-kit).
SETS, comma-separated: town (the square, the east road, the north street by day), ford (Low Ford by
night: camp, road A, road B, the ford, the wood road, two ford lamps), close (the close view at camp,
closest zoom, twice facing away from the fire and twice facing it), camp (the camp at the play camera), towndawn, forddawn,
road (the wood road by night, and the ford road), roaddawn, stones (E5: the ford's stepping stones,
the post's pebbles, a boulder field, by day).
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
    # (E4c: the fourth spot by the square's trees, -6,-12, so the town shows them)
    "town": (["--zone", "waystation", "--time", "day", "--auto", "idle", "--spots", "3,3;24,0;0,-24;-7,-7"], 4),
    "ford": (NIGHT + ["--spots", "-7.5,87.5;3,64;9,40;0,-38;-2,-72;0,-37;-7,-46"], 7),
    "close": (NIGHT + ["--spots", "-8.6,88.6,1,0;-8.6,88.6,1,0;-9.5,92.5,1,0;-9.5,92.5,1,0"], 4),
    # (lead 4: the night restaged with the living held off: no fight, no spell FX; the camp, the ford, the ford's lamp)
    "fordc": (NIGHT + ["--spots-clear", "--spots", "-7.5,87.5;0,-38;0,-37"], 3),
    # (judge r2: the camp at the play camera, centred near the fire, the living held off)
    "camp": (NIGHT + ["--spots-clear", "--spots", "-9.0,90.0;-8.0,91.5"], 2),
    # (env lead 9, G1: the dawns, one frame each: the square at dawn, the camp after the prologue)
    "towndawn": (["--zone", "waystation", "--time", "dawn", "--auto", "idle", "--spots", "3,3"], 1),
    "forddawn": (["--zone", "lowford", "--facts", "prologue.woke=true,prologue.done=true", "--auto", "idle", "--spots-clear", "--spots", "-9.0,90.0"], 1),
    # (env lead 9, E4: the wood road by night and by dawn, the living held off: the trees both sides)
    "road": (NIGHT + ["--spots-clear", "--spots", "-2,-72;3,64"], 2),
    # (E4h: the town's elders in the open by day (-36,-34: 14 m from any tree), at the play camera: their cream flower heads)
    "elder": (["--zone", "waystation", "--time", "day", "--auto", "idle", "--spots", "-37.5,-30.5"], 1),
    # (env lead 10, E5: our stones by day at the play camera: the ford's stepping stones, the post's pebbles and boulders, a boulder field)
    # (E5b: 18,-80 showed only canopy: a boulder, field rocks and pebbles by the road (1,3), and the one open place boulders,
    # field rocks and cliff chunks meet (-58,-53, the west bank))
    # (E5c, judge r2: her on the ford's near (north) bank, not on the water (2.5,-30.5); a pebble patch on open ground (21,23);
    # the west bank's cliff chunk (-73.8,-46.1) 8 m up the frame, her on land below it (-71,-38), not the old spot in the water)
    "stones": (["--zone", "lowford", "--facts", "prologue.woke=true,prologue.done=true", "--auto", "idle", "--spots-clear", "--spots", "2.5,-30.5;21,23;1,3;-71,-38"], 4),
    # (E5b: the same rocks by night)
    "stonesnight": (NIGHT + ["--spots-clear", "--spots", "1,3;-71,-38"], 2),
    # (E5c: only the rock frames of ford and road: the ford's lantern post (ford 03, 05) and the road's faceted boulder (road 01))
    "fordpost": (NIGHT + ["--spots", "0,-38;0,-37"], 2),
    # (E7a: our props by day: the broken wagon on the road, and the camp at the close view, closest zoom, as "close" does by night)
    "wagonday": (["--zone", "lowford", "--facts", "prologue.woke=true,prologue.done=true", "--auto", "idle", "--spots-clear", "--spots", "2.5,62.5"], 1),
    "closedawn": (["--zone", "lowford", "--facts", "prologue.woke=true,prologue.done=true", "--auto", "idle", "--spots", "-8.6,88.6,1,0;-8.6,88.6,1,0;-9.5,92.5,1,0;-9.5,92.5,1,0"], 4),
    "roadrock": (NIGHT + ["--spots-clear", "--spots", "3,64"], 1),
    "roaddawn": (["--zone", "lowford", "--facts", "prologue.woke=true,prologue.done=true", "--auto", "idle", "--spots-clear", "--spots", "-2,-72"], 1),
}
rnd, variants, sets = sys.argv[1], sys.argv[2].split(","), sys.argv[3].split(",")
spec = next((a[4:] for a in sys.argv[4:] if a.startswith("try=")), None)
# try.SET=SPEC: that set's own spec (the day and the night want their own shadow colour)
specs = {a[4:].split("=", 1)[0]: a[4:].split("=", 1)[1] for a in sys.argv[4:] if a.startswith("try.")}
# x=FLAGS / x.SET=FLAGS: extra command-line flags for variant b (x.SET wins for its set)
import shlex
xall = next((a[2:] for a in sys.argv[4:] if a.startswith("x=")), None)
xs = {a[2:].split("=", 1)[0]: a[2:].split("=", 1)[1] for a in sys.argv[4:] if a.startswith("x.")}
# fps=N: Godot's --fixed-fps N (the same frames each run, for pixel comparisons)
fps = next((a[4:] for a in sys.argv[4:] if a.startswith("fps=")), None)
stale = "stale" in sys.argv[4:]
if "b" in variants and not (xall is not None or all(s in xs for s in sets)): sys.exit("variant b needs x=FLAGS or x.SET=FLAGS per set")
if ("t" in variants or "b" in variants) and not (spec or all(s in specs for s in sets)): sys.exit("variants t and b need try=SPEC or try.SET=SPEC per set")
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
            va = {"g": ["--flora-kit", "--grade-dump", os.path.join(shots, f"{rnd}_{s}_g.bin")], "r": ["--grade", "off"], "t": ["--grade-try", specs.get(s, spec) or ""],
                  "b": ["--grade-try", specs.get(s, spec) or ""] + shlex.split(xs.get(s, xall) or ""),
                  # o (E4): as built (our own flora, the default since E4h), plus x= flags if any
                  "o": shlex.split(xs.get(s, xall) or "")}[v]
            args = HER + extra + va + ["--spots-from", "10", "--spots-every", "6", "--shot", name, "--seconds", "15", "--every", "6", "--count", str(n)]
            with open(os.path.join(logs, name + ".log"), "w", encoding="utf-8", errors="replace") as lf:
                p = subprocess.Popen([GODOT, "--path", G, "--resolution", "1920x1080"] + (["--fixed-fps", fps] if fps else []) + ["--"] + args, stdout=lf, stderr=subprocess.STDOUT)
                try: p.wait(timeout=600)
                except subprocess.TimeoutExpired:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True); print(name, "TIMEOUT")
            print(f"[{name}] {time.time()-t0:.0f} s, exit {p.returncode}")
finally:
    subprocess.run([sys.executable, TP, "give", "godot", TURN])
print("DONE")
