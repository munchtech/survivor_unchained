"""A relief modelled as a height field, rendered in Blender (Cycles) under the house light.

    blender -b -P tools/uiforge/blender_relief.py -- relief.npz out.png [samples]

relief.npz (made by relief.py) holds, at the render's own resolution (one vertex per
pixel, y down):
    height  (H, W)     float, in render pixels (how far the surface stands up)
    alpha   (H, W)     coverage, 0..1 (faces where it is 0 are dropped; the edge is
                       anti-aliased by a transparent mix)
    base    (H, W, 3)  linear albedo
    metal   (H, W)     metalness
    rough   (H, W)     roughness
    emit    (H, W, 3)  linear emitted light (ember, the heart's glow)

Everything about the look (iron, gold, wear, grime, ember) is painted in numpy, where it
can be exact; Blender gives the light: reflections of the house's warm softbox and cool
rim (blender_frames.world), the sun's shadows across the relief, and occlusion in the
hollows. A height field is all a piece seen straight on needs.
"""
import math
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_frames as BF  # noqa: E402

U = BF.U


def mesh_from(height, alpha):
    H, W = height.shape
    # Vertices at pixel centres; the camera sees exactly W x H pixels.
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    vx = (xs + 0.5 - W / 2) * U
    vy = (H / 2 - ys - 0.5) * U
    vz = height * U
    co = np.stack([vx, vy, vz], -1).reshape(-1, 3)
    # A quad between four neighbours wherever any corner is covered.
    keep = alpha > 0.002
    k = keep[:-1, :-1] | keep[1:, :-1] | keep[:-1, 1:] | keep[1:, 1:]
    iy, ix = np.nonzero(k)
    a = iy * W + ix
    quads = np.stack([a, a + W, a + W + 1, a + 1], 1)  # counter-clockwise seen from +z
    used = np.zeros(H * W, bool)
    used[quads.ravel()] = True
    remap = np.cumsum(used) - 1
    co = co[used]
    quads = remap[quads]
    me = bpy.data.meshes.new("relief")
    me.vertices.add(len(co))
    me.vertices.foreach_set("co", co.ravel())
    nq = len(quads)
    me.loops.add(nq * 4)
    me.loops.foreach_set("vertex_index", quads.ravel().astype(np.int32))
    me.polygons.add(nq)
    me.polygons.foreach_set("loop_start", (np.arange(nq) * 4).astype(np.int32))
    me.polygons.foreach_set("loop_total", np.full(nq, 4, np.int32))
    me.update(calc_edges=True)
    me.validate()
    me.polygons.foreach_set("use_smooth", np.ones(nq, bool))
    return me, used


def add_attr(me, name, arr, used):
    """A per-vertex attribute (float or colour) from a full-resolution map."""
    if arr.ndim == 2:
        at = me.attributes.new(name, "FLOAT", "POINT")
        at.data.foreach_set("value", arr.reshape(-1)[used].astype(np.float32))
    else:
        rgba = np.concatenate([arr.reshape(-1, 3), np.ones((arr.shape[0] * arr.shape[1], 1), np.float32)], 1)
        at = me.attributes.new(name, "FLOAT_COLOR", "POINT")
        at.data.foreach_set("color", rgba[used].ravel().astype(np.float32))


def material():
    m = bpy.data.materials.new("relief")
    m.use_nodes = True
    nt = m.node_tree
    n, k = nt.nodes, nt.links
    bsdf = n["Principled BSDF"]
    out = n["Material Output"]

    def attr(name, socket="Color"):
        a = n.new("ShaderNodeAttribute")
        a.attribute_name = name
        return a.outputs[socket]
    k.new(attr("base"), bsdf.inputs["Base Color"])
    k.new(attr("metal", "Fac"), bsdf.inputs["Metallic"])
    k.new(attr("rough", "Fac"), bsdf.inputs["Roughness"])
    k.new(attr("emit"), bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 1.0
    # The anti-aliased edge: mixed with nothing by the coverage.
    tr = n.new("ShaderNodeBsdfTransparent")
    mix = n.new("ShaderNodeMixShader")
    k.new(attr("alpha", "Fac"), mix.inputs[0])
    k.new(tr.outputs[0], mix.inputs[1])
    k.new(bsdf.outputs[0], mix.inputs[2])
    k.new(mix.outputs[0], out.inputs[0])
    return m


def build(npz, out, samples=128):
    d = np.load(npz)
    height = d["height"].astype(np.float32)
    alpha = d["alpha"].astype(np.float32)
    H, W = height.shape
    sc = BF.reset()
    BF.world("night")
    BF.suns()
    BF.camera(W, H)
    me, used = mesh_from(height, alpha)
    add_attr(me, "base", d["base"].astype(np.float32), used)
    add_attr(me, "metal", d["metal"].astype(np.float32), used)
    add_attr(me, "rough", d["rough"].astype(np.float32), used)
    add_attr(me, "emit", d["emit"].astype(np.float32), used)
    add_attr(me, "alpha", alpha, used)
    ob = bpy.data.objects.new("relief", me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(material())
    sc.cycles.samples = samples
    sc.cycles.max_bounces = 6
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:]
    build(argv[0], argv[1], int(argv[2]) if len(argv) > 2 else 128)
