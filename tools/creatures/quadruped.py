"""The four-legged rig and its clips, keyed as functions of the stride.

Runs inside Blender (bpy, mathutils). One skeleton for every beast on four
legs (the boar first, the wolf later), built from a creature's landmarks:

    Root
      Pelvis -> Spine1 -> Spine2 -> Chest -> Neck1 -> Neck2 -> Head -> Snout
                                                                  Jaw, Ear_L/R
                                      Chest -> Scapula -> Arm -> Forearm -> Wrist -> FrontToe -> FrontToeEnd
             Pelvis -> Thigh -> Shin -> Hock -> HindToe -> HindToeEnd
             Pelvis -> Tail1 -> Tail2 -> Tail3 -> TailEnd

Conventions (agreed with animation): Blender -Y is the beast's front (glTF
+Z), +Z up, +X its left; hooves flat at z 0 in the rest pose, the legs
straight under it; bones along their own +Y, the left side's local X out to
its left and the right's mirrored; clips in place, the root at the origin.

A clip is a function from its time (0..1) to a pose, built by a Poser: the
body's bones turned in the armature's space, and each leg placed by where its
hoof is (planted on the ground through the stance, travelling back under the
body at exactly the ground's speed, so in the game the hooves hold still) and
how its lower joints fold, solved as a two-bone chain. Every frame is then
keyed as plain rotations, so nothing but the bones' curves leaves Blender.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import bpy
from mathutils import Matrix, Quaternion, Vector

FWD = Vector((0, -1, 0))
UP = Vector((0, 0, 1))
LEFT = Vector((1, 0, 0))

SIDES = ("L", "R")
FRONT = ["Scapula", "Arm", "Forearm", "Wrist", "FrontToe", "FrontToeEnd"]
HIND = ["Thigh", "Shin", "Hock", "HindToe", "HindToeEnd"]


def mirror(p):
    return Vector((-p[0], p[1], p[2]))


# ------------------------------------------------------------------ rig --
def build_armature(lm, name="Armature"):
    """The skeleton from a creature's landmarks (left side given; the right
    mirrored), as a new armature object at the origin.

    lm keys: pelvis spine1 spine2 chest neck1 neck2 head snout snout_end jaw
    jaw_end ear ear_end tail1 tail2 tail3 tail_end scapula shoulder elbow
    carpus fetlock front_toe hip stifle hock hind_fetlock hind_toe."""
    L = {k: Vector(v) for k, v in lm.items()}
    data = bpy.data.armatures.new(name)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    eb = data.edit_bones

    def bone(n, head, tail, parent=None, connect=False, side_axis=LEFT):
        b = eb.new(n)
        b.head, b.tail = Vector(head), Vector(tail)
        y = (b.tail - b.head).normalized()
        # Local X out to the beast's left (mirrored later for the right):
        # a bend in its own plane is a turn about X.
        x = (side_axis - y * side_axis.dot(y))
        if x.length < 1e-4:
            x = UP.cross(y)
        b.align_roll(x.normalized().cross(y))
        if parent:
            b.parent = eb[parent]
            b.use_connect = connect
        b.use_deform = True
        return b

    bone("Root", (0, 0, 0), (0, 0.25, 0))
    bone("Pelvis", L["pelvis"], L["spine1"], "Root")
    bone("Spine1", L["spine1"], L["spine2"], "Pelvis", True)
    bone("Spine2", L["spine2"], L["chest"], "Spine1", True)
    bone("Chest", L["chest"], L["neck1"], "Spine2", True)
    bone("Neck1", L["neck1"], L["neck2"], "Chest", True)
    bone("Neck2", L["neck2"], L["head"], "Neck1", True)
    bone("Head", L["head"], L["snout"], "Neck2", True)
    bone("Snout", L["snout"], L["snout_end"], "Head", True)
    bone("Jaw", L["jaw"], L["jaw_end"], "Head")
    bone("Tail1", L["tail1"], L["tail2"], "Pelvis")
    bone("Tail2", L["tail2"], L["tail3"], "Tail1", True)
    bone("Tail3", L["tail3"], L["tail_end"], "Tail2", True)
    tdir = (L["tail_end"] - L["tail3"]).normalized()
    bone("TailEnd", L["tail_end"], L["tail_end"] + tdir * 0.04, "Tail3", True)
    for s in SIDES:
        m = (lambda p: Vector(p)) if s == "L" else mirror
        ax = LEFT if s == "L" else -LEFT
        bone(f"Ear_{s}", m(L["ear"]), m(L["ear_end"]), "Head", side_axis=ax)
        bone(f"Scapula_{s}", m(L["scapula"]), m(L["shoulder"]), "Chest", side_axis=ax)
        bone(f"Arm_{s}", m(L["shoulder"]), m(L["elbow"]), f"Scapula_{s}", True, side_axis=ax)
        bone(f"Forearm_{s}", m(L["elbow"]), m(L["carpus"]), f"Arm_{s}", True, side_axis=ax)
        bone(f"Wrist_{s}", m(L["carpus"]), m(L["fetlock"]), f"Forearm_{s}", True, side_axis=ax)
        bone(f"FrontToe_{s}", m(L["fetlock"]), m(L["front_toe"]), f"Wrist_{s}", True, side_axis=ax)
        bone(f"FrontToeEnd_{s}", m(L["front_toe"]), m(L["front_toe"]) + FWD * 0.03, f"FrontToe_{s}", True, side_axis=ax)
        bone(f"Thigh_{s}", m(L["hip"]), m(L["stifle"]), "Pelvis", side_axis=ax)
        bone(f"Shin_{s}", m(L["stifle"]), m(L["hock"]), f"Thigh_{s}", True, side_axis=ax)
        bone(f"Hock_{s}", m(L["hock"]), m(L["hind_fetlock"]), f"Shin_{s}", True, side_axis=ax)
        bone(f"HindToe_{s}", m(L["hind_fetlock"]), m(L["hind_toe"]), f"Hock_{s}", True, side_axis=ax)
        bone(f"HindToeEnd_{s}", m(L["hind_toe"]), m(L["hind_toe"]) + FWD * 0.03, f"HindToe_{s}", True, side_axis=ax)
    # Leaves carry no skin: they are there for IK and for baking.
    for n in ["Root", "TailEnd"] + [f"{k}_{s}" for s in SIDES for k in ("FrontToeEnd", "HindToeEnd")]:
        eb[n].use_deform = False
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in obj.pose.bones:
        pb.rotation_mode = "QUATERNION"
    return obj


# ---------------------------------------------------------------- poser --
class Poser:
    """A pose built in the armature's space, bone by bone from the root:
    each operation is applied over the parents' poses as they stand, and
    every bone's local rotation (and the pelvis's move) is read off at the
    end. Bones not touched keep their rest."""

    def __init__(self, arm):
        self.arm = arm
        self.bones = arm.data.bones
        self.basis = {b.name: Matrix.Identity(4) for b in self.bones}
        self.rest = {b.name: b.matrix_local.copy() for b in self.bones}
        self.rel = {b.name: (b.parent.matrix_local.inverted() @ b.matrix_local) if b.parent else b.matrix_local.copy() for b in self.bones}
        self._memo = {}

    def matrix(self, n):
        """The bone's posed matrix in the armature's space."""
        if n in self._memo:
            return self._memo[n]
        b = self.bones[n]
        m = (self.matrix(b.parent.name) if b.parent else Matrix.Identity(4)) @ self.rel[n] @ self.basis[n]
        self._memo[n] = m
        return m

    def head(self, n):
        return self.matrix(n).translation.copy()

    def tail(self, n):
        return self.matrix(n) @ Vector((0, self.bones[n].length, 0))

    def _changed(self, n):
        # Everything under the bone moves with it.
        stack = [self.bones[n]]
        while stack:
            b = stack.pop()
            self._memo.pop(b.name, None)
            stack.extend(b.children)

    def _set_posed(self, n, posed):
        b = self.bones[n]
        parent = self.matrix(b.parent.name) if b.parent else Matrix.Identity(4)
        self.basis[n] = (parent @ self.rel[n]).inverted() @ posed
        self._changed(n)

    def turn(self, n, axis, angle, about=None):
        """Turned by angle (radians) about an axis in the armature's space,
        through its head (or a point given)."""
        if abs(angle) < 1e-9:
            return self
        m = self.matrix(n)
        c = m.translation if about is None else Vector(about)
        r = Quaternion(Vector(axis).normalized(), angle).to_matrix().to_4x4()
        self._set_posed(n, Matrix.Translation(c) @ r @ Matrix.Translation(-c) @ m)
        return self

    def bend(self, n, pitch=0.0, yaw=0.0, roll=0.0):
        """Turned about the beast's own axes at the bone: pitch about its
        left (+: what points forward dips), yaw about up (+: what points
        forward swings to its left), roll about its front (+: its left side
        rises)."""
        self.turn(n, LEFT, pitch)
        self.turn(n, UP, yaw)
        self.turn(n, FWD, roll)
        return self

    def local(self, n, x=0.0, y=0.0, z=0.0):
        """Turned about the bone's own axes (X: its bend, Y: its twist)."""
        m = self.matrix(n)
        r = (Quaternion((1, 0, 0), x) @ Quaternion((0, 1, 0), y) @ Quaternion((0, 0, 1), z)).to_matrix().to_4x4()
        self._set_posed(n, m @ r)
        return self

    def move(self, n, offset):
        """Moved by an offset in the armature's space."""
        self._set_posed(n, Matrix.Translation(Vector(offset)) @ self.matrix(n))
        return self

    def aim(self, n, target):
        """Turned so its tail points at a target (the shortest turn, so it
        does not twist about itself)."""
        m = self.matrix(n)
        cur = (m.to_3x3() @ Vector((0, 1, 0))).normalized()
        want = (Vector(target) - m.translation)
        if want.length < 1e-6:
            return self
        q = cur.rotation_difference(want.normalized())
        self.turn(n, q.axis, q.angle)
        return self

    def apply(self):
        """Onto the armature's pose bones."""
        for pb in self.arm.pose.bones:
            m = self.basis[pb.name]
            pb.rotation_quaternion = m.to_quaternion()
            pb.location = m.translation if pb.name in ("Root", "Pelvis") else Vector()
            pb.scale = Vector((1, 1, 1))

    def key(self, frame):
        self.apply()
        for pb in self.arm.pose.bones:
            pb.keyframe_insert("rotation_quaternion", frame=frame, group=pb.name)
            if pb.name in ("Root", "Pelvis"):
                pb.keyframe_insert("location", frame=frame, group=pb.name)


