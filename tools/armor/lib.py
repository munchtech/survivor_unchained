"""The adornment library (docs/armor/PIECE_SCHEMA.md, "The adornment library").

Builds every library mesh procedurally (no third-party art), life size, metres:
origin at the socket point, local +Z out of the surface it sits on (underside at z=0,
open, so it seats on a plate), +Y up, +X = Y x Z. Exported with Blender's Z-up kept
(export_yup=False), so the glb's axes ARE the socket frame. Unskinned; the build skins
each one to the shell.

  blender -b --python tools/armor/lib.py                 -> godot/art/armor/lib/<id>.glb + lib.json
  blender -b --python tools/armor/lib.py -- --sheet out.png   (also renders a contact sheet)

Material slots: `metal` (all), `gem` on stones; a piece's `mat` replaces them.
"""
import bpy, bmesh, json, math, struct, sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "godot" / "art" / "armor" / "lib"
MM = 0.001
TAU = math.tau


# ---------- helpers ----------
def noise(x, y, z=0.0, seed=0):
    """Smooth deterministic noise in [-1, 1] (sum of sines; enough for hand-forged wobble)."""
    s = seed * 1.618
    return (math.sin(x * 1.7 + s) * math.cos(y * 1.3 - s * 0.7) * 0.5
            + math.sin(x * 0.9 - y * 1.1 + z * 2.1 + s * 1.3) * 0.3
            + math.sin(y * 2.3 + z * 0.7 - s * 2.1) * 0.2)


def mat(name, color, metallic, rough):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    return m


class Builder:
    """Collects verts (mm) and faces with a material index (0 metal, 1 gem) and a flat flag."""

    def __init__(self):
        self.v, self.f = [], []

    def add(self, co):
        self.v.append(tuple(co))
        return len(self.v) - 1

    def face(self, idx, m=0, flat=False):
        self.f.append((list(idx), m, flat))

    def lathe(self, profile, segs, ax=1.0, ay=1.0, m=0, flat=False, rot=0.0,
              wobble=0.0, seed=0, pole=None, zw=0.0):
        """profile: [(d, z)] where d is the radius (round) or inset from the ellipse (ax, ay radii
        of the outermost point, mm). Last ring is closed by a fan to `pole` (x, y, z) if given."""
        rmax = profile[0][0]
        rings = []
        for (d, z) in profile:
            ring = []
            for i in range(segs):
                a = rot + TAU * i / segs
                w = 1.0 + wobble * noise(math.cos(a) * 3, math.sin(a) * 3, z * 0.3, seed)
                rx = (ax - (rmax - d)) if ax != 1.0 else d
                ry = (ay - (rmax - d)) if ay != 1.0 else d
                zz = z + (zw * noise(math.cos(a) * 2.0, math.sin(a) * 2.0, d, seed + 5) if z > 0 else 0.0)
                ring.append(self.add((rx * w * math.cos(a), ry * w * math.sin(a), zz)))
            rings.append(ring)
        for r0, r1 in zip(rings, rings[1:]):
            for i in range(segs):
                j = (i + 1) % segs
                self.face([r0[i], r0[j], r1[j], r1[i]], m, flat)
        if pole is not None:
            p = self.add(pole)
            last = rings[-1]
            for i in range(segs):
                self.face([last[i], last[(i + 1) % segs], p], m, flat)
        return rings

    def sweep(self, path, profile, widths=None, closed=False, zs=None, m=0, closed_profile=False,
              cap_start=False, cap_end=False, hscale=None):
        """path: [(x, y)] mm; profile: [(u, z)] u across in units of half-width (-1..1), z mm above
        the path's base z. widths: half-widths per point. zs: base z per point. hscale: height
        scale per point (tapering tips)."""
        n = len(path)
        widths = widths or [1.0] * n
        zs = zs or [0.0] * n
        hscale = hscale or [1.0] * n
        rings = []
        for i, p in enumerate(path):
            if closed:
                a, b = path[i - 1], path[(i + 1) % n]
            else:
                a, b = path[max(i - 1, 0)], path[min(i + 1, n - 1)]
            t = Vector((b[0] - a[0], b[1] - a[1])).normalized()
            nrm = Vector((-t.y, t.x))
            ring = []
            for (u, z) in profile:
                q = Vector(p) + nrm * (u * widths[i])
                ring.append(self.add((q.x, q.y, zs[i] + z * hscale[i])))
            rings.append(ring)
        k = len(profile)
        pairs = list(zip(rings, rings[1:])) + ([(rings[-1], rings[0])] if closed else [])
        bands = k if closed_profile else k - 1
        for r0, r1 in pairs:
            for j in range(bands):
                jj = (j + 1) % k
                self.face([r0[j], r1[j], r1[jj], r0[jj]], m)
        if cap_start:
            self.face(list(reversed(rings[0])), m)
        if cap_end:
            self.face(list(rings[-1]), m)
        return rings

    def to_object(self, name, mats, sharp_deg=35.0, wobble=None):
        me = bpy.data.meshes.new(name)
        verts = [(x * MM, y * MM, z * MM) for (x, y, z) in self.v]
        me.from_pydata(verts, [], [f for f, _, _ in self.f])
        me.update()
        for poly, (_, mi, flat) in zip(me.polygons, self.f):
            poly.material_index = mi
            poly.use_smooth = not flat
        for mm in mats:
            me.materials.append(mm)
        ob = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(ob)
        fix_normals(ob)
        me.set_sharp_from_angle(angle=math.radians(sharp_deg))
        return ob


