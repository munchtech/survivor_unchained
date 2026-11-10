"""(L1 lead 21 QUIT) The quit's proof: N starts of the game, each to play and out through the game's own quit path.

    python tools/experience/quit_starts.py [--n 10] [--out DIR] [--frames 30] [--args "--veteran 30:2"] [--no-guard]

Each start: `-- --quick --quit-at-play FRAMES` (QuitPath: FRAMES drawn frames into play, Game.QuitGame: the save, the
fade, the early release, one frame, the guard armed, the tree quits). Timed from the log line `quit: requested` (seen at
a 20 ms poll) to the process's end. A HANG is a process still there 15 s after the request: its stacks are dumped
(hang_stacks.py) and it is killed by its PID. Counted from the log: `quit guard: fired` (the guard's kill), `ink: released`.
The caller holds the Godot turn (tools/turn.py) and brings the load; rows are appended to DIR/quit_starts.jsonl, and the
table is of every row in that file (so two batches of 10 with the turn given back between them make one table of 20).
--no-guard: the game's guard off (`--quit-guard off`), to see whether the early release alone ends the hangs.
"""
import json, os, statistics, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
GODOT = os.environ.get("GODOT_CONSOLE", r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe")
sys.path.insert(0, HERE)
import hang_stacks


def opt(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


N, FRAMES = int(opt("--n", "10")), opt("--frames", "30")
OUT = os.path.abspath(opt("--out", os.path.join(ROOT, "godot", ".shots", "quit_starts")))
EXTRA = opt("--args", "").split() + (["--quit-guard", "off"] if "--no-guard" in sys.argv else [])
os.makedirs(OUT, exist_ok=True)
ROWS = os.path.join(OUT, "quit_starts.jsonl")
START_TIMEOUT, HANG_AFTER = 240, 15


def lines_of(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()


def one(i):
    name = f"quit_{int(time.time())}_{i:02d}"
    logp = os.path.join(OUT, name + ".log")
    row = {"name": name, "exit_s": None, "hang": False, "guard": False, "reached": False, "code": None, "stacks": None}
    t0 = time.time()
    with open(logp, "w", encoding="utf-8", errors="replace") as lf:
        p = subprocess.Popen([GODOT, "--path", os.path.join(ROOT, "godot"), "--resolution", "1920x1080", "--", "--quick", "--quit-at-play", FRAMES] + EXTRA,
                             stdout=lf, stderr=subprocess.STDOUT)
        tq = None
        while p.poll() is None:
            time.sleep(0.02)
            now = time.time()
            if tq is None:
                if any(l.startswith("quit: requested") for l in lines_of(logp)): tq = now
                elif now > t0 + START_TIMEOUT: break
            elif now > tq + HANG_AFTER:
                row["hang"] = True; break
        tend = time.time()
        if p.poll() is None:
            row["stacks"] = hang_stacks.dump(p.pid, OUT, name)
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
            p.wait(30)
    log = lines_of(logp)
    row["reached"] = tq is not None
    row["exit_s"] = round(tend - tq, 2) if tq is not None and not row["hang"] else None
    row["guard"] = any(l.startswith("quit guard: fired") for l in log)
    row["ink_line"] = any(l.startswith("ink: released") for l in log)
    row["start_s"] = round((tq or tend) - t0, 1)
    row["code"] = p.returncode
    with open(ROWS, "a", encoding="utf-8") as f: f.write(json.dumps(row) + "\n")
    print(f"{name}  start {row['start_s']:6.1f} s  exit {row['exit_s'] if row['exit_s'] is not None else '   -'} s  "
          f"{'HANG ' + str(row['stacks']) if row['hang'] else ('NEVER REACHED PLAY' if not row['reached'] else 'ended')}"
          f"{'  GUARD FIRED' if row['guard'] else ''}  code {row['code']}{'' if row['ink_line'] else '  (no ink: released line)'}", flush=True)


for i in range(N):
    one(i)

rows = [json.loads(l) for l in open(ROWS, encoding="utf-8") if l.strip()]
ex = sorted(r["exit_s"] for r in rows if r["exit_s"] is not None)
print(f"\nTABLE ({ROWS}): {len(rows)} starts, {sum(r['reached'] for r in rows)} reached play")
if ex: print(f"exit seconds (request to process end): min {ex[0]:.2f} / p50 {statistics.median(ex):.2f} / max {ex[-1]:.2f}; over 3 s: {sum(e > 3 for e in ex)}")
print(f"hangs: {sum(r['hang'] for r in rows)}; guard fires: {sum(r['guard'] for r in rows)} of {len(rows)}; nonzero exit codes: {sum(1 for r in rows if r['code'])}")