def two_bone(a, c, l1, l2, bend):
    """Where the middle joint of a two-bone chain from a to c goes, bent
    toward the direction `bend` (a stretch past full reach is held straight)."""
    d = c - a
    dist = max(1e-6, min(d.length, (l1 + l2) * 0.9999))
    u = d.normalized()
    x = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(0.0, l1 * l1 - x * x))
    b = bend - u * bend.dot(u)
    if b.length < 1e-6:
        b = UP.cross(u)
    return a + u * x + b.normalized() * h


# ------------------------------------------------------------------ legs --
@dataclass
class Leg:
    """One leg as the poser places it: its bones top to bottom, which way
    its middle joint bends (the elbow back, the stifle forward), and its
    rest: the hoof's fetlock and toe, the metapodial (cannon) as a vector up
    from the fetlock."""
    top: str          # the bone whose head is the chain's top joint (Arm, Thigh)
    mid: str          # (Forearm, Shin)
    meta: str         # (Wrist, Hock)
    toe: str          # (FrontToe, HindToe)
    bend: Vector
    sign: float = 1.0  # +1: the hoof folds back (a foreleg's knee); -1: forward (a hind leg's hock)
    fetlock: Vector = field(default_factory=Vector)
    toe_tip: Vector = field(default_factory=Vector)
    cannon: Vector = field(default_factory=Vector)


