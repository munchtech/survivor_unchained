"""The Ford-Warden's hood skirt skinned to his shoulders, not his head (in place, in his package's body.glb and lod.glb).

warden_head.py blends the hood from the body's mantle weights (below 1.465 m) to Head (above 1.535 m) by height
alone, so the skirt lying over his shoulders (out to |x| 0.29 m at 1.46-1.50 m) was already 30-90% Head: when he
bends or lifts his head (C02's rise and bend-lift) the skirt rode up with the head and lifted off the shoulder as a
flap. Here, away from the face and beard (kept exactly as they were):
  - the skirt out over the shoulders (|x| beyond 0.13-0.19 m) takes the mantle's weights under it, whatever its height;
  - the hood's middle band round the neck (1.46-1.56 m) shares neck_01, so the cowl bends with the neck;
  - Head from 1.50 m, full by 1.58 m (around the face the hood still moves with the head).
Only JOINTS_0 / WEIGHTS_0 of the head's primitive are rewritten (same sizes), nothing else.

  python tools/assets/warden_hood_weights.py [PKG_DIR] [--dry]
Run after warden_head.py (and before or after glb_orient.py / warden_wet_maps.py: they don't touch weights).
"""
import argparse, os, sys
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(__file__))
from glb_orient import Glb  # noqa: E402
from warden_wet_maps import smoothstep, Glb as Reader  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pkg", nargs="?", default=os.path.join(os.path.dirname(__file__), "..", "..", "godot", "art", "npc", "ford_warden"))
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    body = Reader(os.path.join(a.pkg, "body.glb"))
    names = [body.j["nodes"][n]["name"] for n in body.j["skins"][0]["joints"]]
    hi, nk = names.index("Head"), names.index("neck_01")
    gen = body.prim("generated")
    sel = gen["POSITION"][:, 1] > 1.25
    rp, rJ, rW = gen["POSITION"][sel].astype(float), gen["JOINTS_0"][sel].astype(int), gen["WEIGHTS_0"][sel].astype(float)
    tree = cKDTree(rp)
    head = body.prim("warden_head")
    col = np.asarray(body.image(head["mat"]["pbrMetallicRoughness"]["baseColorTexture"]["index"]), np.float32) / 255
    for f in ("body.glb", "lod.glb"):
        path = os.path.join(a.pkg, f)
        g = Glb(path)
        for name, p in g.prims():
            if name not in ("warden_head", "warden_head_lod"):
                continue
            P = g.acc(p["attributes"]["POSITION"]).astype(float)
            J = g.acc(p["attributes"]["JOINTS_0"]).astype(int)
            W = g.acc(p["attributes"]["WEIGHTS_0"]).astype(float)
            uv = g.acc(p["attributes"]["TEXCOORD_0"]).astype(float)
            s = col.shape[0]
            cv = col[np.clip((uv[:, 1] * s).astype(int), 0, s - 1), np.clip((uv[:, 0] * s).astype(int), 0, s - 1)]
            x, y, z = P[:, 0], P[:, 1], P[:, 2]
            # the face and beard (pale, in the hood's opening, below its crown): kept as they were
            face = smoothstep(0.12, 0.22, cv.max(1)) * smoothstep(0.11, 0.08, np.abs(x)) * smoothstep(0.03, 0.07, z) * smoothstep(1.715, 1.69, y)
            old = np.zeros((len(P), len(names)))
            np.add.at(old, (np.repeat(np.arange(len(P)), 4), J.ravel()), W.ravel())
            d, k = tree.query(P, 4)
            w = 1 / np.maximum(d, 1e-4)
            w /= w.sum(1, keepdims=True)
            ref = np.zeros((len(P), len(names)))
            for c in range(4):
                np.add.at(ref, (np.repeat(np.arange(len(P)), 4), rJ[k[:, c]].ravel()), (rW[k[:, c]] * w[:, c:c + 1]).ravel())
            side = smoothstep(0.13, 0.19, np.abs(x)) * smoothstep(1.58, 1.52, y)
            wh = smoothstep(1.50, 1.58, y) * (1 - side)
            wn = np.clip(smoothstep(1.46, 1.52, y) - wh, 0, 1) * 0.6 * (1 - side)
            new = ref * (1 - wh - wn)[:, None]
            new[:, hi] += wh
            new[:, nk] += wn
            dense = face[:, None] * old + (1 - face)[:, None] * new
            order = np.argsort(-dense, 1)[:, :4]
            W2 = np.take_along_axis(dense, order, 1)
            W2 /= W2.sum(1, keepdims=True)
            oh = (W * (J == hi)).sum(1)
            nh = (W2 * (order == hi)).sum(1)
            band = (y > 1.44) & (y < 1.54)
            print(f"{f} {name}: {len(P)} verts; Head weight in the skirt band (1.44-1.54 m) {oh[band].mean():.2f} -> {nh[band].mean():.2f}; "
                  f"over the shoulders (|x|>0.17) {oh[band & (np.abs(x) > 0.17)].mean():.2f} -> {nh[band & (np.abs(x) > 0.17)].mean():.2f}; face kept {(face > 0.5).sum()}")
            if not a.dry:
                g.put(p["attributes"]["JOINTS_0"], order.astype(np.uint16))
                g.put(p["attributes"]["WEIGHTS_0"], W2.astype(np.float32))
        if not a.dry:
            open(path, "wb").write(bytes(g.raw))


if __name__ == "__main__":
    main()
