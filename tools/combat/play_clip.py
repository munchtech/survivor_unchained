"""Shoot a whole run of the Autopilot's human hands at 1:1 (1920x1080) and cut it into the evidence for a press-rhythm judge.

  python tools/combat/play_clip.py NAME --minutes M [--fps 30] [--godot-args "..."]

Godot args after `--` come from --godot-args (zone, quick, --auto human, grants...). The game's --clip prints `skill press frame N slot S t T
skill ID kind K resolve V/M` (Autopilot.cs) and `flare press frame N ...` (FlareFx.cs).
Output: C:/Users/munch/Desktop/survivorsunchained_inputs/combat_m3/NAME/
  clip.mp4, presses.txt, rhythm.txt (per minute: presses by skill and kind, the Resolve at the presses of non-grip skills, the longest gap
  with no press of a non-grip skill), moments/ + moments_sheet(.jpg,_half.jpg) (first 12 presses of each non-grip skill, first 3 Flares:
  frames N-6, N, contact), strip.jpg + strip_half.jpg (a frame every 30 s), log.txt.
A grip skill is one that ever prints hold-start. Takes the godot turn (tools/turn.py) and gives it back in a finally; the AVI is deleted.
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
GODOT = os.environ.get("GODOT", "C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe")
FFMPEG = "C:/Users/munch/AppData/Roaming/Python/Python314/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
TURN = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
OUT = Path("C:/Users/munch/Desktop/survivorsunchained_inputs/combat_m3")

ap = argparse.ArgumentParser()
ap.add_argument("name"); ap.add_argument("--minutes", type=float, required=True)
ap.add_argument("--fps", type=int, default=30); ap.add_argument("--godot-args", default="")
a = ap.parse_args()
FPS = a.fps
out = OUT / a.name
shutil.rmtree(out, ignore_errors=True); (out / "moments").mkdir(parents=True)
tmp = Path(tempfile.mkdtemp(prefix="playclip_", dir=str(OUT)))
avi = tmp / "movie.avi"
extra = a.godot_args.split()
if "--auto" not in extra: extra += ["--auto", "human"]
frames = int((a.minutes * 60 + 8) * FPS)
gargs = [GODOT, "--path", str(ROOT / "godot"), "--resolution", "1920x1080", "--write-movie", str(avi),
         "--fixed-fps", str(FPS), "--audio-driver", "Dummy", "--quit-after", str(frames), "--",
         "--clip", "--shot", "clip", "--seconds", str(a.minutes * 60 + 5)] + extra
ov = ROOT / "godot" / "override.cfg"
if ov.exists(): ov.unlink()
label = f"M3: play clip {a.name}"
subprocess.run([sys.executable, TURN, "take", "godot", label, "--wait", "1800"], check=True)
try:
    log = subprocess.run(gargs, capture_output=True, text=True, errors="replace")
    (out / "log.txt").write_text(log.stdout + "\n" + log.stderr, encoding="utf-8")
finally:
    subprocess.run([sys.executable, TURN, "give", "godot", label])
try:
    presses = []
    for m in re.finditer(r"^skill press frame (\d+) slot (\S+) t (\S+) skill (\S+) kind (\S+) resolve ([\d.]+)/(\d+)", log.stdout, re.M):
        presses.append(dict(f=int(m[1]), slot=m[2], t=float(m[3]), skill=m[4], kind=m[5], res=float(m[6]), cap=float(m[7])))
    flares = [int(m[1]) for m in re.finditer(r"^flare press frame (\d+)", log.stdout, re.M)]
    errs = [l for l in (log.stdout + log.stderr).splitlines() if re.search(r"ERROR|Exception|Failed", l)]
    with open(out / "log.txt", "a", encoding="utf-8") as f:
        f.write("\n--- press lines ---\n" + "\n".join(re.findall(r"^(?:skill|flare) press frame.*$", log.stdout, re.M))
                + f"\n--- {len(errs)} error lines ---\n" + "\n".join(errs[:50]) + "\n")
    (out / "presses.txt").write_text("\n".join(
        [f"{p['f']/FPS:8.2f}s  skill press frame {p['f']} slot {p['slot']} skill {p['skill']} kind {p['kind']} resolve {p['res']}/{p['cap']:.0f}" for p in presses]
        + [f"{f/FPS:8.2f}s  flare press frame {f}" for f in flares]) + "\n", encoding="utf-8")
    grip = {p["skill"] for p in presses if p["kind"].startswith("hold")}
    nong = [p for p in presses if p["skill"] not in grip and not p["kind"].startswith("hold")]
    total = a.minutes * 60
    lines = [f"grip skills (hold-start seen): {sorted(grip)}", f"flares: {len(flares)} at {[round(f/FPS,1) for f in flares]}"]
    for mi in range(int(-(-total // 60))):
        lo, hi = mi * 60, min(total, mi * 60 + 60)
        ps = [p for p in presses if lo <= p["f"] / FPS < hi]
        c = Counter(f"{p['skill']}:{p['kind']}" for p in ps)
        ng = [p for p in nong if lo <= p["f"] / FPS < hi]
        times = [lo] + [p["f"] / FPS for p in ng] + [hi]
        gap = max(b - x for x, b in zip(times, times[1:]))
        lines.append(f"minute {mi+1}: {dict(sorted(c.items()))} | flares {sum(lo <= f/FPS < hi for f in flares)} | resolve at non-grip presses sum {sum(p['res'] for p in ng):.0f} "
                     f"(value before each press; the spend itself is not printed) | longest gap with no non-grip press {gap:.1f}s")
    allt = [0] + [p["f"] / FPS for p in nong] + [total]
    lines.append(f"whole run: longest gap with no non-grip press {max(b - x for x, b in zip(allt, allt[1:])):.1f}s; non-grip presses {len(nong)}")
    (out / "rhythm.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))

    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(avi), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-an", str(out / "clip.mp4")], check=True)
    ev = json.loads((ROOT / "godot/data/anim/her_events.json").read_text(encoding="utf-8")).get("clips", {})

    def grab(n, path):
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(avi), "-vf", f"select=eq(n\\,{max(0, n)})", "-frames:v", "1", "-vsync", "0", str(path)], check=True)

    try: font = ImageFont.truetype("arial.ttf", 26)
    except Exception: font = ImageFont.load_default()
    W, H = 960, 540

    def sheet(items, name, cols):
        rows = (len(items) + cols - 1) // cols
        sh = Image.new("RGB", (W * cols, H * max(rows, 1)), "black"); d = ImageDraw.Draw(sh)
        for i, (lab, p) in enumerate(items):
            if not p.exists(): continue
            im = Image.open(p).convert("RGB").resize((W, H)); x, y = (i % cols) * W, (i // cols) * H
            sh.paste(im, (x, y)); d.rectangle([x, y, x + W, y + 36], fill=(0, 0, 0)); d.text((x + 8, y + 4), lab, fill="white", font=font)
        sh.save(out / f"{name}.jpg", quality=92)
        sh.resize((sh.width // 2, sh.height // 2)).save(out / f"{name}_half.jpg", quality=90)

    picks, seen = [], Counter()
    for p in nong:
        if p["kind"] == "dash": continue
        if seen[p["skill"]] < 12: seen[p["skill"]] += 1; picks.append((p["f"], p["skill"], p["kind"]))
    for f in flares[:3]: picks.append((f, "flare", "press"))
    items = []
    for n, sk, kd in picks:
        c = ev.get(sk, {}).get("contact", [None])[0]
        cf = n + (round(c * FPS / 60) if c is not None else 12)
        for tag, fr in (("pre", n - 6), ("press", n), ("contact", cf)):
            pth = out / "moments" / f"{sk}_{n}_{tag}.png"
            grab(fr, pth); items.append((f"{sk} {kd} {n/FPS:.1f}s {tag}", pth))
    for i in range(0, len(items), 24):
        sheet(items[i:i + 24], "moments_sheet" if i == 0 else f"moments_sheet_{i//24}", 3)
    st = []
    for s in range(0, int(total) + 1, 30):
        pth = tmp / f"s{s}.png"; grab(s * FPS, pth); st.append((f"{s}s", pth))
    sheet(st, "strip", 4)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
