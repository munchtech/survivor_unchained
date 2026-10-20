"""Signal pieces for the SB00 renderer: filters, envelopes, rooms, loudness.

The voices ported from the game (godot/src/Audio/Synth.cs) keep its shapes:
a linear rise, a hold and an exponential fall to 1/10000 of the peak; pitch
and filter glides that are exponential over the voice's life; equal-power pan.
"""
import numpy as np
from scipy.signal import lfilter, fftconvolve, resample_poly
import soundfile as sf

SR = 48000


def rng_for(key):
    """One seeded generator per cue id, so a render is the same every time."""
    h = 2166136261
    for ch in str(key).encode():
        h = ((h ^ ch) * 16777619) & 0xFFFFFFFF
    return np.random.default_rng(h)


def db(x):
    return 10 ** (x / 20.0)


def note_hz(n):
    """'Bb3' -> Hz, twelve-tone equal temperament on A4 = 440 (the game's D3 = 146.83)."""
    if isinstance(n, (int, float)):
        return float(n)
    names = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    k = names[n[0]]
    i = 1
    while i < len(n) and n[i] in "#b":
        k += 1 if n[i] == "#" else -1
        i += 1
    octave = int(n[i:])
    m = 12 * (octave + 1) + k
    return 440.0 * 2 ** ((m - 69) / 12)


# ------------------------------------------------------------- envelopes ---

def env_game(n_a, n_h, n_d, peak, n=None):
    """Synth.cs Envelope: linear rise, hold, exponential fall to 1e-4 of peak."""
    a = np.linspace(0.0001, peak, max(1, n_a), endpoint=True)
    h = np.full(max(0, n_h), peak)
    k = (0.0001 / max(1e-6, peak)) ** (1.0 / max(1, n_d))
    d = peak * k ** np.arange(1, max(1, n_d) + 1)
    e = np.concatenate([a, h, d])
    if n is not None:
        e = np.pad(e, (0, max(0, n - len(e))))[:n]
    return e


def glide(f0, f1, n, span_n=None):
    """Synth.cs Glide: exponential from f0 to f1 over span, then holds."""
    if f1 is None or f0 <= 0:
        return np.full(n, float(f0))
    span_n = max(1, int(span_n if span_n is not None else n))
    k = (max(1e-4, f1) / f0) ** (1.0 / span_n)
    i = np.minimum(np.arange(1, n + 1), span_n)
    return f0 * k ** i


def breakpoints(points, n, t0=0.0, sr=SR, log=False):
    """A curve through [t, value] points (seconds from t0), linear or in dB."""
    t = t0 + np.arange(n) / sr
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return np.interp(t, xs, ys)


# --------------------------------------------------------------- filters ---

def biquad_coefs(kind, f, q, sr=SR, gain_db=0.0):
    w = 2 * np.pi * np.clip(f, 10, sr * 0.45) / sr
    cs, sn = np.cos(w), np.sin(w)
    alpha = sn / (2 * q)
    if kind == "lp":
        b = [(1 - cs) / 2, 1 - cs, (1 - cs) / 2]
    elif kind == "hp":
        b = [(1 + cs) / 2, -(1 + cs), (1 + cs) / 2]
    elif kind == "bp":  # constant 0 dB peak (the cookbook's, as Synth.cs)
        b = [alpha, 0.0, -alpha]
    elif kind == "peak":
        A = 10 ** (gain_db / 40)
        b = [1 + alpha * A, -2 * cs, 1 - alpha * A]
        a = [1 + alpha / A, -2 * cs, 1 - alpha / A]
        return np.array(b) / a[0], np.array(a) / a[0]
    elif kind == "lowshelf" or kind == "highshelf":
        A = 10 ** (gain_db / 40)
        sq = 2 * np.sqrt(A) * alpha
        if kind == "lowshelf":
            b = [A * ((A + 1) - (A - 1) * cs + sq), 2 * A * ((A - 1) - (A + 1) * cs), A * ((A + 1) - (A - 1) * cs - sq)]
            a = [(A + 1) + (A - 1) * cs + sq, -2 * ((A - 1) + (A + 1) * cs), (A + 1) + (A - 1) * cs - sq]
        else:
            b = [A * ((A + 1) + (A - 1) * cs + sq), -2 * A * ((A - 1) + (A + 1) * cs), A * ((A + 1) + (A - 1) * cs - sq)]
            a = [(A + 1) - (A - 1) * cs + sq, 2 * ((A - 1) - (A + 1) * cs), (A + 1) - (A - 1) * cs - sq]
        return np.array(b) / a[0], np.array(a) / a[0]
    else:
        raise ValueError(kind)
    a = [1 + alpha, -2 * cs, 1 - alpha]
    return np.array(b) / a[0], np.array(a) / a[0]


