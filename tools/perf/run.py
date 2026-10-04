"""Measured runs of the Godot game (src/Perf.cs), scenario by scenario.

    python tools/perf/run.py SCENARIO [SCENARIO ...] [--tag T] [--res 2560x1440] [--quality high] [--repeat N] [-- extra game args]
    python tools/perf/run.py --list

Each scenario starts the game windowed at the resolution given (the owner's
screen is 2560x1440), runs it with vsync off for its warm-up and its
recording, and leaves godot/.shots/perf/<scenario>_<tag>.json and .csv;
the summaries of all runs are printed as a table at the end. Build the C#
first (`dotnet build godot/SurvivorUnchained.csproj`). docs/PERF_AUDIT.md
has what was measured and how to read it.

The game's user folder for these runs is set by godot/override.cfg (not
committed), so they neither read nor write the owner's saves and settings:

    [application]
    config/use_custom_user_dir=true
    config/custom_user_dir_name="SurvivorUnchainedPerf"
"""
import json
import os
import subprocess
import sys
import time

GODOT = os.environ.get("GODOT", r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GAME = os.path.join(ROOT, "godot")
OUT = os.path.join(GAME, ".shots", "perf")

# A mid-game arsenal (the horde bench's) and a late one, for the arena's later minutes.
MID = "oathblade:6,seeking_motes:5,cinderfall:5,arcweb:4,knifestorm:4,hallowed_ring:4"
LATE = "oathblade:8,seeking_motes:8,cinderfall:8,arcweb:7,knifestorm:7,hallowed_ring:7,+might:3,+haste:2"

HER = ["--quick", "warden", "--sex", "female"]

# name: (game args, warm seconds, recorded seconds)
SCENARIOS = {
    # The town by day, the heroine walking the autopilot's circle.
    "hub": (HER + ["--zone", "waystation", "--time", "day", "--auto"], 10, 30),
    "hub_night": (HER + ["--zone", "waystation", "--time", "night", "--auto"], 10, 30),
    # The Verge by day: packs, the wood's flora.
    "verge": (HER + ["--zone", "verge", "--time", "day", "--auto"], 10, 30),
    # An arena from its start, as it opens (the autopilot drafting first cards).
    "arena_open": (HER + ["--zone", "arena", "--tier", "2", "--auto"], 6, 60),
    # Twenty minutes in with a mid-game build: the horde near its cap.
    "arena_mid": (HER + ["--zone", "arena", "--tier", "2", "--minute", "20", "--give", MID, "--auto"], 20, 40),
    # The boss: the clock set just short of the half hour.
    "boss": (HER + ["--zone", "arena", "--tier", "2", "--minute", "29.9", "--give", LATE, "--auto"], 12, 40),
    # Endless at its densest: the clock past forty minutes (the horde at its cap, tier 3), a late build.
    "endless": (HER + ["--zone", "arena", "--tier", "3", "--minute", "45", "--give", LATE, "--auto"], 25, 40),
    # The same, the dead people (the risen; the most bodies on the ground).
    "endless_dead": (HER + ["--zone", "arena", "--tier", "3", "--people", "dead", "--minute", "45", "--give", LATE, "--auto"], 25, 40),
    # A crowd of 600 put round her (--horde), for the horde alone.
    "horde600": (HER + ["--zone", "arena", "--tier", "2", "--horde", "300:risen,150:wolf,150:footpad", "--auto", "idle"], 15, 30),
    # The title by its fire.
    "title": ([], 8, 20),
}


def others():
    """Other Godot games running on this machine (other sessions' runs; imports and editors are not counted)."""
    try:
        q = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Get-CimInstance Win32_Process -Filter \"Name like 'Godot%'\" | ForEach-Object { $_.CommandLine }"],
                           capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return []
    return [l for l in q.splitlines() if l.strip() and "--import" not in l and "--editor" not in l and " -e " not in l
            and "_console.exe" not in l.split(" --")[0]]


def gpu_busy():
    try:
        q = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits"],
                           capture_output=True, text=True, timeout=30).stdout.strip().split(",")
        return int(q[0]), int(q[1])
    except Exception:
        return -1, -1


def quiet(wait):
    """Wait (up to `wait` seconds) for the GPU to be ours: the RTX 5080 is shared with
    other sessions and ComfyUI, and their frames would be counted in ours."""
    t0 = time.time()
    while True:
        busy, mem = gpu_busy()
        rivals = others()
        if (busy < 15 and not rivals) or time.time() - t0 > wait:
            return busy, mem, len(rivals)
        time.sleep(10)


BIN = os.path.join(GAME, ".godot", "mono", "temp", "bin", "Debug")


def use_build(folder):
    """Put a kept build of the game's C# in place (A/B runs of two builds, interleaved,
    so a busy GPU weighs on both alike)."""
    import shutil
    for f in os.listdir(folder):
        if f.startswith("SurvivorUnchained."):
            shutil.copy2(os.path.join(folder, f), os.path.join(BIN, f))


