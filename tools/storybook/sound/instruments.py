"""The score's instruments: the bowed solo (bowed.py's waveguide played by a
phrase of notes), a plucked gut string under it, the river's singer (a
formant voice) and the drone. Each takes a list of notes from the cue sheet,
times in seconds from the cue's start, and returns mono at 48 kHz.
"""
import numpy as np
from scipy.signal import lfilter
import dsp
from dsp import SR, note_hz, filt
import bowed


def _pitch_track(notes, n, port=0.07, glide_frac=0.45):
    """Hz per sample through the notes: a short portamento into each slurred
    note, and a fall or rise through the last part of a note that has 'to'
    (the take's own glides, as on 'are' and 'reach')."""
    f = np.full(n, note_hz(notes[0]["n"]))
    prev = None
    for i, nt in enumerate(notes):
        s = int(nt["t"] * SR)
        e = min(n, int((nt["t"] + nt["d"]) * SR))
        nxt = int(notes[i + 1]["t"] * SR) if i + 1 < len(notes) else n
        e_hold = max(e, min(n, nxt))  # the pitch holds through any rest, so the ring keeps its note
        hz = note_hz(nt["n"])
        seg = np.full(e_hold - s, hz)
        if nt.get("to"):
            g0 = int((nt["d"] * (1 - nt.get("gf", glide_frac))) * SR)
            g1 = min(e - s, len(seg))
            k = np.linspace(0, 1, max(1, g1 - g0))
            k = k * k * (3 - 2 * k)
            seg[g0:g1] = hz * (note_hz(nt["to"]) / hz) ** k
            seg[g1:] = note_hz(nt["to"])
        if prev is not None and nt.get("slur", True):
            pn = int(nt.get("port", port) * SR)
            pn = min(pn, len(seg))
            k = np.linspace(0, 1, max(1, pn))
            seg[:pn] = prev * (seg[:pn] / prev) ** (k * k * (3 - 2 * k))
        f[s:e_hold] = seg
        prev = seg[min(len(seg) - 1, e - s - 1)] if len(seg) else hz
    return f


