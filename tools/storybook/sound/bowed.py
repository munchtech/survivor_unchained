"""A bowed string: a digital waveguide with a friction bow, after Smith's and
Cook's STK Bowed (McIntyre, Schumacher and Woodhouse's model).

Two delay lines meet at the bow (nut side and bridge side); the bow drags the
string by a friction curve whose slope is the bow pressure; the bridge
reflects through a one-pole low-pass (the string's losses). Grain comes from
noise on the bow's speed (rosin), vibrato moves the finger, and the body is a
bank of resonances (render side). Pure Python per sample: a solo phrase of
ten seconds takes a few seconds, and phrases render in parallel.
"""
import math
import numpy as np

SR = 48000
BETA = 0.127236  # bow point, as a fraction of the string from the bridge (STK's)
# The loop's own delay beyond the two lines: the one-pole's phase delay and the
# read-before-write sample. Measured with pitch.py (tune_check below), in samples.
LOOP_EXTRA = 1.95


# Measured sharpness of the bare loop (cents) by pitch, from tune_check(): the
# one-pole's delay falls with frequency. The asked pitch is lowered by this much.
SHARP = [(73.42, 0.3), (110.0, 0.8), (146.83, 1.0), (220.0, 1.5), (293.66, 2.3), (440.0, 4.2), (1174.66, 19.2)]


def correct(f):
    """Asked pitch -> pitch to give the loop so it sounds at the asked pitch."""
    xs = np.log([p[0] for p in SHARP]); ys = [p[1] for p in SHARP]
    c = np.interp(np.log(np.maximum(f, 1.0)), xs, ys)
    return f * 2 ** (-c / 1200)


def string_loop(f, vel, press, grain, pole=None):
    """f: Hz per sample; vel: bow speed per sample (0 = bow off the string);
    press: 0..1 bow pressure per sample; grain: rosin noise per sample.
    Returns the string's velocity at the bridge (what drives the body)."""
    n = len(f)
    p = pole if pole is not None else 0.75 - 0.2 * 22050.0 / SR
    b0 = 0.95 * (1 - p)
    N = 8192
    mask = N - 1
    neck = [0.0] * N
    bridge = [0.0] * N
    out = [0.0] * n
    y1 = 0.0
    w = 0
    fl = f.tolist(); vl = vel.tolist(); pl = press.tolist(); gl = grain.tolist()
    for i in range(n):
        base = SR / fl[i] - LOOP_EXTRA
        dn = base * (1.0 - BETA)
        dbr = base * BETA
        # neck side, linear interpolation
        rp = w - dn
        k = math.floor(rp); fr = rp - k
        a = neck[k & mask]; nut_out = a + (neck[(k + 1) & mask] - a) * fr
        rp = w - dbr
        k = math.floor(rp); fr = rp - k
        a = bridge[k & mask]; br_out = a + (bridge[(k + 1) & mask] - a) * fr
        y1 = b0 * br_out + p * y1
        bridge_refl = -y1
        nut_refl = -nut_out
        sv = bridge_refl + nut_refl
        v = vl[i]
        if v > 0.0:
            v = v * (1.0 + gl[i])
            dv = v - sv
            slope = 5.0 - 4.0 * pl[i]
            x = abs((dv + 0.001) * slope) + 0.75
            r = x ** -4
            if r > 1.0:
                r = 1.0
            nv = dv * r
        else:
            nv = 0.0
        neck[w & mask] = bridge_refl + nv
        bridge[w & mask] = nut_refl + nv
        out[i] = br_out
        w += 1
    return np.array(out)


def tune_check():
    """Prints the measured pitch of held notes against the asked pitch (cents)."""
    from pitch import yin, midi
    from scipy.signal import resample_poly
    rng = np.random.default_rng(3)
    for hz in [73.42, 110.0, 146.83, 220.0, 293.66, 440.0, 1174.66]:
        n = int(1.5 * SR)
        f = np.full(n, hz)
        vel = np.full(n, 0.12); vel[:2400] *= np.linspace(0, 1, 2400)
        press = np.full(n, 0.55)
        grain = rng.standard_normal(n) * 0.02
        y = string_loop(correct(f), vel, press, grain)
        x = resample_poly(y[SR // 2:], 1, 3)
        ts, fs, ap, rms = yin(x, 16000, fmin=max(40, hz * 0.6), fmax=min(2000, hz * 1.6), thresh=0.2)
        fs = fs[fs > 0]
        m = np.median(fs) if len(fs) else 0
        print(f"{hz:8.2f} -> {m:8.2f}  {100 * (midi(m) - midi(hz)) if m else float('nan'):+6.1f} c")


if __name__ == "__main__":
    import time, sys
    t = time.time()
    tune_check()
    print("took", time.time() - t)
