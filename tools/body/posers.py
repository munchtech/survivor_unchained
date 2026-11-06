"""Posers for the body check: one interface, two ways to pose a body.

    p = make_poser("game"|"lbs", glb_path, rig)        # rig: the parsed --rig json or {}
    p.names, p.index, p.parent, p.rest (bone rest worlds [B,4,4]), p.tail(j), p.subtree(j)
    p.P0 [V,3] rest points (the body, then the closing head pieces), p.T [F,3], p.piece [V] "body"/"head",
    p.D [V,B] dense weights
    V, G, info = p.pose([(bone, R3x3), ...])           # world-space turns about each bone's head, applied in order

"game": her body as the game poses it (tools/anim/skin.py Body with helpers=True: HerShrug, HerRaise, HerScap,
        HerJoints' twists, HerShoulder, her correctives and shoulder PSD shapes), on
        tools/anim/data/heroine_skeleton.json. Only for a body on her current skeleton.
"lbs":  plain linear blend skinning from the glb's own skin (its joints, inverse binds and weights); blend shapes
        driven by the rig's driver module (rig.json "poser", default tools.body.rig_drive). Any skeleton.
"""
from __future__ import annotations

import importlib
import sys

import numpy as np

from gl import REPO, Glb, dense_weights

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
ANIM = str(REPO / "tools" / "anim")


class _Base:
    def tail(self, j):
        ch = [k for k, p in enumerate(self.parent) if p == j]
        h = self.rest[j][:3, 3]
        if not ch:
            return h
        hs = np.stack([self.rest[c][:3, 3] for c in ch])
        if len(ch) == 1:
            return hs[0]
        y = self.rest[j][:3, 1] / max(np.linalg.norm(self.rest[j][:3, 1]), 1e-12)
        d = (hs - h) @ y
        return hs[int(np.argmax(d))] if d.max() > 1e-4 else hs.mean(0)

    def subtree(self, j):
        out, st = [], [j]
        while st:
            k = st.pop()
            out.append(k)
            st.extend(c for c, p in enumerate(self.parent) if p == k)
        return out


class GamePoser(_Base):
    kind = "game"

    def __init__(self, glb_path, rig):
        if ANIM not in sys.path:
            sys.path.insert(0, ANIM)
        import skin
        from rig import Skeleton
        sk = Skeleton.load(skin.SKELETONS / "heroine_skeleton.json")
        body_mesh = rig.get("body_mesh", "Heroine")
        keep = (body_mesh, *rig.get("close_meshes", ["HeroineHead"]))
        self.body = b = skin.Body(sk, [(glb_path, lambda n: n in keep, "skin")], None, label="her", helpers=True)
        self.sk = sk
        self.names = list(sk.names)
        self.index = dict(sk.index)
        self.parent = list(sk.parent)
        self.rest = b.rest.copy()
        self.P0 = b.P.copy()
        self.T = b.T.copy()
        self.piece = np.where(b.piece == body_mesh, "body", "head")
        self.D = dense_weights(b.J, b.W, len(self.names))

    def pose(self, turns):
        import helpers as hp
        import skin
        from rig import qfrom_matrix, qinv, qmul
        sk = self.sk
        rot = sk.rest_rot.copy()
        for bone, R in turns:
            j = sk.index[bone]
            grot, _ = sk.fk(rot[None])
            g = qmul(qfrom_matrix(R), grot[0, j])
            p = sk.parent[j]
            rot[j] = qmul(qinv(grot[0, p]), g) if p >= 0 else g
        clip = skin.Clip("check", 30.0, rot[None], sk.rest_pos[None].copy(), False)
        G = self.body.globals(clip, 0, {}, 1 / 30)
        V = self.body.pose(G)
        info = {"shapes": {k: round(float(w), 4) for k, w in self.body.shape_weights(G).items()}}
        for bone, _ in turns:
            info[f"game_bend_{bone}"] = round(float(hp.bend(sk, rot, bone)), 2)
            info[f"game_flexion_{bone}"] = round(float(hp.flexion(sk, rot, bone)), 2)
        return V, G, info


class LbsPoser(_Base):
    kind = "lbs"

    def __init__(self, glb_path, rig):
        g = Glb(glb_path)
        self.glb, self.rig = g, rig
        sk = g.skeleton(0)
        self.skel = sk
        self.names, self.index, self.parent = sk.names, sk.index, sk.parent
        self.rest = sk.rest.copy()
        body_mesh = rig.get("body_mesh") or guess_body(g)
        head = rig.get("close_meshes", [m.node for m in g.meshes if m.node.endswith("Head")])
        P, T, piece, J, W, tg = [], [], [], [], [], {}
        base = 0
        for nm, tag in [(body_mesh, "body")] + [(h, "head") for h in head]:
            m = g.mesh(nm)
            if m is None or m.J is None:
                continue
            P.append(m.P.astype(float))
            T.append(m.T + base)
            piece += [tag] * len(m.P)
            J.append(m.J)
            W.append(m.W)
            for k, d in m.targets.items():
                tg.setdefault(k, []).append((base, d["POSITION"].astype(float)))
            base += len(m.P)
        k = max(j.shape[1] for j in J)
        self.J = np.concatenate([np.pad(j, ((0, 0), (0, k - j.shape[1]))) for j in J])
        self.W = np.concatenate([np.pad(w, ((0, 0), (0, k - w.shape[1]))) for w in W])
        self.W = self.W / np.maximum(self.W.sum(1, keepdims=True), 1e-12)
        self.Pb = np.concatenate(P)
        self.T = np.concatenate(T)
        self.piece = np.array(piece)
        self.targets = {}
        for name, parts in tg.items():
            full = np.zeros_like(self.Pb)
            for b0, d in parts:
                full[b0:b0 + len(d)] = d
            if np.abs(full).max() > 0:
                self.targets[name] = full
        self.D = dense_weights(self.J, self.W, len(self.names))
        self.driver = importlib.import_module(rig.get("poser", "tools.body.rig_drive"))
        self.P0 = self._skin(self.rest, {})

    def _skin(self, G, weights):
        P = self.Pb.copy()
        for k, w in weights.items():
            if k in self.targets and w:
                P = P + w * self.targets[k]
        S = G @ self.skel.ibm
        Ph = np.concatenate([P, np.ones((len(P), 1))], 1)
        out = np.zeros((len(P), 3))
        for k in range(self.J.shape[1]):
            out += self.W[:, k:k + 1] * np.einsum("nij,nj->ni", S[self.J[:, k]][:, :3, :], Ph)
        return out

    def pose(self, turns):
        G = self.rest.copy()
        for bone, R in turns:
            j = self.index[bone]
            h = G[j][:3, 3].copy()
            Dm = np.eye(4)
            Dm[:3, :3] = R
            Dm[:3, 3] = h - R @ h
            for k in self.subtree(j):
                G[k] = Dm @ G[k]
        G, weights = self.driver.drive(self, G, self.rig)
        V = self._skin(G, weights)
        return V, G, {"shapes": {k: round(float(w), 4) for k, w in weights.items() if w > 0}}


HEAD_PARTS = ("Head", "Eyes", "Lashes", "Teeth", "Tongue", "Brows")


def guess_body(g):
    sk = [m for m in g.meshes if m.J is not None and not m.node.endswith(HEAD_PARTS)]
    return max(sk, key=lambda m: len(m.P)).node


def make_poser(kind, glb_path, rig):
    return GamePoser(glb_path, rig) if kind == "game" else LbsPoser(glb_path, rig)
