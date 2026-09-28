#!/usr/bin/env python3
"""A woman's figure, as morph targets on the people's meshes.

    python tools/assets/figure.py        (needs numpy; run after people.py)

Works on the gathered parts in public/assets/people, in their bind space
(metres, Y up, +Z forward), and gives the female body and the clothes worn
over it two shapes the game blends in by the figure slider:

  bust  fuller breasts: each a rounded form (an ellipsoid, its upper slope
        longer and flatter than its lower, the proportion people read as
        natural) joined smoothly to the chest, so the fold beneath and the
        cleavage between come from the join and not from a crease; a little
        weight settles it down and out. Tops keep their offset from the skin
        and hang from the bust rather than wrapping under it.
  hips  a narrower waist and wider hips, on the body and on anything worn
        over the waist.

The chest is sparse (a few hundred vertices), so a rounded shape there would
show its facets: the region is subdivided twice first, every attribute
carried over (weights merged, normals renormalised), neighbouring triangles
split to match so nothing cracks. Normals for each shape are computed from
the shaped surface, welded across UV seams. Unused vertex data (all-white
colours, extra UV sets) is dropped from the meshes rewritten.

Run once per gathering: the files are marked, and a second run stops.
"""
import json
import os
import sys

import numpy as np

DIR = 'public/assets/people'
BODY = 'Superhero_Female_FullBody'
TOPS = ['Female_Peasant_Body', 'Female_Ranger_Body']
BOTTOMS = ['Female_Peasant_Legs', 'Female_Ranger_Legs']

# How far the shapes go at full strength (the slider's "Full"; it runs to
# half as far again).
PROJ = 0.044      # forward, at the apex (m)
RX = 0.086        # each breast's radius across (m)
SAG = 0.02        # the apex settles down...
SPREAD = 0.012    # ...and out
JOIN = 0.02       # softness of the join to the chest (wider over the upper slope)
WAIST = 0.075     # waist taken in (fraction)
HIPS = 0.085      # hips let out (fraction)
SEAT = 0.12       # and behind

CT = {5126: 'f4', 5123: 'u2', 5125: 'u4', 5121: 'u1'}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


class Gltf:
    def __init__(self, name):
        self.name = name
        self.path = f'{DIR}/{name}.gltf'
        with open(self.path) as f:
            self.g = json.load(f)
        self.bin_path = f'{DIR}/{self.g["buffers"][0]["uri"]}'
        with open(self.bin_path, 'rb') as f:
            self.bin = bytearray(f.read())

    def read(self, i):
        a = self.g['accessors'][i]
        bv = self.g['bufferViews'][a['bufferView']]
        n = NC[a['type']]
        dt = np.dtype(CT[a['componentType']]).newbyteorder('<')
        off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        stride = bv.get('byteStride', dt.itemsize * n)
        if stride == dt.itemsize * n:
            arr = np.frombuffer(self.bin, dtype=dt, count=a['count'] * n, offset=off).reshape(a['count'], n)
        else:
            arr = np.stack([np.frombuffer(self.bin, dtype=dt, count=n, offset=off + k * stride) for k in range(a['count'])])
        return arr.astype(np.float64 if a['componentType'] == 5126 else np.int64)

    def write(self, arr, ctype, typ, target=None, minmax=False):
        dt = np.dtype(CT[ctype]).newbyteorder('<')
        data = np.ascontiguousarray(arr.astype(dt)).tobytes()
        while len(self.bin) % 4:
            self.bin.append(0)
        bv = {'buffer': 0, 'byteOffset': len(self.bin), 'byteLength': len(data)}
        if target:
            bv['target'] = target
        self.bin.extend(data)
        self.g['bufferViews'].append(bv)
        acc = {'bufferView': len(self.g['bufferViews']) - 1, 'componentType': ctype, 'count': int(arr.shape[0]), 'type': typ}
        if minmax:
            acc['min'] = [float(v) for v in arr.min(0)]
            acc['max'] = [float(v) for v in arr.max(0)]
        self.g['accessors'].append(acc)
        return len(self.g['accessors']) - 1

    def save(self):
        self.g['buffers'][0]['byteLength'] = len(self.bin)
        with open(self.bin_path, 'wb') as f:
            f.write(self.bin)
        with open(self.path, 'w') as f:
            json.dump(self.g, f, separators=(',', ':'))


