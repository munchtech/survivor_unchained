def stage_form():
    """The body's forms, clean: the sculpt as a solid in voxels (filled by
    casting through its closed remesh), where it is worked as clay is. What
    we remake is cut away (the tail, the ears, the tusks, the crest), the
    solid is opened (anything thinner than a few centimetres goes: the fur's
    flakes, the crest's spikes) and closed (small pits fill), and its surface
    is smoothed. It is what the low mesh is laid over and its normals' source;
    the paint is still taken from the sculpt."""
    import numpy as np
    from scipy import ndimage
    from mathutils.bvhtree import BVHTree
    load("prep.blend")
    sculpt = bpy.data.objects["Sculpt"]
    symmetrise(sculpt, CONFIG["mirror"])
    shell = duplicate(sculpt, "Shell")
    only(shell)
    shell.data.materials.clear()
    vox = CONFIG.get("voxel", 0.005)
    shell.data.remesh_voxel_size = vox
    bpy.ops.object.voxel_remesh()
    tree = BVHTree.FromObject(shell, bpy.context.evaluated_depsgraph_get())
    lo = Vector([min(v.co[i] for v in shell.data.vertices) for i in range(3)]) - Vector((0.04, 0.04, 0.04))
    hi_ = Vector([max(v.co[i] for v in shell.data.vertices) for i in range(3)]) + Vector((0.04, 0.04, 0.04))
    dims = [int(math.ceil((hi_[i] - lo[i]) / vox)) for i in range(3)]
    X = np.array([lo.x + (i + 0.5) * vox for i in range(dims[0])])
    Y = np.array([lo.y + (j + 0.5) * vox for j in range(dims[1])])
    Z = np.array([lo.z + (k + 0.5) * vox for k in range(dims[2])])
    solid = np.zeros(dims, bool)
    # Inside by parity along each column, cast up from under it.
    up = Vector((0, 0, 1))
    for i, x in enumerate(X):
        for j, y in enumerate(Y):
            o = Vector((x, y, lo.z - 0.01))
            hits = []
            while True:
                loc, nrm, idx, d = tree.ray_cast(o, up)
                if loc is None:
                    break
                hits.append(loc.z)
                o = loc + up * 1e-5
            for a, b in zip(hits[0::2], hits[1::2]):
                solid[i, j, (Z > a) & (Z < b)] = True
    bpy.data.objects.remove(shell)
    print("FILLED", int(solid.sum()))
    gx, gy, gz = np.meshgrid(X, Y, Z, indexing="ij")
    cut = CONFIG.get("cut", {})
    if "tail_y" in cut:
        solid &= ~(gy > cut["tail_y"])
    for (ex, ey, ez, er) in cut.get("ears", []):
        for s in (1, -1):
            solid &= ~((gx - s * ex) ** 2 + (gy - ey) ** 2 + (gz - ez) ** 2 < er * er)
    if "tusks" in cut:
        y0, y1, ax, z0, z1 = cut["tusks"]
        solid &= ~((gy > y0) & (gy < y1) & (np.abs(gx) > ax) & (gz > z0) & (gz < z1))
    back = CONFIG.get("backline")
    if back:
        line = np.array([interp(back["line"], y) for y in Y])
        solid &= ~((np.abs(gx) < back["half"]) & (gz > line[None, :, None] + back["over"]))
    del gx, gy, gz
    edt = ndimage.distance_transform_edt
    r_open, r_close = CONFIG.get("open", 0.015) / vox, CONFIG.get("close", 0.01) / vox
    # (edt(A): each voxel of A's distance to the nearest voxel outside it.)
    solid = edt(~(edt(solid) > r_open)) <= r_open    # opened: what is thinner than 2r goes
    solid = edt(edt(~solid) <= r_close) > r_close    # closed: gaps narrower than 2r fill
    lab, n = ndimage.label(solid)
    if n > 1:
        sizes = ndimage.sum(solid, lab, range(1, n + 1))
        solid = lab == (1 + int(np.argmax(sizes)))
    print("SOLID", dims, int(solid.sum()), "voxels")
    # Its faces where solid meets empty, as a blocky mesh, remeshed and smoothed.
    verts, faces, vid = [], [], {}

    def vert(i, j, k):
        key = (i, j, k)
        if key not in vid:
            vid[key] = len(verts)
            verts.append((lo.x + i * vox, lo.y + j * vox, lo.z + k * vox))
        return vid[key]
    pad = np.pad(solid, 1)
    for axis in range(3):
        d = np.diff(pad.astype(np.int8), axis=axis)
        for sign in (1, -1):
            for (i, j, k) in np.argwhere(d == sign):
                p = [i - 1, j - 1, k - 1]
                p[axis] += 1
                u, v = [(1, 2), (0, 2), (0, 1)][axis]
                q = [list(p) for _ in range(4)]
                q[1][u] += 1
                q[2][u] += 1
                q[2][v] += 1
                q[3][v] += 1
                f = [vert(*c) for c in q]
                faces.append(f if (sign == -1) ^ (axis == 1) else f[::-1])
    mesh = bpy.data.meshes.new("Form")
    mesh.from_pydata(verts, [], faces)
    form = bpy.data.objects.new("Form", mesh)
    bpy.context.scene.collection.objects.link(form)
    only(form)
    form.data.remesh_voxel_size = CONFIG.get("fine", 0.006)
    bpy.ops.object.voxel_remesh()
    sm = form.modifiers.new("smooth", "LAPLACIANSMOOTH")
    sm.iterations = CONFIG.get("smooth", 10)
    sm.lambda_factor = 0.5
    sm.use_volume_preserve = True
    bpy.ops.object.modifier_apply(modifier="smooth")
    bpy.ops.object.shade_smooth()
    symmetrise(form, CONFIG["mirror"])
    print("FORM", len(form.data.vertices), "verts")
    save("form.blend")


