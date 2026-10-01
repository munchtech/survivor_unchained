"""The woman survivor's body from a sculpted figure: one mesh, T-posed,
painted (e.g. a model made in ComfyUI), made into a game body rigged to
the Quaternius skeleton, so every clip of the animation libraries plays
on her unchanged.

    python tools/assets/woman_body.py <figure.glb> godot/art/people/anime_female.glb \
        godot/art/people/woman.glb [--joints preview.png]

The skeleton is taken from the anime body (already fitted to a woman's
proportions, tools/assets/anime_female.py): every joint is moved onto the
new figure by landmarks found in it (the ground, ankle, knee, crotch,
waist, the arms' line, neck, crown; along each arm the shoulder, elbow,
wrist and fingertips) while every bone keeps its orientation, so a pose
means the same on her. Her hands are made the skeleton's: palm down, a
woman's size, each finger laid as its fingers lie, and each digit's joints
down its middle (a sculpt's hands are often splayed, palm forward and
large: every clip's curl then bends them sideways into sausages). The
figure is brought down to a game's weight (the hands less than the rest),
its paint baked onto a clean sheet from the full figure (colour and the
fine shape as a normal map), and it is weighted to the skeleton through a
watertight copy of itself (bone heat fails on a sculpt's open seams and
loose shells; the copy has none), the weights carried back by surface.
Beside it, a mask of what is her skin, her hair and her suit (red, green,
blue: <out>_mask.png), so the game can tone, colour and dye each
(godot/shaders/woman_skin.gdshader), and one shape key, Figure, for the
figure slider (1 fuller, -1 slighter).

Needs Blender's Python module (pip install bpy==4.2.0)."""
import bpy, bmesh, sys, math, os
import numpy as np
from mathutils import Vector, Matrix

args = [a for a in sys.argv[sys.argv.index('--') + 1:]] if '--' in sys.argv else sys.argv[1:]
preview = None
if '--joints' in args:
    i = args.index('--joints'); preview = args[i + 1]; args = args[:i] + args[i + 2:]
fig_path, rig_path, out_glb = args[-3:]
FACES = int(os.environ.get('WOMAN_FACES', '32000'))
SHEET = int(os.environ.get('WOMAN_SHEET', '2048'))

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene

def world_verts(o):
    M = np.array(o.matrix_world)
    V = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    return V @ M[:3, :3].T + M[:3, 3]

def only(o):
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True); bpy.context.view_layer.objects.active = o

