"""Where a tape peaks: the top moments (sample peak per 20 ms), with the energy below 200 Hz,
200 Hz-2 kHz and above 2 kHz in the 50 ms round each. python peaks.py a.wav [n]"""
import sys
import wave
import numpy as np

path = sys.argv[1]
n_top = int(sys.argv[2]) if len(sys.argv) > 2 else 6
with wave.open(path) as w:
    rate = w.getframerate()
    data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, 2).astype(np.float32) / 32768
mono = np.abs(data).max(axis=1)
hop = int(rate * 0.02)
blocks = [(float(mono[i:i + hop].max()), i) for i in range(0, len(mono) - hop, hop)]
blocks.sort(reverse=True)
seen = []
for pk, i in blocks:
    if any(abs(i - j) < rate * 0.1 for j in seen):
        continue
    seen.append(i)
    seg = data[max(0, i - hop):i + 2 * hop].mean(axis=1)
    S = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2
    f = np.fft.rfftfreq(len(seg), 1 / rate)
    tot = S.sum() + 1e-12
    lo, mid, hi = S[f < 200].sum() / tot, S[(f >= 200) & (f < 2000)].sum() / tot, S[f >= 2000].sum() / tot
    print(f"{i / rate:6.2f}s peak {pk:.3f}  low {lo:.2f} mid {mid:.2f} high {hi:.2f}")
    if len(seen) >= n_top:
        break
