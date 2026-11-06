"""Stage 4: tools/body/skeleton.json placed on a MakeHuman body (any slider body: the landmarks are MakeHuman's).

    place_skeleton(skel_json, base, mh_rig, mh_weights, to_world) -> (names, parents, worlds [B,4,4] glTF, ends {name: (head, tail)}, info)
base: stage 1's arrays (MakeHuman space); mh_rig: MPFB's rigs/standard/rig.default.json (its head/tail rules);
mh_weights: weights.default.json "weights"; to_world(P_mh) -> glTF points (the placement, stage 2/3).
Only the left side is placed; the right is its true mirror (x -> -x; Y and Z mirrored, X = Y x Z), and the middle's
bones sit on x = 0 exactly.
"""
import numpy as np

UP, FRONT, LEFT = np.array([0.0, 1, 0]), np.array([0.0, 0, 1]), np.array([1.0, 0, 0])     # glTF: y up, front +z
MH_DIR = {"lateral": np.array([1.0, 0, 0]), "up": np.array([0.0, 0, 1]), "front": np.array([0.0, -1, 0]),
          "back": np.array([0.0, 1, 0])}                                                     # MakeHuman (z up, front -y), her left


def unit(v):
    v = np.asarray(v, float)
    return v / max(np.linalg.norm(v), 1e-12)


def perp(v, n):
    return unit(v - n * (v @ n))


def expand(x, s, S, X):
    if isinstance(x, str):
        return x.replace("{s}", s).replace("{S}", S).replace("{X}", X)
    if isinstance(x, list):
        return [expand(y, s, S, X) for y in x]
    if isinstance(x, dict):
        return {k: expand(v, s, S, X) for k, v in x.items()}
    return x


class Landmarks:
    """Points in MakeHuman space by skeleton.json's rules."""

    def __init__(self, base, mh_rig, mh_weights):
        self.V, self.g, self.rig, self.w = base["V"], base["groups"], mh_rig, mh_weights
        self.skin = self.V[base["inbody"]]

    def mh_end(self, bone, end):
        r = self.rig[bone][end]
        st = r["strategy"]
        if st == "CUBE":
            return self.cube(r["cube_name"])
        if st == "MEAN":
            return self.V[r["vertex_indices"]].mean(0)
        if st == "VERTEX":
            return self.V[r["vertex_index"]]
        raise ValueError(st)

    def cube(self, name):
        return self.V[self.g[name]].mean(0)

    def point(self, p):
        if "cube" in p:
            return self.cube(p["cube"])
        if "mh" in p:
            return self.mh_end(p["mh"], p["end"])
        if "mean" in p:
            return np.mean([self.point(q) for q in p["mean"]], 0)
        if "lerp" in p:
            a, b, t = p["lerp"]
            return (1 - t) * self.point(a) + t * self.point(b)
        if "origin" in p:
            return None
        if "skin_out" in p:
            q, way = p["skin_out"]
            o = self.point(q)
            d = MH_DIR[way].copy()
            if way == "lateral" and o[0] < 0:
                d = -d
            rel = self.skin - o
            along = rel @ d
            off = np.linalg.norm(rel - along[:, None] * d, axis=1)
            m = (off < 0.02) & (along > 0)
            return o + d * along[m].max()
        if "weights_base" in p:
            ww = dict((int(i), float(x)) for i, x in self.w[p["weights_base"]])
            idx = np.array([i for i, x in ww.items() if 0.05 < x < 0.35])
            return self.V[idx].mean(0)
        if any(k in p for k in ANAT_RULES):
            raise ValueError(("an anatomical rule runs on OUR topology only (place_skeleton_ours)", p))
        raise ValueError(p)


def place_skeleton(skel, base, mh_rig, mh_weights, to_world):
    lm = Landmarks(base, mh_rig, mh_weights)
    defs = skel["bones"]
    # the left side (and the middle), in MakeHuman space
    ends = {}
    for d in defs:
        e = expand(d, "l", "l", "L")
        if d.get("leaf"):
            continue
        ends[e["name"]] = [lm.point(e["head"]), lm.point(e["tail"])]
    # to the world (glTF)
    W = {}
    for n, (h, t) in ends.items():
        W[n] = [np.zeros(3) if h is None else to_world(h[None])[0], to_world(t[None])[0]]
    return _place_from_world(defs, W)


