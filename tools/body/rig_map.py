"""B's rig as the clean target for new motion (A1 Stage B: MotionBricks + Kimodo on SOMA), written as data.

    python tools/body/rig_map.py [--glb godot/art/people/body_p1/body.glb] [--rig .../rig.json]
                                 [--soma C:/Users/munch/Tools/mocap/kimodo/bow_0.bvh]

Writes (both deterministic, from the published B and one SOMA BVH's hierarchy; no motion is read):
  tools/body/rig/b_skeleton.json  every B bone: parent, rest head and axes in skeleton space (glTF: +Y up, +Z her
                                  front, +X her left; meters), its length, its class (keyed: a clip writes it;
                                  law: B's girdle law sets it, clips leave it at rest; helper: P1Rig sets it from
                                  rig.json "helpers"; carried: rides its parent at rest (leaf ends, breast tips);
                                  spring: the breasts, set by their springs), and the roll convention as
                                  measured (which local axis runs along the bone, which is its hinge).
  tools/body/rig/soma_to_b.json   for each keyed B bone, its SOMA source: one joint (by name), or for B's five-bone
                                  spine a slerp between the two SOMA joints whose segment midpoints bracket the B
                                  bone's (a slerp of their GLOBAL turns from rest, as P1Retarget's chain rule) along the chain pelvis -> neck base (SOMA Hips..Neck1: three spine joints,
                                  the Chest spanning the thorax; B spine_01..05). Each entry has the aim line (the
                                  B bone's own head -> child, the SOMA joint -> joint that runs the same way) for a
                                  rest calibration, as tools/anim/retarget.py's maps do. SOMA's Jaw, eyes and End
                                  sites have no B bone (the head's face rig is R3's).
The rule for a clip on B (the bake from A's clips and any rebuilt clip): key the "keyed" bones only; the clavicle and
scapula come from the girdle law (rig.json "girdle", driven by the arm: a clip's own clavicle turn is not played, the
upper arm's world aim is), helpers from P1Rig. Derivation: (a) the owner, 5 Nov: "a fresh well built thing instead
of our frankenstein"; B's rig is the target new motion is made on, so it is stated once as data.
"""
from __future__ import annotations

import argparse
import json
import os
import struct

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
LAW = {"clavicle_l", "clavicle_r", "scap_l", "scap_r"}
SPINE_B = ["spine_01", "spine_02", "spine_03", "spine_04", "spine_05"]
SPINE_S = ["Hips", "Spine1", "Spine2", "Chest"]          # SOMA joints whose segments run pelvis -> Neck1


def glb_json(p):
    b = open(p, "rb").read()
    n = struct.unpack("<I", b[12:16])[0]
    return json.loads(b[20:20 + n])