# ------------------------------------------------------------------ rig --
bpy.ops.import_scene.gltf(filepath=rig_path)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
old = max((o for o in bpy.data.objects if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
OV = world_verts(old)
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    bpy.data.objects.remove(o, do_unlink=True)

# --------------------------------------------------------------- figure --
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=fig_path)
hi = next(o for o in bpy.data.objects if o not in before and o.type == 'MESH')
hi.name = 'Figure'
only(hi)
hi.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
# Face the way the rig does, stand on the ground, as tall as the anime body.
# (The rig's front is where its toes point: -Y for the Quaternius skeleton,
# the glTF's +Z. A figure set the other way round on it bends against every
# clip: knees back, arms behind.)
def bone_end(name, end):
    b = arm.data.bones[name]
    return np.array(arm.matrix_world @ (b.head_local if end == 'head' else b.tail_local))
FRONT = np.sign(bone_end('ball_l', 'tail')[1] - bone_end('foot_l', 'head')[1])
V = world_verts(hi)
facing = np.sign(V[:, 1].max() + V[:, 1].min() - 2 * V[:, 1].mean())  # the bust is the front's furthest reach
lo_z, hi_z = V[:, 2].min(), V[:, 2].max()
s = (OV[:, 2].max() - OV[:, 2].min()) / (hi_z - lo_z)
cx = (V[:, 0].max() + V[:, 0].min()) / 2
M = Matrix.Scale(s, 4) @ Matrix.Translation((-cx, 0, -lo_z))
if facing != FRONT: M = Matrix.Rotation(math.pi, 4, 'Z') @ M
hi.data.transform(M)
NV = world_verts(hi)
# Depth: the body's middle where the anime body's is, at the hips.
def section(V, z, band=0.01, xlo=-9, xhi=9):
    return V[(np.abs(V[:, 2] - z) < band) & (V[:, 0] > xlo) & (V[:, 0] < xhi)]
zh = 0.55 * NV[:, 2].max()
dy = section(OV, zh, 0.01, -0.12, 0.12)[:, 1].mean() - section(NV, zh, 0.01, -0.12, 0.12)[:, 1].mean()
hi.data.transform(Matrix.Translation((0, dy, 0)))
NV = world_verts(hi)
print(f'figure: {len(NV)} verts, scaled {s:.3f}, {"turned" if facing != FRONT else "facing"} the rig\'s way ({"+" if FRONT > 0 else "-"}Y)')

# ------------------------------------------------------------ landmarks --
def marks(V):
    H = V[:, 2].max()
    # The crotch: down from the middle of the body, the first height where
    # nothing crosses the middle (the legs part; below, thighs may touch again).
    # (A coarse body's vertices are too far apart to scan; its legs do not
    # touch, so its lowest middle point is the crotch.)
    if len(V) > 100000:
        near = V[np.abs(V[:, 0]) < 0.006]
        crotch = 0.45 * H
        for z in np.arange(0.62 * H, 0.3 * H, -0.002):
            if not np.any(np.abs(near[:, 2] - z) < 0.003): crotch = z; break
        # Thighs that touch all the way up hide it: then it is where a
        # woman's usually is, about half her height.
        if crotch < 0.45 * H: crotch = 0.485 * H
    else:
        mid = V[np.abs(V[:, 0]) < 0.01]
        crotch = mid[(mid[:, 2] > 0.3 * H) & (mid[:, 2] < 0.6 * H)][:, 2].min()
    def width(z, lim):
        s = section(V, z, 0.008, -lim, lim)
        return (s[:, 0].max() - s[:, 0].min()) if len(s) > 4 else 9
    zs = np.linspace(crotch, H, 220)
    neck = min([z for z in zs if 0.78 * H < z < 0.9 * H], key=lambda z: width(z, 0.12))
    waist = min([z for z in zs if crotch + 0.06 * H < z < 0.7 * H], key=lambda z: width(z, 0.22))
    # The arms' line: where the arm is, outside the torso, from the armpit to the fingertips.
    tip = V[:, 0].max()
    # The arm's own line, from the forearm out to the wrist (clear of the
    # shoulder's trapezius and the hair), followed in toward the body.
    xs = np.linspace(0.42 * tip, 0.75 * tip, 12)
    pts = []
    for x in xs:
        s = V[(np.abs(V[:, 0] - x) < 0.008) & (V[:, 2] > 0.6 * H)]
        if len(s): pts.append((x, (s[:, 2].min() + s[:, 2].max()) / 2, (s[:, 1].min() + s[:, 1].max()) / 2))
    P = np.array(pts)
    fz, fy = np.polyfit(P[:, 0], P[:, 1], 1), np.polyfit(P[:, 0], P[:, 2], 1)
    def arm_at(x):
        if x < 0.75 * tip: return float(np.polyval(fz, x)), float(np.polyval(fy, x))
        s = V[(np.abs(V[:, 0] - x) < 0.008) & (V[:, 2] > 0.6 * H)]
        return ((s[:, 2].min() + s[:, 2].max()) / 2, (s[:, 1].min() + s[:, 1].max()) / 2) if len(s) else (float(np.polyval(fz, x)), float(np.polyval(fy, x)))
    return dict(H=H, crotch=crotch, neck=neck, waist=waist, tip=tip, arm_at=arm_at)

om, nm = marks(OV), marks(NV)
B = {b.name: (np.array(b.head_local), np.array(b.tail_local)) for b in arm.data.bones}
o_sh, o_el, o_wr = B['upperarm_l'][0][0], B['lowerarm_l'][0][0], B['hand_l'][0][0]
o_arm_z = B['upperarm_l'][0][2]
# The new figure's shoulder: as far out of its torso as the old one's was of its own.
def torso_half(V, z):
    return np.abs(section(V, z, 0.02, -0.35, 0.35)[:, 0]).max()
# (Measured across the chest, below where the arms are held out, so the
# section is the torso alone.)
zc_o, zc_n = 0.7 * om['H'], 0.7 * nm['H']
print('landmarks old', {k: round(v, 3) for k, v in om.items() if k != 'arm_at'}, 'new', {k: round(v, 3) for k, v in nm.items() if k != 'arm_at'})
n_sh = torso_half(NV, zc_n) * o_sh / max(1e-6, torso_half(OV, zc_o))
print(f"shoulders: old {o_sh:.3f} of a chest {torso_half(OV, zc_o):.3f}; new {n_sh:.3f} of {torso_half(NV, zc_n):.3f}; fingertips {om['tip']:.3f} -> {nm['tip']:.3f}")
k = (nm['tip'] - n_sh) / (om['tip'] - o_sh)
n_el, n_wr = n_sh + (o_el - o_sh) * k, n_sh + (o_wr - o_sh) * k

def pw(x, xs, ys):
    return float(np.interp(x, xs, ys))

def z_map(z):
    o = [0, om['crotch'], om['waist'], om['neck'], om['H']]
    n = [0, nm['crotch'], nm['waist'], nm['neck'], nm['H']]
    return pw(z, o, n)

def mid_y(V, z):
    s = section(V, z, 0.01, -0.15, 0.15)
    return (s[:, 1].min() + s[:, 1].max()) / 2 if len(s) else 0

def leg_x(V, z):
    s = section(V, z, 0.01, 0.0, 0.3)
    return s[:, 0].mean() if len(s) else 0

ARM = ('clavicle', 'upperarm', 'lowerarm', 'hand', 'index', 'middle', 'pinky', 'ring', 'thumb')
LEG = ('thigh', 'calf', 'foot', 'ball')

def place(name, p):
    x, y, z = p
    side = 1 if x >= 0 else -1
    ax = abs(x)
    if name.startswith(ARM) and not name.startswith('clavicle'):
        nx = pw(ax, [0, o_sh, o_el, o_wr, om['tip']], [0, n_sh, n_el, n_wr, nm['tip']])
        oz, oy = om['arm_at'](min(ax, om['tip'] - 0.01))
        nz, ny = nm['arm_at'](min(nx, nm['tip'] - 0.01))
        if oz is None or nz is None: return np.array([side * nx, y, z_map(z)])
        return np.array([side * nx, y - oy + ny, z - oz + nz])
    nz = z_map(z)
    if name.startswith(LEG) or name.startswith('clavicle'):
        ox, nx = leg_x(OV, z), leg_x(NV, nz)
        if name.startswith('clavicle'): nx, ox = n_sh, o_sh
        sx = nx / ox if ox > 1e-4 else 1
        return np.array([x * sx, y - mid_y(OV, z) + mid_y(NV, nz), nz])
    return np.array([x, y - mid_y(OV, z) + mid_y(NV, nz), nz])

only(arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
new = {}
for b in eb:
    h, t = B[b.name]
    nh, nt = place(b.name, h), place(b.name, t)
    d = (t - h); L = np.linalg.norm(d)
    new[b.name] = (nh, nh + d / max(L, 1e-9) * max(np.linalg.norm(nt - nh), 0.01))
for b in eb:
    roll = b.roll
    b.head = Vector(new[b.name][0]); b.tail = Vector(new[b.name][1]); b.roll = roll
bpy.ops.object.mode_set(mode='OBJECT')
print('joints moved:', {n: tuple(np.round(new[n][0], 3)) for n in ('pelvis', 'neck_01', 'Head', 'upperarm_l', 'lowerarm_l', 'hand_l', 'thigh_l', 'calf_l', 'foot_l')})

# --------------------------------------------------------------- hands --
# Her hands as the skeleton's are. A sculpt's T often holds them palm
# forward, fingers splayed and fanned up and down, and larger than life,
# while the skeleton's lie palm down, fingers side by side; then every
# clip's curl bends her fingers sideways into one another, thick as sausages.
# So, on the full figure (the bake then takes the hands as they are made
# here): her digits are found over the hand's surface, each hand turned
# palm down (the forearm taking the twist, as a wrist does), brought to a
# woman's size and laid along the skeleton's, and each finger swung about
# its knuckle to lie as the skeleton's does.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anime_hands as handfit
import heapq
HP = {b.name: np.array(arm.matrix_world @ b.head_local) for b in arm.data.bones}
def bone_dir(name):
    b = arm.data.bones[name]
    d = np.array(arm.matrix_world.to_3x3() @ (b.tail_local - b.head_local))
    return d / np.linalg.norm(d)

def arm_frame(V, side):
    E0, W0 = HP[f'lowerarm_{side}'], HP[f'hand_{side}']
    ax = (W0 - E0) / np.linalg.norm(W0 - E0)
    d = V - W0
    a = d @ ax
    near = np.linalg.norm(d - np.outer(a, ax), axis=1) < 0.15
    return E0, W0, ax, a, near

FE = np.empty(len(hi.data.edges) * 2, np.int64); hi.data.edges.foreach_get('vertices', FE); FE = FE.reshape(-1, 2)

class Surface:
    """The surface within a region as a graph over its distinct points (a
    sculpt's seams split one point into several vertices), for distances
    along it."""
    def __init__(self, V, inside, weld=0.0004):
        # (points closer than weld are one: a sculpt's halves meet at a seam
        # whose two edges lie close, not on each other)
        from mathutils.kdtree import KDTree
        idx = np.nonzero(inside)[0]
        kd = KDTree(len(idx))
        for j, i in enumerate(idx.tolist()): kd.insert(V[i], j)
        kd.balance()
        parent = np.arange(len(idx))
        def root(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]; x = parent[x]
            return x
        for j, i in enumerate(idx.tolist()):
            for _, k, _ in kd.find_range(V[i], weld):
                rj, rk = root(j), root(k)
                if rj != rk: parent[max(rj, rk)] = min(rj, rk)
        roots = np.array([root(j) for j in range(len(idx))])
        _, first, inv = np.unique(roots, return_index=True, return_inverse=True)
        self.node = -np.ones(len(V), np.int64); self.node[idx] = inv.reshape(-1)
        self.rep = idx[first]                         # a vertex for each point
        self.n = len(first)
        e = FE[inside[FE[:, 0]] & inside[FE[:, 1]]]
        a_, b_ = self.node[e[:, 0]], self.node[e[:, 1]]
        k = a_ != b_
        a_, b_ = a_[k], b_[k]
        L = np.linalg.norm(V[self.rep[a_]] - V[self.rep[b_]], axis=1)
        self.nb = [[] for _ in range(self.n)]
        for x, y, l in zip(a_.tolist(), b_.tolist(), L.tolist()):
            self.nb[x].append((y, l)); self.nb[y].append((x, l))
        # A sculpt may be walled twice (a skin, and a shell a little inside
        # it): distances are taken over the outer skin, its largest piece, and
        # each point of any other piece goes with the skin's point nearest it.
        comp = -np.ones(self.n, int); nc = 0
        for s0 in range(self.n):
            if comp[s0] >= 0: continue
            st = [s0]; comp[s0] = nc
            while st:
                u = st.pop()
                for v, _ in self.nb[u]:
                    if comp[v] < 0: comp[v] = nc; st.append(v)
            nc += 1
        self.outer = comp == np.argmax(np.bincount(comp))
        self.alias = np.arange(self.n)
        on = np.nonzero(self.outer)[0]
        kd2 = KDTree(len(on))
        for j, u in enumerate(on.tolist()): kd2.insert(V[self.rep[u]], j)
        kd2.balance()
        for u in np.nonzero(~self.outer)[0].tolist():
            self.alias[u] = on[kd2.find(V[self.rep[u]])[1]]
        self.pieces = nc
    def dist(self, sources):
        d = np.full(self.n, np.inf)
        h = [(0.0, int(s_)) for s_ in sources]
        for _, s_ in h: d[s_] = 0.0
        heapq.heapify(h)
        while h:
            du, u = heapq.heappop(h)
            if du > d[u]: continue
            for v, l in self.nb[u]:
                if du + l < d[v]:
                    d[v] = du + l; heapq.heappush(h, (du + l, v))
        return d

def digits(V, side):
    """Her five digits, found over the hand's skin from the wrist. Each is a
    peak of the distance along the skin from the wrist: going down from the
    furthest points, a digit is a peak that stands at least 2.5 cm above
    where it joins a higher one (its web), and its own region is what is
    above that. The thumb is the digit whose web lies nearest the wrist; the
    fingers follow across the hand from it. Each finger: its vertices (how
    fully each is the finger's, fading in over its web), its tip, and the
    ring of it at its web."""
    E0, W0, ax, a, near = arm_frame(V, side)
    inside = near & (a > -0.005)
    S_ = Surface(V, inside)
    ar = a[S_.rep]
    gw = S_.dist(np.nonzero((ar < 0.004) & S_.outer)[0])
    ok = np.isfinite(gw)
    order = np.nonzero(ok)[0][np.argsort(-gw[ok])]
    up = np.arange(S_.n)                              # each region named by its peak
    def find(x):
        while up[x] != x:
            up[x] = up[up[x]]; x = up[x]
        return x
    seen = np.zeros(S_.n, bool)
    members, own, found = {}, {}, []
    for u in order.tolist():
        cs = {find(v) for v, _ in S_.nb[u] if seen[v]}
        seen[u] = True
        if not cs:
            members[u] = [u]; continue
        cs = sorted(cs, key=lambda c: -gw[c])
        top = cs[0]
        for c in cs[1:]:
            if gw[c] - gw[u] > 0.025:                 # a digit, joining at its web
                found.append((c, gw[u], own.get(c, (gw[u], list(members[c])))))
                own.setdefault(top, (gw[u], list(members[top])))
            up[c] = top; members[top].extend(members.pop(c))
        up[u] = top; members[top].append(u)
    peak = max(members, key=lambda c: gw[c])
    found.append((peak, np.inf, own.get(peak, (0.0, list(members[peak])))))    # (the longest joins nothing)
    if len(found) != 5:
        print(f'{side} hand: {len(found)} digits found, not 5: the hand left as it is')
        return None
    # the thumb joins nearest the wrist
    found.sort(key=lambda d: d[1])
    thumb, rest = found[0], found[1:]
    tp = V[S_.rep[thumb[0]]]
    rest.sort(key=lambda d: np.linalg.norm(V[S_.rep[d[0]]] - tp))
    tw, treg = thumb[2]
    tn = np.array(treg)
    out = {'thumb': S_.rep[thumb[0]], 'thumb_pts': S_.rep[tn], 'thumb_g': gw[tn]}
    names = ('index', 'middle', 'ring', 'pinky')
    al = S_.alias[S_.node[inside]]
    for f, (t, joins, (web, region)) in zip(names, rest):
        reg = np.zeros(S_.n, bool); reg[region] = True
        w = handfit.smooth01((gw - web) / 0.015) * reg
        vw = np.zeros(len(V)); vw[inside] = w[al]
        ring_n = np.nonzero(reg & (gw < web + 0.006))[0]
        out[f] = dict(tip=S_.rep[t], idx=np.nonzero(vw > 0)[0], w=vw[vw > 0], ring=S_.rep[ring_n], web=web, tipg=gw[t],
                      pts=S_.rep[np.array(region)])
    print(f'{side} hand: {S_.n} points in {S_.pieces} pieces; thumb {gw[thumb[0]]:.3f} from the wrist, joining at {thumb[1]:.3f}; ' +
          ', '.join(f'{f} {out[f]["tipg"]:.3f} (web {out[f]["web"]:.3f})' for f in names))
    return out

def palm_down(V, side, thumb):
    """Her hand turned about her forearm until it lies palm down (its fingers
    fanned front to back across the arm, the thumb in front), the turn
    growing from nothing at the elbow to all of it at the wrist."""
    E0, W0, ax, a, near = arm_frame(V, side)
    e1 = np.array([0.0, 1.0, 0.0]); e1 -= (e1 @ ax) * ax; e1 /= np.linalg.norm(e1)
    e2 = np.cross(ax, e1)
    reach = a[near].max()
    F = V[near & (a > 0.5 * reach)] - W0
    F = F - np.outer(F @ ax, ax); F = F - F.mean(0)
    uv = np.stack([F @ e1, F @ e2], 1)
    w, vec = np.linalg.eigh(uv.T @ uv)
    phi = np.arctan2(vec[1, 1], vec[0, 1])          # the fan's direction across the arm
    part = near & (a > (E0 - W0) @ ax - 0.02)
    ramp = handfit.smooth01((a - (E0 - W0) @ ax) / (-(E0 - W0) @ ax))
    best = None
    for ang in (-phi, np.pi - phi):
        X = V.copy()
        X[part] = handfit.rotate(V[part], W0, ax, np.full(part.sum(), ang) * ramp[part])
        front = (X[thumb] - W0) @ e1                  # the thumb's way across: in front is -Y
        if best is None or front < best[0]: best = (front, ang, X)
    print(f'{side} hand turned {np.degrees(best[1]):.0f} deg about the forearm, palm down')
    return best[2]

def resize(V, side):
    """A sculpt's hands run large: hers brought to a woman's, about a tenth
    of her height and a little more from wrist to fingertip, the change
    tapering in over the wrist."""
    E0, W0, ax, a, near = arm_frame(V, side)
    reach = a[near].max()
    want = 0.106 * nm['H']
    k = min(1.0, want / reach)
    part = near & (a > -0.03)
    f = 1 + (k - 1) * handfit.smooth01((a[part] + 0.02) / 0.035)
    V = V.copy(); V[part] = W0 + (V[part] - W0) * f[:, None]
    print(f'{side} hand {reach * 100:.1f} cm from the wrist, made {want * 100:.1f}')
    return V

def lay_fingers(V, side, dig):
    """Each finger swung about its knuckle to lie as the skeleton's does (a
    sculpt's fingers splay; the clips curl them as the skeleton holds them)."""
    for f in ('index', 'middle', 'ring', 'pinky'):
        d = dig[f]
        if len(d['ring']) < 3:
            print(f'{side} {f}: no knuckle found, left as it is'); continue
        K = V[d['ring']].mean(0)
        tip = V[d['tip']]
        have = (tip - K) / np.linalg.norm(tip - K)
        want = bone_dir(f'{f}_01_{side}')
        axis = np.cross(have, want); sn = np.linalg.norm(axis)
        if sn < 1e-6: continue
        ang = np.arctan2(sn, have @ want)
        V[d['idx']] = handfit.rotate(V[d['idx']], K, axis / sn, ang * d['w'])
        print(f'{side} {f} laid {np.degrees(ang):.0f} deg')
    return V

def section_centre(X, p, u, half=0.003):
    """The middle of a digit where it crosses p (its points within half
    of p along the digit's line u)."""
    m = np.abs((X - p) @ u) < half
    return X[m].mean(0) if m.sum() >= 4 else p

def digit_joints(V, side, dig):
    """Each digit's joints down its middle, from its own skin: a finger's
    knuckle a little before its web (as a fifth of its length again into
    the palm), its middle joints at a human finger's proportions; the
    thumb's from its root by the palm to its tip."""
    J = {}
    for f in ('index', 'middle', 'ring', 'pinky'):
        d = dig[f]
        X = V[d['pts']]
        T, K = V[d['tip']], (V[d['ring']].mean(0) if len(d['ring']) else X.mean(0))
        L = np.linalg.norm(T - K); u = (T - K) / L
        kn = K - 0.22 * L * u
        tip = section_centre(X, T - 0.004 * u, u)
        span = np.linalg.norm(tip - kn)
        p2, p3 = handfit.PHALANX[f]
        J[f'{f}_01_{side}'] = kn
        J[f'{f}_02_{side}'] = section_centre(X, kn + p2 * span * u, u)
        J[f'{f}_03_{side}'] = section_centre(X, kn + p3 * span * u, u)
        J[f'{f}_04_leaf_{side}'] = tip
    X, g = V[dig['thumb_pts']], dig['thumb_g']
    T = V[dig['thumb']]
    base = X[g < np.quantile(g, 0.2)].mean(0)
    u = (T - base) / np.linalg.norm(T - base)
    for c, t in zip(('01', '02', '03', '04_leaf'), (0.0, 0.45, 0.76, 0.94)):
        p_ = base + (T - base) * t
        J[f'thumb_{c}_{side}'] = p_ if t == 0 else section_centre(X, p_, u)
    return J

FINGER_JOINTS = {}
V = world_verts(hi)
for side, sx in (('l', 1), ('r', -1)):
    dig = digits(V, side)
    if dig is None: continue
    V = palm_down(V, side, dig['thumb'])
    V = resize(V, side)
    o, axis, ang = handfit.straighten_forearm(V, HP, bone_dir(f'lowerarm_{side}'), side, sx)
    V = handfit.rotate(V, o, axis, ang)
    o, axis, ang = handfit.straighten(V, HP, bone_dir(f'middle_01_{side}'), side, sx)
    V = handfit.rotate(V, o, axis, ang)
    V = lay_fingers(V, side, dig)
    FINGER_JOINTS.update(digit_joints(V, side, dig))
hi.data.vertices.foreach_set('co', V.reshape(-1)); hi.data.update()
if os.environ.get('WOMAN_DEBUG_HANDS'): sys.exit(0)    # (to see the hands found and laid, and stop)
# (normals that came with the figure would still point where the hands were)
if hi.data.has_custom_normals:
    only(hi); bpy.ops.mesh.customdata_custom_splitnormals_clear(); bpy.ops.object.shade_smooth()

if preview:
    # The figure, with a bead on every joint, from the front.
    mat = bpy.data.materials.new('bead'); mat.diffuse_color = (1, 0.2, 0.1, 1)
    for b in arm.data.bones:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, location=arm.matrix_world @ b.head_local)
        bpy.context.object.data.materials.append(mat)
    for o in bpy.data.objects:
        if o.type == 'MESH' and o != hi: o.show_in_front = True
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); scn.collection.objects.link(cam)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.9
    cam.location = (0, -5, 0.85); cam.rotation_euler = (math.pi / 2, 0, 0); scn.camera = cam
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); scn.collection.objects.link(sun); sun.rotation_euler = (0.9, 0, 0.3)
    scn.render.engine = 'BLENDER_WORKBENCH'; scn.display.shading.light = 'FLAT'
    scn.display.shading.show_xray = True; scn.display.shading.xray_alpha = 0.4
    scn.render.resolution_x, scn.render.resolution_y = 1100, 1000
    scn.render.filepath = preview
    bpy.ops.render.render(write_still=True)
    sys.exit(0)