# ------------------------------------------------------------------------ anatomical rules (P1 skel round) --
# Rules that run on OUR body (and her approved head) at placement time, each from a named reference; they replace
# MakeHuman landmarks that put a joint off its anatomy (undone: inherited from MakeHuman). README "skeleton".
ANAT_RULES = ("harrington", "cervical", "occiput", "crown", "knee_tea", "spine_body")
MM = 0.001
_TOPO, _HEAD = {}, {}


def topo_for(n):
    """Our topology's arrays (out/topo/<tier>.npz) for a body of n vertices (part, side, parts)."""
    import os
    if n not in _TOPO:
        here = os.path.dirname(os.path.abspath(__file__))
        for tier in ("close", "play"):
            z = np.load(os.path.join(here, "out", "topo", f"{tier}.npz"), allow_pickle=True)
            _TOPO[len(z["V"])] = {k: z[k] for k in ("part", "side", "parts", "Q")}
    return _TOPO[n]


def head_points():
    """Her approved head (godot/art/people/heroine.glb HeroineHead) at its baked world rest (headbake.py), glTF m."""
    import os
    if "P" not in _HEAD:
        import headbake
        from gl import Glb
        here = os.path.dirname(os.path.abspath(__file__))
        A = Glb(os.path.join(os.path.dirname(os.path.dirname(here)), "godot", "art", "people", "heroine.glb"))
        _HEAD["P"] = headbake.bake(A, ["HeroineHead"])["HeroineHead"]["P"]
    return _HEAD["P"]


def _slab(V, y, half):
    return np.abs(V[:, 1] - y) < half


def harrington_hjc(V, topo, y_keep, r):
    """The left hip joint centre by Harrington et al. 2007 (J Biomech 40:595, the width/depth regression; pelvic
    frame: origin the mid-ASIS, ap = mid-PSIS -> mid-ASIS, ml = her left, up = ap x ml):
        hjc = mid_ASIS + (0.33 PW + 7.3 mm) ml + (-0.30 PW - 10.9 mm) up + (-0.24 PD - 9.9 mm) ap
    PW = the inter-ASIS width, PD = the mid-ASIS to mid-PSIS depth, both bony. Our skin landmarks (left; the right
    is the mirror, so the mids sit on x = 0):
      ASIS: on the trunk's front-left skin at height y_A, the support point toward r["asis_azimuth_deg"] off the
            front (the section's front-lateral corner: the ASIS is the pelvis's front-lateral point);
      PSIS: the trunk's back skin at x = r["psis_x_m"] (the dimples; only the mid-PSIS enters, so its x does not),
            at the height that tilts the ASIS-PSIS line r["tilt_deg"] up toward the back (standing pelvic tilt);
      skin -> bone along ap by r["soft_asis_m"] / r["soft_psis_m"].
    y_A is solved so the joint keeps y_keep (the inherited height, which the trochanter check and Harrington's own
    vertical term both confirm within 5 mm: README "skeleton"). Returns (hjc, info)."""
    part, side, parts = topo["part"], topo["side"], list(topo["parts"])
    tr = (part == parts.index("trunk")) & (side == 1)
    front, back = V[tr & (V[:, 2] > 0)], V[tr & (V[:, 2] < -0.03)]
    a = np.radians(r["asis_azimuth_deg"])
    dirA = np.array([np.sin(a), 0.0, np.cos(a)])
    t = np.tan(np.radians(r["tilt_deg"]))
    yA = y_keep + 0.085
    for _ in range(40):
        half = 0.010                                      # a soft support point (continuous in y_A on either
        while _slab(front, yA, half).sum() < 6:          # tier): a tent over +-10 mm of height times a softmax
            half *= 1.5                                   # (3 mm) of the reach toward the azimuth
        s = front[_slab(front, yA, half)]
        g = s @ dirA
        w = (1.0 - np.abs(s[:, 1] - yA) / half) * np.exp((g - g.max()) / 0.003)
        A = w @ s / w.sum()
        A[1] = yA
        yP = yA + 0.035
        for _ in range(10):
            d = np.hypot(back[:, 0] - r["psis_x_m"], back[:, 1] - yP)
            near = d < max(0.008, np.sort(d)[3] + 1e-6)     # at least 4 points (play)
            w = 1.0 / (d[near] + 1e-4)
            zP = float(w @ back[near, 2] / w.sum())
            yP = yA + t * (A[2] - zP)
        M, Pm = np.array([0.0, yA, A[2]]), np.array([0.0, yP, zP])
        ap = (M - Pm) / np.linalg.norm(M - Pm)
        Mb, Pb = M - r["soft_asis_m"] * ap, Pm + r["soft_psis_m"] * ap
        PW, PD = 2.0 * A[0], float(np.linalg.norm(Mb - Pb))
        up = np.cross(ap, LEFT)
        h = Mb + (0.33 * PW + 7.3 * MM) * LEFT + (-0.30 * PW - 10.9 * MM) * up + (-0.24 * PD - 9.9 * MM) * ap
        if abs(h[1] - y_keep) < 1e-5:
            break
        yA += 0.7 * (y_keep - h[1])
    assert abs(h[1] - y_keep) < 1e-4, ("harrington: the ASIS height did not settle", h[1], y_keep)
    info = {"asis_skin_mm": np.round(A / MM, 1).tolist(), "psis_mid_skin_mm": np.round(Pm / MM, 1).tolist(),
            "PW_mm": round(PW / MM, 1), "PD_mm": round(PD / MM, 1), "hjc_mm": np.round(h / MM, 1).tolist()}
    return h, info


