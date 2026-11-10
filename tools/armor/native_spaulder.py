"""The "spaulder" recipe of the native armor builder: an articulated shoulder defence. Per side a collar and lames down
the upper arm, each ONE rigid part on its own ride (P2 lead 6: her shoulder's skin is rigid in 20 mm strips and not
across the joint, so one cop over it cannot seat under any ride).

build.json: "frame" {"from", "to"} the arm's bones ("*" = the side); "theta" [t0, t1] round the arm (0 front, 90
outer / top, 180 back); "clear" the inner faces' stand-off from her rest skin (along its normals); "thick";
"lames" {"edges" [e0 .. en]: the EXPOSED bands along the arm from its joint (m; part 0, the collar, is e0..e1, lame k
is ek..ek+1), "overlap" [per part]: how far a lame runs up past its band, UNDER the lame above it (lame 1: OVER the
collar: the collar seam), "gap": the room between a lapping band's inner face and the outer face of the part beneath
(a number or one a part), "margin", "rides": "mean" (each part rides the area-weighted mean of her skin weights over
its footprint, top 8: derived here from the body, so a changed body re-derives it; the footprint is her skin under
its exposed band and "ride_reach", 6 mm, up past it) or [a part rule each],
"carry": "part" | "none" (gear_native.part_blends)}; "tip_flare" {"lames" [k ..], "from", "to", "rise"}: those lames'
front tips stand `rise` further off her from theta `from` to `to` (her pec and front armpit skin ride over anything
in front of 45); "mirror" (true): one shape for her two shoulders, on the law lying over both sides' skin;
"materials" {"plate", "rim"}: the rolled rims are their own parts on their lame ("with"), so a set
may trim them; "play" {"step", "step_s"}: the play tier's mesh (<id>.lod1.glb, counted; see the report); "like": another
piece's id: its build.json's params under this one's own keys (the warden's spaulders are the plain ones, gold rims).

Every lame is a tilted strip, as a shingle: low (its inner face `clear` off her) under the lame above, rising to
stand `gap` clear of the lame beneath over the band it laps. The order is upper over lower.

    python tools/armor/native_build.py plate_spaulders_plain
"""
import json
import os

import numpy as np

import native_build as nb
from native_build import MM, Frame, Part, Sheet


# ---------------------------------------------------------------- her skin as a law, a lame

class SkinLaw:
    """rho(s, theta) of the surface standing `clear` off a body's skin (along its normals), read along a frame's rays
    on an (s, theta) grid, eased, and lifted so it never dips under that surface: a law a plate can lie on that keeps
    her skin's own shape (an envelope polynomial cannot follow a shoulder). Clamped outside its domain."""

    def __init__(self, s, th, rho, add=0.0):
        from scipy.interpolate import RectBivariateSpline
        self.s, self.th, self.rho, self.add = np.asarray(s, float), np.asarray(th, float), np.asarray(rho, float), add
        self.f = RectBivariateSpline(self.s, self.th, self.rho, kx=3, ky=3)

    def __call__(self, s, th):
        s, th = np.broadcast_arrays(np.asarray(s, float), np.asarray(th, float))
        v = self.f.ev(np.clip(s, self.s[0], self.s[-1]).reshape(-1), np.clip(th, self.th[0], self.th[-1]).reshape(-1))
        return v.reshape(s.shape) + self.add

    def plus(self, d):
        return SkinLaw(self.s, self.th, self.rho, self.add + d)

    @classmethod
    def off_skin(cls, ref, fr, dom, clear, ds=0.002, dth=2.0, ease=0.6, rmax=0.14):
        from scipy import ndimage
        s0, s1, t0, t1 = dom
        s = np.linspace(s0, s1, int(round((s1 - s0) / ds)) + 1)
        th = np.linspace(t0, t1, int(round((t1 - t0) / dth)) + 1)
        V = ref.V + ref.N * clear
        # (only the skin the rays can meet: inside the can, within 30 degrees of the domain round the arm)
        sv, tv, rv = fr.cyl(V)
        tm, half = 0.5 * (t0 + t1), 0.5 * (t1 - t0) + 30.0
        ok = (sv > s0 - 0.03) & (sv < s1 + 0.03) & (rv < rmax) & (np.abs((tv - tm + 180.0) % 360.0 - 180.0) < half)
        Tn = ref.T[ok[ref.T].any(1)]
        S, TH = np.meshgrid(s, th, indexing="ij")
        rho, _ = nb.radial(V, Tn, fr, S, TH, rmax)
        miss = ~np.isfinite(rho)
        if miss.all():
            raise SystemExit("native_spaulder: no skin along the frame's rays (the frame's bones or its theta range)")
        if miss.any():   # (a ray that meets nothing takes its nearest neighbour's)
            i, j = ndimage.distance_transform_edt(miss, return_distances=False, return_indices=True)
            rho = rho[i, j]
        soft = ndimage.gaussian_filter(rho, ease, mode="nearest") if ease else rho
        law = cls(s, th, soft, float(max((rho - soft).max(), 0.0)))
        law.no_hit, law.eased = int(miss.sum()), float(np.abs(rho - soft).max())
        return law


