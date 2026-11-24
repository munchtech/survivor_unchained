"""Film her in the den at the game camera, so the same run can be shot on two bodies and set side by side.

  python tools/body/switch_film.py --p1-dir res://art/people/body_p1/ --tag b_base [--kit] [--only-kit] [--no-close] [--seed 1]

Without --kit: one run in her starting Warden set, one with the den kit (--wear kit_pauldrons,kit_bodice,kit_brief,kit_belt,
kit_vambraces,kit_gloves,kit_boots), then the 12.5 m idle/run runs. --kit alone shoots the kit run only; --no-kit the starting set only.
(Death: she falls at DIE, lies on the floor at about +1.5 s, and is up again at the den start by +4 s.)
Output: godot/.shots/switch/<tag>/ (git-ignored):
  <set>/NN_name.png        stills at 1920x1080, game camera (the den's own, --cam not given), set = start | kit
  <set>_close/NN_name.png  idle + run at --cam 12.5 (the conversation/chest distance; the game's own --cam switch)
  film_<set>.mp4           the whole scripted run at 1920x1080, 30 fps (the kit run's is the film)
  log_<set>.txt            the Godot log; log_summary.txt = its p1:/gear:/wear:/her tuck/PushError/SameRest/WARNING lines
  sheet_<set>.jpg          a contact sheet of the stills
The run (every switch is an existing one, no game code): the den start (Args.DenTest) under --auto idle, --seed fixed, --fixed-fps 30,
--press (ScriptedPress.cs) for the walk, two skills and the dash, --die T (Game.cs) for the death. Stills are cut from the --write-movie
AVI at frames worked out from the log's `skill press frame N ... t T` lines (the game's frame counter against its play clock).
One godot turn per run (tools/turn.py).
"""
import argparse, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GODOT = os.environ.get("GODOT", "C:/Users/munch/Desktop/Godot_v4.7.2-stable_mono_win64/Godot_v4.7.2-stable_mono_win64_console.exe")
FFMPEG = os.environ.get("FFMPEG", "C:/Users/munch/AppData/Roaming/Python/Python314/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe")
TURN = ROOT / "tools" / "turn.py"
KIT = "kit_pauldrons,kit_bodice,sol_corset,kit_brief,kit_belt,kit_vambraces,kit_gloves,kit_boots"  # (gilt_harness + gilt_boots wear lists, items.json: the den kit as the game equips it)
FPS = 30
DEN = ["--quick", "warden", "--sex", "female", "--zone", "map", "--dungeon", "hollow", "--veteran", "9"]   # Args.DenTest
LOG_RE = r"p1:|gear:|wear:|her tuck|PushError|SameRest|WARNING|ERROR|SCRIPT ERROR"

# The script, in Journey.Playtime seconds (ScriptedPress: slot:t:dx,dz[:hold=S]; walk:t:dx,dz:hold=S; dash:t:dx,dz).
# Idle to 5.0 (the den's title card shows to about 4), walk 5-8, skill 1 (Sunder) 9.0, skill 2 (Heroic Leap) 11.5, walk + dash 13.5-14.5,
# skill 3 (Bladestorm) 16.5, death at DIE.
PRESS = os.environ.get("SWITCH_PRESS", "walk:5:8,0:hold=3;1:9:6,0;2:11.5:6,0;walk:13.5:8,0:hold=2;dash:14.5:8,0;3:16.5:6,0")
DIE = float(os.environ.get("SWITCH_DIE", "19"))
LEN = float(os.environ.get("SWITCH_LEN", "24"))
T_IDLE, T_RUN = 4.0, 6.5
CLOSE_PRESS = "walk:5:8,0:hold=3"
CLOSE_LEN = 8.0


def run_godot(out, name, wear, extra, press, secs, seed):
    out.mkdir(parents=True, exist_ok=True)
    avi = out / f"{name}.avi"
    frames = int((secs + 6) * FPS)
    g = [GODOT, "--path", str(ROOT / "godot"), "--resolution", "1920x1080", "--write-movie", str(avi), "--fixed-fps", str(FPS),
         "--audio-driver", "Dummy", "--quit-after", str(frames), "--"] + DEN + ["--seed", str(seed), "--nocine", "--clip",
         "--shot", "switch", "--seconds", str(secs + 3), "--auto", "idle", "--press", press] + extra
    if wear: g += ["--wear", wear]
    label = f"body-switch: switch_film {name}"
    t0 = time.time()
    cmd = [sys.executable, str(TURN), "run", "godot", label, "--wait", "1800", "--tail", "0", "--", *g]
    for attempt in range(3):   # the engine crashes now and then in CelLib.Drain (4.7.2 mono, InstanceFromId): the run is shot again
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        log = r.stdout + "\n" + r.stderr
        if r.returncode == 0: break
        print(f"{name}: exit {r.returncode} (attempt {attempt + 1}), again", flush=True)
    q = re.search(r"logged to (\S+\.log)", log)   # quiet.py keeps the whole Godot log in a file; stdout has only a tail
    if q and Path(q[1]).exists(): log = Path(q[1]).read_text(encoding="utf-8", errors="replace")
    (out / f"log_{name}.txt").write_text(log, encoding="utf-8")
    print(f"{name}: exit {r.returncode}, {time.time() - t0:.0f} s, movie {'yes' if avi.exists() else 'NO'}", flush=True)
    return avi, log


def anchors(log):
    """(frame, play-clock) pairs from the scripted presses."""
    return [(int(m[1]), float(m[3])) for m in re.finditer(r"skill press frame (\d+) slot (\S+) t ([\d.]+)", log)]


