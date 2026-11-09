"""Shoot a pressed-skill (or dash) clip at 1:1 (1920x1080, 60 fps, with the game's audio tape) in a fight, under `--auto idle`
(the bot stands; the game's --press script presses the keys: Game.cs wraps Pressed/Held/Pointer/Move through ScriptedPress.cs).

  python tools/fx/skill_clip.py NAME --press "1:3.0:6,0" [--time night|day] [--zone Z] [--pre 0.6] [--len 4.0] [--quick warden]
        [--grant heroic_leap,shield_charge] [--grant-union bladestorm] [--anchor P7EV] [--dash-step long_stride,hard_landing] [--horde "50"] [--pack DEG:WIDTH:DIST:SPREAD]
        [--close] [--perf] [--godot-args "..."]

--press SPEC[;SPEC...]: SPEC = slot:t:dx,dz[:hold=S]; slot 1-6 or dash; t = Journey.Playtime seconds (as --cast); dx,dz = metres
  from her at the press (the aim); hold=S holds the key S seconds (a channel). A dash goes toward dx,dz.
Night: zone arena. Day: zone verge + --time day (the arena has no day). Default crowd: --horde 50 --dist 3 --spread 9 --no-spawn,
  dropped when you pass --horde or --pack (or --horde in --godot-args). --pack DEG:WIDTH:DIST:SPREAD = --horde-arc (world degrees
  from +X toward +Z), e.g. --pack 0:50:5:5 puts the crowd 5-10 m east in a 50 degree fan.
--perf: adds --perf; the game's `perf ...` report lines go to perf.txt. --close: there is no way from args to hold the close view in a
  fight (GameCloseUp.cs:26 is out of combat only), so this prints a note and shoots the play camera.

Output: C:/Users/munch/Desktop/survivorsunchained_inputs/skills_p7/NAME/
  clip.mp4 (H.264+AAC, `pre` s before the first press, `len` s), tape.wav (same window), labelled frames f+0.03.png,
  sheet.jpg + sheet_half.jpg (16 frames, 4 a row), events.jpg + events_half.jpg (the view's `p7ev NAME frame N` lines: frames N and
  N+2 of each name's first occurrence, ev_NAME_f0/f2.png; skipped if none), log.txt, perf.txt (with --perf).
Anchor: the game's first `skill press frame N` line. Sound: the offline tape (--wav --stems, Dummy driver) cut to the clip window.
Takes the godot turn (tools/turn.py) and gives it back in a finally.
"""
import argparse, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
GODOT = os.environ.get("GODOT", "C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe")
FFMPEG = "C:/Users/munch/AppData/Roaming/Python/Python314/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
TURN = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
OUT = Path("C:/Users/munch/Desktop/survivorsunchained_inputs/skills_p7")
OFFSETS = [-0.10, 0.00, 0.03, 0.08, 0.17, 0.25, 0.33, 0.45, 0.58, 0.62, 0.67, 0.75, 0.90, 1.20, 1.60, 2.20]
FPS = 60

ap = argparse.ArgumentParser()
ap.add_argument("name"); ap.add_argument("--press", required=True)
ap.add_argument("--time", default="night"); ap.add_argument("--pre", type=float, default=0.6)
ap.add_argument("--len", type=float, default=4.0)
ap.add_argument("--quick", default="warden")
ap.add_argument("--zone", default=None, help="default arena by night, verge by day")
ap.add_argument("--grant", default=None); ap.add_argument("--dash-step", default=None)
ap.add_argument("--grant-union", default=None)
ap.add_argument("--offsets", default=None, help="the sheet's 16 times (s from the press), comma separated")
ap.add_argument("--anchor", default=None, help="a p7ev NAME: the sheet is timed from its first frame, not the press (a kindled skill)")
ap.add_argument("--horde", default=None); ap.add_argument("--pack", default=None, help="DEG:WIDTH:DIST:SPREAD, passed as --horde-arc")
ap.add_argument("--close", action="store_true"); ap.add_argument("--perf", action="store_true")
ap.add_argument("--godot-args", default="")
a = ap.parse_args()
if a.offsets: OFFSETS = [float(x) for x in a.offsets.split(",")]

out = OUT / a.name
shutil.rmtree(out, ignore_errors=True); out.mkdir(parents=True)
tmp = Path(tempfile.mkdtemp(prefix="skillclip_", dir=str(OUT)))
avi = tmp / "movie.avi"
ZONE = a.zone or ("verge" if a.time == "day" else "arena")
extra = a.godot_args.split()
last_t = max(float(s.split(":")[1]) for s in a.press.split(";") if s.strip())
if a.close: print("note: no close-up camera in a fight (GameCloseUp.cs:26 is out of combat only); shooting the play camera")
horde = []
if a.horde is not None: horde = ["--horde", a.horde]
elif "--horde" not in extra: horde = ["--horde", "50"]
if horde and "--dist" not in extra: horde += ["--dist", "3"]
if horde and "--spread" not in extra: horde += ["--spread", "9"]
if horde and "--no-spawn" not in extra: horde += ["--no-spawn"]
if a.pack: horde += ["--horde-arc", a.pack]
label = f"skills-p7: clip {a.name}"
frames = int((last_t + a.pre + a.len + 4) * FPS)
gargs = [GODOT, "--path", str(ROOT / "godot"), "--resolution", "1920x1080", "--write-movie", str(avi),
         "--fixed-fps", str(FPS), "--audio-driver", "Dummy", "--quit-after", str(frames), "--",
         "--quick", a.quick, "--zone", ZONE, "--offer", "0", "--auto", "idle", "--press", a.press,
         "--time", a.time, "--clip", "--shot", "clip", "--seconds", str(last_t + a.len + 2),
         "--wav", str(tmp / "tape.wav"), "--stems", "--soundlog"] + horde