def quat_m(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def b_rest(glb):
    j = glb_json(glb)
    nodes = j["nodes"]
    par = {c: i for i, nd in enumerate(nodes) for c in nd.get("children", [])}
    W = {}

    def w(i):
        if i not in W:
            nd = nodes[i]
            M = np.eye(4)
            M[:3, :3] = quat_m(nd.get("rotation", [0, 0, 0, 1])) * np.array(nd.get("scale", [1, 1, 1]))
            M[:3, 3] = nd.get("translation", [0, 0, 0])
            W[i] = (w(par[i]) @ M) if i in par else M
        return W[i]
    joints = j["skins"][0]["joints"]
    names = [nodes[i]["name"] for i in joints]
    jset = set(joints)
    parent = [nodes[par[i]]["name"] if i in par and par[i] in jset else None for i in joints]
    # (skeleton space: the skin's joints relative to the first joint's parent, the armature node)
    base = np.linalg.inv(w(par[joints[0]])) if joints[0] in par else np.eye(4)
    worlds = [base @ w(i) for i in joints]
    return names, parent, worlds


def soma_hier(bvh):
    names, parent, off, stack = [], [], [], []
    for line in open(bvh):
        t = line.split()
        if not t:
            continue
        if t[0] in ("ROOT", "JOINT"):
            names.append(t[1]); parent.append(stack[-1] if stack else None)
        elif t[0] == "End":
            names.append(None); parent.append(stack[-1])
        elif t[0] == "{":
            stack.append(len(names) - 1)
        elif t[0] == "}":
            stack.pop()
        elif t[0] == "OFFSET":
            off.append(np.array([float(v) for v in t[1:4]]) / 100.0)   # cm -> m
        elif t[0] == "MOTION":
            break
    pos = []
    for i in range(len(names)):
        pos.append(off[i] + (pos[parent[i]] if parent[i] is not None else 0))
    return {n: (p, names[parent[i]] if parent[i] is not None else None) for i, (n, p) in enumerate(zip(names, pos)) if n}


def chain_fracs(pts):
    """Each segment's midpoint as a fraction of the chain's arc length."""
    seg = [np.linalg.norm(pts[k + 1] - pts[k]) for k in range(len(pts) - 1)]
    tot, acc, out = sum(seg), 0.0, []
    for s in seg:
        out.append((acc + s / 2) / tot); acc += s
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--glb", default=os.path.join(REPO, "godot/art/people/body_p1/body.glb"))
    ap.add_argument("--rig", default=os.path.join(REPO, "godot/art/people/body_p1/rig.json"))
    ap.add_argument("--soma", default=r"C:/Users/munch/Tools/mocap/kimodo/bow_0.bvh")
    a = ap.parse_args(argv)
    names, parent, worlds = b_rest(a.glb)
    rig = json.load(open(a.rig))
    helpers = set()
    for h in rig.get("helpers", []):
        if h["kind"] == "unroll":
            continue
        for s in ("l", "r"):
            helpers.add(h["name"].replace("{s}", s))
    idx = {n: i for i, n in enumerate(names)}
    kids = {n: [c for c, p in zip(names, parent) if p == n] for n in names}

    def cls(n):
        if n in LAW:
            return "law"
        if n in helpers:
            return "helper"
        if n.startswith("breast_tip") or "_leaf_" in n:
            return "carried"
        if n.startswith("breast_"):
            return "spring"      # HerJiggle's, a placeholder until R1's breast forms set the bone and its spring
        return "keyed"

    def main_child(n):
        ks = [k for k in kids[n] if cls(k) == "keyed"]
        pref = [k for k in ks if not k.startswith(("thumb", "index", "ring", "pinky")) or n.startswith(("thumb", "index", "middle", "ring", "pinky"))]
        if n.startswith("hand_"):
            pref = [k for k in ks if k.startswith("middle")]
        return (pref or ks or [None])[0]

    bones = []
    for i, n in enumerate(names):
        M = worlds[i]
        R = M[:3, :3] / np.linalg.norm(M[:3, :3], axis=0)
        ch = main_child(n)
        along = None
        if ch:
            d = worlds[idx[ch]][:3, 3] - M[:3, 3]
            if np.linalg.norm(d) > 1e-6:
                loc = R.T @ (d / np.linalg.norm(d))
                k = int(np.argmax(np.abs(loc)))
                along = ("+" if loc[k] > 0 else "-") + "xyz"[k]
        bones.append({"name": n, "parent": parent[i], "class": cls(n), "head": np.round(M[:3, 3], 5).tolist(),
                      "axes": np.round(R.T, 5).tolist(), "child": ch,
                      "length": round(float(np.linalg.norm(worlds[idx[ch]][:3, 3] - M[:3, 3])), 5) if ch else None,
                      "along": along})
    hinge = rig.get("hinge", {})
    out_dir = os.path.join(HERE, "rig")
    os.makedirs(out_dir, exist_ok=True)
    doc = {"about": __doc__.split("\n\n")[0], "space": "skeleton space, glTF: +Y up, +Z her front, +X her left, meters; "
           "axes rows = the bone's local x, y, z in skeleton space",
           "roll": "measured per bone ('along': the local axis that runs head -> main child); "
                   f"rig.json hinge {json.dumps(hinge)}", "source_glb": os.path.relpath(a.glb, REPO).replace("\\", "/"),
           "bones": bones}
    json.dump(doc, open(os.path.join(out_dir, "b_skeleton.json"), "w"), indent=1)

    S = soma_hier(a.soma)
    m = {}
    # spine by chain fraction (B pelvis -> neck_01 against SOMA Hips -> Neck1)
    bpts = [worlds[idx[n]][:3, 3] for n in ["pelvis"] + SPINE_B + ["neck_01"]]
    spts = [S[n][0] for n in SPINE_S + ["Neck1"]]
    fb, fs = chain_fracs(bpts)[1:], chain_fracs(spts)
    for n, f in zip(SPINE_B, fb):
        k = max([q for q in range(len(fs)) if fs[q] <= f] or [0])
        k2 = min(k + 1, len(fs) - 1)
        t = 0.0 if k2 == k else (f - fs[k]) / (fs[k2] - fs[k])
        t = float(np.clip(t, 0, 1))
        m[n] = {"slerp": [SPINE_S[k], SPINE_S[k2], round(t, 4)], "frac": round(float(f), 4)}
    one = {"root": "Root", "pelvis": "Hips", "neck_01": "Neck1", "neck_02": "Neck2", "Head": "Head"}
    for s, S_ in (("l", "Left"), ("r", "Right")):
        one.update({f"clavicle_{s}": f"{S_}Shoulder", f"upperarm_{s}": f"{S_}Arm", f"lowerarm_{s}": f"{S_}ForeArm",
                    f"hand_{s}": f"{S_}Hand", f"thigh_{s}": f"{S_}Leg", f"calf_{s}": f"{S_}Shin",
                    f"foot_{s}": f"{S_}Foot", f"ball_{s}": f"{S_}ToeBase"})
        for f, F in (("index", "Index"), ("middle", "Middle"), ("ring", "Ring"), ("pinky", "Pinky")):
            one[f"{f}_metacarpal_{s}"] = f"{S_}Hand{F}1"
            for k in (1, 2, 3):
                one[f"{f}_0{k}_{s}"] = f"{S_}Hand{F}{k + 1}"
        for k in (1, 2, 3):
            one[f"thumb_0{k}_{s}"] = f"{S_}HandThumb{k}"
    soma_child = {}
    for n, (p, par) in S.items():
        if par is not None:
            soma_child.setdefault(par, n)
    for n, j in one.items():
        if n not in idx:
            continue
        e = {"joint": j}
        if cls(n) == "law":
            e["note"] = "law-driven: the girdle law sets it from the arm; a clip's own turn here is not played"
        m[n] = e
    for n, e in m.items():
        b = bones[idx[n]]
        e["aim_b"] = [n, b["child"]]
        if "joint" in e and e["joint"] in S:
            e["aim_soma"] = [e["joint"], soma_child.get(e["joint"])]
    unmapped = [b["name"] for b in bones if b["class"] == "keyed" and b["name"] not in m]
    soma_unused = [n for n in S if n not in {e.get("joint") for e in m.values()} and n not in SPINE_S
                   and not n.endswith("End") and n != "Neck1"]
    doc2 = {"about": "SOMA (Kimodo / MotionBricks, 77 joints) -> B's keyed bones. tools/body/rig_map.py; see its docstring.",
            "soma_source": a.soma, "map": m, "b_keyed_unmapped": unmapped, "soma_unused": soma_unused}
    json.dump(doc2, open(os.path.join(out_dir, "soma_to_b.json"), "w"), indent=1)
    print(f"b_skeleton.json: {len(bones)} bones ({sum(b['class'] == 'keyed' for b in bones)} keyed, "
          f"{sum(b['class'] == 'law' for b in bones)} law, {sum(b['class'] == 'helper' for b in bones)} helper); "
          f"soma_to_b.json: {len(m)} mapped; B keyed unmapped {unmapped}; SOMA unused {soma_unused}")
    print("spine:", {n: m[n]["slerp"] for n in SPINE_B})


if __name__ == "__main__":
    main()
