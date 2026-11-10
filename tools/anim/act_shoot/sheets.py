"""Review sheets for the --act shots (shoot.sh; godot/src/Actors/PlayerView.Act.cs). Folder M (env ACT_M) holds
<clip>/clips/<cam>/f%08d.png (30 fps, 1920x1080) and <clip>/logs/<cam>.log.

  sheets.py <clip>                 the old outputs: mp4 per camera, an 8-tile sheet and entry/tail strips cropped on the image's centre
  sheets.py --dense <clip> [--first S] [--every N] [--hold-every N] [--cams play,close]
      dense rows of 8 tiles, 1:1 pixels, each tile cropped round her tracked pelvis (the log's `act: scr` lines; clamped to the
      image). Frames: 3 movie frames before the act to 0.6 s after its end, every N-th movie frame (2), every hold-every-th (6)
      inside the held loop, every frame over the act's first S seconds (bladestorm_loop: 1.0); the act's first and last frame
      and each event's frame are always in. Labels: run time, the clip's frame at 60 fps counted from the act's start (negative
      before, end+n after), the event that fires there. Play tiles 300x300 (larger if her box needs it), close tiles sized to
      her box over the picked frames plus 15 cm. Writes <clip>_<cam>_dense_r<k>_1to1.png and _half.jpg, one pair per row (the
      half's labels are drawn at full size). A tile's picture is the movie file f<N> of its `act: scr f=N` line (proved on
      heroic_leap play, files 28-38: the quiet and the moving frames fall on the same N in the log and in the files).
  sheets.py --box <clip>           her box over the act per camera from the logs alone (choosing a close zoom): no pictures read
"""
import math, os, re, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw

M = Path(os.environ.get("ACT_M", r"C:\Users\munch\Desktop\survivorsunchained_inputs\motion_a1\stageB\actions"))
CROP = {"play": (300, 300), "close": (700, 1080)}
N = 8
PAD_M = 0.15                      # flesh, hair and cloth beyond the bones and the held pieces' boxes
FIRST = {"bladestorm_loop": 1.0}  # every frame over the act's first seconds (27 degrees of turn a frame)
W, H = 1920, 1080


def act_info(log):
    """(start run s, duration s, [(event, run s)], held loop (a, b) run s or None) of the first pass from the log."""
    txt = log.read_text(errors="ignore")
    m = re.search(r"act: \S+ at t=([\d.]+) .*?\(pass 1/\d+, ([\d.]+) s long\)", txt)
    ev = [(a, float(b)) for a, b in re.findall(r"act: \S+ event (\S+) hit at t=([\d.]+)", txt)]
    h = re.search(r"act: \S+ loop held over run \[([\d.]+), ([\d.]+)\]", txt)
    hold = (float(h.group(1)), float(h.group(2))) if h else None
    return (float(m.group(1)), float(m.group(2)), ev, hold) if m else (1.0, 3.0, ev, hold)


def track(log):
    """The log's `act: scr` lines: [{f, t, pelvis, head, foot, box, ppm}] in frame order."""
    out = []
    num = r"(-?[\d.]+)"
    pat = re.compile(rf"act: scr f=(\d+) t={num} pelvis={num},{num} head={num},{num} foot={num},{num} box={num},{num},{num},{num} ppm={num}")
    for m in pat.finditer(log.read_text(errors="ignore")):
        g = [float(v) for v in m.groups()]
        out.append(dict(f=int(g[0]), t=g[1], pelvis=(g[2], g[3]), head=(g[4], g[5]), foot=(g[6], g[7]), box=tuple(g[8:12]), ppm=g[12]))
    return out


