"""A recipe of Synth.cs voices rendered offline to a WAV, to hear an interface sound before the
game plays it (the game makes its sounds live and saves none). The voices are modelled as
Synth.cs makes them (the exponential envelope and glide, two-operator FM, the RBJ biquads), and
the room as Godot's reverb on the Room bus (Freeverb: room 0.86, damping 0.7, wet 0.8, 20 ms
predelay), fed by each voice's bus send plus its own Verb, folded back as Synth's tape does.

    python tools/uiforge/sfxpreview.py chain_modal [OUT.wav]
    python tools/uiforge/sfxpreview.py ab             # godot/.shots/sfx_chain_{fm,modal}.wav
"""
from __future__ import annotations

import math
import os
import sys
import wave

import numpy as np
from scipy.signal import lfilter

RATE = 44100
UI_SEND = 0.08          # Synth.Send for Bus.Ui


def env(n_rise, n_fall, peak):
    rise = np.linspace(0.0001, peak, max(1, n_rise), endpoint=False)
    k = (0.0001 / max(1e-6, peak)) ** (1.0 / max(1, n_fall))
    fall = peak * k ** np.arange(max(1, n_fall))
    return np.concatenate([rise, fall, np.zeros(int(0.02 * RATE))])


def biquad(x, kind, f, Q=0.707):
    """The RBJ cookbook biquads Synth.cs uses (band, low, high)."""
    w0 = 2 * math.pi * min(f, RATE * 0.45) / RATE
    al = math.sin(w0) / (2 * Q)
    cw = math.cos(w0)
    if kind == "band":
        b, a = [al, 0, -al], [1 + al, -2 * cw, 1 - al]
    elif kind == "low":
        b, a = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2], [1 + al, -2 * cw, 1 - al]
    else:
        b, a = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2], [1 + al, -2 * cw, 1 - al]
    return lfilter(b, a, x)


def fm(F, Ratio, Index, D, G, A=0.002, F2=None):
    e = env(int(A * RATE), int(D * RATE), G)
    n = len(e)
    f = np.full(n, F) if F2 is None else F * (F2 / F) ** (np.arange(n) / n)
    depth = F * Index * (max(1, F * Index * 0.05) / (F * Index)) ** (np.arange(n) / n)
    mod = np.cumsum(np.full(n, F * Ratio / RATE))
    inst = f + depth * np.sin(mod * 2 * math.pi)
    return np.sin(np.cumsum(inst / RATE) * 2 * math.pi) * e


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


class Mix:
    """Voices laid in time, dry and into the room's send."""

    def __init__(self, secs):
        self.dry = np.zeros(int(secs * RATE))
        self.send = np.zeros(int(secs * RATE))

    def put(self, t, s, verb=0.0):
        i = int(max(0, t) * RATE)
        j = min(len(self.dry), i + len(s))
        self.dry[i:j] += s[:j - i]
        self.send[i:j] += s[:j - i] * (UI_SEND + verb)

    def out(self):
        return self.dry + reverb(self.send) * 0.35


def reverb(x, room=0.86, damping=0.7, wet=0.8, predelay=0.02):
    """Freeverb, as Godot's AudioEffectReverb is: eight damped combs in parallel, four allpasses."""
    fb = room * 0.28 + 0.7
    d = damping * 0.4
    x = np.concatenate([np.zeros(int(predelay * RATE)), x])[:len(x)] * 0.015
    y = np.zeros_like(x)
    for M in (1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617):
        a = np.zeros(M + 1)
        a[0], a[1], a[M] = 1.0, -d, -fb * (1 - d)
        y += lfilter([0] * M + [1.0, -d], a, x)
    for M in (556, 441, 341, 225):
        b = np.zeros(M + 1)
        a = np.zeros(M + 1)
        b[0], b[M] = -1.0, 1.5
        a[0], a[M] = 1.0, -0.5
        y = lfilter(b, a, y)
    return y * wet * 3


def spring_times(n, k=1.0):
    """When each of n links crosses the eye as the chain moves on its slide spring (130, 17),
    fitted: slow off the mark, quickest early, easing to the stop at 0.29 s."""
    return [k * (0.025 + 0.2 * u + 0.04 * u * u) for u in ((i + 0.5) / n for i in range(n))]


def chain_fm(links=6, secs=0.32, seed=3):
    """Sfx.ChainSlide as it was (FM), for the A/B."""
    rng = np.random.default_rng(seed)

    def R(a, b):
        return rng.uniform(a, b)
    k = secs / 0.32
    m = Mix(secs + 2.6)
    n = max(2, min(14, links))
    for i, t in enumerate(spring_times(n, k)):
        u = (i + 0.5) / n
        g = (1.0 - 0.4 * u) * R(0.8, 1.15)
        m.put(t, fm(R(700, 1300), R(1.4, 2.6), R(3, 5), R(0.07, 0.13), 0.035 * g), 0.15)
        f = R(150, 230)
        m.put(t, tone(f, 0.05, 0.025 * g, F2=f * 0.8, Lp=500))
    m.put(0.02 * k, hiss(0.26 * k, 0.035, A=0.05, Lp=900, brown=True, rng=rng))
    stop = 0.29 * k
    m.put(stop, tone(92, 0.25, 0.09, F2=68, Lp=380))
    m.put(stop, fm(R(380, 440), 1.41, 4, 0.32, 0.05), 0.3)
    m.put(stop, hiss(0.07, 0.04, Bp=700, Q=1, rng=rng))
    m.put(stop + 0.17, fm(R(1300, 1600), 2.76, 2.8, 0.14, 0.022), 0.25)
    m.put(stop + 0.42, fm(R(1500, 1800), 3.1, 2.2, 0.1, 0.01), 0.25)
    m.put(stop - 0.05, hiss(0.7, 0.014, A=0.18, Hp=4500, rng=rng))
    return m.out()


