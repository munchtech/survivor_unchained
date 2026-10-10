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
# (her face's outline from one angle of her jaw round her chin to the other, by the face landmarks: under_jaw)
JAW_LINE = [132, 58, 172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361]
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
# head's keys and its parts'; or a key of its own, {"face_<id>": 1}),
# FACE_WHO the words for the woman it is (as face_refs.FACES has her,
# without her hair).
if os.environ.get("FACE_SHAPE"):
    import json
    _shape = json.load(open(os.environ["FACE_SHAPE"], encoding="utf-8-sig"))
    for _o in bpy.data.objects:
        if _o.type == "MESH" and _o.data.shape_keys:
            _kb = _o.data.shape_keys.key_blocks
            for _s, _v in _shape.items():
                if _s in _kb:
                    _kb[_s].value = _v
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
    if os.environ.get("FACE_REF"):
        # Her normals from in front (her skin only), for the reference's own
        # light to be read off it and taken out (delit_reference).
        cam.location = CENTRE + Vector((0, -1, 0))
        cam.rotation_euler = (CENTRE - cam.location).to_track_quat("-Z", "Y").to_euler()
        nm = bpy.data.materials.new("normals")
        nm.use_nodes = True
        nt = nm.node_tree
        geo, em = nt.nodes.new("ShaderNodeNewGeometry"), nt.nodes.new("ShaderNodeEmission")
        mad = nt.nodes.new("ShaderNodeVectorMath")
        mad.operation = "MULTIPLY_ADD"
        mad.inputs[1].default_value = (0.5, 0.5, 0.5)
        mad.inputs[2].default_value = (0.5, 0.5, 0.5)
        nt.links.new(geo.outputs["Normal"], mad.inputs[0])
        nt.links.new(mad.outputs[0], em.inputs["Color"])
        nt.links.new(em.outputs[0], next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL").inputs["Surface"])
        hidden = [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render and o.name not in ("HeroineHead", "Heroine")]
        for o in hidden:
            o.hide_render = True
        # (each slot of her head's and body's given the normals for the one
        # picture: the view layer's override is not EEVEE's)
        kept = {}
        for o in (bpy.data.objects["HeroineHead"], bpy.data.objects["Heroine"]):
            kept[o] = [s.material for s in o.material_slots]
            for s in o.material_slots:
                s.material = nm
        sc.render.filepath = os.path.join(OUT, "normals_front.png")
        bpy.ops.render.render(write_still=True)
        # And her head in clay, lit from in front, with her eyes: where
        # MediaPipe reads her features off her shape (her drawing's colours
        # are MakeHuman's skin's, its lips and brows where MakeHuman has them,
        # not where her shape has them now).
        clay = bpy.data.materials.new("clay")
        clay.use_nodes = True
        clay.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.62, 0.52, 0.47, 1)
        clay.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.55
        eyes = bpy.data.objects["HeroineEyes"]
        eyes.hide_render = False
        kept[eyes] = [s.material for s in eyes.material_slots]
        for o in kept:
            for s in o.material_slots:
                s.material = clay
        sun = bpy.data.objects.new("ClaySun", bpy.data.lights.new("ClaySun", "SUN"))
        sun.data.energy = 2.0
        sun.data.angle = math.radians(20)
        sun.rotation_euler = Vector((0.2, 1.0, -0.5)).normalized().to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(sun)
        sc.render.filepath = os.path.join(OUT, "clay_front.png")
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(sun)
        eyes.hide_render = True
        for o, mats in kept.items():
            for s, m in zip(o.material_slots, mats):
                s.material = m
        for o in hidden:
            o.hide_render = False


def paint_graph(name, path, text, denoise):
    """Krea 2 (turbo, local) painting over a picture, as a ComfyUI graph."""
    img = comfy.upload(path)
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": text, "clip": ["2", 0]}},
        "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "6": {"class_type": "LoadImage", "inputs": {"image": img}},
        "7": {"class_type": "VAEEncode", "inputs": {"pixels": ["6", 0], "vae": ["3", 0]}},
        "8": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["7", 0],
                                                    "seed": SEED, "steps": 8, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple",
                                                    "denoise": denoise}},
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
        "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": f"heroine_face_{name}"}},
    }


# Her skin's grain over her reference (from_reference): a close photograph's.
DETAIL_PROMPT = ("An extreme close-up high-end beauty photograph of a young woman's face from the front, natural real skin with "
                 "fine pores, faint fine vellus hair and delicate light freckles across her nose and cheeks, soft even studio light, "
                 "razor sharp focus, high detail, no retouching.")


def paint(name):
    """A drawing painted over by Krea 2 (turbo, local)."""
    g = paint_graph(name, os.path.join(OUT, f"drawn_{name}.png"), PROMPT.format(view=VIEW_WORDS[name]), DENOISE)
    got = comfy.run(g, OUT)
    dst = os.path.join(OUT, f"painted_{name}.png")
    os.replace(got[0], dst)
    return dst


