"""Low Ford's river banks, sculpted over the exported zone (C03 env, judge C03: 'both banks near-straight lines
meeting at a vanishing point, the width never changes, and the water stops in a flat horizontal edge').

  python tools/assets/zone_banks.py [--dry]

The export (tools/godot/export_zone.mjs) laid the river at a constant distance either side of riverZ(x) (lowford.ts),
straight through the west valley wall to the zone's edge. This warps the zone's data in place, once:
  - each bank wiggles on its own (+-2-4 m over 10-20 m), outside the ford (|x| > 17; none inside |x| < 10), so the
    width changes and no bank runs straight; the warp fades out 18 m from the channel;
  - west of x = -68 the river bends south (-z) 22 m over 32 m (up to 46 deg), into the gorge behind the cliff, so its
    end is out of sight, not a horizontal edge at the zone's rim; the water's quad is widened to hold it;
  - the heights (heights.bin), the paint (splat.png: the mud follows the new banks) and every flora copy's height move
    together; a copy that would stand in the water (not a rock) is dropped;
  - each bank, both reaches, gains rocks (E5's fieldrock set, through the kit's Rock_Medium pieces), hazel and bracken
    clumps at its new waterline, every 3.5-7 m, as flora groups appended to flora.json/bin.
Refuses to run twice (the water's quad already widened).
"""
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

Z = Path(__file__).resolve().parents[2] / 'godot/data/zones/lowford'
N, SIZE, HALF = 261, 260.0, 130.0
WATER_Y = -1.05
QUAD_Z0 = -84.0
# (--bend: the west reach bent 22 m south. Off by default: the play camera's 'stones' set has a frame in that gorge
# (c03e_stones_o_03), which the bend rebuilt; it needs that spot kept clear first)
BEND = -22.0 if '--bend' in sys.argv else 0.0
dry = '--dry' in sys.argv


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def river_z(x):
    return -44 + np.sin(x * 0.032) * 4.5 + np.sin(x * 0.011 + 1) * 3


def lat(i, k):
    """A hash in [0, 1) per lattice point i and stream k."""
    v = (np.asarray(i, dtype=np.int64) * 73856093 ^ (k * 19349663)) & 0x7fffffff
    return (v % 10007) / 10007.0


def vnoise(x, s, k):
    f = np.asarray(x, dtype=float) / s
    i = np.floor(f).astype(np.int64)
    u = f - i
    u = u * u * (3 - 2 * u)
    return lat(i, k) * (1 - u) + lat(i + 1, k) * u


def wiggle(x, k):
    """A bank's offset outward (m): two octaves, 10-20 m swings, -2 .. +4, none at the ford."""
    w = (vnoise(x, 13.0, k) - 0.5) * 7.0 + (vnoise(x, 5.5, k + 1) - 0.5) * 2.4 + 0.6
    return np.clip(w, -2.0, 4.0) * smooth(10, 17, np.abs(x))


def bend(x):
    """The west reach's bend south (m of z), from x = -68 to -100."""
    return BEND * smooth(-68, -100, x)


def src_z(x, z):
    """Where the exported zone had what now stands at (x, z)."""
    zc0 = river_z(x)
    B = bend(x)
    zc = zc0 + B
    d = z - zc
    w = np.where(d > 0, wiggle(x, 101), wiggle(x, 202))
    T = 1 - smooth(9, 18, np.abs(d))
    z1 = zc + d - np.sign(d) * w * T          # the bank pushed out by w (in by -w)
    # the bend: a shear of the strip holding the new and the old channel (piecewise linear, monotonic)
    r = z1 - zc0
    kz = np.stack([np.full_like(B, -1e3), B - 30, B - 14, np.full_like(B, 14.0), 14 - B + 4, np.full_like(B, 1e3)])
    ks = np.stack([np.full_like(B, -1e3), B - 30, np.full_like(B, -14.0), 14 - B, 18 - B, np.full_like(B, 1e3)])
    out = np.empty_like(r)
    for a in range(5):
        lo, hi = kz[a], kz[a + 1]
        m = (r >= lo) & (r < hi) if a < 4 else (r >= lo)
        t = (r - lo) / np.maximum(hi - lo, 1e-6)
        out = np.where(m, ks[a] + t * (ks[a + 1] - ks[a]), out)
    return zc0 + out