class Lame(Sheet):
    """A Sheet with a `rise`: h(s, theta), how far its inner face stands over its law (a lame's tilt over the part it
    laps). Its edges there take the steel's own thickness as a wall (Sheet: a lifted edge)."""

    def __init__(self, *a, rise=None, **k):
        super().__init__(*a, **k)
        self.rise = rise

    def lifted(self, s, th):
        s, th = np.broadcast_arrays(np.asarray(s, float), np.asarray(th, float))
        return np.zeros(s.shape) if self.rise is None else self.rise(s, th)

    def height(self, s, th):
        return super().height(s, th) + self.lifted(s, th)

    def inner(self, s, th):
        """Its inner face's rho."""
        return self.law(s, th) + self.lifted(s, th)

    def freeze(self, pad=0.004, ds=0.001, dth=1.0):
        """Its rise as a table over its own domain (a lame's rise reads the lame beneath it, and that one the next)."""
        from scipy.interpolate import RegularGridInterpolator
        if self.rise is None:
            return self
        tm = 0.5 * (self.t0 + self.t1)
        s = np.arange(float(self.top(tm)) - pad, float(self.bot(tm)) + pad + ds, ds)
        th = np.arange(self.t0 - 4, self.t1 + 4 + dth, dth)
        S, TH = np.meshgrid(s, th, indexing="ij")
        f = RegularGridInterpolator((s, th), self.rise(S, TH), bounds_error=False, fill_value=None)

        def rise(a, b):
            a, b = np.broadcast_arrays(np.asarray(a, float), np.asarray(b, float))
            q = np.c_[np.clip(a, s[0], s[-1]).reshape(-1), np.clip(b, th[0], th[-1]).reshape(-1)]
            return f(q).reshape(a.shape)
        self.rise = rise
        return self


def tilt(law, top_s, low=None, zs=None, up=None, za=None, gap=0.003, gap_up=None):
    """A lame's rise: over the part `low` it laps from s = zs on (down to its bottom edge) and over the part `up` it
    laps down to s = za (lame 1 over the collar), `gap` clear of that part's outer face; a straight ramp between, from
    nothing at its own top edge when no part lies under it there."""
    gap_up = gap if gap_up is None else gap_up

    def room(sheet, s, th, g):
        return np.maximum(sheet.outer(np.clip(s, sheet.top(th), sheet.bot(th)), th) + g - law(s, th), 0.0)

    def h(s, th):
        s, th = np.broadcast_arrays(np.asarray(s, float), np.asarray(th, float))
        s_a = za if up is not None else top_s
        h_a = room(up, np.full(s.shape, za), th, gap_up) if up is not None else np.zeros(s.shape)
        if low is None:
            out = h_a * (1.0 - np.clip((s - s_a) / 0.012, 0, 1)) if up is not None else np.zeros(s.shape)
        else:
            x = np.clip((s - s_a) / max(zs - s_a, 1e-6), 0, 1)
            out = h_a + (room(low, np.full(s.shape, zs), th, gap) - h_a) * x
            out = np.where(s >= zs, room(low, s, th, gap), out)
        if up is not None:
            out = np.where(s <= za, room(up, s, th, gap_up), out)
        return out
    return h


