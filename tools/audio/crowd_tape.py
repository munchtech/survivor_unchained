"""Her heavy hit over the crowd, measured on a game tape (F1, ARPG_FUN P0 item 2's proof).

  python tools/audio/crowd_tape.py TAPE.wav LOG.txt [--dense 50]

The run: the game with `--wav TAPE.wav --stems --kill-trace` (Synth.cs writes TAPE_sfx.wav ... and TAPE_lead.wav, the lead
voices alone; BattleFx prints `[kill-trace] tape=S kills=K heavy=H living=N` a frame that kills or lands a heavy blow).
For each heavy-blow frame: the lead stem against the rest of the effects (sfx minus lead) in the 0-80 ms after it, broadband
and in the 1-6 kHz band the ear finds a hit in; "dying" = kills within 0.5 s either side. Prints the spread, the dense
moments' numbers (dying >= --dense, else the ten densest) and the most living at once.
"""
import argparse, re, sys
import numpy as np
from scipy import signal
from scipy.io import wavfile

ap = argparse.ArgumentParser()
ap.add_argument("tape"); ap.add_argument("log"); ap.add_argument("--dense", type=int, default=50)
a = ap.parse_args()


def load(p):
    r, x = wavfile.read(p)
    x = x.astype(np.float64) / 32768.0
    return r, x.mean(axis=1) if x.ndim == 2 else x


base = a.tape[:-4] if a.tape.lower().endswith(".wav") else a.tape
rate, master = load(a.tape)
_, sfx = load(base + "_sfx.wav")
_, lead = load(base + "_lead.wav")
n = min(len(sfx), len(lead), len(master))
sfx, lead, master = sfx[:n], lead[:n], master[:n]
rest = sfx - lead
sos = signal.butter(4, [1000, 6000], btype="band", fs=rate, output="sos")
lead_b, rest_b = signal.sosfilt(sos, lead), signal.sosfilt(sos, rest)

rows = []
for m in re.finditer(r"\[kill-trace\] tape=([\d.]+) kills=(\d+) heavy=(\d+) living=(\d+)", open(a.log, encoding="utf-8", errors="replace").read()):
    rows.append((float(m[1]), int(m[2]), int(m[3]), int(m[4])))
if not rows:
    sys.exit("no [kill-trace] lines (run with --kill-trace)")
ts = np.array([r[0] for r in rows]); ks = np.array([r[1] for r in rows])


def db(x):
    return 10 * np.log10(max(float(np.mean(x * x)), 1e-14))


out = []
for t, k, h, liv in rows:
    if h == 0:
        continue
    i0, i1 = int(t * rate), int((t + 0.08) * rate)
    if i1 > n or i1 - i0 < 10:
        continue
    if np.max(np.abs(lead[i0:i1])) < 1e-4:
        continue  # (no lead voice sounded: a gate took it; counted below)
    dying = int(ks[(ts >= t - 0.5) & (ts <= t + 0.5)].sum())
    out.append(dict(t=t, dying=dying, living=liv, snr=db(lead[i0:i1]) - db(rest[i0:i1]), snr_b=db(lead_b[i0:i1]) - db(rest_b[i0:i1]),
                    master=db(master[i0:i1])))
heavy_frames = sum(1 for r in rows if r[2] > 0)
print(f"frames traced {len(rows)}, heavy-blow frames {heavy_frames}, with a lead voice sounding {len(out)}; most living at once {max(r[3] for r in rows)}; "
      f"most dying in 1 s {max(int(ks[(ts >= t - 0.5) & (ts <= t + 0.5)].sum()) for t in ts)}")
if not out:
    sys.exit(0)
s = np.array([o["snr"] for o in out]); sb = np.array([o["snr_b"] for o in out])
print(f"her heavy hit over the rest of the effects, 0-80 ms: broadband median {np.median(s):+.1f} dB (p10 {np.percentile(s, 10):+.1f}), "
      f"1-6 kHz median {np.median(sb):+.1f} dB (p10 {np.percentile(sb, 10):+.1f})")
dense = [o for o in out if o["dying"] >= a.dense] or sorted(out, key=lambda o: -o["dying"])[:10]
label = f"dying >= {a.dense}" if any(o["dying"] >= a.dense for o in out) else "the ten densest (none reached --dense)"
print(f"{label}: {len(dense)} hits")
for o in sorted(dense, key=lambda o: o["t"])[:20]:
    print(f"  t={o['t']:7.2f}s dying {o['dying']:3d} living {o['living']:3d}  broadband {o['snr']:+5.1f} dB  1-6 kHz {o['snr_b']:+5.1f} dB  master {o['master']:6.1f} dBFS")
d = np.array([o["snr_b"] for o in dense])
print(f"  dense 1-6 kHz median {np.median(d):+.1f} dB, worst {d.min():+.1f} dB")