def from_reference(ref):
    """The front painted with her reference itself (FACE_REF): its face
    warped onto the front drawing, landmark to landmark (MediaPipe's, read
    off both; a thin-plate spline between), now that her head is shaped
    as the reference's face (face_wrap.py). Every lid's fold, the lips'
    border and the brows' hairs are the photograph's own."""
    import json
    import subprocess

    from PIL import Image
    from scipy import ndimage
    from scipy.interpolate import RBFInterpolator
    py = os.path.join(os.environ.get("LOCALAPPDATA", ""), "facefit", ".venv", "Scripts", "python.exe")
    fit = os.path.join(os.path.dirname(os.path.abspath(__file__)), "face_fit.py")
    pts = {}
    for name, path in (("drawn", os.path.join(OUT, "clay_front.png")), ("ref", ref)):
        js = os.path.join(OUT, f"marks_{name}.json")
        subprocess.run([py, fit, "marks", path, js, "whole"], capture_output=True)
        if not os.path.exists(js):
            raise SystemExit(f"no face found in {path}")
        pts[name] = np.array(json.load(open(js))["points"])
    src = Image.open(ref).convert("RGB")
    sw, sh = src.size
    # (from each pixel of the drawing to where the reference has it: on a
    # coarse grid, then smoothly between)
    # (not by her brows' landmarks: on her clay MediaPipe can only guess
    # them, and her reference's brows are kept as they are, carried by the
    # landmarks round them)
    use = np.setdiff1d(np.arange(len(pts["drawn"])), BROW_A + BROW_B)
    # (the warp's own points: from the drawing to the reference; `src` stays the reference's picture)
    p_from, p_to = pts["drawn"][use], pts["ref"][use]
    # Her brows pinned toward where the reference has them against each eye (in eye widths from the middle of its
    # corners, the orbit's own measure): carried only by the landmarks round them, they were pulled down with the eye,
    # every face's brows a quarter to a third nearer its eyes than its portrait's. Pinned with them, by the same
    # measure, the forehead just over them and the lid's crease under them (MediaPipe's guesses on her clay too):
    # the brows pinned alone were pulled up against those guessed points and the reference's brows folded into
    # vertical streaks (Sunborn's, stretched twelve to twenty-five times over a band). FACE_BROW_PIN is how far, from
    # where the clay has them (0, as before: the brows left out) to the reference's place (1).
    pin = float(os.environ.get("FACE_BROW_PIN", "1"))
    if pin > 0:
        zone, at = brow_zone(pts["drawn"], pts["ref"], pin)
        keep = np.setdiff1d(use, zone)
        p_from, p_to = np.vstack([pts["drawn"][keep], at]), np.vstack([pts["ref"][keep], pts["ref"][zone]])
        brows = np.isin(zone, BROW_A + BROW_B)
        print("BROWS pinned %.2f of the way to the reference's place over each eye, with %d landmarks round them: %.1f px "
              "up (mean)" % (pin, len(zone) - brows.sum(), -(at[brows] - pts["drawn"][zone[brows]])[:, 1].mean()))
    tps = RBFInterpolator(p_from, p_to, kernel="thin_plate_spline", smoothing=2.0)
    step = 8
    gy, gx = np.mgrid[0:DRAW:step, 0:DRAW:step]
    g = tps(np.c_[gx.ravel(), gy.ravel()].astype(float)).reshape(gx.shape + (2,))
    fx = ndimage.zoom(g[..., 0], step, order=1)[:DRAW, :DRAW]
    fy = ndimage.zoom(g[..., 1], step, order=1)[:DRAW, :DRAW]
    a = np.asarray(src, np.float32)
    out = np.stack([ndimage.map_coordinates(a[..., k], [np.clip(fy, 0, sh - 1), np.clip(fx, 0, sw - 1)], order=1) for k in range(3)], 2)
    dst = os.path.join(OUT, "painted_front.png")
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst)
    # Her skin's fine grain: the photograph, warped to her, is a little soft
    # at her head's size (a face 600 pixels across laid over 1500 texels), and
    # she read airbrushed. Krea paints it over lightly at full size, and only
    # its finest detail (pores, freckles, the grain of skin) is added back:
    # every colour and feature stays the photograph's.
    if float(os.environ.get("FACE_DETAIL", "0.3")) > 0:
        Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(os.path.join(OUT, "drawn_detail.png"))
        g = paint_graph("detail", os.path.join(OUT, "drawn_detail.png"), DETAIL_PROMPT, float(os.environ.get("FACE_DETAIL", "0.3")))
        got = comfy.run(g, OUT)
        kre = np.asarray(Image.open(got[0]).convert("RGB").resize((DRAW, DRAW), Image.LANCZOS), np.float32)
        os.replace(got[0], os.path.join(OUT, "painted_detail.png"))
        fine = kre - np.stack([ndimage.gaussian_filter(kre[..., k], 2.5) for k in range(3)], 2)
        lum = fine @ np.array([0.3, 0.59, 0.11])
        out = out + np.clip(lum, -40, 40)[..., None] * 0.9 + (fine - lum[..., None]) * 0.4
        print("DETAIL from Krea over the reference: fine grain %.1f levels (rms)" % np.sqrt((lum ** 2).mean()))
    # Her brows' hairs drawn crisper (an unsharp mask over them only, found
    # in the reference by its landmarks and warped as it was): laid on her
    # head at her head's size they read as a soft smudge at the Look's close-up.
    from PIL import ImageDraw
    bm = Image.new("L", (sw, sh), 0)
    bd = ImageDraw.Draw(bm)
    for ring in (BROW_A, BROW_B):
        q = pts["ref"][ring]
        c = q.mean(0)
        bd.polygon([tuple(v) for v in c + (q - c) * np.array([1.25, 1.9])], fill=255)
    bm = ndimage.gaussian_filter(np.asarray(bm, np.float32) / 255, 6)
    bmask = ndimage.map_coordinates(bm, [np.clip(fy, 0, sh - 1), np.clip(fx, 0, sw - 1)], order=1)[..., None]
    soft = np.stack([ndimage.gaussian_filter(out[..., k], 1.6) for k in range(3)], 2)
    out = out + (out - soft) * 1.1 * bmask
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst)
    err = np.linalg.norm(tps(pts["drawn"]) - pts["ref"], axis=1)
    print("REFERENCE laid on the front drawing: %d landmarks, %.1f px off (rms)" % (len(err), np.sqrt((err ** 2).mean())))
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


def delit_reference():
    """The reference, laid on the front, without the light it was taken in,
    its own colours kept (its brows, lips, blush and freckles: delit() would
    put the drawing's broad colour, MakeHuman's brows and all, under it).
    Her head's shape is the reference's now, so its light can be read off
    her normals: its lightness fitted as a light from one side plus an even
    one (first-order spherical harmonics) over her plain skin, and divided out."""
    import json

    from PIL import Image, ImageDraw
    paint = load(os.path.join(OUT, "painted_front.png"))
    nrm = np.asarray(Image.open(os.path.join(OUT, "normals_front.png")).convert("RGB"), np.float32)[::-1] / 255
    nrm = np.where(nrm <= 0.04045, nrm / 12.92, ((nrm + 0.055) / 1.055) ** 2.4)      # (written as sRGB)
    n = nrm * 2 - 1
    on = np.linalg.norm(n, axis=2) > 0.7
    n /= np.linalg.norm(n, axis=2)[..., None] + 1e-6
    # (her plain skin: not her eyes, brows, nostrils or lips, nor her hair)
    L = np.array(json.load(open(os.path.join(OUT, "marks_drawn.json")))["points"])
    feat = Image.new("L", (DRAW, DRAW), 0)
    d = ImageDraw.Draw(feat)
    for ring, grow in ((EYE_RING_A, 1.6), (EYE_RING_B, 1.6), (BROW_A, 1.4), (BROW_B, 1.4), (LIP_RING, 1.25), (NOSTRILS, 1.5)):
        p = L[ring]
        c = p.mean(0)
        d.polygon([tuple(q) for q in c + (p - c) * grow], fill=255)
    top = L[10, 1] + 0.15 * (L[152, 1] - L[10, 1])            # (well below where her hair may begin)
    feat = np.asarray(feat)[::-1] > 0
    rows = np.arange(DRAW)[::-1][:, None] * np.ones((1, DRAW))
    skin = on & ~feat & (rows > top) & (rows < L[152, 1])
    lum = paint @ np.array([0.3, 0.59, 0.11])
    A = np.c_[np.ones(skin.sum()), n[skin]]
    keep = np.ones(skin.sum(), bool)
    for _ in range(4):
        coef = np.linalg.lstsq(A[keep], lum[skin][keep], rcond=None)[0]
        r = lum[skin] - A @ coef
        keep = np.abs(r) < 2.0 * r[keep].std()
    S = coef[0] + n @ coef[1:]
    # (taken out only in part: a beauty dish's light is softer than a single
    # light's falls off, and divided out whole her face's edges glowed; and
    # a little of its modelling kept reads as her shape, not as a stain)
    S = np.clip(S / np.median(S[skin]), 0.55, 1.6) ** 0.45
    print("REFERENCE'S LIGHT: even %.3f, from %s; its shading %.2f to %.2f over her skin" % (
        coef[0], np.round(coef[1:] / (np.linalg.norm(coef[1:]) + 1e-9), 2), np.percentile(S[skin], 2), np.percentile(S[skin], 98)))
    out = np.where(on[..., None], paint / S[..., None], paint)
    # (and its shine taken off her skin: a highlight is the light's, not her
    # skin's colour, and on a cheekbone it showed in the game as a pale smudge)
    from scipy import ndimage as _nd
    local = np.stack([_nd.gaussian_filter(out[..., k], DRAW / 200) for k in range(3)], 2)
    cap = local * 1.06
    shine = on & ~feat & (rows > top)
    out = np.where(shine[..., None] & (out > cap), cap + (out - cap) * 0.2, out)
    from PIL import Image as _I
    _I.fromarray((np.clip(out[::-1], 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, "delit_front.png"))
    return np.clip(out, 0, 1)


# MediaPipe's landmarks of a face's parts (its face mesh's numbers): her
# eyes' rims, her brows, her lips' outline, about her nostrils.
EYE_RING_A = [33, 246, 161, 160, 159, 158, 157, 173, 133, 155, 154, 153, 145, 144, 163, 7]
EYE_RING_B = [263, 466, 388, 387, 386, 385, 384, 398, 362, 382, 381, 380, 374, 373, 390, 249]
BROW_A = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
BROW_B = [300, 293, 334, 296, 336, 285, 295, 282, 283, 276]
LIP_RING = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 375, 321, 405, 314, 17, 84, 181, 91, 146]
NOSTRILS = [98, 64, 48, 115, 220, 45, 4, 275, 440, 344, 278, 294, 327, 2]