class Prim:
    """One triangle list and its vertex attributes, as arrays."""

    def __init__(self, gl, p):
        self.gl, self.p = gl, p
        keep = lambda k: k in ('POSITION', 'NORMAL', 'TEXCOORD_0') or k.startswith(('JOINTS_', 'WEIGHTS_'))
        self.attr = {k: gl.read(v) for k, v in p['attributes'].items() if keep(k)}
        self.types = {k: gl.g['accessors'][v]['componentType'] for k, v in p['attributes'].items() if keep(k)}
        self.tri = gl.read(p['indices']).reshape(-1, 3)

    @property
    def pos(self):
        return self.attr['POSITION']

    def welded(self):
        """An id per vertex shared by every vertex at the same place."""
        q = np.round(self.pos / 1e-5).astype(np.int64)
        _, ids = np.unique(q, axis=0, return_inverse=True)
        return ids.reshape(-1)

    def subdivide(self, region):
        """Split every triangle touching the region into four; neighbours
        sharing a split edge into two or three, so the surface stays whole."""
        wid = self.welded()
        inside = region(self.pos)
        split = set()
        for t in self.tri[inside[self.tri].any(1)]:
            for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                split.add((min(wid[a], wid[b]), max(wid[a], wid[b])))
        n0 = len(self.pos)
        mids, parents = {}, []

        def mid(a, b):
            key = (min(a, b), max(a, b))
            if key not in mids:
                mids[key] = n0 + len(parents)
                parents.append(key)
            return mids[key]

        tris = []
        for a, b, c in self.tri:
            s = [(min(wid[x], wid[y]), max(wid[x], wid[y])) in split for x, y in ((a, b), (b, c), (c, a))]
            n = sum(s)
            if n == 0:
                tris.append((a, b, c))
            elif n == 3:
                ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
                tris += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
            else:
                # Turn the triangle so its split edges come first.
                while not s[0] or (n == 2 and not s[1]):
                    a, b, c = b, c, a
                    s = s[1:] + s[:1]
                if n == 1:
                    ab = mid(a, b)
                    tris += [(a, ab, c), (ab, b, c)]
                else:
                    ab, bc = mid(a, b), mid(b, c)
                    tris += [(ab, b, bc), (a, ab, bc), (a, bc, c)]
        pa = np.array([p[0] for p in parents], dtype=np.int64)
        pb = np.array([p[1] for p in parents], dtype=np.int64)
        for k, v in list(self.attr.items()):
            if k.startswith(('JOINTS_', 'WEIGHTS_')):
                continue
            m = (v[pa] + v[pb]) / 2
            if k == 'NORMAL':
                m /= np.maximum(np.linalg.norm(m, axis=1, keepdims=True), 1e-9)
            self.attr[k] = np.concatenate([v, m])
        self.mix_weights(pa, pb)
        self.tri = np.array(tris, dtype=np.int64)

    def mix_weights(self, pa, pb):
        """A midpoint takes both ends' bone weights; the strongest are kept."""
        sets = sorted(k[len('JOINTS_'):] for k in self.attr if k.startswith('JOINTS_'))
        J = np.concatenate([self.attr[f'JOINTS_{s}'] for s in sets], axis=1)
        W = np.concatenate([self.attr[f'WEIGHTS_{s}'] for s in sets], axis=1)
        slots = J.shape[1]
        nj, nw = np.zeros((len(pa), slots), dtype=np.int64), np.zeros((len(pa), slots))
        for i, (a, b) in enumerate(zip(pa, pb)):
            d = {}
            for v in (a, b):
                for j, w in zip(J[v], W[v]):
                    if w > 0:
                        d[int(j)] = d.get(int(j), 0) + w / 2
            top = sorted(d.items(), key=lambda t: -t[1])[:slots]
            tot = sum(w for _, w in top) or 1
            for s, (j, w) in enumerate(top):
                nj[i, s], nw[i, s] = j, w / tot
        J, W = np.concatenate([J, nj]), np.concatenate([W, nw])
        for si, s in enumerate(sets):
            self.attr[f'JOINTS_{s}'] = J[:, si * 4:si * 4 + 4]
            self.attr[f'WEIGHTS_{s}'] = W[:, si * 4:si * 4 + 4]

    def smooth(self, d, rounds=10):
        """Relax a displacement over the surface: each point moves toward the
        mean of its neighbours' (welded across seams), which irons out steps
        where a shape meets what was modelled."""
        wid = self.welded()
        n = wid.max() + 1
        dw = np.zeros((n, 3))
        cnt = np.zeros(n)
        np.add.at(dw, wid, d)
        np.add.at(cnt, wid, 1)
        dw /= cnt[:, None]
        e = np.concatenate([self.tri[:, [0, 1]], self.tri[:, [1, 2]], self.tri[:, [2, 0]]])
        a, b = wid[e[:, 0]], wid[e[:, 1]]
        deg = np.zeros(n)
        np.add.at(deg, a, 1)
        np.add.at(deg, b, 1)
        for _ in range(rounds):
            acc = np.zeros((n, 3))
            np.add.at(acc, a, dw[b])
            np.add.at(acc, b, dw[a])
            dw = 0.4 * dw + 0.6 * acc / np.maximum(deg, 1)[:, None]
        return dw[wid]

    def normals(self, pos):
        """Smooth normals of a surface, welded across seams."""
        wid = self.welded()
        a, b, c = pos[self.tri[:, 0]], pos[self.tri[:, 1]], pos[self.tri[:, 2]]
        fn = np.cross(b - a, c - a)
        acc = np.zeros((wid.max() + 1, 3))
        for k in range(3):
            np.add.at(acc, wid[self.tri[:, k]], fn)
        n = acc[wid]
        return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)

    def store(self, targets, names):
        gl = self.gl
        at = {}
        for k, v in self.attr.items():
            ct = self.types[k]
            typ = {1: 'SCALAR', 2: 'VEC2', 3: 'VEC3', 4: 'VEC4'}[v.shape[1]]
            at[k] = gl.write(v, ct, typ, 34962, minmax=(k == 'POSITION'))
        self.p['attributes'] = at
        self.p['indices'] = gl.write(self.tri.reshape(-1), 5125 if len(self.attr['POSITION']) > 65535 else 5123, 'SCALAR', 34963)
        self.p['targets'] = [{k: gl.write(v, 5126, 'VEC3', 34962, minmax=(k == 'POSITION')) for k, v in t.items()} for t in targets]
        return names


