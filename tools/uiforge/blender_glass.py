"""Her life's glass and the draught's (docs/design/HUD_V2.md 3, "Her life (the left glass)", "The draught"),
rendered in Blender Cycles in the house light (blender_frames' world and suns, the iron kit's camera and
scale: 2x files, 3x supersampled) and filed as the layers the vessel shader (shaders/hud_vessel.gdshader)
composites:

  hud/glass_liquid[_small].png  the view through the glass at N fill levels, an atlas of opaque frames
                                (frame 0 the empty glass: its inner wall, the far side's reflection of the
                                window, the lit wall band; the last frame full): real blood behind thick glass,
                                its surface seen from a little above (an ellipse 8% of its chord) with its
                                meniscus. No reflection off the outer surface (that is the front).
  hud/glass_front[_small].png   the outer surface's own light: the arched window, the hot spot, the rim's
                                reflections of the cuff (rgb, added in linear light); alpha the cuff's shadow on
                                the glass (for what the shader draws on it: film, frost).
  hud/glass_lines[_small].png   per frame and per file column, where its surface is (the far edge, the
                                meniscus, 16 bit in R and G; the near edge in B), so the shader can slide the
                                two frames either side of any level onto one surface and blend them.
  hud/glass_film.png            the hurt film's map: R the time each place clears (a sheet with a ragged front,
                                5 to 8 tapered, wavering rivulets with beaded tips), G its thickness, B the dried
                                film of the empty glass.
  hud/glass_frost[_small].png   the shield's frost: R its whiteness, G the order it grows in (round from the top
                                and in from the rim), B its crystals' cells (the crack), A its cover.

The glass is a ball of thick old glass (a shell: outer radius ro, wall `wall`) held in the cuff (the iron
band of blender_irons, invisible to the camera but casting its shadow and seen in the glass's rim); the
blood is a volume (emission and absorption: lit as the spec says, light entering at the upper left and
leaving at the lower right) whose free surface is a refracting skin with a meniscus climbing the wall; the
wet wall is a glass-to-blood interface, the dry wall glass to air (so its rim shows the thick glass's ring).

    blender -b -P tools/uiforge/blender_glass.py -- tools/uiforge/glass.json OUTDIR [big] [small] [--test] [--levels 0,0.55,1]
    python tools/uiforge/blender_glass.py [--render] [--test] [big] [small]     (renders under no turn: take one)
"""
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
RAW = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "glass", "raw")
HUD = os.path.join(ROOT, "godot", "art", "ui", "hud")
SPEC = json.load(open(os.path.join(HERE, "glass.json"), encoding="utf-8"))

try:
    import bpy  # noqa: F401
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False