BROW_EDGES = {  # (lower edge, upper edge), each from the outer end to the inner (MediaPipe's numbers)
    "A": ([46, 53, 52, 65, 55], [70, 63, 105, 66, 107]),
    "B": ([276, 283, 282, 295, 285], [300, 293, 334, 296, 336]),
}


def brow_zone(drawn, ref, frac):
    """Each eye's brow and the landmarks round it (the lid's crease under it, the temple past its tail, the
    forehead over it), and where they go on the drawing: the brow `frac` of the way from where MediaPipe has it on
    the clay to where the reference has it against that eye (its frame: the middle of its corners, along them, and
    its width), its neighbours carried with it. Rows from the top, as MediaPipe gives them.
    FACE_BROW_SMOOTH=1: round 1's split (one quadratic over brow and neighbours, shares by height); 0: point by point."""
    mode = os.environ.get("FACE_BROW_SMOOTH", "2")
    if mode != "2":
        return brow_zone_v1(drawn, ref, frac, smooth=mode != "0")
    # (10 October, round 2's judge, on Doe and Sunborn at 1.0: three faults in round 1's split. (a) Its share was
    # by height across the whole brow, and a tail lies low everywhere, so tails moved at the lower share and drooped
    # 0.15 to 0.2 eye widths under the portraits'; now each landmark's share is by where it sits between the
    # brow's own lower and upper edges at that point along it. (b) The forehead over the brow stayed put, so the
    # brow's top was squeezed under it (1.8 to 3.6 times; Sunborn's 104 flipped over 103), which made the dip; now
    # the forehead moves with the brow's top, easing to nothing two eye widths over it. (c) One straight fit
    # across brow and neighbours under-moved the brow and over-moved the crease (peaking the lid); now the brow is
    # fitted alone along its length (a cubic), and the crease to its own goals.)
    low = float(os.environ.get("FACE_BROW_LOW", "0.65"))
    # (how far over the brow's top the forehead moves, in eye widths: at 1.0 the first gap over the brow was still
    # squeezed 1.3 times on the saved landmarks; at 2.0 it is the portrait's (0.92 to 1.11) and the rest is spread
    # over the bare forehead, 0.72 to 0.9)
    over = float(os.environ.get("FACE_BROW_OVER", "2.0"))

    def frame(P, c0, c1):
        o = (P[c0] + P[c1]) / 2
        e1 = P[c1] - P[c0]
        w = np.linalg.norm(e1)
        e1 = e1 / w
        return o, e1, np.array([e1[1], -e1[0]]) * (1 if e1[0] > 0 else -1), w       # (e2 up her face)

    def smoothstep(a, b, x):
        t = np.clip((x - a) / (b - a), 0, 1)
        return t * t * (3 - 2 * t)
    acc, wsum = {}, {}

    def add(js, mv):
        for j, m in zip(js, mv):
            acc[j] = acc.get(j, 0) + m
            wsum[j] = wsum.get(j, 0) + 1
    for side, ring, (c0, c1) in (("A", BROW_A, (33, 133)), ("B", BROW_B, (263, 362))):
        lo_ids, up_ids = BROW_EDGES[side]
        o_r, e1_r, e2_r, w_r = frame(ref, c0, c1)
        o_d, e1_d, e2_d, w_d = frame(drawn, c0, c1)
        uv = np.c_[(ref - o_r) @ e1_r / w_r, (ref - o_r) @ e2_r / w_r]

        def goal(js):
            return o_d + w_d * (uv[js, :1] * e1_d + uv[js, 1:] * e2_d)

        def edge(ids, u):
            k = np.argsort(uv[ids, 0])
            return np.interp(u, uv[ids, 0][k], uv[ids, 1][k])
        span = uv[ring, 0]
        u0, u1 = span.min(), span.max()                # (u runs from the outer corner (c0) to the inner)
        # The brow: its own goals, one smooth cubic along it (and linear across it), each landmark's share by
        # where it sits between the brow's own lower and upper edges there.
        jb = np.array(ring)
        u, v = uv[jb, 0], uv[jb, 1]
        A = np.c_[np.ones_like(u), u, u * u, u ** 3, v]
        coef, *_ = np.linalg.lstsq(A, goal(jb) - drawn[jb], rcond=None)

        def brow_move(uq, vq):
            uq = np.clip(uq, u0, u1)
            return np.c_[np.ones_like(uq), uq, uq * uq, uq ** 3, vq] @ coef

        def share(uq, vq):
            lo, up = edge(lo_ids, uq), edge(up_ids, uq)
            return np.clip((vq - lo) / np.maximum(up - lo, 1e-3), 0, 1)
        add(jb, brow_move(u, v) * (frac * (low + (1 - low) * share(u, v)))[:, None])
        # Its neighbours: from the crease (0.42 eye widths over the eye's middle) to `over` above the brow's top,
        # from 0.4 past its tail to 0.15 past its inner end, eased out past its ends.
        lo_all, up_all = edge(lo_ids, uv[:, 0]), edge(up_ids, uv[:, 0])
        near = np.where((uv[:, 1] > 0.42) & (uv[:, 1] < up_all + over) & (uv[:, 0] > u0 - 0.4) & (uv[:, 0] < u1 + 0.15))[0]
        near = np.array([j for j in near if j not in ring], int)
        if not len(near):
            continue
        un, vn = uv[near, 0], uv[near, 1]
        out_by = np.where(un < u0, (u0 - un) / 0.4, np.where(un > u1, (un - u1) / 0.15, 0.0))
        ease_u = 1 - smoothstep(0, 1, out_by)
        below, above = vn < lo_all[near], vn > up_all[near]
        mid = ~below & ~above
        # (the crease under it to its own goals, fitted alone, at the lower share: about half the brow's move)
        if below.any():
            jc = near[below]
            mc = goal(jc) - drawn[jc]
            if len(jc) >= 6:
                Ac = np.c_[np.ones(len(jc)), un[below], un[below] ** 2, vn[below]]
                cc, *_ = np.linalg.lstsq(Ac, mc, rcond=None)
                mc = Ac @ cc
            add(jc, mc * (frac * low * ease_u[below])[:, None])
        # (past its ends at the brow's own height: as the brow's end moves, by their place across it)
        if mid.any():
            jm = near[mid]
            add(jm, brow_move(un[mid], vn[mid]) * (frac * (low + (1 - low) * share(un[mid], vn[mid])) * ease_u[mid])[:, None])
        # (the forehead over it: as the brow's top moves there, easing to nothing `over` above it)
        if above.any():
            ja = near[above]
            ease_v = 1 - smoothstep(0, over, vn[above] - up_all[ja])
            add(ja, brow_move(un[above], up_all[ja]) * (frac * ease_v * ease_u[above])[:, None])
    zone = np.array(sorted(acc))
    at = np.array([drawn[j] + acc[j] / wsum[j] for j in zone])
    return zone, at