def fix_normals(ob):
    """Recalculate outward normals (all our meshes are open at z=0 so recalc can be fooled:
    afterwards flip any face whose normal points into the piece's axis-below hemisphere)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()


def orient_up(ob):
    """Open shells: recalc can pick either side, so per island with a boundary (open at z=0),
    flip the island if its area-weighted normal points down. Closed islands keep recalc's."""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.faces.ensure_lookup_table()
    seen = set()
    for f0 in bm.faces:
        if f0.index in seen:
            continue
        isl, stack = [], [f0]
        seen.add(f0.index)
        while stack:
            f = stack.pop()
            isl.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen:
                        seen.add(g.index)
                        stack.append(g)
        open_ = any(e.is_boundary for f in isl for e in f.edges)
        if open_ and sum(f.normal.z * f.calc_area() for f in isl) < 0:
            for f in isl:
                f.normal_flip()
    bm.to_mesh(me)
    bm.free()


def tris_of(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


# ---------- the ten ----------
def rivet():
    b = Builder()
    # 6.5 mm head; not a perfect hemisphere: a squat, slightly lopsided hammered dome
    b.lathe([(3.25, 0.0), (3.05, 0.85), (2.05, 1.85)], 8, wobble=0.035, seed=1,
            pole=(0.18, -0.12, 2.35), zw=0.08)
    return b, 40, 70


def stud():
    b = Builder()
    # square faceted pyramid, ~7 mm, with a chamfered skirt (the bevel) and a blunted tip
    prof = [(3.5 * 1.414, 0.0), (3.35 * 1.414, 0.45), (2.95 * 1.414, 0.85), (0.45 * 1.414, 2.75)]
    rings = b.lathe(prof, 4, rot=math.pi / 4, flat=True, wobble=0.02, seed=2)
    b.face(rings[-1], 0, True)
    return b, 40, 30


def dome():
    b = Builder()
    b.lathe([(6.0, 0.0), (5.8, 0.55), (4.95, 1.9), (3.2, 2.95)], 10, wobble=0.025, seed=3,
            pole=(0.15, 0.1, 3.45), zw=0.06)
    return b, 80, 60


def grommet():
    b = Builder()
    # a rolled eyelet ring: inner lip curls over, outer skirt seats
    b.lathe([(2.2, 0.0), (2.45, 0.85), (3.15, 1.2), (3.8, 0.8), (4.0, 0.0)], 8, wobble=0.02, seed=4)
    return b, 64, 70


def gem(ax, ay, name, seed):
    """Bezel cup (metal) with a faceted stone (gem). ax, ay: stone girdle radii (mm)."""
    b = Builder()
    segs = 16
    bz = 1.2  # bezel wall thickness beyond the stone
    # bezel: outer skirt -> bevelled top lip -> inner lip folding over the girdle
    prof = [(ax + bz, 0.0), (ax + bz - 0.15, 1.45), (ax + bz - 0.5, 2.05), (ax + 0.05, 2.2),
            (ax - 0.25, 1.85), (ax - 0.25, 1.3)]
    if ax == ay:
        rings = b.lathe(prof, segs, wobble=0.012, seed=seed)
    else:
        rings = b.lathe(prof, segs, ax=ax + bz, ay=ay + bz, wobble=0.012, seed=seed)
    # cup floor under the stone
    floor = b.add((0, 0, 1.3))
    last = rings[-1]
    for i in range(segs):
        b.face([last[i], last[(i + 1) % segs], floor], 0)
    # stone: girdle 16 -> star 8 -> table 8 (brilliant-ish crown); the pavilion hides in the cup
    g = [b.add((ax * 1.0 * math.cos(TAU * i / 16), ay * math.sin(TAU * i / 16), 1.95)) for i in range(16)]
    crown = 0.72
    s = [b.add(((ax * 0.74) * math.cos(TAU * (i + 0.5) / 8), (ay * 0.74) * math.sin(TAU * (i + 0.5) / 8),
                1.95 + crown * ax * 0.32)) for i in range(8)]
    t = [b.add(((ax * 0.5) * math.cos(TAU * i / 8), (ay * 0.5) * math.sin(TAU * i / 8),
                1.95 + crown * ax * 0.42)) for i in range(8)]
    for i in range(8):
        g0, g1, g2 = g[2 * i], g[2 * i + 1], g[(2 * i + 2) % 16]
        si, sp = s[i], s[i - 1]
        ti, tn = t[i], t[(i + 1) % 8]
        # girdle facets
        b.face([g0, g1, si], 1, True)
        b.face([g1, g2, si], 1, True)
        # kite between stars down to the girdle main point
        b.face([g0, si, ti], 1, True)
        b.face([g0, ti, sp], 1, True)
        # star facet to the table
        b.face([si, tn, ti], 1, True)
    b.face(t, 1, True)  # table (octagon)
    return b, 300, 50


def gem_round():
    return gem(6.0, 6.0, "gem_round", 5)


def gem_oval():
    return gem(8.0, 5.5, "gem_oval", 6)


def boss():
    b = Builder()
    prof = [(15.0, 0.0), (15.0, 0.55), (14.65, 1.15), (14.0, 1.35), (13.35, 1.05),  # rolled rim
            (12.6, 0.85), (7.4, 1.25),  # flange, rising slightly
            (6.6, 1.55), (5.6, 3.35), (3.6, 4.75)]  # dome
    b.lathe(prof, 20, wobble=0.015, seed=7, pole=(0.25, -0.2, 5.35), zw=0.12)
    return b, 400, 45


def rounded_rect(hx, hy, r, per_corner):
    pts = []
    corners = [(hx - r, hy - r, 0.0), (-(hx - r), hy - r, 0.25), (-(hx - r), -(hy - r), 0.5), (hx - r, -(hy - r), 0.75)]
    for (cx, cy, a0) in corners:
        for k in range(per_corner):
            a = TAU * (a0 + 0.25 * k / (per_corner - 1))
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def plate_ring(b, path, prof, seed, m=0):
    """Closed outline sweep for a plate edge: prof [(inset mm, z)] from the outline inward."""
    # centroid-based inward offset (outlines here are convex rounded rects)
    rings = []
    n = len(path)
    for (d, z) in prof:
        ring = []
        for i, p in enumerate(path):
            a, c = path[i - 1], path[(i + 1) % n]
            t = Vector((c[0] - a[0], c[1] - a[1])).normalized()
            nrm = Vector((t.y, -t.x))  # outward for a CCW outline
            w = 0.12 * noise(p[0] * 0.4, p[1] * 0.4, 0, seed)
            q = Vector(p) + nrm * (w - d)
            ring.append(b.add((q.x, q.y, z)))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            b.face([r0[i], r0[j], r1[j], r1[i]], m)
    return rings


def rune_plate():
    b = Builder()
    path = rounded_rect(20.0, 11.0, 4.0, 6)
    field = 1.15
    rings = plate_ring(b, path, [(0.0, 0.0), (0.0, 0.6), (0.4, 1.2), (1.0, 1.45), (1.6, 1.35), (2.2, field)], 8)
    b.face(rings[-1], 0)          # field, filled for the boolean
    b.face(list(reversed(rings[0])), 0)  # bottom, removed after the boolean
    ob = b.to_object("rune_plate", [MATS["metal"]], sharp_deg=30)
    # rune channel: chisel-cut V grooves (convex hulls of a raised outline and a sunk ridge)
    strokes = [((0.0, -7.0), (0.0, 7.0)),      # stave
               ((0.0, 2.2), (-4.6, 6.4)), ((0.0, 2.2), (4.6, 6.4)),   # upper arms
               ((0.0, -1.2), (-3.6, -4.8)), ((0.0, -1.2), (3.6, -4.8)),  # lower arms
               ((-14.5, -6.5), (-14.5, 6.5)), ((14.5, -6.5), (14.5, 6.5))]  # framing strokes
    cutters = []
    for k, (p, q) in enumerate(strokes):
        p, q = Vector(p), Vector(q)
        t = (q - p).normalized()
        n = Vector((-t.y, t.x))
        hw, depth, lift = 1.5, 0.6, 0.6
        ztop, zbot = field + lift, field - depth
        e = 0.9  # pointed chisel ends
        top = [p - t * e, p + n * hw, q + n * hw, q + t * e, q - n * hw, p - n * hw]
        bot = [p + t * 0.4, q - t * 0.4]
        bm = bmesh.new()
        for v in top:
            bm.verts.new((v.x * MM, v.y * MM, ztop * MM))
        for v in bot:
            bm.verts.new((v.x * MM, v.y * MM, zbot * MM))
        bmesh.ops.convex_hull(bm, input=bm.verts[:])
        me = bpy.data.meshes.new(f"cut{k}")
        bm.to_mesh(me)
        bm.free()
        c = bpy.data.objects.new(f"cut{k}", me)
        bpy.context.collection.objects.link(c)
        cutters.append(c)
    for c in cutters:
        mod = ob.modifiers.new("cut", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.solver = "EXACT"
        mod.object = c
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(c)
    drop_bottom(ob)
    ob.data.set_sharp_from_angle(angle=math.radians(30))
    return ob, 600


def drop_bottom(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    kill = [f for f in bm.faces if f.normal.z < -0.99 and all(abs(v.co.z) < 1e-6 for v in f.verts)]
    bmesh.ops.delete(bm, geom=kill, context="FACES_ONLY")
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4], quad_method="BEAUTY", ngon_method="BEAUTY")
    bm.to_mesh(ob.data)
    bm.free()


def spiral(c, start, k, turns_rad, n, sgn=1.0):
    """Log spiral about c from `start`, radius r0*exp(-k*phi), phi up to turns_rad."""
    d = Vector(start) - Vector(c)
    r0, a0 = d.length, math.atan2(d.y, d.x)
    pts = []
    for i in range(n):
        ph = turns_rad * i / (n - 1)
        r = r0 * math.exp(-k * ph)
        a = a0 + sgn * ph
        pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    return pts


WIRE = [(-1.0, 0.0), (-0.8, 1.0), (0.0, 1.5), (0.8, 1.0), (1.0, 0.0)]  # half-round wire, 1.5 mm


def filigree_plate():
    b = Builder()
    # frame: a flat-topped band round the plate (outer 45 x 28)
    frame = rounded_rect(21.3, 12.8, 3.5, 7)
    b.sweep(frame, [(-1.0, 0.0), (-0.65, 1.5), (0.65, 1.5), (1.0, 0.0)], widths=[1.2] * len(frame), closed=True)
    # stem across the middle, top to bottom
    stem = [(0.0, -12.2), (0.0, 0.0), (0.0, 12.2)]
    b.sweep(stem, WIRE, widths=[0.85] * 3)
    # four C-scrolls sprouting from the stem and curling into each quadrant (a lyre)
    n = 17
    for sx in (1, -1):
        for sy in (1, -1):
            pts = spiral((-10.0 * sx, 4.2 * sy), (0.0, 1.8 * sy), 0.255, 7.2, n, sgn=(1.0 if sx * sy > 0 else -1.0))
            w = [0.85 - 0.45 * (i / (n - 1)) ** 1.5 for i in range(n)]
            h = [1.0 - 0.35 * (i / (n - 1)) ** 2 for i in range(n)]
            rings = b.sweep(pts, WIRE, widths=w, hscale=h, cap_end=True)
    ob = b.to_object("filigree_plate", [MATS["metal"]], sharp_deg=40)
    return ob, 800


def buckle():
    b = Builder()
    frame = rounded_rect(12.0, 8.9, 3.0, 6)
    wobble = [1.6 * (1 + 0.06 * noise(x * 0.5, y * 0.5, 0, 9)) for (x, y) in frame]
    b.sweep(frame, WIRE, widths=wobble, closed=True, hscale=[1.55] * len(frame))
    # pin bar across the frame
    bar = [(-4.0, -9.4), (-4.0, 0.0), (-4.0, 9.4)]
    b.sweep(bar, WIRE, widths=[1.15] * 3, hscale=[1.25] * 3)
    # tongue: a forged pin from the bar over the frame's far side, tapering, bent down at the tip
    tp = [(-5.2, 0.0), (-3.0, 0.0), (1.5, 0.0), (6.5, 0.0), (11.0, 0.0), (13.2, 0.0)]
    tz = [1.0, 1.75, 2.15, 2.45, 2.7, 1.9]
    tw = [1.25, 1.3, 1.2, 1.05, 0.9, 0.7]
    ring = [(-1.0, 0.0), (-0.75, 0.6), (0.0, 0.85), (0.75, 0.6), (1.0, 0.0), (0.0, -0.55)]
    b.sweep(tp, ring, widths=tw, zs=tz, closed_profile=True, cap_start=True, cap_end=True)
    ob = b.to_object("buckle", [MATS["metal"]], sharp_deg=40)
    return ob, 400


SPEC = {  # id: (builder, kind)
    "rivet": rivet, "stud": stud, "dome": dome, "grommet": grommet,
    "gem_round": gem_round, "gem_oval": gem_oval, "boss": boss,
    "rune_plate": rune_plate, "filigree_plate": filigree_plate, "buckle": buckle,
}


def glb_stats(path):
    data = path.read_bytes()
    ln = struct.unpack_from("<I", data, 12)[0]
    js = json.loads(data[20:20 + ln])
    tris, lo, hi, mats = 0, [9e9] * 3, [-9e9] * 3, [m["name"] for m in js.get("materials", [])]
    for mesh in js["meshes"]:
        for pr in mesh["primitives"]:
            acc = js["accessors"][pr["attributes"]["POSITION"]]
            lo = [min(a, b) for a, b in zip(lo, acc["min"])]
            hi = [max(a, b) for a, b in zip(hi, acc["max"])]
            tris += js["accessors"][pr["indices"]]["count"] // 3
    return tris, lo, hi, mats


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    bpy.ops.wm.read_factory_settings(use_empty=True)
    global MATS
    MATS = {"metal": mat("metal", (0.55, 0.53, 0.5), 1.0, 0.38),
            "gem": mat("gem", (0.5, 0.05, 0.08), 0.0, 0.08)}
    OUT.mkdir(parents=True, exist_ok=True)
    index, bad = {}, []
    for gid, fn in SPEC.items():
        for o in list(bpy.data.objects):
            bpy.data.objects.remove(o)
        res = fn()
        if isinstance(res[0], Builder):
            bld, budget, sharp = res
            mats = [MATS["metal"]] + ([MATS["gem"]] if any(m == 1 for _, m, _ in bld.f) else [])
            ob = bld.to_object(gid, mats, sharp_deg=sharp)
        else:
            ob, budget = res
        orient_up(ob)
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        f = OUT / f"{gid}.glb"
        bpy.ops.export_scene.gltf(filepath=str(f), export_format="GLB", use_selection=True,
                                  export_yup=False, export_apply=True, export_normals=True,
                                  export_texcoords=False, export_materials="EXPORT")
        tris, lo, hi, mnames = glb_stats(f)
        size = [round((h - l) / MM, 2) for l, h in zip(lo, hi)]
        index[gid] = {"file": f"{gid}.glb", "tris": tris, "size_mm": size, "materials": mnames}
        flag = "" if tris <= budget and abs(lo[2]) < 1e-5 else "  <-- CHECK"
        if flag:
            bad.append(gid)
        print(f"LIB {gid:15s} tris {tris:4d}/{budget:<4d} size_mm {size} zmin {lo[2] / MM:.3f} mats {mnames}{flag}")
    (OUT / "lib.json").write_text(json.dumps(index, indent=1) + "\n")
    print("LIB wrote", OUT / "lib.json", "bad:", bad)
    if "--sheet" in argv:
        sheet(Path(argv[argv.index("--sheet") + 1]), index)


def sheet(path, index):
    """Contact sheet: re-import each glb (tests the frame), stand it +Z up on a grey ground."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    ids = list(index)
    pitch = 0.055
    for k, gid in enumerate(ids):
        bpy.ops.import_scene.gltf(filepath=str(OUT / index[gid]["file"]))
        ob = bpy.context.selected_objects[0]
        # importer maps glTF +Y to Blender +Z; undo that so glTF +Z (out) is Blender +Z here
        ob.rotation_mode = "XYZ"
        ob.rotation_euler = (-math.pi / 2, 0, 0)
        col, row = k % 5, k // 5
        ob.location = (col * pitch, -row * pitch * 0.85, 0)
        # 10 mm scale bar in front
        bpy.ops.mesh.primitive_cube_add(size=1, location=(col * pitch - 0.012, -row * pitch * 0.85 - 0.02, 0.0002))
        bar = bpy.context.active_object
        bar.scale = (0.010, 0.0012, 0.0004)
        bar.location.x += 0.005
        bm = bpy.data.materials.new("bar")
        bm.use_nodes = True
        bm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1)
        bar.data.materials.append(bm)
        bpy.ops.object.text_add(location=(col * pitch - 0.022, -row * pitch * 0.85 - 0.03, 0.0002))
        t = bpy.context.active_object
        t.data.body = f"{gid}  {index[gid]['tris']}t  (bar 10 mm)"
        t.data.size = 0.0042
        t.data.materials.append(bm)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.11, -0.02, -0.00005))
    g = bpy.context.active_object
    gm = bpy.data.materials.new("ground")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.32, 0.32, 0.32, 1)
    gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
    g.data.materials.append(gm)
    bpy.ops.object.light_add(type="AREA", location=(0.05, 0.05, 0.25))
    L = bpy.context.active_object
    L.data.energy = 2.0
    L.data.size = 0.3
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 1), rotation=(math.radians(45), 0, math.radians(-30)))
    bpy.context.active_object.data.energy = 1.2
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.4, 0.4, 0.42, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.12
    sc.world = w
    bpy.ops.object.camera_add(location=(0.11, -0.30, 0.26), rotation=(math.radians(43), 0, 0))
    cam = bpy.context.active_object
    cam.data.lens = 38
    cam.data.clip_start = 0.005
    sc.camera = cam
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 64
    sc.cycles.device = "CPU"
    sc.render.resolution_x, sc.render.resolution_y = 2400, 1300
    sc.render.filepath = str(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)
    print("LIB sheet", path)


MATS = {}
main()
