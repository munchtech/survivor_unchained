"""The twelve frames (H2, one look): the demo's whole look shot in one Godot batch, so every restyle
round re-shoots the same frames with one command and is judged against the same twelve (plus her close-up).

    python tools/style/frames.py shoot [--out DIR] [--only 04,09] [--extra "--grade-try vib=1.1"] [--scout] [--root WT] [--stale-ok]
    python tools/style/frames.py sheet DIR                 -> DIR/sheet.jpg from DIR/frames/*.png (+ _half.jpg copies)
    python tools/style/frames.py compare BEFORE AFTER OUT  -> OUT/NN_id_ab.jpg (before | after, 1:1 halves) + OUT/ab_sheet.jpg

The frames, in the player's order (docs/design/LOOK_BIBLE.md judges them as one game):
  01 title  02 sb00 (one plate)  03 c01 (shot 12, her)  04 verge_day  05 ford_night  06 warden (the fight, play camera)
  07 town_day  08 lamps  09 shaw_horde  10 pack_mother  11 result (won)  12 hud (over play)  13 close (her, closest zoom)
One godot turn for the batch (tools/experience/demo_run.py: builds first, one Godot per run at 1920x1080 with
--fixed-fps 60 so game time steps evenly and a round's frames are the same moments as the last's). Each run's frames
land in godot/.shots; the picked one is copied to OUT/frames/NN_id.png with a half-size copy, and OUT/sheet.jpg
(4 x 4 tiles of 480 x 270, labelled) is the contact sheet. --scout keeps every candidate of each run in OUT/scout/
(with a sheet per run) to re-pick the moments. --extra goes on every run (a restyle round's flags). --only shoots
some frames and keeps the others in OUT/frames. Frame 08 loads the demo snapshot fr3_loop:loop_back_1
(survivorsunchained_inputs/demo_runs) when it is there, a quick start in the town otherwise.
OUT defaults to survivorsunchained_inputs/look_h2/r0."""
import json, os, shutil, subprocess, sys, time

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
INPUTS = r"C:\Users\munch\Desktop\survivorsunchained_inputs"
SNAPS = os.path.join(INPUTS, "demo_runs")
HER = ["--sex", "female", "--preset", "own", "--skin", "fair", "--eyes", "moss", "--hair", "braid"]
Q = ["--quick", "warden"] + HER
FPS = ["--fixed-fps", "60"]
ARENA = Q + ["--zone", "arena", "--offer", "0", "--tier", "1"]

# The runs (several frames may share one). (H2 R4, 3 Nov: the arena minutes since H1's teeth, tier 1 ten minutes to its
# boss (Content/Teeth, Pace 1): 09 at 8.5 +20 s (the pack streaming at her) and 12 at 6 +35 s
# (a pack at her lower left), picked from a scout; the old 14 and 20 of thirty were past the boss; 10 keeps 29.9.)
# The runs (several frames may share one). "scout" replaces the run's frame options in --scout mode.
RUNS = {
    "lk_title": dict(args=["--seconds", "6", "--count", "1"], fresh=True, timeout=300),
    "lk_sb00": dict(args=["--storybook", "sb00", "--sb-shots", "21.0", "--seconds", "300", "--until", "300"], timeout=400,
                    scout=["--storybook", "sb00", "--sb-shots", "8.0,21.0,30.0,42.0,51.0,64.0,76.0", "--seconds", "300", "--until", "300"]),
    "lk_c01": dict(args=Q + ["--cine", "c01", "--until", "30"], timeout=400),
    "lk_verge": dict(args=Q + ["--zone", "verge", "--time", "day", "--auto", "--seconds", "50", "--count", "1"], timeout=500,
                     scout=Q + ["--zone", "verge", "--time", "day", "--auto", "--seconds", "20", "--every", "15", "--count", "4"]),
    "lk_ford": dict(args=Q + ["--zone", "lowford", "--auto", "--pace", "--seconds", "100", "--every", "100", "--count", "2"], timeout=1500,
                    scout=Q + ["--zone", "lowford", "--auto", "--pace", "--seconds", "60", "--every", "20", "--count", "12"]),
    "lk_town": dict(args=Q + ["--zone", "waystation", "--time", "day", "--seconds", "18", "--count", "1"], timeout=400,
                    scout=Q + ["--zone", "waystation", "--time", "day", "--seconds", "6", "--every", "6", "--count", "3"]),
    "lk_lamps": dict(args=["--open", "lamps", "--seconds", "6", "--count", "1"], load_snap="fr3_loop:loop_back_1", timeout=400,
                     fallback=Q + ["--zone", "waystation", "--time", "day", "--open", "lamps", "--seconds", "6", "--count", "1"]),
    "lk_shaw": dict(args=ARENA + ["--auto", "--minute", "8.5", "--seconds", "20", "--count", "1"], timeout=600,
                    scout=ARENA + ["--auto", "--minute", "8.5", "--seconds", "20", "--every", "15", "--count", "4"]),
    "lk_pack": dict(args=ARENA + ["--auto", "--minute", "29.9", "--seconds", "18", "--count", "1"], timeout=600,
                    scout=ARENA + ["--auto", "--minute", "29.9", "--seconds", "12", "--every", "6", "--count", "5"]),
    "lk_result": dict(args=ARENA + ["--open", "result", "--seconds", "7", "--count", "1"], timeout=400,
                      scout=ARENA + ["--open", "result", "--seconds", "3", "--every", "2", "--count", "3"]),
    "lk_hud": dict(args=ARENA + ["--auto", "--minute", "6", "--seconds", "35", "--count", "1"], timeout=600,
                   scout=ARENA + ["--auto", "--minute", "6", "--seconds", "25", "--every", "10", "--count", "3"]),
    "lk_close": dict(args=Q + ["--zone", "waystation", "--time", "day", "--close", "1", "--seconds", "8", "--count", "1"], timeout=400,
                     scout=Q + ["--zone", "waystation", "--time", "day", "--close", "1", "--seconds", "6", "--every", "3", "--count", "2"]),
}