if a.grant: gargs += ["--grant", a.grant]
if a.grant_union: gargs += ["--grant-union", a.grant_union]
if a.dash_step: gargs += ["--dash-step", a.dash_step]
if a.perf: gargs += ["--perf"]
gargs += extra
ov = ROOT / "godot" / "override.cfg"
if ov.exists(): ov.unlink()
subprocess.run([sys.executable, TURN, "take", "godot", label, "--wait", "900"], check=True)
try:
    log = subprocess.run(gargs, capture_output=True, text=True, errors="replace")
    (out / "log.txt").write_text(log.stdout + "\n" + log.stderr, encoding="utf-8")
finally:
    subprocess.run([sys.executable, TURN, "give", "godot", label])
try:
    m = re.search(r"skill press frame (\d+)", log.stdout)
    if not m: sys.exit("no 'skill press frame' in the log; see " + str(out / "log.txt"))
    pf = int(m.group(1))
    print(re.search(r"skill press frame.*", log.stdout).group(0))
    for gl in re.findall(r"^(?:grant|grant-union|dash-step): .*$", log.stdout, re.M): print(gl)
    if (a.grant or a.grant_union or a.dash_step) and not re.search(r"^(?:grant|grant-union|dash-step): ", log.stdout, re.M):
        print("WARNING: no grant line in the log: the skill was never granted (rerun)")
    if a.anchor:
        am = re.search(r"p7ev " + re.escape(a.anchor) + r" frame (\d+)", log.stdout)
        if not am: sys.exit(f"no p7ev {a.anchor} in the log; see " + str(out / "log.txt"))
        pf = int(am.group(1)); print(f"anchored on {a.anchor} frame {pf}")
    ss = max(0.0, pf / FPS - a.pre)
    import soundfile as sf
    tape, sr = sf.read(str(tmp / "tape.wav"), dtype="float32", always_2d=True)
    a0 = int(ss * sr); a1 = a0 + int(a.len * sr)
    sf.write(str(out / "tape.wav"), tape[a0:a1], sr)
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-ss", f"{ss:.3f}", "-i", str(avi), "-i", str(out / "tape.wav"),
                    "-t", str(a.len), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(out / "clip.mp4")], check=True)

    def grab(n, path):
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(avi), "-vf", f"select=eq(n\\,{max(0, n)})",
                        "-frames:v", "1", "-vsync", "0", str(path)], check=True)

    W, H = 960, 540
    try: font = ImageFont.truetype("arial.ttf", 28)
    except Exception: font = ImageFont.load_default()

    def sheet(items, name):
        rows = (len(items) + 3) // 4
        sh = Image.new("RGB", (W * 4, H * rows), "black"); d = ImageDraw.Draw(sh)
        for i, (lab, p) in enumerate(items):
            if not p.exists(): continue
            im = Image.open(p).convert("RGB").resize((W, H)); x, y = (i % 4) * W, (i // 4) * H
            sh.paste(im, (x, y)); d.text((x + 10, y + 8), lab, fill="yellow", font=font)
        sh.save(out / name, quality=88)
        subprocess.run([sys.executable, str(ROOT / "tools" / "half.py"), str(out / name)], check=True)

    shots = []
    for o in OFFSETS:
        p = out / f"f{o:+.2f}.png"; grab(pf + round(o * FPS), p); shots.append((f"{o:+.2f}s", p))
    sheet(shots, "sheet.jpg")
    seen = {}
    for nm, n in re.findall(r"p7ev (\S+) frame (\d+)", log.stdout):
        seen.setdefault(nm, int(n))
    ev = []
    for nm, n in seen.items():
        for k in (0, 2):
            p = out / f"ev_{nm}_f{k}.png"; grab(n + k, p); ev.append((f"{nm} f{k} (frame {n + k}, {(n + k - pf) / FPS:+.2f}s)", p))
    if ev: sheet(ev, "events.jpg")
    else: print("no p7ev lines in the log: events sheet skipped")
    if a.perf:
        pl = [l for l in log.stdout.splitlines() if l.startswith("perf ")]
        (out / "perf.txt").write_text("\n".join(pl), encoding="utf-8")
        print("\n".join(l for l in pl if re.search(r"gpu|cpu", l, re.I)))
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print("done", out)