def legs(arm):
    out = {}
    for s in SIDES:
        for kind, (top, mid, meta, toe, bend) in {
            "F": ("Arm", "Forearm", "Wrist", "FrontToe", -FWD),
            "H": ("Thigh", "Shin", "Hock", "HindToe", FWD),
        }.items():
            b = arm.data.bones
            fet = b[f"{toe}_{s}"].head_local.copy()
            out[kind + s] = Leg(f"{top}_{s}", f"{mid}_{s}", f"{meta}_{s}", f"{toe}_{s}", bend.copy(), 1.0 if kind == "F" else -1.0, fet,
                                b[f"{toe}_{s}"].tail_local.copy(), b[f"{meta}_{s}"].head_local - fet)
    return out


def place_leg(p: Poser, leg: Leg, fetlock: Vector, fold: float, toe_pitch: float = 0.0):
    """A leg put down with its fetlock at a point: the cannon turned from
    its rest by `fold` (radians; +: folded as in the swing, a foreleg's hoof
    drawn back and up behind its knee, a hind leg's forward under its hock),
    the upper two bones solved to reach the top of the cannon, and the toe
    pitched from its rest (+: its tip down)."""
    cannon = Quaternion(LEFT, leg.sign * fold) @ leg.cannon
    top = fetlock + cannon
    a = p.head(leg.top)
    l1 = p.bones[leg.top].length
    l2 = p.bones[leg.mid].length
    mid = two_bone(a, top, l1, l2, leg.bend)
    p.aim(leg.top, mid)
    p.aim(leg.mid, top)
    p.aim(leg.meta, fetlock)
    rest_toe = leg.toe_tip - leg.fetlock
    p.aim(leg.toe, p.head(leg.toe) + Quaternion(LEFT, toe_pitch) @ rest_toe)


# ----------------------------------------------------------------- gaits --
def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


