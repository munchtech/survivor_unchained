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


def biquad(x, kind, f, Q=0.707):
    """The RBJ cookbook biquads Synth.cs uses (band, low, high)."""
    from scipy.signal import lfilter
    w0 = 2 * math.pi * f / RATE
    al = math.sin(w0) / (2 * Q)
    cw = math.cos(w0)
    if kind == "band":
        b, a = [al, 0, -al], [1 + al, -2 * cw, 1 - al]
    elif kind == "low":
        b, a = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2], [1 + al, -2 * cw, 1 - al]
    else:
        b, a = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2], [1 + al, -2 * cw, 1 - al]
    return lfilter(b, a, x)


def hiss(D, G, A=0.003, Bp=None, Q=1.0, Lp=None, Hp=None, brown=False, rng=None):
    e = env(int(A * RATE), int(D * RATE), G)
    x = (rng or np.random.default_rng(0)).standard_normal(len(e)) * 0.35
    if brown:
        x = np.cumsum(x) * 0.02
        x = x - np.convolve(x, np.ones(512) / 512, mode="same")
    if Bp:
        x = biquad(x, "band", Bp, Q)
    if Lp:
        x = biquad(x, "low", Lp)
    if Hp:
        x = biquad(x, "high", Hp)
    return x * e


def tone(F, D, G, F2=None, A=0.002, Lp=None):
    """A sine through an envelope, gliding from F to F2, low-passed if asked."""
    e = env(int(A * RATE), int(D * RATE), G)
    n = len(e)
    f = np.full(n, F) if F2 is None else F * (F2 / F) ** (np.arange(n) / n)
    x = np.sin(np.cumsum(f / RATE) * 2 * math.pi)
    if Lp:
        x = biquad(x, "low", Lp)
    return x * e


def chain(links=6, secs=0.32, seed=3):
    """Sfx.ChainSlide, as Sfx.cs plays it."""
    rng = np.random.default_rng(seed)

    def R(a, b):
        return rng.uniform(a, b)
    k = secs / 0.32
    out = np.zeros(int((secs + 1.4) * RATE))

    def put(t, s):
        i = int(max(0, t) * RATE)
        j = min(len(out), i + len(s))
        out[i:j] += s[:j - i]
    n = max(2, min(14, links))
    for i in range(n):
        u = (i + 0.5) / n
        t = k * (0.025 + 0.2 * u + 0.04 * u * u) + R(-0.004, 0.004)
        g = (1.0 - 0.4 * u) * R(0.8, 1.15)
        put(t, fm(R(700, 1300), R(1.4, 2.6), R(3, 5), R(0.07, 0.13), 0.035 * g))
        f = R(150, 230)
        put(t, tone(f, 0.05, 0.025 * g, F2=f * 0.8, Lp=500))
    put(0.02 * k, hiss(0.26 * k, 0.035, A=0.05, Lp=900, brown=True, rng=rng))
    stop = 0.29 * k
    put(stop, tone(92, 0.25, 0.09, F2=68, Lp=380))
    put(stop, fm(R(380, 440), 1.41, 4, 0.32, 0.05))
    put(stop, hiss(0.07, 0.04, Bp=700, Q=1, rng=rng))
    put(stop + 0.17, fm(R(1300, 1600), 2.76, 2.8, 0.14, 0.022))
    put(stop + 0.42, fm(R(1500, 1800), 3.1, 2.2, 0.1, 0.01))
    put(stop - 0.05, hiss(0.7, 0.014, A=0.18, Hp=4500, rng=rng))
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
