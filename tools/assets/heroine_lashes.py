"""Her lashes painted, hair by hair, onto her lash cards (heroine_head.py's HeroineLashes: four cards, a grid each, rows
from her lid's edge outward, columns along it): godot/art/people/head_tex/heroine_lashes.png.

    blender -b tools/comfy/out/heroes/heroine_built.blend --python tools/assets/heroine_lashes.py [-- OUT.png]

MakeHuman's lash paint (eyelashes03) was a dense black band with long winged clumps at the outer corners, cut hard
by the cards' alpha: in close-up the surest sign of a render on her face. Real lashes, seen from a portrait's
distance, are a soft dark line at the lid's edge thinning out into separate fine tips: upper lashes about a hundred
and ten to an eye in two or three rows, short at the inner corner, longest a little past the middle (about 10 mm),
tapered from a tenth of a millimetre to nothing, curving out and toward the outer corner, a few gathered in twos and
threes; lower lashes a third as many, finer, 3 to 6 mm. Their colour is a dark brown, lighter toward the tips (pure
black read as a hole). Each lash is drawn in the card's own measure (millimetres along her lid and out from it, from
the cards' points), four times over and averaged, so its edge is soft as a hair's is.
"""
import math
import os
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
OUT = os.path.join(ROOT, "godot", "art", "people", "head_tex", "heroine_lashes.png")
SIZE = 1024                     # the paint's pixels across (the old one's 512 left a lash two texels wide at the root)
SS = 4                          # drawn at four times that, averaged down
SEED = 23

# Upper and lower lashes: how many to an eye; length (mm) along her lid from its inner corner (0) to its outer (1);
# width at the root (mm); how far they lean toward the outer corner (degrees, along the lid); how deep the rows of
# roots go behind the lid's edge (mm); opacity.
# (10 October, a judge: the first paint, 128 lashes a tenth of a millimetre wide, carried 13% of MakeHuman's ink
# and was gone by the mip the Look samples: her lids read bare. Now as many as read at the Look, in clumps of three
# to five, wide enough at the root to hold four to six texels, over a near-opaque root band: the lash line.)
UPPER = dict(count=300, length=((0.0, 4.2), (0.18, 6.6), (0.45, 8.6), (0.72, 10.0), (0.9, 9.8), (1.0, 8.6)),
             width=0.28, lean=((0.0, -3.0), (0.3, 2.0), (0.7, 13.0), (0.9, 16.0), (1.0, 10.0)), rows=0.6, alpha=1.0,
             start=0.04, end=0.97, clump=0.27, band=(0.42, 0.92))
LOWER = dict(count=48, length=((0.0, 2.2), (0.3, 3.6), (0.65, 5.2), (0.9, 5.8), (1.0, 5.0)),
             width=0.13, lean=((0.0, 0.0), (0.5, 6.0), (0.9, 10.0), (1.0, 6.0)), rows=0.45, alpha=0.7,
             start=0.12, end=0.95, clump=0.45, band=(0.22, 0.6))
ROOT_COL = np.array([0.105, 0.075, 0.062])      # (sRGB 0 to 1: a dark brown at the root)
TIP_COL = np.array([0.215, 0.165, 0.135])       # (lighter and browner toward the tip)


def curve(points, x):
    xs, ys = zip(*points)
    return np.interp(x, xs, ys)


