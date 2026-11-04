"""Shoot a Flare clip at 1:1 (1920x1080, 60 fps, with the game's audio) in the arena under `--auto idle` (the bot stands; plain --auto presses the Flare at once, so --cast would be moot).
--cast T is Journey.Playtime seconds (arena time).

  python tools/fx/flare_clip.py NAME --flare ID [--cast T] [--time night|day] [--pre 1.0] [--len 6.0]
                                [--godot-args "--horde 25 --seed 7"]

Output: C:/Users/munch/Desktop/survivorsunchained_inputs/flare_h7/NAME/
  clip.mp4 (H.264+AAC, `pre` s before the press, `len` s long), f+0.32.png style frames at press
  offsets -0.10 .. +4.00 s, sheet.jpg (half-size frames, 4 a row, labelled), sheet_half.jpg, log.txt.

The press frame comes from the game's own `flare press frame N` line (FlareFx.Press, with --clip).
NOTE: under --shot (the default here, for the seed and the quit) the game is SILENT (Synth.cs); --sound drops it.
Takes the godot turn around the run (tools/turn.py) and gives it back in a finally.
GPU frame time for the same setup: run the same command by hand with `--perf` added to
--godot-args (Perf.cs prints the frame-time report); this tool does not run it.
"""
import argparse, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
GODOT = os.environ.get("GODOT", "C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe")
FFMPEG = "C:/Users/munch/AppData/Roaming/Python/Python314/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
TURN = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
OUT = Path("C:/Users/munch/Desktop/survivorsunchained_inputs/flare_h7")
OFFSETS = [-0.10, 0.03, 0.12, 0.22, 0.32, 0.42, 0.55, 0.70, 0.90, 1.20, 1.60, 2.20, 3.00, 4.00]
FPS = 60

ap = argparse.ArgumentParser()
ap.add_argument("name"); ap.add_argument("--flare", required=True)
ap.add_argument("--cast", type=float, default=50.0)
ap.add_argument("--time", default="night"); ap.add_argument("--pre", type=float, default=1.0)
ap.add_argument("--len", type=float, default=6.0); ap.add_argument("--bot", default="idle", help="Autopilot mode: idle (stands, so --cast T decides the press) or toward/across/away; the plain bot presses the full Flare itself the moment 3 foes are near")
ap.add_argument("--godot-args", default="")
ap.add_argument("--sound", action="store_true", help="drop --shot so the game plays its audio (Synth.cs returns early under --shot): clip.mp4 then has sound, but the run is unseeded and the struck-down line and slow-frame pictures are gone (not tested)")
a = ap.parse_args()

out = OUT / a.name
shutil.rmtree(out, ignore_errors=True); out.mkdir(parents=True)
tmp = Path(tempfile.mkdtemp(prefix="flareclip_", dir=str(OUT)))
avi = tmp / "movie.avi"
label = f"flare-h7: clip {a.name}"
frames = int((a.cast + a.pre + a.len + 4) * FPS)  # headroom; the press lands near cast + startup
gargs = [GODOT, "--path", str(ROOT / "godot"), "--resolution", "1920x1080", "--write-movie", str(avi),
         "--fixed-fps", str(FPS), "--quit-after", str(frames), "--",
         "--quick", "warden", "--zone", "arena", "--offer", "0", "--auto", a.bot, "--flare", a.flare,
         "--cast", str(a.cast), "--time", a.time, "--clip"] + ([] if a.sound else ["--shot", "clip", "--seconds", str(a.cast + a.len + 2)]) + a.godot_args.split()
ov = ROOT / "godot" / "override.cfg"
if ov.exists(): ov.unlink()
subprocess.run([sys.executable, TURN, "take", "godot", label, "--wait", "600"], check=True)
try:
    log = subprocess.run(gargs, capture_output=True, text=True, errors="replace")
    (out / "log.txt").write_text(log.stdout + "\n" + log.stderr, encoding="utf-8")
finally:
    subprocess.run([sys.executable, TURN, "give", "godot", label])
try:
    m = re.search(r"flare press frame (\d+)", log.stdout)
    if not m: sys.exit("no 'flare press frame' in the log; see " + str(out / "log.txt"))
    pf = int(m.group(1))
    print(re.search(r"flare press frame.*", log.stdout).group(0))
    s = re.search(r"struck down (\d+), standing in reach (\d+)", log.stdout)
    print(f"press frame {pf} ({pf/FPS:.2f}s)", s.group(0) if s else "(no struck-down line)")
    ss = max(0.0, pf / FPS - a.pre)
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-ss", f"{ss:.3f}", "-i", str(avi), "-t", str(a.len),
                    "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    str(out / "clip.mp4")], check=True)
    shots = []
    for o in OFFSETS:
        n = f"f{o:+.2f}.png"
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(avi), "-vf", f"select=eq(n\\,{max(0, pf + round(o*FPS))})",
                        "-frames:v", "1", "-vsync", "0", str(out / n)], check=True)
        shots.append((o, out / n))
    W, H = 960, 540
    sheet = Image.new("RGB", (W * 4, H * 4), "black"); d = ImageDraw.Draw(sheet)
    try: font = ImageFont.truetype("arial.ttf", 28)
    except Exception: font = ImageFont.load_default()
    for i, (o, p) in enumerate(shots):
        if not p.exists(): continue
        im = Image.open(p).convert("RGB").resize((W, H)); x, y = (i % 4) * W, (i // 4) * H
        sheet.paste(im, (x, y)); d.text((x + 10, y + 8), f"{o:+.2f}s", fill="yellow", font=font)
    sheet.save(out / "sheet.jpg", quality=88)
    subprocess.run([sys.executable, str(ROOT / "tools" / "half.py"), str(out / "sheet.jpg")], check=True)
    # half.py writes sheet_half.jpg next to it
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print("done", out)