# ------------------------------------------------------------------ shapes --

def smoothmax(a, b, k):
    h = np.clip(0.5 + 0.5 * (a - b) / k, 0, 1)
    return a * h + b * (1 - h) + k * h * (1 - h)


class Bust:
    """The breasts at full strength: each an ellipsoid set into the chest,
    its front where the fuller apex goes, joined to the body by a soft union
    (a surface inside it is pushed out to it, radially; near its surface the
    push eases in, which makes the fold beneath and the cleavage between)."""

    def __init__(self, body_pos):
        P = body_pos
        R = (P[:, 1] > 1.2) & (P[:, 1] < 1.45) & (np.abs(P[:, 0]) > 0.02) & (np.abs(P[:, 0]) < 0.2) & (P[:, 2] > 0)
        Q = P[R & (P[:, 0] > 0)]
        self.apex = Q[np.argmax(Q[:, 2])]          # (x, y, z), right side
        ax, ay, az = self.apex
        self.front = np.array([ax + SPREAD, ay - SAG, az + PROJ])
        # Radii: across, above (the longer, flatter upper slope), below (the
        # rounder lower), and deep.
        self.rx, self.up, self.down, self.rz = RX, RX * 1.5, RX * 0.92, RX * 0.85
        self.c = self.front - np.array([0, 0, self.rz])
        print(f'  apex {self.apex.round(3)} -> {self.front.round(3)}, centre {self.c.round(3)}')

    def push(self, pos, side, lift):
        """How far each point goes to reach one ellipsoid (grown by `lift`)."""
        c = self.c * np.array([side, 1, 1])
        q = pos - c
        ry = np.where(q[:, 1] > 0, self.up, self.down) + lift
        rad = np.stack([np.full(len(pos), self.rx) + lift, ry, np.full(len(pos), self.rz) + lift], 1)
        u = q / rad
        m = np.linalg.norm(u, axis=1)
        # Depth inside, in metres (roughly), and the soft union's push.
        depth = (1 - m) * rad.mean(1)
        # The upper slope eases into the chest over a longer run.
        k = np.where(q[:, 1] > 0, JOIN * 1.8, JOIN)
        amount = np.where(depth > k, depth, np.where(depth > -k, (depth + k) ** 2 / (4 * k), 0))
        # Outward along the ellipsoid's radial direction, in metres.
        dirn = (u / np.maximum(m, 1e-9)[:, None]) * rad
        dirn /= np.maximum(np.linalg.norm(dirn, axis=1, keepdims=True), 1e-9)
        return dirn * amount[:, None]

    def shape(self, pos, lift=0.0):
        """Where a surface over the chest goes (plus `lift`, a garment's
        distance from the skin, per point)."""
        lift = np.broadcast_to(lift, (len(pos),))
        front = (pos[:, 2] > -0.05) & (pos[:, 1] > 1.0) & (pos[:, 1] < 1.6) & (np.abs(pos[:, 0]) < 0.3)
        d = np.zeros_like(pos)
        for side in (1, -1):
            mine = front & (pos[:, 0] * side > -0.02)
            d[mine] += self.push(pos[mine], side, lift[mine])
        return d

    def drape(self, pos, nrm, body_pos, body_d):
        """A garment over the chest: it moves as the skin beneath it does
        (nearest point of the body in front), spans flat between the breasts
        instead of dipping in, and below them hangs from them before
        meeting the waist. Only what faces forward follows."""
        x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
        d = np.zeros_like(pos)
        for i in range(0, len(pos), 2048):
            sl = slice(i, i + 2048)
            dd = (body_pos[None, :, 0] - x[sl, None]) ** 2 + (body_pos[None, :, 1] - y[sl, None]) ** 2 + 0.25 * (body_pos[None, :, 2] - z[sl, None]) ** 2
            d[sl] = body_d[np.argmin(dd, axis=1)]
        ax, ay = self.front[0], self.front[1]
        full = body_d[:, 2].max()
        # Between the apexes: no lower than the front of them, easing off
        # above and below the apex line.
        between = np.clip(1 - (np.abs(x) - ax * 0.6) / (ax * 0.4), 0, 1)
        level = np.exp(-((y - ay) / np.where(y > ay, 0.07, 0.05)) ** 2)
        bridge = full * 0.85 * between * level
        # Below: hanging from the apex line down to the waist.
        drop = np.clip(1 - (ay - y) / 0.16, 0, 1) * (y < ay)
        col = np.exp(-((np.abs(x) - ax) / 0.08) ** 2) + between
        hang = full * 0.9 * drop ** 1.6 * np.clip(col, 0, 1)
        d[:, 2] = np.maximum(d[:, 2], np.maximum(bridge, hang))
        facing = np.clip((nrm[:, 2] - 0.05) / 0.4, 0, 1)
        return d * facing[:, None]


