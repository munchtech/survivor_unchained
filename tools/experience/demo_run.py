"""The demo run tool (Experience 11-12): play batches of the game as a player would, frames and saves kept.

    python tools/experience/demo_run.py BATCH.json [only_name,...] [--out DIR] [--root WORKTREE]

BATCH.json: [{"name": "loop1", "args": ["--quick", "warden", "--zone", "waystation", "--auto", "--nights", "1"],
              "timeout": 2900, "fresh": true, "snap": true, "load_snap": "loop1:loop_back_1"}, ...]
Each run: Godot at 1920x1080 with --shot NAME added; frames go to godot/.shots/NAME*.png, the log to OUT/logs/NAME.log.
- "fresh": true moves user://saves aside first (to OUT/saves_backup): a first-time player.
- "snap": true copies the saves folder after the run to OUT/snap_NAME.
- Step snapshots, always on: each "auto: saved TAG" line the autopilot prints (Autopilot.Keep: the town, back
  at the table after night N) copies the saves folder to OUT/snap_NAME_TAG while the run goes on, so a later
  run can start from any step of the loop.
- "load_snap": "SNAP" (a folder name after snap_) or "RUN:TAG" reloads the longest-played slot in it with --load.
- "godot": ["--fixed-fps", "60"]: engine arguments before the game's own (tools/style/frames.py: even game time, the same frames each round).
One godot turn (tools/turn.py) for the whole batch; the game is built first. Stops only the Godot it started, by PID.
OUT defaults to survivorsunchained_inputs/demo_runs (outside the repo: saves and logs are large and personal)."""
import json, os, shutil, subprocess, sys, time

args = sys.argv[1:]
# --stale-ok: the turn taken for a shot that needs no current art (a flow proof), as turn.py has it.
STALE_OK = "--stale-ok" in args
if STALE_OK: args.remove("--stale-ok")
def opt(name, default):
    if name in args:
        i = args.index(name); v = args[i + 1]; del args[i:i + 2]; return v
    return default
ROOT = os.path.abspath(opt("--root", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
OUT = os.path.abspath(opt("--out", r"C:\Users\munch\Desktop\survivorsunchained_inputs\demo_runs"))
G = os.path.join(ROOT, "godot")
GODOT = os.environ.get("GODOT_CONSOLE", r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe")
LOGS = os.path.join(OUT, "logs"); os.makedirs(LOGS, exist_ok=True)
TP = os.path.join(ROOT, "tools", "turn.py")
USER = os.path.join(os.environ["APPDATA"], "Godot", "app_userdata", "Survivor Unchained", "saves")
runs = json.load(open(args[0], encoding="utf-8"))
if len(args) > 1: runs = [r for r in runs if r["name"] in args[1].split(",")]

def snap(dst):
    if os.path.isdir(USER):
        shutil.rmtree(dst, ignore_errors=True); shutil.copytree(USER, dst)

def longest(folder):
    best = None
    for f in os.listdir(folder):
        if f.startswith("slot"):
            pt = json.load(open(os.path.join(folder, f), encoding="utf-8")).get("playtime", 0)
            if best is None or pt > best[0]: best = (pt, os.path.join(folder, f))
    return best

b = subprocess.run(["dotnet", "build", os.path.join(G, "SurvivorUnchained.csproj"), "-v", "q", "-nologo"], capture_output=True, text=True)
if b.returncode != 0: print(b.stdout[-3000:]); sys.exit(1)
TURN = "demo_run: " + os.path.basename(args[0])
if subprocess.run([sys.executable, TP, "take", "godot", TURN, "--wait", "3600", "--root", ROOT] + (["--stale-ok"] if STALE_OK else [])).returncode != 0:
    print("TURN REFUSED"); sys.exit(1)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import freshness
freshness.reimport_if_stale(ROOT)
try:
    for r in runs:
        name = r["name"]; t0 = time.time(); extra = list(r["args"])
        if r.get("fresh") and os.path.isdir(USER):
            bk = os.path.join(OUT, "saves_backup"); os.makedirs(bk, exist_ok=True)
            for f in os.listdir(USER): shutil.move(os.path.join(USER, f), os.path.join(bk, f"{int(t0)}_{f}"))
        if r.get("load_snap"):
            best = longest(os.path.join(OUT, "snap_" + r["load_snap"].replace(":", "_")))
            print(f"[{name}] loading {best[1]} (playtime {best[0]})", flush=True)
            extra = ["--load", best[1]] + extra
        logp = os.path.join(LOGS, name + ".log")
        with open(logp, "w", encoding="utf-8", errors="replace") as lf:
            p = subprocess.Popen([GODOT, "--path", G, "--resolution", "1920x1080"] + list(r.get("godot", [])) + ["--", "--shot", name] + extra, stdout=lf, stderr=subprocess.STDOUT)
            seen, deadline = 0, t0 + r.get("timeout", 600)
            while p.poll() is None:
                time.sleep(2)
                with open(logp, encoding="utf-8", errors="replace") as rf: lines = rf.read().splitlines()
                for ln in lines[seen:]:
                    if ln.startswith("auto: saved "):
                        tag = ln.split()[2]; snap(os.path.join(OUT, f"snap_{name}_{tag}")); print(f"[{name}] step saved: {tag}", flush=True)
                seen = len(lines)
                if time.time() > deadline:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True); print(name, "TIMEOUT (stopped by its PID)"); break
        if r.get("snap"): snap(os.path.join(OUT, "snap_" + name))
        sd = os.path.join(G, ".shots")
        shots = [f for f in os.listdir(sd) if f.startswith(name)] if os.path.isdir(sd) else []
        log = open(logp, encoding="utf-8", errors="replace").read()
        print(f"[{name}] {time.time()-t0:.0f} s, exit {p.returncode}, {len(shots)} frames, {log.count('Exception')} 'Exception' lines", flush=True)
finally:
    subprocess.run([sys.executable, TP, "give", "godot", TURN])
print("DONE")