def run(name, tag, res, quality, extra, wait=0, build=None):
    args, warm, span = SCENARIOS[name]
    out = f"{name}_{tag}" if tag else name
    if build:
        use_build(build)
    busy, mem, rivals = quiet(wait)
    print(f"  GPU before: {busy}% busy, {mem} MB used, {rivals} other games running")
    cmd = [GODOT, "--path", GAME, "--resolution", res, "--", *args, "--quality", quality,
           "--perf", out, "--perf-warm", str(warm), "--perf-for", str(span), *extra]
    t0 = time.time()
    log = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=warm + span + 600)
    took = time.time() - t0
    lines = [l for l in log.stdout.splitlines() if l.startswith("perf") or "ERROR" in l or "baked" in l]
    for l in lines[:60]:
        print("  " + l)
    path = os.path.join(OUT, out + ".json")
    if not os.path.exists(path):
        print(f"  {out}: no result (exit {log.returncode}, {took:.0f}s)")
        print("\n".join(log.stdout.splitlines()[-30:]))
        print("\n".join(log.stderr.splitlines()[-30:]))
        return None
    with open(path, encoding="utf-8") as f:
        r = json.load(f)
    r["_wall"] = took
    r["_gpu_before"] = busy
    r["_rivals"] = rivals
    r["_gpu_after"] = gpu_busy()[0]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(r, f, indent=1)
    return r


def table(rows):
    cols = [("run", 22), ("fps", 5), ("ms", 6), ("p50", 6), ("1%", 6), ("0.1%", 6), ("max", 6), ("main", 6), ("sim", 5), ("plyr", 5),
            ("crowd", 5), ("fx", 5), ("hud", 5), ("snd", 5), ("rcpu", 5), ("gpu", 5),
            ("draws", 6), ("shdw", 5), ("ui", 4), ("prims", 7), ("KB/f", 6), ("gc", 8), ("pipes", 5), ("foes", 4), ("vram", 5), ("busy", 5)]
    print(" ".join(c.rjust(w) for c, w in cols))
    for name, r in rows:
        vals = [name, f"{r['fps_mean']:.0f}", f"{r['ms_mean']:.2f}", f"{r['ms_p50']:.2f}", f"{r['ms_low1']:.1f}", f"{r['ms_low01']:.1f}",
                f"{r['ms_max']:.1f}", f"{r['cpu_main_ms']:.2f}", f"{r['cpu_sim_ms']:.2f}", f"{r['cpu_player_ms']:.2f}", f"{r['cpu_crowd_ms']:.2f}",
                f"{r['cpu_fx_ms']:.2f}", f"{r['cpu_hud_ms']:.2f}", f"{r['cpu_sound_ms']:.2f}",
                f"{r['cpu_render_ms'] + r['cpu_setup_ms']:.2f}", f"{r['gpu_ms']:.2f}", f"{r['draws']:.0f}", f"{r['draws_shadow']:.0f}",
                f"{r['draws_canvas']:.0f}", f"{r['primitives'] / 1e6:.2f}M", f"{r['alloc_kb_frame']:.1f}", "/".join(str(x) for x in r["gc"]),
                str(r["pipelines_recorded"]), f"{r.get('foes', 0):.0f}", f"{r['video_mem_mb']:.0f}", f"{r.get('_gpu_before', -1)}"]
        print(" ".join(v.rjust(w) for v, (_, w) in zip(vals, cols)))


def main():
    argv = sys.argv[1:]
    extra = []
    if "--" in argv:
        i = argv.index("--")
        argv, extra = argv[:i], argv[i + 1:]
    if not argv or "--list" in argv:
        for k, (a, w, s) in SCENARIOS.items():
            print(f"{k:14} warm {w:3}s rec {s:3}s  {' '.join(a)}")
        return
    def opt(flag, default):
        if flag in argv:
            i = argv.index(flag)
            v = argv[i + 1]
            del argv[i:i + 2]
            return v
        return default
    tag = opt("--tag", "")
    res = opt("--res", "2560x1440")
    quality = opt("--quality", "high")
    repeat = int(opt("--repeat", "1"))
    wait = int(opt("--wait", "600"))
    # --builds A=DIR,B=DIR: each scenario run with each kept build in turn (tags A, B).
    builds = [b.split("=", 1) for b in opt("--builds", "").split(",") if b]
    rows = []
    for rep in range(repeat):
        for name in argv:
            for label, folder in builds or [("", None)]:
                t = f"{tag}{label}{rep}" if repeat > 1 else f"{tag}{label}"
                print(f"{name} ({t or 'untagged'}, {res}, {quality})")
                r = run(name, t, res, quality, extra, wait, folder)
                if r:
                    rows.append((f"{name}_{t}" if t else name, r))
    print()
    table(rows)


if __name__ == "__main__":
    main()
