"""Levels of the game's own mix (--wav): peak, clipped samples, loudest 50 ms and 400 ms, and the
mean over the run, each in dBFS. python levels.py a.wav b.wav ...  (Measured, not heard.)"""
import sys
import wave
import numpy as np


def db(v):
    return 20 * np.log10(max(v, 1e-9))


print(f"{'file':28s} {'peak':>6s} {'dBFS':>6s} {'clip':>5s} {'50ms':>6s} {'400ms':>6s} {'mean':>6s} {'crest':>6s}")
for path in sys.argv[1:]:
    with wave.open(path) as w:
        rate = w.getframerate()
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, 2)
    data = raw.astype(np.float32) / 32768
    mono = data.mean(axis=1)
    peak = float(np.max(np.abs(data)))
    clip = int(np.sum(np.abs(raw.astype(np.int32)) >= 32767))

    def loudest(sec):
        win = int(rate * sec)
        c = np.concatenate([[0.0], np.cumsum(mono.astype(np.float64) ** 2)])
        sq = (c[win:] - c[:-win]) / win
        return float(np.sqrt(sq.max())) if len(sq) else 0.0

    l50, l400 = loudest(0.05), loudest(0.4)
    mean = float(np.sqrt(np.mean(mono ** 2)))
    name = path.replace("\\", "/").split("/")[-1]
    print(f"{name:28s} {peak:6.3f} {db(peak):6.1f} {clip:5d} {db(l50):6.1f} {db(l400):6.1f} {db(mean):6.1f} {db(peak) - db(mean):6.1f}")
