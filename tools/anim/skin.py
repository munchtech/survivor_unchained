"""Her body (and what she wears) posed as the game poses it, in Python, so
motion can be measured against her actual mesh rather than capsules.

    from skin import Body
    body = Body.heroine(outfit="warden")      # or Body.hero()
    clip = body.clip("run_warden")             # a built clip (tools/anim/out)
    for f in range(clip.frames):
        v = body.posed(clip, f)                # [V, 3] skeleton space, jiggle on

The skinning is Godot's: linear blend, every weight a vertex carries (four,
or eight on her body of record), each bone's matrix its posed global over its
rest global (her bind pose is her rest).

Her body of record's rig (the shoulder helpers delt/trap/pec/lat in her
skeleton; Body.game_rig, SKIN_GAME=1/0 forces it) is posed with the game's
whole stack, checked against Godot's --pose-dump (Body 13 b2, 26 Oct: 100
bones within 0.3 mm, shapes within 0.003, skin within 0.35 mm): HerShrug,
HerRaise's breast lift, HerScap, HerJoints' twists (the roll unwrapped frame
to frame), HerShoulder; the shoulder shapes incl. shoulder_lvl80; her Head's
rest scale and its file's own bind (heroine_headscale.py). Older bodies keep
the posing their baselines were counted with. Pose it on its own skeleton
dump (tools_scenes/anim_skeleton.gd): bones the skeleton lacks lose their
weight (a warning says how much).
Her springs (HerJiggle.cs) are run here as there, frame by frame in the
world, so a breast swings into an arm's way as it does in the game; the
warden's plate holds them (Amount 0.55, no squash), as People.HerOutfit sets.

Vertices are labelled by what moves them (`parts`): each arm (upper arm,
forearm and hand, and their helper bones), each leg, and the trunk. A point
is an arm's when nearly all its weight is that arm's; the shoulder's blend
is left out of contact checks (skin there is meant to fold).
"""
from __future__ import annotations

import json
import os
import struct
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from rig import DATA, REPO, Skeleton, qfrom_matrix, qmatrix, qnorm
import staged

# (ANIM_PEOPLE, ANIM_SKELETONS, ANIM_OUT: another body, skeleton dump or
# clip library to measure, a "before" kept aside say.)
PEOPLE = Path(os.environ.get("ANIM_PEOPLE", REPO / "godot" / "art" / "people"))
SKELETONS = Path(os.environ.get("ANIM_SKELETONS", DATA))
OUT = Path(os.environ.get("ANIM_OUT", Path(__file__).resolve().parent / "out"))


# ------------------------------------------------------------------ glTF --
class Gltf:
    """A .glb or .gltf with its buffers, read as numpy arrays."""

    TYPES = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8, 5122: np.int16, 5120: np.int8}
    WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}

    def __init__(self, path):
        path = Path(path)
        self.path = path
        if path.suffix == ".glb":
            b = path.read_bytes()
            n = struct.unpack_from("<I", b, 12)[0]
            self.js = json.loads(b[20:20 + n])
            off = 20 + n
            ln = struct.unpack_from("<I", b, off)[0]
            self.buffers = [b[off + 8:off + 8 + ln]]
        else:
            self.js = json.loads(path.read_text())
            self.buffers = [(path.parent / buf["uri"]).read_bytes() for buf in self.js["buffers"]]

    def _read(self, view, offset, count, ctype, w):
        bv = self.js["bufferViews"][view]
        dt = np.dtype(self.TYPES[ctype])
        start = bv.get("byteOffset", 0) + offset
        stride = bv.get("byteStride", 0) or dt.itemsize * w
        buf = self.buffers[bv["buffer"]]
        raw = np.frombuffer(buf, dtype=np.uint8, count=stride * (count - 1) + dt.itemsize * w, offset=start)
        if stride == dt.itemsize * w:
            return np.array(raw.view(dt).reshape(count, w))
        return np.array(np.lib.stride_tricks.as_strided(raw.view(dt), shape=(count, w), strides=(stride, dt.itemsize)))

    def accessor(self, i):
        a = self.js["accessors"][i]
        dt = np.dtype(self.TYPES[a["componentType"]])
        w = self.WIDTH[a["type"]]
        if "bufferView" in a:
            out = self._read(a["bufferView"], a.get("byteOffset", 0), a["count"], a["componentType"], w)
        else:
            out = np.zeros((a["count"], w), dt)
        sp = a.get("sparse")
        if sp:
            # (a morph target is written sparse: only the points it moves)
            ix = self._read(sp["indices"]["bufferView"], sp["indices"].get("byteOffset", 0), sp["count"], sp["indices"]["componentType"], 1)
            out[ix[:, 0].astype(np.int64)] = self._read(sp["values"]["bufferView"], sp["values"].get("byteOffset", 0), sp["count"],
                                                        a["componentType"], w)
        if a.get("normalized"):
            out = out.astype(np.float64) / np.iinfo(dt).max
        return out