# =============================================================================================== Blender ==
if IN_BLENDER:
    import bmesh  # noqa: F401
    from mathutils import Vector
    import blender_frames as B
    import blender_irons as I
    import blender_chainline as C

    class Graph:
        """Node-building shorthand: numbers and tuples become default values, sockets are linked."""

        def __init__(self, nt):
            self.nt = nt

        def node(self, kind, **kw):
            n = self.nt.nodes.new(kind)
            for k, v in kw.items():
                setattr(n, k, v)
            return n

        def put(self, sock, v):
            if hasattr(v, "is_linked") or hasattr(v, "links"):
                self.nt.links.new(v, sock)
            else:
                sock.default_value = v

        def m(self, op, a, b=None, clamp=False):
            n = self.node("ShaderNodeMath", operation=op, use_clamp=clamp)
            self.put(n.inputs[0], a)
            if b is not None:
                self.put(n.inputs[1], b)
            return n.outputs[0]

        def v(self, op, a, b=None, scale=None):
            n = self.node("ShaderNodeVectorMath", operation=op)
            self.put(n.inputs[0], a)
            if b is not None:
                self.put(n.inputs[1], b)
            if scale is not None:
                self.put(n.inputs["Scale"], scale)
            return n.outputs["Value"] if op in ("DOT_PRODUCT", "LENGTH", "DISTANCE") else n.outputs[0]

        def smooth(self, x, a, b):
            n = self.node("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP")
            self.put(n.inputs["Value"], x)
            n.inputs["From Min"].default_value = a
            n.inputs["From Max"].default_value = b
            return n.outputs["Result"]

        def mix(self, fac, a, b):
            n = self.node("ShaderNodeMixShader")
            self.put(n.inputs[0], fac)
            self.nt.links.new(a, n.inputs[1])
            self.nt.links.new(b, n.inputs[2])
            return n.outputs[0]

        def add(self, a, b):
            n = self.node("ShaderNodeAddShader")
            self.nt.links.new(a, n.inputs[0])
            self.nt.links.new(b, n.inputs[1])
            return n.outputs[0]

        def bsdf(self, kind, **inputs):
            n = self.node(kind)
            for k, v in inputs.items():
                self.put(n.inputs[k], v)
            return n.outputs[0]

    def new_mat(name):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        return m, Graph(nt), out

    def black(g):
        return g.bsdf("ShaderNodeEmission", Color=(0, 0, 0, 1), Strength=0.0)

    def shadow_pass(g, sh):
        """Fake caustics: shadow rays go straight through the glass and the blood's skin."""
        lp = g.node("ShaderNodeLightPath")
        return g.mix(lp.outputs["Is Shadow Ray"], sh, g.bsdf("ShaderNodeBsdfTransparent"))

    def glass_volume(g):
        gs = SPEC["glass"]
        if gs["scatter"] <= 0:
            return None
        return g.bsdf("ShaderNodeVolumeScatter", Color=(1, 0.98, 0.95, 1), Density=gs["scatter"] / K, Anisotropy=gs["scatter_aniso"])

    def outer_material(mode):
        """The ball's outer surface. through: only what it lets in (refraction times 1 - F); front: only
        what it reflects (F times a mirror); mask: refraction only. Rays already inside the glass see it
        as whole glass."""
        gs = SPEC["glass"]
        m, g, out = new_mat("outer_" + mode)
        tint = tuple(gs["tint"]) + (1,)
        lp = g.node("ShaderNodeLightPath")
        first = g.m("LESS_THAN", lp.outputs["Ray Depth"], 0.5)
        fr = g.node("ShaderNodeFresnel")
        fr.inputs["IOR"].default_value = gs["ior"]
        refr = g.bsdf("ShaderNodeBsdfRefraction", Color=tint, Roughness=0.0, IOR=gs["ior"])
        whole = g.bsdf("ShaderNodeBsdfGlass", Color=tint, Roughness=0.0, IOR=gs["ior"])
        if mode == "through":
            sh = g.mix(first, whole, g.mix(fr.outputs[0], refr, black(g)))
        elif mode == "front":
            mirror = g.bsdf("ShaderNodeBsdfGlossy", Color=(1, 1, 1, 1), Roughness=0.0)
            sh = g.mix(first, whole, g.mix(fr.outputs[0], black(g), mirror))
        else:
            sh = refr
        g.nt.links.new(shadow_pass(g, sh), out.inputs["Surface"])
        if mode != "mask":
            vol = glass_volume(g)
            if vol is not None:
                g.nt.links.new(vol, out.inputs["Volume"])
        return m

    def inner_material(wet, mode):
        """The cavity's wall: glass to air (dry) or glass to blood (wet, IOR 1.5 / 1.35)."""
        gs = SPEC["glass"]
        ior = gs["ior"] if not wet else gs["ior"] / 1.35
        m, g, out = new_mat(("wet_" if wet else "dry_") + mode)
        tint = tuple(gs["tint"]) + (1,)
        if mode == "mask":
            sh = g.bsdf("ShaderNodeBsdfRefraction", Color=(1, 1, 1, 1), Roughness=0.0, IOR=ior)
        else:
            sh = g.bsdf("ShaderNodeBsdfGlass", Color=tint, Roughness=0.0, IOR=ior)
        g.nt.links.new(shadow_pass(g, sh), out.inputs["Surface"])
        if mode != "mask":
            vol = glass_volume(g)
            if vol is not None:
                g.nt.links.new(vol, out.inputs["Volume"])
        return m

    def blood_volume(g, bs, ri, h):
        """The blood's light, as the spec has it: its body one red, at most ~27% darker toward the upper
        left, lighter just under its surface, the light that entered at the upper left leaving at the lower
        right as a glow and a rim of the brightest red; seen through `absorb` per px of it."""
        tc = g.node("ShaderNodeTexCoord")
        q = g.v("SCALE", tc.outputs["Object"], scale=1.0 / K)
        r = g.v("LENGTH", q)
        n = (0.0, math.cos(TILT), math.sin(TILT))
        dep = g.m("MAXIMUM", g.m("SUBTRACT", h, g.v("DOT_PRODUCT", q, n)), 0.0)
        near = g.m("EXPONENT", g.m("MULTIPLY", dep, -1.0 / 6.0))
        qxy = g.v("MULTIPLY", q, (1.0, 1.0, 0.0))
        ul = g.m("MINIMUM", g.m("MAXIMUM", g.m("DIVIDE", g.v("DOT_PRODUCT", qxy, (-0.7071, 0.7071, 0.0)), ri), 0.0), 1.0)
        ga = Vector(bs["glow_at"]).normalized() * (ri * 0.92)
        d = g.m("DIVIDE", g.v("DISTANCE", q, tuple(ga)), bs["glow_r"] * ri)
        glow = g.m("EXPONENT", g.m("MULTIPLY", g.m("POWER", d, 2.0), -1.0))
        lr = g.m("POWER", g.m("MAXIMUM", g.v("DOT_PRODUCT", g.v("NORMALIZE", qxy), (0.7071, -0.7071, 0.0)), 0.0), 2.0)
        rimb = g.m("MULTIPLY", g.smooth(g.v("LENGTH", qxy), ri - 9.0, ri - 0.6), lr)       # (seen edge-on: the silhouette's)
        nz = g.node("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 0.055
        nz.inputs["Detail"].default_value = 2.0
        nz.inputs["Roughness"].default_value = 0.5
        g.nt.links.new(q, nz.inputs["Vector"])
        body_k = g.m("MULTIPLY", g.m("ADD", g.m("MULTIPLY", near, bs["near"]), 1.0), g.m("SUBTRACT", 1.0, g.m("MULTIPLY", ul, bs["ul"])))
        body_k = g.m("MULTIPLY", body_k, g.m("ADD", 1.0, g.m("MULTIPLY", g.m("SUBTRACT", nz.outputs["Fac"], 0.5), 2 * bs["noise"])))
        rim_k = g.m("ADD", g.m("MULTIPLY", glow, bs["glow"]), g.m("MULTIPLY", rimb, bs["rimband"]))
        body_c = B.hexc(bs["body"])[:3]
        rim_c = B.hexc(bs["rim"])[:3]
        col = g.v("ADD", g.v("SCALE", body_c, scale=body_k), g.v("SCALE", rim_c, scale=rim_k))
        sig = bs["absorb"] / K
        em = g.node("ShaderNodeEmission")
        g.nt.links.new(col, em.inputs["Color"])
        em.inputs["Strength"].default_value = sig
        ab = g.bsdf("ShaderNodeVolumeAbsorption", Color=(0, 0, 0, 1), Density=sig)
        return g.add(em.outputs[0], ab)

    def blood_materials(bs, ri, h, mode):
        """[the wall-contact skin (only a volume boundary), the free surface (a refracting skin)]."""
        mats = []
        for part in ("contact", "free"):
            m, g, out = new_mat(f"blood_{part}_{mode}")
            if mode == "mask":
                c = (0, 1, 0, 1) if part == "contact" else (1, 0, 0, 1)
                g.nt.links.new(g.bsdf("ShaderNodeEmission", Color=c, Strength=1.0), out.inputs["Surface"])
            else:
                if part == "contact":
                    sh = g.bsdf("ShaderNodeBsdfTransparent")
                else:
                    sh = shadow_pass(g, g.bsdf("ShaderNodeBsdfGlass", Color=(1, 1, 1, 1), Roughness=bs["surface_rough"], IOR=1.35))
                g.nt.links.new(sh, out.inputs["Surface"])
                g.nt.links.new(blood_volume(g, bs, ri, h), out.inputs["Volume"])
            mats.append(m)
        return mats

    # ------------------------------------------------------------------------------------- geometry --
    def basis(a):
        a = Vector(a).normalized()
        t = Vector((1, 0, 0)) if abs(a.x) < 0.9 else Vector((0, 1, 0))
        u = (t - a * t.dot(a)).normalized()
        return u, a.cross(u), a

    def sphere_rows(R, axis, thetas, nseg):
        """Vertex rows of a sphere of radius R about `axis` at polar angles `thetas` (from +axis)."""
        u, v, a = basis(axis)
        rows = []
        for th in thetas:
            st, ct = math.sin(th), math.cos(th)
            rows.append([(u * math.cos(2 * math.pi * j / nseg) + v * math.sin(2 * math.pi * j / nseg)) * (R * st) + a * (R * ct) for j in range(nseg)])
        return rows

    def grid_faces(verts, rows, nseg, outward, mat, faces, mats):
        """Append rows of vertices (ring by ring from the +axis pole) and their quads, facing out of the
        sphere (or into it)."""
        base = len(verts)
        for row in rows:
            verts.extend(row)
        for i in range(len(rows) - 1):
            for j in range(nseg):
                a, b = base + i * nseg + j, base + i * nseg + (j + 1) % nseg
                c, d = base + (i + 1) * nseg + (j + 1) % nseg, base + (i + 1) * nseg + j
                f = (a, b, c, d)                         # (this winding faces into the sphere)
                faces.append(f[::-1] if outward else f)
                mats.append(mat(i) if callable(mat) else mat)
        return base

    def cap(verts, faces, mats, ring0, nseg, centre, at_top, outward, mat):
        """Close a ring with a fan to its pole (the fan's winding faces out at the top pole)."""
        ci = len(verts)
        verts.append(centre)
        for j in range(nseg):
            f = (ring0 + j, ring0 + (j + 1) % nseg, ci)
            faces.append(f[::-1] if at_top != outward else f)
            mats.append(mat)

    def make_object(name, verts, faces, mats, materials, loc):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(p) for p in verts], [], faces)
        me.update()
        for mt in materials:
            me.materials.append(mt)
        me.polygons.foreach_set("material_index", mats)
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        if LIT is not None:
            LIT.objects.link(ob)                 # (the hot spot's light falls on the glass and the blood alone)
        ob.location = loc
        return ob

    def thetas_with(n, extra=()):
        ts = sorted(set([math.pi * i / n for i in range(n + 1)] + [t for t in extra if 0 < t < math.pi]))
        return ts

    def shell(piece, h, wet_mode):
        """The glass: outer ball and the cavity's wall in one object (one volume), the wall wet below the
        blood's top (h + meniscus along the surface's normal) and dry above."""
        ps = SPEC[piece]
        ro, ri = ps["ro"] * K, (ps["ro"] - ps["wall"]) * K
        n = (0.0, math.cos(TILT), math.sin(TILT))
        verts, faces, mats = [], [], []
        # the outer ball, its poles at 3 and 9 o'clock (under the cuff)
        nseg = 512 if piece == "big" else 256
        nth = 256 if piece == "big" else 128
        rows = sphere_rows(ro, (1, 0, 0), [math.pi * (i + 0.5) / nth for i in range(nth)], nseg)
        b0 = grid_faces(verts, rows, nseg, True, 0, faces, mats)
        cap(verts, faces, mats, b0, nseg, Vector((ro, 0, 0)), True, True, 0)
        cap(verts, faces, mats, b0 + (nth - 1) * nseg, nseg, Vector((-ro, 0, 0)), False, True, 0)
        # the cavity, about the surface's normal, with a row exactly at the wet line
        if h is None:
            tw = None
        else:
            top = (h + SPEC["meniscus"]["height"]) / (ps["ro"] - ps["wall"])
            tw = math.acos(max(-1.0, min(1.0, top))) if -1 < top < 1 else (0.0 if top >= 1 else math.pi)
        ths = thetas_with(nth, [tw] if tw is not None else [])
        ths = [min(max(t, 1e-4), math.pi - 1e-4) for t in ths]
        rows = sphere_rows(ri, n, ths, nseg)

        def wet(i):
            if tw is None:
                return 1
            return 2 if 0.5 * (ths[i] + ths[i + 1]) > tw else 1
        b1 = grid_faces(verts, rows, nseg, False, wet, faces, mats)       # (the cavity's wall faces its middle)
        nv = Vector(n)
        cap(verts, faces, mats, b1, nseg, nv * ri, True, False, 2 if (tw is not None and tw <= 1e-3) else 1)
        cap(verts, faces, mats, b1 + (len(rows) - 1) * nseg, nseg, -nv * ri, False, False, 2 if tw is not None else 1)
        mt = [MATS["outer_" + wet_mode], MATS["dry_" + ("mask" if wet_mode == "mask" else "render")],
              MATS["wet_" + ("mask" if wet_mode == "mask" else "render")]]
        return make_object("shell", verts, faces, mats, mt, Vector((0, 0, ps["zc"] * K)))

    def blood_mesh(piece, h, materials):
        """The blood up to the plane n.q = h, its free surface rising `meniscus` px to meet the wall."""
        ps = SPEC[piece]
        rl = ps["ro"] - ps["wall"] - ps["gap"]
        M, lam = SPEC["meniscus"]["height"], SPEC["meniscus"]["reach"]
        n = Vector((0.0, math.cos(TILT), math.sin(TILT)))
        u, v, _ = basis(n)
        nseg = 512 if piece == "big" else 256
        nth = 256 if piece == "big" else 128
        verts, faces, mats = [], [], []
        full = h + M >= rl
        if full:
            ths = [math.pi * (i + 0.5) / nth for i in range(nth)]
            rows = sphere_rows(rl * K, n, ths, nseg)
            b = grid_faces(verts, rows, nseg, True, 0, faces, mats)
            cap(verts, faces, mats, b, nseg, n * (rl * K), True, True, 0)
            cap(verts, faces, mats, b + (nth - 1) * nseg, nseg, -n * (rl * K), False, True, 0)
        else:
            tl = math.acos((h + M) / rl)
            ths = [tl + (math.pi - tl) * i / nth for i in range(nth)]
            rows = sphere_rows(rl * K, n, ths, nseg)
            b = grid_faces(verts, rows, nseg, True, 0, faces, mats)
            cap(verts, faces, mats, b + (nth - 1) * nseg, nseg, -n * (rl * K), False, True, 0)
            # the free surface: rings from the wall in, dense where the meniscus climbs
            wM = math.sqrt(max(rl * rl - (h + M) ** 2, 1e-6))
            rad = [wM - 4.0 * i / 40 for i in range(1, 41) if wM - 4.0 * i / 40 > 0]
            last = rad[-1] if rad else wM
            rad += [last * (1 - i / 24) for i in range(1, 24)]
            srows = []
            for rr in rad:
                z = M * math.exp(-(wM - rr) / lam)
                srows.append([(u * math.cos(2 * math.pi * j / nseg) + v * math.sin(2 * math.pi * j / nseg)) * (rr * K) + n * ((h + z) * K)
                              for j in range(nseg)])
            # join the surface's first ring to the contact cap's top ring (shared vertices: row b)
            s0 = len(verts)
            for row in srows:
                verts.extend(row)
            for j in range(nseg):
                a, bb = b + j, b + (j + 1) % nseg
                c, d = s0 + (j + 1) % nseg, s0 + j
                faces.append((a, d, c, bb))
                mats.append(1)
            for i in range(len(srows) - 1):
                for j in range(nseg):
                    a, bb = s0 + i * nseg + j, s0 + i * nseg + (j + 1) % nseg
                    c, d = s0 + (i + 1) * nseg + (j + 1) % nseg, s0 + (i + 1) * nseg + j
                    faces.append((a, d, c, bb))
                    mats.append(1)
            cap(verts, faces, mats, s0 + (len(srows) - 1) * nseg, nseg, n * ((h + M * math.exp(-wM / lam)) * K), True, True, 1)
        ob = make_object("blood", verts, faces, mats, materials, Vector((0, 0, ps["zc"] * K)))
        # outward normals throughout (the mesh is closed)
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(ob.data)
        bm.free()
        ob.data.polygons.foreach_set("use_smooth", [True] * len(ob.data.polygons))
        return ob

    # --------------------------------------------------------------------------------------- scene --
    class Stage:
        def __init__(self, W, S):
            self.W = self.H = W
            self.S = S

        def P(self, x, y, z=0.0):
            return B.P(x * self.S, y * self.S, self.W * self.S, self.H * self.S, z * self.S)

        def add(self, ob, catcher=False):
            return ob

    def world_for_glass():
        """The house world, dimmed for what the glass reflects or lets through (its own light is the window
        and the hot spot; the softbox's reflection was the 'blurred smudge')."""
        B.world()
        irons = I.SPEC.get("light", {})
        nt = bpy.context.scene.world.node_tree
        for nd in nt.nodes:
            if nd.type == "MATH" and nd.operation == "MULTIPLY" and abs(nd.inputs[1].default_value - 2.5) < 1e-6:
                nd.inputs[1].default_value *= irons.get("rim_world", 1.0)
        bg = nt.nodes["Background"]
        src = bg.inputs["Color"].links[0].from_socket
        g = Graph(nt)
        lp = g.node("ShaderNodeLightPath")
        w = SPEC["world"]
        dim = g.m("MAXIMUM", g.m("MULTIPLY", lp.outputs["Is Glossy Ray"], 1 - w["glossy"]),
                  g.m("MULTIPLY", lp.outputs["Is Transmission Ray"], 1 - w["transmission"]))
        k = g.m("SUBTRACT", 1.0, dim)
        sc = g.v("SCALE", src, scale=k)
        nt.links.new(sc, bg.inputs["Color"])

    def window_object():
        """An arched window far up and to the left, seen only in reflections: a tall opening with a round
        head, its edge soft over `soft` of its width."""
        ws = SPEC["window"]
        az, tl = math.radians(ws["azimuth"]), math.radians(ws["tilt"])
        el = 2 * tl  # the reflected direction is twice the normal's tilt from the eye
        d = Vector((math.sin(el) * math.cos(az), math.sin(el) * math.sin(az), math.cos(el)))
        D = 60.0
        hh = 2 * D * math.tan(math.radians(ws["height_deg"]) / 2)
        ww = 2 * D * math.tan(math.radians(ws["width_deg"]) / 2)
        bpy.ops.mesh.primitive_plane_add(size=1)
        ob = bpy.context.active_object
        ob.name = "window"
        ob.scale = (ww, hh, 1)
        ob.location = d * D
        up = Vector((0, 1, 0))
        ob.rotation_euler = (-d).to_track_quat("Z", "Y").to_euler()      # its face toward the glass, its head up
        del up
        # its mask: an arch (UV in 0..1, the head a half circle of the width)
        m, g, out = new_mat("window")
        tc = g.node("ShaderNodeTexCoord")
        sep = g.node("ShaderNodeSeparateXYZ")
        g.nt.links.new(tc.outputs["UV"], sep.inputs[0])
        aspect = hh / ww
        x = g.m("SUBTRACT", sep.outputs[0], 0.5)
        y = g.m("MULTIPLY", sep.outputs[1], aspect)                     # in widths
        yc = aspect - 0.5                                               # the head's centre
        sd_rect = g.m("MAXIMUM", g.m("SUBTRACT", g.m("ABSOLUTE", x), 0.5), g.m("SUBTRACT", 0.0, y))
        sd_head = g.m("SUBTRACT", g.m("SQRT", g.m("ADD", g.m("POWER", x, 2.0), g.m("POWER", g.m("SUBTRACT", y, yc), 2.0))), 0.5)
        above = g.m("GREATER_THAN", y, yc)
        sd = g.m("ADD", g.m("MULTIPLY", above, sd_head), g.m("MULTIPLY", g.m("SUBTRACT", 1.0, above), sd_rect))
        mask = g.smooth(g.m("MULTIPLY", sd, -1.0), -ws["soft"] * 0.5, ws["soft"] * 0.5)
        head = g.m("ADD", 0.78, g.m("MULTIPLY", g.m("DIVIDE", y, aspect), 0.22))   # brighter at its head
        em = g.node("ShaderNodeEmission")
        em.inputs["Color"].default_value = B.hexc(ws["color"])
        g.put(em.inputs["Strength"], g.m("MULTIPLY", g.m("MULTIPLY", mask, head), ws["strength"]))
        g.nt.links.new(g.mix(mask, g.bsdf("ShaderNodeBsdfTransparent"), em.outputs[0]), out.inputs["Surface"])
        ob.data.materials.append(m)
        ob.visible_camera = False
        ob.visible_diffuse = False
        ob.visible_shadow = False
        ob.visible_volume_scatter = False
        return ob

    def hot_light():
        hs = SPEC["hot"]
        az, tl = math.radians(hs["azimuth"]), math.radians(hs["tilt"])
        el = 2 * tl
        d = Vector((math.sin(el) * math.cos(az), math.sin(el) * math.sin(az), math.cos(el)))
        ld = bpy.data.lights.new("hot", "SUN")
        ld.energy = hs["strength"]
        ld.angle = math.radians(hs["angle"])
        ld.color = (1.0, 0.97, 0.92)
        ob = bpy.data.objects.new("hot", ld)
        bpy.context.scene.collection.objects.link(ob)
        ob.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        ob.visible_diffuse = False
        ob.visible_transmission = False
        ob.visible_volume_scatter = False
        return ob

    def setup(piece, test):
        global K
        ps = SPEC[piece]
        S = 2 if test else SPEC["scale"]
        K = S * B.U
        W = ps["canvas"]
        sc = B.reset()
        sc.cycles.samples = 48 if test else SPEC["samples"]
        sc.cycles.max_bounces = 24
        sc.cycles.transmission_bounces = 24
        sc.cycles.glossy_bounces = 12
        sc.cycles.transparent_max_bounces = 32
        sc.cycles.volume_bounces = 2
        sc.cycles.volume_step_rate = 0.5
        sc.cycles.caustics_reflective = True
        sc.cycles.caustics_refractive = True
        sc.cycles.blur_glossy = 0.0
        sc.cycles.use_denoising = False          # (3x supersampled; a denoiser smears the meniscus)
        sc.render.image_settings.color_depth = "16"
        world_for_glass()
        B.suns()
        for nm in ("key", "fill", "rim"):
            o = bpy.data.objects[nm]
            o.visible_glossy = False
            o.visible_transmission = False
        bpy.data.objects["rim"].data.energy *= I.SPEC.get("light", {}).get("rim_sun", 1.0)
        B.camera(W * S, W * S)
        st = Stage(W, S)
        bs = ps["band"]
        band = I.ring_band(st, "band", W / 2, W / 2, bs["ri"], bs["ro"], bs["crown"], seed=bs["seed"], n=1800 if piece == "big" else 1000)
        I.wear(st, band, ztop=bs["crown"], zw=0.3, seed=1)
        # (only seen in the glass's rim, and casting its shadow on it: dark iron, no bright metal to mirror)
        mi, gi, oi = new_mat("band_dark")
        gi.nt.links.new(gi.bsdf("ShaderNodeBsdfDiffuse", Color=B.hexc("#161314")), oi.inputs["Surface"])
        band.data.materials.append(mi)
        band.visible_camera = False
        # behind the ball: the cuff's dark socket (what an empty glass shows through itself)
        bpy.ops.mesh.primitive_plane_add(size=1)
        back = bpy.context.active_object
        back.name = "back"
        back.scale = (W * 3 * K, W * 3 * K, 1)
        back.location = (0, 0, (ps["zc"] - ps["ro"] - 1.0) * K)
        bd = SPEC["backdrop"]
        mb, gb, ob_ = new_mat("back")
        gb.nt.links.new(gb.bsdf("ShaderNodeBsdfDiffuse", Color=B.hexc(bd["color"])), ob_.inputs["Surface"])
        back.data.materials.append(mb)
        global LIT
        LIT = bpy.data.collections.new("lit_glass")
        sc.collection.children.link(LIT)
        win = window_object()
        hot = hot_light()
        hot.light_linking.receiver_collection = LIT
        for mode in ("through", "front", "mask"):
            MATS["outer_" + mode] = outer_material(mode)
        for mode in ("render", "mask"):
            MATS["dry_" + mode] = inner_material(False, "mask" if mode == "mask" else "render")
            MATS["wet_" + mode] = inner_material(True, "mask" if mode == "mask" else "render")
        return sc, band, back, win, hot

    MATS = {}
    LIT = None
    K = 0.06
    TILT = math.asin(SPEC["tilt"])

    def level_h(piece, L):
        """The plane's height (along its normal) for level L: its centre seen at (2L - 1) of the cavity."""
        ps = SPEC[piece]
        ri = ps["ro"] - ps["wall"]
        return (2 * L - 1) * ri / math.cos(TILT)

    def render_to(sc, path, samples=None):
        if samples:
            sc.cycles.samples = samples
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)

    def run(piece, out, test, levels):
        sc, band, back, win, hot = setup(piece, test)
        ps = SPEC[piece]
        bsp = SPEC[ps["blood"]]
        ri = ps["ro"] - ps["wall"]
        samples = sc.cycles.samples
        msamples = 8 if test else SPEC["mask_samples"]
        N = ps["frames"]
        todo = levels if levels is not None else [k / (N - 1) for k in range(N)]
        # the front: only what the outer surface reflects (and its shadow pass)
        sh = shell(piece, None, "front")
        render_to(sc, os.path.join(out, f"{piece}_front.png"), samples)
        bpy.data.objects.remove(sh)
        # the cuff's shadow on the ball: a white ball under the key alone, with the band and without
        sh = shell(piece, None, "through")
        wm, wg, wo = new_mat("white")
        wg.nt.links.new(wg.bsdf("ShaderNodeBsdfDiffuse", Color=(1, 1, 1, 1)), wo.inputs["Surface"])
        sh.data.materials[0] = wm
        bgs = bpy.context.scene.world.node_tree.nodes["Background"].inputs["Strength"]
        bgs.default_value = 0.0
        hidden = [bpy.data.objects[n] for n in ("fill", "rim")] + [hot, back]
        for o in hidden:
            o.hide_render = True
        render_to(sc, os.path.join(out, f"{piece}_lit_band.png"), 16)
        band.visible_shadow = False
        render_to(sc, os.path.join(out, f"{piece}_lit_free.png"), 16)
        band.visible_shadow = True
        for o in hidden:
            o.hide_render = False
        bgs.default_value = 1.0
        bpy.data.objects.remove(sh)
        # the frames: through the glass at each level, and the mask that says where its surface is
        meta = {"levels": [], "h": []}
        for k, L in enumerate(todo):
            h = None if L <= 0 else level_h(piece, L)
            if h is not None and h + SPEC["meniscus"]["height"] >= ri - ps["gap"]:
                h = ri + 10.0
            for mode in ("render", "mask"):
                sh = shell(piece, h, "through" if mode == "render" else "mask")
                bl = None
                if h is not None:
                    # (a full glass has no surface to be lit under: its light is the body's alone)
                    hs = h + 40.0 if h > ri else h
                    bl = blood_mesh(piece, h, blood_materials(bsp, ri, hs, mode))
                if mode == "mask":
                    win.hide_render = True
                    back.hide_render = True
                    band.hide_render = True
                    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
                    render_to(sc, os.path.join(out, f"{piece}_mask_{k:02d}.png"), msamples)
                    win.hide_render = False
                    back.hide_render = False
                    band.hide_render = False
                    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
                else:
                    render_to(sc, os.path.join(out, f"{piece}_frame_{k:02d}.png"), samples)
                bpy.data.objects.remove(sh)
                if bl is not None:
                    for mt in bl.data.materials:
                        bpy.data.materials.remove(mt)
                    bpy.data.objects.remove(bl)
            meta["levels"].append(L)
            meta["h"].append(h)
        json.dump(meta, open(os.path.join(out, f"{piece}_meta.json"), "w"), indent=1)

    def main():
        argv = sys.argv[sys.argv.index("--") + 1:]
        SPEC.update(json.load(open(argv[0], encoding="utf-8")))
        out = os.path.abspath(argv[1])
        os.makedirs(out, exist_ok=True)
        irons = json.load(open(os.path.join(HERE, "irons.json"), encoding="utf-8"))
        I.SPEC.update(irons)
        C.SPEC.update(irons["material"])
        test = "--test" in argv
        levels = None
        if "--levels" in argv:
            levels = [float(x) for x in argv[argv.index("--levels") + 1].split(",")]
        pieces = [a for a in argv[2:] if a in ("big", "small")] or ["big", "small"]
        for p in pieces:
            run(p, out, test, levels)

    if __name__ == "__main__":
        main()


