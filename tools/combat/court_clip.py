"""Shoot the Corvane court (vault_opened's first stage) at 1:1 (1920x1080) from arrival to 4 s after the door opens.

  python tools/combat/court_clip.py NAME [--quick warden] [--fps 30] [--godot-args ""] [--answers 0,0] [--bot idle|play] [--minutes 6]

The game prints `court <event> frame N` under --clip (CourtTrace: talk raise sig pull knock low down cue gone open; the Flare's
own `flare press frame N`). The Autopilot answers the door_night choices (--answers; default the first, which is
go_home -> wrong -> lie_down -> raise). Output: C:/Users/munch/Desktop/survivorsunchained_inputs/combat_p6/NAME/
  clip.mp4 (1 s before talk .. 4 s after open), PNG frames by moment, sheet.jpg (half size, 4 a row), sheet_half.jpg,
  log.txt (court lines + errors), events.txt (event, frame, second).
Takes the godot turn (tools/turn.py) and gives it back in a finally. The temporary AVI is deleted after the cuts.
"""
import argparse, os, re, shutil, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
GODOT = os.environ.get("GODOT", "C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe")
FFMPEG = "C:/Users/munch/AppData/Roaming/Python/Python314/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
TURN = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
OUT = Path("C:/Users/munch/Desktop/survivorsunchained_inputs/combat_p6")

ap = argparse.ArgumentParser()
ap.add_argument("name"); ap.add_argument("--quick", default="warden"); ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--bot", default="idle", help="Autopilot mode: idle (stands and fights: the standing player Corvane is tuned for) or play (the plain bot, which dodged about and died in r1)")
ap.add_argument("--stand", action="store_true", help="--stand-at-boss: the idle bot walks up and stands at him (r4)")
ap.add_argument("--no-hold", action="store_true", help="drop --court-hold (her health is held by default so she lives to his fall)")
ap.add_argument("--flare", default="", help="her Flare id (the warden's: the_long_cut), pressed --cast-low s after he passes half life")
ap.add_argument("--cast-low", type=float, default=1.0)
ap.add_argument("--godot-args", default=""); ap.add_argument("--answers", default="0,0"); ap.add_argument("--minutes", type=float, default=6.0)
a = ap.parse_args()
FPS = a.fps
free = shutil.disk_usage("C:/").free / 2**30
if free < 50: sys.exit(f"C: has {free:.0f} GB free (< 50): run the sweep first")

out = OUT / a.name
shutil.rmtree(out, ignore_errors=True); out.mkdir(parents=True)
avi = out / "movie.avi"
label = f"P6: court clip {a.name}"
frames = int(a.minutes * 60 * FPS)
gargs = [GODOT, "--path", str(ROOT / "godot"), "--resolution", "1920x1080", "--write-movie", str(avi),
         "--fixed-fps", str(FPS), "--audio-driver", "Dummy", "--quit-after", str(frames), "--",
         "--quick", a.quick, "--zone", "arena", "--night", "vault", "--auto", a.bot, "--answers", a.answers, "--clip"] + (["--stand-at-boss"] if a.stand else []) + ([] if a.no_hold else ["--court-hold"]) + (["--flare", a.flare, "--cast", "100000", "--cast-low", str(a.cast_low)] if a.flare else []) + ["--court-tail", str(5 * FPS),
         "--shot", "clip", "--seconds", str(a.minutes * 60 + 5)] + a.godot_args.split()
ov = ROOT / "godot" / "override.cfg"
if ov.exists(): ov.unlink()
subprocess.run([sys.executable, TURN, "take", "godot", label, "--wait", "600"], check=True)
try:
    log = subprocess.run(gargs, capture_output=True, text=True, errors="replace")
    text = log.stdout + "\n" + log.stderr
finally:
    subprocess.run([sys.executable, TURN, "give", "godot", label])