# The frames: id, label, run, the file it leaves in godot/.shots.
FRAMES = [
    ("01", "title", "lk_title", "lk_title.png"),
    ("02", "sb00", "lk_sb00", "sb_sb00_21.00.png"),
    ("03", "c01", "lk_c01", "lk_c01_c01_s12_1.png"),
    ("04", "verge_day", "lk_verge", "lk_verge.png"),
    ("05", "ford_night", "lk_ford", "lk_ford_00.png"),
    ("06", "warden", "lk_ford", "lk_ford_01.png"),
    ("07", "town_day", "lk_town", "lk_town.png"),
    ("08", "lamps", "lk_lamps", "lk_lamps.png"),
    ("09", "shaw_horde", "lk_shaw", "lk_shaw.png"),
    ("10", "pack_mother", "lk_pack", "lk_pack.png"),
    ("11", "result", "lk_result", "lk_result.png"),
    ("12", "hud", "lk_hud", "lk_hud.png"),
    ("13", "close", "lk_close", "lk_close.png"),
]


def opt(args, name, default):
    if name in args:
        i = args.index(name); v = args[i + 1]; del args[i:i + 2]; return v
    return default


def font(size=18):
    try: return ImageFont.truetype("arial.ttf", size)
    except Exception: return ImageFont.load_default()