# ---------------------------------------------------------------- footprints and rides

def vertex_area(V, T):
    ta = np.linalg.norm(np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]), axis=1) / 2
    A = np.zeros(len(V))
    np.add.at(A, T.reshape(-1), np.repeat(ta / 3, 3))
    return A


def footprint(ref, fr, s0, s1, t0, t1, rmax=0.09):
    """Her skin under a strip of the frame: the vertices of the triangles lying wholly in s0..s1, theta t0..t1, on the
    frame's own side of her."""
    s, th, rho = fr.cyl(ref.V)
    ok = (ref.V[:, 0] * fr.hand > 0) & (th >= t0) & (th <= t1) & (rho < rmax) & (s >= s0) & (s <= s1)
    return np.unique(ref.T[ok[ref.T].all(1)])


def mean_ride(ref, vs, top=8):
    """{bone: share}: the area-weighted mean of her skin weights over the vertices `vs`, its `top` bones."""
    if not len(vs):
        raise SystemExit("native_spaulder: a lame has no skin under it (its band lies off her)")
    A = getattr(ref, "_va", None)
    if A is None:
        A = ref._va = vertex_area(ref.V, ref.T)
    D = np.zeros(len(ref.joint_names))
    np.add.at(D, np.asarray(ref.J)[vs].reshape(-1), (np.asarray(ref.W, float)[vs] * A[vs][:, None]).reshape(-1))
    j = [int(a) for a in np.argsort(-D)[:top] if D[a] > 0]
    tot = D[j].sum()
    return {ref.joint_names[a]: round(float(D[a] / tot), 4) for a in j if D[a] / tot >= 0.00005}


def split_rim(p, rim_name, rim_material):
    """A built sheet as two parts: its plate, and its rolled edges with their walls (every triangle on a roll: the
    shader's flag 0), under their own material. Both keep the whole sheet's normals: no seam shows between them."""
    on = (p.col[p.T, 3] < 0.5).all(1)

    def sub(name, material, T):
        used = np.zeros(len(p.P), bool)
        used[T] = True
        return Part(name, material, p.P[used], (np.cumsum(used) - 1)[T], p.uv0[used], p.uv1[used], p.col[used], p.N[used])
    return sub(p.name, p.material, p.T[~on]), (sub(rim_name, rim_material, p.T[on]) if on.any() else None)


# ---------------------------------------------------------------- the recipe

def part_names(n, sd):
    return [f"collar_{sd}_rigid"] + [f"lame{k}_{sd}_rigid" for k in range(1, n)]