# ------------------------------------------------- down to a game's weight --
only(hi)
bpy.ops.object.duplicate()
low = bpy.context.object; low.name = 'Woman'
only(low)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0004)
bpy.ops.object.mode_set(mode='OBJECT')
# Her hands brought down on their own, keeping more of them than of the
# rest (fingers brought down with the body come out as stubby prisms): the
# body to what is left of the faces, each hand to WOMAN_HAND_FACES.
HAND_FACES = int(os.environ.get('WOMAN_HAND_FACES', '2400'))
def hand_faces():
    LK = world_verts(low)
    hv = np.zeros(len(LK), bool)
    for side in ('l', 'r'):
        E0, W0, ax, a_, near = arm_frame(LK, side)
        hv |= near & (a_ > -0.01)
    PV = np.empty(len(low.data.loops), np.int64); low.data.loops.foreach_get('vertex_index', PV)
    starts = np.empty(len(low.data.polygons), np.int64); low.data.polygons.foreach_get('loop_start', starts)
    inhand = np.logical_and.reduceat(hv[PV], starts)
    return inhand
def decimate_where(sel, ratio):
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_mode(type='FACE')
    bm = bmesh.from_edit_mesh(low.data); bm.faces.ensure_lookup_table()
    for f in bm.faces: f.select_set(False)
    for i in np.nonzero(sel)[0].tolist(): bm.faces[i].select_set(True)
    bm.select_flush_mode(); bmesh.update_edit_mesh(low.data)
    bpy.ops.mesh.decimate(ratio=min(1.0, ratio))
    bpy.ops.object.mode_set(mode='OBJECT')
