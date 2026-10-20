"""SB00's sound effects. Two kinds:

- ports of the game's own synthesized sounds (godot/src/Audio/Sfx.cs and
  Synth.cs: Tone, Hiss, Fm, Clip voices; the Cine presets frost_crack, rasp,
  drip, owl, water_close, hit, groan, kneel_water; Heartbeat; the ember
  pickup Xp; Pour; Anvil), so the storybook's family matches the game's;
- new sounds made the same way (noise, oscillators, the game's recordings)
  for what the game has no sound for yet: wind, a striker, a stone door,
  bubbles under water, birds.

Each generator takes (params, rng, length in seconds) and returns
(stereo dry, stereo room send) at 48 kHz.
"""
import glob
import os
import numpy as np
import dsp
from dsp import SR, filt, tvfilt, env_game, glide, db

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SOUND = os.path.join(ROOT, "godot", "art", "sound")


def _n(s):
    return int(round(s * SR))


class Mix:
    """A little stereo bus a generator plays its voices into, with a room send,
    as Synth.cs's dry mix and its send to the room."""

    def __init__(self, length):
        self.n = _n(length)
        self.dry = np.zeros((self.n, 2))
        self.wet = np.zeros((self.n, 2))

    def add(self, x, t=0.0, pan=0.0, verb=0.0, g=1.0):
        s = _n(t)
        if s >= self.n or len(x) == 0:
            return
        if s < 0:
            x = x[-s:]
            s = 0
        e = min(self.n, s + len(x))
        x = x[: e - s] * g
        if x.ndim == 1:
            l, r = dsp.pan_gains(pan)
            x = np.stack([x * l, x * r], axis=1)
        self.dry[s:e] += x
        if verb:
            self.wet[s:e] += x * verb

    def out(self):
        return self.dry, self.wet


# ------------------------------------------------------ Synth.cs voices ---

def _osc(kind, ph):
    p = ph - np.floor(ph)
    if kind == "tri":
        return 4 * np.abs(p - 0.5) - 1
    if kind == "square":
        return np.where(p < 0.5, 1.0, -1.0)
    if kind == "saw":
        return 2 * p - 1
    return np.sin(p * 2 * np.pi)


def tone(F, D, G, A=0.005, Hold=0.0, F2=None, Glide=None, Type="sine", Lp=None, Lp2=None, Q=None, Hp=None, Detune=0.0, **_):
    """Synth.cs ToneVoice."""
    n = _n(A + Hold + D + 0.02)
    env = env_game(_n(A), _n(Hold), _n(D), G, n)
    f = glide(F, F2, n, _n(Glide if Glide is not None else A + D))
    ph = np.cumsum(f * 2 ** (Detune / 1200)) / SR
    x = _osc(Type, ph)
    if Lp is not None:
        q = max(0.5, 10 ** (Q / 20) * 0.707) if Q is not None else 0.707
        x = tvfilt(x, "lp", glide(Lp, Lp2, n), q, block=32)
    if Hp is not None:
        x = filt(x, "hp", Hp)
    return x * env


def hiss(D, G, rng, A=0.003, Bp=None, Bp2=None, Q=1.0, Lp=None, Lp2=None, Hp=None, Brown=False, **_):
    """Synth.cs NoiseVoice."""
    n = _n(A + D + 0.02)
    env = env_game(_n(A), 0, _n(D), G, n)
    x = dsp.brown(rng, n) if Brown else dsp.white(rng, n)
    if Bp is not None:
        x = tvfilt(x, "bp", glide(Bp, Bp2, n), Q or 1.0, block=32)
    if Lp is not None:
        x = tvfilt(x, "lp", glide(Lp, Lp2, n), 0.707, block=32)
    if Hp is not None:
        x = filt(x, "hp", Hp)
    return x * env


def fm(F, Ratio, Index, D, G, A=0.002, F2=None, **_):
    """Synth.cs FmVoice: the modulator's depth falls to 5% over the voice."""
    n = _n(A + D + 0.02)
    env = env_game(_n(A), 0, _n(D), G, n)
    f = glide(F, F2, n)
    depth = glide(F * Index, max(1, F * Index * 0.05), n)
    mod = np.sin(2 * np.pi * np.cumsum(np.full(n, F * Ratio)) / SR)
    car = np.cumsum(f + depth * mod) / SR
    return np.sin(2 * np.pi * car) * env


def takes(family):
    """The game's recordings of one family (godot/art/sound/<family>_<i>.wav)."""
    return sorted(glob.glob(os.path.join(SOUND, f"{family}_[0-9]*.wav")))


