"""A small glb writer (numpy + json): our skeleton and body, and the ref's head meshes copied byte for byte.

    write(path, ref_path, skeleton, body, heads, head_joint_map, extras)
skeleton: {"names", "parents", "worlds" [B,4,4] rest worlds (glTF), "scale": {bone: s} (a rest scale left out of the
          inverse binds, as heroine_headscale.py does her Head)}
body:     {"node", "material", "P", "N", "UV", "T", "J", "W"} (J/W [n,8]: JOINTS_0/1, WEIGHTS_0/1); optional "Tan"
          [n,4] (TANGENT: xyz, w the bitangent's sign; P1 E2)
heads:    node names in the ref to copy: their meshes (every attribute, target, extras, default weights), materials,
          textures, samplers and images verbatim; only JOINTS_0 is rewritten (head_joint_map: the ref's joint
          index -> ours), WEIGHTS_0 kept as stored.
head_override (optional, P1 B2a: the head scale baked, our head weights): {node: {"P" [V,3], "J" [V,k], "W" [V,k]
          (k 4 or 8), "targets": {name: dP [V,3]}}} over the mesh's primitives in order: POSITION, the joints and
          weights and those targets' POSITION written from these; everything else still copied verbatim.
"""
import json
import os
import struct

import numpy as np

COMP = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def _read_glb(path):
    d = open(path, "rb").read()
    jl = struct.unpack("<I", d[12:16])[0]
    js = json.loads(d[20:20 + jl])
    o = 20 + jl
    bl = struct.unpack("<I", d[o:o + 4])[0]
    return js, d[o + 8:o + 8 + bl]