def frame_at(anc, t):
    """The movie frame at play time t: from the last press at or before t (hit-stop holds the clock, so the nearest is the truest)."""
    a = [x for x in anc if x[1] <= t] or anc
    n, tt = min(a, key=lambda x: abs(x[1] - t)) if a else (0, 0)
    return max(0, n + round((t - tt) * FPS))


def grab(avi, n, path):
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(avi), "-vf", f"select=eq(n\\,{n})", "-frames:v", "1", "-vsync", "0", str(path)], check=True)


def sheet(folder, out):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return
    files = sorted(folder.glob("*.png"))
    if not files: return
    W, H, cols = 640, 360, 4
    rows = (len(files) + cols - 1) // cols
    sh = Image.new("RGB", (W * cols, H * rows), "black"); d = ImageDraw.Draw(sh)
    for i, f in enumerate(files):
        x, y = (i % cols) * W, (i // cols) * H
        sh.paste(Image.open(f).convert("RGB").resize((W, H)), (x, y)); d.text((x + 6, y + 4), f.stem, fill="white")
    sh.save(out, quality=90)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p1-dir", default=None, help="her body folder; omitted: the game default (data/body/her_body.json dir)"); ap.add_argument("--tag", required=True)
    ap.add_argument("--kit", action="store_true", help="the den kit only (default: both sets)")
    ap.add_argument("--no-kit", action="store_true", help="the starting set only")
    ap.add_argument("--no-close", action="store_true"); ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--keep-avi", action="store_true")
    a = ap.parse_args()
    base = ROOT / "godot" / ".shots" / "switch" / a.tag
    base.mkdir(parents=True, exist_ok=True)
    ov = ROOT / "godot" / "override.cfg"
    if ov.exists(): ov.unlink()
    sets = [("kit", KIT)] if a.kit else [("start", None)] if a.no_kit else [("start", None), ("kit", KIT)]
    summary = []
    t0 = time.time()
    for name, wear in sets:
        press = PRESS
        avi, log = run_godot(base, name, wear, (["--p1-dir", a.p1_dir] if a.p1_dir else []) + ["--die", str(DIE)], press, LEN, a.seed)
        anc = anchors(log)
        summary.append(f"[{name}] press anchors (frame, t): {anc}")
        if not avi.exists() or not anc:
            summary.append(f"[{name}] NO MOVIE or NO PRESS LINES: stills skipped"); continue
        d = base / name; shutil.rmtree(d, ignore_errors=True); d.mkdir()
        # the stills: (name, play-clock seconds or ("hit", press index)). Contact frames follow the press by the clip's contact (her_events.json).
        pr = sorted(anc, key=lambda x: x[1])
        shots = [("idle", frame_at(anc, T_IDLE)), ("run", frame_at(anc, T_RUN))]
        def hit(n, ev, fallback):   # the game's own event frame (p7ev lines of --clip) after the press
            m = [int(x) for x in re.findall(rf"p7ev {ev} frame (\d+)", log) if int(x) >= n]
            return m[0] if m else n + fallback
        for i, (n, t) in enumerate(pr):
            if abs(t - 9.0) < 0.5: shots.append(("skill1_sunder_press", n)); shots.append(("skill1_sunder_hit", hit(n, "sunder_ring", 6)))
            elif abs(t - 11.5) < 0.5: shots.append(("skill2_leap_press", n)); shots.append(("skill2_leap_hit", hit(n, "leap_land", 18)))
            elif abs(t - 14.5) < 0.5: shots.append(("dash_mid", n + 4))
        for dt in (0.5, 1.0, 1.5, 2.0): shots.append((f"death_p{dt}s", frame_at(anc, DIE + dt)))
        for k, (nm, n) in enumerate(shots, 1):
            grab(avi, n, d / f"{k:02d}_{nm}_f{n}.png")
        sheet(d, base / f"sheet_{name}.jpg")
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(avi), "-ss", "4", "-t", f"{DIE + 3.0 - 4:.1f}", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-an", str(base / f"film_{name}.mp4")], check=True)
        if not a.keep_avi: avi.unlink()
        summary.append(f"[{name}] stills: {[s[0] + '@' + str(s[1]) for s in shots]}")
    if not a.no_close:
        for name, wear in sets:
            avi, log = run_godot(base, f"{name}_close", wear, (["--p1-dir", a.p1_dir] if a.p1_dir else []) + ["--cam", "12.5"], CLOSE_PRESS, CLOSE_LEN, a.seed)
            anc = anchors(log)
            if not avi.exists(): summary.append(f"[{name}_close] NO MOVIE"); continue
            d = base / f"{name}_close"; shutil.rmtree(d, ignore_errors=True); d.mkdir()
            # a walk prints no press line: movie frame = play clock x fps (the full runs' first press lands within a frame of that)
            for k, (nm, t) in enumerate([("idle", T_IDLE), ("run", T_RUN)], 1):
                grab(avi, round(t * FPS), d / f"{k:02d}_{nm}.png")
            sheet(d, base / f"sheet_{name}_close.jpg")
            if not a.keep_avi: avi.unlink()
    lines = []
    for f in sorted(base.glob("log_*.txt")):
        for l in f.read_text(encoding="utf-8", errors="replace").splitlines():
            if re.search(LOG_RE, l): lines.append(f"{f.stem}: {l}")
    (base / "log_summary.txt").write_text("\n".join(summary + [""] + lines) + "\n", encoding="utf-8")
    print("\n".join(summary)); print(f"{len(lines)} log lines of interest -> {base / 'log_summary.txt'}")
    print(f"done in {time.time() - t0:.0f} s -> {base}")


if __name__ == "__main__":
    main()