def _psd():
    import sys
    sys.path.insert(0, str(REPO / "tools" / "assets"))
    import shoulder_psd_post
    return shoulder_psd_post


def _psd_names():
    if os.environ.get("PSD_OFF"):      # (a baseline without them: --psd-off as the game reads it)
        return []
    # (every slot psd_weights keys, as Play/ShoulderPsd.Shapes: the sampled shapes and the level slot shoulder_lvl80)
    return [n + "_" + s for n in _psd().psd_weights(0.0, 0.0) for s in "lr"]


def _trs(n):
    m = np.eye(4)
    if "matrix" in n:
        return np.array(n["matrix"], float).reshape(4, 4).T
    r = n.get("rotation", [0, 0, 0, 1])
    s = n.get("scale", [1, 1, 1])
    m[:3, :3] = qmatrix(qnorm(np.array(r, float))) * np.array(s, float)
    m[:3, 3] = n.get("translation", [0, 0, 0])
    return m


# ------------------------------------------------------------ the springs --
class Jiggle:
    """HerJiggle.cs, step for step: a mass at each soft bone's tip on a
    spring in the world, the bone turned toward it and stretched along it."""

    MASSES = (("breast_l", 250.0, 7.0, 0.04, 0.12), ("breast_r", 250.0, 7.0, 0.04, 0.12),
              ("glute_l", 400.0, 10.0, 0.025, 0.08), ("glute_r", 400.0, 10.0, 0.025, 0.08))

    def __init__(self, sk: Skeleton, amount=1.0, squash=1.0):
        self.sk = sk
        self.amount = amount
        self.squash = squash
        self.state = {}
        self.keep_scale = False   # (the scale the layers before set kept: Body.frames turns it on for the game rig)
        self.bones = [(sk.index[b], k, d, r, s) for b, k, d, r, s in self.MASSES if b in sk.index]

    def reset(self):
        self.state = {}

    def apply(self, G, world, dt):
        """Turn and stretch the soft bones in G (globals [J, 4, 4], changed in
        place) as the springs have moved; `world` places the skeleton."""
        if self.amount <= 0:
            return
        dt = min(max(dt, 0.0), 1 / 20)
        winv = np.linalg.inv(world)
        sk = self.sk
        for j, stiff, damp, reach0, stretch in self.bones:
            pose = G[j]
            ln = 0.10 if sk.names[j].startswith("glute") else 0.085
            y = pose[:3, 1] / np.linalg.norm(pose[:3, 1])
            target = (world @ np.append(pose[:3, 3] + y * ln, 1))[:3]
            st = self.state.get(j)
            if st is None or dt <= 0:
                self.state[j] = [target.copy(), np.zeros(3)]
                continue
            P, V = st
            reach = reach0 * self.amount
            h = dt / 4
            for _ in range(4):
                off = P - target
                a = -off * stiff - V * damp
                over = np.linalg.norm(off) - reach
                if over > 0:
                    a = a - off / max(np.linalg.norm(off), 1e-12) * over * stiff * 8
                V = V + a * h
                P = P + V * h
            o = P - target
            if np.linalg.norm(o) > reach * 1.6:
                P = target + o / np.linalg.norm(o) * reach * 1.6
            st[0], st[1] = P, V
            frm = (winv @ np.append(target, 1))[:3] - pose[:3, 3]
            to = (winv @ np.append(target + (P - target) * self.amount, 1))[:3] - pose[:3, 3]
            if np.dot(frm, frm) < 1e-8 or np.dot(to, to) < 1e-8:
                continue
            a_, b_ = frm / np.linalg.norm(frm), to / np.linalg.norm(to)
            c = np.cross(a_, b_)
            d = float(np.dot(a_, b_))
            if d < -0.999999:
                turn = -np.eye(3)
            else:
                vx = np.array([[0, -c[2], c[1]], [c[2], 0, -c[0]], [-c[1], c[0], 0]])
                turn = np.eye(3) + vx + vx @ vx / (1 + d)
            basis = turn @ pose[:3, :3]
            # The bone's own turn (scale off), then stretched along its line.
            u, _, vt = np.linalg.svd(basis)
            rot = u @ vt
            k = 1 + np.clip((np.linalg.norm(to) - np.linalg.norm(frm)) / max(reach, 1e-4), -1, 1) * stretch * self.squash
            side = 1 / np.sqrt(max(k, 0.5))
            # Godot sets the local rotation and scale: the scale is in the
            # bone's own frame, so the global is the turned rotation scaled
            # (times the scale the layers before it set: HerRaise's stretch).
            sc = np.array([side, k, side])
            if self.keep_scale:
                sc = sc * np.linalg.norm(pose[:3, :3], axis=0)
            G[j][:3, :3] = rot @ np.diag(sc)