def _midline_profile(V, sign, y0, y1, step=0.002):
    """The midline skin's z per height (min z behind, max z in front) over |x| < 6 mm, in 2 mm bins, the empty bins
    (play's coarser rows) interpolated: a uniform profile on either tier."""
    m = (np.abs(V[:, 0]) < 0.006) & (np.sign(V[:, 2]) == sign) & (V[:, 1] >= y0) & (V[:, 1] < y1)
    P = V[m]
    ys = np.arange(y0, y1, step)
    b = np.clip(((P[:, 1] - y0) / step).astype(int), 0, len(ys) - 1)
    zs = np.full(len(ys), np.nan)
    for i in range(len(ys)):
        q = P[b == i, 2]
        if len(q):
            zs[i] = q.min() if sign < 0 else q.max()
    ok = ~np.isnan(zs)
    return ys, np.interp(ys, ys[ok], zs[ok])


C7_BAND_BELOW_TOP_M = (0.22, 0.12)   # C7's allowed height: 120-220 mm below the body's top (the head ring); her C7 is 170 mm
                                     # below it (ANSUR II cervicale/stature ~0.857). The skull base is far above this band.


def cervical_joint(V, r):
    """neck_01's head, the C7/T1 joint. The cervicale (C7's spinous process, the vertebra prominens) is the nape's
    corner on the back midline: where the upper back's forward slope turns into the neck's back line. Rule: the back
    midline profile z(y) from the upper back's furthest-back point to the body's top (the head ring) less 4 mm, fitted
    by a degree-6 polynomial (rms 0.3 mm on either tier; a discrete curvature pick jumped 10 mm between the tiers),
    and its point farthest in front of the chord between those ends (the curve's knee). The joint is in front of it at
    the C7 body: r["depth"] of the horizontal midline depth (throat skin - nape skin) forward of the back skin (the
    cervical bodies sit just behind the neck's middle: the airway and larynx fill its front). Cross-check: ANSUR II
    women's cervicale height / stature ~0.857 (README "skeleton").
    Bounded: the knee is only accepted inside the band C7_BAND_BELOW_TOP_M (120-220 mm under the top). Where the
    curve has no clear knee (the chord-distance maximum falls outside the band, as on her smooth nape, where a 0.1 mm
    wobble near the neck's top moved it 16 cm) or the throat sampling at the knee would be empty, the joint takes the
    nape's deepest point (minimum z) inside the band, and info["cervical_fallback"] names the reason."""
    top = V[:, 1].max()
    yb, zb = _midline_profile(V, -1, top - 0.30, top - 0.004)
    i0 = int(np.argmin(zb))
    y0 = yb[i0]
    c6 = np.polyfit(yb[i0:] - y0, zb[i0:], 6)
    g = np.arange(y0, yb[-1], 0.0005)
    f = np.polyval(c6, g - y0)
    j = int(np.argmax(f - (f[0] + (g - g[0]) / (g[-1] - g[0]) * (f[-1] - f[0]))))
    band = (g >= top - C7_BAND_BELOW_TOP_M[0]) & (g <= top - C7_BAND_BELOW_TOP_M[1])
    why = None
    if not band.any():
        why = "band_outside_profile"
    elif not band[j]:
        why = "no_knee_in_band"
    if why is None:
        y = float(g[j])
        if not _throat_has_points(V, y):
            why = "empty_throat_sample"
    if why is not None:
        if band.any():
            jb = np.flatnonzero(band)
            j = int(jb[np.argmin(f[jb])])
        else:
            j = int(np.argmin(np.abs(g - (top - 0.17))))
    y, zback = float(g[j]), float(f[j])
    yf, zf = _midline_profile(V, 1, y - 0.008, y + 0.008)
    zfront = float(np.interp(y, yf, zf))
    p = np.array([0.0, y, zback + r["depth"] * (zfront - zback)])
    info = {"cervicale_skin_mm": [0.0, round(y / MM, 1), round(zback / MM, 1)],
            "throat_skin_z_mm": round(zfront / MM, 1), "joint_mm": np.round(p / MM, 1).tolist()}
    if why:
        info["cervical_fallback"] = why
    return p, info