inhand = hand_faces()
decimate_where(~inhand, (FACES - 2 * HAND_FACES) / max(1, (~inhand).sum()))
inhand = hand_faces()
decimate_where(inhand, 2 * HAND_FACES / max(1, inhand.sum()))
bpy.ops.object.shade_smooth()
LK = world_verts(low)
print(f'down to {len(low.data.polygons)} faces, {int(hand_faces().sum())} of them the hands; each hand ' + ', '.join(str(int((arm_frame(LK, sd)[4] & (arm_frame(LK, sd)[3] > 0)).sum())) for sd in ('l', 'r')) + ' vertices')

# A clean sheet, and the full figure's paint and fine shape baked onto it.
while low.data.uv_layers: low.data.uv_layers.remove(low.data.uv_layers[0])
low.data.uv_layers.new(name='UVMap')
only(low)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004)
bpy.ops.uv.pack_islands(margin=0.004)
bpy.ops.object.mode_set(mode='OBJECT')
scn.render.engine = 'CYCLES'; scn.cycles.samples = 1; scn.cycles.device = 'CPU'
src_mat = hi.data.materials[0]
nt = src_mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
col_tex = bsdf.inputs['Base Color'].links[0].from_node
def sheet(name, colour):
    im = bpy.data.images.new(name, SHEET, SHEET, alpha=False); im.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'
    return im
