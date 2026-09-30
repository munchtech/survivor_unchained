"""Rig donizaki's anime female base (Sketchfab, CC BY) to the Quaternius
skeleton: the same bone names and orientations, so the Universal Animation
Libraries play on her unchanged; the joints moved to her body, her arms
raised from her A-pose to the skeleton's T, her hands fitted and weighted
by anime_hands.py. Her own shape keys (bust, hips, waist...) come along.

    python tools/assets/anime_female.py "Anime Base Female.blend" \
        ".packs/Universal Base Characters/.../Godot - UE/Superhero_Female_FullBody.gltf" \
        <folder with Character_Body.png, Character_Face.png> godot/art/people/anime_female.glb

Needs Blender's Python module (pip install bpy). The .blend comes out
beside the .glb, to look at; it is not part of the game."""
import bpy, sys, math, os
import numpy as np
from mathutils import Vector, Matrix, Quaternion

anime_path, quat_path, tex_dir, out_glb = sys.argv[-4:]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=quat_path)
qarm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
qarm.name = 'Armature'
qbody = bpy.data.objects['Superhero_Female']

def world_verts(o):
    M = np.array(o.matrix_world)
    V = np.array([v.co[:] for v in o.data.vertices])
    return V @ M[:3, :3].T + M[:3, 3]

QV = world_verts(qbody)
QH = {b.name: np.array(b.head_local) for b in qarm.data.bones}
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    bpy.data.objects.remove(o, do_unlink=True)

with bpy.data.libraries.load(anime_path) as (src, dst):
    dst.objects = ['Character']
ch = dst.objects[0]
bpy.context.scene.collection.objects.link(ch)
for im in bpy.data.images:
    im.filepath = f"{tex_dir}/{im.name.replace(' ', '_')}.png"
bpy.context.view_layer.objects.active = ch
ch.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = ch.data
keys = me.shape_keys.key_blocks
n = len(me.vertices)

def get(kb):
    a = np.empty(n * 3); kb.data.foreach_get('co', a); return a.reshape(n, 3)
def put(kb, a):
    kb.data.foreach_set('co', a.reshape(-1))

# ------------------------------------------------------------ landmarks --
def section(V, z, band=0.008, xlo=-9, xhi=9):
    return V[(np.abs(V[:, 2] - z) < band) & (V[:, 0] > xlo) & (V[:, 0] < xhi)]

def marks(V):
    H, G = V[:, 2].max(), V[:, 2].min()
    mid = V[np.abs(V[:, 0]) < 0.006]
    crotch = mid[mid[:, 2] > G + 0.3 * (H - G)][:, 2].min()
    def w(z, lim):
        s = section(V, z, 0.01, -lim, lim)
        return (s[:, 0].max() - s[:, 0].min()) if len(s) else 9
    zs = np.linspace(crotch, H, 160)
    neck = min([z for z in zs if G + 0.72 * (H - G) < z < G + 0.93 * (H - G)], key=lambda z: w(z, 0.12))
    waist = min([z for z in zs if crotch + 0.05 * (H - G) < z < G + 0.68 * (H - G)], key=lambda z: w(z, 0.2))
    return dict(H=H, G=G, crotch=crotch, neck=neck, waist=waist)

def torso_hw(V, z):
    """Half width of the torso alone at z (the arms, if beside it, left out)."""
    s = np.sort(section(V, z, 0.01, 0, 0.6)[:, 0])
    if len(s) == 0: return 0
    gaps = np.where(np.diff(s) > 0.012)[0]
    return s[gaps[0]] if len(gaps) else s[-1]

def centre_y(V, z, xlo=-0.12, xhi=0.12):
    s = section(V, z, 0.01, xlo, xhi)
    return (s[:, 1].min() + s[:, 1].max()) / 2, (s[:, 1].max() - s[:, 1].min())

qm = marks(QV)
A0 = get(keys[0])
am0 = marks(A0)
# Scale so the crotch (and so the hips) sit where the skeleton's do: the
# animations drive the hips at the skeleton's height.
s = (qm['crotch'] - qm['G']) / (am0['crotch'] - am0['G'])
qy, _ = centre_y(QV, qm['crotch'] + 0.05)
ay, _ = centre_y(A0, am0['crotch'] + 0.05 / s)
def fit(a):
    b = a.copy()
    b[:, 0] = a[:, 0] * s
    b[:, 1] = (a[:, 1] - ay) * s + qy
    b[:, 2] = (a[:, 2] - am0['G']) * s + qm['G']
    return b