def _throat_has_points(V, y):
    m = (np.abs(V[:, 0]) < 0.006) & (V[:, 2] > 0) & (V[:, 1] >= y - 0.008) & (V[:, 1] < y + 0.008)
    return bool(m.any())


def occiput_joint(H, r):
    """Head's head, the atlanto-occipital joint (the occipital condyles), from her approved head mesh H: midline, at
    the earlobe's level, under the ear (below and just in front of the mastoid, which lies behind the lobe). The ear
    = her left head points within r["ear_band_m"] of the head's widest left point (the helix); the joint's height =
    the ear's lowest point (the lobe), its depth = the ear's mean z."""
    L = H[H[:, 0] > 0]
    ear = L[L[:, 0] > L[:, 0].max() - r["ear_band_m"]]
    p = np.array([0.0, float(ear[:, 1].min()), float(ear[:, 2].mean())])
    return p, {"ear_y_mm": [round(ear[:, 1].min() / MM, 1), round(ear[:, 1].max() / MM, 1)],
               "ear_z_mm": [round(ear[:, 2].min() / MM, 1), round(ear[:, 2].max() / MM, 1)],
               "joint_mm": np.round(p / MM, 1).tolist()}


# Grünwald et al. 2024 (BMC Med Imaging 24:110, doi 10.1186/s12880-024-01293-6) Table 1, the "mild" (least deformed)
# group: the vertebral body centre -> the spinous process tip, transverse (mm), T1..T12, L1..L5. The paper: this
# distance is "rather similar across different patients of the same gender" (the skin distance is not).
GRUNWALD_L12_MM = [65, 63, 59, 57, 56, 55, 55, 58, 59, 60, 60, 62, 68, 71, 73, 73, 68]
GRAYS_LUMBAR = 18.0 / (18.0 + 28.0)       # Gray's Anatomy: the thoracic column ~28 cm, the lumbar ~18 cm


