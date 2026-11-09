"""glb reading for the body check: meshes in their bind space, the skin, the skeleton as the file defines it.

Nothing here assumes her skeleton: bones are whatever the file's skin lists, with the node hierarchy above them.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "anim"))
from skin import Gltf, _trs  # noqa: E402  (the repo's glTF reader and node TRS)


@dataclass
class Mesh:
    node: str
    name: str
    skin: int | None
    materials: list
    P: np.ndarray            # [V,3] float32 as stored (bind space for a skinned mesh)
    N: np.ndarray | None
    UV: np.ndarray | None
    T: np.ndarray            # [F,3] int64
    J: np.ndarray | None     # [V,K] joint indices into the skin's joints
    W: np.ndarray | None     # [V,K]
    targets: dict = field(default_factory=dict)   # name -> {"POSITION": [V,3], "NORMAL": [V,3]}
    prim_of: np.ndarray | None = None              # [F] primitive index


class Glb:
    def __init__(self, path):
        self.path = Path(path)
        self.g = Gltf(self.path)
        js = self.g.js
        self.js = js
        self.nodes = js["nodes"]
        self.parent = {}
        for i, n in enumerate(self.nodes):
            for c in n.get("children", []):
                self.parent[c] = i
        self._world = {}
        self.meshes = [self._mesh(i) for i, n in enumerate(self.nodes) if "mesh" in n]
        self.materials = [m.get("name", f"material_{i}") for i, m in enumerate(js.get("materials", []))]

    def world(self, i):
        if i not in self._world:
            self._world[i] = (self.world(self.parent[i]) if i in self.parent else np.eye(4)) @ _trs(self.nodes[i])
        return self._world[i]

    def acc(self, i):
        return self.g.accessor(i)

    def _mesh(self, ni):
        n = self.nodes[ni]
        m = self.js["meshes"][n["mesh"]]
        names_t = m.get("extras", {}).get("targetNames", [])
        P, N, UV, T, J, W, mats, prim = [], [], [], [], [], [], [], []
        tg = {}
        base = 0
        for pi, pr in enumerate(m["primitives"]):
            a = pr["attributes"]
            p = self.acc(a["POSITION"]).astype(np.float32)
            P.append(p)
            N.append(self.acc(a["NORMAL"]).astype(np.float32) if "NORMAL" in a else np.zeros_like(p))
            UV.append(self.acc(a["TEXCOORD_0"]).astype(np.float32) if "TEXCOORD_0" in a else np.zeros((len(p), 2), np.float32))
            idx = self.acc(pr["indices"]).reshape(-1, 3).astype(np.int64) if "indices" in pr else np.arange(len(p)).reshape(-1, 3)
            T.append(idx + base)
            prim.append(np.full(len(idx), pi))
            sets = [q for q in range(4) if f"JOINTS_{q}" in a]
            if sets:
                J.append(np.concatenate([self.acc(a[f"JOINTS_{q}"]).astype(np.int64) for q in sets], 1))
                W.append(np.concatenate([self.acc(a[f"WEIGHTS_{q}"]).astype(np.float64) for q in sets], 1))
            mats.append(pr.get("material"))
            for k, t in enumerate(pr.get("targets", [])):
                nm = names_t[k] if k < len(names_t) else f"target_{k}"
                d = tg.setdefault(nm, {"POSITION": [], "NORMAL": []})
                for key in ("POSITION", "NORMAL"):
                    d[key].append(self.acc(t[key]).astype(np.float32) if key in t else np.zeros_like(p))
            base += len(p)
        if J:
            k = max(j.shape[1] for j in J)
            J = np.concatenate([np.pad(j, ((0, 0), (0, k - j.shape[1]))) for j in J])
            W = np.concatenate([np.pad(w, ((0, 0), (0, k - w.shape[1]))) for w in W])
        else:
            J = W = None
        targets = {nm: {key: np.concatenate(v) for key, v in d.items()} for nm, d in tg.items()}
        matn = [self.js["materials"][x].get("name", str(x)) if x is not None else None for x in mats]
        return Mesh(n.get("name", f"node_{ni}"), m.get("name", ""), n.get("skin"), matn, np.concatenate(P), np.concatenate(N),
                    np.concatenate(UV), np.concatenate(T), J, W, targets, np.concatenate(prim))

    def mesh(self, node):
        for m in self.meshes:
            if m.node == node:
                return m
        return None

    def node_names(self):
        return [n.get("name", f"node_{i}") for i, n in enumerate(self.nodes)]

    # ---------------------------------------------------------------- skeleton --
    def skeleton(self, skin=0):
        return FileSkeleton(self, skin)


class FileSkeleton:
    """The skin's joints as the file has them: names, parents (within the joints), rest worlds, inverse binds."""

    def __init__(self, glb: Glb, skin=0):
        s = glb.js["skins"][skin]
        self.nodes = s["joints"]
        self.names = [glb.nodes[j].get("name", f"node_{j}") for j in self.nodes]
        self.index = {n: i for i, n in enumerate(self.names)}
        pos = {nd: i for i, nd in enumerate(self.nodes)}
        self.parent = []
        for nd in self.nodes:
            p = glb.parent.get(nd)
            while p is not None and p not in pos:
                p = glb.parent.get(p)
            self.parent.append(pos[p] if p is not None else -1)
        self.rest = np.stack([glb.world(nd) for nd in self.nodes])
        self.ibm = glb.acc(s["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1).astype(float)
        self.children = [[k for k, p in enumerate(self.parent) if p == j] for j in range(len(self.names))]

    def head(self, j):
        return self.rest[j][:3, 3]

    def tail(self, j):
        """The bone's far end: its children's heads' mean (the one on its line if several), else its head (a leaf)."""
        ch = self.children[j]
        if not ch:
            return self.head(j)
        hs = np.stack([self.head(c) for c in ch])
        if len(ch) == 1:
            return hs[0]
        # several children (pelvis, hand): the child furthest along the bone's own Y, else the mean
        y = self.rest[j][:3, 1] / max(np.linalg.norm(self.rest[j][:3, 1]), 1e-12)
        d = (hs - self.head(j)) @ y
        return hs[int(np.argmax(d))] if d.max() > 1e-4 else hs.mean(0)

    def subtree(self, j):
        out, st = [], [j]
        while st:
            k = st.pop()
            out.append(k)
            st.extend(self.children[k])
        return out


def weld(P, tol=1e-6):
    """Index of each point's welded representative (points within tol share one): [V] ints, compact."""
    from scipy.spatial import cKDTree
    tr = cKDTree(P)
    pairs = tr.query_pairs(tol, output_type="ndarray")
    rep = np.arange(len(P))
    if len(pairs):
        import scipy.sparse as sp
        from scipy.sparse.csgraph import connected_components
        g = sp.coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(len(P), len(P)))
        _, rep = connected_components(g, directed=False)
    else:
        rep = np.arange(len(P))
    return rep


def edges(T):
    e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    return np.unique(np.sort(e, 1), axis=0)


def boundary_edges(T):
    e = np.sort(np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1)
    u, c = np.unique(e, axis=0, return_counts=True)
    return u[c == 1]


def dense_weights(J, W, nb):
    D = np.zeros((len(J), nb))
    for k in range(J.shape[1]):
        np.add.at(D, (np.arange(len(J)), J[:, k]), W[:, k])
    return D
