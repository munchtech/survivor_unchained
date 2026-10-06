"""Spectrograms of the game's own mix (--wav), one strip per file, labelled, with its peak and loudest
50 ms: python spec.py OUT.png a.wav b.wav ...  (Seeing what plays, not hearing it.)"""
import sys
import wave
import numpy as np
from PIL import Image, ImageDraw

out = sys.argv[1]
strips = []
for path in sys.argv[2:]:
    with wave.open(path) as w:
        rate = w.getframerate()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, 2).astype(np.float32) / 32768
    mono = data.mean(axis=1)
    n, hop = 2048, 512
    frames = [mono[i:i + n] * np.hanning(n) for i in range(0, max(1, len(mono) - n), hop)]
    S = np.abs(np.fft.rfft(np.array(frames), axis=1)).T + 1e-6
    db = 20 * np.log10(S)
    # Log-frequency rows from 40 Hz to 16 kHz.
    freqs = np.fft.rfftfreq(n, 1 / rate)
    rows = np.geomspace(40, 16000, 200)
    idx = np.clip(np.searchsorted(freqs, rows), 0, len(freqs) - 1)
    img = db[idx][::-1]
    img = np.clip((img + 30) / 70, 0, 1)
    im = Image.fromarray((img * 255).astype(np.uint8)).resize((1200, 200)).convert("RGB")
    win = int(rate * 0.05)
    rms = [np.sqrt(np.mean(mono[i:i + win] ** 2)) for i in range(0, len(mono) - win, win)]
    peak = float(np.max(np.abs(data))) if len(data) else 0
    loud = 20 * np.log10(max(rms) + 1e-9) if rms else -99
    ImageDraw.Draw(im).text((4, 2), f"{path.split(chr(92))[-1].split('/')[-1]}  {len(mono) / rate:.1f}s  peak {peak:.2f}  loudest 50ms {loud:.1f} dBFS", fill=(255, 255, 0))
    strips.append(im)
    print(path, f"peak {peak:.2f} loudest {loud:.1f} dBFS")
sheet = Image.new("RGB", (1200, 204 * len(strips)), (0, 0, 0))
for i, s in enumerate(strips):
    sheet.paste(s, (0, i * 204))
sheet.save(out)