def picks(tr, t0, dur, ev, hold, first, every, hold_every):
    """[(track index, label)] of the frames a dense sheet shows."""
    e = 1e-4
    i0 = next(i for i, r in enumerate(tr) if r["t"] >= t0 - e)
    i1 = max(i for i, r in enumerate(tr) if r["t"] <= t0 + dur + e)
    iz = max(i for i, r in enumerate(tr) if r["t"] <= t0 + dur + 0.6 + e)
    fire = {}
    for name, te in ev:
        k = next((i for i, r in enumerate(tr) if r["t"] >= te - e), None)
        if k is not None:
            fire[k] = (fire[k] + "+" if k in fire else "") + name
    out, nxt = [], max(0, i0 - 3)
    for i in range(max(0, i0 - 3), iz + 1):
        t = tr[i]["t"]
        step = 1 if first and t0 - e <= t < t0 + first else hold_every if hold and hold[0] - e <= t < hold[1] - e and i <= i1 else every
        if i < nxt and i not in fire and i not in (i0, i1):
            continue
        nxt = i + step
        lab = f"t={t:.2f} " + (f"end+{round((t - t0 - dur) * 60)}" if i > i1 else f"f{round((t - t0) * 60)}")
        if i == i0: lab += " START"
        if i == i1: lab += " END"
        if i in fire: lab += " " + fire[i].upper()
        out.append((i, lab))
    return out


def extents(tr, idx):
    """Her padded box round her pelvis over the frames: (left, right, up, down) px, and how many frames leave the image."""
    L = R = U = D = 0.0
    out = 0
    for i in idx:
        r = tr[i]; p = PAD_M * r["ppm"]; (px, py), (x0, y0, x1, y1) = r["pelvis"], r["box"]
        L, R, U, D = max(L, px - x0 + p), max(R, x1 - px + p), max(U, py - y0 + p), max(D, y1 - py + p)
        out += x0 - p < 0 or y0 - p < 0 or x1 + p > W or y1 + p > H
    return L, R, U, D, out