def layout(cfg, ref, step=None, step_s=None, roll=True, laws=None):
    """The recipe's geometry on a body, per side: {"fr", "law", "sheets" (the collar, then the lames down the arm),
    "names", "spans" [(top s, bottom s) a part], "foot" [her skin vertices under each part]}. step / step_s / roll /
    laws: another tier's mesh over the same faces (no rolled edges, so no edge rows; the sides' laws as read)."""
    t0, t1 = cfg["theta"]
    lm = cfg["lames"]
    E = np.asarray(lm["edges"], float)
    n = len(E) - 1
    lap = list(lm.get("overlap") or [0.0] * n)
    per = lambda key, k, d: (lm[key][k] if isinstance(lm.get(key), list) else lm.get(key, d))  # noqa: E731
    clear, thick, margin = cfg["clear"], cfg["thick"], lm.get("margin", 0.002)
    rl = tuple(cfg.get("roll", (0.0045, 0.001))) if roll else None
    tf = cfg.get("tip_flare") or {}
    out = {}
    frames = {sd: Frame.bones(ref, cfg["frame"]["from"].replace("*", sd), cfg["frame"]["to"].replace("*", sd), hand)
              for sd, hand in (("l", 1), ("r", -1))}
    if laws is None:
        laws = {sd: SkinLaw.off_skin(ref, fr, (E[0] - 0.012, E[-1] + 0.012, t0 - 12, t1 + 12), clear, ease=cfg.get("ease", 0.6))
                for sd, fr in frames.items()}
        if cfg.get("mirror", True):
            # one shape for her two shoulders: the law lying on or over both sides' (her skin's two sides are not
            # mirrors to the millimetre; a plate made for one would stand closer than `clear` to the other)
            a, b = laws["l"], laws["r"]
            both = SkinLaw(a.s, a.th, np.maximum(a.rho + a.add, b.rho + b.add))
            both.no_hit, both.eased = a.no_hit + b.no_hit, max(a.eased, b.eased)
            both.sides_mm = round(float(np.abs(a.rho + a.add - b.rho - b.add).max()) / MM, 2)
            laws = {"l": both, "r": both}
    for sd, fr in frames.items():
        base = laws[sd]

        def law_of(k, base=base):
            if not tf or k not in tf.get("lames", []) or not tf.get("rise"):
                return base
            return lambda s, th: base(s, th) + tf["rise"] * np.clip((tf["from"] - np.asarray(th, float)) / (tf["from"] - tf["to"]), 0, 1.2) ** tf.get("power", 2.0)

        spans = [(E[0], E[1])] + [(E[k] - lap[k], E[k + 1]) for k in range(1, n)]
        line = lambda v: (lambda th: np.full(np.shape(th), float(v)))  # noqa: E731
        kw = dict(roll=rl, clear=clear, lip=cfg.get("lip", 0.0012), step=step or cfg.get("step", 0.008),
                  step_s=step_s or cfg.get("step_s", 0.006))
        sheets = [None] * n
        # (the collar: under lame 1, so flat; then the lames from the last one up, each reading the one beneath it)
        sheets[0] = Lame(fr, law_of(0), t0, t1, line(spans[0][0]), line(spans[0][1]), thick, roll_on="t01" if roll else "", **kw)
        for k in range(n - 1, 0, -1):
            low = sheets[k + 1] if k + 1 < n else None
            up = sheets[0] if k == 1 else None
            rise = tilt(law_of(k), spans[k][0], low, spans[k + 1][0] - margin if low is not None else None, up,
                        spans[k][0] + lap[k] + margin if up is not None else None, per("gap", k + 1 if low is not None else k, 0.003),
                        per("gap", k, 0.003))
            on = ("tb01" if k == 1 else "b01") if roll else ""
            sheets[k] = Lame(fr, law_of(k), t0, t1, line(spans[k][0]), line(spans[k][1]), thick, roll_on=on, rise=rise, **kw).freeze()
        # (what a part's ride reads: her skin under its exposed band and `ride_reach` up past it, not its whole lap:
        # the band hidden under the lame above is that lame's skin)
        reach = lm.get("ride_reach", 0.006)
        foot = [footprint(ref, fr, max(a, E[k] - reach), b, t0, t1) for k, (a, b) in enumerate(spans)]
        out[sd] = {"fr": fr, "law": base, "sheets": sheets, "names": part_names(n, sd), "spans": spans, "foot": foot, "lap": lap}
    return out