def spine_body_joint(V, y, y0, y1, r):
    """A spine joint's depth: the vertebral column's centre line behind the midline back skin at the joint's
    (inherited) height y. Level: s = (y - y0) / (y1 - y0) from L5/S1 (y0, the pelvis joint) to C7/T1 (y1, the cervical
    rule), the lumbar the lowest GRAYS_LUMBAR of it, five equal levels, the thoracic twelve; each body's centre at its
    level's middle. Depth = the back skin (midline, max behind) + soft tissue over the spinous tips r["soft_m"] (a lean
    young woman: (a) an estimate, 1:1 sensitivity) + Grünwald's body centre -> spinous tip at s (linear between the
    levels' centres, held past L5's and T1's). Smooth by construction (the skin is; the table is): lordosis and
    kyphosis are her back's own curve."""
    s = (y - y0) / (y1 - y0)
    sl = [(4.5 - k) / 5 * GRAYS_LUMBAR for k in range(5)]                  # L1..L5 body centres (L1 highest)
    st = [GRAYS_LUMBAR + (11.5 - k) / 12 * (1 - GRAYS_LUMBAR) for k in range(12)]   # T1..T12
    ss = np.array(st + sl)
    d = float(np.interp(s, ss[::-1], np.array(GRUNWALD_L12_MM, float)[::-1])) * MM
    yb, zb = _midline_profile(V, -1, y - 0.012, y + 0.012)
    zback = float(np.interp(y, yb, zb))
    p = np.array([0.0, y, zback + r["soft_m"] + d])
    return p, {"s": round(s, 3), "spinous_to_body_mm": round(d / MM, 1), "back_skin_z_mm": round(zback / MM, 1),
               "joint_mm": np.round(p / MM, 1).tolist()}


def _plane_section(V, Q, keep, o, n):
    """The points where our quads' edges (all four vertices in keep) cross the plane (o, n): a section that is
    continuous on either tier."""
    Qk = Q[keep[Q].all(1)]
    E = np.concatenate([Qk[:, [0, 1]], Qk[:, [1, 2]], Qk[:, [2, 3]], Qk[:, [3, 0]]])
    h = (V - o) @ n
    a, b = h[E[:, 0]], h[E[:, 1]]
    m = (a * b < 0)
    t = a[m] / (a[m] - b[m])
    return V[E[m, 0]] + t[:, None] * (V[E[m, 1]] - V[E[m, 0]])


def knee_tea_joint(V, topo, k0, hip, ankle, back_frac=0.5):
    """The knee's flexion axis centre: the midpoint of the femoral epicondyles ((b) Grood & Suntay 1983 / ISB, Wu et
    al. 2002: the knee joint centre; Churchill et al. 1998: the transepicondylar axis approximates the knee's flexion
    axis). On our skin: the epicondyles are the knee's medial and lateral extremes at the joint line, and they sit at
    the knee's mid-depth (surface anatomy: palpated at the middle of the knee's side, between the patella's edge and
    the hamstring tendons). Rule: the left leg's section (thigh, knee, shin) by the plane through the inherited joint
    (its height kept, (c)) normal to the leg axis hip -> ankle; the joint = the section's centre (mid of its medial /
    lateral and its front / back extremes in that plane)."""
    part, side, parts = topo["part"], topo["side"], list(topo["parts"])
    keep = np.isin(part, [parts.index(x) for x in ("thigh", "knee", "shin")]) & (side == 1)
    n = unit(ankle - hip)
    S = _plane_section(V, topo["Q"], keep, k0, n)
    ex, ez = unit(perp(LEFT, n)), unit(perp(FRONT, n))
    u, w = (S - k0) @ ex, (S - k0) @ ez
    p = k0 + ex * (u.max() + u.min()) / 2 + ez * (w.min() + back_frac * (w.max() - w.min()))
    return p, {"section_pts": int(len(S)), "width_mm": round((u.max() - u.min()) / MM, 1),
               "depth_mm": round((w.max() - w.min()) / MM, 1), "inherited_mm": np.round(k0 / MM, 1).tolist(),
               "joint_mm": np.round(p / MM, 1).tolist()}


