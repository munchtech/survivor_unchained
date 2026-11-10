"""The lookdev stage (L1 B0): every material class side by side, under each lighting rig, at the game's cameras, in one
Godot run (src/Game/GameLookdev.cs, --lookdev). The stage stands in a tier-1 Deep Shaw arena (its painted ground, its air)
with nothing spawning: her (the game's idle), three wolves (VAT), two townsfolk, the Waystation's small plaster house,
the square's setts, barrel, crate, lamp post, boulder, spruce, young alder, pebbles, branches, the camp's fire, a lantern
and five material spheres (skin, leather, cloth, iron, bronze).

    python tools/style/lookdev.py shoot --out DIR [--rigs night,day,dawn,arena] [--extra "--cel off"] [--root WT]
    python tools/style/lookdev.py sheet DIR    -> DIR/lookdev_sheet.jpg (+ _half.jpg copies of every frame and the sheet)
    python tools/style/lookdev.py check DIR    -> each frame's mean luma, how much of it differs from the ground, and the
                                                  stage's own frame check (every item's box in frame, not covered; her centred)

Rigs: night (the Low Ford's play night), day (the town's day), dawn (the Low Ford's dawn), arena (the arena's own night);
all is the four. Cameras per rig: play (FollowCamera's play pose), close (the close view at its nearest, --close 1's),
side (15 degrees of pitch, three-quarters from the right, across the rows). Frames: DIR/lookdev_RIG_CAM.png at 1920x1080.
Like tools/style/frames.py, the run goes through tools/experience/demo_run.py, which builds and takes the godot turn
itself (one turn for the run); a shared worktree's build lock (look-l1's wtlock.sh) is the caller's.
--extra goes to the game (--cel off, --ink off, --grade-try ...). OUT defaults to survivorsunchained_inputs/look_l1/lookdev/r0."""
import json, os, shutil, subprocess, sys, time

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
INPUTS = r"C:\Users\munch\Desktop\survivorsunchained_inputs"
HER = ["--sex", "female", "--preset", "own", "--skin", "fair", "--eyes", "moss", "--hair", "braid"]
STAGE = ["--quick", "warden"] + HER + ["--zone", "arena", "--offer", "0", "--tier", "1", "--no-foes", "--nohud", "--count", "0"]
RIGS = ["night", "day", "dawn", "arena"]
MORE = ["morning", "wdawn", "wild"]  # (named only, never in all: GameLookdev.MoreRigs; L7 S1d wild = the Verge's day, day_wild)
CAMS = ["play", "close", "side"]


def opt(args, name, default):
    if name in args:
        i = args.index(name); v = args[i + 1]; del args[i:i + 2]; return v
    return default


def font(size=20):
    try: return ImageFont.truetype("arial.ttf", size)
    except Exception: return ImageFont.load_default()