def build_parts(cfg, lay, ref=None, rivets=True):
    """The mesh parts of a layout: per lame its plate (its lap rivets joined in) and its rolled rim (its own part)."""
    mats = cfg.get("materials", {"plate": "steel", "rim": "steel"})
    t0, t1 = cfg["theta"]
    parts, rims = [], {}
    for sd, L in lay.items():
        n = len(L["sheets"])
        for k, (sh, name) in enumerate(zip(L["sheets"], L["names"])):
            p = sh.build(name, mats["plate"], ao=1.0 if k <= 1 else 0.92)
            if ref is not None:
                nb.seat(p, ref, cfg.get("seat", 0.0012))
            plate, rim = split_rim(p, f"rim{k}_{sd}_rigid", mats.get("rim", mats["plate"]))
            riv = []
            if rivets and k >= 1:
                rows = []
                if k + 1 < n:      # on the band lapping the lame beneath
                    rows.append(L["spans"][k][1] - max(0.5 * L["lap"][k + 1], 0.0075))
                if k == 1:         # lame 1 on the collar
                    rows.append(L["spans"][k][0] + max(0.5 * L["lap"][k], 0.0075))
                for s_r in rows:
                    for th_e, sgn in ((t0, 1), (t1, -1)):
                        c, nn = sh.at(np.array(s_r), np.array(th_e + sgn * np.degrees(0.011 / float(sh.law(s_r, th_e)))))
                        # (her right side's rivet is the mirror of one made on her left: the two sides stay mirrors)
                        m = np.array([sh.fr.hand, 1.0, 1.0])
                        rv = nb.rivet(c * m, nn * m, name=name, material=mats["plate"])
                        if sh.fr.hand < 0:
                            rv.P, rv.N, rv.T = rv.P * m, rv.N * m, rv.T[:, ::-1]
                        riv.append(rv)
            parts.append(Part.join(name, mats["plate"], [plate] + riv) if riv else plate)
            if rim is not None:
                parts.append(rim)
                rims[rim.name] = name
    return parts, rims


def edge_report(sh, ref, n=25):
    """Her skin's distance under a sheet's inner face along each edge and over its face, mm (min, max)."""
    t = np.linspace(sh.t0, sh.t1, n)
    tm = 0.5 * (sh.t0 + sh.t1)
    s = np.linspace(float(sh.top(tm)), float(sh.bot(tm)), 9)
    S, TH = np.meshgrid(s, t, indexing="ij")
    X = sh.fr.pt(S, TH, sh.inner(S, TH))
    q, nn, _ = ref.closest(X.reshape(-1, 3))
    c = ((X.reshape(-1, 3) - q) * nn).sum(1).reshape(S.shape) / MM
    mm = lambda v: [round(float(v.min()), 1), round(float(v.max()), 1)]  # noqa: E731
    return {"top": mm(c[0]), "bottom": mm(c[-1]), "front": mm(c[:, 0]), "back": mm(c[:, -1]), "face": mm(c)}


def resolve(cfg):
    """A build.json that is "like" another piece's: that piece's params under this one's own keys (a set's variant:
    the same geometry by construction, its own name and materials)."""
    if cfg.get("like"):
        base = json.load(open(os.path.join(nb.NATIVE, cfg["like"], "build.json"), encoding="utf-8"))
        cfg = {**resolve(base), **{k: v for k, v in cfg.items() if k != "like"}}
    return cfg