def hips(pos):
    """Waist in, hips out, seat back: a field over the torso."""
    x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
    torso = np.clip(1 - (np.abs(x) - 0.22) / 0.06, 0, 1)
    waist = np.exp(-((y - 1.1) / 0.075) ** 2) * torso
    hip = np.exp(-((y - 0.93) / 0.1) ** 2) * torso
    d = np.zeros_like(pos)
    d[:, 0] = x * (-WAIST * waist + HIPS * hip)
    d[:, 2] = (z - 0.0) * (-WAIST * 0.6 * waist) + np.where(z < 0, z * SEAT * hip, 0)
    return d


def normal_delta(prim, base, shaped):
    return prim.normals(shaped) - prim.normals(base)


def chest(pos):
    return (np.abs(pos[:, 0]) < 0.25) & (pos[:, 1] > 1.08) & (pos[:, 1] < 1.52) & (pos[:, 2] > -0.03)


def shape_file(name, bust, tops=False, legs=False, body=False):
    gl = Gltf(name)
    if gl.g.get('asset', {}).get('extras', {}).get('figure'):
        sys.exit(f'{name}: already shaped (gather again with people.py first)')
    for mesh in gl.g['meshes']:
        if name == BODY and mesh.get('name') != 'Superhero_Female':
            continue
        for p in mesh['primitives']:
            prim = Prim(gl, p)
            # (Belts barely move and are left as they are.)
            if (body or tops) and 'Belt' not in mesh.get('name', ''):
                for _ in range(2):
                    prim.subdivide(chest)
            base = prim.pos
            if body:
                db = prim.smooth(bust.shape(base))
            elif tops:
                db = prim.smooth(bust.drape(base, prim.attr['NORMAL'], _body[0], _body[1]), 6)
            else:
                db = np.zeros_like(base)
            dh = hips(base)
            targets = [
                {'POSITION': db, 'NORMAL': normal_delta(prim, base, base + db)},
                {'POSITION': dh, 'NORMAL': normal_delta(prim, base, base + dh)},
            ]
            prim.store(targets, None)
            print(f'  {mesh.get("name")}: {len(base)} vertices, bust moves {np.abs(db).max():.3f} m, hips {np.abs(dh).max():.3f} m')
        mesh['weights'] = [0, 0]
        mesh.setdefault('extras', {})['targetNames'] = ['bust', 'hips']
    gl.g.setdefault('asset', {}).setdefault('extras', {})['figure'] = 1
    gl.save()