for kb in keys:
    put(kb, fit(get(kb)))
me.vertices.foreach_set('co', get(keys[0]).reshape(-1))
AV = get(keys[0])
am = marks(AV)
print('scale', round(s, 3), 'height', round(am['H'] - am['G'], 3), 'quat', round(qm['H'] - qm['G'], 3))
print('quat marks', {k: round(v, 3) for k, v in qm.items()})
print('anime marks', {k: round(v, 3) for k, v in am.items()})

# Heights: piecewise-linear between matching landmarks.
QZ = [qm['G'], qm['crotch'], qm['waist'], qm['neck'], qm['H']]
AZ = [am['G'], am['crotch'], am['waist'], am['neck'], am['H']]
vz = lambda z: float(np.interp(z, QZ, AZ))

P = {}
# Midline: pelvis, spine, neck, head (and root).
for b in ['root', 'pelvis', 'spine_01', 'spine_02', 'spine_03', 'neck_01', 'Head']:
    q = QH[b]
    if b == 'root':
        P[b] = q.copy(); continue
    z = vz(q[2])
    cq, dq = centre_y(QV, q[2]); ca, da = centre_y(AV, z)
    P[b] = np.array([0.0, ca + (q[1] - cq) * da / max(dq, 1e-6), z])

# Legs: heights as they are (the scale matched them); across and deep at the
# middle of her leg there.
def leg_centre(V, z, side):
    sec = section(V, z, 0.01, 0.005, 0.4) if side > 0 else section(V, z, 0.01, -0.4, -0.005)
    return np.array([(sec[:, 0].min() + sec[:, 0].max()) / 2, (sec[:, 1].min() + sec[:, 1].max()) / 2]) if len(sec) else None
for side, sx in (('l', 1), ('r', -1)):
    th, ca, ft, ba = QH[f'thigh_{side}'], QH[f'calf_{side}'], QH[f'foot_{side}'], QH[f'ball_{side}']
    # Hip joint: across as the thigh's middle a little below the crotch, as on the skeleton.
    zq = qm['crotch'] - 0.06
    lq, la = leg_centre(QV, zq, sx), leg_centre(AV, zq, sx)
    P[f'thigh_{side}'] = np.array([th[0] - lq[0] + la[0], th[1] - lq[1] + la[1], th[2]])
    for b, q in ((f'calf_{side}', ca), (f'foot_{side}', ft)):
        lq, la = leg_centre(QV, q[2], sx), leg_centre(AV, q[2], sx)
        P[b] = np.array([q[0] - lq[0] + la[0], q[1] - lq[1] + la[1], q[2]])
    # The ball of the foot: as far forward of the ankle as her toes are.
    foot = AV[(AV[:, 2] < am['G'] + 0.06) & (AV[:, 0] * sx > 0.01)]
    qfoot = QV[(QV[:, 2] < qm['G'] + 0.06) & (QV[:, 0] * sx > 0.01)]
    k = (P[f'foot_{side}'][1] - foot[:, 1].min()) / max(1e-6, (ft[1] - qfoot[:, 1].min()))
    for b in (f'ball_{side}', f'ball_leaf_{side}'):
        q = QH[b]
        P[b] = P[f'foot_{side}'] + (q - ft) * np.array([1, k, 1])