paint, shape = sheet('Woman_Body', True), sheet('Woman_Normal', False)
mat = bpy.data.materials.new('Woman'); mat.use_nodes = True
mn = mat.node_tree.nodes
tex_c = mn.new('ShaderNodeTexImage'); tex_c.image = paint
tex_n = mn.new('ShaderNodeTexImage'); tex_n.image = shape
low.data.materials.clear(); low.data.materials.append(mat)
# The colour: the figure's paint, as light (emission bakes it unshaded).
emit = nt.nodes.new('ShaderNodeEmission'); nt.links.new(col_tex.outputs['Color'], emit.inputs['Color'])
out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
shade_link = out.inputs['Surface'].links[0].from_socket
nt.links.new(emit.outputs['Emission'], out.inputs['Surface'])
# The cage the rays are cast from: the light figure blown out a little
# along its normals, but never more than half way to her own surface the
# other side (where the thighs touch, a cage blown out evenly sits inside
# the other leg, and the paint there comes from inside it).
from mathutils.bvhtree import BVHTree
cage_obj = low.copy(); cage_obj.data = low.data.copy(); cage_obj.name = 'Cage'
scn.collection.objects.link(cage_obj)
tree = BVHTree.FromObject(low, bpy.context.evaluated_depsgraph_get())
Mw = low.matrix_world
blown = 0
for v, cv in zip(low.data.vertices, cage_obj.data.vertices):
    p, n = Mw @ v.co, (Mw.to_3x3() @ v.normal).normalized()
    hit = tree.ray_cast(p + n * 0.0005, n, 0.03)
    out_by = 0.012 if hit[0] is None else min(0.012, 0.45 * (hit[3] + 0.0005))
    blown += out_by < 0.012
    cv.co = v.co + v.normal * out_by