_body = [None, None]


def compact(name):
    """Rewrite a part's buffer with only the data still referenced (what
    was replaced or dropped goes)."""
    gl = Gltf(name)
    g = gl.g
    # Accessors still read: by primitives, skins and animations.
    refs = []
    for m in g.get('meshes', []):
        for p in m['primitives']:
            refs += [(p['attributes'], k) for k in p['attributes']]
            if 'indices' in p:
                refs.append((p, 'indices'))
            for t in p.get('targets', []):
                refs += [(t, k) for k in t]
    for sk in g.get('skins', []):
        if 'inverseBindMatrices' in sk:
            refs.append((sk, 'inverseBindMatrices'))
    for an in g.get('animations', []):
        for smp in an['samplers']:
            refs += [(smp, 'input'), (smp, 'output')]
    keep = sorted({o[k] for o, k in refs})
    amap = {old: new for new, old in enumerate(keep)}
    g['accessors'] = [g['accessors'][i] for i in keep]
    for o, k in refs:
        o[k] = amap[o[k]]
    used = sorted({a['bufferView'] for a in gl.g['accessors'] if 'bufferView' in a})
    remap, out = {}, bytearray()
    views = []
    for i in used:
        bv = dict(gl.g['bufferViews'][i])
        while len(out) % 4:
            out.append(0)
        start = bv.get('byteOffset', 0)
        chunk = gl.bin[start:start + bv['byteLength']]
        bv['byteOffset'] = len(out)
        out.extend(chunk)
        remap[i] = len(views)
        views.append(bv)
    for a in gl.g['accessors']:
        if 'bufferView' in a:
            a['bufferView'] = remap[a['bufferView']]
    before = len(gl.bin)
    gl.g['bufferViews'], gl.bin = views, out
    gl.save()
    return before - len(out)


def main():
    body = Gltf(BODY)
    mesh = next(m for m in body.g['meshes'] if m.get('name') == 'Superhero_Female')
    pos = body.read(mesh['primitives'][0]['attributes']['POSITION'])
    bust = Bust(pos)
    print(BODY)
    shape_file(BODY, bust, body=True)
    # The shaped body's front, for garments to follow.
    body = Gltf(BODY)
    mesh = next(m for m in body.g['meshes'] if m.get('name') == 'Superhero_Female')
    p = mesh['primitives'][0]
    bp, bd = body.read(p['attributes']['POSITION']), body.read(p['targets'][0]['POSITION'])
    keep = chest(bp) & (bp[:, 2] > 0.02)
    _body[0], _body[1] = bp[keep], bd[keep]
    for t in TOPS:
        print(t)
        shape_file(t, bust, tops=True)
    for b in BOTTOMS:
        print(b)
        shape_file(b, bust, legs=True)
    # Every part, shaped or not, loses the data nothing reads any more.
    saved = sum(compact(f[:-5]) for f in sorted(os.listdir(DIR)) if f.endswith('.gltf'))
    print(f'compacted: {saved / 1e6:.1f} MB freed')


main()
