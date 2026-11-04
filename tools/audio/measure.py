"""Loudness/shape measurements for sound files. measure(samples, rate) -> dict."""
import sys, json
import numpy as np
from scipy import signal


def _db(x):
    return float(20 * np.log10(max(float(x), 1e-10)))


def measure(samples, rate=44100):
    x = np.asarray(samples, dtype=np.float64)
    mono = x if x.ndim == 1 else x.mean(axis=1)
    n = len(mono)
    ab = np.abs(x)
    peak = float(ab.max()) if n else 0.0
    ch = [x] if x.ndim == 1 else [x[:, c] for c in range(x.shape[1])]
    tp = max(float(np.abs(signal.resample_poly(c, 4, 1)).max()) for c in ch) if n else 0.0
    rms = float(np.sqrt(np.mean(x ** 2))) if n else 0.0
    out = {"duration_s": n / rate, "peak_dbfs": _db(peak), "true_peak_dbfs": _db(tp),
           "rms_dbfs": _db(rms), "crest_db": _db(peak) - _db(rms)}
    # lufs
    import pyloudnorm as pyln
    padded = False
    y = x
    if n < int(0.4 * rate):
        pad = int(0.4 * rate) - n
        y = np.concatenate([x, np.zeros((pad,) + x.shape[1:])])
        padded = True
    try:
        out["lufs"] = float(pyln.Meter(rate).integrated_loudness(y))
    except Exception:
        out["lufs"] = float("-inf")
    out["lufs_padded"] = padded
    if n > 6 * rate:  # short-term max over 3 s windows (hop 1 s), for long tapes
        m = pyln.Meter(rate)
        st = []
        for s in range(0, n - 3 * rate + 1, rate):
            try:
                st.append(float(m.integrated_loudness(x[s:s + 3 * rate])))
            except Exception:
                pass
        out["lufs_short_max"] = max(st) if st else float("-inf")
    # onset / tail
    if n and peak > 0:
        thr = peak * 10 ** (-20 / 20)
        idx = np.nonzero(np.abs(mono) >= thr)[0] if x.ndim == 1 else np.nonzero(ab.max(axis=1) >= thr)[0]
        out["onset_ms"] = float(idx[0] / rate * 1000) if len(idx) else 0.0
        env = ab if x.ndim == 1 else ab.max(axis=1)
        ipk = int(np.argmax(env))
        last = np.nonzero(env > 10 ** (-50 / 20))[0]
        out["tail_ms"] = float(max(0, last[-1] - ipk) / rate * 1000) if len(last) else 0.0
    else:
        out["onset_ms"] = 0.0
        out["tail_ms"] = 0.0
    # centroid
    cen = 0.0
    if n >= 1024:
        hop = 512
        nf = 1 + (n - 1024) // hop
        idx = np.arange(1024)[None, :] + hop * np.arange(nf)[:, None]
        fr = mono[idx] * np.hanning(1024)[None, :]
        lvl = np.sqrt((fr ** 2).sum(axis=1) / (np.hanning(1024) ** 2).sum())
        good = lvl > 10 ** (-40 / 20)
        if good.any():
            mag = np.abs(np.fft.rfft(fr[good], axis=1))
            f = np.fft.rfftfreq(1024, 1 / rate)
            c = (mag * f[None, :]).sum(axis=1) / np.maximum(mag.sum(axis=1), 1e-12)
            cen = float(c.mean())
    elif n:
        sp = np.abs(np.fft.rfftfreq(n, 1 / rate))
        mg = np.abs(np.fft.rfft(mono))
        cen = float((sp * mg).sum() / max(mg.sum(), 1e-12))
    out["centroid_hz"] = cen
    out["clipped"] = int((ab >= 0.999).sum())
    return out


def read_wav(path):
    import soundfile as sf
    d, r = sf.read(path, dtype="float64", always_2d=False)
    return d, r


def main(argv):
    as_json = "--json" in argv
    files = [a for a in argv if not a.startswith("--")]
    for f in files:
        d, r = read_wav(f)
        m = measure(d, r)
        if as_json:
            print(json.dumps({"file": f, **m}))
        else:
            print("%s: %.2fs peak %.1f tp %.1f lufs %.1f%s rms %.1f crest %.1f onset %.0fms tail %.0fms cent %.0fHz clip %d" % (
                f, m["duration_s"], m["peak_dbfs"], m["true_peak_dbfs"], m["lufs"], "*" if m["lufs_padded"] else "",
                m["rms_dbfs"], m["crest_db"], m["onset_ms"], m["tail_ms"], m["centroid_hz"], m["clipped"]))


if __name__ == "__main__":
    main(sys.argv[1:])