def spaulder(pid, cfg, out=None, ref=None):
    cfg = resolve(cfg)
    ref = ref or nb.Ref.her()
    lm = cfg["lames"]
    lay = layout(cfg, ref)
    parts, rim_of = build_parts(cfg, lay, ref)
    rules, sockets, rims, rep = {}, {}, {}, {"id": pid, "sides": {}}
    t0, t1 = cfg["theta"]
    for sd, L in lay.items():
        r = rep["sides"][sd] = {"law": {"no_hit": L["law"].no_hit, "eased_mm": round(L["law"].eased / MM, 2),
                                        "lift_mm": round(L["law"].add / MM, 2), "sides_differ_mm": getattr(L["law"], "sides_mm", None)}}
        for k, (sh, name) in enumerate(zip(L["sheets"], L["names"])):
            given = lm.get("rides", "mean")
            rule = {"bones": mean_ride(ref, L["foot"][k])} if given == "mean" else json.loads(json.dumps(given[k]))
            if "bones" in rule:
                rule.setdefault("carry", lm.get("carry", "none"))
            rules[name] = rule
            tm = 0.5 * (t0 + t1)
            c, nn = sh.at(np.array(0.5 * sum(L["spans"][k])), np.array(tm))
            sockets[name[:-6]] = {"point": c.round(5).tolist(), "normal": nn.round(5).tolist(), "up": (-L["fr"].a).round(5).tolist()}
            r[name] = {"s_mm": [round(v / MM, 1) for v in L["spans"][k]], "foot_points": int(len(L["foot"][k])),
                       "ride": rule.get("bones", rule), "skin_under_mm": edge_report(sh, ref)}
        sockets[f"cop_{sd}"] = sockets[f"lame1_{sd}"]
        te = np.linspace(t0, t1, 12)
        top, low = L["sheets"][0], L["sheets"][-1]
        rims[f"top_rim_{sd}"] = {"points": top.at(top.top(te), te)[0].round(5).tolist()}
        rims[f"arm_rim_{sd}"] = {"points": low.at(low.bot(te), te)[0].round(5).tolist()}
    for rim, name in rim_of.items():
        rules[rim] = {"with": name}
    by = {p.name: p for p in parts}
    for sd in lay:
        for name in lay[sd]["names"]:
            rep["sides"][sd][name]["tris"] = int(len(by[name].T)) + int(sum(len(by[r].T) for r, h in rim_of.items() if h == name))
    if hasattr(ref, "body"):
        import gear_field
        for sd in lay:
            for name in lay[sd]["names"]:
                c, _ = gear_field.signed_clear(ref.body, np.vstack([by[name].P] + [by[r].P for r, h in rim_of.items() if h == name]), k=16)
                rep["sides"][sd][name].update({"rest_clear_mm_min": round(float(c.min()) / MM, 2), "inside": int((c < 0).sum())})
    # (the two sides are one rule on her two arms: how far the right is from the left's mirror)
    rep["mirror_mm_max"] = round(max(float(np.abs(by[a].P * [-1, 1, 1] - by[b].P).max()) if by[a].P.shape == by[b].P.shape else 1e3
                                     for a, b in zip(lay["l"]["names"], lay["r"]["names"])) / MM, 3)
    piece = dict(cfg["piece"])
    piece.update({"id": pid, "native": {"rest_body": ref.rest_body, "rest_hash": ref.hashes, "builder": "tools/armor/native_build.py",
                                        "recipe": cfg["recipe"]}, "parts": rules})
    sj = {"id": pid, "slot": piece["slot"], "body_hash": ref.hashes.get("close"),
          "space": "glTF / Godot: Y up, metres, her_b's rest (native_build)", "sockets": sockets, "rims": rims, "fixings": []}
    d = nb.write_piece(pid, piece, parts, sj, out)
    rep["dir"] = os.path.relpath(d, nb.REPO).replace("\\", "/")
    rep["tris"] = int(sum(len(p.T) for p in parts))
    rep["parts"] = {p.name: [int(len(p.P)), int(len(p.T)), p.material] for p in parts}
    # the play tier's mesh: the same faces at a coarse step, no rolled edges, walls or rivets
    pl = cfg.get("play") or {}
    lod, _ = build_parts(cfg, layout(cfg, ref, pl.get("step", 0.014), pl.get("step_s", 0.012), roll=False,
                                     laws={sd: L["law"] for sd, L in lay.items()}), ref, rivets=False)
    import gear_native as gn
    gn.write_glb(os.path.join(d, f"{pid}.lod1.glb"), [p.node() for p in lod], {"native_build": {"piece": pid, "tier": "play"}})
    rep["play_tris"] = int(sum(len(p.T) for p in lod))
    json.dump(rep, open(os.path.join(d, "build_report.json"), "w"), indent=1)
    return rep


RECIPES = {"spaulder": spaulder}