# ================================================================================================ filing ==
def _lin(c):
    import numpy as np
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _enc(c):
    import numpy as np
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def _load(name):
    """A raw render (16-bit, sRGB-encoded) as linear float RGBA."""
    import cv2
    import numpy as np
    a = cv2.imread(os.path.join(RAW, name + ".png"), cv2.IMREAD_UNCHANGED).astype(np.float32) / 65535
    return np.dstack([_lin(a[..., 2]), _lin(a[..., 1]), _lin(a[..., 0]), a[..., 3]]).astype(np.float32)


def _down(img, size):
    import cv2
    return cv2.resize(img.astype("float32"), (size, size), interpolation=cv2.INTER_AREA)


def _save8(arr, path):
    import numpy as np
    from PIL import Image
    Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(path, optimize=True)
    return path


def _radius(F, canvas):
    """Per pixel of an F-px square over `canvas` shown px: the radius and x, y (shown px, y down) from its middle."""
    import numpy as np
    yy, xx = np.mgrid[0:F, 0:F].astype(np.float32)
    k = F / canvas
    X, Y = (xx + 0.5) / k - canvas / 2, (yy + 0.5) / k - canvas / 2
    return np.hypot(X, Y), X, Y


def _edge(col, thr):
    """The first crossing of `thr` down a column (sub-pixel, in px from the top), or None."""
    import numpy as np
    idx = np.nonzero(col > thr)[0]
    if not len(idx):
        return None
    i = idx[0]
    if i == 0:
        return 0.0
    a, b = col[i - 1], col[i]
    return i - 1 + (thr - a) / max(b - a, 1e-6) + 0.5