try:
    ev = [(m.group(1), int(m.group(2))) for m in re.finditer(r"court (\w+) frame (\d+)", text)]
    fl = [("flare", int(m.group(1))) for m in re.finditer(r"flare press frame (\d+)", text)]
    ev = sorted(ev + fl, key=lambda x: x[1])
    (out / "events.txt").write_text("\n".join(f"{n}\t{f}\t{f / FPS:.2f}s" for n, f in ev) + "\n", encoding="utf-8")
    bad = [l for l in text.splitlines() if re.search(r"court \w+ frame|ERROR|SCRIPT ERROR|NullReference|Exception|flare press", l)]
    (out / "log.txt").write_text("\n".join(bad) + "\n", encoding="utf-8")
    (out / "log_full.txt").write_text(text, encoding="utf-8")
    first = lambda n: next((f for k, f in ev if k == n), None)
    alln = lambda n: [f for k, f in ev if k == n]
    for need in ("talk", "raise", "open"):
        if first(need) is None: sys.exit(f"no '{need}' event; see {out/'log_full.txt'}")
    S = lambda s: round(s * FPS)
    shots = []  # (name, frame)
    def add(n, f):
        if f is not None: shots.append((n, max(0, f)))
    add("a_arrival_talk-2.0", first("talk") - S(2))
    add("b_talk+1.0", first("talk") + S(1)); add("c_before_raise", first("raise") - 1)
    sigs, pulls, knocks = alln("sig"), alln("pull"), alln("knock")
    # A signature she stepped out of (no knock before the next one; the first such of the first three) and one that knocked
    # her down (the first): each its cast, pull and (knocked) knock frames.
    def knocked(k):
        nxt = sigs[k + 1] if k + 1 < len(sigs) else 10**9
        return next((f for f in knocks if sigs[k] <= f < nxt), None)
    outk = next((k for k in range(min(3, len(sigs))) if knocked(k) is None), None)
    hitk = next((k for k in range(len(sigs)) if knocked(k) is not None), None)
    for tag, k in (("sigOut", outk), ("sigKnock", hitk)):
        if k is None: continue
        s0 = sigs[k]
        add(f"{tag}{k + 1}_cast+0.00", s0); add(f"{tag}{k + 1}_cast+0.35", s0 + S(0.35)); add(f"{tag}{k + 1}_cast+0.70", s0 + S(0.7))
        pm = next((f for f in pulls if f >= s0), None)
        if pm is not None:
            add(f"{tag}{k + 1}_pull+0.5", pm + S(0.5)); add(f"{tag}{k + 1}_pull+1.2", pm + S(1.2))
        if knocked(k) is not None: add(f"{tag}{k + 1}_knock+0.2", knocked(k) + S(0.2))
    print("sigs", len(sigs), "stepped out:", [k + 1 for k in range(len(sigs)) if knocked(k) is None], "knocked:", [k + 1 for k in range(len(sigs)) if knocked(k) is not None])
    if first("low"): add("low+0.5", first("low") + S(0.5))
    if first("flare"): add("flare+0.3", first("flare") + S(0.3)); add("flare+1.0", first("flare") + S(1.0))
    if first("down"): add("down+0.5", first("down") + S(0.5)); add("down+2.0", first("down") + S(2.0))
    if first("cue"): add("cue+0.5", first("cue") + S(0.5))
    if first("gone"): add("gone+0.5", first("gone") + S(0.5))
    add("open+2.0", first("open") + S(2))
    t0 = max(0, first("talk") - S(1)) / FPS
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-ss", f"{t0:.3f}", "-i", str(avi), "-t", f"{first('open') / FPS + 4 - t0:.3f}",
                    "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-an", str(out / "clip.mp4")], check=True)
    done = []
    for n, f in shots:
        p = out / f"{n}.png"
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(avi), "-vf", f"select=eq(n\\,{f})", "-frames:v", "1", "-vsync", "0", str(p)], check=True)
        if p.exists(): done.append((n, p))
    W, H = 960, 540
    rows = (len(done) + 3) // 4
    sheet = Image.new("RGB", (W * 4, H * max(1, rows)), "black"); d = ImageDraw.Draw(sheet)
    try: font = ImageFont.truetype("arial.ttf", 28)
    except Exception: font = ImageFont.load_default()
    for i, (n, p) in enumerate(done):
        im = Image.open(p).convert("RGB").resize((W, H)); x, y = (i % 4) * W, (i // 4) * H
        sheet.paste(im, (x, y)); d.text((x + 10, y + 8), n, fill="yellow", font=font)
    sheet.save(out / "sheet.jpg", quality=88)
    subprocess.run([sys.executable, str(ROOT / "tools" / "half.py"), str(out / "sheet.jpg")], check=True)
finally:
    avi.unlink(missing_ok=True)
print("done", out)