print(f'cage: {blown} vertices held in near another part of her')
bpy.ops.object.select_all(action='DESELECT')
hi.select_set(True); low.select_set(True); bpy.context.view_layer.objects.active = low
mn.active = tex_c
bake_from = dict(use_selected_to_active=True, use_cage=True, cage_object=cage_obj.name, margin=8)
bpy.ops.object.bake(type='EMIT', **bake_from)
print('baked the paint')
# The fine shape: the figure's normals (its own detail and normal map) onto the light one's.
nt.links.new(shade_link, out.inputs['Surface'])
mn.active = tex_n
bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT', **bake_from)
bpy.data.objects.remove(cage_obj, do_unlink=True)
print('baked the shape')
bsdf2 = mn['Principled BSDF']
mat.node_tree.links.new(tex_c.outputs['Color'], bsdf2.inputs['Base Color'])
nmap = mn.new('ShaderNodeNormalMap'); mat.node_tree.links.new(tex_n.outputs['Color'], nmap.inputs['Color'])
mat.node_tree.links.new(nmap.outputs['Normal'], bsdf2.inputs['Normal'])
bsdf2.inputs['Roughness'].default_value = 0.6
bsdf2.inputs['Metallic'].default_value = 0.0

# ---------------------------------------------------------------- mask --
# Which of her is skin, hair and suit, for the game to dye (skin to the tone
# chosen, hair to its colour, the suit to the calling's cloth): by her
# paint's colour (skin is rosy, the hair yellow, the suit a dark blue-grey)
# and by where it is (hair only about the head and shoulders, never on the
# face), smoothed, and baked onto a small sheet of its own.
PX = np.asarray(paint.pixels[:]).reshape(SHEET, SHEET, 4)[:, :, :3]  # (as painted: a byte sheet's pixels are its sRGB)
uv = low.data.uv_layers.active.data
per = np.zeros((len(low.data.vertices), 3)); cnt = np.zeros(len(low.data.vertices))
for poly in low.data.polygons:
    for li in poly.loop_indices:
        u, v = uv[li].uv
        c = PX[min(SHEET - 1, max(0, int(v * SHEET))), min(SHEET - 1, max(0, int(u * SHEET)))]
        vi = low.data.loops[li].vertex_index
        per[vi] += c; cnt[vi] += 1
per /= np.maximum(cnt, 1)[:, None]
LV = world_verts(low)
rest = {b.name: arm.matrix_world @ b.head_local for b in arm.data.bones}
neck_z, head = rest['neck_01'].z, rest['Head']
crown = LV[:, 2].max()
lum = per @ np.array([0.3, 0.59, 0.11])
rg, gb = per[:, 0] - per[:, 1], per[:, 1] - per[:, 2]
blue = per[:, 2] - per[:, 0]
suit = (blue > -0.01) | ((lum < 0.22) & (blue > -0.05))  # (its sheen is bright, but never rosy)
# Her face: an oval on the front of the head, from the chin (about the head
# joint's height) to the hairline. Her blonde and her skin are too near in
# colour to tell apart by it, so above the chin all that is not her face (nor
# her suit's collar) is hair; below it, hair hanging over the shoulders is told
# from them by its colour (yellower than her skin).
fx, fz = LV[:, 0] / 0.056, (LV[:, 2] - (head.z + 0.083)) / 0.08
face = (fx ** 2 + fz ** 2 < 1) & ((LV[:, 1] - head.y) * FRONT > 0.03)
above_chin = LV[:, 2] > head.z + 0.02
suit &= ~above_chin
about_head = (LV[:, 2] > neck_z - 0.14) & (np.abs(LV[:, 0]) < 0.16)  # (the arms are held out at that height)
hair = about_head & ~face & ~suit & (above_chin | (gb > rg - 0.02))
skin = ~suit & ~hair
lab = np.stack([skin, hair, suit], 1).astype(float)
# Smoothed over the surface twice, so the edges between them are soft.
edges = np.array([e.vertices[:] for e in low.data.edges])
for _ in range(2):
    acc = lab.copy(); n = np.ones(len(lab))
    np.add.at(acc, edges[:, 0], lab[edges[:, 1]]); np.add.at(acc, edges[:, 1], lab[edges[:, 0]])
    np.add.at(n, edges[:, 0], 1); np.add.at(n, edges[:, 1], 1)
    lab = acc / n[:, None]
attr = low.data.color_attributes.new('mask', 'FLOAT_COLOR', 'POINT')
attr.data.foreach_set('color', np.hstack([lab, np.ones((len(lab), 1))]).reshape(-1))
print(f'mask: skin {skin.mean():.0%}, hair {hair.mean():.0%}, suit {suit.mean():.0%}')
# The paint's own tones, which the game's shader tones from (shaders/woman_skin.gdshader's paint_*).
# (Her skin as lit: its shadows are carried over by the shader, so the
# reference is the lighter quarter of it, not its middle.)
lit = per[skin][np.argsort(per[skin] @ np.array([0.2126, 0.7152, 0.0722]))[int(skin.sum() * 0.75)]]
print('paint tones (sRGB):', ', '.join(f'{n} ' + str(tuple(np.round(c, 3))) for n, c in [('skin as lit', lit), ('hair', np.median(per[hair], 0)), ('suit', np.median(per[suit], 0))]))
if os.environ.get('WOMAN_DEBUG'):
    for name, sel in [('torso', (np.abs(LV[:, 0]) < 0.12) & (LV[:, 2] > 0.95) & (LV[:, 2] < 1.2)), ('thigh', (np.abs(LV[:, 0]) < 0.15) & (LV[:, 2] > 0.55) & (LV[:, 2] < 0.75)),
                      ('forearm', (np.abs(LV[:, 0]) > 0.4) & (np.abs(LV[:, 0]) < 0.6)), ('crown', LV[:, 2] > crown - 0.05), ('face', face)]:
        c = per[sel]
        print(name, sel.sum(), 'mean', (c.mean(0) * 255).round(), 'p10', (np.percentile(c, 10, 0) * 255).round(), 'p90', (np.percentile(c, 90, 0) * 255).round(), 'suit', suit[sel].mean().round(2), 'hair', hair[sel].mean().round(2))
    sys.exit(0)