@dataclass
class Gait:
    """A stride cycle (in place). Phases: when each foot touches down, as a
    fraction of the cycle. Duty: the fraction a foot is planted."""
    period: float                       # seconds per cycle
    speed: float                        # metres a second of the ground under it (model units)
    duty: float
    phase: dict                         # {"FL": 0, "HR": 0, "FR": .5, "HL": .5}
    lift: dict = field(default_factory=lambda: {"F": 0.12, "H": 0.1})
    fold: dict = field(default_factory=lambda: {"F": 1.9, "H": 0.9})
    reach: dict = field(default_factory=lambda: {"F": 0.0, "H": 0.0})   # where the stride centres, forward of rest
    bob: float = 0.03                   # the body's rise and fall
    bobs: int = 2                       # rises a cycle (a trot two, a gallop one)
    bob_phase: float = 0.0
    pitch: float = 0.0                  # the body rocking nose-down/up a cycle (gallop)
    flex: float = 0.0                   # the back's flexion a cycle (gallop)
    roll: float = 0.02
    head_low: float = 0.0               # the head carried lower (radians, +: down)
    scapula: float = 0.18               # the shoulder blade swinging with the foreleg


def foot(g: Gait, key: str, t: float, leg: Leg):
    """A foot at the cycle's time t (0..1): its fetlock, its cannon's fold
    and its toe's pitch."""
    kind = key[0]
    ph = (t - g.phase[key]) % 1.0
    stride = g.speed * g.period * g.duty           # how far it travels back while planted
    centre = leg.fetlock + FWD * g.reach[kind]
    if ph < g.duty:
        s = ph / g.duty
        pos = centre + FWD * (stride / 2 - stride * s)
        # Rolling off the toe at the end of the stance: the heel up.
        off = smooth((s - 0.75) / 0.25)
        pos.z += 0.035 * off
        fold = 0.35 * off if kind == "F" else 0.25 * off
        pitch = 0.5 * off
        return pos, fold, pitch
    s = (ph - g.duty) / (1 - g.duty)
    # The swing: forward with the speed easing in and out, up early and
    # set down gently; the lower leg folded through the middle of it and
    # opened out to reach before it lands.
    f = smooth(s)
    pos = centre + FWD * (-stride / 2 + stride * f)
    pos.z += g.lift[kind] * math.sin(math.pi * min(1.0, s * 1.08)) ** 1.3
    fold = g.fold[kind] * math.sin(math.pi * min(1.0, s * 1.25)) ** 1.5
    if s > 0.8:
        fold *= max(0.0, 1 - (s - 0.8) / 0.2)
    pitch = 0.9 * math.sin(math.pi * s) - 0.15 * smooth((s - 0.75) / 0.25)
    return pos, fold, pitch


def pose_gait(p: Poser, g: Gait, t: float, legs_: dict, extra=None):
    """A gait's pose at cycle time t."""
    a = 2 * math.pi * (t + g.bob_phase)
    p.move("Pelvis", (0, 0, -g.bob * 0.5 + g.bob * 0.5 * math.cos(a * g.bobs)))
    p.bend("Pelvis", pitch=g.pitch * math.sin(a), roll=g.roll * math.sin(a))
    # The back flexes (gathers) and extends against the pelvis's rock.
    for n, w in (("Spine1", 0.4), ("Spine2", 0.35), ("Chest", 0.25)):
        p.bend(n, pitch=-g.flex * w * math.sin(a) - g.pitch * w * math.sin(a) * 0.6)
    # The head held steadier than the body, carried low if charging.
    p.bend("Neck1", pitch=g.head_low * 0.5 + g.pitch * 0.3 * math.sin(a))
    p.bend("Head", pitch=g.head_low * 0.5 - g.bob * 2.0 * math.cos(a * g.bobs))
    for s in SIDES:
        # The shoulder blade swings with its foreleg.
        ph = (t - g.phase["F" + s]) % 1.0
        sw = math.cos(2 * math.pi * (ph - g.duty / 2) / 1.0)
        p.bend(f"Scapula_{s}", pitch=-g.scapula * 0.5 * sw)
    for key, leg in legs_.items():
        k = key[0] + key[1]
        pos, fold, pitch = foot(g, key, t, leg)
        place_leg(p, leg, pos, fold, pitch)
    p.bend("Tail1", pitch=0.15 * math.sin(a * g.bobs + 1.0))
    if extra:
        extra(p, t)


# ----------------------------------------------------------------- clips --
def key_clip(arm, name, seconds, fps, pose, loop=False):
    """A clip as an action: pose(p, t) for t in 0..1 over its frames. A
    looped clip's last frame is its first, so the loop closes exactly."""
    action = bpy.data.actions.new(name)
    arm.animation_data_create()
    arm.animation_data.action = action
    frames = max(2, int(round(seconds * fps)))
    for f in range(frames + 1):
        t = f / frames
        p = Poser(arm)
        pose(p, t % 1.0 if loop else t)
        p.key(f)
    for fc in action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    # Kept for the exporter as its own NLA strip.
    track = arm.animation_data.nla_tracks.new()
    track.name = name
    strip = track.strips.new(name, 0, action)
    strip.action_frame_end = frames
    arm.animation_data.action = None
    action.use_fake_user = True
    return action