# Arms: the shoulder where hers is; the arm along her arm (she stands in an
# A-pose) and then raised to the skeleton's T; the hand and fingers scaled
# for now (anime_hands.py fits them to her once the arm is up).
arm_bones = {}
Rot = {}
Axis = {}
for side, sx in (('l', 1), ('r', -1)):
    ua, la, ha = QH[f'upperarm_{side}'], QH[f'lowerarm_{side}'], QH[f'hand_{side}']
    cl = QH[f'clavicle_{side}']
    sz = vz(ua[2])
    cq, dq = centre_y(QV, ua[2]); ca, da = centre_y(AV, sz)
    # Her arm's axis (from below the shoulder to above the wrist, clear of
    # the torso), followed up to the shoulder's height: the joint is on it.
    tipa = AV[np.argmax(AV[:, 0] * sx)]
    armv = AV[(AV[:, 0] * sx > 0.2) & (AV[:, 0] * sx < 0.2 + 0.55 * (tipa[0] * sx - 0.2)) & (AV[:, 2] > tipa[2])]
    c0 = armv.mean(0)
    u, sv, vt = np.linalg.svd(armv - c0)
    ax = vt[0] if vt[0][2] > 0 else -vt[0]
    S = c0 + ax * (sz - c0[2]) / ax[2]
    S[1] = ca + (ua[1] - cq) * da / max(dq, 1e-6)
    P[f'upperarm_{side}'] = S
    czq = QH[f'clavicle_{side}']
    P[f'clavicle_{side}'] = np.array([czq[0] * (S[0] / ua[0]), ca + (czq[1] - cq) * da / max(dq, 1e-6), vz(czq[2])])
    tipq = QV[np.argmax(QV[:, 0] * sx)]
    tipa = AV[np.argmax(AV[:, 0] * sx)]
    Lq = np.linalg.norm(tipq - ua); La = np.linalg.norm(tipa - S)
    k = La / Lq
    names = [b.name for b in qarm.data.bones if b.name.endswith('_' + side) and any(b.name.startswith(p) for p in ('upperarm', 'lowerarm', 'hand', 'index', 'middle', 'pinky', 'ring', 'thumb'))]
    arm_bones[side] = names
    for b in names:
        P[b] = S + (QH[b] - ua) * k                     # the arm as the skeleton holds it (T), her length
    # Raised about the shoulder so that her arm's own line (not her hand,
    # which she holds bent back) lies along the skeleton's arm.
    dT = Vector(QH[f'hand_{side}'] - ua).normalized(); dA = Vector(-ax).normalized()
    Rot[side] = (dT.rotation_difference(dA), S)
    Axis[side] = (S, np.array(dA), La)
    print(side, 'shoulder', np.round(S, 3), 'arm', round(La, 3), 'vs', round(Lq, 3), 'down by', round(math.degrees(dT.angle(dA)), 1), 'deg')

# ------------------------------------------------------------ skeleton --
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = qarm
qarm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
eb = qarm.data.edit_bones
def primary_child(b):
    kids = [c for c in b.children]
    return kids[0] if len(kids) == 1 else next((c for c in kids if c.name.startswith(('lowerarm', 'hand', 'calf', 'foot', 'ball', 'spine', 'neck', 'Head'))), None)
for b in eb:
    if b.name not in P: print('unmapped', b.name); continue
for b in eb:
    if b.name not in P: continue
    d = Vector(P[b.name]) - b.head
    b.translate(d)
for b in eb:
    c = primary_child(b)
    if c is not None and c.name in P:
        L = (Vector(P[c.name]) - b.head).length
        if L > 1e-3:
            b.length = L
def about(q, S):
    return Matrix.Translation(Vector(S)) @ q.to_matrix().to_4x4() @ Matrix.Translation(-Vector(S))
for side in ('l', 'r'):
    q, S = Rot[side]
    M = about(q, S)
    for name in arm_bones[side]:
        eb[name].transform(M)                           # down into her A-pose, to bind
bpy.ops.object.mode_set(mode='OBJECT')

# ------------------------------------------------------------ weights --
bpy.ops.object.select_all(action='DESELECT')
ch.select_set(True); qarm.select_set(True)
bpy.context.view_layer.objects.active = qarm
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
# What the heat left out (eyes, lashes, brows: separate pieces in the head)
# rides the head.
head = ch.vertex_groups.get('Head') or ch.vertex_groups.new(name='Head')
loose = [v.index for v in me.vertices if not v.groups]
head.add(loose, 1.0, 'REPLACE')
print('bound;', len(loose), 'loose vertices given to the head')
# Bone heat splits the pelvis from the thighs (and the chest from the
# shoulders) too sharply: a lifted leg creases. Relax the weights across
# the joints of the body (the head's pieces stay rigid).
bpy.ops.object.select_all(action='DESELECT')
ch.select_set(True)
bpy.context.view_layer.objects.active = ch
bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
for g in ch.vertex_groups:
    if g.name in ('Head',): continue
    ch.vertex_groups.active_index = g.index
    bpy.ops.object.vertex_group_smooth(group_select_mode='ACTIVE', factor=0.5, repeat=6, expand=0.0)
bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
bpy.ops.object.mode_set(mode='OBJECT')

# ------------------------------------------------------------ arms up --
gidx = {g.name: g.index for g in ch.vertex_groups}
W = {side: np.zeros(n) for side in ('l', 'r')}
for v in me.vertices:
    for g in v.groups:
        nm = ch.vertex_groups[g.group].name
        for side in ('l', 'r'):
            if nm in arm_bones[side]:
                W[side][v.index] += g.weight