def file_piece(piece):
    import numpy as np
    ps = SPEC[piece]
    canvas, R = ps["canvas"], ps["r"]
    ri = ps["ro"] - ps["wall"]
    F = canvas * 2                                     # a frame, file px (2x)
    SS = SPEC["scale"] // 2
    suf = "" if piece == "big" else "_small"
    meta = json.load(open(os.path.join(RAW, f"{piece}_meta.json")))
    N = len(meta["levels"])
    cols = int(math.ceil(math.sqrt(N)))
    rows = int(math.ceil(N / cols))
    atlas = np.zeros((rows * F, cols * F, 4), np.float32)
    lines = np.zeros((N, F, 4), np.float32)
    for k in range(N):
        fr = _down(_load(f"{piece}_frame_{k:02d}"), F)
        y0, x0 = (k // cols) * F, (k % cols) * F
        atlas[y0:y0 + F, x0:x0 + F, :3] = _enc(fr[..., :3])
        atlas[y0:y0 + F, x0:x0 + F, 3] = 1
        # where its surface is, per file column: the far edge (blood of either kind) and the near edge (the
        # blood seen through the front wall); outside the chord, held at its ends
        mk = _load(f"{piece}_mask_{k:02d}")
        mr, mg = _enc(mk[..., 0]), _enc(mk[..., 1])
        L, h = meta["levels"][k], meta["h"][k]
        far, near = np.full(F, np.nan), np.full(F, np.nan)
        if 0 < L < 1 and h is not None and h < ri:
            hh = h * math.cos(math.asin(SPEC["tilt"]))
            half = math.sqrt(max(ri * ri - hh * hh, 0)) * 0.86
            for c in range(F):
                if abs((c + 0.5) / 2 - canvas / 2) > half:
                    continue
                cr = int((c + 0.5) * SS)
                e1 = _edge(mr[:, cr] + mg[:, cr], 0.5)
                e2 = _edge(mg[:, cr], 0.5)
                if e1 is not None:
                    far[c] = e1 / SS
                if e2 is not None:
                    near[c] = e2 / SS
            for arr in (far, near):
                ok = np.nonzero(~np.isnan(arr))[0]
                if len(ok):
                    arr[:ok[0]] = arr[ok[0]]
                    arr[ok[-1] + 1:] = arr[ok[-1]]
        if np.isnan(far).all():
            yv = F / 2 + (ri + 3) * 2 if (L <= 0 or h is None) else F / 2 - (ri + 3) * 2
            far[:] = yv
            near[:] = yv
        near = np.where(np.isnan(near), far, near)
        e = np.clip(np.round(far * 256), 0, 65535).astype(np.int64)
        lines[k, :, 0] = (e >> 8) / 255
        lines[k, :, 1] = (e & 255) / 255
        lines[k, :, 2] = np.clip(np.round(near), 0, 255) / 255
        lines[k, :, 3] = 1
    made = [_save8(atlas, os.path.join(HUD, f"glass_liquid{suf}.png")), _save8(lines, os.path.join(HUD, f"glass_lines{suf}.png"))]
    # the front: the outer surface's light plus the lit wall line at the lower right; alpha the cuff's shadow
    fr = _down(_load(f"{piece}_front"), F)
    lb, lf = _down(_load(f"{piece}_lit_band"), F), _down(_load(f"{piece}_lit_free"), F)
    shade = np.clip(1 - lb[..., 0] / np.maximum(lf[..., 0], 1e-4), 0, 1) * (lf[..., 3] > 0.5)
    rho, X, Y = _radius(F, canvas)
    ws = SPEC["wall_line"]
    ang = np.degrees(np.arctan2(Y, X))                # 0 at 3 o'clock, 90 at 6 (y down)
    da = np.abs((ang - ws["at"] + 180) % 360 - 180)
    along = np.clip(1 - (da / ws["span"]) ** 2, 0, 1) ** 1.5
    sc = max(R / 60, 0.6)
    r0 = R - ws["inset"] * sc
    w = ws["width"] * sc
    band = np.clip((rho - (r0 - w)) * 2, 0, 1) * np.clip((r0 + 0.8 - rho) * 1.2, 0, 1) * (0.55 + 0.45 * np.clip((rho - (r0 - w)) / w, 0, 1))
    light = fr[..., :3] + (ws["strength"] * band * along)[..., None] * np.array(ws["color"], np.float32)
    made.append(_save8(np.dstack([_enc(light), shade]), os.path.join(HUD, f"glass_front{suf}.png")))
    made.append(_save8(frost_map(F, canvas, R, SPEC["seed"] + (0 if piece == "big" else 7)), os.path.join(HUD, f"glass_frost{suf}.png")))
    if piece == "big":
        made.append(_save8(film_map(F, canvas, ri, SPEC["seed"]), os.path.join(HUD, "glass_film.png")))
    return made, {"frames": N, "cols": cols, "rows": rows, "canvas": canvas, "cavity": ri}


def _stroke(img, pts, widths, vals, ss):
    """An anti-aliased tapered stroke (later stamps over earlier) through pts (px of img / ss)."""
    import cv2
    import numpy as np
    for (x0, y0), (x1, y1), w0, w1, v0, v1 in zip(pts[:-1], pts[1:], widths[:-1], widths[1:], vals[:-1], vals[1:]):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) * ss))
        for t in np.linspace(0, 1, n):
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            w, v = w0 + (w1 - w0) * t, v0 + (v1 - v0) * t
            cv2.circle(img, (int(round(x * ss)), int(round(y * ss))), max(1, int(round(w * ss / 2))), float(v), -1, lineType=cv2.LINE_AA)