def _quat(R):
    """Rotation matrix -> glTF quaternion [x, y, z, w] (w >= 0)."""
    m = R
    t = np.trace(m)
    if t > 0:
        s = np.sqrt(t + 1.0) * 2
        q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, 0.25 * s]
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        q = [0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s, (m[2, 1] - m[1, 2]) / s]
    elif m[1, 1] > m[2, 2]:
        s = np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        q = [(m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s]
    else:
        s = np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        q = [(m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s, (m[1, 0] - m[0, 1]) / s]
    q = np.array(q)
    q /= np.linalg.norm(q)
    return q if q[3] >= 0 else -q


class _Out:
    def __init__(self):
        self.bin = bytearray()
        self.views, self.accs = [], []

    def view(self, data, target=None):
        while len(self.bin) % 4:
            self.bin += b"\0"
        v = {"buffer": 0, "byteOffset": len(self.bin), "byteLength": len(data)}
        if target:
            v["target"] = target
        self.bin += data
        self.views.append(v)
        return len(self.views) - 1

    def acc(self, arr, kind, comp, target=None, minmax=False, normalized=False):
        arr = np.ascontiguousarray(arr.astype(COMP[comp]))
        a = {"bufferView": self.view(arr.tobytes(), target), "componentType": comp,
             "count": int(arr.shape[0]), "type": kind}
        if normalized:
            a["normalized"] = True
        if minmax:
            a["min"] = [float(x) for x in arr.reshape(len(arr), -1).min(0)]
            a["max"] = [float(x) for x in arr.reshape(len(arr), -1).max(0)]
        self.accs.append(a)
        return len(self.accs) - 1

    def copy_acc(self, ref_js, ref_bin, i):
        """The ref's accessor i, its bytes as stored (tightly packed when its view was strided)."""
        a = dict(ref_js["accessors"][i])
        if "sparse" in a:
            sp_ = {k: dict(v_) for k, v_ in a["sparse"].items() if isinstance(v_, dict)}
            sp_["count"] = a["sparse"]["count"]
            for part in ("indices", "values"):
                vv = ref_js["bufferViews"][sp_[part]["bufferView"]]
                off = vv.get("byteOffset", 0) + sp_[part].get("byteOffset", 0)
                ln = vv["byteLength"] - sp_[part].get("byteOffset", 0)
                sp_[part].pop("byteOffset", None)
                sp_[part]["bufferView"] = self.view(bytes(ref_bin[off:off + ln]))
            a["sparse"] = sp_
        if "bufferView" not in a:                  # (all zeros, or sparse over zeros)
            self.accs.append(a)
            return len(self.accs) - 1
        v = ref_js["bufferViews"][a["bufferView"]]
        n = NCOMP[a["type"]]
        size = np.dtype(COMP[a["componentType"]]).itemsize * n
        off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = v.get("byteStride", size)
        if stride == size:
            data = bytes(ref_bin[off:off + size * a["count"]])
        else:
            data = b"".join(bytes(ref_bin[off + k * stride:off + k * stride + size]) for k in range(a["count"]))
        a.pop("byteOffset", None)
        a["bufferView"] = self.view(data, v.get("target"))
        self.accs.append(a)
        return len(self.accs) - 1


def write(path, ref_path, skeleton, body, heads, head_joint_map, extras=None, head_override=None):
    rjs, rbin = _read_glb(ref_path)
    out = _Out()
    names, parents, worlds = skeleton["names"], skeleton["parents"], skeleton["worlds"]
    nodes = []
    # joints
    for j, n in enumerate(names):
        p = parents[j]
        L = worlds[j] if p < 0 else np.linalg.inv(worlds[p]) @ worlds[j]
        nd = {"name": n}
        t = L[:3, 3]
        if np.abs(t).max() > 0:
            nd["translation"] = [float(x) for x in t]
        R = L[:3, :3]
        q = _quat(R)
        if abs(q[3] - 1) > 1e-12:
            nd["rotation"] = [float(x) for x in q]
        if n in skeleton.get("scale", {}):
            k = float(skeleton["scale"][n])
            nd["scale"] = [k, k, k]
        kids = [c for c, pp in enumerate(parents) if pp == j]
        if kids:
            nd["children"] = kids
        nodes.append(nd)
    ibm = np.stack([np.linalg.inv(G) for G in worlds]).transpose(0, 2, 1).reshape(-1, 16)
    skin = {"name": "Armature", "joints": list(range(len(names))), "inverseBindMatrices": out.acc(ibm, "MAT4", 5126)}
    # materials, textures, images: the heads' as the ref has them; the body's a plain one
    mats, texs, imgs, samps = [], [], [], []
    tex_map, img_map, samp_map, mat_map = {}, {}, {}, {}

    def copy_tex(ti):
        if ti in tex_map:
            return tex_map[ti]
        t = dict(rjs["textures"][ti])
        if "sampler" in t:
            si = t["sampler"]
            if si not in samp_map:
                samps.append(rjs["samplers"][si])
                samp_map[si] = len(samps) - 1
            t["sampler"] = samp_map[si]
        ii = t["source"]
        if ii not in img_map:
            im = dict(rjs["images"][ii])
            v = rjs["bufferViews"][im["bufferView"]]
            off = v.get("byteOffset", 0)
            im["bufferView"] = out.view(bytes(rbin[off:off + v["byteLength"]]))
            imgs.append(im)
            img_map[ii] = len(imgs) - 1
        t["source"] = img_map[ii]
        texs.append(t)
        tex_map[ti] = len(texs) - 1
        return tex_map[ti]

    def fix_tex(o):
        if isinstance(o, dict):
            return {k: (dict(v, index=copy_tex(v["index"])) if isinstance(v, dict) and "index" in v and k.endswith("Texture")
                        else fix_tex(v)) for k, v in o.items()}
        return o

    def copy_mat(mi):
        if mi not in mat_map:
            mats.append(fix_tex(rjs["materials"][mi]))
            mat_map[mi] = len(mats) - 1
        return mat_map[mi]
    mats.append(body["material"])
    meshes = []
    # the body
    prim = {"attributes": {
        "POSITION": out.acc(body["P"], "VEC3", 5126, 34962, minmax=True),
        "NORMAL": out.acc(body["N"], "VEC3", 5126, 34962),
        "TEXCOORD_0": out.acc(body["UV"], "VEC2", 5126, 34962),
        "JOINTS_0": out.acc(body["J"][:, :4], "VEC4", 5123, 34962),
        "WEIGHTS_0": out.acc(body["W"][:, :4], "VEC4", 5126, 34962),
        "JOINTS_1": out.acc(body["J"][:, 4:8], "VEC4", 5123, 34962),
        "WEIGHTS_1": out.acc(body["W"][:, 4:8], "VEC4", 5126, 34962),
        **({"TANGENT": out.acc(np.asarray(body["Tan"], np.float32), "VEC4", 5126, 34962)} if "Tan" in body else {})},
        "indices": out.acc(body["T"].reshape(-1), "SCALAR", 5125, 34963), "material": 0}
    meshes.append({"name": body["node"], "primitives": [prim]})
    mesh_nodes = [{"name": body["node"], "mesh": 0, "skin": 0}]
    # the heads, verbatim
    rnode = {n.get("name"): n for n in rjs["nodes"]}
    jmap = np.asarray(head_joint_map)
    for h in heads:
        rm = rjs["meshes"][rnode[h]["mesh"]]
        m = {k: v for k, v in rm.items() if k != "primitives"}
        m["primitives"] = []
        ov = (head_override or {}).get(h)
        tnames = rm.get("extras", {}).get("targetNames", [])
        o0 = 0
        for pr in rm["primitives"]:
            q = {k: v for k, v in pr.items() if k not in ("attributes", "indices", "targets", "material")}
            q["attributes"] = {}
            if ov is not None:
                cnt = rjs["accessors"][pr["attributes"]["POSITION"]]["count"]
                sl = slice(o0, o0 + cnt)
                o0 += cnt
                for k, ai in pr["attributes"].items():
                    if k == "POSITION":
                        q["attributes"][k] = out.acc(np.asarray(ov["P"][sl], np.float32), "VEC3", 5126, 34962, minmax=True)
                    elif not k.startswith(("JOINTS_", "WEIGHTS_")):
                        q["attributes"][k] = out.copy_acc(rjs, rbin, ai)
                Jo, Wo = np.asarray(ov["J"][sl]), np.asarray(ov["W"][sl])
                for s_ in range(Jo.shape[1] // 4):
                    q["attributes"][f"JOINTS_{s_}"] = out.acc(Jo[:, 4 * s_:4 * s_ + 4], "VEC4", 5123, 34962)
                    q["attributes"][f"WEIGHTS_{s_}"] = out.acc(Wo[:, 4 * s_:4 * s_ + 4], "VEC4", 5126, 34962)
                q["indices"] = out.copy_acc(rjs, rbin, pr["indices"])
                if "targets" in pr:
                    q["targets"] = []
                    for ti_, t in enumerate(pr["targets"]):
                        tt = {k: out.copy_acc(rjs, rbin, ai) for k, ai in t.items() if k != "POSITION"}
                        if "POSITION" in t:
                            tt["POSITION"] = out.acc(np.asarray(ov["targets"][tnames[ti_]][sl], np.float32), "VEC3", 5126,
                                                     34962, minmax=True)
                        q["targets"].append(tt)
                if "material" in pr:
                    q["material"] = copy_mat(pr["material"])
                m["primitives"].append(q)
                continue
            for k, ai in pr["attributes"].items():
                if k.startswith("JOINTS_"):
                    a = rjs["accessors"][ai]
                    v = rjs["bufferViews"][a["bufferView"]]
                    off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
                    J = np.frombuffer(rbin, COMP[a["componentType"]], a["count"] * 4, off).reshape(-1, 4)
                    q["attributes"][k] = out.acc(jmap[J.astype(np.int64)], "VEC4", 5123, 34962)
                else:
                    q["attributes"][k] = out.copy_acc(rjs, rbin, ai)
            q["indices"] = out.copy_acc(rjs, rbin, pr["indices"])
            if "targets" in pr:
                q["targets"] = [{k: out.copy_acc(rjs, rbin, ai) for k, ai in t.items()} for t in pr["targets"]]
            if "material" in pr:
                q["material"] = copy_mat(pr["material"])
            m["primitives"].append(q)
        meshes.append(m)
        mesh_nodes.append({"name": h, "mesh": len(meshes) - 1, "skin": 0})
    base = len(nodes)
    nodes += mesh_nodes
    roots = [j for j, p in enumerate(parents) if p < 0]
    nodes.append({"name": "Armature", "children": list(range(base, base + len(mesh_nodes))) + roots})
    js = {"asset": {"generator": "Survivor Unchained tools/body/build.py", "version": "2.0"}, "scene": 0,
          "scenes": [{"name": "Scene", "nodes": [len(nodes) - 1]}], "nodes": nodes, "meshes": meshes,
          "materials": mats, "skins": [skin], "accessors": out.accs, "bufferViews": out.views,
          "buffers": [{"byteLength": 0}]}
    if texs:
        js["textures"], js["images"] = texs, imgs
    if samps:
        js["samplers"] = samps
    if extras:
        js["extras"] = extras
    while len(out.bin) % 4:
        out.bin += b"\0"
    js["buffers"][0]["byteLength"] = len(out.bin)
    j = json.dumps(js, separators=(",", ":")).encode()
    j += b" " * ((4 - len(j) % 4) % 4)
    blob = (struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(j) + 8 + len(out.bin)) + struct.pack("<II", len(j), 0x4E4F534A)
            + j + struct.pack("<II", len(out.bin), 0x004E4942) + bytes(out.bin))
    with open(path, "wb") as f:
        f.write(blob)


def _compact(js, b):
    """(P1 R1 round 30) Drop the accessors and bufferViews nothing references and repack the binary chunk: set_targets
    replaces a mesh's shapes, and the old ones' bytes were left in the file (round_30's body.glb carried 29 MB of
    them in 60 dead accessors, play.glb 17 MB). Returns the new bin; `js` is rewritten in place."""
    accs, views = js.get("accessors", []), js.get("bufferViews", [])
    used = set()
    for m in js.get("meshes", []):
        for pr in m["primitives"]:
            used.update(pr["attributes"].values())
            if "indices" in pr:
                used.add(pr["indices"])
            for t in pr.get("targets", []):
                used.update(t.values())
    for s in js.get("skins", []):
        if "inverseBindMatrices" in s:
            used.add(s["inverseBindMatrices"])
    for an in js.get("animations", []):
        for sm in an["samplers"]:
            used.update((sm["input"], sm["output"]))
    amap = {o: n for n, o in enumerate(sorted(used))}
    for m in js.get("meshes", []):
        for pr in m["primitives"]:
            pr["attributes"] = {k: amap[v] for k, v in pr["attributes"].items()}
            if "indices" in pr:
                pr["indices"] = amap[pr["indices"]]
            if "targets" in pr:
                pr["targets"] = [{k: amap[v] for k, v in t.items()} for t in pr["targets"]]
    for s in js.get("skins", []):
        if "inverseBindMatrices" in s:
            s["inverseBindMatrices"] = amap[s["inverseBindMatrices"]]
    for an in js.get("animations", []):
        for sm in an["samplers"]:
            sm["input"], sm["output"] = amap[sm["input"]], amap[sm["output"]]
    accs = [accs[o] for o in sorted(used)]
    vused = set()
    for a in accs:
        if "bufferView" in a:
            vused.add(a["bufferView"])
        if "sparse" in a:
            vused.update((a["sparse"]["indices"]["bufferView"], a["sparse"]["values"]["bufferView"]))
    for im in js.get("images", []):
        if "bufferView" in im:
            vused.add(im["bufferView"])
    vmap, nb, nviews = {}, bytearray(), []
    for o in sorted(vused):
        while len(nb) % 4:
            nb += b"\0"
        v = dict(views[o])
        off = v.get("byteOffset", 0)
        nb += b[off:off + v["byteLength"]]
        v["byteOffset"] = len(nb) - v["byteLength"]
        vmap[o] = len(nviews)
        nviews.append(v)
    for a in accs:
        if "bufferView" in a:
            a["bufferView"] = vmap[a["bufferView"]]
        if "sparse" in a:
            for k in ("indices", "values"):
                a["sparse"][k]["bufferView"] = vmap[a["sparse"][k]["bufferView"]]
    for im in js.get("images", []):
        if "bufferView" in im:
            im["bufferView"] = vmap[im["bufferView"]]
    js["accessors"], js["bufferViews"] = accs, nviews
    return nb


def set_targets(path, node, targets, out_path=None):
    """Write blend shapes onto one mesh of a glb we wrote (its primitive 0): `targets` {name: (dP [V,3], dN [V,3])},
    in order; any targets the mesh had are replaced (their old bytes dropped: _compact). The mesh gets
    extras.targetNames and default weights 0."""
    js, b = _read_glb(path)
    out = _Out()
    out.bin = bytearray(b)
    out.views, out.accs = js["bufferViews"], js["accessors"]
    mi = next(n["mesh"] for n in js["nodes"] if n.get("name") == node and "mesh" in n)
    m = js["meshes"][mi]
    pr = m["primitives"][0]
    tg = []
    for nm, (dP, dN) in targets.items():
        tg.append({"POSITION": out.acc(np.asarray(dP, np.float32), "VEC3", 5126, 34962, minmax=True),
                   "NORMAL": out.acc(np.asarray(dN, np.float32), "VEC3", 5126, 34962)})
    if tg:
        pr["targets"] = tg
        m["extras"] = dict(m.get("extras", {}), targetNames=list(targets))
        m["weights"] = [0.0] * len(tg)
    else:
        pr.pop("targets", None)
        m.pop("weights", None)
        if "extras" in m:
            m["extras"].pop("targetNames", None)
    out.bin = _compact(js, bytes(out.bin))
    while len(out.bin) % 4:
        out.bin += b"\0"
    js["buffers"][0]["byteLength"] = len(out.bin)
    j = json.dumps(js, separators=(",", ":")).encode()
    j += b" " * ((4 - len(j) % 4) % 4)
    blob = (struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(j) + 8 + len(out.bin)) + struct.pack("<II", len(j), 0x4E4F534A)
            + j + struct.pack("<II", len(out.bin), 0x004E4942) + bytes(out.bin))
    with open(out_path or path, "wb") as f:
        f.write(blob)


def attach_maps(path, node, maps, out_path=None):
    """(P1 E2) Embed PNG maps in a glb we wrote and point its node's primitive-0 material at them: maps {"baseColor":
    png, "normal": png, "metallicRoughness": png} (any subset; each a bufferView image, one linear-mip sampler).
    Run after the correctives (stage 6) so every export carries them; the material's factors are kept, the
    roughness factor set to 1 when a metallicRoughness map comes (the map holds it)."""
    js, b = _read_glb(path)
    out = _Out()
    out.bin = bytearray(b)
    out.views, out.accs = js["bufferViews"], js["accessors"]
    mi = next(n["mesh"] for n in js["nodes"] if n.get("name") == node and "mesh" in n)
    pr = js["meshes"][mi]["primitives"][0]
    imgs, texs, samps = js.setdefault("images", []), js.setdefault("textures", []), js.setdefault("samplers", [])
    samps.append({"magFilter": 9729, "minFilter": 9987, "wrapS": 33071, "wrapT": 33071})
    si = len(samps) - 1
    mat = dict(js["materials"][pr["material"]])
    pbr = dict(mat.get("pbrMetallicRoughness", {}))
    for key, png in maps.items():
        with open(png, "rb") as f:
            data = f.read()
        imgs.append({"bufferView": out.view(data), "mimeType": "image/png", "name": os.path.basename(png)})
        texs.append({"source": len(imgs) - 1, "sampler": si})
        ti = {"index": len(texs) - 1}
        if key == "baseColor":
            pbr["baseColorTexture"] = ti
        elif key == "metallicRoughness":
            pbr["metallicRoughnessTexture"] = ti
            pbr["roughnessFactor"] = 1.0
            pbr["metallicFactor"] = 1.0
        elif key == "normal":
            mat["normalTexture"] = ti
        else:
            raise ValueError(key)
    mat["pbrMetallicRoughness"] = pbr
    js["materials"].append(mat)
    pr["material"] = len(js["materials"]) - 1
    while len(out.bin) % 4:
        out.bin += b"\0"
    js["buffers"][0]["byteLength"] = len(out.bin)
    j = json.dumps(js, separators=(",", ":")).encode()
    j += b" " * ((4 - len(j) % 4) % 4)
    blob = (struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(j) + 8 + len(out.bin)) + struct.pack("<II", len(j), 0x4E4F534A)
            + j + struct.pack("<II", len(out.bin), 0x004E4942) + bytes(out.bin))
    with open(out_path or path, "wb") as f:
        f.write(blob)


def get_targets(path, node):
    """The blend shapes on one mesh's primitive 0 of a glb we wrote: {name: (dP [V,3], dN [V,3])} in order."""
    js, b = _read_glb(path)
    mi = next(n["mesh"] for n in js["nodes"] if n.get("name") == node and "mesh" in n)
    m = js["meshes"][mi]
    pr = m["primitives"][0]
    names = m.get("extras", {}).get("targetNames", [])
    out = {}

    def arr(ai):
        a = js["accessors"][ai]
        v = js["bufferViews"][a["bufferView"]]
        off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        return np.frombuffer(b, np.float32, a["count"] * 3, off).reshape(-1, 3).copy()
    for nm, t in zip(names, pr.get("targets", [])):
        out[nm] = (arr(t["POSITION"]), arr(t["NORMAL"]) if "NORMAL" in t else np.zeros((js["accessors"][t["POSITION"]]["count"], 3), np.float32))
    return out


def add_targets(path, node, targets):
    """set_targets with the mesh's present shapes kept (new names after them; a name already there is replaced)."""
    have = get_targets(path, node)
    have.update(targets)
    set_targets(path, node, have)
