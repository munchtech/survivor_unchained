"""The visible fold-over at her knees and elbows, measured as the review's
cameras see it: her skin posed here, drawn from anim_review's own camera
(VIEW, LOOK, ZOOM, FOV 32, 400 px) into a z-buffer culled as the game culls
(only faces turned to the camera), and shaded with the normals the game skins
(the rest normal through each point's blended bone matrix, scale and all).
Hidden folds inside the crease do not count; what shows does:

- flip: pixels of faces that show although they are turned over (their
  posed face against their skinned normals): the inside of a fold seen;
- notch: shading the eye reads as a crack: the high-pass of the shaded
  picture (its difference from a 2 px blur, at 400 px) past a threshold;
- edge: fold edges inside her outline: neighbouring pixels from faces far
  apart on her (no shared point within two rings) and a depth step.
All in pixels at 400 px framing, summed over the views given.

    python -u tick.py <variant> ... [--joint knee|elbow] [--poses 120,145] [--views side,back,left] [--png dir]
Variants: before, built, split (helpers.SPEC as it stands), or split with
overrides: split,cut=0.45,reach=0.035,kb=0.5,kmax=1.5,kp=0.059,eb=..,emax=..,ep=..
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
from sweep import S, WT, pose, elbow, knee  # noqa: E402
from rigtest import thigh_forward  # noqa: E402
import helpers as hp  # noqa: E402
from rig import Skeleton  # noqa: E402
from skin import Body, Gltf  # noqa: E402

RES = 4            # supersampling over the review's 400 px
VIEWS = {"front": (0, 0.2, 4.6), "back": (0, 0.2, -4.6), "side": (4.6, 0.2, 0), "left": (-4.6, 0.2, 0),
         "three": (3.2, 0.6, 3.4)}
KEY = np.array([0.369, 0.766, 0.527])     # toward anim_review's key light (rotation -50, 35)
RIM = None


def light_dirs():
    def d(rx, ry):
        rx, ry = math.radians(rx), math.radians(ry)
        v = np.array([0.0, math.sin(rx), -math.cos(rx)])          # Rx * (0,0,-1)
        v = np.array([v[2] * math.sin(ry), v[1], v[2] * math.cos(ry)])
        return -v / np.linalg.norm(v)
    return d(-50, 35), d(-20, 200)


KEY, RIM = light_dirs()


def variant_body(spec):
    parts = spec.split(",")
    which = parts[0]
    over = dict(p.split("=") for p in parts[1:])
    for h in hp.SPEC["helpers"]:
        if h["name"].startswith("calf_share"):
            h["bulge"] = float(over.get("kb", h["bulge"]))
            h["bulge_max"] = float(over.get("kmax", h["bulge_max"]))
            h["pivot"] = float(over.get("kp", h.get("pivot", 0.0)))
        if h["name"].startswith("lowerarm_share"):
            h["bulge"] = float(over.get("eb", h["bulge"]))
            h["bulge_max"] = float(over.get("emax", h["bulge_max"]))
            h["pivot"] = float(over.get("ep", h.get("pivot", 0.0)))
    cr = hp.SPEC["weights"].get("crease") or {"cut": 0.0, "reach": 0.035}
    hp.SPEC["weights"]["crease"] = {"cut": float(over.get("cut", cr["cut"])), "reach": float(over.get("reach", cr["reach"]))}
    if "share" in over:
        hp.SPEC["weights"]["share"] = float(over["share"])
    if which == "before":
        sk = Skeleton.load(S / "before" / "data" / "heroine_skeleton.json")
        f, helpers = S / "before/people/heroine.glb", False
    elif which == "split":
        sk = Skeleton.load(S / "before" / "data" / "heroine_skeleton.json")
        f, helpers = S / "before/people/heroine.glb", True
    elif which.startswith("dir="):
        # another helper build kept aside: dir=<folder holding people/ and heroine_skeleton.json>
        d = Path(which[4:])
        sk = Skeleton.load(d / "heroine_skeleton.json")
        f, helpers = d / "people" / "heroine.glb", True
    else:
        sk = Skeleton.load(WT / "tools/anim/data/heroine_skeleton.json")
        f, helpers = WT / "godot/art/people/heroine.glb", True
    b = Body(sk, [(f, lambda n: n == "Heroine", "skin")], None, helpers=helpers)
    # Her rest normals, in the order Body reads her points.
    g = Gltf(f)
    N = []
    for n in g.js["nodes"]:
        if n.get("name") != "Heroine" or "mesh" not in n or "skin" not in n:
            continue
        for pr in g.js["meshes"][n["mesh"]]["primitives"]:
            N.append(g.accessor(pr["attributes"]["NORMAL"]).astype(float))
    b.N = np.concatenate(N)
    assert len(b.N) == len(b.P)
    return b


def ring_neighbours(T, nv):
    """Each point's neighbours within two rings, as a sparse set test."""
    import scipy.sparse as sp
    e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(nv, nv)).tocsr()
    A = ((A + A.T) > 0).astype(np.int8)
    A2 = ((A @ A + A + sp.identity(nv, dtype=np.int8)) > 0).tocsr()
    return A2