def film_map(F, canvas, ri, seed):
    """R: when each place of the hurt film clears (0..1 of its run), over (x across the glass, s from the film's
    top (0) down to the blood's surface (1)): a sheet whose top clears first along a ragged front, and seven
    rivulets at irregular places, wavering, tapered toward their tops, beaded at their tips and along them,
    lasting longest; G its thickness (denser toward the blood). B, in the glass's own space: the dried film."""
    import cv2
    import numpy as np
    rng = np.random.default_rng(seed)
    ss = 4
    W = F * ss
    xs = np.linspace(-1, 1, W)
    s = np.linspace(0, 1, W)[:, None]

    def n1(x, f, ph):
        return sum(np.sin(x * f * (1.9 ** i) + ph * (i + 1) * 1.7) / (1.6 ** i) for i in range(4)) / 2.2
    rag = n1(xs, 4.0, rng.uniform(0, 6)) * 0.10 + n1(xs, 19.0, rng.uniform(0, 6)) * 0.035
    T = np.clip(0.04 + s * 0.80 + rag[None, :], 0, 0.9)
    G = np.clip(0.30 + 0.55 * s ** 1.6 + 0.08 * rag[None, :], 0, 1) * np.ones_like(T)
    tr = np.zeros((W, W), np.float32)
    th = np.zeros((W, W), np.float32)
    xsel = np.sort(rng.uniform(-0.78, 0.78, 7))
    for i, x0 in enumerate(xsel):
        top = rng.uniform(0.0, 0.35)
        wmax = rng.uniform(1.1, 2.8) * F / canvas                         # 1 to 3 shown px at the bottom, in file px
        amp, fq, ph = rng.uniform(0.006, 0.02), rng.uniform(5, 11), rng.uniform(0, 6)
        n = 40
        ys = np.linspace(top, 1.0, n)
        px = [((x0 + amp * np.sin(y * fq + ph) + 0.4 * amp * np.sin(y * fq * 2.7 + ph * 2)) + 1) / 2 * F for y in ys]
        py = [y * F for y in ys]
        wd = [max(0.5, wmax * (0.25 + 0.75 * ((y - top) / (1 - top)) ** 0.6)) for y in ys]
        late = rng.uniform(0.86, 0.97)
        tv = [0.40 + (late - 0.40) * ((y - top) / (1 - top)) ** 0.8 for y in ys]
        _stroke(tr, list(zip(px, py)), wd, tv, ss)
        _stroke(th, list(zip(px, py)), wd, [0.75 + 0.25 * (y - top) / (1 - top) for y in ys], ss)
        for b in [0.0] + list(rng.uniform(0.25, 0.8, int(rng.integers(1, 3)))):
            j = int(b * (n - 1))
            br = wd[j] * rng.uniform(1.5, 2.1) / 2 * ss
            cv2.circle(tr, (int(px[j] * ss), int(py[j] * ss)), max(1, int(br)), float(min(0.97, tv[j] + 0.06)), -1, lineType=cv2.LINE_AA)
            cv2.circle(th, (int(px[j] * ss), int(py[j] * ss)), max(1, int(br)), 1.0, -1, lineType=cv2.LINE_AA)
    T = np.maximum(T, tr)
    G = np.maximum(G, th)
    out = np.zeros((F, F, 4), np.float32)
    out[..., 0] = _down(T, F)
    out[..., 1] = _down(G, F)
    rho, X, Y = _radius(F, canvas)
    u, v = X / ri, Y / ri
    nz = cv2.GaussianBlur(rng.random((F, F)).astype(np.float32), (0, 0), F / 40)
    nz = (nz - nz.min()) / (nz.max() - nz.min())
    tide = np.exp(-((v - 0.80 - 0.02 * np.sin(u * 9)) / (1.1 / ri)) ** 2) * (np.abs(u) < 0.58)
    pool = np.clip((v - 0.80) / 0.12, 0, 1) * 0.9
    stain = np.clip((nz - 0.45) / 0.3, 0, 1) * np.clip(v + 0.1, 0, 1) * 0.5
    out[..., 2] = np.clip(np.maximum.reduce([tide * 0.8, pool, stain]), 0, 1) * (rho < ri - 0.5)
    out[..., 3] = 1
    return out