def clip(Of, G, rng, Pitch=1.0, Lp=None, take=None, **_):
    """Synth.cs ClipVoice: a take of the family, varispeed, a low-pass if asked."""
    files = takes(Of)
    f = files[take if take is not None else int(rng.integers(len(files)))]
    x = dsp.repitch(dsp.load_wav(f), Pitch)
    if Lp is not None:
        x = filt(x, "lp", Lp)
    return x * G


def R(rng, a, b):
    return float(rng.uniform(a, b))


def play(m, rng, kind, T=0.0, Pan=0.0, Verb=0.0, **o):
    """One Synth.cs voice into a Mix at time T."""
    if kind == "tone":
        x = tone(**o)
    elif kind == "hiss":
        x = hiss(rng=rng, **o)
    elif kind == "fm":
        x = fm(**o)
    else:
        x = clip(rng=rng, **o)
    m.add(x, T, Pan, Verb)


# ------------------------------------------------------------ the ports ---

def cine(p, rng, length):
    """Sfx.Cine(name, gain, pan), ported preset by preset."""
    m = Mix(length)
    g = p.get("g", 1.0)
    pan = p.get("pan", 0.0)
    name = p["name"]
    if name == "water_close":
        play(m, rng, "hiss", 0, A=0.04, D=1.6, G=0.32 * g, Lp=520, Lp2=110, Brown=True)
        play(m, rng, "tone", 0, F=58, F2=34, D=1.3, G=0.42 * g)
        bt = 0.12
        for i in range(9):
            bt += R(rng, 0.06, 0.14)
            play(m, rng, "tone", bt, F=R(rng, 260, 420), F2=R(rng, 700, 1100), D=R(rng, 0.04, 0.08),
                 G=0.035 * g * (1 - i / 11.0), Lp=1400, Pan=R(rng, -0.3, 0.3))
    elif name == "drip":
        play(m, rng, "tone", 0, F=R(rng, 1250, 1500), F2=R(rng, 520, 640), D=0.09, G=0.11 * g, Verb=0.35, Pan=pan)
        play(m, rng, "tone", 0.004, F=2700, F2=1800, D=0.03, G=0.04 * g, Pan=pan)
    elif name == "owl":
        for dt, f in [(0.0, 392.0), (0.62, 349.0), (0.9, 349.0)]:
            play(m, rng, "tone", dt, F=f, F2=f * 0.94, Type="tri", A=0.06, D=0.34, G=0.045 * g, Lp=900, Verb=0.8, Pan=pan)
    elif name == "frost_crack":
        t = 0.0
        for i in range(14):
            t += R(rng, 0.03, 0.07)
            play(m, rng, "hiss", t, D=R(rng, 0.02, 0.05), G=R(rng, 0.05, 0.11) * g, Bp=R(rng, 1800, 4200), Q=4,
                 Pan=pan + R(rng, -0.15, 0.15))
        play(m, rng, "tone", 0.55, F=46, F2=28, D=1.1, G=0.5 * g)
        play(m, rng, "hiss", 0.55, D=0.9, G=0.18 * g, Lp=260, Lp2=90, Brown=True)
    elif name == "rasp":
        play(m, rng, "hiss", 0, A=0.35, D=1.2, G=0.07 * g, Bp=850, Bp2=600, Q=1.6, Brown=True, Pan=pan)
    elif name == "breath_out":
        play(m, rng, "hiss", 0, A=0.25, D=1.4, G=0.05 * g, Bp=1500, Bp2=900, Q=0.9, Pan=pan)
    elif name == "hit":
        play(m, rng, "tone", 0, F=62, F2=33, D=1.5, G=0.55 * g)
        play(m, rng, "hiss", 0, D=0.5, G=0.2 * g, Lp=400, Lp2=100, Brown=True)
        play(m, rng, "hiss", 0.02, A=0.05, D=0.9, G=0.06 * g, Bp=3400, Bp2=2600, Q=7, Verb=0.5)
    elif name == "groan":
        play(m, rng, "tone", 0, F=31, F2=27, A=1.0, Hold=1.6, D=1.4, G=0.5 * g)
        play(m, rng, "tone", 0.6, F=52, F2=44, Type="saw", A=0.8, Hold=1.4, D=1.2, G=0.06 * g, Lp=320, Lp2=180, Verb=0.5)
        play(m, rng, "hiss", 0.4, A=1.0, D=2.0, G=0.06 * g, Lp=220, Lp2=90, Brown=True)
    elif name == "kneel_water":
        play(m, rng, "tone", 0, F=90, F2=46, D=0.5, G=0.32 * g, Pan=pan)
        play(m, rng, "hiss", 0, A=0.01, D=0.7, G=0.13 * g, Bp=1200, Bp2=500, Q=0.8, Pan=pan)
    elif name == "cloth_water":
        play(m, rng, "hiss", 0, A=0.05, D=0.9, G=0.06 * g, Bp=2400, Q=0.7, Pan=pan)
        t = 0.2
        for i in range(4):
            play(m, rng, "tone", t, F=R(rng, 1100, 1500), F2=R(rng, 500, 700), D=0.07, G=0.05 * g, Verb=0.3, Pan=pan)
            t += R(rng, 0.12, 0.2)
    else:
        raise ValueError(name)
    return m.out()


