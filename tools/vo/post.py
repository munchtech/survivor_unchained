"""The dialogue edit and mix, as a studio would do it to a chosen take.

    clean   DC and rumble out (high-pass 70 Hz), clicks repaired
    edit    trimmed to the performance, a breath before it kept, a short
            tail after; dead air inside a line capped
    tone    gentle EQ (a little mud out, a little presence and air in),
            sibilance tamed, light compression
    place   the room the scene is in: early reflections and a short tail for
            an inn or a forge, a long one for a shrine or a cave, nothing for
            the narrator, who is close and dry; and that room's own tone
            underneath, so a line never starts out of digital silence
    voice   what some parts are as well as who: the Warden is enormous, the
            dead are hollow, a lampling's stressed words ring like its lamp
    level   loudness to -16 LUFS (the narrator -17), true peak under -1.5 dBTP

Then the parts of a line (the narrator's aside, the speaker) are joined with
the pause between them, and the whole is written as Ogg Vorbis, mono, 32 kHz.

    python tools/vo/post.py in.wav out.ogg --room inn [--fx giant]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy import signal

SR = 48000
# Speech has nothing a listener misses above 16 kHz; at 32 kHz the files are a
# third smaller for the same Vorbis quality.
OUT_SR = 32000
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# -------------------------------------------------------------- basics --

def load(path: str) -> np.ndarray:
    import librosa
    x, sr = sf.read(path, dtype="float32", always_2d=False)
    if x.ndim > 1:
        x = x.mean(axis=1)
    if sr != SR:
        x = librosa.resample(x, orig_sr=sr, target_sr=SR, res_type="soxr_vhq")
    return x.astype(np.float64)


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-12))


def biquad(kind: str, f: float, q: float = 0.707, gain_db: float = 0.0):
    """RBJ cookbook biquad as second-order sections."""
    A = 10 ** (gain_db / 40)
    w = 2 * np.pi * f / SR
    cw, sw = np.cos(w), np.sin(w)
    alpha = sw / (2 * q)
    if kind == "peak":
        b = [1 + alpha * A, -2 * cw, 1 - alpha * A]; a = [1 + alpha / A, -2 * cw, 1 - alpha / A]
    elif kind == "lowshelf":
        s = 2 * np.sqrt(A) * alpha
        b = [A * ((A + 1) - (A - 1) * cw + s), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - s)]
        a = [(A + 1) + (A - 1) * cw + s, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - s]
    elif kind == "highshelf":
        s = 2 * np.sqrt(A) * alpha
        b = [A * ((A + 1) + (A - 1) * cw + s), -2 * A * ((A - 1) + (A + 1) * cw), A * ((A + 1) + (A - 1) * cw - s)]
        a = [(A + 1) - (A - 1) * cw + s, 2 * ((A - 1) - (A + 1) * cw), (A + 1) - (A - 1) * cw - s]
    else:
        raise ValueError(kind)
    return signal.tf2sos(np.array(b) / a[0], np.array(a) / a[0])


def env_follow(x: np.ndarray, attack: float, release: float) -> np.ndarray:
    """A peak envelope with separate attack and release (seconds)."""
    a, r = np.exp(-1 / (attack * SR)), np.exp(-1 / (release * SR))
    y = np.abs(x)
    e = np.empty_like(y)
    v = 0.0
    for i, s in enumerate(y):
        v = a * v + (1 - a) * s if s > v else r * v + (1 - r) * s
        e[i] = v
    return e


def smooth_env(x: np.ndarray, win: float = 0.01) -> np.ndarray:
    n = max(1, int(win * SR))
    return np.sqrt(np.convolve(x * x, np.ones(n) / n, mode="same"))


# --------------------------------------------------------------- clean --

def clean(x: np.ndarray) -> np.ndarray:
    x = x - np.mean(x)
    sos = signal.butter(2, 70, "highpass", fs=SR, output="sos")
    x = signal.sosfiltfilt(sos, x)
    return declick(x)


def declick(x: np.ndarray, k: float = 9.0) -> np.ndarray:
    """Clicks are single-sample jumps far beyond the local slope: bridge them."""
    d = np.diff(x, prepend=x[0])
    local = np.convolve(np.abs(d), np.ones(64) / 64, mode="same") + 1e-6
    hits = np.where(np.abs(d) > k * local)[0]
    y = x.copy()
    for i in hits:
        a, b = max(0, i - 4), min(len(x) - 1, i + 4)
        y[a:b + 1] = np.linspace(y[a], y[b], b - a + 1)
    return y


# ---------------------------------------------------------------- edit --

def speech_bounds(x: np.ndarray, rel_db: float = -42.0) -> tuple[int, int]:
    e = db(smooth_env(x, 0.02))
    peak = np.percentile(e, 99.5)
    on = np.where(e > peak + rel_db)[0]
    if len(on) == 0:
        return 0, len(x)
    return int(on[0]), int(on[-1])


def edit(x: np.ndarray, head: float = 0.06, tail: float = 0.22, max_gap: float = 1.6) -> np.ndarray:
    s, e = speech_bounds(x)
    s = max(0, s - int(head * SR))
    e = min(len(x), e + int(tail * SR))
    x = x[s:e].copy()
    # Dead air inside the line, capped (a long pause is acting; two seconds of nothing is a fault).
    env = db(smooth_env(x, 0.03))
    quiet = env < np.percentile(env, 99.5) - 45
    out, i, n = [], 0, len(x)
    cap = int(max_gap * SR)
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            seg = x[i:j]
            if len(seg) > cap:
                keep = cap // 2
                seg = np.concatenate([seg[:keep], seg[-keep:]])
            out.append(seg)
            i = j
        else:
            j = i
            while j < n and not quiet[j]:
                j += 1
            out.append(x[i:j])
            i = j
    x = np.concatenate(out) if out else x
    fi, fo = int(0.008 * SR), int(0.06 * SR)
    x[:fi] *= np.linspace(0, 1, fi)
    x[-fo:] *= np.linspace(1, 0, fo) ** 2
    return x


# ---------------------------------------------------------------- tone --

# How close the mic is, by how loud the read is: a whisper is close (the
# chest's warmth comes up, the room falls away), a shout is further off.
NEAR = {"hushed": (2.5, -6.0), "quiet": (1.2, -3.0), "level": (0.0, 0.0), "raised": (-0.5, 2.0), "shout": (-1.0, 4.0)}


def tone(x: np.ndarray, sex: str = "m", vol: str = "level") -> np.ndarray:
    warmth = NEAR.get(vol, (0.0, 0.0))[0]
    sos = np.vstack([
        biquad("peak", 280 if sex == "m" else 350, 1.0, -1.5),     # mud
        biquad("peak", 3400, 0.8, 1.5),                            # presence
        biquad("highshelf", 10000, 0.7, 1.0),                      # air
        biquad("lowshelf", 180, 0.7, warmth),                      # proximity
    ])
    x = signal.sosfilt(sos, x)
    x = deess(x)
    return compress(x)


def deess(x: np.ndarray, thresh_db: float = -26.0, max_cut: float = 6.0) -> np.ndarray:
    band = signal.sosfilt(signal.butter(2, [5500, 9500], "bandpass", fs=SR, output="sos"), x)
    e = db(env_follow(band, 0.001, 0.05))
    over = np.clip(e - thresh_db, 0, max_cut)
    g = 10 ** (-over / 20)
    hi = signal.sosfilt(signal.butter(2, 5000, "highpass", fs=SR, output="sos"), x)
    return x - hi + hi * g


def compress(x: np.ndarray, thresh_db: float = -22.0, ratio: float = 2.5, attack: float = 0.008, release: float = 0.12) -> np.ndarray:
    peak = np.max(np.abs(x)) + 1e-9
    y = x / peak * 0.5
    e = db(env_follow(y, attack, release))
    over = np.clip(e - thresh_db, 0, None)
    g = 10 ** (-(over - over / ratio) / 20)
    return y * g


# --------------------------------------------------------------- place --

ROOMS = {
    # rt60 (s), wet (dB under dry), pre-delay (ms), tone colour, tone level dBFS
    "close":      (0.0,  -99, 0,  "none", -99),
    "inn":        (0.38, -19, 9,  "warm", -60),
    "tavern":     (0.42, -18, 10, "warm", -58),
    "watchhouse": (0.35, -19, 8,  "stone", -62),
    "hut":        (0.25, -21, 6,  "warm", -62),
    "forge":      (0.55, -18, 12, "fire", -57),
    "office":     (0.30, -21, 7,  "warm", -64),
    "shrine":     (1.10, -16, 18, "stone", -62),
    "tower":      (0.70, -18, 14, "stone", -63),
    "yard":       (0.12, -24, 20, "air", -60),
    "outdoor":    (0.10, -25, 25, "air", -60),
    "camp":       (0.18, -22, 30, "air", -59),
    "dig":        (1.40, -13, 25, "cave", -58),
    "ford":       (0.25, -22, 30, "water", -58),
}


def impulse(rt60: float, pre_ms: float, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int((rt60 * 1.2 + 0.05) * SR)
    t = np.arange(n) / SR
    tail = rng.standard_normal(n) * np.exp(-6.9 * t / max(rt60, 0.05))
    tail = signal.sosfilt(signal.butter(2, 4500, "lowpass", fs=SR, output="sos"), tail)
    ir = np.zeros(n + int(pre_ms * SR / 1000))
    p = int(pre_ms * SR / 1000)
    ir[p:p + n] += tail * 0.6
    for k in range(6):  # early reflections
        d = p + int(rng.uniform(0.002, 0.03 + rt60 * 0.03) * SR)
        if d < len(ir):
            ir[d] += rng.uniform(0.3, 0.7) * (-1) ** k
    return ir / (np.sqrt(np.sum(ir ** 2)) + 1e-9)


def room_tone(n: int, colour: str, level_db: float, seed: int) -> np.ndarray:
    if colour == "none" or level_db <= -90:
        return np.zeros(n)
    rng = np.random.default_rng(seed)
    w = rng.standard_normal(n)
    if colour in ("warm", "fire", "stone"):
        w = signal.sosfilt(signal.butter(1, 400 if colour != "stone" else 700, "lowpass", fs=SR, output="sos"), w)
    elif colour == "cave":
        w = signal.sosfilt(signal.butter(2, [60, 300], "bandpass", fs=SR, output="sos"), w)
    elif colour == "water":
        w = signal.sosfilt(signal.butter(2, [300, 2500], "bandpass", fs=SR, output="sos"), w)
        w *= 0.7 + 0.3 * np.sin(np.arange(n) / SR * 2 * np.pi * 0.7)
    elif colour == "air":
        w = signal.sosfilt(signal.butter(1, [150, 3000], "bandpass", fs=SR, output="sos"), w)
    if colour == "fire":  # the odd crackle
        pops = rng.random(n) < 4 / SR
        w += signal.sosfilt(signal.butter(2, 2500, "highpass", fs=SR, output="sos"), pops * rng.standard_normal(n) * 30)
    w /= np.sqrt(np.mean(w ** 2)) + 1e-9
    return w * 10 ** (level_db / 20)


def place(x: np.ndarray, room: str, seed: int = 7, vol: str = "level") -> np.ndarray:
    rt60, wet_db, pre, colour, tone_db = ROOMS.get(room, ROOMS["close"])
    wet_db += NEAR.get(vol, (0.0, 0.0))[1]
    if rt60 > 0:
        wet = signal.fftconvolve(x, impulse(rt60, pre, seed))[: len(x) + int(rt60 * SR)]
        y = np.zeros(len(wet))
        y[: len(x)] += x
        y += wet * 10 ** (wet_db / 20) * np.sqrt(np.mean(x ** 2)) / (np.sqrt(np.mean(wet ** 2)) + 1e-12)
        x = y
    return x


# --------------------------------------------------------------- voice --

def fx(x: np.ndarray, kind: str | None) -> np.ndarray:
    import librosa
    if not kind:
        return x
    if kind == "giant":
        # Slowed like a tape: lower and larger, with a sub-octave under it.
        slow = librosa.resample(x, orig_sr=SR, target_sr=int(SR / 0.8), res_type="soxr_vhq")
        sub = librosa.effects.pitch_shift(slow.astype(np.float32), sr=SR, n_steps=-12).astype(np.float64)
        sub = signal.sosfilt(signal.butter(2, 900, "lowpass", fs=SR, output="sos"), sub)
        y = slow + sub * 0.35
        return place(y, "dig", seed=11)
    if kind == "dead":
        y = signal.sosfilt(signal.butter(2, [220, 4200], "bandpass", fs=SR, output="sos"), x)
        hollow = signal.fftconvolve(y, impulse(0.25, 4, 13))[: len(y)]
        return y + 0.35 * hollow / (np.max(np.abs(hollow)) + 1e-9) * np.max(np.abs(y))
    if kind == "lamp":
        # A thin metallic ring under the voice (a comb at a lamp's pitch).
        d = int(SR / 1180)
        ring = np.zeros_like(x)
        ring[d:] = x[:-d]
        y = x + 0.28 * ring
        return signal.sosfilt(biquad("peak", 2400, 2.0, 3.0), y)
    return x


# --------------------------------------------------------------- level --

def loudness(x: np.ndarray, target: float = -16.0, ceiling_db: float = -1.5) -> np.ndarray:
    import pyloudnorm as pyln
    meter = pyln.Meter(SR)
    lufs = meter.integrated_loudness(x) if len(x) > SR * 0.4 else 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9) - 0.7
    if np.isfinite(lufs):
        x = x * 10 ** ((target - lufs) / 20)
    return limit(x, ceiling_db)


def limit(x: np.ndarray, ceiling_db: float) -> np.ndarray:
    """A look-ahead peak limiter judged on 4x oversampled (true) peaks."""
    c = 10 ** (ceiling_db / 20)
    up = signal.resample_poly(x, 4, 1)
    pk = np.abs(up).reshape(-1, 4).max(axis=1)[: len(x)]
    need = np.minimum(1.0, c / np.maximum(pk, 1e-9))
    from scipy.ndimage import minimum_filter1d
    look = int(0.005 * SR)
    # The gain a peak needs, from 5 ms before it to 5 ms after (look-ahead).
    g = minimum_filter1d(need, size=2 * look + 1)
    g = np.minimum(g, 1.0)
    rel = np.exp(-1 / (0.08 * SR))
    for i in range(1, len(g)):
        g[i] = min(g[i], 1 - (1 - g[i - 1]) * rel) if g[i] >= g[i - 1] else g[i]
    return x * g


# ------------------------------------------------------------ the whole --

def master(path: str, room: str = "close", sex: str = "m", kind: str | None = None, seed: int = 7, vol: str = "level") -> np.ndarray:
    """One take, edited and toned, before it is placed and levelled with its line."""
    x = load(path)
    x = clean(x)
    x = edit(x)
    x = tone(x, sex, vol)
    x = fx(x, kind)
    return x


def assemble(parts: list[tuple[np.ndarray, str]], gap: float = 0.38, seed: int = 7, vol: str = "level") -> tuple[np.ndarray, list[list[float]]]:
    """The parts of a line in order, each in its room, the pause between
    them; returns the line and where each part starts and ends (seconds).
    `vol` is the speaker's (the narrator's asides stay at his distance)."""
    out, marks, t = [], [], 0.0
    for i, (x, room) in enumerate(parts):
        y = place(x, room, seed + i, vol if room != "close" else "level")
        if out:
            g = np.zeros(int(gap * SR))
            out.append(g)
            t += gap
        marks.append([round(t, 3), round(t + len(x) / SR, 3)])
        out.append(y)
        t += len(y) / SR
    line = np.concatenate(out)
    # The room tone of the speaker's room runs under the whole line.
    room = parts[-1][1]
    _, _, _, colour, tone_db = ROOMS.get(room, ROOMS["close"])
    rt = room_tone(len(line), colour, tone_db, seed)
    f = int(0.03 * SR)
    rt[:f] *= np.linspace(0, 1, f); rt[-f:] *= np.linspace(1, 0, f)
    return line + rt * np.max(np.abs(line)) / 0.5, marks


def write_ogg(x: np.ndarray, path: str, ffmpeg: str, quality: float = 2.0):
    import librosa
    y = librosa.resample(x.astype(np.float32), orig_sr=SR, target_sr=OUT_SR, res_type="soxr_vhq")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp.wav"
    sf.write(tmp, y, OUT_SR, subtype="PCM_24")
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", tmp, "-c:a", "libvorbis", "-q:a", str(quality), "-ac", "1", path], check=True)
    os.remove(tmp)


def main(argv):
    from common import FFMPEG
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--room", default="close")
    ap.add_argument("--sex", default="m")
    ap.add_argument("--fx")
    ap.add_argument("--lufs", type=float, default=-16.0)
    a = ap.parse_args(argv)
    x = master(a.src, a.room, a.sex, a.fx)
    line, _ = assemble([(x, a.room)])
    line = loudness(line, a.lufs)
    if a.dst.endswith(".wav"):
        sf.write(a.dst, line, SR)
    else:
        write_ogg(line, a.dst, FFMPEG)


if __name__ == "__main__":
    main(sys.argv[1:])