def camera(target, view, zoom):
    off = np.array(VIEWS[view], float) / zoom / 1.04       # her space (the game scales her by 1.04)
    E = target + off
    f = target - E
    f /= np.linalg.norm(f)
    r = np.cross(f, [0, 1.0, 0])
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return E, f, r, u


def raster(P, T, E, f, r, u, fov=32.0, size=None, draw=None):
    """Nearest face turned to the camera at each pixel (or of the faces
    `draw`, whichever way they face): (face id or -1, depth, barycentrics)."""
    size = size or 400 * RES
    d = P - E
    z = d @ f
    t = math.tan(math.radians(fov / 2))
    sx = size / 2 + (d @ r) / z / t * (size / 2)
    sy = size / 2 - (d @ u) / z / t * (size / 2)
    ids = np.full((size, size), -1, np.int64)
    depth = np.full((size, size), np.inf)
    bary = np.zeros((size, size, 3))
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    facing = np.einsum("ij,ij->i", n, E - P[T[:, 0]]) > 0
    for ti in np.nonzero(facing if draw is None else draw)[0]:
        a, b_, c = T[ti]
        xs, ys = sx[[a, b_, c]], sy[[a, b_, c]]
        x0, x1 = max(int(np.floor(xs.min())), 0), min(int(np.ceil(xs.max())), size - 1)
        y0, y1 = max(int(np.floor(ys.min())), 0), min(int(np.ceil(ys.max())), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(den) < 1e-12:
            continue
        w0 = ((ys[1] - ys[2]) * (X - xs[2]) + (xs[2] - xs[1]) * (Y - ys[2])) / den
        w1 = ((ys[2] - ys[0]) * (X - xs[2]) + (xs[0] - xs[2]) * (Y - ys[2])) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any():
            continue
        zz = w0 * z[a] + w1 * z[b_] + w2 * z[c]
        sub = depth[y0:y1 + 1, x0:x1 + 1]
        win = inside & (zz < sub)
        if not win.any():
            continue
        sub[win] = zz[win]
        ids[y0:y1 + 1, x0:x1 + 1][win] = ti
        bb = bary[y0:y1 + 1, x0:x1 + 1]
        bb[win] = np.stack([w0[win], w1[win], w2[win]], 1)
    return ids, depth, bary


def box_blur(img, rad):
    """Separable box blur (twice: near a Gaussian) with edge clamping."""
    out = img
    for _ in range(2):
        k = 2 * rad + 1
        p = np.pad(out, ((rad, rad), (0, 0)), mode="edge")
        c = np.cumsum(np.pad(p, ((1, 0), (0, 0))), 0)
        out = (c[k:] - c[:-k]) / k
        p = np.pad(out, ((0, 0), (rad, rad)), mode="edge")
        c = np.cumsum(np.pad(p, ((0, 0), (1, 0))), 1)
        out = (c[:, k:] - c[:, :-k]) / k
    return out


def measure(b, G, joint_bone, view, zoom, reach=0.17, png=None, label=""):
    sk = b.sk
    j = sk.index[joint_bone]
    target = G[j][:3, 3]
    P = b.pose(G)
    # All of her skin that can stand in the way is drawn; only what shows
    # within `reach` of the joint is counted.
    near = np.linalg.norm(P - target, axis=1) < 0.7
    if joint_bone.startswith("calf"):
        # (her other leg left out, so the inside of the knee can be seen)
        other = b.parts.index("leg_r" if joint_bone.endswith("_l") else "leg_l")
        near &= b.part != other
    T = b.T[near[b.T].all(1)]
    counted = np.linalg.norm(P[T].mean(1) - target, axis=1) < reach
    # Skinned normals as the game skins them (the blended matrix, scale and all).
    Sm = b.skin_mats(G)
    Nn = np.zeros_like(b.N)
    for k in range(4):
        Nn += b.W[:, k:k + 1] * np.einsum("nij,nj->ni", Sm[b.J[:, k], :3, :3], b.N)
    Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12)
    E, f, r, u = camera(target, view, zoom)
    ids, depth, bary = raster(P, T, E, f, r, u)
    vis = ids >= 0
    tri = np.where(vis, ids, 0)
    # shading normal per pixel (interpolated skinned normals)
    ns = (bary[..., 0:1] * Nn[T[tri, 0]] + bary[..., 1:2] * Nn[T[tri, 1]] + bary[..., 2:3] * Nn[T[tri, 2]])
    ns /= np.maximum(np.linalg.norm(ns, axis=-1, keepdims=True), 1e-12)
    view_dir = E - (target)          # (near enough for a narrow lens)
    view_dir /= np.linalg.norm(view_dir)
    shade = 0.25 + 0.6 * np.clip(ns @ KEY, 0, 1) + 0.3 * np.clip(ns @ RIM, 0, 1)
    shade = np.where(vis, shade, 0.0)
    # flip: a face shown though its skinned normals say it is turned over
    gn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    carried = Nn[T].sum(1)
    flipped_face = np.einsum("ij,ij->i", gn, carried) < 0
    near_px = vis & counted[tri]
    flip_px = near_px & flipped_face[tri]
    # lip: skin showing over a turned-over face just under it (within 1 cm):
    # the outer lip of a fold-over, whose edge is the tick
    _, tdepth, _ = raster(P, T, E, f, r, u, draw=flipped_face)
    with np.errstate(invalid="ignore"):
        lip_px = near_px & (tdepth > depth) & (tdepth - depth < 0.01)
        # seen: skin seen through a turned-over face just in front of it
        # (within 1 cm; culled, so the fold's far side shows past its edge)
        seen_px = near_px & (tdepth < depth) & (depth - tdepth < 0.01)
    # tick: where such a fold ends in sight: a step in depth (over 2 mm
    # between neighbouring pixels, inside her outline) beside a lip or a seen
    # pixel; a fold tucked under smooth skin has no step and does not count
    step = np.zeros_like(vis)
    for dy, dx in ((0, 1), (1, 0)):
        a = depth[:depth.shape[0] - dy, :depth.shape[1] - dx]
        c = depth[dy:, dx:]
        with np.errstate(invalid="ignore"):
            s_ = np.isfinite(a) & np.isfinite(c) & (np.abs(a - c) > 0.002)
        step[:step.shape[0] - dy, :step.shape[1] - dx] |= s_
        step[dy:, dx:] |= s_
    fold = lip_px | seen_px
    grown = fold.copy()
    for _ in range(2 * RES):
        g = grown.copy()
        g[1:, :] |= grown[:-1, :]
        g[:-1, :] |= grown[1:, :]
        g[:, 1:] |= grown[:, :-1]
        g[:, :-1] |= grown[:, 1:]
        grown = g
    tick_px = step & grown & near_px
    # notch: high-pass of the shading, within the outline (eroded so the
    # outline's own step does not count)
    inner = vis.copy()
    for _ in range(3 * RES):
        e = inner.copy()
        e[1:, :] &= inner[:-1, :]
        e[:-1, :] &= inner[1:, :]
        e[:, 1:] &= inner[:, :-1]
        e[:, :-1] &= inner[:, 1:]
        inner = e
    hpass = shade - box_blur(shade, 2 * RES)
    notch_px = inner & near_px & (np.abs(hpass) > 0.06)
    # edge: neighbours from faces far apart on her and a depth step
    A2 = b._ring2
    edge = np.zeros_like(vis)
    for dy, dx in ((0, 1), (1, 0)):
        a = ids[:ids.shape[0] - dy, :ids.shape[1] - dx]
        c = ids[dy:, dx:]
        both_ = (a >= 0) & (c >= 0) & (a != c)
        ya, xa = np.nonzero(both_)
        if len(ya) == 0:
            continue
        ta, tc = a[ya, xa], c[ya, xa]
        va, vc = T[ta, 0], T[tc, 0]
        close = np.asarray(A2[va, vc]).ravel() > 0
        # any corner of one within two rings of the first corner of the other
        for kk in (1, 2):
            close |= np.asarray(A2[T[ta, kk], vc]).ravel() > 0
            close |= np.asarray(A2[va, T[tc, kk]]).ravel() > 0
        dz = np.abs(depth[ya, xa] - depth[ya + dy, xa + dx])
        far = (~close) & (dz > 0.002)
        edge[ya[far], xa[far]] = True
    edge &= inner & near_px
    sc = 1.0 / RES
    res = {"tick": tick_px.sum() * sc, "seen": seen_px.sum() * sc * sc, "lip": lip_px.sum() * sc * sc, "flip": flip_px.sum() * sc * sc, "notch": np.abs(hpass[notch_px]).sum() * sc * sc / 0.06,
           "edge": edge.sum() * sc, "vis": vis.sum() * sc * sc}
    if png is not None:
        from PIL import Image
        g = (np.clip(shade, 0, 1) * 255).astype(np.uint8)
        rgb = np.stack([g, g, g], -1)
        rgb[notch_px] = (rgb[notch_px] * 0.4 + np.array([0, 160, 255]) * 0.6).astype(np.uint8)
        rgb[edge] = [255, 220, 0]
        rgb[lip_px] = (rgb[lip_px] * 0.3 + np.array([255, 0, 255]) * 0.7).astype(np.uint8)
        rgb[seen_px] = [0, 255, 80]
        rgb[tick_px] = [255, 140, 0]
        rgb[flip_px] = [255, 0, 60]
        # the whole 400 px frame at 2x, and (ZOOMAT=x,y,half in 400 px) a crop at full res
        Image.fromarray(rgb).resize((800, 800), Image.LANCZOS).save(png)
        import os
        if os.environ.get("ZOOMAT"):
            zx, zy, zh = [int(v) for v in os.environ["ZOOMAT"].split(",")]
            crop = rgb[(zy - zh) * RES:(zy + zh) * RES, (zx - zh) * RES:(zx + zh) * RES]
            Image.fromarray(crop).save(str(png).replace(".png", "_z.png"))
            sh = (np.clip(shade, 0, 1) * 255).astype(np.uint8)[(zy - zh) * RES:(zy + zh) * RES, (zx - zh) * RES:(zx + zh) * RES]
            Image.fromarray(sh).save(str(png).replace(".png", "_zs.png"))
    res["_pix"] = (flip_px, notch_px, edge, ids, T)
    return res