def heartbeat(p, rng, length):
    """Sfx.Heartbeat at each time in p['beats'] (seconds), each a little weaker
    and duller: the slowing heart under water. A brown thump under the game's
    two tones so it is felt on small speakers too."""
    m = Mix(length)
    beats = p["beats"]
    for i, (t, u) in enumerate(beats):
        g = 0.05 + 0.06 * u
        lp = 220 * (0.75 + 0.25 * u)
        play(m, rng, "tone", t, F=58, F2=42, D=0.16, G=g, Lp=lp)
        play(m, rng, "tone", t + p.get("gap", 0.24) * (1 + 0.2 * (1 - u)), F=52, F2=38, D=0.2, G=g * 0.75, Lp=lp * 0.9)
        play(m, rng, "hiss", t, A=0.01, D=0.18, G=g * 0.6, Lp=140, Brown=True)
    return m.out()


LADDER = [0, 3, 5, 7, 10, 12, 15, 17, 19, 22, 24]


def ember_spill(p, rng, length):
    """The light pouring out of the body onto the frost: the ember pickup's
    voice (Sfx.Xp: an FM chime on D6's minor-pentatonic ladder, with a tone
    under it) scattered as stones land, high to low, thinning, with a soft
    glass settle and a breath of bright hiss as it pours."""
    m = Mix(length)
    k = p.get("count", 13)
    t = 0.0
    for i in range(k):
        step = LADDER[max(0, min(len(LADDER) - 1, int(len(LADDER) - 1 - i * 0.7 + R(rng, -1.5, 1.5))))]
        f = 1174.66 * 2 ** (step / 12)
        g = 0.036 * (1 - i / (k + 3)) * p.get("g", 1.0)
        pan = R(rng, -0.5, 0.5)
        play(m, rng, "fm", t, F=f, Ratio=3.0, Index=0.3, A=0.002, D=0.09 + 0.05 * (i / k), G=g, Pan=pan, Verb=0.35)
        play(m, rng, "tone", t, F=f, A=0.002, D=0.09, G=g * 0.5, Detune=7, Pan=pan)
        t += R(rng, 0.03, 0.09) * (1 + i / k)
    play(m, rng, "hiss", 0.0, A=0.08, D=0.9, G=0.025 * p.get("g", 1.0), Bp=6000, Bp2=2500, Q=0.9, Verb=0.3)
    for i in range(4):
        play(m, rng, "clip", 0.15 + i * R(rng, 0.08, 0.16), Of="impactGlass_light", G=0.05 * p.get("g", 1.0),
             Pitch=R(rng, 1.4, 1.8), Lp=6000, Pan=R(rng, -0.4, 0.4))
    return m.out()


def anvil(p, rng, length):
    """Sfx.Anvil: the recorded hammer, a heavy metal impact under it and a
    struck FM shimmer, at each time in p['blows']."""
    m = Mix(length)
    for i, t in enumerate(p["blows"]):
        play(m, rng, "clip", t, Of="anvil", G=0.42, Pitch=R(rng, 0.97, 1.03) - 0.06 * p.get("down", 1), Verb=0.3)
        play(m, rng, "clip", t, Of="impactMetal_heavy", G=0.16, Pitch=R(rng, 0.85, 0.95), Verb=0.25)
        play(m, rng, "fm", t, F=1320 * R(rng, 0.98, 1.02), Ratio=2.76, Index=1.4, D=1.1, G=0.025, Verb=0.6)
        for j in range(5):  # sparks off the link
            play(m, rng, "hiss", t + 0.01 + j * R(rng, 0.01, 0.04), D=R(rng, 0.01, 0.03), G=R(rng, 0.01, 0.03),
                 Bp=R(rng, 5000, 9000), Q=3, Pan=R(rng, -0.3, 0.3), Verb=0.2)
    return m.out()


