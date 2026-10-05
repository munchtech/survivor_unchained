"""A recipe of Synth.cs voices rendered offline to a WAV, to hear an interface sound before the
game plays it (the game makes its sounds live and saves none). Fm and Hiss are modelled as
Synth.cs makes them: the exponential envelope and glide, the two-operator FM, the biquad
band-pass. No reverb.

    python tools/uiforge/sfxpreview.py chain [OUT.wav]
"""
from __future__ import annotations

import math
import os
import sys
import wave

import numpy as np

RATE = 44100


def env(n_rise, n_fall, peak):
    rise = np.linspace(0.0001, peak, max(1, n_rise), endpoint=False)
    k = (0.0001 / max(1e-6, peak)) ** (1.0 / max(1, n_fall))
    fall = peak * k ** np.arange(max(1, n_fall))
    return np.concatenate([rise, fall, np.zeros(int(0.02 * RATE))])


def fm(F, Ratio, Index, D, G, A=0.002, F2=None):
    e = env(int(A * RATE), int(D * RATE), G)
    n = len(e)
    span = n
    f = np.full(n, F) if F2 is None else F * (F2 / F) ** (np.arange(n) / span)
    depth = F * Index * (max(1, F * Index * 0.05) / (F * Index)) ** (np.arange(n) / span)
    mod = np.cumsum(np.full(n, F * Ratio / RATE))
    inst = f + depth * np.sin(mod * 2 * math.pi)
    car = np.cumsum(inst / RATE)
    return np.sin(car * 2 * math.pi) * e


def hiss(D, G, A=0.003, Bp=None, Q=1.0, rng=None):
    from scipy.signal import lfilter
    e = env(int(A * RATE), int(D * RATE), G)
    x = (rng or np.random.default_rng(0)).standard_normal(len(e)) * 0.35
    if Bp:
        w0 = 2 * math.pi * Bp / RATE
        al = math.sin(w0) / (2 * Q)
        b = [al, 0, -al]
        a = [1 + al, -2 * math.cos(w0), 1 - al]
        x = lfilter(b, a, x)
    return x * e


def chain(links=6, secs=0.32, seed=3):
    """Sfx.ChainSlide, as Sfx.cs plays it."""
    rng = np.random.default_rng(seed)

    def R(a, b):
        return rng.uniform(a, b)
    out = np.zeros(int((secs + 0.6) * RATE))

    def put(t, s):
        i = int(t * RATE)
        j = min(len(out), i + len(s))
        out[i:j] += s[:j - i]
    n = max(2, min(12, links))
    for i in range(n):
        u = (i + 0.5) / n
        t = secs * 0.7 * (1 - (1 - u) ** (1 / 3)) + R(-0.004, 0.004)
        g = 0.022 * (1.0 - 0.45 * u) * R(0.75, 1.15)
        put(max(0, t), fm(R(2200, 3400), R(2.7, 3.6), R(2.4, 3.4), R(0.03, 0.06), g))
    put(0, hiss(secs * 0.9, 0.012, A=0.02, Bp=4200, Q=1.4, rng=rng))
    put(secs * 0.8, fm(R(1500, 1800), 2.92, 3.2, 0.16, 0.03))
    put(secs * 0.8 + 0.15, fm(R(1900, 2300), 3.27, 2.4, 0.08, 0.012))
    return out


def save(x, path, gain=6.0):
    """Mono 16-bit, raised to a hearing level (the game's buses and compressor lift it too)."""
    y = np.clip(x * gain, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((y * 32767).astype(np.int16).tobytes())


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "chain"
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "godot", ".shots", f"sfx_{what}.wav")
    save({"chain": chain}[what](), out)
    print(out)