masker = bpy.data.images.new('Woman_Mask', SHEET // 2, SHEET // 2, alpha=False); masker.colorspace_settings.name = 'Non-Color'
tmp = bpy.data.materials.new('masking'); tmp.use_nodes = True
tn = tmp.node_tree.nodes
ca = tn.new('ShaderNodeAttribute'); ca.attribute_name = 'mask'
em = tn.new('ShaderNodeEmission'); tmp.node_tree.links.new(ca.outputs['Color'], em.inputs['Color'])
tmp.node_tree.links.new(em.outputs['Emission'], tn['Material Output'].inputs['Surface'])
mt = tn.new('ShaderNodeTexImage'); mt.image = masker; tn.active = mt
low.data.materials[0] = tmp
only(low)
bpy.ops.object.bake(type='EMIT', use_selected_to_active=False, margin=8)
low.data.materials[0] = mat
low.data.color_attributes.remove(low.data.color_attributes['mask'])
masker.filepath_raw = os.path.splitext(out_glb)[0] + '_mask.png'; masker.file_format = 'PNG'; masker.save()
print('baked the mask')

# --------------------------------------------------------- finger joints --
# Her hands, laid as the skeleton's (above), now get their joints: the
# elbow and wrist in the middle of her arm (anime_hands.py), each digit's
# joints down its middle as found with it above (or, for a hand whose
# digits were not found, by the hand tool's sections across it).
Mlow = np.array(low.matrix_world); Milow = np.linalg.inv(Mlow)
def low_get():
    return world_verts(low)
def low_put(V):
    low.data.vertices.foreach_set('co', (V @ Milow[:3, :3].T + Milow[:3, 3]).reshape(-1)); low.data.update()
EI = np.array([e.vertices[:] for e in low.data.edges])
ek = {tuple(sorted(e.vertices[:])): i for i, e in enumerate(low.data.edges)}
HM = (EI, np.array([(p.index, ek[tuple(sorted(k))]) for p in low.data.polygons for k in p.edge_keys]))
HP = {b.name: np.array(arm.matrix_world @ b.head_local) for b in arm.data.bones}

V = low_get()
for side, sx in (('l', 1), ('r', -1)):
    handfit.centre_arm(V, HM, HP, side, sx)
    mine = {k: v for k, v in FINGER_JOINTS.items() if k.endswith('_' + side)}
    if len(mine) == 20:
        HP.update(mine)
    else:
        handfit.fit_fingers(V, HM, HP, side, sx)
        handfit.fit_thumb(V, HP, side, sx)
# The skeleton's hand joints where they now are, each bone keeping its way.
only(arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
Ai = np.linalg.inv(np.array(arm.matrix_world))
DIGITS = ('index', 'middle', 'ring', 'pinky', 'thumb')
for side in ('l', 'r'):
    names = [f'lowerarm_{side}', f'hand_{side}'] + [f'{f}_0{i}_{side}' for f in DIGITS for i in (1, 2, 3)] + [f'{f}_04_leaf_{side}' for f in DIGITS]
    for c in names:
        eb[c].translate(Vector(HP[c] @ Ai[:3, :3].T + Ai[:3, 3]) - eb[c].head)
    pairs = [(f'upperarm_{side}', f'lowerarm_{side}'), (f'lowerarm_{side}', f'hand_{side}'), (f'hand_{side}', f'middle_01_{side}')]
    for f in DIGITS:
        pairs += [(f'{f}_01_{side}', f'{f}_02_{side}'), (f'{f}_02_{side}', f'{f}_03_{side}'), (f'{f}_03_{side}', f'{f}_04_leaf_{side}')]
    for a_, b_ in pairs:
        L = (eb[b_].head - eb[a_].head).length
        if L > 1e-4: eb[a_].length = L
bpy.ops.object.mode_set(mode='OBJECT')

# ------------------------------------------------------------- weights --
# Through a watertight copy: bone heat on the sculpt's own surface fails on
# its open seams and loose shells. The copy's holes are closed before it is
# made of voxels (through an open seam the outside floods in, and what is left
# is a hollow skin, inner and outer, that bone heat cannot solve), and only
# its outermost shell is kept. Should bone heat still fail, a coarser or
# finer grid is tried.
def make_proxy(voxel):
    only(low)
    bpy.ops.object.duplicate()
    proxy = bpy.context.object; proxy.name = 'Proxy'
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.0005); bpy.ops.mesh.fill_holes(sides=0)
    bpy.ops.object.mode_set(mode='OBJECT')
    rm = proxy.modifiers.new('rm', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = voxel
    bpy.ops.object.modifier_apply(modifier='rm')
    before = set(bpy.data.objects)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
    parts = [proxy] + [o for o in bpy.data.objects if o not in before]
    keep = max(parts, key=lambda o: np.ptp(world_verts(o), axis=0).prod())
    for o in parts:
        if o is not keep: bpy.data.objects.remove(o, do_unlink=True)
    keep.name = 'Proxy'
    bpy.ops.object.select_all(action='DESELECT')
    keep.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    got = sum(1 for v in keep.data.vertices if v.groups) / max(1, len(keep.data.vertices))
    print(f'proxy at {voxel * 1000:.0f} mm: {len(keep.data.vertices)} verts in {len(parts)} shells, {got:.0%} weighted')
    return keep, got
for voxel in (0.006, 0.007, 0.005, 0.008, 0.01):
    proxy, got = make_proxy(voxel)
    if got > 0.98: break
    bpy.data.objects.remove(proxy, do_unlink=True)
else:
    sys.exit('bone heat failed on every proxy')
only(low)
for b in arm.data.bones: low.vertex_groups.new(name=b.name)
dt = low.modifiers.new('dt', 'DATA_TRANSFER'); dt.object = proxy
dt.use_vert_data = True; dt.data_types_verts = {'VGROUP_WEIGHTS'}
dt.vert_mapping = 'POLYINTERP_NEAREST'; dt.layers_vgroup_select_src = 'ALL'; dt.layers_vgroup_select_dst = 'NAME'
bpy.ops.object.modifier_apply(modifier='dt')
# Her thighs touch, and the watertight copy is joined there: below the crotch
# each leg is moved by its own bones only, or the inner thigh is dragged along
# by the other leg (a web between them as she walks or sits).
LW = world_verts(low)
left_x = np.sign(bone_end('thigh_l', 'head')[0])
below = LW[:, 2] < nm['crotch'] + 0.02
for side, other, sx in (('l', 'r', left_x), ('r', 'l', -left_x)):
    on = np.nonzero(below & (LW[:, 0] * sx > 0.004))[0].tolist()
    for g in low.vertex_groups:
        if g.name.startswith(LEG) and g.name.endswith('_' + other): g.remove(on)
    # (what is left with nothing goes with its own thigh)
    bare = [i for i in on if not low.data.vertices[i].groups]
    if bare: low.vertex_groups['thigh_' + side].add(bare, 1.0, 'REPLACE')
# The hands from their joint lines (anime_hands.py): through the watertight
# copy her fingers are fused, and bone heat gives each the next one's bones.
VH = low_get()
for side, sx in (('l', 1), ('r', -1)):
    idx, blend, Wn = handfit.hand_weights(VH, HP, side, sx)
    for j, vi in enumerate(idx.tolist()):
        v = low.data.vertices[vi]
        new = {n: blend[j] * w[j] for n, w in Wn.items()}
        for g in v.groups:
            n = low.vertex_groups[g.group].name
            new[n] = new.get(n, 0) + (1 - blend[j]) * g.weight
        for gi in [g.group for g in v.groups]:
            low.vertex_groups[gi].remove([vi])
        tot = sum(new.values())
        for n, w in new.items():
            if w / tot > 1e-3:
                low.vertex_groups[n].add([vi], w / tot, 'REPLACE')
    print(side, 'hand weights from its joints:', len(idx), 'vertices')
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
bpy.data.objects.remove(proxy, do_unlink=True)
bpy.data.objects.remove(hi, do_unlink=True)
low.parent = arm
mod = low.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
unweighted = sum(1 for v in low.data.vertices if not v.groups)
print(f'weighted: {len(low.data.vertices) - unweighted} of {len(low.data.vertices)}')
if unweighted: sys.exit(f'{unweighted} vertices without weights')

# -------------------------------------------------------------- figure --
# One shape key for the figure slider: at 1 fuller (the bust rounder and
# further out, the hips wider, the waist in), at -1 slighter.
only(low)
low.shape_key_add(name='Basis')
key = low.shape_key_add(name='Figure', from_mix=False)
key.slider_min = -1
# (Worked in the world's frame, where the joints were measured: she hangs
# from the armature now, and her own frame may be turned.)
# (And turned, if need be, so that her front is +Y here.)
Mw = np.array(low.matrix_world); Mi = np.linalg.inv(Mw)
F = np.array([1, FRONT, 1])
P = world_verts(low) * F
rest_f = {k: np.array(v) * F for k, v in rest.items()}
D = np.zeros_like(P)
# The chest wall: the front of the torso just under the bust.
under = (np.abs(P[:, 2] - (rest_f['spine_02'][2] + 0.02)) < 0.015) & (np.abs(P[:, 0]) < 0.08)
wall = np.percentile(P[under][:, 1], 90)
chest = (P[:, 2] > rest_f['spine_02'][2]) & (P[:, 2] < rest_f['neck_01'][2] - 0.04) & (np.abs(P[:, 0]) < 0.17)
for side in (1, -1):
    pts = P[chest & (P[:, 0] * side > 0.02)]
    tip = pts[np.argmax(pts[:, 1])]
    # Swelled out from a point behind the chest wall, most at the tip and
    # fading to nothing a little past the breast's root.
    c = np.array([tip[0] - side * 0.005, wall - 0.03, tip[2] + 0.005])
    R = 1.45 * np.linalg.norm(tip - c)
    d = np.linalg.norm(P - c, axis=1)
    fall = np.clip(1 - (d / R) ** 2, 0, 1) ** 1.5 * np.clip((P[:, 1] - (c[1] - 0.02)) / 0.04, 0, 1) * (np.abs(P[:, 0]) < 0.2)
    D += (P - c) * 0.42 * fall[:, None]
    # and settled a touch lower, as a fuller bust sits
    D[:, 2] -= 0.008 * fall
# Hips and seat fuller, the waist in.
hips_z = rest_f['thigh_l'][2]
fh = np.clip(1 - np.abs(P[:, 2] - hips_z) / 0.2, 0, 1) ** 2 * (np.abs(P[:, 0]) < 0.3)
D[:, 0] += P[:, 0] * 0.11 * fh
mid_y = rest_f['pelvis'][1]
seat = fh * (P[:, 1] < mid_y) * (np.abs(P[:, 0]) < 0.2)
D[:, 1] += (P[:, 1] - mid_y) * 0.12 * seat
waist_z = rest_f['spine_01'][2] + 0.04
fw = np.clip(1 - np.abs(P[:, 2] - waist_z) / 0.1, 0, 1) ** 2 * (np.abs(P[:, 0]) < 0.25)
D[:, 0] -= P[:, 0] * 0.09 * fw
D[:, 1] -= (P[:, 1] - mid_y) * 0.05 * fw
Q = (P + D) * F
key.data.foreach_set('co', (Q @ Mi[:3, :3].T + Mi[:3, 3]).reshape(-1))
low.data.update()
print(f'figure key made: moves {np.count_nonzero(np.linalg.norm(D, axis=1) > 0.001)} vertices, at most {np.linalg.norm(D, axis=1).max() * 100:.1f} cm')

# --------------------------------------------------------------- export --
for im in (paint, shape):
    im.filepath_raw = os.path.join(os.path.dirname(out_glb) or '.', f'{im.name}.png'); im.file_format = 'PNG'
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True); low.select_set(True)
bpy.ops.export_scene.gltf(filepath=out_glb, use_selection=True, export_format='GLB', export_skins=True, export_animations=False,
                          export_image_format='AUTO', export_yup=True)
print('wrote', out_glb, os.path.getsize(out_glb))