def filt(x, kind, f, q=0.707, gain_db=0.0):
    """A fixed biquad over a mono or (n, 2) signal."""
    b, a = biquad_coefs(kind, f, q, gain_db=gain_db)
    return lfilter(b, a, x, axis=0)


def tvfilt(x, kind, f, q=0.707, block=64):
    """A biquad whose frequency moves (an array per sample), coefficients remade
    every block, state carried across: Synth.cs remakes its every 32 samples."""
    x = np.asarray(x, dtype=np.float64)
    f = np.broadcast_to(np.asarray(f, dtype=np.float64), (x.shape[0],))
    y = np.empty_like(x)
    zi = np.zeros((2,) + x.shape[1:])
    for s in range(0, x.shape[0], block):
        e = min(x.shape[0], s + block)
        b, a = biquad_coefs(kind, float(f[s]), q)
        y[s:e], zi = lfilter(b, a, x[s:e], axis=0, zi=zi)
    return y


def onepole_lp(x, f):
    p = np.exp(-2 * np.pi * f / SR)
    return lfilter([1 - p], [1, -p], x, axis=0)


# ------------------------------------------------------------------ noise ---

def white(rng, n):
    return rng.standard_normal(n) * 0.35


def brown(rng, n):
    """Leaky-integrated white, as the game's Brown buffer: dark, rolling."""
    w = rng.standard_normal(n)
    b = lfilter([0.02], [1, -0.995], w)
    return b / (np.max(np.abs(b)) + 1e-9) * 0.9


def pink(rng, n):
    w = rng.standard_normal(n)
    b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
    a = [1, -2.494956002, 2.017265875, -0.522189400]
    return lfilter(b, a, w) * 0.5


# ------------------------------------------------------------------- pan ---

def pan_gains(p):
    x = (np.clip(p, -1, 1) + 1) / 2
    return np.cos(x * np.pi / 2), np.sin(x * np.pi / 2)


def to_stereo(m, pan=0.0, width=0.0, rng=None):
    """Equal-power pan; width > 0 spreads a mono source by a short decorrelating delay."""
    if m.ndim == 2:
        return m
    l, r = pan_gains(pan)
    out = np.stack([m * l, m * r], axis=1)
    if width > 0 and len(m) > 600:
        # the right side a few ms later, so a mono take opens without moving off centre
        d = int(0.009 * SR)
        late = np.concatenate([np.zeros(d), m[:-d]])
        out[:, 1] = out[:, 1] * (1 - width) + late * r * width
    return out


# ----------------------------------------------------------------- rooms ---

def room_ir(rt60, seconds=None, lp=6000.0, lp_end=1200.0, pre=0.0, early=None, seed=1, damp_lows=0.0):
    """A stereo impulse response: decorrelated noise under an exponential
    decay whose top end dies faster (a low-pass that closes along the tail),
    plus a few early reflections. Rooms are made, not sampled."""
    rng = rng_for(f"room{seed}")
    seconds = seconds or rt60 * 1.1
    n = int(seconds * SR)
    t = np.arange(n) / SR
    decay = 10 ** (-3 * t / rt60)
    ir = np.stack([rng.standard_normal(n), rng.standard_normal(n)], axis=1) * decay[:, None]
    fcut = lp * (lp_end / lp) ** (t / seconds)
    ir = tvfilt(ir, "lp", fcut, 0.707, block=256)
    if damp_lows > 0:
        ir = filt(ir, "hp", damp_lows)
    if early:
        for (dt, g, pan) in early:
            i = int(dt * SR)
            if i < n:
                l, r = pan_gains(pan)
                ir[i, 0] += g * l * 6
                ir[i, 1] += g * r * 6
    if pre > 0:
        ir = np.concatenate([np.zeros((int(pre * SR), 2)), ir])
    ir /= np.sqrt(np.sum(ir ** 2) / 2) + 1e-12
    return ir