def half(path):
    im = Image.open(path).convert("RGB")
    out = os.path.splitext(path)[0] + "_half.jpg"
    im.resize((im.width // 2, im.height // 2), Image.LANCZOS).save(out, quality=88)
    return out


def grid(files, labels, out, cols=4, tw=480):
    th = tw * 9 // 16
    rows = (len(files) + cols - 1) // cols
    S = Image.new("RGB", (tw * cols, th * rows), (16, 16, 16))
    d = ImageDraw.Draw(S); f = font(18)
    for i, (p, lab) in enumerate(zip(files, labels)):
        x, y = (i % cols) * tw, (i // cols) * th
        if p and os.path.exists(p):
            S.paste(Image.open(p).convert("RGB").resize((tw, th), Image.LANCZOS), (x, y))
        else:
            d.text((x + 10, y + th // 2), "MISSING", fill=(255, 80, 80), font=f)
        d.rectangle([x, y, x + 10 * len(lab) + 10, y + 24], fill=(0, 0, 0))
        d.text((x + 5, y + 2), lab, fill=(255, 230, 120), font=f)
    S.save(out, quality=88)
    return out


def sheet(out_dir):
    fr = os.path.join(out_dir, "frames")
    files = [os.path.join(fr, f"{n}_{i}.png") for n, i, _, _ in FRAMES]
    for p in files:
        if os.path.exists(p): half(p)
    print(grid(files, [f"{n} {i}" for n, i, _, _ in FRAMES], os.path.join(out_dir, "sheet.jpg")))


def compare(a_dir, b_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    pairs = []
    for n, i, _, _ in FRAMES:
        a, b = os.path.join(a_dir, "frames", f"{n}_{i}.png"), os.path.join(b_dir, "frames", f"{n}_{i}.png")
        if not (os.path.exists(a) and os.path.exists(b)): continue
        S = Image.new("RGB", (1920, 540), (0, 0, 0))
        S.paste(Image.open(a).convert("RGB").resize((960, 540), Image.LANCZOS), (0, 0))
        S.paste(Image.open(b).convert("RGB").resize((960, 540), Image.LANCZOS), (960, 0))
        d = ImageDraw.Draw(S); f = font(20)
        for x, t in ((0, f"{n} {i}: before"), (960, "after")):
            d.rectangle([x, 0, x + 11 * len(t) + 10, 26], fill=(0, 0, 0)); d.text((x + 5, 2), t, fill=(255, 230, 120), font=f)
        p = os.path.join(out_dir, f"{n}_{i}_ab.jpg"); S.save(p, quality=90); pairs.append(p)
    if pairs: print(grid(pairs, [os.path.basename(p)[:-7] for p in pairs], os.path.join(out_dir, "ab_sheet.jpg"), cols=2, tw=960))


def shoot(args):
    root = os.path.abspath(opt(args, "--root", os.path.join(HERE, "..", "..")))
    out = os.path.abspath(opt(args, "--out", os.path.join(INPUTS, "look_h2", "r0")))
    only = opt(args, "--only", None)
    extra = opt(args, "--extra", "").split()
    scout = "--scout" in args
    # --stale-ok: passed to demo_run's turn (an A/B in one tree that needs no newer art; say so on the sheet)
    stale = ["--stale-ok"] if "--stale-ok" in args else []
    frames = [f for f in FRAMES if only is None or f[0] in only.split(",") or f[1] in only.split(",")]
    runs = sorted({f[2] for f in frames}, key=list(RUNS).index)
    batch = []
    for name in runs:
        r = RUNS[name]
        a = list(r.get("scout", r["args"]) if scout else r["args"])
        e = dict(name=name, timeout=r["timeout"], godot=FPS)
        if r.get("fresh"): e["fresh"] = True
        if r.get("load_snap"):
            snap = "snap_" + r["load_snap"].replace(":", "_")
            if os.path.isdir(os.path.join(SNAPS, snap)):
                # (demo_run reads snapshots from its own OUT: a copy of the demo's there)
                dst = os.path.join(out, "run", snap); shutil.rmtree(dst, ignore_errors=True); shutil.copytree(os.path.join(SNAPS, snap), dst)
                e["load_snap"] = r["load_snap"]
            else: a = list(r["fallback"]); print(f"[{name}] no snapshot {r['load_snap']}: quick start instead")
        e["args"] = a + extra
        batch.append(e)
    os.makedirs(out, exist_ok=True)
    bp = os.path.join(out, "batch_scout.json" if scout else "batch.json")
    json.dump(batch, open(bp, "w", encoding="utf-8"), indent=1)
    shots = os.path.join(root, "godot", ".shots")
    t0 = time.time() - 5
    rc = subprocess.run([sys.executable, os.path.join(root, "tools", "experience", "demo_run.py"), bp, "--out", os.path.join(out, "run"), "--root", root] + stale).returncode
    if rc != 0: print("demo_run failed", rc); sys.exit(rc)
    fresh = lambda f: os.path.exists(os.path.join(shots, f)) and os.path.getmtime(os.path.join(shots, f)) >= t0
    if scout:
        sd = os.path.join(out, "scout"); os.makedirs(sd, exist_ok=True)
        for name in runs:
            pre = ("sb_sb00_",) if name == "lk_sb00" else (name + "_", name + ".")
            got = sorted(f for f in os.listdir(shots) if f.startswith(pre) and f.endswith(".png") and fresh(f))
            for f in got: shutil.copy2(os.path.join(shots, f), os.path.join(sd, f))
            if got: print(grid([os.path.join(sd, f) for f in got], [f[:-4] for f in got], os.path.join(sd, f"{name}_sheet.jpg")))
        return
    fr = os.path.join(out, "frames"); os.makedirs(fr, exist_ok=True)
    log = {"commit": subprocess.run(["git", "-C", root, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip(),
           "extra": extra, "when": time.strftime("%Y-%m-%d %H:%M"), "frames": {}}
    for n, i, run, f in frames:
        if fresh(f):
            shutil.copy2(os.path.join(shots, f), os.path.join(fr, f"{n}_{i}.png")); log["frames"][f"{n}_{i}"] = f
        else: print(f"MISSING {n} {i}: {f} not made this batch (see {out}\\run\\logs\\{run}.log)")
    lp = os.path.join(out, "frames.json")
    if os.path.exists(lp) and only:
        old = json.load(open(lp, encoding="utf-8")); old["frames"].update(log["frames"]); log["frames"] = old["frames"]
    json.dump(log, open(lp, "w", encoding="utf-8"), indent=1)
    sheet(out)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] not in ("shoot", "sheet", "compare"): print(__doc__); sys.exit(1)
    if a[0] == "shoot": shoot(a[1:])
    elif a[0] == "sheet": sheet(os.path.abspath(a[1]))
    else: compare(os.path.abspath(a[1]), os.path.abspath(a[2]), os.path.abspath(a[3]))