# ---------------------------------------------------------------- bodies --
@dataclass
class Clip:
    name: str
    fps: float
    rot: np.ndarray       # [T, J, 4] local
    pos: np.ndarray       # [T, J, 3] local
    loop: bool
    meta: dict = field(default_factory=dict)

    @property
    def frames(self):
        return self.rot.shape[0]


ARM_PARTS = ("clavicle", "upperarm", "lowerarm", "hand", "index", "middle", "ring", "pinky", "thumb")


def _normals(P, T):
    """Area-weighted point normals [V, 3] of triangles T, welded by place
    (points split at a seam share one); points on none get zero."""
    _, inv = np.unique(np.round(P, 6), axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    N = np.zeros((inv.max() + 1, 3))
    for k in range(3):
        np.add.at(N, inv[T[:, k]], fn)
    N = N[inv]
    on = np.zeros(len(P), bool)
    on[T.ravel()] = True
    return np.where(on[:, None], N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12), 0.0)


def part_of(name):
    """Which part a bone moves: arm_l, arm_r, leg_l, leg_r or trunk."""
    side = name[-1] if name[-2:] in ("_l", "_r") else ""
    head = name.split("_")[0]
    if head in ARM_PARTS[1:] and side:
        return "arm_" + side
    if head in ("thigh", "calf", "foot", "ball") and side:
        return "leg_" + side
    return "trunk"


