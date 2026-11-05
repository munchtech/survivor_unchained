"""Stage 1 (inside Blender): MakeHuman's woman (MPFB, CC0) from a spec, as arrays.

    make_base(spec) -> dict of numpy arrays:
      V [N,3]  every point of MakeHuman's mesh (helpers too), in the world (Blender: z up, her front -y), every target
               of the spec laid, then the spec's sculpts (tools/body/sculpts.py) as tools/assets/heroine_head.py lays them;
      F [M,4]  the skin's faces (the "body" vertex group's: helpers dropped), quads, into V;
      U [M,4,2] each face corner's UV;
      inbody [N] bool;  groups: {"joint-...": indices} (MPFB's joint cubes, for the skeleton);
      eyes [E,3] the eyes proxy's points, fitted to her (their middles weigh the head's smoothing, as heroine_head.py).
      Vs [N,3] with "sliders": the slider body (sliders.py: the catalogue's macros and targets on top), same topology.
Spec keys: macros, targets (name -> weight, sides already expanded), build (the same, laid after), sculpts
(name -> weight), eyes (MakeHuman's eyes asset), sliders (catalogue.json name -> value).
"""
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
PORTRAITS = os.path.join(REPO, "tools", "assets", "heroine_face", "targets")


def target_paths():
    tdir = os.path.join(bpy.utils.user_resource("EXTENSIONS"), "user_default", "mpfb", "data", "targets")
    out = {}
    for root, _, files in sorted(os.walk(tdir)):
        for f in sorted(files):
            if f.endswith(".target.gz") and "expression" not in root:
                out.setdefault(f[:-10], os.path.join(root, f))
    if os.path.isdir(PORTRAITS):
        for f in sorted(os.listdir(PORTRAITS)):
            if ".target" in f:
                out[f.split(".target")[0]] = os.path.join(PORTRAITS, f)
    return out


def grab(o):
    e = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m = e.to_mesh()
    mw = np.array(o.matrix_world)
    V = np.array([v.co[:] for v in m.vertices]) @ mw[:3, :3].T + mw[:3, 3]
    F = [list(p.vertices) for p in m.polygons]
    uvd = m.uv_layers.active.data
    U = [np.array([uvd[li].uv[:] for li in p.loop_indices]) for p in m.polygons]
    e.to_mesh_clear()
    return V, F, U


def human(spec, macros, targets):
    """One MakeHuman human from macros and targets (the spec's face and neck targets, then `targets`), its arrays."""
    from bl_ext.user_default.mpfb.services.humanservice import HumanService
    from bl_ext.user_default.mpfb.services.targetservice import TargetService
    import sculpts
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    hm = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True,
                                   feet_on_ground=True, scale=0.1, macro_detail_dict=macros)
    paths = target_paths()
    for key in ("targets", "build"):
        for n, w in spec.get(key, {}).items():
            TargetService.load_target(hm, paths[n], weight=float(w))
    for n, w in targets.items():
        TargetService.load_target(hm, paths[n], weight=float(w))
    data = os.path.join(bpy.utils.user_resource("EXTENSIONS"), ".user", "user_default", "mpfb", "data")   # (MPFB keeps its assets here)
    eyes = HumanService.add_mhclo_asset(os.path.join(data, "eyes", spec["eyes"], spec["eyes"] + ".mhclo"), hm,
                                        asset_type="eyes", subdiv_levels=0, material_type="NONE", set_up_rigging=False,
                                        interpolate_weights=False, import_subrig=False, import_weights=False)
    for mo in hm.modifiers:
        mo.show_viewport = False
    bpy.context.view_layer.update()
    V, F, U = grab(hm)
    EV = grab(eyes)[0]
    V0 = V.copy()
    for n, w in spec.get("sculpts", {}).items():
        V = V + float(w) * sculpts.SCULPTS[n](V0, sculpts.anatomy(V0))
    return hm, V, F, U, EV


def make_base(spec):
    """The head's human (the spec's macros and targets: v1's woman, whose head A carries) as V; with "sliders", the
    slider body (sliders.py) too, as Vs, on the same topology (forms.compose joins them under the head)."""
    sys.path.insert(0, HERE)
    import sliders
    hm, V, F, U, EV = human(spec, spec["macros"], {})
    body = hm.vertex_groups["body"].index
    inbody = np.array([any(g.group == body for g in v.groups) for v in hm.data.vertices])
    keep = [i for i, f in enumerate(F) if inbody[f].all()]
    assert all(len(F[i]) == 4 for i in keep), "MakeHuman's skin is all quads"
    groups = {}
    names = {g.index: g.name for g in hm.vertex_groups}
    for v in hm.data.vertices:
        for g in v.groups:
            nm = names[g.group]
            if nm.startswith("joint-") and g.weight > 0:
                groups.setdefault(nm, []).append(v.index)
    out = {"V": V, "F": np.array([F[i] for i in keep], np.int64), "U": np.array([U[i] for i in keep]),
           "inbody": inbody, "groups": {k: np.array(v, np.int64) for k, v in sorted(groups.items())}, "eyes": EV}
    if spec.get("sliders"):
        macros, targets = sliders.resolve(spec)
        out["Vs"] = human(spec, macros, targets)[1]
    return out
