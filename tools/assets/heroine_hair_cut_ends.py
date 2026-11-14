"""Her hair's cut cards given a tip (hair-chip, 13 Nov).

    python tools/assets/heroine_hair_cut_ends.py godot/art/people [--dry] [--check] [--style braid[,pixie,...]]
    python tools/assets/heroine_hair_cut_ends.py --file ANY.glb|.gltf [--check]   (a built NPC glb carrying her hair)

heroine_hair.py cuts a card short where its strand would run on over her brow (off_brow), past the tie
(gathered's GATHER_CUT) or into her ear (clear_ears, ear_zone): its points from there on are folded onto the last
good one, so the card stops dead there at full cover, a blunt square end. Under the other layers that hides; on top
it shows. The judge's "pale chip at her parting" (close-up, day and night) was one: an outer-layer front card rooted
on her parting, cut by off_brow 18 mm along, its 1 cm stub crumpled along her hairline catching the cel shine band
as a pale ~10 x 5 px block with a square end (heroine_hair.gdshaderinc: cover = t.a * COLOR.a, the band on every
lit card). A real hair ends in a tip, so each cut card's cover (the hair shader's COLOR.a) is eased to none over its
last END metres before the fold, as the ragged tips' 8 mm taper; its folded points (no area) to none. A cut card that
reaches its full cover less than STUB (9 mm) before its cut (a stub: the chip itself, whose taper alone left a fainter chip in
the after frames) is dropped whole.

A card: one connected strip of three columns (heroine_hair.py cards(): left, middle, right, each its U), V 0 at its
root to 1 at its tip (glTF's V). Folded: its middle column's last links move under EPS. Run after the build's other
post steps (heroine_ear_shape --follow-only, heroine_shape_falloff, heroine_pixie_ear --style); done-mark: the gltf's
asset extras cut_ends; the .bin rewritten in place. --check: exit 1 if any card in a "hair" or "hair_fine" surface
ends folded with cover over CHECK_MAX at its end, or is a stub still drawn (cover over CHECK_MAX) (godot/tests HairCutEndsTests reads the gltf the same way).
"""
import os
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heroine_neck import _Gl  # noqa: E402

MARK = "cut_ends"
END = 0.008          # m: the taper before a cut card's fold (the ragged tips' 8 mm)
STUB = 0.009         # m: a cut card whose full cover runs less than this before its cut is a stub (dropped)
EPS = 2e-4           # m: a link shorter than this does not move (a folded point)
CHECK_MAX = 0.1      # a folded card's cover at its last moving point, at most
SURFACES = ("hair", "hair_fine")


def _ss(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def cut_cards(V, UV, F):
    """Each folded card: (its vertex indices, each one's arc from the root along the middle column, the arc at its
    fold). Cards that run their full length are not listed."""
    n = len(V)
    e = np.r_[F[:, [0, 1]], F[:, [1, 2]]]
    _, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    order = np.argsort(lab, kind="stable")
    cuts = np.flatnonzero(np.diff(lab[order])) + 1
    out = []
    for vs in np.split(order, cuts):
        us = np.unique(UV[vs, 0].round(4))
        if len(us) != 3:
            continue
        mid = vs[np.abs(UV[vs, 0] - us[1]) < 1e-4]
        vv, first = np.unique(UV[mid, 1].round(4), return_index=True)
        q = V[mid[first]]                                     # root (V 0) first
        L = np.linalg.norm(np.diff(q, axis=0), axis=1)
        mv = np.flatnonzero(L > EPS)
        if len(mv) == 0 or mv[-1] + 1 >= len(q) - 1:          # all folded (no area) or not folded
            continue
        arc = np.r_[0.0, np.cumsum(L)]
        end = arc[mv[-1] + 1]
        out.append((vs, np.interp(UV[vs, 1].round(4), vv, arc), end))
    return out


def run(art, style="braid", dry=False, check=False, path=None):
    path = path or os.path.join(art, "heroine_hair_%s.gltf" % style)
    G = _Gl(path)
    if not check and MARK in G.g["asset"].get("extras", {}):
        print("CUT_ENDS: %s has had it" % os.path.basename(path))
        return 0
    bad = 0
    for p in [p for m in G.g["meshes"] for p in m["primitives"]]:   # (every mesh: a staged NPC glb's NpcHair too)
        name = G.g["materials"][p.get("material", 0)].get("name")
        if name not in SURFACES:
            continue
        a = p["attributes"]
        V = G.get(a["POSITION"]).astype(float)
        UV = G.get(a["TEXCOORD_0"]).astype(float)
        F = G.get(p["indices"]).astype(np.int64).reshape(-1, 3)
        assert G.g["accessors"][a["COLOR_0"]]["componentType"] == 5123
        C = G.get(a["COLOR_0"]).astype(float) / 65535.0
        cc = cut_cards(V, UV, F)
        if check:
            for vs, s, end in cc:
                at = vs[np.abs(s - end) < 1e-6]
                k = vs[np.abs(s - (end - 1e-6)) < 0.0015]           # its last 1.5 mm
                mx = C[vs, 3].max()
                full = s[C[vs, 3] >= 0.95 * mx].min(initial=end)
                if C[k, 3].max(initial=0.0) > CHECK_MAX:
                    bad += 1
                    print("CUT_ENDS: %s %s: a cut card ends at cover %.2f near %s" % (style, name, C[k, 3].max(), np.round(V[at[0]], 3).tolist()))
                elif mx > CHECK_MAX and end - full < STUB:      # (a stub kept: tapered, it still draws the fleck)
                    bad += 1
                    print("CUT_ENDS: %s %s: a stub (full cover %.1f mm before its cut) kept near %s" % (style, name, (end - full) * 1e3, np.round(V[at[0]], 3).tolist()))
            continue
        drop = 0
        for vs, s, end in cc:
            # (a stub: its cover reaches its full less than STUB before the cut (a front card's root fade-in, 2-14 mm,
            # as long as the card), so the END taper leaves it no full run, its fade-in meeting its fade-out: a fleck,
            # no lock. The parting chip was one: cut 17.8 mm along, full from 9.8 mm (8.0 mm, at the taper's own
            # length, so STUB is END plus 1 mm: the braid's next shortest runs, 10-11 mm, are side cards over her ears,
            # kept with their taper). Dropped.)
            full = s[C[vs, 3] >= 0.95 * C[vs, 3].max()].min(initial=end)
            if end - full < STUB:
                C[vs, 3] = 0.0
                drop += 1
            else:
                C[vs, 3] *= _ss((end - s) / END)
        print("CUT_ENDS: %s %s: %d cut cards tapered over %.0f mm, %d stubs dropped" % (style, name, len(cc) - drop, END * 1e3, drop))
        G.put(a["COLOR_0"], np.clip(np.round(C * 65535.0), 0, 65535).astype(np.uint16))
    if check:
        print("CUT_ENDS: %s: %d blunt cut ends or kept stubs" % (style, bad))
        return 1 if bad else 0
    G.g["asset"].setdefault("extras", {})[MARK] = "cut cards tapered over %.0f mm, stubs dropped" % (END * 1e3)
    if not dry:
        G.save()
        print("CUT_ENDS: %s written" % path)
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    st = a[a.index("--style") + 1].split(",") if "--style" in a else ["braid"]
    if "--file" in a:
        sys.exit(run(None, dry="--dry" in a, check="--check" in a, path=a[a.index("--file") + 1]))
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] not in ("--style", "--file"))]
    sys.exit(max(run(pos[0] if pos else "godot/art/people", style=s_, dry="--dry" in a, check="--check" in a) for s_ in st))
