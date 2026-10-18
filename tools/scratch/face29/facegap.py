"""How her hair lies on her face at bind pose: strand vertices over the front of her face (cheek, temple, jaw), their
gap to the skin and the angle between the card and the skin (0 = lying flat on it)."""
import numpy as np
from clipmeasure import G, skinned, Surf, HJ, her, surf, A
head = surf(her, lambda n, m: n == "HeroineHead")
S = Surf(head)
eye_y = 1.748
for s in ["bob", "pixie", "long", "ponytail", "braid"]:
    g = G(A + rf"\heroine_hair_{s}.gltf"); names = g.joint_names(0)
    mats = np.array([HJ[n] if n in HJ else g.W(g.j["skins"][0]["joints"][q]) for q, n in enumerate(names)]) @ g.ibm(0)
    for (node, mesh, k, mat, P, J, Wt, sk, I, ni) in g.meshes():
        if mat in ("hair_cap", "hair_tie"): continue
        at = g.j["meshes"][g.j["nodes"][ni]["mesh"]]["primitives"][k]["attributes"]
        uv = g.acc(at["TEXCOORD_0"]).astype(float); Nn = g.acc(at["NORMAL"]).astype(float)
        V = skinned(P, J, Wt, mats)
        R = mats[J[np.arange(len(J)), Wt.argmax(1)]][:, :3, :3]; Nw = np.einsum("nij,nj->ni", R, Nn); Nw /= np.linalg.norm(Nw, axis=1)[:, None] + 1e-12
        d, idx = S.kd.query(V, k=1)
        tn = S.N[idx]
        # the front of her face: the nearest skin faces forward (+Z) and lies below her brows, above her chin
        face = (tn[:, 2] > 0.35) & (V[:, 1] < eye_y + 0.03) & (V[:, 1] > eye_y - 0.16) & (uv[:, 1] >= 0.1)
        sd = S.sd(V[face], k=12, reach=0.03)
        ok = np.isfinite(sd); x = sd[ok] * 1000
        if not ok.sum(): print(f"{s:9s} {mat:10s} no strands over the face"); continue
        cosang = np.abs((Nw[face][ok] * tn[face][ok]).sum(1))
        ang = np.degrees(np.arccos(np.clip(cosang, 0, 1)))
        print(f"{s:9s} {mat:10s} {ok.sum():6d} v over the face (within 30 mm): gap median {np.median(x):5.1f} mm; "
              f"<1 mm {np.mean(x<1)*100:4.0f}%  <2 mm {np.mean(x<2)*100:4.0f}%  <4 mm {np.mean(x<4)*100:4.0f}%  inside {np.mean(x<0)*100:4.0f}%; "
              f"card-to-skin angle median {np.median(ang):4.0f} deg, <15 deg {np.mean(ang<15)*100:3.0f}%")