class OurLandmarks:
    """skeleton.json's points on OUR vertices (P1 B1): each atomic rule (cube / mh / weights_base, keyed by its
    canonical json) is landmarks.json's sparse weighted sum of our vertices (landmarks_fit.py); skin_out is its rule
    run on our skin (its inner point from the table); mean and lerp compose them in our frame (glTF); origin is none.
    No MakeHuman data at placement time."""

    def __init__(self, V, table, head=None):
        self.V, self.t, self.head = np.asarray(V, float), table, head
        self.info = {}

    def _head(self):
        return head_points() if self.head is None else np.asarray(self.head, float)

    def point(self, p):
        if "origin" in p:
            return None
        if any(k in p for k in ANAT_RULES):              # each anatomical rule once per placement
            import json
            kk = json.dumps(p, sort_keys=True)
            if kk not in self.info.setdefault("_memo", {}):
                self.info["_memo"][kk] = self._anat(p)
            return self.info["_memo"][kk]
        return self._table_point(p)

    def _anat(self, p):
        if "harrington" in p:
            r = p["harrington"]
            h, self.info["harrington"] = harrington_hjc(self.V, topo_for(len(self.V)), self.point(r["height"])[1], r)
            return h
        if "cervical" in p:
            c, self.info["cervical"] = cervical_joint(self.V, p["cervical"])
            return c
        if "occiput" in p:
            c, self.info["occiput"] = occiput_joint(self._head(), p["occiput"])
            return c
        if "knee_tea" in p:
            r = p["knee_tea"]
            c, self.info["knee_tea"] = knee_tea_joint(self.V, topo_for(len(self.V)), self.point(r["height"]),
                                                      self.point(r["hip"]), self.point(r["ankle"]),
                                                      r.get("back_frac", 0.5))
            return c
        if "spine_body" in p:
            r = p["spine_body"]
            y = float(self.point(r["height"])[1])
            c, i = spine_body_joint(self.V, y, float(self.point(r["base"])[1]), float(self.point(r["top"])[1]), r)
            import json
            self.info.setdefault("spine_body", {})[json.dumps(r["height"])] = i
            return c
        if "crown" in p:                                  # the head's top (the vertex), on the midline
            H = self._head()
            return np.array([0.0, float(H[:, 1].max()), float(H[np.argmax(H[:, 1]), 2])])

    def _table_point(self, p):
        if "mean" in p:
            return np.mean([self.point(q) for q in p["mean"]], 0)
        if "lerp" in p:
            a, b, t = p["lerp"]
            return (1 - t) * self.point(a) + t * self.point(b)
        import json
        r = self.t.get(json.dumps(p, sort_keys=True, separators=(",", ":")))
        if r is None and "skin_out" in p:                 # a skin_out on a new inner point: the rule as it is
            r = {"rule": "skin_out"}
        if r.get("rule") == "skin_out":                  # the rule itself, on our skin (glTF directions)
            q, way = p["skin_out"]
            o = self.point(q)
            d = {"lateral": LEFT, "up": UP, "front": FRONT, "back": -FRONT}[way].copy()
            if way == "lateral" and o[0] < 0:
                d = -d
            rel = self.V - o
            along = rel @ d
            off = np.linalg.norm(rel - along[:, None] * d, axis=1)
            m = (off < r.get("tube_m", 0.02)) & (along > 0)
            return o + d * along[m].max()
        return np.asarray(r["w"]) @ self.V[r["ids"]]


def place_skeleton_ours(skel, V, table, head=None):
    """place_skeleton on OUR vertices V (glTF, our topology's order) with landmarks.json's table for that tier
    (tools/body/base/landmarks.json "tiers"[tier]); the same returns; info["anatomy"] = the anatomical rules' points.
    head: her baked head mesh's points (glTF m; default: headbake.py on heroine.glb)."""
    lm = OurLandmarks(V, table, head)
    defs = skel["bones"]
    W = {}
    for d in defs:
        if d.get("leaf"):
            continue
        e = expand(d, "l", "l", "L")
        h = lm.point(e["head"])
        W[e["name"]] = [np.zeros(3) if h is None else h, lm.point(e["tail"])]
    out = _place_from_world(defs, W)
    out[4]["anatomy"] = {k: v for k, v in lm.info.items() if k != "_memo"}
    return out