def pour(p, rng, length):
    """Sfx.Pour stretched into oil glugging from a jug into a lamp: the
    game's pour hiss, and its little rising tones slowed into glugs."""
    m = Mix(length)
    d = p.get("dur", 1.6)
    play(m, rng, "hiss", 0.02, A=0.1, D=d, G=0.035, Bp=1100, Bp2=650, Q=3, Verb=0.2)
    t = 0.05
    while t < d:
        f0 = R(rng, 180, 260)
        play(m, rng, "tone", t, F=f0, F2=f0 * R(rng, 1.6, 2.2), A=0.006, D=R(rng, 0.06, 0.1), G=0.05, Lp=900, Verb=0.25)
        t += R(rng, 0.12, 0.22)
    return m.out()


# ---------------------------------------------------- recordings, looped ---

def rec(p, rng, length):
    """A recording: looped (beds) or once (a take), varispeed, offset into it."""
    n = _n(length)
    if "family" in p:
        x = clip(p["family"], 1.0, rng, p.get("pitch", 1.0), take=p.get("take"))
    else:
        x = dsp.repitch(dsp.load_wav(os.path.join(ROOT, p["file"])), p.get("pitch", 1.0))
    if p.get("loop"):
        y = dsp.loop_to(x, n, _n(p.get("offset", 0.0)))
        if p.get("stereo", True):
            # the right side half a take along, as the game plays its beds wide
            y2 = dsp.loop_to(x, n, _n(p.get("offset", 0.0)) + len(x) // 2)
            return np.stack([y, y2], axis=1), None
        return y, None
    x = x[_n(p.get("offset", 0.0)):]
    return x[:n], None


# ----------------------------------------------------------- new sounds ---

def wind(p, rng, length):
    """Wind over hills: brown and pink noise through a band that wanders, in
    slow gusts; the two sides drawn apart so it surrounds."""
    n = _n(length)
    out = np.zeros((n, 2))
    t = np.arange(n) / SR
    for side in range(2):
        x = dsp.brown(rng, n) * 0.6 + dsp.pink(rng, n) * 0.4
        wander = np.cumsum(rng.standard_normal(n // 2400 + 2))
        wander = np.interp(np.arange(n), np.arange(len(wander)) * 2400, wander)
        wander = (wander - wander.mean()) / (np.std(wander) + 1e-9)
        fc = p.get("f", 500) * 2 ** (0.6 * wander)
        y = tvfilt(x, "bp", fc, p.get("q", 0.9), block=256)
        gust = 0.6 + 0.4 * np.clip(0.5 + 0.5 * wander, 0, 1)
        out[:, side] = y * gust
    if p.get("whistle", 0) > 0:  # cold air over an edge: a thin moving whistle
        w = tvfilt(dsp.white(rng, n), "bp", p.get("whistle_f", 1600) * (1 + 0.15 * np.sin(2 * np.pi * 0.09 * t)), 25, block=256)
        out += np.stack([w, w * 0.6], axis=1) * p["whistle"]
    return out * 2.0, None


def striker(p, rng, length):
    """Flint on steel, twice, at a stone window: a small metal tick, a spray
    of sparks; then the wick takes (a soft rush of air, a few crackles) and a
    small flame flutters."""
    m = Mix(length)
    for i, t in enumerate(p.get("strikes", [0.0, 0.32])):
        play(m, rng, "clip", t, Of="impactMetal_light", G=0.22, Pitch=R(rng, 1.7, 2.0), Lp=9000)
        play(m, rng, "hiss", t, A=0.001, D=0.09, G=0.05, Hp=4500)
        for j in range(6):
            play(m, rng, "hiss", t + 0.01 + j * R(rng, 0.006, 0.02), D=R(rng, 0.005, 0.015), G=R(rng, 0.02, 0.05),
                 Bp=R(rng, 6000, 10000), Q=4, Pan=R(rng, -0.2, 0.2))
    tc = p.get("catch", 0.5)
    play(m, rng, "hiss", tc, A=0.12, D=0.55, G=0.10, Lp=300, Lp2=1800, Brown=True)
    for j in range(5):
        play(m, rng, "hiss", tc + 0.1 + j * R(rng, 0.05, 0.15), D=0.01, G=R(rng, 0.03, 0.06), Bp=R(rng, 2000, 4500), Q=2)
    # the flame after: a steady soft flutter
    n0 = _n(tc + 0.2)
    if n0 < m.n:
        L = m.n - n0
        fl = filt(dsp.brown(rng, L), "bp", 420, 0.8)
        am = 0.7 + 0.3 * dsp.onepole_lp(rng.standard_normal(L), 8) * 6
        fade = np.minimum(1, np.arange(L) / (0.4 * SR))
        m.add(fl * am * fade * p.get("flame", 0.12), tc + 0.2)
    return m.out()


def flame(p, rng, length):
    """A lamp flame: a soft low flutter; 'gutter' makes it catch and sag."""
    n = _n(length)
    x = filt(dsp.brown(rng, n), "bp", p.get("f", 380), 0.8)
    am = 0.7 + 0.3 * np.tanh(dsp.onepole_lp(rng.standard_normal(n), p.get("rate", 8)) * 6)
    if p.get("gutter"):
        drops = dsp.onepole_lp((rng.random(n) < 2.0 / SR).astype(float) * SR * 0.02, 3)
        am *= np.clip(1 - drops, 0.15, 1)
        tick = (rng.random(n) < 3.0 / SR).astype(float)
        x += filt(tick, "bp", 2500, 2) * 0.6
    return x * am, None


def march(p, rng, length):
    """The Legion's column far off: many boots at a march, out of step with
    each other, and the clink of kit, as from across a valley."""
    m = Mix(length)
    beat = p.get("beat", 0.58)
    for s in range(p.get("men", 9)):
        t = R(rng, 0, beat)
        pan = R(rng, -0.7, 0.7)
        g = R(rng, 0.5, 1.0)
        while t < length - 0.5:
            play(m, rng, "clip", t, Of="footstep_dirt", G=0.3 * g, Pitch=R(rng, 0.75, 0.9), Pan=pan)
            if rng.random() < 0.35:
                play(m, rng, "clip", t + R(rng, 0.0, 0.08), Of="chainLink", G=0.05 * g, Pitch=R(rng, 0.8, 1.1), Pan=pan)
            if rng.random() < 0.15:
                play(m, rng, "clip", t + R(rng, 0.0, 0.1), Of="impactPlate_medium", G=0.06 * g, Pitch=R(rng, 0.9, 1.2), Pan=pan)
            t += beat * R(rng, 0.97, 1.03)
    return m.out()


def deep_breath(p, rng, length):
    """The sleeper under the hill: one slow breath, felt more than heard: a sub
    swell under dark air, in and out (the game's 'groan' slowed and softened)."""
    m = Mix(length)
    d = p.get("dur", 4.0)
    play(m, rng, "tone", 0, F=33, F2=29, A=d * 0.45, Hold=0.2, D=d * 0.5, G=0.5)
    play(m, rng, "tone", 0.2, F=49, F2=44, Type="saw", A=d * 0.4, Hold=0.2, D=d * 0.5, G=0.035, Lp=200, Lp2=120, Verb=0.4)
    play(m, rng, "hiss", 0, A=d * 0.45, D=d * 0.55, G=0.08, Lp=180, Lp2=80, Brown=True, Verb=0.3)
    return m.out()


def stone_door(p, rng, length):
    """A stone door closing on a chain: grinding stone (rough dark noise
    rubbed slower and lower as it goes), the chain dragged in with it, and
    the close landing as one low hit (Cine 'hit') with a dull stone thud."""
    m = Mix(length)
    d = p.get("dur", 3.4)
    n = _n(d)
    x = dsp.brown(rng, n) * 0.7 + dsp.white(rng, n) * 0.1
    rough = np.abs(dsp.onepole_lp(rng.standard_normal(n), 25)) * 12
    fc = np.linspace(380, 160, n)
    y = tvfilt(x, "bp", fc, 1.4, block=128) * np.clip(rough, 0, 2) * np.minimum(1, np.arange(n) / (0.8 * SR))
    m.add(y * 0.5, 0, 0, 0.3)
    play(m, rng, "clip", 0.4, Of="chainDrag", G=0.18, Pitch=0.6, Lp=2500, Verb=0.3)
    play(m, rng, "clip", 1.6, Of="chainDrag", G=0.14, Pitch=0.55, Lp=2000, Verb=0.3)
    th = d
    sub = cine({"name": "hit", "g": p.get("hit", 1.0)}, rng, 3.0)
    m.add(sub[0], th, verb=0)
    m.add(sub[1], th, verb=1.0)
    play(m, rng, "clip", th, Of="impactMining", G=0.35, Pitch=0.45, Lp=1200, Verb=0.6)
    play(m, rng, "clip", th, Of="impactWood_heavy", G=0.3, Pitch=0.5, Lp=900, Verb=0.5)
    return m.out()


def motes(p, rng, length):
    """Ember rising through rock: a faint crystalline hiss climbing, and now
    and then a tiny chime from the pickup's ladder, far up and soft."""
    m = Mix(length)
    d = p.get("dur", 6.0)
    play(m, rng, "hiss", 0, A=d * 0.4, D=d * 0.6, G=0.03, Bp=4500, Bp2=9500, Q=2.5, Verb=0.4)
    play(m, rng, "hiss", 0.3, A=d * 0.4, D=d * 0.6, G=0.02, Bp=7000, Bp2=12000, Q=4, Verb=0.4, Pan=0.3)
    t = 0.3
    i = 0
    while t < d:
        step = LADDER[min(len(LADDER) - 1, int(i * 0.8) % len(LADDER))]
        f = 1174.66 * 2 ** (step / 12) * 2
        play(m, rng, "fm", t, F=f, Ratio=3.0, Index=0.25, D=0.12, G=0.009, Pan=R(rng, -0.6, 0.6), Verb=0.6)
        t += R(rng, 0.25, 0.6)
        i += 1
    return m.out()


def town(p, rng, length):
    """The town, small and warm and far: a door, coins in a palm, a cart going
    by on the road (a wheel's creak and its rumble, a horse's slow steps)."""
    m = Mix(length)
    play(m, rng, "clip", p.get("door", 0.0), Of="doorOpen", G=0.25, Pitch=0.9, Lp=4000, Verb=0.3, Pan=-0.4)
    play(m, rng, "clip", p.get("door", 0.0) + 1.1, Of="doorClose", G=0.18, Pitch=0.9, Lp=3500, Verb=0.3, Pan=-0.4)
    play(m, rng, "clip", p.get("coins", 1.5), Of="handleCoins", G=0.4, Lp=7000, Verb=0.2, Pan=0.1)
    tc = p.get("cart", 3.0)
    dc = p.get("cart_dur", 5.0)
    n = _n(dc)
    rum = filt(dsp.brown(rng, n), "lp", 160) * np.sin(np.linspace(0, np.pi, n)) ** 2
    m.add(rum * 0.5, tc, 0.2, 0.2)
    t = tc + 0.3
    while t < tc + dc - 0.4:
        play(m, rng, "clip", t, Of="creak", G=0.06, Pitch=R(rng, 0.8, 1.0), Lp=3000, Pan=0.3, Verb=0.3)
        t += R(rng, 0.9, 1.3)
    t = tc + 0.2
    while t < tc + dc - 0.3:
        play(m, rng, "clip", t, Of="footstep_dirt", G=0.12, Pitch=R(rng, 0.6, 0.7), Lp=2500, Pan=0.25, Verb=0.25)
        t += 0.62 * R(rng, 0.95, 1.05)
    return m.out()


def spear(p, rng, length):
    """The Watchman's spear: a short push of air, the point going in (a heavy
    punch on something soft), the shaft's wood creaking under it."""
    m = Mix(length)
    play(m, rng, "hiss", 0, A=0.06, D=0.18, G=0.06, Bp=900, Bp2=2400, Q=1.4)
    play(m, rng, "clip", 0.2, Of="impactPunch_heavy", G=0.35, Pitch=0.85)
    play(m, rng, "clip", 0.21, Of="impactSoft_heavy", G=0.3, Pitch=0.8, Lp=2000)
    play(m, rng, "clip", 0.35, Of="creak", G=0.06, Pitch=1.3, Lp=4000)
    return m.out()


def body_fall(p, rng, length):
    m = Mix(length)
    play(m, rng, "clip", 0, Of="impactSoft_heavy", G=0.35, Pitch=0.7, Lp=1500, Verb=0.2)
    play(m, rng, "clip", 0.12, Of="impactSoft_medium", G=0.2, Pitch=0.75, Lp=1500, Verb=0.2)
    play(m, rng, "clip", 0.05, Of="cloth", G=0.12, Pitch=0.85, Verb=0.1)
    return m.out()


def scrape(p, rng, length):
    """The string scraped: the bow dug in near the bridge, too slow and too
    hard, so the string chatters instead of singing (bowed.py at full pressure)."""
    import instruments
    notes = [{"t": 0.0, "d": p.get("dur", 1.2), "n": p.get("n", "D2"), "dyn": p.get("dyn", 0.35), "press": 1.0,
              "a": 0.05, "r": 0.25, "vib": 0, "to": p.get("to")}]
    y = instruments.bowed_phrase({"notes": notes, "grain": 0.25, "hair": 0.8, "vib": 0, "check": False}, rng, length)
    return y, None


def bird(p, rng, length):
    """A small bird waking: a few clear whistled notes with quick slides,
    then a short trill (sine and a little FM, bright, a long way off)."""
    m = Mix(length)
    t = 0.0
    for i in range(p.get("notes", 4)):
        f0 = R(rng, 2600, 3600)
        play(m, rng, "tone", t, F=f0, F2=f0 * R(rng, 1.2, 1.5), Glide=0.05, A=0.01, D=R(rng, 0.08, 0.16), G=0.05,
             Pan=p.get("pan", 0.0), Verb=0.5)
        t += R(rng, 0.14, 0.26)
    if p.get("trill", True):
        f0 = R(rng, 3800, 4600)
        for i in range(7):
            play(m, rng, "fm", t, F=f0 * (1 - 0.02 * i), Ratio=1.0, Index=0.08, A=0.004, D=0.035, G=0.03, Pan=p.get("pan", 0.0), Verb=0.5)
            t += 0.045
    return m.out()


def drain(p, rng, length):
    """Light draining into the ground like water into sand: a soft falling
    hiss and a slow fall of the pickup's chime, dimming."""
    m = Mix(length)
    d = p.get("dur", 4.0)
    play(m, rng, "hiss", 0, A=0.6, D=d, G=0.03, Bp=3000, Bp2=400, Q=1.2, Verb=0.4)
    t = 0.2
    for i in range(8):
        f = 1174.66 * 2 ** (LADDER[8 - i] / 12)
        play(m, rng, "fm", t, F=f, F2=f * 0.94, Ratio=3.0, Index=0.2, D=0.3, G=0.012 * (1 - i / 9), Pan=R(rng, -0.4, 0.4), Verb=0.5)
        t += R(rng, 0.25, 0.45)
    return m.out()


def blue_flame(p, rng, length):
    """The blue lamps: a cold, even hiss with a thin high edge, no crackle
    (the warm fire's crackle is what it lacks), each lamp a little apart."""
    n = _n(length)
    out = np.zeros((n, 2))
    for i, pan in enumerate(p.get("pans", [-0.5, 0.0, 0.45])):
        x = dsp.white(rng, n)
        y = filt(x, "bp", p.get("f", 5200) * (1 + 0.1 * i), 1.3) + filt(x, "bp", 9000, 3) * 0.3
        am = 0.8 + 0.2 * np.tanh(dsp.onepole_lp(rng.standard_normal(n), 3) * 8)
        l, r = dsp.pan_gains(pan)
        out[:, 0] += y * am * l
        out[:, 1] += y * am * r
    return out, None


def glug(p, rng, length):
    """The flask held under: air leaving its neck in glugs (low tones that
    rise as the cavity fills) and a run of small bubbles."""
    m = Mix(length)
    t = 0.0
    k = p.get("glugs", 7)
    for i in range(k):
        f0 = 140 + 30 * i + R(rng, -10, 10)
        play(m, rng, "tone", t, F=f0, F2=f0 * 1.8, Glide=0.07, A=0.004, D=0.11, G=0.22 * (1 - i / (k + 4)), Lp=700)
        play(m, rng, "hiss", t, A=0.002, D=0.06, G=0.03, Bp=900, Q=1.5)
        t += R(rng, 0.13, 0.2)
    for i in range(p.get("bubbles", 14)):
        bt = t + R(rng, -0.6, 0.6)
        f0 = R(rng, 600, 1300)
        play(m, rng, "tone", bt, F=f0, F2=f0 * 1.7, A=0.002, D=R(rng, 0.02, 0.05), G=0.03, Pan=R(rng, -0.2, 0.2))
    return m.out()


def splash(p, rng, length):
    """The pull: a heavy body taken into the water. A slap, a wide burst of
    spray, the water closing (Cine 'kneel_water' and 'water_close' over it)."""
    m = Mix(length)
    play(m, rng, "clip", 0, Of="impactSoft_heavy", G=0.6, Pitch=0.6, Lp=1800)
    play(m, rng, "clip", 0, Of="impactPunch_heavy", G=0.3, Pitch=0.55, Lp=1500)
    n = _n(1.2)
    spray = filt(dsp.white(rng, n), "bp", 1800, 0.5) * np.exp(-np.arange(n) / (0.25 * SR))
    spray2 = filt(dsp.white(rng, n), "bp", 3500, 0.6) * np.exp(-np.arange(n) / (0.18 * SR))
    m.add(np.stack([spray + spray2 * 0.4, spray * 0.8 + spray2 * 0.6], axis=1) * 0.9, 0.02, verb=0.4)
    a, b = cine({"name": "kneel_water", "g": 2.0}, rng, 1.0)
    m.add(a, 0)
    a, b = cine({"name": "water_close", "g": 1.6}, rng, 2.0)
    m.add(a, 0.12)
    return m.out()


def under_roar(p, rng, length):
    """The river from inside it: the roar dropped to a muffle, a low churning
    that moves past the ears."""
    n = _n(length)
    out = np.zeros((n, 2))
    for s in range(2):
        x = dsp.brown(rng, n)
        y = filt(x, "lp", p.get("lp", 240), 0.8)
        am = 0.75 + 0.25 * np.tanh(dsp.onepole_lp(rng.standard_normal(n), 1.5) * 10)
        out[:, s] = y * am
    return out * 3.0, None


def blub(p, rng, length):
    """Bubbles bursting past the face under water: blub, blub-blub. Each a
    low tone that jumps up as the bubble pinches off and rises (Minnaert's
    pitch, set by its size), dulled by the water; dense at first, thinning."""
    m = Mix(length)
    d = p.get("dur", 2.5)
    t = 0.0
    while t < d:
        dens = 1 - t / d
        f0 = R(rng, 110, 300)
        g = R(rng, 0.10, 0.22) * (0.4 + 0.6 * dens)
        play(m, rng, "tone", t, F=f0, F2=f0 * R(rng, 1.8, 2.6), Glide=R(rng, 0.03, 0.06), A=0.003, D=R(rng, 0.05, 0.11),
             G=g, Lp=900, Pan=R(rng, -0.5, 0.5))
        if rng.random() < 0.5:  # a small one after it
            f1 = R(rng, 300, 600)
            play(m, rng, "tone", t + R(rng, 0.03, 0.08), F=f1, F2=f1 * 2.0, A=0.002, D=0.04, G=g * 0.4, Lp=1500,
                 Pan=R(rng, -0.5, 0.5))
        t += R(rng, 0.05, 0.13) / (0.35 + 0.65 * dens)
    return m.out()


def thrash(p, rng, length):
    """Cloth and a body fighting the water, heard from inside it: muffled
    surges of churned water, cloth dragging, a few dull knocks. No voice."""
    m = Mix(length)
    d = p.get("dur", 1.6)
    t = 0.0
    while t < d:
        L = R(rng, 0.12, 0.3)
        play(m, rng, "hiss", t, A=0.03, D=L, G=R(rng, 0.25, 0.45) * (1 - 0.5 * t / d), Lp=R(rng, 350, 600), Lp2=150,
             Brown=True, Pan=R(rng, -0.4, 0.4))
        if rng.random() < 0.5:
            play(m, rng, "clip", t, Of="cloth", G=0.12, Pitch=R(rng, 0.6, 0.75), Lp=900, Pan=R(rng, -0.3, 0.3))
        if rng.random() < 0.35:
            play(m, rng, "clip", t + 0.05, Of="impactSoft_medium", G=0.2, Pitch=R(rng, 0.5, 0.6), Lp=500)
        t += R(rng, 0.15, 0.32) * (1 + t / d)
    return m.out()


def steps(p, rng, length):
    """The traveler's steps, away from the fire toward the water."""
    m = Mix(length)
    t = 0.0
    for i in range(p.get("count", 5)):
        play(m, rng, "clip", t, Of=p.get("surface", "footstep_grass"), G=0.25 * (1 - i * p.get("away", 0.08)),
             Pitch=R(rng, 0.9, 1.0), Pan=p.get("pan", 0.0) + 0.05 * i, Verb=0.2)
        t += p.get("pace", 0.55) * R(rng, 0.95, 1.05)
    return m.out()


def kneel(p, rng, length):
    """Kneeling on the flat stones at the water's edge: cloth, a knee on stone,
    a bag's strap."""
    m = Mix(length)
    play(m, rng, "clip", 0, Of="cloth", G=0.2, Pitch=0.9)
    play(m, rng, "clip", 0.15, Of="impactSoft_medium", G=0.22, Pitch=0.9, Lp=3000)
    play(m, rng, "clip", 0.2, Of="footstep_concrete", G=0.12, Pitch=0.8, Lp=3000)
    play(m, rng, "clip", 0.5, Of="handleSmallLeather", G=0.12, Pitch=1.0)
    return m.out()


def music_gen(name):
    import instruments
    return {"bowed": instruments.bowed_phrase, "pluck": instruments.pluck_notes, "sung": instruments.sung_phrase,
            "drone": instruments.drone, "harmonic": instruments.harmonic}[name]


GENS = {
    "cine": cine, "heartbeat": heartbeat, "ember_spill": ember_spill, "anvil": anvil, "pour": pour,
    "rec": rec, "wind": wind, "striker": striker, "flame": flame, "march": march, "deep_breath": deep_breath,
    "stone_door": stone_door, "motes": motes, "town": town, "spear": spear, "body_fall": body_fall,
    "scrape": scrape, "bird": bird, "drain": drain, "blue_flame": blue_flame, "glug": glug, "splash": splash,
    "under_roar": under_roar, "blub": blub, "thrash": thrash, "steps": steps, "kneel": kneel,
}


def generate(gen, p, rng, length):
    if gen in GENS:
        out = GENS[gen](p, rng, length)
    else:
        out = (music_gen(gen)(p, rng, length), None)
    return out