def dense(clip, first, every, hold_every, cams):
    files = []
    for cam in cams:
        d = M / clip / "clips" / cam
        log = M / clip / "logs" / f"{cam}.log"
        tr = track(log)
        if not tr or not any(d.glob("f*.png")):
            print(f"{clip} {cam}: no frames or no `act: scr` lines"); continue
        t0, dur, ev, hold = act_info(log)
        pk = picks(tr, t0, dur, ev, hold, first, every, hold_every)
        L, R, U, D, out = extents(tr, [i for i, _ in pk])
        mw, mh = (300, 300) if cam == "play" else (0, 0)
        tw, th = max(mw, 20 * math.ceil((L + R) / 20)), max(mh, 20 * math.ceil((U + D) / 20))
        tw, th = min(tw, W), min(th, H)
        ox, oy = L + (tw - L - R) / 2, U + (th - U - D) / 2   # the pelvis's place in the tile
        print(f"{clip} {cam}: {len(pk)} tiles of {tw}x{th}, {tr[len(tr) // 2]['ppm']:.0f} px/m, her box leaves the image on {out} of them")
        for k in range(0, len(pk), N):
            part = pk[k:k + N]
            row = Image.new("RGB", (tw * N, th + 18))
            dr = ImageDraw.Draw(row)
            for j, (i, lab) in enumerate(part):
                r = tr[i]
                im = Image.open(d / f"f{r['f']:08d}.png").convert("RGB")
                x0 = max(0, min(im.width - tw, round(r["pelvis"][0] - ox))); y0 = max(0, min(im.height - th, round(r["pelvis"][1] - oy)))
                row.paste(im.crop((x0, y0, x0 + tw, y0 + th)), (j * tw, 18))
                dr.text((j * tw + 3, 3), lab, fill=(255, 255, 255))
            f = M / clip / f"{clip}_{cam}_dense_r{k // N + 1}_1to1.png"
            row.save(f)
            # (the half-size copy: the pictures halved, the labels drawn again at full size so they still read)
            half = Image.new("RGB", (tw * N // 2, th // 2 + 18))
            half.paste(row.crop((0, 18, row.width, row.height)).resize((tw * N // 2, th // 2), Image.LANCZOS), (0, 18))
            hd = ImageDraw.Draw(half)
            for j, (_, lab) in enumerate(part):
                hd.text((j * tw // 2 + 3, 3), lab, fill=(255, 255, 255))
            half.save(str(f).replace("_1to1.png", "_half.jpg"), quality=90)
            files.append((f, len(part)))
    for f, n in files:
        print(f"{f}  ({n} tiles)  +  {f.name.replace('_1to1.png', '_half.jpg')}")


def box(clip):
    for cam in ("play", "close"):
        log = M / clip / "logs" / f"{cam}.log"
        tr = track(log) if log.exists() else []
        if not tr: continue
        t0, dur, ev, hold = act_info(log)
        idx = [i for i, r in enumerate(tr) if t0 - 0.11 <= r["t"] <= t0 + dur + 0.6]
        L, R, U, D, out = extents(tr, idx)
        bx = [tr[i]["box"] for i in idx]
        print(f"{clip} {cam}: act {t0:.2f}+{dur:.2f} s, {len(idx)} frames, {tr[idx[0]]['ppm']:.0f} px/m; box x {min(b[0] for b in bx):.0f}..{max(b[2] for b in bx):.0f} "
              f"y {min(b[1] for b in bx):.0f}..{max(b[3] for b in bx):.0f} (unpadded); round the pelvis L{L:.0f} R{R:.0f} U{U:.0f} D{D:.0f} padded; out of the image on {out} frames; events {ev}; hold {hold}")


def old(clip):
    import imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe()
    out = []
    for cam, (cw, ch) in CROP.items():
        d = M / clip / "clips" / cam
        fr = sorted(d.glob("f*.png"))
        if not fr:
            continue
        t0, dur, ev, _ = act_info(M / clip / "logs" / f"{cam}.log")
        subprocess.run([FF, "-y", "-loglevel", "error", "-framerate", "30", "-i", str(d / "f%08d.png"), "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-crf", "20", str(M / clip / f"{clip}_{cam}.mp4")], check=False)
        row = Image.new("RGB", (cw * N, ch + 18))
        dr = ImageDraw.Draw(row)
        for k in range(N):
            t = t0 + dur * k / (N - 1)
            im = Image.open(fr[min(len(fr) - 1, int(round(t * 30)))]).convert("RGB")
            cx, cy = im.width // 2, im.height // 2
            x0 = max(0, min(im.width - cw, cx - cw // 2)); y0 = max(0, min(im.height - ch, cy - ch // 2))
            row.paste(im.crop((x0, y0, x0 + cw, y0 + ch)), (k * cw, 18))
            near = min(ev, key=lambda e: abs(e[1] - t), default=None)
            dr.text((k * cw + 3, 3), f"t={t:.2f}" + (f"  ~{near[0]} ({near[1]:.2f})" if near else ""), fill=(255, 255, 255))
        f = M / clip / f"{clip}_{cam}_sheet_1to1.png"
        row.save(f)
        out.append(str(f))
        sw, sh = (400, 400) if cam == "play" else (cw, ch)
        t_end = t0 + dur
        for tag, frames in (("entry", [round(t0 * 30) - 2 + 2 * k for k in range(N)]),
                            ("tail", [round(t_end * 30) - 4 + 3 * k for k in range(N)])):
            strip = Image.new("RGB", (sw * N, sh + 18))
            sd = ImageDraw.Draw(strip)
            for k, fi in enumerate(frames):
                im = Image.open(fr[max(0, min(len(fr) - 1, fi))]).convert("RGB")
                cx, cy = im.width // 2, im.height // 2
                x0 = max(0, min(im.width - sw, cx - sw // 2)); y0 = max(0, min(im.height - sh, cy - sh // 2))
                strip.paste(im.crop((x0, y0, x0 + sw, y0 + sh)), (k * sw, 18))
                off = fi - round((t0 if tag == "entry" else t_end) * 30)
                sd.text((k * sw + 3, 3), f"{'start' if tag == 'entry' else 'end'}{off:+d}", fill=(255, 255, 255))
            g = M / clip / f"{clip}_{cam}_{tag}_1to1.png"
            strip.save(g)
            out.append(str(g))
    print("\n".join(out))
    if out:
        subprocess.run([sys.executable, "C:/Users/munch/Desktop/survivorsunchained/tools/half.py"] + out)


def main(a):
    def opt(k, d):
        return type(d)(a[a.index(k) + 1]) if k in a else d
    if "--box" in a:
        return box(a[a.index("--box") + 1])
    if "--dense" in a:
        clip = a[a.index("--dense") + 1]
        return dense(clip, opt("--first", FIRST.get(clip, 0.0)), opt("--every", 2), opt("--hold-every", 6), opt("--cams", "play,close").split(","))
    old(a[0])


main(sys.argv[1:])
