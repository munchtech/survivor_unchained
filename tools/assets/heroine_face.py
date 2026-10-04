"""Her face painted: photographic skin, brows, lashes and lips for the head
heroine_head.py made, by the local ComfyUI.

    blender -b tools/comfy/out/heroes/heroine_built.blend --python tools/assets/heroine_face.py -- tools/assets/heroine_face

Her head is drawn flat (its colours, no light) from the front and from
three-quarters either side; Krea 2 paints each drawing over as a photograph
of a beautiful young woman, lightly (so her features stay where her head has
them); and each painting is laid back onto her head's texture, every texel
from the views that see it most squarely. The views are matched to the
front's colouring where they overlap, and all of it to her own skin.

Written to <out>/face_paint.png, in her head's UV (heroine_head.py lays it
over her skin, by its alpha), with the drawings and paintings beside it.
Run again when her face's shape (heroine_head.py's FACE) changes. ComfyUI
must be running (tools/comfy/comfy.py).
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "comfy"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comfy  # noqa: E402
import face_shapes as fs  # noqa: E402

OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
os.makedirs(OUT, exist_ok=True)
SIZE = 4096                        # her head's texture (heroine_head.py's HSIZE)
SCALE = 0.25                       # metres across each drawing
DRAW = 1536                        # its pixels across
CENTRE = Vector((0.0, -0.02, 1.735))
VIEWS = {"front": 0.0, "left": 55.0, "right": -55.0}
DENOISE = 0.45                     # more and her features move away from her head's
SEED = int(os.environ.get("FACE_SEED", "7"))
# A beauty campaign's photograph, as her reference faces were painted
# (face_refs.py), but bald (her head is) and in flat light (it is taken off
# after, and the game lights her): fine groomed brows (heavy ones read
# masculine, FACE_RESEARCH.md), lashes and a lip tint, luminous skin.
PROMPT = ("A high-end beauty campaign photograph, {view} of the face of a breathtakingly beautiful young woman of twenty-four, fair "
          "porcelain skin with light delicate freckles across her nose and cheeks, luminous smooth skin with fine natural pores, bright "
          "green eyes, long dark defined eyelashes, fine softly arched groomed auburn eyebrows, clean eyelids, subtle elegant makeup, "
          "full soft rose lips with a soft lip tint, completely bald smooth shaved head, serene neutral expression, flat even soft "
          "studio lighting with no shadows, plain grey background, sharp focus, high detail.")
VIEW_WORDS = {"front": "straight-on front view", "left": "three-quarter view", "right": "three-quarter view"}

head = bpy.data.objects["HeroineHead"]
sc = bpy.context.scene
SKIN_AS_IS = None

# One of her other faces (face_presets.py), painted on her head shaped as
# it: FACE_SHAPE a JSON file of its sliders ({slider: -1 to 1}, set on her
# head's keys and its parts'), FACE_WHO the words for the woman it is (as
# face_refs.FACES has her, without her hair).
if os.environ.get("FACE_SHAPE"):
    import json
    _shape = json.load(open(os.environ["FACE_SHAPE"], encoding="utf-8-sig"))
    for _o in bpy.data.objects:
        if _o.type == "MESH" and _o.data.shape_keys:
            _kb = _o.data.shape_keys.key_blocks
            for _s, _v in _shape.items():
                if _s + "+" in _kb:
                    _kb[_s + "+"].value = max(_v, 0.0)
                if _s + "-" in _kb:
                    _kb[_s + "-"].value = max(-_v, 0.0)
    bpy.context.view_layer.update()
    print("SHAPED as", _shape)
if os.environ.get("FACE_WHO"):
    PROMPT = ("A high-end beauty campaign photograph, {view} of the face of " + os.environ["FACE_WHO"] + " Completely bald smooth "
              "shaved head, serene neutral expression, subtle elegant makeup, defined lashes, luminous skin with fine natural pores, flat "
              "even soft studio lighting with no shadows, plain grey background, sharp focus, high detail.")


def as_shaped(o):
    """An object's points and normals as its keys shape it (each key's move
    at its value: no modifiers, which would renumber its points), in the world."""
    me = o.data
    V = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3)
    if me.shape_keys:
        kb = me.shape_keys.key_blocks
        base = np.zeros(len(V) * 3)
        kb[0].data.foreach_get("co", base)
        base = base.reshape(-1, 3)
        V = base.copy()
        for k in kb[1:]:
            if k.value:
                co = np.zeros(len(V) * 3)
                k.data.foreach_get("co", co)
                V += k.value * (co.reshape(-1, 3) - base)
    mw = np.array(o.matrix_world)
    V = V @ mw[:3, :3].T + mw[:3, 3]
    # (normals from the faces round each point, as shaped)
    N = np.zeros_like(V)
    for p in me.polygons:
        vs = list(p.vertices)
        n = np.cross(V[vs[1]] - V[vs[0]], V[vs[-1]] - V[vs[0]])
        N[vs] += n
    N /= np.linalg.norm(N, axis=1)[:, None] + 1e-12
    # (out from her, as Blender's own normals are)
    own = np.array([v.normal[:] for v in me.vertices]) @ mw[:3, :3].T
    if (N * own).sum(1).mean() < 0:
        N = -N
    return V, N


# ------------------------------------------------------------ drawings --
def clean_skin(size=21):
    """Her head's skin as drawn, without MakeHuman's freckles (a grey
    closing: every dark fleck smaller than `size` texels, 2 mm or so on her
    face, filled from the skin round it). Drawn with them, the painting
    copies every one, far more than the light freckles asked for. (The
    drawing's only: nothing is saved.)"""
    global SKIN_AS_IS
    from scipy import ndimage
    img = next(n.image for n in head.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and n.image)
    w, h = img.size
    a = np.array(img.pixels[:], np.float32).reshape(h, w, 4)
    SKIN_AS_IS = a.copy()                    # (her skin's colouring, which the painting is matched to, as it is)
    for k in range(3):
        a[..., k] = ndimage.grey_closing(a[..., k], size=(size, size))
    img.pixels.foreach_set(a.ravel())
    img.update()


def draw():
    """Her head and neck in their own colours, no light, from each view."""
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            pass
    sc.render.resolution_x = sc.render.resolution_y = DRAW
    sc.view_settings.view_transform = "Standard"
    sc.world = sc.world or bpy.data.worlds.new("W")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.45, 0.45, 0.47, 1)
    # Her brows drawn too, so the painting keeps them where her brow is (left
    # to itself it painted them higher); not her lashes.
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.hide_render = o.name not in ("HeroineHead", "HeroineEyes", "HeroineBrows", "Heroine")
            for m in o.modifiers:
                m.show_render = False
    for o in bpy.data.objects:
        if o.type != "MESH" or o.hide_render:
            continue
        for m in o.data.materials:
            nt = m.node_tree
            tex = next((n for n in nt.nodes if n.type == "TEX_IMAGE"), None)
            out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
            em = nt.nodes.new("ShaderNodeEmission")
            if tex:
                nt.links.new(tex.outputs["Color"], em.inputs["Color"])
            if tex and (m.name.startswith("eyes") or m.name.startswith("brows")):
                # (the clear cornea, clear)
                tr = nt.nodes.new("ShaderNodeBsdfTransparent")
                mix = nt.nodes.new("ShaderNodeMixShader")
                nt.links.new(tex.outputs["Alpha"], mix.inputs[0])
                nt.links.new(tr.outputs[0], mix.inputs[1])
                nt.links.new(em.outputs[0], mix.inputs[2])
                nt.links.new(mix.outputs[0], out.inputs["Surface"])
                m.surface_render_method = "DITHERED"
            else:
                nt.links.new(em.outputs[0], out.inputs["Surface"])
    clean_skin()
    cam = bpy.data.objects.new("FaceCam", bpy.data.cameras.new("FaceCam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = SCALE
    for name, ang in VIEWS.items():
        a = math.radians(ang)
        cam.location = CENTRE + Vector((math.sin(a), -math.cos(a), 0))
        cam.rotation_euler = (CENTRE - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(OUT, f"drawn_{name}.png")
        bpy.ops.render.render(write_still=True)


def paint(name):
    """A drawing painted over by Krea 2 (turbo, local)."""
    img = comfy.upload(os.path.join(OUT, f"drawn_{name}.png"))
    g = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": PROMPT.format(view=VIEW_WORDS[name]), "clip": ["2", 0]}},
        "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "6": {"class_type": "LoadImage", "inputs": {"image": img}},
        "7": {"class_type": "VAEEncode", "inputs": {"pixels": ["6", 0], "vae": ["3", 0]}},
        "8": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["7", 0],
                                                    "seed": SEED, "steps": 8, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple",
                                                    "denoise": DENOISE}},
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
        "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": f"heroine_face_{name}"}},
    }
    got = comfy.run(g, OUT)
    dst = os.path.join(OUT, f"painted_{name}.png")
    os.replace(got[0], dst)
    return dst


