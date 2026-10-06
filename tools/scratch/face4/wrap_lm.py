NRM = vertex_normals(P, F)


# ---------------------------------------------------------- TRELLIS's head --
def load_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    ob = next(o for o in new if o.type == "MESH")
    for o in new:
        if o != ob:
            bpy.data.objects.remove(o)
    mw = np.array(ob.matrix_world)
    ob.parent = None
    V = np.zeros(len(ob.data.vertices) * 3)
    ob.data.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
    ob.matrix_world = Matrix.Identity(4)
    ob.data.vertices.foreach_set("co", V.ravel())
    ob.data.update()
    return ob, V


shape_ob, TV = load_glb(SHAPE)
paint_ob, PV = load_glb(PAINTED)
print("TRELLIS: %d points of surface (%d painted); %.3f across" % (len(TV), len(PV), np.ptp(TV, 0).max()))
sc = bpy.context.scene
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        sc.render.engine = eng
        break
    except TypeError:
        pass
sc.view_settings.view_transform = "Standard"
sc.world = bpy.data.worlds.new("w")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.5, 0.5, 1)
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
_sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
_sun.data.energy = 2.0
_sun.data.angle = math.radians(20)
sc.collection.objects.link(_sun)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
sc.render.resolution_x = sc.render.resolution_y = 1024
sc.render.resolution_percentage = 100
grey = bpy.data.materials.new("clay")
grey.use_nodes = True
grey.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.62, 0.52, 0.47, 1)
grey.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.55
# (its colours on its points, for the hair it is read to have)
_pm = bpy.data.materials.new("painted")
_pm.use_nodes = True
_nt = _pm.node_tree
_attr = _nt.nodes.new("ShaderNodeVertexColor")
if paint_ob.data.color_attributes:
    _attr.layer_name = paint_ob.data.color_attributes[0].name
_nt.links.new(_attr.outputs["Color"], _nt.nodes["Principled BSDF"].inputs["Base Color"])
_nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
paint_ob.data.materials.clear()
paint_ob.data.materials.append(_pm)
shape_ob.data.materials.clear()
shape_ob.data.materials.append(grey)
paint_ob.hide_render = True
hm.hide_render = True


def mesh_object(name, V, Fc):
    m_ = bpy.data.meshes.new(name)
    m_.from_pydata([tuple(p) for p in V], [], [tuple(int(i) for i in f) for f in Fc])
    for p_ in m_.polygons:
        p_.use_smooth = True
    o_ = bpy.data.objects.new(name, m_)
    sc.collection.objects.link(o_)
    m_.materials.append(grey)
    return o_


def look(centre, fwd, scale):
    """The orthographic camera on `centre`, looking along `fwd`, `scale` across;
    the sun from over the camera's shoulder."""
    fwd = Vector(fwd).normalized()
    cam.location = Vector(centre) - fwd * 3.0
    cam.rotation_euler = fwd.to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = scale
    cam.data.clip_end = 10.0
    _sun.rotation_euler = (fwd + Vector((0.2, 0, -0.5))).normalized().to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()


def marks(png):
    """MediaPipe's landmarks in a render, in its pixels (None: no face)."""
    js = png[:-4] + ".json"
    if os.path.exists(js):
        os.remove(js)
    subprocess.run([FACEFIT_PY, os.path.join(HERE, "face_fit.py"), "marks", png, js, "whole"], capture_output=True)
    return np.array(json.load(open(js))["points"]) if os.path.exists(js) else None


def to_world(px):
    """Pixels of the camera's picture as points on its plane, and its forward."""
    mwc = cam.matrix_world
    right, up, fwd = (np.array((mwc.to_3x3() @ Vector(a))[:]) for a in ((1, 0, 0), (0, 1, 0), (0, 0, -1)))
    res = sc.render.resolution_x
    u = (px[:, 0] / res - 0.5) * cam.data.ortho_scale
    v = (0.5 - px[:, 1] / res) * cam.data.ortho_scale
    return np.array(mwc.translation)[None] + u[:, None] * right + v[:, None] * up, fwd