# Only the arm itself goes up with it: near its axis and past the shoulder
# (in her A-pose the heat leaks the arm into the side of her chest).
A0v = get(keys[0])
adj = [[] for _ in range(n)]
for e in me.edges:
    a_, b_ = e.vertices
    adj[a_].append(b_); adj[b_].append(a_)
for side in ('l', 'r'):
    S, ax, La = Axis[side]
    d = A0v - S
    t = d @ ax
    perp = np.linalg.norm(d - np.outer(t, ax), axis=1)
    near = np.clip((0.075 - perp) / 0.03, 0, 1) * np.clip((t + 0.03) / 0.05, 0, 1)
    W[side] *= near
    # The forearm and hand (what joins the fingertip along its own skin
    # past the elbow, not the thigh or the hip it hangs against) go up
    # whole, the thumb with them: the heat gives some of the hand to the
    # thigh beside it, and a hand half raised folds.
    inside = (t > 0.42 * La) & (perp < 0.2)
    comp = np.zeros(n, bool)
    todo = [int(np.argmax(np.where(perp < 0.1, t, -9)))]      # the fingertip
    comp[todo[0]] = True
    while todo:
        v = todo.pop()
        for u in adj[v]:
            if inside[u] and not comp[u]:
                comp[u] = True; todo.append(u)
    ramp = np.clip((t - 0.42 * La) / (0.1 * La), 0, 1)
    ramp = ramp * ramp * (3 - 2 * ramp)
    W[side][comp] = np.maximum(W[side][comp], ramp[comp])
    print(side, 'forearm and hand:', comp.sum(), 'vertices')
for kb in keys:
    a = get(kb)
    for side in ('l', 'r'):
        q, S = Rot[side]
        Rinv = np.array(q.inverted().to_matrix())
        up = S + (a - S) @ Rinv.T
        w = np.clip(W[side], 0, 1)[:, None]
        a = a + w * (up - a)
    put(kb, a)
me.vertices.foreach_set('co', get(keys[0]).reshape(-1))
me.update()
bpy.context.view_layer.objects.active = qarm
bpy.ops.object.mode_set(mode='EDIT')
for side in ('l', 'r'):
    q, S = Rot[side]
    Minv = about(q.inverted(), S)
    for name in arm_bones[side]:
        eb[name].transform(Minv)                        # and back to the skeleton's T
bpy.ops.object.mode_set(mode='OBJECT')

# Her hands (anime_hands.py): the elbow and the wrist in the middle of her arm,
# the hand turned at the wrist to lie along the skeleton's, and each
# finger's joints on the line through the middle of that finger.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anime_hands as handfit
EI = np.array([e.vertices[:] for e in me.edges])
ek = {tuple(sorted(e.vertices[:])): i for i, e in enumerate(me.edges)}
M = (EI, np.array([(p.index, ek[tuple(sorted(k))]) for p in me.polygons for k in p.edge_keys]))
V = get(keys[0])
for side, sx in (('l', 1), ('r', -1)):
    handfit.centre_arm(V, M, P, side, sx)
    o, axis, ang = handfit.straighten_forearm(V, P, QH[f'hand_{side}'] - QH[f'lowerarm_{side}'], side, sx)
    for kb in keys:
        put(kb, handfit.rotate(get(kb), o, axis, ang))
    V = get(keys[0])
    handfit.centre_arm(V, M, P, side, sx)
    o, axis, ang = handfit.straighten(V, P, QH[f'middle_04_leaf_{side}'] - QH[f'middle_01_{side}'], side, sx)
    for kb in keys:
        put(kb, handfit.rotate(get(kb), o, axis, ang))
    V = get(keys[0])
    handfit.fit_fingers(V, M, P, side, sx)
    handfit.fit_thumb(V, P, side, sx)
me.vertices.foreach_set('co', V.reshape(-1))
me.update()
bpy.context.view_layer.objects.active = qarm
bpy.ops.object.mode_set(mode='EDIT')
DIGITS = ('index', 'middle', 'ring', 'pinky', 'thumb')
for side in ('l', 'r'):
    names = [f'lowerarm_{side}', f'hand_{side}'] + [f'{f}_0{i}_{side}' for f in DIGITS for i in (1, 2, 3)] + [f'{f}_04_leaf_{side}' for f in DIGITS]
    for c in names:
        eb[c].translate(Vector(P[c]) - eb[c].head)
    pairs = [(f'upperarm_{side}', f'lowerarm_{side}'), (f'lowerarm_{side}', f'hand_{side}'), (f'hand_{side}', f'middle_01_{side}')]
    for f in DIGITS:
        pairs += [(f'{f}_01_{side}', f'{f}_02_{side}'), (f'{f}_02_{side}', f'{f}_03_{side}'), (f'{f}_03_{side}', f'{f}_04_leaf_{side}')]
    for a_, b_ in pairs:
        L = (eb[b_].head - eb[a_].head).length
        if L > 1e-4: eb[a_].length = L