def brow_zone_v1(drawn, ref, frac, smooth=True):
    """Each eye's brow and the landmarks round it (from just over the lid's crease to a little over the brow's top,
    across the brow's length), and where they go on the drawing: `frac` of the way from where MediaPipe has them on
    the clay to where the reference has them against that eye (its frame: the middle of its corners, along them, and
    its width). Rows from the top, as MediaPipe gives them."""
    def frame(P, c0, c1):
        o = (P[c0] + P[c1]) / 2
        e1 = P[c1] - P[c0]
        w = np.linalg.norm(e1)
        e1 = e1 / w
        return o, e1, np.array([e1[1], -e1[0]]) * (1 if e1[0] > 0 else -1), w       # (e2 up her face)
    # (10 October, a judge on Sunborn at 1.0: point by point, the pin kinked her brow (a dip at its inner end, a hump
    # at the arch) and left a muddy ghost band under it, and every pinned brow smeared grey past its tail. So each
    # eye's move is one smooth curve along the brow (a quadratic in u, and linear in v, fitted to every point's own
    # move), the brow's upper edge pinned harder than its lower (FACE_BROW_LOW of `frac` at and under its lower edge,
    # all of it at and over its top: the brow grows to the portrait's thickness rather than the whole band sliding up
    # and stretching the lid), and the zone reaches out over the temple past the tail, so the tail is carried, not
    # torn from the skin beside it. FACE_BROW_SMOOTH=0 for the old point-by-point move.)
    low = float(os.environ.get("FACE_BROW_LOW", "0.65"))
    zone, at = [], []
    for ring, (c0, c1) in ((BROW_A, (33, 133)), (BROW_B, (263, 362))):
        o_r, e1_r, e2_r, w_r = frame(ref, c0, c1)
        o_d, e1_d, e2_d, w_d = frame(drawn, c0, c1)
        uv = np.c_[(ref - o_r) @ e1_r / w_r, (ref - o_r) @ e2_r / w_r]
        top, bot, span = uv[ring, 1].max(), uv[ring, 1].min(), uv[ring, 0]
        # (u runs from the outer corner (c0) to the inner: the temple is u below the brow's span)
        out_reach = 0.4 if smooth else 0.15
        near = np.where((uv[:, 1] > 0.42) & (uv[:, 1] < top + 0.32) & (uv[:, 0] > span.min() - out_reach) & (uv[:, 0] < span.max() + 0.15))[0]
        js = [j for j in sorted(set(near) | set(ring)) if j not in zone]   # (one place for a landmark both eyes' zones reach)
        if not js:
            continue
        js = np.array(js)
        goal = o_d + w_d * (uv[js, :1] * e1_d + uv[js, 1:] * e2_d)
        move = goal - drawn[js]
        if smooth and len(js) >= 6:
            u, v = uv[js, 0], uv[js, 1]
            A = np.c_[np.ones_like(u), u, u * u, v]
            coef, *_ = np.linalg.lstsq(A, move, rcond=None)
            move = A @ coef
        if smooth:
            f = frac * (low + (1 - low) * np.clip((uv[js, 1] - bot) / max(top - bot, 1e-3), 0, 1))
        else:
            f = np.full(len(js), frac)
        zone += list(js)
        at += list(drawn[js] + f[:, None] * move)
    return np.array(zone), np.array(at)


def front_hair(img):
    """Where the reference laid on the front shows its own hair or backdrop over her temples and forehead (rows from
    the bottom, as load() gives them), 0 to 1, feathered: not skin-coloured (by linear chromaticity against its
    cheeks') or much darker than its skin, from its brows' level up and beside its eyes' outer corners down to its mouth, never its
    brows or eyes. Laid there, its hairline's edge and the strays over her temple took the tint and turned blue-grey
    (brows round 2's judge). Saved as hair_front.png. None if no face is found on the front."""
    import json

    from PIL import Image, ImageDraw
    from scipy import ndimage
    js = os.path.join(OUT, "marks_front.json")
    if not os.path.exists(js):
        return None
    L = np.array(json.load(open(js))["points"])[:, :2]
    h = img.shape[0]
    c = _lin(np.clip(img, 0, 1))
    ch = c / np.maximum(c.sum(2, keepdims=True), 1e-6)
    y = c @ np.array([0.2126, 0.7152, 0.0722])
    # (its cheeks' skin: a box under each eye)
    ys, xs = np.mgrid[0:h, 0:img.shape[1]]
    yy = h - 1 - ys                                                   # (rows from the top, as the landmarks)
    box = np.zeros(y.shape, bool)
    for a, b in ((50, 205), (280, 425)):
        q0, q1 = np.minimum(L[a], L[b]), np.maximum(L[a], L[b])
        box |= (xs >= q0[0]) & (xs <= q1[0]) & (yy >= q0[1]) & (yy <= q1[1])
    if box.sum() < 50:
        return None
    d = np.linalg.norm(ch - np.median(ch[box], 0), axis=2)
    ym = np.median(y[box])
    # (hair: much darker than its skin, or not skin-coloured and no lighter than it (a sheen is lighter, and
    # is skin); the backdrop: off its head (normals_front.png))
    hairy = (y < 0.35 * ym) | ((d > 0.1) & (y < 0.8 * ym))
    nf = os.path.join(OUT, "normals_front.png")
    if os.path.exists(nf):
        n = np.asarray(Image.open(nf).convert("RGB").resize((img.shape[1], h)), np.float32)[::-1] / 255 * 2 - 1
        hairy |= np.linalg.norm(n, axis=2) < 0.5
    # (only over her temples and forehead: from its brows' lower edge up, and beside its eyes' outer corners)
    brow_y = min(L[BROW_A][:, 1].max(), L[BROW_B][:, 1].max())
    ew = np.linalg.norm(L[133] - L[33])
    side = (xs < min(L[33, 0], L[263, 0]) - 0.25 * ew) | (xs > max(L[33, 0], L[263, 0]) + 0.25 * ew)
    region = (yy < brow_y) | (side & (yy < L[13, 1]))
    m = Image.new("L", (img.shape[1], h), 0)
    dr = ImageDraw.Draw(m)
    # (each brow's outline swept about, more up than down: its sparse top hairs are the brow's, not her hair;
    # scaled about its middle instead, an arched brow's outline folded and left the brow itself out)
    for ring in (BROW_A, BROW_B):
        p = L[ring]
        bw, bh = np.ptp(p[:, 0]), np.ptp(p[:, 1])
        for dx in np.linspace(-0.12, 0.12, 5) * bw:
            for dy in np.linspace(-1.0, 0.5, 9) * bh:
                dr.polygon([tuple(v) for v in p + np.array([dx, dy])], fill=255)
    for ring in (EYE_RING_A, EYE_RING_B):
        p = L[ring]
        cc = p.mean(0)
        dr.polygon([tuple(v) for v in cc + (p - cc) * np.array([1.5, 2.4])], fill=255)
    keep_out = (np.asarray(m) > 0)[::-1]
    hm = (hairy & region & ~keep_out).astype(np.float32)
    # (no specks: a freckle or a pore is not hair)
    hm = ndimage.gaussian_filter(hm, h / 250)
    hm = np.clip((hm - 0.35) / 0.3, 0, 1)
    hm = np.clip(ndimage.gaussian_filter(hm, h / 150) * 1.4, 0, 1)
    Image.fromarray((hm[::-1] * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, "hair_front.png"))
    print("FRONT HAIR: the photograph's hair and backdrop kept off %.1f%% of the front" % (100 * (hm > 0.5).mean()))
    return hm