# ----------------------------------------------------------- laid back --
def load(path):
    from PIL import Image
    return np.asarray(Image.open(path).convert("RGB"), np.float32)[::-1] / 255     # rows from the bottom


def sample(img, uv):
    h, w = img.shape[:2]
    x = np.clip(uv[:, 0] * w - 0.5, 0, w - 1.001)
    y = np.clip(uv[:, 1] * h - 0.5, 0, h - 1.001)
    x0, y0 = x.astype(int), y.astype(int)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


def delit(name):
    """The painting without the light it was painted in: its fine detail
    (pores, freckles, brow hairs, lips) on the broad colour of the flat
    drawing, so no shadow of the painting's is laid on her (the game lights
    her)."""
    from scipy import ndimage
    paint, drawn = load(os.path.join(OUT, f"painted_{name}.png")), load(os.path.join(OUT, f"drawn_{name}.png"))
    sg = DRAW / 25
    broad_p = np.stack([ndimage.gaussian_filter(paint[..., k], sg) for k in range(3)], 2)
    broad_d = np.stack([ndimage.gaussian_filter(drawn[..., k], sg) for k in range(3)], 2)
    return np.clip(paint / np.maximum(broad_p, 1e-3) * broad_d, 0, 1)


def texels():
    """Every texel of her head's texture its faces cover: where it is on her
    and which way it faces (and its triangle and weights, for what else is
    known at her head's points)."""
    me = head.data
    V, N = as_shaped(head)                 # (as shaped: one of her other faces, if asked for)
    me.calc_loop_triangles()
    T = np.array([t.vertices[:] for t in me.loop_triangles])
    L = np.array([t.loops[:] for t in me.loop_triangles])
    uvd = me.uv_layers[0].data
    UV = np.array([d.uv[:] for d in uvd])[L] * SIZE
    rows, cols, tri, bary = [], [], [], []
    for k, t in enumerate(UV):
        x0, y0 = np.maximum(np.floor(t.min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(t.max(0)).astype(int), SIZE - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        p = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        a, b, c = t
        v0, v1, v2 = b - a, c - a, p - a
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12:
            continue
        v = (v2[:, 0] * v1[1] - v1[0] * v2[:, 1]) / den
        w = (v0[0] * v2[:, 1] - v2[:, 0] * v0[1]) / den
        bb = np.stack([1 - v - w, v, w], 1)
        m = (bb > -1e-3).all(1)
        rows.append(ys.ravel()[m])
        cols.append(xs.ravel()[m])
        tri.append(np.full(m.sum(), k))
        bary.append(bb[m])
    rows, cols, tri, bary = (np.concatenate(x) for x in (rows, cols, tri, bary))
    P = (V[T[tri]] * bary[:, :, None]).sum(1)
    Nt = (N[T[tri]] * bary[:, :, None]).sum(1)
    Nt /= np.linalg.norm(Nt, axis=1)[:, None] + 1e-12
    return rows, cols, T, tri, bary, V, N, P, Nt


def seen(V, N, toward):
    """Which of her head's points a view sees (nothing of her in the way)."""
    objs = [o for o in bpy.data.objects if o.type == "MESH" and o.name in ("HeroineHead", "Heroine", "HeroineEyes")]
    vs, fs = [], []
    for o in objs:
        base = len(vs)
        vs += [tuple(p) for p in as_shaped(o)[0]]
        fs += [[base + i for i in p.vertices] for p in o.data.polygons]
    bvh = BVHTree.FromPolygons(vs, fs)
    d = Vector(toward)
    return np.array([bvh.ray_cast(Vector(p) + Vector(n) * 0.0008 + d * 0.0005, d, 2.0)[0] is None for p, n in zip(V, N)])


def match(src, ref, m):
    """src's colouring made ref's, over the texels m."""
    ms, ss = src[m].mean(0), src[m].std(0) + 1e-6
    mr, sr = ref[m].mean(0), ref[m].std(0) + 1e-6
    return mr + (src - ms) * np.clip(sr / ss, 0.8, 1.25)


def free():
    """The shared GPU given back (the server answers with nothing)."""
    import json
    import urllib.request
    req = urllib.request.Request(comfy.URL + "/free", data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req).read()


if __name__ == "__main__":
    # (FACE_LAY_ONLY=1: the drawings and paintings already in <out>, say the
    # best view of each of several seeds gathered there, only laid back on)
    if not os.environ.get("FACE_LAY_ONLY"):
        draw()
        try:
            for name in VIEWS:
                paint(name)
                print("PAINTED", name)
        finally:
            free()
    rows, cols, T, tri, bary, V, N, P, Nt = texels()
    base = SKIN_AS_IS if SKIN_AS_IS is not None else \
        np.array(head.data.materials[0].node_tree.nodes["Image Texture"].image.pixels[:], np.float32).reshape(SIZE, SIZE, 4)
    cols_v, weights = {}, {}
    for name, ang in VIEWS.items():
        a = math.radians(ang)
        fwd = np.array([-math.sin(a), math.cos(a), 0.0])
        right = np.array([math.cos(a), math.sin(a), 0.0])
        d = P - np.array(CENTRE)
        uv = np.stack([0.5 + (d @ right) / SCALE, 0.5 + d[:, 2] / SCALE], 1)
        vis = seen(V, N, -fwd)[T[tri]]
        vis = (vis * bary).sum(1) > 0.99
        facing = np.clip(Nt @ -fwd, 0, 1)
        edge = np.clip(np.minimum.reduce([uv[:, 0], 1 - uv[:, 0], uv[:, 1], 1 - uv[:, 1]]) / 0.05, 0, 1)
        weights[name] = facing ** 4 * edge * vis * (1.0 if name == "front" else 0.8)
        cols_v[name] = sample(delit(name), uv)
        print("LAID", name, "%d texels seen" % (weights[name] > 0.05).sum())
    # The sides coloured as the front where both see her well.
    for name in ("left", "right"):
        both = (weights["front"] > 0.3) & (weights[name] > 0.3)
        if both.sum() > 500:
            cols_v[name] = match(cols_v[name], cols_v["front"], both)
    wsum = sum(weights.values())
    col = sum(cols_v[n] * weights[n][:, None] for n in VIEWS) / np.maximum(wsum, 1e-6)[:, None]
    cover = np.clip(wsum / 0.25, 0, 1)
    # Her face only: none of it over her scalp, from 1 to 3 cm above her
    # hairline (face_shapes.HAIRLINE), where her hair lies (a painting of a
    # bald head can paint hair there, swept back, and it showed at her temples).
    eye_z = float(np.mean([(bpy.data.objects["HeroineEyes"].matrix_world @ v.co).z
                           for v in bpy.data.objects["HeroineEyes"].data.vertices]))
    theta = np.arctan2(P[:, 0], -P[:, 1])
    up = P[:, 2] - (eye_z + fs.hairline_height(theta))
    cover *= 1 - np.clip((up - 0.01) / 0.02, 0, 1)
    # And all of it coloured as her skin (her head's own, which heroine_head.py
    # matched to her body), over her cheeks, brow and neck seen square on.
    skin = (cover > 0.9) & (np.abs(col - np.median(col[cover > 0.9], 0)).max(1) < 0.08)
    col = match(col, base[rows, cols, :3], skin)
    out = np.zeros((SIZE, SIZE, 4), np.float32)
    out[rows, cols, :3] = np.clip(col, 0, 1)
    out[rows, cols, 3] = cover
    from PIL import Image
    Image.fromarray((out[::-1] * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, "face_paint.png"))
    print("FACE PAINT", os.path.join(OUT, "face_paint.png"), "%d%% of her head painted" % (100 * (cover > 0.5).mean()))