def _vibrato(notes, n, rng, depth=16, rate=5.4, delay=0.25, rise=0.45):
    """Cents per sample: a vibrato that blooms after the note speaks, its rate wandering."""
    t = np.arange(n) / SR
    wander = np.cumsum(rng.standard_normal(n // 480 + 2))[: n // 480 + 2]
    wander = np.interp(np.arange(n), np.arange(len(wander)) * 480, wander)
    wander = (wander - wander.mean()) / (np.std(wander) + 1e-9) * 0.25
    ph = 2 * np.pi * np.cumsum(rate + wander) / SR
    amt = np.zeros(n)
    for nt in notes:
        s = int((nt["t"] + nt.get("vdelay", delay)) * SR)
        e = min(n, int((nt["t"] + nt["d"]) * SR))
        if e <= s:
            continue
        d = nt.get("vib", depth)
        k = np.clip(np.arange(e - s) / (rise * SR), 0, 1)
        amt[s:e] = d * k
    return amt * np.sin(ph)


def _bow(notes, n, attack=0.12, release=0.14):
    """Bow speed and pressure per sample: each note's dynamic, a swell through
    long notes, a small dip where the bow changes direction between slurred notes."""
    vel = np.zeros(n)
    press = np.zeros(n)
    for i, nt in enumerate(notes):
        s = int(nt["t"] * SR)
        e = min(n, int((nt["t"] + nt["d"]) * SR))
        L = e - s
        if L <= 0:
            continue
        dyn = nt.get("dyn", 0.5)
        v = 0.03 + 0.2 * dyn
        a = int(nt.get("a", attack) * SR)
        r = int(nt.get("r", release) * SR)
        env = np.ones(L)
        joined = i > 0 and nt.get("slur", True) and notes[i - 1]["t"] + notes[i - 1]["d"] >= nt["t"] - 1e-3
        a = min(a, L // 2)
        if joined:
            env[:a] = 0.82 + 0.18 * np.linspace(0, 1, a) if a else 1
        else:
            env[:a] = np.sin(np.linspace(0, np.pi / 2, a)) ** 1.5 if a else 1
        last = i + 1 >= len(notes) or not notes[i + 1].get("slur", True) or \
            notes[i + 1]["t"] > nt["t"] + nt["d"] + 1e-3
        if last and r > 0:
            r = min(r, L - a)
            env[L - r:] *= np.cos(np.linspace(0, np.pi / 2, r)) ** 1.2
        sw = nt.get("swell", 0.0)  # a hairpin through the note: + grows, - fades
        if sw:
            env *= 1 + sw * np.sin(np.linspace(0, np.pi, L)) if sw > 0 else np.linspace(1, 1 + sw, L)
        vel[s:e] = np.maximum(vel[s:e], v * env)
        press[s:e] = nt.get("press", 0.55)
    return vel, press


def body(x, kind="cello"):
    """The instrument's wooden box: a few resonances and the bridge hill, a
    gentle top cut (a real body has no fizz above 6 kHz)."""
    if kind == "cello":
        modes = [(98, 4.0, 6), (196, 5.0, 4), (290, 4.0, 4.5), (440, 3.0, 2.5), (620, 2.0, -2), (1200, 1.5, 1.5), (2300, 1.2, 4)]
    else:  # a smaller box for the plucked gut string
        modes = [(130, 3.0, 4), (260, 4.0, 4), (520, 3.0, 2), (2600, 1.2, 2)]
    y = filt(x, "hp", 55, 0.7)
    for f0, q, g in modes:
        y = filt(y, "peak", f0, q, g)
    y = filt(y, "lp", 6500, 0.6)
    return y


def bowed_phrase(p, rng, length):
    """A phrase on the solo string. A real bow can catch a string's octave or
    twelfth instead of its note (too little pressure for the speed); the model
    does too, now and then. So each note is listened to after the take and,
    if it caught the wrong mode, the take is played again with a little more
    weight on that note and a fresh bow (as a player would), up to six times."""
    import copy
    notes = copy.deepcopy(p["notes"])
    seed = int(rng.integers(1 << 30))
    for attempt in range(6):
        q = dict(p, notes=notes)
        y = _bowed_take(q, np.random.default_rng(seed + attempt), length)
        if not p.get("check", True):
            return y
        bad = _wrong_mode(y, notes, length)
        if not bad:
            return y
        for i in bad:
            notes[i]["press"] = min(0.85, notes[i].get("press", 0.55) + 0.06)
            notes[i]["dyn"] = notes[i].get("dyn", 0.5) * 0.92
    return y


def _wrong_mode(y, notes, length):
    """Notes whose middle is mostly more than 60 cents from where they should be."""
    from pitch import yin, midi
    from scipy.signal import resample_poly
    ts, fs, ap, rms = yin(resample_poly(y, 1, 3), 16000, 55, 900, thresh=0.2)
    bad = []
    for i, nt in enumerate(notes):
        m = (ts >= nt["t"] + 0.15) & (ts <= nt["t"] + nt["d"] * 0.85) & (fs > 0)
        if m.sum() < 3:
            continue
        got = midi(fs[m])
        lo = min(midi(note_hz(nt["n"])), midi(note_hz(nt.get("to", nt["n"])))) - 0.6
        hi = max(midi(note_hz(nt["n"])), midi(note_hz(nt.get("to", nt["n"])))) + 0.6
        if np.mean((got >= lo) & (got <= hi)) < 0.85:
            bad.append(i)
    return bad


def _bowed_take(p, rng, length):
    n = int(length * SR)
    notes = p["notes"]
    f = _pitch_track(notes, n, port=p.get("port", 0.07))
    cents = _vibrato(notes, n, rng, depth=p.get("vib", 16), rate=p.get("vib_rate", 5.4))
    f = f * 2 ** (cents / 1200)
    vel, press = _bow(notes, n, attack=p.get("attack", 0.12), release=p.get("release", 0.14))
    grain_amt = p.get("grain", 0.03)
    grain = rng.standard_normal(n) * grain_amt
    # rosin catches: the bow sticks and slips a little more as it slows
    y = bowed.string_loop(bowed.correct(f), vel, press, grain)
    y = body(y) * 2.2
    # the bow hair on the string, heard close: a breath of hiss that follows the bow
    hair = filt(rng.standard_normal(n), "bp", 3800, 0.9) * dsp.onepole_lp(vel, 30) * p.get("hair", 0.25)
    return y + hair


def pluck_notes(p, rng, length):
    """A gut string plucked: decaying partials with a little stretch, a soft
    thumb noise at the start, through a small box."""
    n = int(length * SR)
    y = np.zeros(n)
    t_all = np.arange(n) / SR
    for nt in p["notes"]:
        s = int(nt["t"] * SR)
        if s >= n:
            continue
        hz = note_hz(nt["n"])
        L = min(n - s, int(nt.get("ring", p.get("ring", 2.2)) * SR))
        t = t_all[:L]
        out = np.zeros(L)
        pos = p.get("pos", 0.18)  # where the thumb takes the string
        tau1 = nt.get("ring", p.get("ring", 2.2)) / 3.0
        for k in range(1, 24):
            fk = k * hz * np.sqrt(1 + 0.00015 * k * k)
            if fk > 9000:
                break
            amp = abs(np.sin(k * np.pi * pos)) / k ** 1.25
            tau = tau1 / (1 + 0.5 * (k - 1))
            out += amp * np.sin(2 * np.pi * fk * t + rng.uniform(0, 6.28)) * np.exp(-t / tau)
        a = int(0.004 * SR)
        out[:a] *= np.linspace(0, 1, a)
        thumb = filt(rng.standard_normal(min(L, 400)), "bp", 1400, 0.8) * np.exp(-np.arange(min(L, 400)) / 60.0) * 0.08
        out[: len(thumb)] += thumb
        y[s:s + L] += out * nt.get("dyn", 0.6)
    return body(y, "gut") * 0.5


# formants (Hz, bandwidth Hz, gain dB) for a bass voice: 'oo' and 'oh'
VOWELS = {
    "u": [(330, 70, 0), (700, 90, -8), (2350, 140, -26), (2700, 160, -30)],
    "o": [(420, 70, 0), (760, 80, -6), (2450, 120, -22), (2700, 140, -26)],
    "a": [(620, 80, 0), (1050, 90, -4), (2500, 120, -18), (2800, 140, -22)],
}


def sung_phrase(p, rng, length):
    """A deep voice singing the motif on a vowel, no words: a glottal source
    (harmonics falling at 12 dB an octave) through the vowel's formants, with
    a slow wide vibrato and breath. The river's song, before it has words."""
    n = int(length * SR)
    notes = p["notes"]
    f = _pitch_track(notes, n, port=p.get("port", 0.12))
    cents = _vibrato(notes, n, rng, depth=p.get("vib", 30), rate=p.get("vib_rate", 4.6), delay=0.3, rise=0.6)
    f = f * 2 ** (cents / 1200)
    ph = 2 * np.pi * np.cumsum(f) / SR
    src = np.zeros(n)
    for k in range(1, 60):
        lim = (k * f < 5000).astype(float)
        src += lim * np.sin(k * ph) / k ** 1.6
    env = np.zeros(n)
    for i, nt in enumerate(notes):
        s = int(nt["t"] * SR); e = min(n, int((nt["t"] + nt["d"]) * SR))
        L = e - s
        if L <= 0:
            continue
        a = min(L // 2, int(nt.get("a", 0.18) * SR)); r = min(L - a, int(nt.get("r", 0.3) * SR))
        e1 = np.ones(L) * nt.get("dyn", 0.7)
        e1[:a] *= np.linspace(0, 1, a) ** 1.5
        if r > 0:
            e1[L - r:] *= np.linspace(1, 0, r) ** 1.5
        env[s:e] = np.maximum(env[s:e], e1)
    env = dsp.onepole_lp(env, 25)
    src = src * env + filt(rng.standard_normal(n), "bp", 1200, 0.6) * env * p.get("breath", 0.02)
    y = np.zeros(n)
    for fr, bw, g in VOWELS[p.get("vowel", "u")]:
        y += filt(src, "bp", fr, fr / bw) * dsp.db(g)
    return y * 3.0


def drone(p, rng, length):
    """The Night drone on D: a bowed-sounding stack of D2, A2, D3 (saws,
    slightly detuned pairs, dark low-pass that breathes), and a breath of
    bandpassed noise (Sfx.Cine 'drone', moved to the Night's root)."""
    n = int(length * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for hz, g in p.get("stack", [["D2", 1.0], ["A2", 0.7], ["D3", 0.55]]):
        hz = note_hz(hz)
        for det in (-5.0, 4.0):
            fr = hz * 2 ** (det / 1200) * (1 + 0.0015 * np.sin(2 * np.pi * 0.11 * t + rng.uniform(0, 6)))
            ph = np.cumsum(fr) / SR
            saw = 2 * (ph - np.floor(ph)) - 1
            y += saw * g * 0.5
    lp = p.get("lp", 420) * (1 + 0.25 * np.sin(2 * np.pi * 0.07 * t + 1.0))
    y = dsp.tvfilt(y, "lp", lp, 0.8, block=256)
    y += filt(dsp.pink(rng, n), "bp", 700, 1.2) * p.get("breath", 0.25)
    return y * 0.25


def harmonic(p, rng, length):
    """A bowed harmonic, high and cold: nearly a sine, a flutter of bow noise,
    no vibrato (flautando on the string's node)."""
    n = int(length * SR)
    hz = note_hz(p["n"])
    t = np.arange(n) / SR
    fr = hz * (1 + 0.0008 * np.sin(2 * np.pi * 0.3 * t))
    ph = 2 * np.pi * np.cumsum(fr) / SR
    y = np.sin(ph) + 0.08 * np.sin(2 * ph) + 0.03 * np.sin(3 * ph)
    flutter = 1 + 0.06 * dsp.onepole_lp(rng.standard_normal(n), 6) * 8
    noise = filt(rng.standard_normal(n), "bp", hz * 1.0, 6) * 0.15
    return (y * flutter + noise) * 0.5
