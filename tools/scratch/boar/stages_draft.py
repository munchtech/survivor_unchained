# Draft of the later stages, merged into boar_build.py once the sculpt is in.

def symmetrise(obj, keep="+X"):
    """Half kept (the side the picture showed) and mirrored over x = 0."""
    only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.symmetrize(direction="POSITIVE_X" if keep == "+X" else "NEGATIVE_X", threshold=0.0005)
    bpy.ops.object.mode_set(mode="OBJECT")


def retopo(hi, faces=4600):
    """The low mesh: the sculpt remeshed watertight, then laid out in quads
    by QuadriFlow (mirrored over x = 0), and shrunk back onto the sculpt."""
    lo = hi.copy()
    lo.data = hi.data.copy()
    lo.name = "Boar"
    bpy.context.scene.collection.objects.link(lo)
    only(lo)
    for m in list(lo.data.materials):
        pass
    lo.data.materials.clear()
    lo.data.remesh_voxel_size = 0.008
    bpy.ops.object.voxel_remesh()
    bpy.ops.object.quadriflow_remesh(use_mesh_symmetry=True, use_preserve_sharp=False, use_preserve_boundary=False,
                                     preserve_attributes=False, smooth_normals=False, mode="FACES", target_faces=faces, seed=3)
    sw = lo.modifiers.new("onto", "SHRINKWRAP")
    sw.target = hi
    sw.wrap_method = "PROJECT"
    sw.use_negative_direction = True
    sw.use_positive_direction = True
    bpy.ops.object.modifier_apply(modifier="onto")
    return lo
