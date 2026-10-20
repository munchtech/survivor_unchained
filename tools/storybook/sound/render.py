"""Renders SB00's soundtrack bed (everything but the Watchman's spoken lines)
from the cue sheet, offline and the same every time.

    python tools/storybook/sound/render.py            # render, measure, write the oggs
    python tools/storybook/sound/render.py --wav x.wav  # also a wav of the bed, to listen to

Reads tools/storybook/sound/sb00_cues.json; writes godot/art/storybook/sb00/audio/
sb00_bed.ogg (the sum), sb00_music.ogg and sb00_fx.ogg (its two stems, which add
up to the bed), and tools/storybook/sound/measure.txt (loudness, peaks, the solo's
tuning, a level per second). Change a time in the sheet and run it again: that
is all it takes.
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dsp  # noqa: E402
from dsp import SR, filt, tvfilt  # noqa: E402
import sounds  # noqa: E402

ROOT = sounds.ROOT
SHEET = os.path.join(HERE, "sb00_cues.json")
OUT = os.path.join(ROOT, "godot", "art", "storybook", "sb00", "audio")


def curve(points, t0, n):
    """Breakpoints [[absolute seconds, value], ...] sampled over a cue that starts at t0."""
    return dsp.breakpoints(points, n, t0)


def render_cue(args):
    cue, sheet = args
    L = sheet["length"]
    t0 = cue["t"]
    length = min(cue.get("len", 4.0), L - t0)
    if cue["bus"] == "music":
        length = min(length, sheet["score_stop"] - t0 + 0.01)
    if length <= 0:
        return cue["id"], None, None, t0
    rng = dsp.rng_for(cue["id"])
    dry, wet = sounds.generate(cue["gen"], cue.get("p", {}), rng, length)
    n = int(length * SR)

    def fit(x):
        if x is None:
            return None
        x = np.asarray(x, dtype=np.float64)
        if len(x) < n:
            x = np.pad(x, ((0, n - len(x)),) + ((0, 0),) * (x.ndim - 1))
        return x[:n]

    dry, wet = fit(dry), fit(wet)
    dry = dsp.to_stereo(dry, cue.get("pan", 0.0), cue.get("width", 0.0))
    if wet is not None:
        wet = dsp.to_stereo(wet, cue.get("pan", 0.0))
    # filters, fixed or moving along the absolute timeline
    for kind in ("hp", "lp"):
        if kind in cue:
            v = cue[kind]
            if isinstance(v, list):
                f = curve(v, t0, n)
                dry = tvfilt(dry, kind, f, 0.707, block=128)
                if wet is not None:
                    wet = tvfilt(wet, kind, f, 0.707, block=128)
            else:
                dry = filt(dry, kind, v)
                if wet is not None:
                    wet = filt(wet, kind, v)
    g = np.full(n, dsp.db(cue.get("gain", 0.0)))
    if "auto" in cue:
        g *= dsp.db(curve(cue["auto"], t0, n))
    fi = int(cue.get("fade_in", 0.0) * SR)
    if fi > 0:
        g[:fi] *= np.sin(np.linspace(0, np.pi / 2, fi)) ** 2
    fo = int(cue.get("fade_out", 0.0) * SR)
    if fo > 0:
        fo = min(fo, n)
        g[n - fo:] *= np.cos(np.linspace(0, np.pi / 2, fo)) ** 2
    if cue["bus"] == "music":
        # the score stops when the traveler leaves the firelight: the bow lifts
        ss = int((sheet["score_stop"] - t0) * SR)
        lift = int(sheet.get("score_stop_lift", 0.12) * SR)
        if ss < n:
            g[ss:] = 0
        a = max(0, ss - lift)
        if a < n:
            g[a:min(n, ss)] *= np.cos(np.linspace(0, np.pi / 2, min(n, ss) - a)) ** 2
    dry = dry * g[:, None]
    sends = {}
    for room, amt in cue.get("send", {}).items():
        sends[room] = dry * amt
    if wet is not None:
        room = next(iter(cue.get("send", {"valley": 0})))
        sends[room] = sends.get(room, 0) + wet * g[:, None]
    return cue["id"], dry, sends, t0


def place(buf, x, t0):
    s = int(round(t0 * SR))
    e = min(len(buf), s + len(x))
    if e > s:
        buf[s:e] += x[: e - s]


def speech_windows(sheet):
    """When the Watchman speaks: each line from its plate's start + the
    offset, at the sheet's words per second (the doc's Lines table)."""
    out = []
    for ln in sheet["lines"]:
        s = sheet["plates"][ln["plate"]][0] + sheet.get("line_offset", 0.3)
        out.append((s, s + ln["words"] / sheet.get("words_per_sec", 2.0), ln["id"]))
    return out


def duck_gain(bed, sheet):
    """The bed under the Watchman: wherever he speaks, its short-term (1 s)
    loudness is held at or under the sheet's target, by a gain that leans in
    0.4 s and lets go over 0.8 s. The composed levels do most of it; this
    catches what pokes up."""
    n = len(bed)
    target = sheet["mix"]["under_voice_lufs"]
    t, l = dsp.lufs_curve(bed, window=1.0, hop=0.05)
    need = np.zeros_like(t)
    for s, e, _ in speech_windows(sheet):
        m = (t >= s - 0.2) & (t <= e + 0.2)
        need[m] = np.maximum(need[m], l[m] - target)
    need = np.clip(need, 0, 24)
    # look ahead: start leaning before a rise, then smooth
    k = int(0.4 / 0.05)
    ahead = np.array([need[i:i + k].max() for i in range(len(need))])
    sm = np.zeros_like(ahead)
    for i in range(len(ahead)):
        prev = sm[i - 1] if i else 0
        rate = 0.05 / 0.4 if ahead[i] > prev else 0.05 / 0.8
        sm[i] = prev + (ahead[i] - prev) * min(1, rate * 3)
    gdb = -np.interp(np.arange(n) / SR, t, sm)
    return dsp.db(gdb)


def limiter(x, ceiling_db, look=0.005, release=0.12):
    """A look-ahead peak limiter on the 4x-oversampled peak, for the splash only."""
    c = dsp.db(ceiling_db)
    from scipy.signal import resample_poly
    up = np.abs(resample_poly(x, 4, 1, axis=0)).max(axis=1)
    pk = up.reshape(-1, 4).max(axis=1)[: len(x)]
    if len(pk) < len(x):
        pk = np.pad(pk, (0, len(x) - len(pk)))
    need = np.minimum(1.0, c / np.maximum(pk, 1e-9))
    la = int(look * SR)
    from scipy.ndimage import minimum_filter1d
    need = minimum_filter1d(need, size=2 * la + 1, origin=0)
    g = np.empty_like(need)
    a = np.exp(-1 / (release * SR))
    cur = 1.0
    for i in range(len(need)):  # instant attack, smooth release
        cur = need[i] if need[i] < cur else need[i] + (cur - need[i]) * a
        g[i] = cur
    return g


def solo_tuning(sheet, solo):
    """The solo's notes as rendered: the median pitch over the middle of each
    note (glides and onsets left out), against the note asked for."""
    from pitch import yin, midi, name
    from scipy.signal import resample_poly
    rows = []
    for cue in sheet["cues"]:
        if cue["gen"] != "bowed" or cue["id"] not in solo:
            continue
        x = solo[cue["id"]].mean(axis=1)
        x16 = resample_poly(x, 1, 3)
        ts, fs, ap, rms = yin(x16, 16000, 55, 900, thresh=0.2)
        for nt in cue["p"]["notes"]:
            if cue["t"] + nt["t"] >= sheet["score_stop"]:
                continue
            a = nt["t"] + nt["d"] * 0.25
            b = nt["t"] + nt["d"] * (0.5 if nt.get("to") else 0.8)
            m = (ts >= a) & (ts <= b) & (fs > 0)
            if m.sum() < 3:
                continue
            got = float(np.median(midi(fs[m])))
            want = float(midi(dsp.note_hz(nt["n"])))
            rows.append((cue["id"], round(cue["t"] + nt["t"], 2), nt["n"], name(got), round(100 * (got - want), 1)))
    return rows


def write_ogg(path, x):
    """Ogg Vorbis, written in small blocks: libsndfile's Vorbis encoder overflows
    the stack when handed a minute and a half in one call."""
    with sf.SoundFile(path, "w", SR, 2, format="OGG", subtype="VORBIS") as f:
        for s in range(0, len(x), 4096):
            f.write(x[s:s + 4096])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", default=SHEET)
    ap.add_argument("--wav", help="also write the bed as a wav here (not for the repo)")
    ap.add_argument("--only", help="comma list of cue ids to render (auditioning)")
    ap.add_argument("--jobs", type=int, default=12)
    ap.add_argument("--levels", action="store_true", help="print each cue's own loudest second (dry, after its gain)")
    a = ap.parse_args()
    t_start = time.time()
    sheet = json.load(open(a.sheet))
    L = sheet["length"]
    n = int(round(L * SR))
    cues = [c for c in sheet["cues"] if not c.get("off")]
    if a.only:
        keep = set(a.only.split(","))
        cues = [c for c in cues if c["id"] in keep]
    stems = {"music": np.zeros((n, 2)), "fx": np.zeros((n, 2))}
    sends = {b: {r: np.zeros((n, 2)) for r in sheet["rooms"]} for b in stems}
    solo = {}
    with ProcessPoolExecutor(a.jobs) as ex:
        for cid, dry, snd, t0 in ex.map(render_cue, [(c, sheet) for c in cues]):
            if dry is None:
                continue
            cue = next(c for c in cues if c["id"] == cid)
            place(stems[cue["bus"]], dry, t0)
            for r, x in snd.items():
                place(sends[cue["bus"]][r], x, t0)
            if cue["gen"] == "bowed":
                solo[cid] = dry
            if a.levels:
                tl, ll = dsp.lufs_curve(dry, window=1.0, hop=0.1)
                print(f"  {cid:16s} {cue['bus']:5s} t={t0:6.2f}  loudest 1 s {ll.max():6.1f} LUFS at {t0 + tl[ll.argmax()]:6.2f}")
    # the rooms
    for b in stems:
        for r, spec in sheet["rooms"].items():
            if not np.any(sends[b][r]):
                continue
            ir = dsp.room_ir(spec["rt60"], lp=spec.get("lp", 6000), lp_end=spec.get("lp_end", 1200),
                             pre=spec.get("pre", 0.0), early=spec.get("early"), seed=r,
                             damp_lows=spec.get("damp_lows", 0.0))
            wet = dsp.convolve_st(sends[b][r], ir)[:n] * dsp.db(spec.get("gain", 0.0))
            stems[b] += wet
    # after the score stops, only a short ring of the room is left, then nothing
    ss = int(sheet["score_stop"] * SR)
    ring = int(sheet.get("score_ring", 0.6) * SR)
    stems["music"][ss:ss + ring] *= (np.cos(np.linspace(0, np.pi / 2, len(stems["music"][ss:ss + ring]))) ** 2)[:, None]
    stems["music"][ss + ring:] = 0
    # the well: from the black, the water and everything in it sinks away
    sk = sheet["sink"]
    tt = np.arange(n) / SR
    fx = stems["fx"]
    well_in = fx * dsp.breakpoints(sk["well_send"], n)[:, None]
    spec = sheet["rooms"][sk["room"]]
    ir = dsp.room_ir(spec["rt60"], lp=spec.get("lp", 3000), lp_end=spec.get("lp_end", 300), pre=spec.get("pre", 0.0),
                     early=spec.get("early"), seed="well")
    well = dsp.convolve_st(well_in, ir)[:n] * dsp.db(spec.get("gain", 0.0))
    fx = tvfilt(fx, "lp", dsp.breakpoints(sk["lp"], n), 0.707, block=128) * dsp.db(dsp.breakpoints(sk["gain"], n))[:, None]
    well = tvfilt(well, "lp", dsp.breakpoints(sk["lp"], n), 0.707, block=128) * dsp.db(dsp.breakpoints(sk["well_gain"], n))[:, None]
    stems["fx"] = fx + well
    # under the Watchman, and the peaks
    bed = stems["music"] + stems["fx"]
    g = duck_gain(bed, sheet)
    for b in stems:
        stems[b] *= g[:, None]
    bed = stems["music"] + stems["fx"]
    gl = limiter(bed, sheet["mix"]["ceiling_dbtp"] - 0.3)
    for b in stems:
        stems[b] *= gl[:, None]
    # true silence at the end: the last samples are digital zero
    # zeroed a little before the tail so the Vorbis blocks around it decode to exact zero
    z = int(round((L - sheet["silence_tail"] - sheet.get("zero_lead", 0.15)) * SR))
    for b in stems:
        stems[b][z:] = 0
    bed = stems["music"] + stems["fx"]
    os.makedirs(OUT, exist_ok=True)
    if not a.only:
        write_ogg(os.path.join(OUT, "sb00_bed.ogg"), bed)
        write_ogg(os.path.join(OUT, "sb00_music.ogg"), stems["music"])
        write_ogg(os.path.join(OUT, "sb00_fx.ogg"), stems["fx"])
    if a.wav:
        sf.write(a.wav, bed, SR, subtype="PCM_24")
    report(sheet, bed, stems, solo, time.time() - t_start, write=not a.only)


def report(sheet, bed, stems, solo, took, write=True):
    lines = []
    p = lines.append
    # what the game will play: decode the ogg back, so the numbers are the shipped file's
    path = os.path.join(OUT, "sb00_bed.ogg")
    shipped = sf.read(path, always_2d=True)[0] if write else bed
    p(f"rendered in {took:.0f} s; {len(shipped) / SR:.2f} s at {SR} Hz, stereo")
    p(f"integrated loudness (bed, shipped ogg): {dsp.lufs_integrated(shipped):.1f} LUFS")
    p(f"true peak (shipped ogg): {dsp.true_peak_db(shipped):.2f} dBTP")
    for b in stems:
        p(f"  {b} stem: {dsp.lufs_integrated(stems[b]):.1f} LUFS")
    tail = shipped[-int(sheet['silence_tail'] * SR):]
    p(f"last {sheet['silence_tail']} s: max |sample| = {np.max(np.abs(tail)):.2e} (0 is digital silence)")
    t, st = dsp.lufs_curve(shipped, window=3.0, hop=1.0)
    t1, mo = dsp.lufs_curve(shipped, window=1.0, hop=0.1)
    win = speech_windows(sheet)
    p("under the Watchman (bed's 1 s loudness while each line plays; target "
      f"{sheet['mix']['under_voice_lufs']} LUFS, he is about -16):")
    for s, e, lid in win:
        m = (t1 >= s) & (t1 <= e)
        p(f"  {lid:10s} {s:6.1f}-{e:5.1f} s  median {np.median(mo[m]):6.1f}  max {np.max(mo[m]):6.1f}")
    p("level per second (short-term 3 s loudness, LUFS, centred on each second; plate in brackets):")
    plates = sheet["plates"]
    row = []
    for ti, v in zip(t, st):
        pl = next((k for k, (a, b) in plates.items() if a <= ti < b), "black")
        row.append(f"{int(ti):3d}s {max(v, -99):6.1f} [{pl}]")
    for i in range(0, len(row), 6):
        p("  " + "  ".join(row[i:i + 6]))
    rows = solo_tuning(sheet, solo)
    if rows:
        worst = max(abs(r[4]) for r in rows)
        p(f"solo tuning, measured from the render (median over each note's middle): worst {worst:.1f} cents")
        for r in rows:
            p(f"  {r[0]:14s} {r[1]:6.2f}s  asked {r[2]:4s} heard {r[3]:4s} {r[4]:+5.1f} c")
    txt = "\n".join(lines)
    print(txt)
    if write:
        open(os.path.join(HERE, "measure.txt"), "w").write(txt + "\n")


if __name__ == "__main__":
    main()
