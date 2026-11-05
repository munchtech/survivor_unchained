"""Shoot a Flare clip at 1:1 (1920x1080, 60 fps, with the game's audio) in the arena under `--auto idle` (the bot stands; plain --auto presses the Flare at once, so --cast would be moot).
--cast T is Journey.Playtime seconds (arena time).
--time day: the arena is always night (ArenaRun.TimeOf), so a day clip is shot on the Verge (--zone verge --time day) with a
placed, still horde (--horde 25 --dist 4 --spread 8 --no-spawn, as tools/audio/moments.json m05_long_cut; your --godot-args
--horde overrides it); use a short --cast there (3 or so), since the horde stands at her from the start.

  python tools/fx/flare_clip.py NAME --flare ID [--cast T] [--time night|day] [--pre 1.0] [--len 6.0]
                                [--quick warden|arcanist|stalker|reaver] [--godot-args "--horde 25 --seed 7"]

Output: C:/Users/munch/Desktop/survivorsunchained_inputs/flare_h7/NAME/
  clip.mp4 (H.264+AAC, `pre` s before the press, `len` s long), long.wav + long_flare.wav (the tape and the flare stem from
  4 s before the press to the clip's end; long.txt: the press's second in them; the log's [soundlog] lines count the cue ids),
  f+0.32.png style frames at press
  offsets -0.10 .. +4.00 s, sheet.jpg (half-size frames, 4 a row, labelled), sheet_half.jpg, log.txt.

The press frame comes from the game's own `flare press frame N` line (FlareFx.Press, with --clip).
Sound: --shot silences the live mixer, so the game's offline tape (--wav tmp/tape.wav --stems, Dummy audio driver) is cut to the clip
window and muxed in; tape.wav and flare_stem.wav (same window) are kept. The onset line checks tape vs movie alignment.
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
ap.add_argument("--quick", default="warden", help="the calling she plays (warden, arcanist, stalker, reaver): a Flare is its calling's")
ap.add_argument("--zone", default=None, help="default arena by night, verge by day (the arena has no day)")
ap.add_argument("--sound", action="store_true", help="drop --shot so the game plays its audio (Synth.cs returns early under --shot): clip.mp4 then has sound, but the run is unseeded and the struck-down line and slow-frame pictures are gone (not tested)")
a = ap.parse_args()

out = OUT / a.name
shutil.rmtree(out, ignore_errors=True); out.mkdir(parents=True)
tmp = Path(tempfile.mkdtemp(prefix="flareclip_", dir=str(OUT)))
avi = tmp / "movie.avi"
ZONE = a.zone or ("verge" if a.time == "day" else "arena")
if ZONE == "verge" and "--horde" not in a.godot_args.split(): a.godot_args = "--horde 25 --dist 4 --spread 8 --no-spawn " + a.godot_args
label = f"flare-h7: clip {a.name}"
frames = int((a.cast + a.pre + a.len + 4) * FPS)  # headroom; the press lands near cast + startup
gargs = [GODOT, "--path", str(ROOT / "godot"), "--resolution", "1920x1080", "--write-movie", str(avi),
         "--fixed-fps", str(FPS), "--audio-driver", "Dummy", "--quit-after", str(frames), "--",
         "--quick", a.quick, "--zone", ZONE, "--offer", "0", "--auto", a.bot, "--flare", a.flare,
         "--cast", str(a.cast), "--time", a.time, "--clip"] + ([] if a.sound else ["--shot", "clip", "--seconds", str(a.cast + a.len + 2)]) + (["--wav", str(tmp / "tape.wav"), "--stems", "--soundlog"] if not a.sound else []) + a.godot_args.split()
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
    import numpy as np, soundfile as sf
    tape, sr = sf.read(str(tmp / "tape.wav"), dtype="float32", always_2d=True)
    stem, _ = sf.read(str(tmp / "tape_flare.wav"), dtype="float32", always_2d=True)
    # The tape adds one sample block per game frame (Synth._Process), so tape time is movie time from the
    # frame Synth came up; the flare stem's first big onset near the press measures any offset.
    lo = max(0, int((pf / FPS - 1.0) * sr)); env = np.abs(stem).max(axis=1)
    pk = env[lo:lo + 6 * sr].max()
    first = lambda th: (lo + np.nonzero(env[lo:] > th * pk)[0][0]) / sr if (env[lo:] > th * pk).any() else float("nan")
    onset, swell = first(0.05), first(0.25)  # the cue's first sound; and where the swell passes 25% of its peak
    print(f"flare stem 25%-of-peak point {swell:.3f}s ({(swell - pf / FPS) * FPS:+.1f} frames: the cue swells, so this is not the onset)")
    off_frames = (onset - pf / FPS) * FPS
    print(f"flare stem first onset {onset:.3f}s vs press {pf/FPS:.3f}s: {off_frames:+.1f} frames")
    a0 = int(ss * sr); a1 = a0 + int(a.len * sr)
    sf.write(str(out / "tape.wav"), tape[a0:a1], sr); sf.write(str(out / "flare_stem.wav"), stem[a0:a1], sr)
    # (for flare_measure's loudness: 4 s of the fight before the press to the clip's end, the tape and the flare stem)
    l0 = max(0, int((pf / FPS - 4.0) * sr))
    sf.write(str(out / "long.wav"), tape[l0:a1], sr); sf.write(str(out / "long_flare.wav"), stem[l0:a1], sr)
    (out / "long.txt").write_text(f"press_s {(pf / FPS) - l0 / sr:.4f}\n", encoding="utf-8")
    mean_db = 20 * np.log10(max(1e-9, float(np.sqrt((tape[a0:a1] ** 2).mean()))))
    print(f"tape window rms {mean_db:.1f} dBFS")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-ss", f"{ss:.3f}", "-i", str(avi), "-i", str(out / "tape.wav"),
                    "-t", str(a.len), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", str(out / "clip.mp4")], check=True)
    shots = []
    for o in OFFSETS:
        n = f"f{o:+.2f}.png"
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(avi), "-vf", f"select=eq(n\\,{max(0, pf + round(o*FPS))})",
                        "-frames:v", "1", "-vsync", "0", str(out / n)], check=True)
        shots.append((o, out / n))
    # The stop's last held frame (two before the release, the log's 'flare release frame N'): flare_measure's true-hold pair.
    rm = re.search(r"flare release frame (\d+)", log.stdout)
    if rm:
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(avi), "-vf", f"select=eq(n\\,{int(rm.group(1)) - 2})",
                        "-frames:v", "1", "-vsync", "0", str(out / "f_stop_end.png")], check=True)
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