def landmarks(objs, bvhs, V, name, fwds=((0, 1, 0),)):
    """MediaPipe's landmarks on a head (`objs` drawn, in clay, lit from in
    front: the same for hers and TRELLIS's, so the two are read alike),
    cast back onto its surfaces (`bvhs`): each landmark's point, and which
    surface it fell on (-1 none) with its face there."""
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.hide_render = o not in objs
    mid = (V.min(0) + V.max(0)) / 2
    L2 = None
    for fwd in fwds:
        look(mid, fwd, np.ptp(V, 0).max() * 1.05)
        sc.render.filepath = os.path.join(WORK, name + "_find.png")
        bpy.ops.render.render(write_still=True)
        L2 = marks(sc.render.filepath)
        if L2 is not None:
            break
    if L2 is None:
        raise SystemExit("no face found on " + name)
    # (then closer: the face filling the picture, for MediaPipe's best)
    pts, f_ = to_world(L2)
    span = np.ptp(L2, 0).max() / sc.render.resolution_x * cam.data.ortho_scale
    look(pts.mean(0), fwd, span * 1.6)
    sc.render.filepath = os.path.join(WORK, name + "_front.png")
    bpy.ops.render.render(write_still=True)
    L2 = marks(sc.render.filepath)
    if L2 is None:
        raise SystemExit("no face found close up on " + name)
    pts, f_ = to_world(L2)
    out = np.full((len(L2), 3), np.nan)
    which = -np.ones(len(L2), int)
    face = -np.ones(len(L2), int)
    for i, p in enumerate(pts):
        best = None
        for k, bvh in enumerate(bvhs):
            r = bvh.ray_cast(Vector(p), Vector(f_), 10.0)
            if r[0] is not None and (best is None or r[3] < best[1][3]):
                best = (k, r)
        if best is not None:
            out[i], which[i], face[i] = best[1][0][:], best[0], best[1][2]
    print("LANDMARKS on %s: %d of %d" % (name, (which >= 0).sum(), len(L2)))
    return out, which, face


# Her landmarks: her head as she is (her face's targets and sculpts), with
# her eyeballs in, so the rims of her lids are read where they lie.
DATA = os.path.join(bpy.utils.user_resource("EXTENSIONS"), ".user", "user_default", "mpfb", "data")
_eo = HumanService.add_mhclo_asset(os.path.join(DATA, "eyes", "high-poly", "high-poly.mhclo"), hm, asset_type="eyes",
                                   subdiv_levels=0, material_type="NONE", set_up_rigging=False, interpolate_weights=False,
                                   import_subrig=False, import_weights=False)
for mo in _eo.modifiers:
    mo.show_viewport = mo.show_render = False
bpy.context.view_layer.update()
_ee = _eo.evaluated_get(bpy.context.evaluated_depsgraph_get())
_em = _ee.to_mesh()
EV = np.array([(_ee.matrix_world @ v.co)[:] for v in _em.vertices])
_em.calc_loop_triangles()
EF = np.array([t.vertices[:] for t in _em.loop_triangles])
_ee.to_mesh_clear()
bpy.data.objects.remove(_eo)
her_ob = mesh_object("her", P, F)
eyes_ob = mesh_object("her_eyes", EV, EF)
HBVH = BVHTree.FromPolygons([tuple(p) for p in P], F.tolist())
EBVH = BVHTree.FromPolygons([tuple(p) for p in EV], EF.tolist())
L0, _w0, _f0 = landmarks([her_ob, eyes_ob], [HBVH, EBVH], P[BODY & (P[:, 2] > P[BODY, 2].max() - 0.32)], "her")
# Each landmark on her skin anchored there (its face and where in it), to move as her skin does.
hit = _w0 == 0
tri = np.zeros((len(L0), 3), int)
bary = np.zeros((len(L0), 3))
for i in np.where(hit)[0]:
    a_, b_, c_ = P[F[_f0[i]]]
    v0, v1, v2 = b_ - a_, c_ - a_, L0[i] - a_
    d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01
    bv, bw = (d11 * d20 - d01 * d21) / den, (d00 * d21 - d01 * d20) / den
    tri[i], bary[i] = F[_f0[i]], [1 - bv - bw, bv, bw]
hit[IRIS] = False
her_ob.hide_render = eyes_ob.hide_render = True

TBVH = BVHTree.FromObject(shape_ob, bpy.context.evaluated_depsgraph_get())
Lt, _wt, _ = landmarks([shape_ob], [TBVH], TV, "trellis", fwds=((0, 1, 0), (0, -1, 0), (1, 0, 0), (-1, 0, 0)))