def card_grids():
    """Each lash card as a grid (rows from the lid's edge out, columns along it), its UVs and its points (mm), from
    HeroineLashes in the open blend; with whether it is an upper card and which way along it is inward."""
    import bpy
    from collections import defaultdict
    lash = bpy.data.objects["HeroineLashes"]
    me = lash.data
    uvl = me.uv_layers.active.data
    mw = np.array(lash.matrix_world)
    adj = defaultdict(set)
    uv_of, co_of = {}, {}
    for p in me.polygons:
        keys = [(p.vertices[i], round(uvl[li].uv[0], 5), round(uvl[li].uv[1], 5)) for i, li in enumerate(p.loop_indices)]
        for i, k in enumerate(keys):
            uv_of[k] = np.array(uvl[p.loop_indices[i]].uv[:])
            co_of[k] = (mw @ np.r_[np.array(me.vertices[k[0]].co[:]), 1.0])[:3] * 1000.0
            adj[k] |= {keys[(i + 1) % len(keys)], keys[(i - 1) % len(keys)]}
    eyes = bpy.data.objects["HeroineEyes"]
    V = np.array([eyes.matrix_world @ v.co for v in eyes.data.vertices]) * 1000.0
    centres = [V[V[:, 0] > 0].mean(0), V[V[:, 0] <= 0].mean(0)]
    seen, cards = set(), []
    for k in adj:
        if k in seen:
            continue
        comp, stack = [], [k]
        seen.add(k)
        while stack:
            a = stack.pop()
            comp.append(a)
            for b in adj[a] - seen:
                seen.add(b)
                stack.append(b)
        cards.append(comp)
    grids = []
    for comp in cards:
        corners = [c for c in comp if len(adj[c]) == 2]
        edge = {c for c in comp if len(adj[c]) < 4}

        def side(a, nxt):
            path, prev, cur = [a], a, nxt
            while True:
                path.append(cur)
                if cur in corners:
                    return path
                step = [b for b in adj[cur] if b in edge and b != prev and b not in path]
                if not step:
                    return path
                prev, cur = cur, step[0]
        s1, s2 = (side(corners[0], b) for b in adj[corners[0]])
        rows = [max(s1, s2, key=len)]
        used = set(rows[0])
        while len(rows) < len(min(s1, s2, key=len)):
            nxt = [next(iter(adj[p] - used)) for p in rows[-1]]
            rows.append(nxt)
            used |= set(nxt)
        co = np.array([[co_of[k] for k in r] for r in rows])
        uv = np.array([[uv_of[k] for k in r] for r in rows])
        eye = centres[0] if co[..., 0].mean() > 0 else centres[1]
        if np.linalg.norm(co[-1] - eye, axis=1).mean() < np.linalg.norm(co[0] - eye, axis=1).mean():
            co, uv = co[::-1], uv[::-1]                               # (root row first)
        if abs(co[0, 0, 0]) > abs(co[0, -1, 0]):
            co, uv = co[:, ::-1], uv[:, ::-1]                         # (inner corner first)
        upper = co[..., 2].mean() > eye[2]
        grids.append({"co": co, "uv": uv, "upper": bool(upper)})
    return grids