def poses_for(joint, which):
    out = {}
    for p in which:
        if joint == "knee":
            if p == "hip110":
                out["hip110 k135"] = [thigh_forward("l", 110), thigh_forward("r", 110), knee("l", 135), knee("r", 135)]
            else:
                out[f"knee {p}"] = [knee("l", int(p)), knee("r", int(p))]
        else:
            out[f"elbow {p}"] = [elbow("l", int(p)), elbow("r", int(p))]
    return out


def main():
    args = sys.argv[1:]
    opts = {"--joint": "knee", "--poses": "120,145", "--views": "side,back,left", "--png": ""}
    variants = []
    i = 0
    while i < len(args):
        if args[i] in opts:
            opts[args[i]] = args[i + 1]
            i += 2
        else:
            variants.append(args[i])
            i += 1
    joint = opts["--joint"]
    bone, zoom = ("calf_l", 4.5) if joint == "knee" else ("lowerarm_l", 5.0)
    poses = poses_for(joint, opts["--poses"].split(","))
    views = opts["--views"].split(",")
    import copy
    spec0 = copy.deepcopy(hp.SPEC)
    for v in variants:
        hp.SPEC.clear()
        hp.SPEC.update(copy.deepcopy(spec0))
        b = variant_body(v)
        b._ring2 = ring_neighbours(b.T, len(b.P))
        tot = {}
        for pname, edits in poses.items():
            G = pose(b, edits)
            cells = []
            for view in views:
                png = None
                if opts["--png"]:
                    Path(opts["--png"]).mkdir(parents=True, exist_ok=True)
                    tag = v.replace(",", "_").replace("=", "")
                    png = Path(opts["--png"]) / f"{tag}_{pname.replace(' ', '')}_{view}.png"
                m = measure(b, G, bone, view, zoom, png=png)
                for k in ("tick", "seen", "lip", "flip", "notch", "edge"):
                    tot[k] = tot.get(k, 0) + m[k]
                cells.append(f"{view} tick {m['tick']:5.1f} seen {m['seen']:5.1f} lip {m['lip']:5.1f} flip {m['flip']:4.1f}")
            print(f"{v:40s} {pname:12s} " + " | ".join(cells), flush=True)
        print(f"{v:40s} TOTAL tick {tot['tick']:6.1f} seen {tot['seen']:6.1f} lip {tot['lip']:6.1f} flip {tot['flip']:6.1f} notch {tot['notch']:7.1f} edge {tot['edge']:6.1f}", flush=True)


if __name__ == "__main__":
    main()