# Iron rings' bending modes: n(n^2-1)/sqrt(n^2+1) for n = 2..5, relative to the first (1, 2.83,
# 5.42, 8.77); a chain link is a stretched ring, so each mode splits in two close partials.
RING = [1.0, 2.83, 5.42, 8.77]


def strike(m, t, f0, g, rng, decay=0.13, verb=0.12, body=True):
    """One link struck: its ring's partials (each split, detuned and decaying on its own, the
    higher ones faster), a tick of contact, and a little low body under it."""
    for j, r in enumerate(RING):
        for split in (-1, 1):
            f = f0 * r * (1 + split * rng.uniform(0.003, 0.009)) * (1 + rng.uniform(-0.01, 0.01))
            if f > 15000:
                continue
            amp = g * (0.9 ** j) * (1.0 if j else 1.15) * rng.uniform(0.7, 1.1) * 0.5
            d = decay / (1 + 1.2 * j) * rng.uniform(0.75, 1.25)
            m.put(t, tone(f, d, amp, A=0.0006), verb)
    m.put(t, hiss(rng.uniform(0.004, 0.008), g * 1.3, A=0.0004, Bp=f0 * rng.uniform(4, 7), Q=0.9, rng=rng))
    if body:
        fb = rng.uniform(120, 165)
        m.put(t, tone(fb, rng.uniform(0.07, 0.1), g * 0.55, F2=fb * 0.85, A=0.002, Lp=400))


def chain_modal(links=6, secs=0.32, seed=3):
    """Sfx.ChainSlide, modal: each passing link a struck iron ring (tuned from a ring's own
    inharmonic modes, every link its own pitch and ring), timed to the slide spring; a bed of
    scrape grains as iron drags over iron, thicker while it runs fastest; at the stop a
    sub-thump and a heavy ring of the whole chain settling, a chink as it settles and a softer
    one as it swings back; the hiss of the links taking the heat."""
    rng = np.random.default_rng(seed)

    def R(a, b):
        return rng.uniform(a, b)
    k = secs / 0.32
    m = Mix(secs + 2.6)
    n = max(2, min(14, links))
    times = spring_times(n, k)
    for i, t in enumerate(times):
        u = (i + 0.5) / n
        strike(m, t + R(-0.004, 0.004), R(420, 640), 0.03 * (1.0 - 0.35 * u) * R(0.8, 1.15), rng)
        # Links knock their neighbours a beat later, softer and higher.
        if rng.random() < 0.5:
            strike(m, t + R(0.012, 0.03), R(600, 900), 0.012 * R(0.7, 1.1), rng, decay=0.08, body=False)
    # The drag: grains of iron on iron, densest where the chain runs fastest.
    end = 0.29 * k
    t = 0.02 * k
    while t < end:
        speed = max(0.15, math.sin(min(1, t / end) * math.pi) ** 0.7)
        m.put(t, hiss(R(0.006, 0.018), 0.022 * speed * R(0.5, 1.1), A=0.001, Bp=R(1200, 3600), Q=R(2, 5), rng=rng))
        t += R(0.008, 0.02) / speed
    stop = end
    # The stop: a sub-thump through the band, the chain's whole weight ringing low, then the settle.
    m.put(stop, tone(62, 0.22, 0.12, F2=44, A=0.003, Lp=160))
    m.put(stop, hiss(0.06, 0.05, A=0.002, Lp=300, brown=True, rng=rng))
    strike(m, stop, R(300, 360), 0.05, rng, decay=0.45, verb=0.28)
    strike(m, stop + 0.006, R(430, 520), 0.03, rng, decay=0.3, verb=0.28, body=False)
    strike(m, stop + 0.17, R(640, 760), 0.02, rng, decay=0.25, verb=0.25, body=False)
    strike(m, stop + 0.42, R(700, 860), 0.01, rng, decay=0.2, verb=0.25, body=False)
    # The heat: a sizzle of tiny pops as the new links take it, dying away.
    t = stop - 0.05
    while t < stop + 0.65:
        f = 1 - (t - stop + 0.05) / 0.7
        m.put(t, hiss(R(0.002, 0.005), 0.012 * f * R(0.4, 1.0), A=0.0003, Hp=R(4500, 7000), rng=rng))
        t += R(0.01, 0.045)
    return m.out()


def save(x, path, peak=0.7):
    """Mono 16-bit, normalised to a hearing level (the game's buses and compressor lift it too)."""
    y = x * (peak / max(1e-6, np.abs(x).max()))
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())


SHOTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "godot", ".shots")
RECIPES = {"chain_fm": chain_fm, "chain_modal": chain_modal, "chain": chain_modal}

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "chain"
    if what == "ab":
        for k in ("chain_fm", "chain_modal"):
            p = os.path.join(SHOTS, f"sfx_{k}.wav")
            save(RECIPES[k](), p)
            print(p)
    else:
        out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(SHOTS, f"sfx_{what}.wav")
        save(RECIPES[what](), out)
        print(out)