def front_features():
    """Where the reference laid on the front has its features (its brows, its eyes with their lids and lashes, its
    lips), in the front's pixels (rows from the bottom, as load() gives them), 0 to 1, soft at the edge. There the
    front is laid alone: blended with the sides' paintings (Krea's, of another day, its brows MakeHuman's cards
    painted higher), every face's brows came out at half their portrait's darkness and thin, a faint second brow
    above them, and its lips thinner. The brows' outline grown well up, over where the sides painted theirs.
    (FACE_FRONT_FEATURES=0: blended as before.) None if no face is found on the front."""
    import json
    import subprocess

    from PIL import Image, ImageDraw
    from scipy import ndimage
    js = os.path.join(OUT, "marks_front.json")
    if not os.path.exists(js):
        py = os.path.join(os.environ.get("LOCALAPPDATA", ""), "facefit", ".venv", "Scripts", "python.exe")
        fit = os.path.join(os.path.dirname(os.path.abspath(__file__)), "face_fit.py")
        subprocess.run([py, fit, "marks", os.path.join(OUT, "painted_front.png"), js, "whole"], capture_output=True)
    if not os.path.exists(js):
        print("FRONT FEATURES: no face found on the front; blended as before")
        return None
    L = np.array(json.load(open(js))["points"])
    m = Image.new("L", (DRAW, DRAW), 0)
    d = ImageDraw.Draw(m)
    # (each outline grown about its middle, across and up-down, and lifted by a share of its height: up is -y here)
    # (the brows' grown down as well as up: the sides' paintings have theirs lower, where MakeHuman's are)
    for ring, gx, gy, lift in ((BROW_A, 1.25, 3.4, 0.2), (BROW_B, 1.25, 3.4, 0.2), (EYE_RING_A, 1.3, 2.2, 0.2),
                               (EYE_RING_B, 1.3, 2.2, 0.2), (LIP_RING, 1.12, 1.35, 0.0)):
        p = L[ring]
        c = p.mean(0)
        q = c + (p - c) * np.array([gx, gy])
        q[:, 1] -= lift * (p[:, 1].max() - p[:, 1].min())
        d.polygon([tuple(v) for v in q], fill=255)
    f = ndimage.gaussian_filter(np.asarray(m, np.float32) / 255, DRAW / 300)
    print("FRONT FEATURES: brows, eyes and lips from the reference alone, %.1f%% of the front" % (100 * (f > 0.5).mean()))
    return np.clip(f * 1.5, 0, 1)[::-1]


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


def under_jaw(V, N, T, tri, bary, eye_z):
    """Her neck under her jaw and her jaw's underside, 0 to 1 a texel (eased over a few mm): what no painting of a
    face should lay its colour on. The portraits' necks there are in their jaws' shadow; laid on her, that shadow
    showed as a grey-violet patch with a stepped edge down the front and sides of her neck on every face (the owner,
    10 October 2026), a second shadow under the one the game casts. (The lay's own cut below her chin missed it: its
    chin, the lowest point turned forward down her middle, was her neck's.)
      - Her neck: below her jaw's line as her head is drawn from the front (its outline's lower half,
        marks_drawn.json beside the drawings, found as front_features finds the front's; FACE_JAW_MARKS another),
        from 2 mm over the line to 4 mm under it; beyond the angles of her jaw, below their height.
      - Her jaw's underside: turned down, below her mouth's corners, off her lips and her chin's middle (the chin's
        own cut is the lay's).
    None of her is cut if no face is found on the drawing."""
    import json
    import subprocess
    me = head.data
    js = os.environ.get("FACE_JAW_MARKS") or os.path.join(OUT, "marks_drawn.json")
    if not os.path.exists(js):
        py = os.path.join(os.environ.get("LOCALAPPDATA", ""), "facefit", ".venv", "Scripts", "python.exe")
        fit = os.path.join(os.path.dirname(os.path.abspath(__file__)), "face_fit.py")
        subprocess.run([py, fit, "marks", os.path.join(OUT, "drawn_front.png"), js, "whole"], capture_output=True)
    if not os.path.exists(js):
        print("UNDER JAW: no face found on the drawing; nothing cut")
        return np.zeros(len(tri))
    L = np.array(json.load(open(js))["points"])[:, :2]
    line = L[JAW_LINE]
    line = line[np.argsort(line[:, 0])]
    # (her points as the front drawing has them: across, and down from its top, in its pixels)
    d = V - np.array(CENTRE)
    px = (0.5 + d[:, 0] / SCALE) * DRAW
    py = (0.5 - d[:, 2] / SCALE) * DRAW
    below = (py - np.interp(px, line[:, 0], line[:, 1])) * SCALE / DRAW          # (metres under her jaw's line)
    def ramp(x, a, b):
        return np.clip((x - a) / (b - a), 0, 1)
    neck = ramp(below, -0.002, 0.004)
    jaw = ramp(-N[:, 2], 0.3, 0.6) * ramp(eye_z - 0.06 - V[:, 2], 0, 0.01) * ramp(np.abs(V[:, 0]), 0.025, 0.035)
    cut = np.maximum(neck, jaw)
    # (eased over a ring or two of her points: not a stepped edge)
    nv = len(V)
    e = np.array([(f[k], f[(k + 1) % len(f)]) for f in (list(p.vertices) for p in me.polygons) for k in range(len(f))])
    import scipy.sparse as _sp
    adj = _sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(nv, nv)).tocsr()
    adj = ((adj + adj.T) > 0).astype(float)
    A = _sp.diags(1 / np.maximum(np.asarray(adj.sum(1)).ravel(), 1)) @ adj
    for _ in range(int(os.environ.get("FACE_JAW_EASE", "3"))):
        cut = 0.5 * cut + 0.5 * (A @ cut)
    print("UNDER JAW: %d of her points under her jaw's line, %d on its underside" % ((neck > 0.5).sum(), (jaw > 0.5).sum()))
    return (cut[T[tri]] * bary).sum(1)