def convolve_st(x, ir):
    """Stereo in, stereo out: each side through its own side of the room."""
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    out = np.zeros((x.shape[0] + ir.shape[0] - 1, 2))
    out[:, 0] = fftconvolve(x[:, 0], ir[:, 0]) * 0.75 + fftconvolve(x[:, 1], ir[:, 0]) * 0.25
    out[:, 1] = fftconvolve(x[:, 1], ir[:, 1]) * 0.75 + fftconvolve(x[:, 0], ir[:, 1]) * 0.25
    return out


# ------------------------------------------------------------ recordings ---

_cache = {}


def load_wav(path):
    """A recording at 48 kHz, mono, peak as recorded."""
    if path not in _cache:
        x, r = sf.read(path, always_2d=True)
        x = x.mean(1)
        if r != SR:
            g = np.gcd(int(r), SR)
            x = resample_poly(x, SR // g, int(r) // g)
        _cache[path] = x.astype(np.float64)
    return _cache[path]


def repitch(x, pitch):
    """Varispeed, as the game's Clip: pitch 0.5 is an octave down and twice as long."""
    if abs(pitch - 1) < 1e-6:
        return x
    n = int(len(x) / pitch)
    return np.interp(np.arange(n) * pitch, np.arange(len(x)), x)


def loop_to(x, n, offset=0, xfade=0.25):
    """A looped recording n samples long, starting `offset` into it, the seam crossfaded."""
    xf = int(xfade * SR)
    body = x[: len(x) - xf].copy()
    body[:xf] = body[:xf] * np.linspace(0, 1, xf) + x[len(x) - xf:] * np.linspace(1, 0, xf)
    reps = int(np.ceil((n + offset) / len(body))) + 1
    y = np.tile(body, reps)
    return y[offset: offset + n]


# ------------------------------------------------------------- loudness ---

def k_weight(x):
    """ITU-R BS.1770-4 K-weighting at 48 kHz (the standard's own coefficients)."""
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2 = [1.0, -2.0, 1.0]
    a2 = [1.0, -1.99004745483398, 0.99007225036621]
    return lfilter(b2, a2, lfilter(b1, a1, x, axis=0), axis=0)


def _block_power(y, win, hop):
    p = np.sum(y ** 2, axis=1) if y.ndim == 2 else y ** 2
    c = np.concatenate([[0.0], np.cumsum(p)])
    starts = np.arange(0, max(1, len(p) - win + 1), hop)
    return (c[starts + win] - c[starts]) / win, starts


def lufs_integrated(x):
    y = k_weight(x)
    z, _ = _block_power(y, int(0.4 * SR), int(0.1 * SR))
    l = -0.691 + 10 * np.log10(z + 1e-20)
    z1 = z[l > -70]
    if len(z1) == 0:
        return -np.inf
    lr = -0.691 + 10 * np.log10(np.mean(z1)) - 10
    z2 = z1[(-0.691 + 10 * np.log10(z1)) > lr]
    return -0.691 + 10 * np.log10(np.mean(z2))


def lufs_curve(x, window=3.0, hop=0.1):
    """Short-term (3 s) or momentary (0.4 s) loudness, centred on each hop."""
    y = k_weight(x)
    win = int(window * SR)
    pad = np.zeros((win // 2,) + y.shape[1:])
    y = np.concatenate([pad, y, pad])
    z, starts = _block_power(y, win, int(hop * SR))
    return starts / SR, -0.691 + 10 * np.log10(z + 1e-20)


def true_peak_db(x):
    up = resample_poly(x, 4, 1, axis=0)
    return 20 * np.log10(np.max(np.abs(up)) + 1e-20)