def sample(grid, x, z, res, size):
    """Bilinear, grid rows from -z, columns from -x."""
    fx = (x + size / 2) / size * (res - 1)
    fz = (z + size / 2) / size * (res - 1)
    fx = np.clip(fx, 0, res - 1.0001)
    fz = np.clip(fz, 0, res - 1.0001)
    i, j = np.floor(fz).astype(int), np.floor(fx).astype(int)
    u, v = fx - j, fz - i
    g = grid
    if g.ndim == 3:
        u, v = u[..., None], v[..., None]
    return (g[i, j] * (1 - u) * (1 - v) + g[i, j + 1] * u * (1 - v) + g[i + 1, j] * (1 - u) * v + g[i + 1, j + 1] * u * v)


def main():
    wbin = (Z / 'water.bin').read_bytes()
    pos = list(struct.unpack_from('<12f', wbin, 0))
    if min(pos[2::3]) <= QUAD_Z0 or (Z / '.banks_applied').exists():
        sys.exit('zone_banks: already applied')
    H0 = np.fromfile(Z / 'heights.bin', dtype='<f4').reshape(N, N).astype(np.float64)
    ax = np.linspace(-HALF, HALF, N)
    X, Zg = np.meshgrid(ax, ax)
    H1 = sample(H0, X, src_z(X, Zg), N, SIZE)
    def ground(h, x, z):
        return sample(h, np.asarray(x, float), np.asarray(z, float), N, SIZE)

    # the paint
    sp = Image.open(Z / 'splat.png')
    S0 = np.asarray(sp).astype(np.float64)
    R = S0.shape[0]
    a2 = (np.arange(R) + 0.5) / R * SIZE - HALF
    SX, SZ = np.meshgrid(a2, a2)
    S1 = sample(S0, SX, src_z(SX, SZ), R, SIZE)

    # the flora: heights follow, a copy in the water dropped (rocks kept)
    meta = json.loads((Z / 'flora.json').read_text())
    fb = np.fromfile(Z / 'flora.bin', dtype='<f4').reshape(-1, 12).copy()
    out_meta, out_bin, at, dropped = [], [], 0, 0
    ZS = np.linspace(-HALF - 40, HALF + 40, 2401)
    for g in meta:
        t = fb[at:at + g['count']]
        at += g['count']
        x, z0 = t[:, 9].astype(float), t[:, 11].astype(float)
        # (each copy travels with its ground: where the warp took the ground it stood on, so the gorge's cliff
        # rocks stay on its walls)
        z = np.array([np.interp(zo, src_z(np.full_like(ZS, xx), ZS), ZS) for xx, zo in zip(x, z0)])
        t[:, 11] = z
        t[:, 10] += ground(H1, x, z) - ground(H0, x, z0)
        keep = (ground(H1, x, z) > WATER_Y + 0.08) | (g['kind'] in ('rock', 'boulder', 'cliff', 'pebble'))
        dropped += int((~keep).sum())
        t = t[keep]
        if len(t):
            out_meta.append(dict(g, count=int(len(t))))
            out_bin.append(t)
    tmpl = {}
    for g in meta:
        tmpl.setdefault((g['kind'], g['piece']), g)

    # the banks' rocks and clumps, at each bank's new waterline
    rng = np.random.default_rng(31)
    add = {}
    nb = {1: 0, -1: 0}
    for x0, x1 in ((-100.0, -16.0), (16.0, 75.0)):
        for side in (1, -1):
            x = x0 + rng.uniform(0, 3)
            while x < x1:
                zc = river_z(x) + bend(x)
                # walk out from the channel's middle to the first dry ground
                d = 1.5
                while d < 20 and ground(H1, x, zc + side * d) < WATER_Y:
                    d += 0.25
                if d < 20:
                    roll = rng.random()
                    if roll < 0.5:
                        kind, piece = 'rock', f'Rock_Medium_{1 + int(rng.integers(0, 3))}'
                        dd = d + rng.uniform(-1.0, 0.4)        # rocks stand in the shallows and on the lip
                        s = rng.uniform(0.7, 1.9) if rng.random() < 0.8 else rng.uniform(2.0, 2.8)
                        sink = 0.12
                    elif roll < 0.8:
                        kind, piece = 'bush', 'Bush_Common'
                        dd = d + rng.uniform(0.6, 1.8)
                        s = rng.uniform(0.6, 1.1)
                        sink = 0.05
                    else:
                        kind, piece = 'fern', rng.choice(['Fern_1', 'Plant_1_Big'])
                        dd = d + rng.uniform(0.3, 1.2)
                        s = rng.uniform(0.8, 1.4)
                        sink = 0.0
                    if kind == 'fern' and piece == 'Plant_1_Big':
                        kind = 'plant'
                    g = tmpl.get((kind, piece)) or tmpl.get(('fern', 'Fern_1'))
                    zz = zc + side * dd
                    y = float(ground(H1, x, zz))
                    if kind != 'rock' and y < WATER_Y + 0.08:
                        x += rng.uniform(1.0, 2.0)
                        continue
                    yaw = rng.uniform(0, math.tau)
                    sx, sy = g['sx'] * s, g['sy'] * s
                    c, sn = math.cos(yaw), math.sin(yaw)
                    m = [c * sx, 0, -sn * sx, 0, sy, 0, sn * sx, 0, c * sx, x, y - sink * s, zz]
                    add.setdefault((g['kind'], g['piece']), []).append(m)
                    nb[side] += 1
                x += rng.uniform(3.5, 7.0)
    # the bend's banks (x -66 .. -104): boulders 1.6-3 at the waterline every 2.5-4 m, half in the water, so the far
    # bank the camera sees across the bend is broken, not a level line
    for side in (1, -1):
        x = -66.0 - rng.uniform(0, 2)
        while x > -104:
            zc = river_z(x) + bend(x)
            d = 1.5
            while d < 20 and ground(H1, x, zc + side * d) < WATER_Y:
                d += 0.25
            if d < 20:
                g = tmpl[('boulder', f'Rock_Medium_{1 + int(rng.integers(0, 3))}')]
                s = rng.uniform(1.6, 3.0) if side == 1 else rng.uniform(1.0, 2.2)
                zz = zc + side * (d + rng.uniform(-1.2, 0.3))
                y = float(ground(H1, x, zz))
                yaw = rng.uniform(0, math.tau)
                c, sn = math.cos(yaw), math.sin(yaw)
                sx, sy = g['sx'] * s, g['sy'] * s
                add.setdefault((g['kind'], g['piece']), []).append([c * sx, 0, -sn * sx, 0, sy, 0, sn * sx, 0, c * sx, x, y - 0.2 * s, zz])
                nb[side] += 1
            x -= rng.uniform(2.5, 4.0)
    for (kind, piece), ms in add.items():
        g = tmpl.get((kind, piece))
        out_meta.append(dict(g, count=len(ms)))
        out_bin.append(np.array(ms, dtype='<f4'))

    # the water's quad widened to hold the bend
    pos2 = pos[:]
    for i in range(4):
        if pos2[i * 3 + 2] < -40:
            pos2[i * 3 + 2] = QUAD_Z0
    fl = list(struct.unpack_from('<8f', wbin, 48))
    for i in range(4):
        if fl[i * 2 + 1] < -40:
            fl[i * 2 + 1] = QUAD_Z0
    wbin2 = struct.pack('<12f', *pos2) + struct.pack('<8f', *fl) + wbin[80:]

    wet0, wet1 = (H0 < WATER_Y), (H1 < WATER_Y)
    ford = np.abs(X) < 10
    print(f'heights: max change {np.abs(H1 - H0).max():.2f} m; at the ford (|x|<10) {np.abs(H1 - H0)[ford].max():.4f} m; '
          f'wet cells {wet0.sum()} -> {wet1.sum()}')
    for xx in (-90, -60, -40, -25, 25, 40, 55):
        j = xx + 130
        col = np.where(wet1[:, j])[0]
        print(f'  x {xx}: water z {ax[col.min()]:.0f} .. {ax[col.max()]:.0f} (width {len(col)})' if len(col) else f'  x {xx}: dry')
    print(f'flora: {dropped} copies dropped (in the water); bank pieces added north {nb[1]}, south {nb[-1]}; groups {len(meta)} -> {len(out_meta)}')
    if dry:
        return
    H1.astype('<f4').tofile(Z / 'heights.bin')
    Image.fromarray(np.clip(np.round(S1), 0, 255).astype(np.uint8), sp.mode).save(Z / 'splat.png')
    (Z / 'flora.json').write_text(json.dumps(out_meta, indent=1) + '\n')
    np.concatenate(out_bin).astype('<f4').tofile(Z / 'flora.bin')
    if BEND:
        (Z / 'water.bin').write_bytes(wbin2)
    (Z / '.banks_applied').write_text("zone_banks")
    print('written')


if __name__ == '__main__':
    main()
