"""Flicker in motion: what alternates from frame to frame once the camera's movement is taken out.
    python flick.py TAG [TAG ...]
Three consecutive frames, the second and third lined up on the first (phase correlation, Fourier
shift), tile by tile over the ground away from her: |a - 2b + c|. Steady motion (the camera's
drift, grass swaying in the wind) is near-linear over two frames at 164 Hz and cancels; crawling
edges, popping blades and noise do not. Also the share of pixels flickering by more than 8/255."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import crops as C  # noqa: E402
from mres import T, shift_of, fshift  # noqa: E402


def run(tag):
    fs = C.frames(tag)
    if len(fs) < 3:
        return None
    ims = [C.load(f).mean(axis=2) for f in fs]
    H, W = ims[0].shape
    c = C.her_at(fs[0], C.load(fs[0]))
    vals, hot, grads = [], [], []
    m = 16
    for i in range(len(ims) - 2):
        a, b, cc = ims[i], ims[i + 1], ims[i + 2]
        # (Below the tips' text, left of the journal's: an overlay standing still over a moving
        # world is no flicker, but one shift cannot describe it.)
        for y in range(int(H * 0.28), int(H * 0.78) - T, T):
            for x in range(int(W * 0.05), int(W * 0.75) - T, T):
                if abs(x + T / 2 - c[0]) < H * 0.16 and abs(y + T / 2 - c[1]) < H * 0.2:
                    continue
                ta, tb, tc = a[y:y + T, x:x + T], b[y:y + T, x:x + T], cc[y:y + T, x:x + T]
                if ta.std() < 2:
                    continue
                d1 = shift_of(ta, tb)
                d2 = shift_of(ta, tc)
                if min(d1[2], d2[2]) < 0.2:
                    continue
                tb2 = fshift(tb, -d1[0], -d1[1])
                tc2 = fshift(tc, -d2[0], -d2[1])
                dd = np.abs(ta - 2 * tb2 + tc2)[m:-m, m:-m]
                core = ta[m:-m, m:-m]
                vals.append(dd.mean())
                hot.append((dd > 16).mean())
                grads.append(np.abs(np.diff(core, axis=0)).mean() + np.abs(np.diff(core, axis=1)).mean())
    # Medians over tiles: a tile one shift cannot describe (a near tree's parallax against the
    # ground) is no flicker, and a minority.
    vals, grads = np.array(vals), np.array(grads)
    return np.median(vals), np.median(hot) * 100, np.median(grads), len(vals)


if __name__ == "__main__":
    print(f"{'run':16s} {'flicker':>8s} {'hot %':>6s} {'ground grad':>12s} {'tiles':>6s}   (medians over tiles)")
    for t in sys.argv[1:]:
        r = run(t)
        if r:
            print(f"{t:16s} {r[0]:8.3f} {r[1]:6.3f} {r[2]:12.3f} {r[3]:6d}")