def _place_from_world(defs, W):
    """The left side's (and the middle's) bone ends in the world (glTF) -> the skeleton: leaves, frames, mirror."""
    for n, (hw, tw) in W.items():
        hw, tw = np.array(hw, float), np.array(tw, float)
        W[n] = [hw, tw]
        if not n.endswith("_l"):
            hw[0] = 0.0
            tw[0] = 0.0
        W[n] = [hw, tw]
    for d in defs:
        if d.get("leaf"):
            e = expand(d, "l", "l", "L")
            ph, pt = W[e["parent"]]
            W[e["name"]] = [pt, pt + (pt - ph) / 3.0]
    # frames
    ya = unit(W["upperarm_l"][1] - W["upperarm_l"][0])
    yb = unit(W["lowerarm_l"][1] - W["lowerarm_l"][0])
    hinge = unit(np.cross(yb, -ya))                 # flexion (+X) takes the forearm toward the upper arm
    bend = float(np.degrees(np.arccos(np.clip(ya @ yb, -1, 1))))
    hand_y = unit(W["hand_l"][1] - W["hand_l"][0])

    def curl(chain):
        """The direction a finger's rest curl turns it (toward the palm)."""
        v = []
        for a, b in zip(chain, chain[1:]):
            y1, y2 = unit(W[a][1] - W[a][0]), unit(W[b][1] - W[b][0])
            v.append(y2 - y1 * (y1 @ y2))
        return unit(np.sum(v, 0))
    palm = unit(np.sum([curl([f"{f}_01_l", f"{f}_02_l", f"{f}_03_l"]) for f in ("index", "middle", "ring", "pinky")], 0))
    thumb = curl(["thumb_01_l", "thumb_02_l", "thumb_03_l"])

    def frame(d, Y):
        kind = d["frame"]
        if kind == "elbow_upper":
            X = perp(hinge, Y)
            return X, np.cross(X, Y)
        if kind == "elbow_lower":
            X = perp(hinge, Y)
            return X, np.cross(X, Y)
        if kind == "hand":
            X = perp(hinge, Y)
            return X, np.cross(X, Y)
        if kind == "knee":
            Z = perp(-FRONT, Y)
        elif kind == "palm":
            Z = perp(palm, Y)
        elif kind == "thumb":
            Z = perp(thumb if np.linalg.norm(thumb) > 0.5 else palm, Y)
        elif kind == "up":
            Z = perp(UP, Y) if abs(Y @ UP) < 0.7 else perp(FRONT, Y)
        else:
            Z = perp(FRONT, Y) if abs(Y @ FRONT) < 0.7 else perp(UP, Y)
        return np.cross(Y, Z), Z
    names, parents, worlds, ends_out = [], [], [], {}
    M = np.diag([-1.0, 1, 1])
    for d in defs:
        sides = ("l", "r") if "{s}" in d["name"] else ("",)
        for s in sides:
            e = expand(d, s or "l", s or "l", "L" if s != "r" else "R")
            nl = expand(d["name"], "l", "l", "L")
            h, t = W[nl]
            ends_out[e["name"]] = (M @ h, M @ t) if s == "r" else (h.copy(), t.copy())
            Y = unit(t - h)
            X, Z = frame(d, Y)
            G = np.eye(4)
            if s == "r":
                Y, Z, h = M @ Y, M @ Z, M @ h
                X = np.cross(Y, Z)
            G[:3, 0], G[:3, 1], G[:3, 2], G[:3, 3] = X, Y, Z, h
            names.append(e["name"])
            parents.append(e["parent"])
            worlds.append(G)
    idx = {n: i for i, n in enumerate(names)}
    par = [idx[p] if p else -1 for p in parents]
    info = {"bones": len(names), "elbow_rest_bend_deg": round(bend, 2), "hinge_l": [round(float(x), 4) for x in hinge],
            "palm_l": [round(float(x), 3) for x in palm]}
    return names, par, np.stack(worlds), ends_out, info
