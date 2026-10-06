"""Spectrogram and loudness of a game WAV: python spec.py IN.wav OUT.png [T0 T1] (seconds).
The top is 0..5 kHz (log-magnitude), the strip under it the loudness in dBFS (-60..0)."""
import sys, wave
import numpy as np
from PIL import Image, ImageDraw

path, out = sys.argv[1], sys.argv[2]
w = wave.open(path)
rate, n, ch, width = w.getframerate(), w.getnframes(), w.getnchannels(), w.getsampwidth()
raw = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32)
x = raw.reshape(-1, ch).mean(axis=1) / 32768
t0 = float(sys.argv[3]) if len(sys.argv) > 3 else 0
t1 = float(sys.argv[4]) if len(sys.argv) > 4 else len(x) / rate
x = x[int(t0 * rate):int(t1 * rate)]
print(f"{len(x) / rate:.1f} s at {rate} Hz, peak {np.abs(x).max():.3f}, rms {np.sqrt((x ** 2).mean()):.4f}")
N, hop = 4096, 512
win = np.hanning(N)
frames = [np.abs(np.fft.rfft(x[i:i + N] * win)) for i in range(0, len(x) - N, hop)]
S = np.array(frames).T
top = int(5000 / (rate / N))
S = 20 * np.log10(S[:top] + 1e-7)
S = np.clip((S - S.max() + 75) / 75, 0, 1)
img = (S[::-1] * 255).astype(np.uint8)
spec = Image.fromarray(img).resize((1800, 600))
spec = Image.merge("RGB", (spec, spec.point(lambda v: int(v * 0.6)), spec.point(lambda v: int(v * 0.25))))
sheet = Image.new("RGB", (1800, 760), (12, 10, 14))
sheet.paste(spec, (0, 0))
d = ImageDraw.Draw(sheet)
blk = rate // 50
env = [20 * np.log10(np.sqrt((x[i:i + blk] ** 2).mean()) + 1e-6) for i in range(0, len(x) - blk, blk)]
pts = [(i * 1800 / len(env), 750 - (max(-60, e) + 60) / 60 * 140) for i, e in enumerate(env)]
d.line(pts, fill=(120, 200, 255), width=2)
secs = len(x) / rate
for s in range(int(secs) + 1):
    X = s * 1800 / secs
    d.line([(X, 600), (X, 612)], fill=(200, 200, 200))
    d.text((X + 2, 612), f"{t0 + s:.0f}", fill=(200, 200, 200))
for hz in (500, 1000, 2000, 3000, 4000):
    Y = 600 - hz / 5000 * 600
    d.text((4, Y - 6), f"{hz}", fill=(90, 220, 90))
sheet.save(out)