bpy.ops.object.mode_set(mode='OBJECT')

# Weighted again, now in the T: the arms clear of the body, nothing of them
# reaches into the chest.
for m in [m for m in ch.modifiers if m.type == 'ARMATURE']:
    ch.modifiers.remove(m)
ch.vertex_groups.clear()
ch.parent = None
bpy.ops.object.select_all(action='DESELECT')
ch.select_set(True); qarm.select_set(True)
bpy.context.view_layer.objects.active = qarm
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
head = ch.vertex_groups.get('Head') or ch.vertex_groups.new(name='Head')
loose = [v.index for v in me.vertices if not v.groups]
head.add(loose, 1.0, 'REPLACE')
print('bound again in T;', len(loose), 'loose vertices to the head')
# The bust moves as one with the chest (split between the chest and the
# collarbones, a turn of the shoulders shears it): where her own 'Breast
# Size' shape moves the surface, the weight goes to spine_03, softly.
B0 = get(keys[0])
bust = np.linalg.norm(get(keys['Breast Size']) - B0, axis=1)
# (the key also nudges a few far vertices, the hands among them: the chest only)
cz = P['spine_03'][2]
region = (np.abs(B0[:, 0]) < 0.16) & (np.abs(B0[:, 2] - cz) < 0.16) & (B0[:, 1] < P['spine_03'][1])
wb = np.clip((bust - 0.0008) / 0.004, 0, 1) * region
wb = wb * wb * (3 - 2 * wb)
chest = ch.vertex_groups.get('spine_03')
groups = {g.index: g for g in ch.vertex_groups}
moved = 0
for v in me.vertices:
    k = wb[v.index]
    if k <= 0: continue
    for g in v.groups:
        groups[g.group].add([v.index], g.weight * (1 - k), 'REPLACE')
    cur = next((g.weight for g in v.groups if g.group == chest.index), 0.0)
    chest.add([v.index], cur + k, 'REPLACE')
    moved += 1
print('bust to the chest:', moved, 'vertices')
bpy.ops.object.select_all(action='DESELECT')
ch.select_set(True)
bpy.context.view_layer.objects.active = ch
bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
for g in ch.vertex_groups:
    if g.name == 'Head': continue
    ch.vertex_groups.active_index = g.index
    bpy.ops.object.vertex_group_smooth(group_select_mode='ACTIVE', factor=0.5, repeat=6, expand=0.0)
bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
bpy.ops.object.mode_set(mode='OBJECT')

# The hands weighted from their joint lines (bone heat gives the palm to
# the knuckles, and a curled finger drags the palm after it).
def group(name):
    return ch.vertex_groups.get(name) or ch.vertex_groups.new(name=name)
for side, sx in (('l', 1), ('r', -1)):
    idx, blend, Wn = handfit.hand_weights(V, P, side, sx)
    for j, vi in enumerate(idx.tolist()):
        v = me.vertices[vi]
        new = {n: blend[j] * w[j] for n, w in Wn.items()}
        for g in v.groups:
            n = ch.vertex_groups[g.group].name
            new[n] = new.get(n, 0) + (1 - blend[j]) * g.weight
        for gi in [g.group for g in v.groups]:
            ch.vertex_groups[gi].remove([vi])
        tot = sum(new.values())
        for n, w in new.items():
            if w / tot > 1e-3:
                group(n).add([vi], w / tot, 'REPLACE')
    print(side, 'hand weights from its joints:', len(idx), 'vertices')

# ------------------------------------------------------------ materials --
for mat in me.materials:
    img = next((n.image for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image), None)
    nt = mat.node_tree
    for nd in list(nt.nodes): nt.nodes.remove(nd)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = 0.65
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    if img:
        tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    print('material', mat.name, img.name if img else None)

bpy.ops.object.select_all(action='DESELECT')
ch.select_set(True); qarm.select_set(True)
bpy.ops.export_scene.gltf(filepath=out_glb, export_format='GLB', use_selection=True, export_animations=False,
                          export_morph=True, export_morph_normal=True, export_skins=True, export_yup=True)
bpy.ops.wm.save_as_mainfile(filepath=out_glb.replace('.glb', '.blend'))
print('wrote', out_glb)
