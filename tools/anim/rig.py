"""Her skeleton, and the arithmetic every clip is made with.

Godot's conventions throughout: quaternions are (x, y, z, w), Y is up, she
faces +Z and her left is +X. A bone's pose is its transform in its parent's
space, rest included (what an Animation's rotation_3d / position_3d tracks
hold); a bone's global is its transform in the skeleton's space.

The skeleton comes from tools/anim/data/heroine_skeleton.json, which
godot/tools_scenes/anim_skeleton.gd writes from art/people/heroine.glb, so the
numbers are the ones Godot itself will play against.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DATA = HERE / "data"


# --------------------------------------------------------------- quaternions --
def q(x=0.0, y=0.0, z=0.0, w=1.0):
    return np.array([x, y, z, w], dtype=float)


def qmul(a, b):
    """a then b applied to a vector is qmul(a, b) (a outer): (a*b)v = a(b v)."""
    ax, ay, az, aw = np.moveaxis(np.asarray(a, float), -1, 0)
    bx, by, bz, bw = np.moveaxis(np.asarray(b, float), -1, 0)
    return np.stack([
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    ], axis=-1)


def qinv(a):
    a = np.asarray(a, float)
    return a * np.array([-1, -1, -1, 1.0])


def qnorm(a):
    a = np.asarray(a, float)
    return a / np.linalg.norm(a, axis=-1, keepdims=True)


def qrot(a, v):
    """Rotate vector(s) v by quaternion(s) a."""
    a = np.asarray(a, float)
    v = np.asarray(v, float)
    u = a[..., :3]
    w = a[..., 3:4]
    t = 2.0 * np.cross(u, v)
    return v + w * t + np.cross(u, t)


def qaxis(axis, deg):
    axis = np.asarray(axis, float)
    axis = axis / np.linalg.norm(axis)
    h = math.radians(deg) / 2
    return np.array([*(axis * math.sin(h)), math.cos(h)])


def qbetween(a, b):
    """The smallest rotation taking direction a onto direction b."""
    a = np.asarray(a, float) / np.linalg.norm(a)
    b = np.asarray(b, float) / np.linalg.norm(b)
    d = float(np.dot(a, b))
    if d < -0.999999:
        ortho = np.cross([1, 0, 0], a)
        if np.linalg.norm(ortho) < 1e-6:
            ortho = np.cross([0, 1, 0], a)
        return qaxis(ortho, 180)
    c = np.cross(a, b)
    r = np.array([c[0], c[1], c[2], 1 + d])
    return r / np.linalg.norm(r)


def qslerp(a, b, t):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    d = float(np.dot(a, b))
    if d < 0:
        b, d = -b, -d
    if d > 0.9995:
        r = a + (b - a) * t
        return r / np.linalg.norm(r)
    th = math.acos(min(1.0, d))
    s = math.sin(th)
    return (math.sin((1 - t) * th) / s) * a + (math.sin(t * th) / s) * b


def qfrom_basis(x, y, z):
    """The rotation whose columns are the given axes (orthonormal)."""
    m = np.stack([x, y, z], axis=1)
    return qfrom_matrix(m)


def qfrom_matrix(m):
    m = np.asarray(m, float)
    tr = m[0, 0] + m[1, 1] + m[2, 2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        w = 0.25 * s
        x = (m[2, 1] - m[1, 2]) / s
        y = (m[0, 2] - m[2, 0]) / s
        z = (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        w = (m[2, 1] - m[1, 2]) / s
        x = 0.25 * s
        y = (m[0, 1] + m[1, 0]) / s
        z = (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        w = (m[0, 2] - m[2, 0]) / s
        x = (m[0, 1] + m[1, 0]) / s
        y = 0.25 * s
        z = (m[1, 2] + m[2, 1]) / s
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        w = (m[1, 0] - m[0, 1]) / s
        x = (m[0, 2] + m[2, 0]) / s
        y = (m[1, 2] + m[2, 1]) / s
        z = 0.25 * s
    return qnorm(np.array([x, y, z, w]))


def qmatrix(a):
    x, y, z, w = a
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def qeuler(yaw=0.0, pitch=0.0, roll=0.0):
    """Character-space turn in degrees: yaw about up (+ to her left), pitch
    about her left-right axis (+ leans forward), roll about forward (+ tips
    her toward her right). Applied roll, then pitch, then yaw. (She faces +Z
    with her left at +X: a turn about +Y takes her nose toward her left, about
    +X tips her head forward, about +Z tips it toward her right.)"""
    return qmul(qaxis([0, 1, 0], yaw), qmul(qaxis([1, 0, 0], pitch), qaxis([0, 0, 1], roll)))


def qangle(a):
    return math.degrees(2 * math.acos(min(1.0, abs(float(a[3])))))


def qcontinuous(qs):
    """Flip signs along a sequence so neighbours agree (no long-way slerps)."""
    out = np.array(qs, float)
    for i in range(1, len(out)):
        if np.dot(out[i], out[i - 1]) < 0:
            out[i] = -out[i]
    return out


# ------------------------------------------------------------------ skeleton --
@dataclass
class Skeleton:
    names: list
    parent: list
    rest_rot: np.ndarray        # [J, 4] local
    rest_pos: np.ndarray        # [J, 3] local
    path: str = "Armature/Skeleton3D"
    index: dict = field(default_factory=dict)

    @staticmethod
    def load(path=DATA / "heroine_skeleton.json") -> "Skeleton":
        d = json.loads(Path(path).read_text())
        bones = d["bones"]
        s = Skeleton(
            names=[b["name"] for b in bones], parent=[b["parent"] for b in bones],
            rest_rot=np.array([b["rot"] for b in bones], float), rest_pos=np.array([b["pos"] for b in bones], float),
            path=d["skeleton_path"])
        s.index = {n: i for i, n in enumerate(s.names)}
        return s

    def __len__(self):
        return len(self.names)

    def i(self, name):
        return self.index[name]

    def children(self, j):
        return [k for k, p in enumerate(self.parent) if p == j]

    def fk(self, rot, pos=None):
        """Globals from local poses: rot [..., J, 4], pos [..., J, 3] (rest
        positions if None). Returns (grot, gpos)."""
        rot = np.asarray(rot, float)
        if pos is None:
            pos = np.broadcast_to(self.rest_pos, rot.shape[:-1] + (3,))
        grot = np.empty_like(rot)
        gpos = np.empty(rot.shape[:-1] + (3,))
        for j, p in enumerate(self.parent):
            if p < 0:
                grot[..., j, :] = rot[..., j, :]
                gpos[..., j, :] = pos[..., j, :]
            else:
                grot[..., j, :] = qmul(grot[..., p, :], rot[..., j, :])
                gpos[..., j, :] = gpos[..., p, :] + qrot(grot[..., p, :], pos[..., j, :])
        return grot, gpos

    def rest_globals(self):
        return self.fk(self.rest_rot[None], self.rest_pos[None])

    def local_from_global(self, grot, j):
        """A bone's local rotation for a wanted global one, given its parent's
        global (grot holds the parents' globals already)."""
        p = self.parent[j]
        return grot[..., j, :] if p < 0 else qmul(qinv(grot[..., p, :]), grot[..., j, :])


# ------------------------------------------------------------------------ IK --
def two_bone_ik(a, b, c, target, pole):
    """Upper bone from a to b, lower from b to c. Returns the new b and c
    positions reaching for target, the knee/elbow bent toward pole. Lengths
    are kept; out of reach it straightens (a hair short of fully, so the
    joint never pops)."""
    l1 = np.linalg.norm(b - a)
    l2 = np.linalg.norm(c - b)
    d = target - a
    dist = np.linalg.norm(d)
    dist = min(max(dist, abs(l1 - l2) + 1e-4), (l1 + l2) * 0.9995)
    dn = d / max(np.linalg.norm(d), 1e-9)
    # Angle at a between the reach line and the upper bone.
    cos_a = (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist)
    ang = math.acos(max(-1.0, min(1.0, cos_a)))
    side = pole - a
    side = side - dn * np.dot(side, dn)
    if np.linalg.norm(side) < 1e-6:
        side = np.cross(dn, [1, 0, 0])
    side = side / np.linalg.norm(side)
    nb = a + dn * (l1 * math.cos(ang)) + side * (l1 * math.sin(ang))
    nc = a + dn * dist
    return nb, nc


def aim(grot_bone, gpos_head, gpos_child_now, gpos_child_want):
    """Turn a bone (global rotation) so its child moves from now to want."""
    r = qbetween(gpos_child_now - gpos_head, gpos_child_want - gpos_head)
    return qmul(r, grot_bone)


# --------------------------------------------------------------------- clips --
@dataclass
class Clip:
    """A clip on her skeleton: local rotations for every bone per frame, the
    pelvis (and root) positions, at `fps`. `meta` goes to the game (speed in
    metres a second of her own skeleton, contact frames, the layer)."""
    name: str
    fps: float
    rot: np.ndarray             # [T, J, 4]
    pos: np.ndarray             # [T, J, 3]
    loop: bool = False
    meta: dict = field(default_factory=dict)

    @property
    def frames(self):
        return self.rot.shape[0]

    @property
    def length(self):
        # A loop's last frame is its first again, so either way the clip
        # runs from the first frame to the last.
        return (self.frames - 1) / self.fps

    def to_json(self, sk: Skeleton, moving=None):
        """The clip as godot/tools_scenes/anim_pack.gd reads it: a track for
        every bone that moves from rest (or `moving`), positions for the root
        and the pelvis."""
        rot = np.array([qcontinuous(self.rot[:, j]) for j in range(len(sk))]).transpose(1, 0, 2)
        tracks = []
        for j, n in enumerate(sk.names):
            r = rot[:, j]
            varies = np.max(np.abs(r - r[0])) > 1e-5 or np.max(np.abs(r[0] - sk.rest_rot[j])) > 1e-5
            if moving is not None:
                varies = n in moving or varies
            if varies:
                tracks.append({"bone": n, "type": "rot", "keys": np.round(r, 6).tolist()})
        for n in ("root", "pelvis"):
            j = sk.i(n)
            p = self.pos[:, j]
            if np.max(np.abs(p - sk.rest_pos[j])) > 1e-5 or n == "pelvis":
                tracks.append({"bone": n, "type": "pos", "keys": np.round(p, 6).tolist()})
        return {"name": self.name, "fps": self.fps, "loop": self.loop, "length": self.length,
                "path": sk.path, "tracks": tracks, "meta": self.meta}


def write_clip(clip: Clip, sk: Skeleton, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{clip.name}.json").write_text(json.dumps(clip.to_json(sk), separators=(",", ":")))


# ------------------------------------------------------- character space ---
# The root bone turns the skeleton's Z-up into Godot's Y-up: the pelvis's
# position is held in the root's space.
def root_space(sk: Skeleton, v):
    return qrot(qinv(sk.rest_rot[sk.i("root")]), v)


def from_root_space(sk: Skeleton, v):
    return qrot(sk.rest_rot[sk.i("root")], v)


def smoothstep(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)