def match(src, ref, m):
    """src's colouring made ref's, over the texels m."""
    ms, ss = src[m].mean(0), src[m].std(0) + 1e-6
    mr, sr = ref[m].mean(0), ref[m].std(0) + 1e-6
    return mr + (src - ms) * np.clip(sr / ss, 0.8, 1.25)


def _lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((np.maximum(c, 0) + 0.055) / 1.055) ** 2.4)


def _srgb(c):
    c = np.maximum(c, 0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def skin_like(col, m):
    """How like her skin each texel's colour is (1 to 0), by its linear chromaticity against the median of the
    texels m, and dark texels (hair) less so."""
    c = _lin(np.clip(col, 0, 1))
    ch = c / np.maximum(c.sum(1, keepdims=True), 1e-6)
    d = np.linalg.norm(ch - np.median(ch[m], 0), axis=1)
    y = c @ np.array([0.2126, 0.7152, 0.0722])
    ym = np.median(y[m])
    return (1 - np.clip((d - 0.06) / 0.08, 0, 1)) * np.clip((y / ym - 0.15) / 0.25, 0, 1)


def tint_to(src, ref, m, like=None):
    """src's skin brought to ref's colour over the texels m, as a light or a skin's pigment would: each channel scaled
    in linear light, so every feature keeps its depth against the skin round it. (match() moved its mean by adding
    and squeezed its spread toward her plain head's: a face's brows came out half their portrait's darkness against
    its skin, and its lips half as red.) (FACE_MATCH=add: as match() did.)
    (10 October, brows round 2's judge: the per-channel gains (Sunborn's x1.93/3.15/4.60) turned every grey or black
    texel the photograph laid on her temple (its hair's edge, sparse tail hairs, its studio sheen) blue-grey or
    lavender, and the gains differed lay to lay (the texels fitted on were picked by colour, from the colours being
    fitted). So the gains are fitted on m's middle 80% of light (no sheen, no shadow) as medians, and with `like`
    (skin_like), only skin-like texels take the colour shift; the rest take the light's gain alone.)"""
    if os.environ.get("FACE_MATCH") == "add":
        return match(src, ref, m)
    ls, lr = _lin(src[m]), _lin(ref[m])
    w = np.array([0.2126, 0.7152, 0.0722])
    y = ls @ w
    mid = (y > np.percentile(y, 10)) & (y < np.percentile(y, 90))
    g = np.median(lr[mid], 0) / np.maximum(np.median(ls[mid], 0), 1e-6)
    gy = float(np.median(lr[mid] @ w) / max(np.median(y[mid]), 1e-6))
    print("TINTED to her skin: x %.3f %.3f %.3f (linear), light alone x %.3f, over %d texels" % (*g, gy, mid.sum()))
    if like is None:
        return _srgb(_lin(src) * g)
    return _srgb(_lin(src) * (gy + like[:, None] * (g - gy)))


def free():
    """The shared GPU given back (the server answers with nothing). (No server running, as in a run that painted
    nothing with Krea: nothing to give back.)"""
    import json
    import urllib.error
    import urllib.request
    req = urllib.request.Request(comfy.URL + "/free", data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10).read()
    except (urllib.error.URLError, OSError):
        print("FREE: no ComfyUI to free")


if __name__ == "__main__" and os.environ.get("FACE_JAW_ONLY"):
    # (FACE_JAW_ONLY=1: nothing painted; under_jaw's cut written to <out>/jaw_cut.png and her head's own skin, with
    # the texels her head covers as its alpha, to <out>/base_skin.png, both as the face paint lies (rows from the
    # top): tools/assets/heroine_jaw_cut.py takes the paint off a built head with them, without building her again.
    # With FACE_JAW_HEAD (that head's paint) also what her own skin is brought by where the paint comes off:
    # <out>/jaw_field.npz, as matched_base in heroine_head.py brings it, a smooth field over her head's points,
    # held to the head's paint where nothing is cut and to her body's skin (nothing added) over the 6 mm above
    # SPLIT, eased between (over her points, so across her texture's seams as on her))
    from PIL import Image
    import scipy.sparse as _sp
    import scipy.sparse.linalg as _spl
    if not os.environ.get("FACE_JAW_MARKS") and not os.path.exists(os.path.join(OUT, "marks_drawn.json")) \
            and not os.path.exists(os.path.join(OUT, "drawn_front.png")):
        draw()                                   # (her jaw's line is found on the front drawing)
    rows, cols, T, tri, bary, V, N, P, Nt = texels()
    eye_z = float(np.mean([(bpy.data.objects["HeroineEyes"].matrix_world @ v.co).z
                           for v in bpy.data.objects["HeroineEyes"].data.vertices]))
    ct = under_jaw(V, N, T, tri, bary, eye_z)
    jc = np.zeros((SIZE, SIZE), np.float32)
    jc[rows, cols] = ct
    Image.fromarray((jc[::-1] * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, "jaw_cut.png"))
    bs = SKIN_AS_IS.copy() if SKIN_AS_IS is not None else \
        np.array(head.data.materials[0].node_tree.nodes["Image Texture"].image.pixels[:], np.float32).reshape(SIZE, SIZE, 4)
    bs[..., 3] = 0
    bs[rows, cols, 3] = 1
    Image.fromarray((np.clip(bs[::-1], 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, "base_skin.png"))
    if os.environ.get("FACE_JAW_HEAD"):
        # (her neck where the paint comes off: one smooth colour field over her head's points, held to the head's
        # paint (its broad colour) where nothing is cut and to her body's own skin (its broad colour, as her body's
        # texture has it a little under SPLIT) along her head's edge at SPLIT, eased between. Her head's own skin was
        # tried first, brought by a field as matched_base brings it: MakeHuman's skin is greyer than hers and
        # mauve under her jaw, and heroine_head.py's easing into her body at her neck had left lighter lobes along
        # SPLIT; the game's pores and grain give her neck its fine detail.)
        from scipy.spatial import cKDTree
        hd = np.asarray(Image.open(os.environ["FACE_JAW_HEAD"]).convert("RGB"), np.float32)[::-1] / 255
        nv = len(V)
        tv = T[tri]

        def to_points(vals, w):
            acc = np.zeros((nv, vals.shape[1]))
            ws = np.zeros(nv)
            for k in range(3):
                wk = bary[:, k] * w
                ws += np.bincount(tv[:, k], wk, nv)
                for ch in range(vals.shape[1]):
                    acc[:, ch] += np.bincount(tv[:, k], vals[:, ch] * wk, nv)
            return acc / np.maximum(ws, 1e-9)[:, None], ws
        col_v, wk = to_points(hd[rows, cols], (ct < 0.02).astype(float))
        cut_v, _ = to_points(ct[:, None], np.ones(len(ct)))
        e = np.array([(f[k], f[(k + 1) % len(f)]) for f in (list(p.vertices) for p in head.data.polygons) for k in range(len(f))])
        adj = _sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(nv, nv)).tocsr()
        adj = ((adj + adj.T) > 0).astype(float)
        lap = (_sp.diags(np.asarray(adj.sum(1)).ravel()) - adj).tocsr()

        def split(p):
            return 1.625 + 0.27 * (p[:, 1] + 0.02)
        seam = V[:, 2] - split(V) < 0.006
        known = (wk > 0.3) & (cut_v[:, 0] < 0.02) & ~seam
        # (the paint's broad colour: its freckles and pores not carried in)
        Am = _sp.diags(1 / np.maximum(np.asarray(adj.sum(1)).ravel(), 1)) @ adj
        for _ in range(10):
            col_v = np.where(known[:, None], (Am @ np.where(known[:, None], col_v, 0)) / np.maximum(Am @ known.astype(float), 1e-6)[:, None], col_v)
        # (her body's skin under her neck's edge: her body's faces there, each sampled at its corners and middle)
        body = bpy.data.objects["Heroine"]
        BV, _ = as_shaped(body)
        bme = body.data
        uvb = bme.uv_layers.active.data
        pix = {}
        pts, cs = [], []
        for p in bme.polygons:
            vs = list(p.vertices)
            cen = BV[vs].mean(0)
            s = cen[2] - (1.625 + 0.27 * (cen[1] + 0.02))
            if not (-0.04 < s < -0.002) or abs(cen[0]) > 0.14:
                continue
            mat = body.material_slots[p.material_index].material if p.material_index < len(body.material_slots) else None
            img = next((n.image for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image), None) if mat and mat.use_nodes else None
            if img is None:
                continue
            if img.name not in pix:
                w_, h_ = img.size
                pix[img.name] = np.array(img.pixels[:], np.float32).reshape(h_, w_, 4)
            px_ = pix[img.name]
            uvs = np.array([uvb[li].uv[:] for li in p.loop_indices])
            for q, u in list(zip(BV[vs], uvs)) + [(cen, uvs.mean(0))]:
                x = int(np.clip((u[0] % 1.0) * px_.shape[1], 0, px_.shape[1] - 1))
                y = int(np.clip((u[1] % 1.0) * px_.shape[0], 0, px_.shape[0] - 1))
                pts.append(q)
                cs.append(px_[y, x, :3])
        pts, cs = np.array(pts), np.array(cs)
        tree = cKDTree(pts)
        si = np.where(seam)[0]
        body_c = np.zeros((len(si), 3))
        for n, i in enumerate(si):
            near = tree.query_ball_point(V[i] - np.array([0, 0, 0.006]), 0.015)
            if near:
                d2 = ((pts[near] - (V[i] - np.array([0, 0, 0.006]))) ** 2).sum(1)
                w_ = np.exp(-d2 / (2 * 0.007 ** 2))
                body_c[n] = (cs[near] * w_[:, None]).sum(0) / w_.sum()
            else:
                body_c[n] = col_v[i]
        val = col_v.copy()
        val[si] = body_c
        fixed = known | seam
        fr, fx = np.where(~fixed)[0], np.where(fixed)[0]
        rhs = -lap[fr][:, fx] @ val[fx]
        A = (lap[fr][:, fr] + 1e-6 * _sp.identity(len(fr))).tocsc()
        out_v = val.copy()
        for ch in range(3):
            out_v[fr, ch] = _spl.spsolve(A, rhs[:, ch])
        f_t = (out_v[tv] * bary[:, :, None]).sum(1)
        m = ct > 0.001
        np.savez_compressed(os.path.join(OUT, "jaw_field.npz"), rows=(SIZE - 1 - rows[m]).astype(np.int16),
                            cols=cols[m].astype(np.int16), colour=np.clip(f_t[m], 0, 1).astype(np.float32))
        print("JAW FIELD: %d of her points held to the paint, %d to her body at SPLIT (%d samples of it, mean %s), %d eased" % (
            known.sum(), seam.sum(), len(pts), np.round(body_c.mean(0) * 255).astype(int), len(fr)))
    print("JAW CUT written", OUT)
elif __name__ == "__main__":
    # (FACE_LAY_ONLY=1: the drawings and paintings already in <out>, say the
    # best view of each of several seeds gathered there, only laid back on)
    if not os.environ.get("FACE_LAY_ONLY"):
        draw()
        try:
            for name in VIEWS:
                if name == "front" and os.environ.get("FACE_REF"):
                    from_reference(os.environ["FACE_REF"])
                elif os.environ.get("FACE_REUSE") and os.path.exists(os.path.join(OUT, f"painted_{name}.png")):
                    continue                     # (FACE_REUSE=1: a view already painted in <out> kept)
                else:
                    paint(name)
                print("PAINTED", name)
        finally:
            free()
    rows, cols, T, tri, bary, V, N, P, Nt = texels()
    base = SKIN_AS_IS if SKIN_AS_IS is not None else \
        np.array(head.data.materials[0].node_tree.nodes["Image Texture"].image.pixels[:], np.float32).reshape(SIZE, SIZE, 4)
    # Each view laid back as two: its broad colour (light, blush, the
    # tone of her skin), blended among the views that see a place; and its
    # fine detail (pores, freckles, the grain of her skin, finer than
    # DETAIL_MM), taken from the one view that sees it most squarely. Blended
    # as one, her front's grain was averaged half and half with the sides'
    # over her cheeks (paintings of another day, their freckles not hers:
    # each dimmed the other), and her paint held half the grain of the
    # photograph laid on her front.
    from scipy import ndimage as _ndi
    _sg = float(os.environ.get("FACE_DETAIL_MM", "1.6")) / 1000 * DRAW / SCALE
    cols_v, fine_v, weights = {}, {}, {}
    feat_img = front_features() if os.environ.get("FACE_REF") and os.environ.get("FACE_FRONT_FEATURES", "1") != "0" else None
    feat = None
    for name, ang in VIEWS.items():
        a = math.radians(ang)
        fwd = np.array([-math.sin(a), math.cos(a), 0.0])
        right = np.array([math.cos(a), math.sin(a), 0.0])
        d = P - np.array(CENTRE)
        uv = np.stack([0.5 + (d @ right) / SCALE, 0.5 + d[:, 2] / SCALE], 1)
        vis = seen(V, N, -fwd)[T[tri]]
        # (eased in over a triangle as its points come into view, not all or
        # nothing a triangle at a time: that stepped the paint's edges, as a
        # pale stair under her jaw)
        vis = np.clip(((vis * bary).sum(1) - 0.6) / 0.4, 0, 1)
        facing = np.clip(Nt @ -fwd, 0, 1)
        edge = np.clip(np.minimum.reduce([uv[:, 0], 1 - uv[:, 0], uv[:, 1], 1 - uv[:, 1]]) / 0.05, 0, 1)
        weights[name] = facing ** 4 * edge * vis * (1.0 if name == "front" else 0.8)
        if name == "front" and os.environ.get("FACE_REF"):
            # (her reference over all it sees well, its sides too: Krea's
            # sides, painted another day, gave her redder lips and heavier
            # freckles seen from three-quarters)
            weights[name] = facing ** 1.5 * edge * vis * 1.5
            if feat_img is not None:
                # (its features where the front sees them at all)
                feat = sample(feat_img[..., None], uv)[:, 0] * np.clip((vis - 0.5) / 0.5, 0, 1) * np.clip((facing - 0.15) / 0.2, 0, 1)
        ref_front = name == "front" and os.path.exists(os.path.join(OUT, "normals_front.png")) and os.environ.get("FACE_REF")
        img = delit_reference() if ref_front else delit(name)
        if ref_front and os.environ.get("FACE_HAIR_MASK", "1") != "0":
            # (the photograph's own hair and backdrop not laid on her: front_hair())
            hm = front_hair(img)
            if hm is not None:
                weights[name] = weights[name] * (1 - sample(hm[..., None], uv)[:, 0])
        broad = np.stack([_ndi.gaussian_filter(img[..., k], _sg) for k in range(3)], 2)
        cols_v[name] = sample(broad, uv)
        fine_v[name] = sample(img - broad, uv)
        if os.environ.get("FACE_DEBUG") and name == "front":
            # (the front alone, laid as it is: view_front_uv.png)
            from PIL import Image as _Im
            _v = np.zeros((SIZE, SIZE, 3), np.float32)
            _v[rows, cols] = np.clip(sample(img, uv), 0, 1)
            _Im.fromarray((_v[::-1] * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, "view_front_uv.png"))
        print("LAID", name, "%d texels seen" % (weights[name] > 0.05).sum())
    # The sides coloured as the front where both see her well.
    for name in ("left", "right"):
        both = (weights["front"] > 0.3) & (weights[name] > 0.3)
        if both.sum() > 500:
            cols_v[name] = match(cols_v[name], cols_v["front"], both)
    if feat is not None:
        # (the reference's features from it alone: front_features)
        for name in ("left", "right"):
            weights[name] = weights[name] * (1 - feat)
        # (and where they lie on her head, in her head's UV: features_uv.png beside the paint)
        from PIL import Image as _Im
        _fu = np.zeros((SIZE, SIZE), np.float32)
        _fu[rows, cols] = feat
        _Im.fromarray((_fu[::-1] * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, "features_uv.png"))
    wsum = sum(weights.values())
    col = sum(cols_v[n] * weights[n][:, None] for n in VIEWS) / np.maximum(wsum, 1e-6)[:, None]
    # (the detail's weights sharpened: where two views see a place almost as
    # squarely, still eased from one to the other, not cut)
    wf = {n: weights[n] ** 6 for n in VIEWS}
    wfs = sum(wf.values())
    fine = sum(fine_v[n] * wf[n][:, None] for n in VIEWS) / np.maximum(wfs, 1e-12)[:, None]
    fine *= np.clip(wsum / 0.25, 0, 1)[:, None]
    cover = np.clip(wsum / 0.25, 0, 1)
    # Her face only: none of it over her scalp, faded out from just under
    # her hairline (face_shapes.HAIRLINE) to 6 mm over it, where her hair
    # lies (a painting of a bald head can paint hair there, swept back, and
    # it showed at her temples; her reference's own hair is its colour, not
    # the one she is dyed: her scalp is darkened to that in the game).
    eye_z = float(np.mean([(bpy.data.objects["HeroineEyes"].matrix_world @ v.co).z
                           for v in bpy.data.objects["HeroineEyes"].data.vertices]))
    theta = np.arctan2(P[:, 0], -P[:, 1])
    up = P[:, 2] - (eye_z + fs.hairline_height(theta))
    cover *= 1 - np.clip((up + 0.002) / 0.008, 0, 1)
    # Nor under her jaw and down her neck: the paintings' necks, lighter
    # than her body's, showed as a pale patch between her jaw and her
    # collar; there her head's own skin (her body's colouring) is kept.
    front_mid = (np.abs(P[:, 0]) < 0.012) & (Nt[:, 1] < -0.6)
    chin_z = P[front_mid, 2].min() if front_mid.any() else eye_z - 0.11
    below_mouth = np.clip((eye_z - 0.095 - P[:, 2]) / 0.01, 0, 1)            # (her chin and below: not her lips' undersides)
    # (nor her jaw's underside, from as soon as it turns down: the paintings lit
    # it, and it showed pale under her jaw; her head's own skin there is brought
    # to her face's colour and her body's by heroine_head.py)
    cover *= 1 - below_mouth * np.clip((-Nt[:, 2] - 0.05) / 0.3, 0, 1)
    cover *= 1 - np.clip((chin_z + 0.003 - P[:, 2]) / 0.012, 0, 1)
    # (nor her neck under her jaw at its sides, nor her jaw's underside: under_jaw; FACE_JAW_CUT=0 as before)
    if os.environ.get("FACE_JAW_CUT", "1") != "0":
        cover *= 1 - under_jaw(V, N, T, tri, bary, eye_z)
    # And all of it coloured as her skin (her head's own, which heroine_head.py
    # matched to her body), over her cheeks, brow and neck seen square on.
    # (the texels it is fitted on by where they are, not picked by a tight colour window from the colours being
    # fitted: all her painted face but her features, then only those near the median colour (a mole, a lash out))
    feat_t = feat if feat is not None else np.zeros(len(col))
    # (all her painted face, as before, so its edge meets her head's own skin: fitted on her cheeks alone, the
    # front's lighter skin set the gains and her face's edge stood 1.3 to 1.6% off her head's against 0.7%)
    place = (cover > 0.9) & (feat_t < 0.05)
    skin = place & (np.abs(col - np.median(col[place], 0)).max(1) < 0.12)
    # (broad colour to broad colour: her head's own skin as broad as the views' is, about 12 texels to their 1.6 mm)
    base_b = np.stack([_ndi.gaussian_filter(base[..., k], 12) for k in range(3)], 2)
    col = tint_to(col, base_b[rows, cols], skin, skin_like(col, skin) if os.environ.get("FACE_TINT_SKIN", "1") != "0" else None)
    # Her fine detail over it as the views have it (FACE_DETAIL_GAIN: a little
    # more, for what the game's filtering and light under her skin smooth away).
    col = col + fine * float(os.environ.get("FACE_DETAIL_GAIN", "1.0"))
    out = np.zeros((SIZE, SIZE, 4), np.float32)
    out[rows, cols, :3] = np.clip(col, 0, 1)
    out[rows, cols, 3] = cover
    from PIL import Image
    Image.fromarray((out[::-1] * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, "face_paint.png"))
    print("FACE PAINT", os.path.join(OUT, "face_paint.png"), "%d%% of her head painted" % (100 * (cover > 0.5).mean()))