def frost_map(F, canvas, R, seed):
    """The shield's frost in the glass's own space: crystals grown in from the rim (needles with side
    branches at about 60 degrees, each of its own depth, some places bare), and a broken hoar along the rim.
    R its whiteness, G the order it comes in (round from the top), B each crystal's number (its shard when it
    cracks), A its cover."""
    import cv2
    import numpy as np
    rng = np.random.default_rng(seed)
    ss = 4
    k = F / canvas
    W = F * ss
    wh = np.zeros((W, W), np.float32)
    idm = np.zeros((W, W), np.float32)
    c = canvas / 2
    scale = R / 60
    n = int(64 * scale + 10)

    def needle(p, d, L, w, v, lvl, cid):
        q = p + d * L
        _stroke(wh, [tuple(p * k), tuple(q * k)], [w * k, w * k * 0.3], [v, v * 0.7], ss)
        _stroke(idm, [tuple(p * k), tuple(q * k)], [w * k, w * k * 0.3], [cid, cid], ss)
        if lvl < 2:
            for t in np.linspace(0.25, 0.8, int(rng.integers(2, 4))):
                for sgn in (-1, 1):
                    if rng.random() < 0.7:
                        a = sgn * math.radians(rng.uniform(50, 68))
                        rd = np.array([d[0] * math.cos(a) - d[1] * math.sin(a), d[0] * math.sin(a) + d[1] * math.cos(a)])
                        needle(p + d * L * t, rd, L * (1 - t) * rng.uniform(0.35, 0.6), w * 0.7, v * 0.85, lvl + 1, cid)
    for i in range(n):
        a = 2 * math.pi * (i + rng.uniform(-0.35, 0.35)) / n
        if rng.random() < 0.22:
            continue
        depth = rng.uniform(0.35, 1.0)
        L = rng.uniform(5, 17) * scale * (0.5 + 0.5 * depth)
        r0 = R - rng.uniform(0.0, 1.2)
        tl = rng.uniform(-0.45, 0.45)
        d = np.array([-math.cos(a + tl), -math.sin(a + tl)])
        p0 = np.array([c + r0 * math.cos(a), c + r0 * math.sin(a)])
        needle(p0, d, L, rng.uniform(0.7, 1.15) * max(scale, 0.7), depth, 0, rng.uniform(0.05, 1.0))
    rr, X, Y = _radius(W, canvas)
    hn = cv2.GaussianBlur(rng.random((W, W)).astype(np.float32), (0, 0), W / 60)
    hn = (hn - hn.min()) / (hn.max() - hn.min())
    hoar = np.clip((rr - (R - (2.0 + 3.5 * hn))) / 1.2, 0, 1) * (rr < R + 1) * np.clip((hn - 0.3) / 0.25, 0, 1) * (0.35 + 0.35 * hn)
    wh = np.maximum(wh, hoar.astype(np.float32))
    out = np.zeros((F, F, 4), np.float32)
    whd = _down(wh, F)
    out[..., 0] = np.clip(whd * 1.15, 0, 1)
    _, Xf, Yf = _radius(F, canvas)
    order = np.abs(np.arctan2(Xf, -Yf)) / math.pi
    out[..., 1] = np.clip(order + (cv2.GaussianBlur(rng.random((F, F)).astype(np.float32), (0, 0), 2) - 0.5) * 0.04, 0, 1)
    out[..., 2] = _down(idm, F)
    out[..., 3] = np.clip(whd * 1.6, 0, 1)
    return out


def main_file(argv):
    import imports
    if "--render" in argv:
        blender = os.environ.get("BLENDER", r"C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe")
        os.makedirs(RAW, exist_ok=True)
        r = subprocess.run([blender, "-b", "-P", os.path.abspath(__file__), "--", os.path.join(HERE, "glass.json"), RAW]
                           + [a for a in argv if a in ("big", "small", "--test")], capture_output=True, text=True, timeout=7200)
        if "Traceback" in r.stdout + r.stderr:
            raise SystemExit((r.stdout + r.stderr)[-3000:])
    pieces = [a for a in argv if a in ("big", "small")] or ["big", "small"]
    made, info = [], {}
    for p in pieces:
        m, inf = file_piece(p)
        made += m
        info[p] = inf
    imports.write(made)
    for p in made:
        q = p + ".import"
        t = open(q, encoding="utf-8").read().replace("process/fix_alpha_border=true", "process/fix_alpha_border=false")
        if "glass_lines" not in p:
            t = t.replace("mipmaps/generate=false", "mipmaps/generate=true")
        open(q, "w", encoding="utf-8", newline="\n").write(t)
    print(json.dumps(info))


if not IN_BLENDER and __name__ == "__main__":
    main_file(sys.argv[1:])
