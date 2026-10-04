"""Painted frames made to tile (UiArt.Slice Tile): Godot repeats a frame's
edges along their length and its centre both ways, so each must follow on
from itself, and from the corners either side, without a seam.

For an edge strip S between corners A and B (in reading order A | S | B):
  - S's tail is cross-faded into A's tail, so the last column of S leads
    into S's own first column (as A's last column did in the painting);
  - B's head is cross-faded from S's head, so B starts as S did after A.
Both blends are between pieces of the same strap, so they do not show.
The centre is made periodic by the offset-and-blend method (blended with
itself shifted half a period, through a window that is one in the middle).
"""
from __future__ import annotations

import numpy as np


def _ramp(n):
    t = np.linspace(0, 1, n, dtype=np.float32)
    return t * t * (3 - 2 * t)


def offset_blend(c):
    """A texture made periodic: blended with itself shifted half a period through a
    window that is one in the middle (for patches with no edge features)."""
    h, w = c.shape[:2]
    shifted = np.roll(np.roll(c, h // 2, axis=0), w // 2, axis=1)
    wy = np.sin(np.linspace(0, np.pi, h, dtype=np.float32)) ** 2
    wx = np.sin(np.linspace(0, np.pi, w, dtype=np.float32)) ** 2
    win = (wy[:, None] * wx[None, :])[..., None]
    return c * win + shifted * (1 - win)


def periodic_centre(c):
    """The centre made to repeat both ways: its own middle (away from the border's shading,
    which would otherwise be wrapped into the middle as a cross) made periodic and laid
    two by two."""
    h, w = c.shape[:2]
    ph, pw = (h + 1) // 2, (w + 1) // 2
    y0, x0 = (h - ph) // 2, (w - pw) // 2
    patch = offset_blend(c[y0:y0 + ph, x0:x0 + pw])
    big = np.tile(patch, (2, 2, 1))
    # Phase it so the patch starts where the centre starts.
    return big[:h, :w]


def tileable(img, margins, blend=None):
    """img: HxWxC float (file pixels); margins (l, t, r, b) in file pixels."""
    out = img.copy()
    H, W = img.shape[:2]
    l, t, r, b = margins
    P, Q = W - l - r, H - t - b
    D = blend or max(8, min(P, Q) // 6)
    a = _ramp(D)
    # Top and bottom strips: horizontal blends.
    for (y0, y1) in ((0, t), (H - b, H)):
        A_tail = img[y0:y1, l - D:l]
        S_head = img[y0:y1, l:l + D]
        # S's tail into A's tail.
        out[y0:y1, l + P - D:l + P] = img[y0:y1, l + P - D:l + P] * (1 - a)[None, :, None] + A_tail * a[None, :, None]
        # B's head from S's head.
        out[y0:y1, W - r:W - r + D] = S_head * (1 - a)[None, :, None] + img[y0:y1, W - r:W - r + D] * a[None, :, None]
    # Left and right strips: vertical blends.
    for (x0, x1) in ((0, l), (W - r, W)):
        A_tail = img[t - D:t, x0:x1]
        S_head = img[t:t + D, x0:x1]
        out[t + Q - D:t + Q, x0:x1] = img[t + Q - D:t + Q, x0:x1] * (1 - a)[:, None, None] + A_tail * a[:, None, None]
        out[H - b:H - b + D, x0:x1] = S_head * (1 - a)[:, None, None] + img[H - b:H - b + D, x0:x1] * a[:, None, None]
    out[t:t + Q, l:l + P] = periodic_centre(img[t:t + Q, l:l + P])
    return out