def paint(grids, size=SIZE, ss=SS, seed=SEED):
    """The lashes drawn on every card (an RGBA array, rows from the top)."""
    from PIL import Image, ImageChops, ImageDraw
    big = size * ss
    alpha = Image.new("L", (big, big), 0)
    colour = Image.new("RGB", (big, big), tuple(int(v * 255) for v in ROOT_COL))
    rng = np.random.default_rng(seed)

    def draw_lash(p, widths, fades, cols):
        """One lash (its points in big pixels) laid over the rest: its cover the greater of its own and what is
        there (crossing lashes don't cut each other), its colour where it covers."""
        x0, y0 = np.floor(p.min(0) - widths.max() - 2).astype(int)
        x1, y1 = np.ceil(p.max(0) + widths.max() + 2).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, big), min(y1, big)
        if x1 <= x0 or y1 <= y0:
            return
        la = Image.new("L", (x1 - x0, y1 - y0), 0)
        lc = Image.new("RGB", (x1 - x0, y1 - y0), 0)
        d1, d2 = ImageDraw.Draw(la), ImageDraw.Draw(lc)
        q = p - np.array([x0, y0])
        for j in range(len(q) - 1):
            seg = [tuple(q[j]), tuple(q[j + 1])]
            w = int(round(widths[j]))
            d1.line(seg, fill=int(255 * fades[j]), width=w)
            d2.line(seg, fill=tuple(int(c * 255) for c in cols[j]), width=w + 2)
            # (round joints, so a curving lash has no notches)
            r = widths[j] / 2
            d1.ellipse([q[j + 1][0] - r, q[j + 1][1] - r, q[j + 1][0] + r, q[j + 1][1] + r], fill=int(255 * fades[j]))
        box = (x0, y0, x1, y1)
        alpha.paste(ImageChops.lighter(alpha.crop(box), la), box)
        colour.paste(Image.composite(lc, colour.crop(box), la.point(lambda a: 255 if a > 8 else 0)), box)
    for g in grids:
        co, uv = g["co"], g["uv"]
        nr, nc = co.shape[:2]
        spec = UPPER if g["upper"] else LOWER
        # (the card's own measure: along the lid in mm at the root row, and out from it, column by column)
        along = np.r_[0, np.cumsum(np.linalg.norm(np.diff(co[0], axis=0), axis=1))]
        out_mm = np.c_[np.zeros(nc), np.cumsum(np.linalg.norm(np.diff(co, axis=0), axis=2), axis=0).T]   # (nc, nr)

        def col_at(a_mm):
            """The card's column (fractional) a_mm along her lid's edge from its inner end."""
            return np.interp(a_mm, along, np.arange(nc))

        def at(a_mm, t_mm):
            """UV pixels (big) of a point a_mm along the lid from its inner end and t_mm out from its edge."""
            c = np.clip(col_at(a_mm), 0, nc - 1)
            c0 = np.clip(np.floor(c).astype(int), 0, nc - 2)
            fc = c - c0
            prof = out_mm[c0] * (1 - fc)[..., None] + out_mm[c0 + 1] * fc[..., None]       # (rows' mm out, here)
            r = np.array([np.interp(tm, pr, np.arange(nr)) for tm, pr in zip(np.atleast_1d(t_mm), np.atleast_2d(prof))])
            r0 = np.clip(np.floor(r).astype(int), 0, nr - 2)
            fr = r - r0
            q = (uv[r0, c0] * ((1 - fr) * (1 - fc))[:, None] + uv[r0, c0 + 1] * ((1 - fr) * fc)[:, None]
                 + uv[r0 + 1, c0] * (fr * (1 - fc))[:, None] + uv[r0 + 1, c0 + 1] * (fr * fc)[:, None])
            return np.c_[q[:, 0] * big, (1 - q[:, 1]) * big]
        lid_len = along[-1]
        n = spec["count"]
        # (roots spread evenly along the lid, each jittered within its share, sparser at the inner end, where lashes
        # are few: random roots left bald gaps and bunches)
        grid_s = np.linspace(0, 1, 200)
        dens = np.interp(grid_s, (0.0, 0.25, 1.0), (0.5, 1.0, 1.0))
        cdf = np.r_[0, np.cumsum((dens[1:] + dens[:-1]) / 2)]
        cdf /= cdf[-1]
        u = np.interp((np.arange(n) + rng.uniform(0.2, 0.8, n)) / n, cdf, grid_s)
        u = spec["start"] + (spec["end"] - spec["start"]) * u
        clump = np.cumsum(rng.uniform(0, 1, n) < spec["clump"])           # (gathered: threes to fives above)
        # The lash line: a band along the lid's edge, near opaque, its width wavering, where the roots crowd.
        bw, ba = spec["band"]
        m = 160
        a_b = np.linspace(spec["start"], spec["end"], m) * lid_len
        t_b = 0.12 + 0.05 * np.sin(np.linspace(0, 9.0, m) + rng.uniform(0, 6.3))
        p_b = at(a_b, t_b)
        mm_b = np.linalg.norm(np.diff(p_b, axis=0), axis=1).sum() / max(a_b[-1] - a_b[0], 1e-3)
        ends = np.minimum(1.0, np.minimum(np.linspace(0, 1, m - 1), np.linspace(1, 0, m - 1)) / 0.08)   # (tapered ends)
        w_b = np.maximum(bw * mm_b * (0.8 + 0.2 * np.sin(np.linspace(0, 23.0, m - 1))) * ends, 0.6 * ss / 4)
        draw_lash(p_b, w_b, ba * (0.4 + 0.6 * ends), np.tile(ROOT_COL * 0.9, (m - 1, 1)))
        for i in range(n):
            s = u[i]                                                        # (its root: a share of the lid's length)
            a0 = s * lid_len
            L = curve(spec["length"], s) * rng.uniform(0.78, 1.12)
            maxlen = np.interp(col_at(a0), np.arange(nc), out_mm[:, -1]) * 0.97
            L = min(L, maxlen)
            lean = math.radians(curve(spec["lean"], s) + rng.normal(0, 2.5))
            mates = np.where(clump == clump[i])[0]
            pull = (u[mates].mean() - s) * lid_len * 0.25                 # (tips drawn toward the clump's middle, mm)
            t0 = rng.uniform(0, spec["rows"])
            w0 = spec["width"] * rng.uniform(0.75, 1.15)
            bend = rng.normal(0, 0.03)                                     # (a slight sideways curve of its own)
            k = 28
            v = np.linspace(0, 1, k)
            t_mm = t0 + v * L
            side_mm = np.sin(lean) * v * L + pull * v ** 2 + bend * L * v * (1 - v)
            # (kept on the card: past its ends a lash ran along the card's edge)
            p = at(np.clip(a0 + side_mm, 0.4, lid_len - 0.4), t_mm)
            mm_px = np.linalg.norm(p[-1] - p[0]) / max(L, 1e-3)              # (this lash's pixels per mm, roughly)
            # (dark brown, lightening only over its last third)
            col = (ROOT_COL + (TIP_COL - ROOT_COL) * np.clip((v[:, None] - 0.67) / 0.33, 0, 1) ** 1.2) * rng.uniform(0.85, 1.15)
            vv = (v[:-1] + v[1:]) / 2
            widths = np.maximum(w0 * (1 - vv) ** 0.85 * mm_px, 0.6 * ss / 4)
            fades = spec["alpha"] * np.where(vv < 0.7, 1.0, 1 - (vv - 0.7) / 0.3 * 0.75)
            draw_lash(p, widths, fades, col)
    a = np.asarray(alpha.resize((size, size), Image.BOX), np.float32) / 255
    c = np.asarray(colour.resize((size, size), Image.BOX), np.float32) / 255
    return np.dstack([c, a])


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = os.path.abspath(args[0]) if args else OUT
    from PIL import Image
    img = paint(card_grids())
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(out)
    print("LASHES painted:", out, "%.1f%% covered" % (100 * (img[..., 3] > 0.05).mean()))