class Body:
    """A skinned body and, if asked, one of her outfits, on a skeleton."""

    def __init__(self, sk: Skeleton, files, jiggle=None, world_scale=1.04, label="her", helpers=False):
        import helpers as hp
        # Her helper bones (tools/anim/helpers.py): added to a skeleton that
        # lacks them, her weights split onto them as the build splits them.
        self.split_here = helpers and not hp.has_helpers(sk)
        if helpers:
            sk = hp.extend(sk)
        self.helpers = helpers
        self.sk = sk
        self.label = label
        self.world_scale = world_scale
        self.jiggle = jiggle
        grot, gpos = sk.rest_globals()
        self.rest = self._mats(grot[0], gpos[0])
        self.rest_inv = np.linalg.inv(self.rest)
        # each joint's rest scale as its file sets it (her Head: 1.07, heroine_headscale.py, its bind left unscaled, so
        # Godot draws all skinned to it that much larger); the game rig's globals carry it (globals)
        self.rest_scale = {}
        # (the game rig: a joint whose file binds it off its rest (her Head: heroine_headscale.py) skinned with that
        # file's own bind, as Godot skins each mesh with its skin's binds; each such bind a virtual bone after the
        # skeleton's: Jv indexes skin_mats)
        self.game = helpers and self.game_rig()
        self.vbind = []
        Jv = []
        P, W, Jn, T, piece, kind = [], [], [], [], [], []
        CP, CN = {}, {}
        base = 0
        for path, which, tag in files:
            g = Gltf(path)
            js = g.js
            nodes = js["nodes"]
            # Node worlds at rest (to check her bind pose is her rest).
            parent = {}
            for i, n in enumerate(nodes):
                for c in n.get("children", []):
                    parent[c] = i
            world = {}

            def wm(i):
                if i not in world:
                    world[i] = (wm(parent[i]) if i in parent else np.eye(4)) @ _trs(nodes[i])
                return world[i]

            for ni, n in enumerate(nodes):
                if "mesh" not in n or "skin" not in n:
                    continue
                if which is not None and not which(n["name"]):
                    continue
                skin = js["skins"][n["skin"]]
                names = [nodes[j]["name"] for j in skin["joints"]]
                # (a body built with its helpers is not split again)
                if "lowerarm_twist_01_l" in names:
                    self.split_here = False
                remap = np.array([sk.index.get(nm, -1) for nm in names])
                for j in skin["joints"]:
                    sc = nodes[j].get("scale")
                    if sc and nodes[j]["name"] in sk.index and np.abs(np.asarray(sc, float) - 1).max() > 1e-6:
                        self.rest_scale[sk.index[nodes[j]["name"]]] = np.asarray(sc, float)
                ibm = g.accessor(skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
                # Bind pose against her rest: world_j @ ibm_j should be identity.
                for k, j in enumerate(skin["joints"][:3]):
                    err = np.abs(wm(j) @ ibm[k] - np.eye(4)).max()
                    if err > 1e-3:
                        raise ValueError(f"{path.name}: {names[k]} is not bound at rest ({err:.4f})")
                mesh = js["meshes"][n["mesh"]]
                for pr in mesh["primitives"]:
                    a = pr["attributes"]
                    p = g.accessor(a["POSITION"]).astype(float)
                    # Her corrective shapes as built: morph targets, by name.
                    names_t = mesh.get("extras", {}).get("targetNames", [])
                    tgs = pr.get("targets", [])
                    for cn in hp.corrective_names() + _psd_names():
                        k = names_t.index(cn) if cn in names_t else -1
                        tg = tgs[k] if 0 <= k < len(tgs) else {}
                        for key, into in (("POSITION", CP), ("NORMAL", CN)):
                            into.setdefault(cn, []).append(g.accessor(tg[key]).astype(float) if key in tg else np.zeros_like(p))
                    # every weight set the point carries (her body of record: 8, JOINTS_1/WEIGHTS_1; Godot 4.5 imports all)
                    jj = np.concatenate([remap[g.accessor(a[f"JOINTS_{q}"]).astype(int)] for q in range(4) if f"JOINTS_{q}" in a], 1)
                    ww = np.concatenate([g.accessor(a[f"WEIGHTS_{q}"]).astype(float) for q in range(4) if f"JOINTS_{q}" in a], 1)
                    lost = np.where(jj < 0, ww, 0).sum()
                    if lost > 1e-6 * len(p):
                        import sys
                        miss = sorted({names[k] for k in np.unique(g.accessor(a["JOINTS_0"]).astype(int)) if remap[k] < 0})
                        print(f"skin: {path.name} {n['name']}: {lost / max(ww.sum(), 1e-9):.2%} of its weight on bones the skeleton lacks "
                              f"(dropped: {' '.join(miss) or 'in a later set'}); pose it on its own skeleton dump", file=sys.stderr)
                    ww = np.where(jj < 0, 0, ww)
                    ww = ww / np.maximum(ww.sum(1, keepdims=True), 1e-9)
                    jj = np.where(jj < 0, 0, jj)
                    jv = jj.copy()
                    if self.game:
                        raw = np.concatenate([g.accessor(a[f"JOINTS_{q}"]).astype(int) for q in range(4) if f"JOINTS_{q}" in a], 1)
                        for k in np.unique(raw):
                            j = remap[k]
                            if j >= 0 and np.abs(ibm[k] - self.rest_inv[j]).max() > 1e-4:
                                hit = [v for v, (b, m) in enumerate(self.vbind) if b == j and np.abs(m - ibm[k]).max() < 1e-7]
                                if not hit:
                                    self.vbind.append((j, ibm[k]))
                                    hit = [len(self.vbind) - 1]
                                jv[raw == k] = len(sk.names) + hit[0]
                    Jv.append(jv)
                    idx = g.accessor(pr["indices"]).reshape(-1, 3).astype(np.int64) if "indices" in pr else np.arange(len(p)).reshape(-1, 3)
                    P.append(p)
                    W.append(ww)
                    Jn.append(jj)
                    T.append(idx + base)
                    piece += [n["name"]] * len(p)
                    kind += [tag] * len(p)
                    base += len(p)
        self.P = np.concatenate(P)
        # (pieces with fewer weight sets padded with empty ones: four a point unless a piece carries eight)
        nw = max(w.shape[1] for w in W)
        W = [np.pad(w, ((0, 0), (0, nw - w.shape[1]))) for w in W]
        Jn = [np.pad(j, ((0, 0), (0, nw - j.shape[1]))) for j in Jn]
        Jv = [np.pad(j, ((0, 0), (0, nw - j.shape[1]))) for j in Jv]
        self.W = np.concatenate(W)
        self.J = np.concatenate(Jn)
        self.Jv = np.concatenate(Jv)   # (J with the game rig's off-rest binds as their virtual bones: what skin_mats indexes)
        self.T = np.concatenate(T)
        self.piece = np.array(piece)
        self.kind = np.array(kind)
        self.corr = {k: np.concatenate(v) for k, v in CP.items() if np.abs(np.concatenate(v)).max() > 0}
        self.corrN = {k: np.concatenate(CN[k]) for k in self.corr}
        if self.split_here:
            import helpers as hp
            dense = np.zeros((len(self.P), len(sk.names)))
            for k in range(self.J.shape[1]):
                np.add.at(dense, (np.arange(len(self.P)), self.J[:, k]), self.W[:, k])
            heads = {n: self.rest[j][:3, 3] for n, j in sk.index.items()}
            dense = hp.split(dense, self.P, sk.index, heads, front=(0.0, 0.0, 1.0))
            order = np.argsort(-dense, axis=1)[:, :4]
            self.J = self.Jv = order
            self.W = np.take_along_axis(dense, order, 1)
            self.W = self.W / np.maximum(self.W.sum(1, keepdims=True), 1e-12)
            # Her corrective shapes made here as the build makes them (her
            # skin's; the shape's normals as Blender's shape key normals: of
            # the moved points, welded).
            idx = np.nonzero(self.kind == "skin")[0]
            if len(idx) and not self.corr:
                D = np.zeros((len(idx), len(sk.names)))
                for k in range(4):
                    np.add.at(D, (np.arange(len(idx)), self.J[idx, k]), self.W[idx, k])
                Ts = self.T[(self.kind[self.T] == "skin").all(1)]
                n0 = _normals(self.P, Ts)
                for k, d in hp.corrective(self.P[idx], D, sk, front=(0.0, 0.0, 1.0)).items():
                    full = np.zeros_like(self.P)
                    full[idx] = d
                    self.corr[k] = full
                    self.corrN[k] = _normals(self.P + full, Ts) - n0
        # What moves each point: the part holding most of its weight, and how
        # much of its weight that part holds.
        parts = ["trunk", "arm_l", "arm_r", "leg_l", "leg_r"]
        bone_part = np.array([parts.index(part_of(n)) for n in sk.names])
        share = np.zeros((len(self.P), len(parts)))
        for k in range(self.J.shape[1]):
            np.add.at(share, (np.arange(len(self.P)), bone_part[self.J[:, k]]), self.W[:, k])
        self.parts = parts
        self.part = share.argmax(1)
        self.share = share

    @staticmethod
    def _mats(grot, gpos, scale=None, shift=None):
        n = len(grot)
        M = np.tile(np.eye(4), (n, 1, 1))
        for j in range(n):
            R = qmatrix(grot[j])
            M[j, :3, :3] = R
            if scale is not None:
                M[j, :3, :3] = R @ np.diag(scale[j])
            M[j, :3, 3] = gpos[j] if shift is None else gpos[j] + R @ shift[j]
        return M

    # -------------------------------------------------------- the factories --
    @staticmethod
    def heroine(outfit=None, jiggle=True, body_file=None, helpers=False, head=False):
        sk = Skeleton.load(SKELETONS / "heroine_skeleton.json")
        keep = ("Heroine", "HeroineHead") if head else ("Heroine",)
        files = [(Path(body_file) if body_file else PEOPLE / "heroine.glb", lambda n: n in keep, "skin")]
        if outfit:
            files.append((PEOPLE / f"heroine_outfit_{outfit}.gltf", lambda n, o=outfit: n.startswith(o + "."), "garment"))
        jig = None
        if jiggle:
            jig = Jiggle(sk, amount=0.55 if outfit == "warden" else 1.0, squash=0.0 if outfit == "warden" else 1.0)
        return Body(sk, files, jig, label="her", helpers=helpers)

    @staticmethod
    def hero(body_file=None, helpers=False):
        sk = Skeleton.load(SKELETONS / "hero_skeleton.json")
        g = Gltf(Path(body_file) if body_file else PEOPLE / "hero.glb")
        # His body is the skinned mesh that is not a part of his head.
        heads = ("HeroHead", "HeroEyes", "HeroLashes", "HeroTeeth", "HeroTongue")
        files = [(g.path, lambda n: n not in heads, "skin")]
        return Body(sk, files, None, label="him", helpers=helpers)

    # ------------------------------------------------------------- clips --
    def clip(self, name, folder=None):
        folder = Path(folder) if folder else OUT / ("clips" if self.label == "her" else "hero")
        d = json.loads((folder / f"{name}.json").read_text())
        if self.label == "her" and staged.want():
            d = staged.staged_json(d)   # the clip as the game plays it (tools/anim/staged.py; --raw: as written)
        sk = self.sk
        n = len(d["tracks"][0]["keys"])
        rot = np.tile(sk.rest_rot, (n, 1, 1)).astype(float)
        pos = np.tile(sk.rest_pos, (n, 1, 1)).astype(float)
        for t in d["tracks"]:
            j = sk.index.get(t["bone"])
            if j is None:
                continue
            k = np.array(t["keys"], float)
            if t["type"] == "rot":
                rot[:, j] = k
            else:
                pos[:, j] = k
        return Clip(d["name"], d["fps"], rot, pos, d.get("loop", False), d.get("meta", {}))

    def game_rig(self):
        """Her body of record's rig (the shoulder helpers, SPEC "shoulder", in her skeleton): posed with the game's
        whole stack (HerRaise's breast lift, the twist roll unwrapped frame to frame, HerShoulder). Bodies before it
        keep the posing their baselines were counted with. SKIN_GAME=1/0 (env) forces it on or off."""
        import helpers as hp
        v = os.environ.get("SKIN_GAME")
        return (v == "1") if v in ("0", "1") else any(hp.has_shoulder(self.sk.index, s) for s in "lr")

    def globals(self, clip: Clip, f, state=None, dt=None):
        """Bone globals [J, 4, 4] of frame f (no springs; her helpers driven
        as the game drives them). `state` (a dict kept from frame to frame,
        {} at the first) and `dt`: the game rig's twist roll unwrapped as the
        game does (frames passes them)."""
        rot = clip.rot[f]
        pos = clip.pos[f]
        scale = shift = None
        game = self.helpers and self.game_rig()
        if self.helpers:
            import helpers as hp
            scale = np.ones((len(self.sk.names), 3))
            shift = np.zeros((len(self.sk.names), 3))
            rot = hp.drive(self.sk, rot.copy(), scale, shift, state if game else None, dt, panels=False)
            if game:
                # HerRaise's pull on her breasts (after HerShrug, before the springs), at the worn top's squash
                pos = pos.copy()
                hp.raise_breasts(self.sk, rot, pos, scale, self.jiggle.squash if self.jiggle else 1.0)
        grot, gpos = self.sk.fk(rot[None], pos[None])
        # (A bone's own scale and shift reach only itself: the helpers have no children.)
        G = self._mats(grot[0], gpos[0], scale, shift)
        if game:
            for j, sc in self.rest_scale.items():
                # (a bone's pose scale is its rest's unless a layer sets it; applied to itself: Head is a leaf)
                G[j, :3, :3] = G[j, :3, :3] * sc
            import helpers as hp
            hp.drive_shoulder(self.sk, G)   # HerShoulder: last, from the pose every layer above has made
        return G

    def world(self, clip: Clip, f):
        """Where the skeleton stands in the world at frame f: scaled as the
        game scales her, carried forward at the clip's own speed (a loop runs
        on the spot while she moves)."""
        m = np.diag([self.world_scale] * 3 + [1.0])
        v = float(clip.meta.get("speed", 0) or 0) * self.world_scale
        m[2, 3] = v * f / clip.fps
        return m

    def frames(self, clip: Clip, settle=True):
        """Every frame's bone globals with the springs run through the clip
        (a loop is run twice and the second pass kept, so the springs start
        as they would mid-run)."""
        out = []
        if self.jiggle:
            self.jiggle.reset()
            self.jiggle.keep_scale = self.helpers and self.game_rig()
        passes = 2 if (clip.loop and settle) else 1
        st = {}   # (the twist roll's unwrap, carried through both passes as the game plays on)
        for p in range(passes):
            keep = p == passes - 1
            for f in range(clip.frames):
                G = self.globals(clip, f, st, 1 / clip.fps)
                if self.jiggle:
                    self.jiggle.apply(G, self.world(clip, f + p * (clip.frames - 1)), 1 / clip.fps)
                if keep:
                    out.append(G)
        return out

    def skin_mats(self, G):
        """Skinning matrices, indexed by Jv: each bone's posed global over its bind (its rest; then the game rig's
        off-rest binds, vbind)."""
        S = G @ self.rest_inv
        if self.vbind:
            S = np.concatenate([S, np.stack([G[j] @ m for j, m in self.vbind])])
        return S

    def shape_weights(self, G):
        """Her corrective shapes' weights for globals G: each keyed on its
        joint's bend (helpers.corrective_weights), read from G."""
        if not self.corr:
            return {}
        import helpers as hp
        rot = self.sk.rest_rot.copy()
        for c in hp.SPEC.get("correctives", []):
            for s in "lr":
                j = self.sk.index.get(c["bone"].replace("{s}", s))
                if j is None:
                    continue
                a, b = G[self.sk.parent[j]][:3, :3], G[j][:3, :3]
                a, b = a / np.linalg.norm(a, axis=0), b / np.linalg.norm(b, axis=0)
                rot[j] = qnorm(qfrom_matrix(a.T @ b))
        out = {k: w for k, w in hp.corrective_weights(self.sk, rot).items() if k in self.corr and w > 0}
        # her shoulder pose-space shapes (tools/assets/shoulder_psd_post.py), from the arms' directions as HerRaise sets them
        if any(k.startswith("shoulder_") for k in self.corr):
            out.update({k: w for k, w in _psd().weights_from_globals(G, self.sk.index, self.rest).items() if k in self.corr and w > 0})
        return out

    def rest_points(self, G, idx=None):
        """Her points at rest with her corrective shapes in, as set for G."""
        P = self.P if idx is None else self.P[idx]
        for k, w in self.shape_weights(G).items():
            P = P + w * (self.corr[k] if idx is None else self.corr[k][idx])
        return P

    def rest_normals(self, N, G):
        """Rest normals N [V, 3] with her corrective shapes' in, as set for G."""
        sw = self.shape_weights(G)
        if not sw:
            return N
        for k, w in sw.items():
            N = N + w * self.corrN[k]
        return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)

    def pose(self, G, idx=None):
        """Posed points [V, 3] (or only `idx`) for globals G (her corrective
        shapes in, as the game sets them)."""
        S = self.skin_mats(G)
        J = self.Jv if idx is None else self.Jv[idx]
        W = self.W if idx is None else self.W[idx]
        P = self.rest_points(G, idx)
        Ph = np.concatenate([P, np.ones((len(P), 1))], 1)
        out = np.zeros((len(P), 3))
        for k in range(J.shape[1]):
            M = S[J[:, k]]
            out += W[:, k:k + 1] * np.einsum("nij,nj->ni", M[:, :3, :], Ph)
        return out