def half(path):
    im = Image.open(path).convert("RGB")
    out = os.path.splitext(path)[0] + "_half.jpg"
    im.resize((im.width // 2, im.height // 2), Image.LANCZOS).save(out, quality=88)
    return out


def sheet(out_dir, rigs=None):
    rigs = rigs or [r for r in RIGS + MORE if any(os.path.exists(os.path.join(out_dir, f"lookdev_{r}_{c}.png")) for c in CAMS)]
    tw, th = 640, 360
    S = Image.new("RGB", (tw * len(CAMS), th * max(1, len(rigs))), (16, 16, 16))
    d = ImageDraw.Draw(S); f = font(20)
    for j, r in enumerate(rigs):
        for i, c in enumerate(CAMS):
            p = os.path.join(out_dir, f"lookdev_{r}_{c}.png"); x, y = i * tw, j * th
            if os.path.exists(p):
                S.paste(Image.open(p).convert("RGB").resize((tw, th), Image.LANCZOS), (x, y)); half(p)
            else: d.text((x + 10, y + th // 2), "MISSING", fill=(255, 80, 80), font=f)
            lab = f"{r} / {c}"
            d.rectangle([x, y, x + 11 * len(lab) + 10, y + 26], fill=(0, 0, 0)); d.text((x + 5, y + 2), lab, fill=(255, 230, 120), font=f)
    out = os.path.join(out_dir, "lookdev_sheet.jpg"); S.save(out, quality=90)
    subprocess.run([sys.executable, os.path.join(HERE, "..", "half.py"), out], capture_output=True)
    if not os.path.exists(os.path.splitext(out)[0] + "_half.jpg"): half(out)
    print(out)


def check(out_dir):
    """Numbers only: mean luma (0-255), and the share of pixels off the frame's ground (the median colour of its lowest
    tenth) by more than 24 levels, as a stand-in for 'the rows are in frame' (a bare-ground frame scores near 0)."""
    import numpy as np
    # The stage's own frame check (GameLookdev.LookFrame): each item's box on screen, in frame and covered, per frame.
    stage, items = {}, {}
    log = os.path.join(out_dir, "run", "logs", "lookdev.log")
    if os.path.exists(log):
        for ln in open(log, encoding="utf-8", errors="replace"):
            w = ln.split()
            if len(w) < 3 or w[0] != "lookdev-frame": continue
            if w[2] in ("PASS", "FAIL"): stage[w[1]] = " ".join(w[2:4]) if w[2] == "FAIL" else "PASS"
            elif len(w) >= 17: items.setdefault(w[1], []).append(dict(row=w[2], name=w[3], rect=[float(v) for v in w[5:9]], inside=float(w[10]), hidden=float(w[12]), foot=float(w[16])))
    rows = []
    for r in RIGS + MORE:
        for c in CAMS:
            p = os.path.join(out_dir, f"lookdev_{r}_{c}.png")
            if not os.path.exists(p): continue
            a = np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
            luma = (a @ np.array([0.2126, 0.7152, 0.0722], np.float32))
            ground = np.median(a[int(a.shape[0] * 0.9):].reshape(-1, 3), axis=0)
            off = (np.abs(a - ground).max(axis=2) > 24).mean()
            # The setts' mask check: the middle of their rectangle against a band of ground round it (mean RGB difference;
            # a culled or unpainted patch reads as the ground, near 0).
            setts = None
            for it in items.get(f"{r}_{c}", []):
                if it["name"] != "setts": continue
                H, Wd = a.shape[:2]; x0, y0, x1, y1 = it["rect"]
                ix = [int(max(0, min(1, v)) * n) for v, n in ((x0 + (x1 - x0) * .3, Wd), (y0 + (y1 - y0) * .3, H), (x1 - (x1 - x0) * .3, Wd), (y1 - (y1 - y0) * .3, H))]
                ox = [int(max(0, min(1, v)) * n) for v, n in ((x0 - (x1 - x0) * .25, Wd), (y0 - (y1 - y0) * .25, H), (x1 + (x1 - x0) * .25, Wd), (y1 + (y1 - y0) * .25, H))]
                ring = np.ones(a.shape[:2], bool); ring[:ox[1]] = ring[ox[3]:] = False; ring[:, :ox[0]] = ring[:, ox[2]:] = False
                ring[int(y0 * H):int(y1 * H), int(x0 * Wd):int(x1 * Wd)] = False
                inner = a[ix[1]:ix[3], ix[0]:ix[2]].reshape(-1, 3)
                if inner.size and ring.any(): setts = round(float(np.abs(inner.mean(0) - a[ring].mean(0)).mean()), 1)
            mid = luma[a.shape[0] // 3: 2 * a.shape[0] // 3, a.shape[1] // 3: 2 * a.shape[1] // 3].std()
            rows.append(dict(frame=f"{r}_{c}", mean=round(float(luma.mean()), 1), p01=round(float(np.percentile(luma, 1)), 1),
                             p99=round(float(np.percentile(luma, 99)), 1), off_ground=round(float(off), 3), centre_std=round(float(mid), 1),
                             black=bool(luma.mean() < 4), stage=stage.get(f"{r}_{c}", "no check"), setts_vs_ground=setts,
                             min_inside=min((i["inside"] for i in items.get(f"{r}_{c}", [])), default=None),
                             max_hidden=max((i["hidden"] for i in items.get(f"{r}_{c}", []) if i["name"] not in ("setts", "grass", "branches", "pebbles")), default=None)))
    for x in rows: print(x)
    json.dump(rows, open(os.path.join(out_dir, "check.json"), "w"), indent=1)
    json.dump(items, open(os.path.join(out_dir, "check_items.json"), "w"), indent=1)
    return rows


def shoot(args):
    root = os.path.abspath(opt(args, "--root", os.path.join(HERE, "..", "..")))
    out = os.path.abspath(opt(args, "--out", os.path.join(INPUTS, "look_l1", "lookdev", "r0")))
    rigs = [r for r in opt(args, "--rigs", "all").replace("all", ",".join(RIGS)).split(",") if r in RIGS + MORE]
    extra = opt(args, "--extra", "").split()
    os.makedirs(out, exist_ok=True)
    run = [dict(name="lookdev", timeout=240 + 40 * len(rigs), godot=["--fixed-fps", "60"],
                args=STAGE + ["--lookdev", ",".join(rigs)] + extra)]
    bp = os.path.join(out, "batch.json"); json.dump(run, open(bp, "w", encoding="utf-8"), indent=1)
    shots = os.path.join(root, "godot", ".shots")
    t0 = time.time() - 5
    # --stale-ok (as frames.py): passed to demo_run's turn, for a measure that needs no newer art (B3r3's swatch row)
    stale = ["--stale-ok"] if "--stale-ok" in args else []
    rc = subprocess.run([sys.executable, os.path.join(root, "tools", "experience", "demo_run.py"), bp, "--out", os.path.join(out, "run"), "--root", root] + stale).returncode
    if rc != 0: print("demo_run failed", rc); sys.exit(rc)
    got = {}
    for r in rigs:
        for c in CAMS:
            f = os.path.join(shots, f"lookdev_{r}_{c}_1.png")
            if os.path.exists(f) and os.path.getmtime(f) >= t0:
                shutil.copy2(f, os.path.join(out, f"lookdev_{r}_{c}.png")); got[f"{r}_{c}"] = True
            else: print(f"MISSING {r} {c} (see {out}\\run\\logs\\lookdev.log)")
    json.dump({"commit": subprocess.run(["git", "-C", root, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip(),
               "extra": extra, "rigs": rigs, "when": time.strftime("%Y-%m-%d %H:%M"), "frames": sorted(got)},
              open(os.path.join(out, "lookdev.json"), "w", encoding="utf-8"), indent=1)
    sheet(out, rigs)
    check(out)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] not in ("shoot", "sheet", "check"): print(__doc__); sys.exit(1)
    if a[0] == "shoot": shoot(a[1:])
    elif a[0] == "sheet": sheet(os.path.abspath(a[1]))
    else: check(os.path.abspath(a[1]))
