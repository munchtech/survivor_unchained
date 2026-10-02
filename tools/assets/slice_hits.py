"""Long recordings of many blows cut into one file per blow.

    python tools/assets/slice_hits.py <in dir> <out dir> [--max 6] [--len 0.9]

Each recording is scanned for onsets: where the short-term energy jumps
well above the energy just before it. Each blow is cut from a few
milliseconds before its onset to `len` seconds after (or to the next blow),
faded out over its last fifth, trimmed of silence, and peak-normalised to
-1 dBFS. The strongest `max` blows of each recording are kept, each named
after its recording, as 48 kHz mono 16-bit WAV.
"""
import argparse
import glob
import os
import re
import wave

import numpy as np


def read(path):
    w = wave.open(path)
    ch, sw, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
    raw = w.readframes(n)
    if sw == 2:
        d = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    elif sw == 3:
        b = np.frombuffer(raw, np.uint8).reshape(-1, 3)
        v = (b[:, 0].astype(np.int32) | b[:, 1].astype(np.int32) << 8 | b[:, 2].astype(np.int32) << 16)
        v = np.where(v & 0x800000, v - 0x1000000, v)
        d = v.astype(np.float32) / 8388608
    elif sw == 4:
        d = np.frombuffer(raw, np.int32).astype(np.float32) / 2147483648
    else:
        raise ValueError(f"{sw * 8}-bit audio")
    return d.reshape(-1, ch).mean(axis=1), rate


def resample(x, rate, to=48000):
    if rate == to:
        return x
    t = np.arange(int(len(x) * to / rate)) * rate / to
    return np.interp(t, np.arange(len(x)), x).astype(np.float32)


def onsets(x, rate):
    hop = int(rate * 0.005)
    e = np.array([np.sqrt((x[i:i + hop] ** 2).mean() + 1e-12) for i in range(0, len(x) - hop, hop)])
    floor = np.percentile(e, 20) + 1e-5
    out, last = [], -10 ** 9
    for i in range(8, len(e)):
        before = e[i - 8:i - 1].mean() + floor
        if e[i] > before * 6 and e[i] > floor * 20 and (i - last) * hop > rate * 0.25:
            out.append((i * hop, e[i]))
            last = i
    return out


def write(path, x, rate=48000):
    w = wave.open(path, "wb")
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    w.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--max", type=int, default=6)
    ap.add_argument("--len", type=float, default=0.9)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    total = 0
    for f in sorted(glob.glob(os.path.join(a.src, "**", "*.wav"), recursive=True)):
        x, rate = read(f)
        x = resample(x, rate)
        rate = 48000
        hits = onsets(x, rate)
        starts = [s for s, _ in hits]
        best = sorted(hits, key=lambda h: -h[1])[: a.max]
        base = re.sub(r"[^a-z0-9]+", "_", os.path.splitext(os.path.basename(f))[0].lower()).strip("_")
        for k, (s, _) in enumerate(sorted(best)):
            nxt = min([t for t in starts if t > s] + [len(x)])
            e = min(s + int(a.len * rate), nxt - int(0.01 * rate), len(x))
            seg = x[max(0, s - int(0.004 * rate)):e].copy()
            if len(seg) < rate * 0.05:
                continue
            # Trim the tail once it has fallen 50 dB below the peak.
            env = np.abs(seg)
            peak = env.max()
            above = np.nonzero(env > peak * 0.003)[0]
            seg = seg[: above[-1] + 1]
            fade = max(1, len(seg) // 5)
            seg[-fade:] *= np.linspace(1, 0, fade)
            seg *= 0.89 / max(1e-6, np.abs(seg).max())
            write(os.path.join(a.out, f"{base}_{k}.wav"), seg)
            total += 1
    print(f"{total} blows")


if __name__ == "__main__":
    main()
