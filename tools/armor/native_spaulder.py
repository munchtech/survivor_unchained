"""The "spaulder" recipe of the native armor builder: a shoulder defence as a real one is made. Per side a domed COP
over the shoulder top, wide LAMES shingled down the upper arm under it, and a skinned leather ARMING CAP under them
all. Each plate is ONE rigid part on its own ride (P2 lead 6: her shoulder's skin is rigid in 20 mm strips and not
across the joint, so no plate held 3 mm off her skin can seat across it). So the cop does not hug her: it is a standing
dome whose rim clears her rest skin and whose crown stands well off, and the arming cap (a bendy part: it follows her
skin) shows in any gap, never bare skin.

build.json: "frame" {"from", "to"} the arm's bones ("*" = the side); "theta" [t0, t1] the COP's reach round the arm
(0 front, 90 outer / top, 180 back); "clear" the plates' inner faces' stand-off from her rest skin (along its normals);
"thick" the plates' steel; "roll" [width, height] a rolled edge; "lip"; "ease" (the skin law's smoothing, grid cells: a
plate keeps her shoulder's shape, not her skin's small relief), "grid" [ds, dtheta] the law's grid (2 mm, 2 degrees);
"lames" {"edges" [e0 .. en]: the EXPOSED bands along the arm from its joint (m; part 0, the cop, is e0..e1, lame k is
ek..ek+1), "theta" [a, b] the lames' reach (the cop's when absent) or a list [[a, b] one a lame, from the cop down]: each
lame its own reach (a SPLINTED spaulder: narrow top lames over the shoulder, full-wrap ones down the arm; the rivets sit
at the two ends of the lap, where both plates are), "arc": the lames' edges (and the cop's lower edge) rise this far
toward the shoulder at the two ends of the lame below the edge (a curved edge, never a ruled band), "overlap" [per
part]: how far a lame runs up past its band, UNDER the plate above it (never past that plate's own exposed band less
`margin`: a longer one is cut to it and reported, build_report "lap_cut_mm" {part: [asked, built]}), "gap": the room between a lapping band's inner face and the
outer face of the part beneath (a number or one a part), "margin", "last_flare": the last lame's lower edge stands this
far further off her, "rides": "mean" (each plate rides the area-weighted mean of her skin weights over its footprint,
top 8: derived here from the body, so a changed body re-derives it; the footprint is her skin under its exposed band
and "ride_reach", 6 mm, up past it) or [a part rule each], "carry": "part" | "none" (gear_native.part_blends), "bend"
{"max", "smooth", "clear", "clips"} (one for every lame, or a list, one per lame or null): the plate bends only as far
as her moving skin needs, written into its part rule (gear_native.part_blends solves it at build time)};
"cop" {"apex": how far its crown stands over its rim's surface, "rim": its rim's own extra stand-off, "shape" [a, b]:
the dome's fullness along / round the arm (2 a parabola, more is fuller), "roll" its own rolled rim, "ridge" {"theta",
"h", "w", "fade"}: a keel down its crown (Sheet), "bend": as the lames' (its own), "ride_band" [s0, s1]: the band of her skin its ride reads (her skin
under its own outline when absent), "over" {"depth", "ease"}: the cop CROWNS her shoulder: e0 may lie up past the
joint, over her acromion and outer trapezius, because the frame's centres are let down to stay `depth` under her
skin's crest line there (ShoulderFrame; depth: her skin's own at lame 1's top when absent; read from her skin, so
another body re-derives it), "arch" {"span", "power"}: its upper edge is an arch (e0 at its middle, down to `span`
above its lower edge at its two ends: a rounded outline, never a box), "wing" {"end", "curl", "power", "min"}: where
the cop's reach runs round past the lames' ends (by "min" degrees or more, 8) that end of it is a WING: its lower
corner is rounded (its lower edge rises from the lames' end to leave its side edge `end` long), and it curls back in
over the end of lame 1 (curl 1: down to its own surface at its tip, so no slot shows under it from the front; 0: it
keeps the lame's room all the way), "lie" {"len", "drop"}: its upper edge LIES DOWN along her (a real cop's neck edge
lies on the trapezius; a rim standing off her there shows from the neck side as a fin with a dark slot under it): at
that edge the plate has no "rim" stand-off and no crown and sits `drop` under the plates' own clearance, easing up to
its dome over `len` down from the edge, so it leaves the edge along her skin, never as a wall. Full where the upper
edge is highest (the arch's middle), nothing at the arch's two ends (the cop's front and back edges are as they
were; no arch: the whole edge), "close" {"len", "flat", "room", "fade"}: its NECK END IS CLOSED: a real cop's neck
end is a plate lying on the arming leather over the trapezius, and its dome stands over the point of the shoulder;
a dome that starts at the neck edge is a wall facing the neck (from the other shoulder's side: a fin, a plate
hovering, its edge wall a dark slot). Along its upper edge the plate's inner face LANDS `room` over the arming
cap's outer face (no arming cap: over her skin's own surface), it lies that low for `flat` down from the edge, then
eases up to its dome over `len`; so the edge wall (Sheet: it runs down past the inner face) ends in the leather and
nothing shows under it. In full wherever the upper edge runs `fade` or more above the level of the arch's two ends,
nothing at those ends (no arch: the whole edge). It lands on what the arming cap IS, not `drop` under a clearance:
with it "lie" is not needed};
"arming" {"clear", "thick", "roll", "past" [up, down, round (degrees)]: how far it shows beyond the plates' outline
(the cop's arch, the cop's sides, then in to the lames' sides), "theta" [a, b]: its own least reach round the arm all
along its length (it covers her where no steel is, e.g. the deltoid's front and back beside narrow top plates; then
`round` is past whichever plate is at that s; absent: the cop's sides easing in to lame 1's), "step"} (absent or null: no arming cap; its material
must be a key some gear source carries painted, gear_native.material_templates: "darkleather"; a bare key is white); "rivet" {"r", "h", "in"}: the articulation rivets, at the two ends of every
lap; "tip_flare" {"lames" [k ..], "from", "to", "rise"}: those parts' front tips stand `rise` further off her from
theta `from` to `to` (her pec and front armpit skin ride over anything in front of 45); "mirror" (true): one shape for
her two shoulders, on the law lying over both sides' skin; "materials" {"plate", "rim", "arming"}: the rolled rims are
their own parts on their plate ("with"), so a set may trim them; "play" {"step", "step_s"}: the play tier's mesh
(<id>.lod1.glb, counted; see the report); "like": another piece's id: its build.json's params under this one's own keys
(the warden's spaulders are the plain ones, gold rims).

Every plate is a tilted strip, as a shingle: low (its inner face `clear` off her) under the plate above, rising to
stand `gap` clear of the lame beneath over the band it laps. The order is upper over lower, the cop over them all.

    python tools/armor/native_build.py plate_spaulders_plain
"""
import json
import os

import numpy as np

import native_build as nb
from native_build import MM, Frame, Part, Sheet


# ---------------------------------------------------------------- the frame over her shoulder top

class ShoulderFrame(Frame):
    """The arm's frame with its centres let down under her shoulder top: c(s) = c + s a - drop(s) o. Past the shoulder
    joint the arm's own axis runs out of her through her trapezius, so no ray from it meets the top of her shoulder;
    these centres stay under her skin's crest line (theta 90) instead, the planes s = const as they were (so a ray's
    direction is still theta's alone, and every Sheet works on it unchanged). drop is 0 from the lames on: there it
    IS the arm's frame."""

    def __init__(self, fr, s, drop):
        self.c, self.hand, self.L, self.a, self.f, self.o = fr.c, fr.hand, fr.L, fr.a, fr.f, fr.o
        self.ds, self.dd = np.asarray(s, float), np.asarray(drop, float)

    def drop(self, s):
        return np.interp(np.asarray(s, float), self.ds, self.dd)

    def origin(self, s):
        s = np.asarray(s, float)
        return self.c + s[..., None] * self.a - self.drop(s)[..., None] * self.o

    def pt(self, s, th, rho):
        return self.origin(s) + np.asarray(rho, float)[..., None] * self.radial(th)

    def cyl(self, P):
        d = np.asarray(P, float) - self.c
        s = d @ self.a
        x, y = d @ self.f, d @ self.o + self.drop(s)
        return s, np.degrees(np.arctan2(y, x)), np.hypot(x, y)


def crest_line(ref, fr, s0, s1, ds=0.002, far=0.25):
    """(s, r): her skin's height over the arm's axis along its crest line (theta 90), read from outside her (a ray
    down each plane s = const: the outermost skin, where the axis itself lies out of her it is negative)."""
    s = np.arange(s0, s1 + 0.5 * ds, ds)
    Tn = nb.near(ref.V, ref.T, fr, s0 - 0.04, s1 + 0.04, 2 * far)
    Tn = Tn[(ref.V[Tn][:, :, 0] * fr.hand > -0.01).all(1)]
    t, _ = nb.raycast(ref.V, Tn, fr.c + s[:, None] * fr.a + far * fr.o, np.tile(-fr.o, (len(s), 1)), 3 * far)
    ok = np.isfinite(t)
    if not ok.any():
        raise SystemExit("native_spaulder: no skin on the arm's crest line (the frame's bones)")
    return s, np.interp(s, s[ok], far - t[ok])


def crest_drop(s, r, keep, depth=None, ease=0.006, blend=0.02):
    """drop(s): how far the centres go under the arm's axis so they stay `depth` under the crest line r(s) (her
    skin's own depth at `keep`, where the lames start, when none is given), eased along s, 0 from `keep` on."""
    from scipy import ndimage
    depth = float(np.interp(keep, s, r)) if depth is None else depth
    d = ndimage.gaussian_filter1d(np.maximum(depth - r, 0.0), ease / (s[1] - s[0]), mode="nearest")
    k = np.clip((keep - 0.004 - s) / blend, 0.0, 1.0)
    return d * k * k * (3 - 2 * k)


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
        if hasattr(fr, "origin"):     # (a frame whose centres leave the axis: its own rays)
            rho = nb.raycast(V, Tn, fr.origin(S.reshape(-1)), fr.radial(TH.reshape(-1)), rmax)[0].reshape(S.shape)
        else:
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
        tt = np.linspace(self.t0, self.t1, 17)     # (its edges may be curves: the table covers them all)
        s = np.arange(float(np.min(self.top(tt))) - pad, float(np.max(self.bot(tt))) + pad + ds, ds)
        th = np.arange(self.t0 - 4, self.t1 + 4 + dth, dth)
        S, TH = np.meshgrid(s, th, indexing="ij")
        f = RegularGridInterpolator((s, th), self.rise(S, TH), bounds_error=False, fill_value=None)

        def rise(a, b):
            a, b = np.broadcast_arrays(np.asarray(a, float), np.asarray(b, float))
            q = np.c_[np.clip(a, s[0], s[-1]).reshape(-1), np.clip(b, th[0], th[-1]).reshape(-1)]
            return f(q).reshape(a.shape)
        self.rise = rise
        return self


def tilt(law, top, bot, low=None, zs=None, gap=0.003, flare=0.0, curl=None):
    """A plate's rise over its law. Over the lame `low` it laps: from the line s = zs(theta) on (down to its bottom
    edge) it stands `gap` clear of that lame's outer face, a straight ramp from nothing at its own top edge down to
    there (a shingle). The last lame (no `low`): its lower edge stands `flare` further off her. curl [(a, b, k) ..]:
    from theta a (the lapped lame's end) on to b (its own) its room over that lame eases off by k (a wing)."""
    def keep(th):
        f = np.ones(np.shape(th))
        for a, b, k in curl or ():
            x = np.clip((np.asarray(th, float) - a) / (b - a), 0, 1)
            f = f * (1 - k * x * x * (3 - 2 * x))
        return f

    def room(s, th):
        return np.maximum(low.outer(np.clip(s, low.top(th), low.bot(th)), th) + gap - law(s, th), 0.0) * keep(th)

    def h(s, th):
        s, th = np.broadcast_arrays(np.asarray(s, float), np.asarray(th, float))
        a = top(th)
        if low is None:
            return flare * np.clip((s - a) / np.maximum(bot(th) - a, 1e-6), 0, 1) ** 2
        z = zs(th)
        x = np.clip((s - a) / np.maximum(z - a, 1e-6), 0, 1)
        return np.where(s >= z, room(s, th), room(z, th) * x)
    return h


def dome(top, bot, t0, t1, apex, shape=(2.4, 2.4)):
    """A cop's crown: how far it stands over its rim's surface at (s, theta): `apex` at its middle, nothing along its
    four edges, curved both ways (a dome, not a bent strip)."""
    def h(s, th):
        s, th = np.broadcast_arrays(np.asarray(s, float), np.asarray(th, float))
        a = top(th)
        u = np.clip(2.0 * (s - a) / np.maximum(bot(th) - a, 1e-6) - 1.0, -1, 1)
        v = np.clip((2.0 * th - t0 - t1) / (t1 - t0), -1, 1)
        return apex * (1.0 - np.abs(u) ** shape[0]) * (1.0 - np.abs(v) ** shape[1])
    return h


# ---------------------------------------------------------------- footprints and rides

def vertex_area(V, T):
    ta = np.linalg.norm(np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]), axis=1) / 2
    A = np.zeros(len(V))
    np.add.at(A, T.reshape(-1), np.repeat(ta / 3, 3))
    return A


def footprint(ref, fr, s0, s1, t0, t1, rmax=0.09):
    """Her skin under a strip of the frame: the vertices of the triangles lying wholly in s0..s1, theta t0..t1, on the
    frame's own side of her. s0 / s1: numbers, or edge lines s(theta) (a plate's own outline)."""
    s, th, rho = fr.cyl(ref.V)
    tc = np.clip(th, t0, t1)
    lo, hi = (s0(tc) if callable(s0) else s0), (s1(tc) if callable(s1) else s1)
    ok = (ref.V[:, 0] * fr.hand > 0) & (th >= t0) & (th <= t1) & (rho < rmax) & (s >= lo) & (s <= hi)
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
    """The rigid plates of a side, from the shoulder down: the cop, then the lames."""
    return [f"cop_{sd}_rigid"] + [f"lame{k}_{sd}_rigid" for k in range(1, n)]


def arming_name(sd):
    return f"arming_{sd}_cap"


def side_laws(ref, frames, dom, clear, ease, mirror, grid=(0.002, 2.0)):
    """Her skin's law per side; with `mirror` one law lying on or over both sides' (her skin's two sides are not
    mirrors to the millimetre; a plate made for one would stand closer than `clear` to the other)."""
    laws = {sd: SkinLaw.off_skin(ref, fr, dom, clear, ds=grid[0], dth=grid[1], ease=ease) for sd, fr in frames.items()}
    if mirror:
        a, b = laws["l"], laws["r"]
        both = SkinLaw(a.s, a.th, np.maximum(a.rho + a.add, b.rho + b.add))
        both.no_hit, both.eased = a.no_hit + b.no_hit, max(a.eased, b.eased)
        both.sides_mm = round(float(np.abs(a.rho + a.add - b.rho - b.add).max()) / MM, 2)
        laws = {"l": both, "r": both}
    return laws


def layout(cfg, ref, step=None, step_s=None, roll=True, laws=None):
    """The recipe's geometry on a body, per side: {"fr", "law", "sheets" (the cop, then the lames down the arm),
    "names", "spans" [(top s, bottom s) a part, at the lames' middle], "top" / "bot" [each part's edge lines s(theta)],
    "theta" [each part's reach], "foot" [her skin vertices under each part], "arming" (the arming cap's sheet or None),
    "arm_law"}. step / step_s / roll / laws: another tier's mesh over the same faces (no rolled edges, so no edge
    rows; the sides' laws as read: {side: {"law", "arm_law"}})."""
    t0, t1 = cfg["theta"]
    lm, cp, am = cfg["lames"], cfg.get("cop") or {}, cfg.get("arming")
    E = np.asarray(lm["edges"], float)
    n = len(E) - 1
    lth = lm.get("theta", cfg["theta"])
    # (each lame's own reach round the arm: one [a, b] for them all, or a list, one a lame from the cop down)
    pth = [tuple(map(float, x)) for x in lth] if np.ndim(lth) == 2 else [tuple(map(float, lth))] * max(n - 1, 1)
    assert len(pth) == max(n - 1, 1), "lames.theta: one [a, b] or one a lame"
    lt0, lt1 = pth[0]            # (lame 1's: the cop's wings are its ends past lame 1's)
    lap = list(lm.get("overlap") or [0.0] * n)
    per = lambda key, k, d: (lm[key][k] if isinstance(lm.get(key), list) else lm.get(key, d))  # noqa: E731
    clear, thick, margin = cfg["clear"], cfg["thick"], lm.get("margin", 0.002)
    # a lame laps under the plate above it only: never up past that plate's own exposed band (it would run under the
    # plate above that one too, inside its lap); a longer overlap asked is cut to it (reported: "lap_cut")
    lap_cut = {}
    for k in range(1, n):
        room_k = float(E[k] - E[k - 1]) - margin
        if lap[k] > room_k:
            lap_cut[k] = (lap[k], room_k)
            lap[k] = room_k
    rl = tuple(cfg.get("roll", (0.0045, 0.001))) if roll else None
    crl = tuple(cp.get("roll", cfg.get("roll", (0.0045, 0.001)))) if roll else None
    tf = cfg.get("tip_flare") or {}
    mirror = cfg.get("mirror", True)
    tm, arc = 0.5 * (lt0 + lt1), lm.get("arc", 0.0)

    def arcf(th, j=1):
        """The curve of the edge E[j] (the lames' edges: their ends rise `arc`), on the reach of the lame below it."""
        a, b = pth[min(max(j, 1), n - 1) - 1] if n > 1 else pth[0]
        return -arc * ((np.asarray(th, float) - 0.5 * (a + b)) / (0.5 * (b - a))) ** 2
    past = list((am or {}).get("past", (0.008, 0.010, 6.0)))
    out = {}
    frames = {sd: Frame.bones(ref, cfg["frame"]["from"].replace("*", sd), cfg["frame"]["to"].replace("*", sd), hand)
              for sd, hand in (("l", 1), ("r", -1))}
    ov, yk = cp.get("over"), (am or {}).get("yoke")
    up0 = min(float(E[0]), yk["to"]) if yk else E[0]     # (how far up the leather goes: the yoke's neck line)
    if ov:
        # the cop crowns her shoulder: the frame's centres stay under her skin's crest line up past the joint, read
        # from her skin (one drop for her two sides, the larger: the plates stay mirrors); the arm's own from lame 1 on
        keep = float(E[1] - (lap[1] if n > 1 else 0.0))
        crest = {sd: crest_line(ref, fr, up0 - past[0] - 0.05, keep) for sd, fr in frames.items()}
        drops = {sd: crest_drop(s, r, keep, ov.get("depth"), ov.get("ease", 0.006)) for sd, (s, r) in crest.items()}
        if mirror:
            drops = dict.fromkeys(drops, np.maximum(drops["l"], drops["r"]))
        frames = {sd: ShoulderFrame(fr, crest[sd][0], drops[sd]) for sd, fr in frames.items()}
    if laws is None:
        th_a = min([t0] + [a for a, _ in pth] + [((am or {}).get("theta") or [t0])[0]])
        th_b = max([t1] + [b for _, b in pth] + [((am or {}).get("theta") or [0, t1])[1]])
        plate = side_laws(ref, frames, (E[0] - 0.012, E[-1] + 0.012, th_a - 12, th_b + 12), clear, cfg.get("ease", 0.6), mirror,
                          cfg.get("grid", (0.002, 2.0)))
        arm = side_laws(ref, frames, (up0 - past[0] - 0.012, E[-1] + past[1] + 0.012, th_a - past[2] - 12, th_b + past[2] + 12),
                        am.get("clear", 0.0012), am.get("ease", 0.6), mirror, am.get("grid", (0.004, 4.0))) if am else {"l": None, "r": None}
        laws = {sd: {"law": plate[sd], "arm_law": arm[sd]} for sd in frames}
    bot = [lambda th, k=k: E[k + 1] + arcf(th, k + 1) for k in range(n)]
    ar = cp.get("arch")
    s_end = float(min(bot[0](t0), bot[0](t1))) - (ar or {}).get("span", 0.03)
    # the cop's wings: an end of it that reaches round past the lames' (lames' end, its own end), its corner rounded
    wg = cp.get("wing") or {}
    wings = [(tl, te) for tl, te in ((lt0, t0), (lt1, t1)) if wg and n > 1 and abs(te - tl) >= wg.get("min", 8.0)]
    w_end, edge0 = wg.get("end", 0.008), bot[0]

    def bot0(th):
        th = np.asarray(th, float)
        b = edge0(th)
        for tl, te in wings:
            b = b - max(float(edge0(te)) - s_end - w_end, 0.0) * np.clip((th - tl) / (te - tl), 0, 1) ** wg.get("power", 2.0)
        return b
    if wings:
        bot[0] = bot0

    def arch0(th):
        """The cop's upper edge: E[0], or with "arch" a rounded outline: E[0] at its middle, coming down to `span`
        above its lower edge at its two ends."""
        th = np.asarray(th, float)
        if not ar:
            return np.full(th.shape, float(E[0]))
        v = np.clip(np.abs(2.0 * th - t0 - t1) / (t1 - t0), 0, 1)
        return E[0] + (s_end - E[0]) * v ** ar.get("power", 2.6)
    # "reach": the cop reaches toward her neck only as far as her skin rides with it (reach_line: measured on her clips)
    rc = cp.get("reach")
    R = None if not rc else (laws[next(iter(frames))].get("reach")
                             or reach_line(ref, frames, {sd: laws[sd]["law"] for sd in frames}, arch0, bot[0], t0, t1, rc, mirror))
    hang = (cp.get("roll", cfg.get("roll", (0.0045, 0.001)))[0] + cfg.get("lip", 0.0012)) if rc else 0.0   # (its roll and wall hang past its edge)
    top0 = arch0 if R is None else (lambda th: np.maximum(arch0(th), np.interp(np.asarray(th, float), R["th"], R["line"]) + hang))
    top = [top0] + [lambda th, k=k: E[k] - lap[k] + arcf(th, k) for k in range(1, n)]
    reach = [(t0, t1)] + pth[:n - 1]
    crown = dome(top[0], bot[0], t0, t1, cp.get("apex", 0.014), cp.get("shape", (2.4, 2.4)))
    lie = cp.get("lie")

    def stand(s, th):
        """The cop over its law: its rim's stand-off and its crown; with "lie" both eased in from its upper edge, the
        edge itself `drop` under the law (by the arch's height there: nothing at the arch's ends)."""
        v = cp.get("rim", 0.0) + crown(s, th)
        if not lie:
            return v
        x = np.clip((np.asarray(s, float) - top0(th)) / lie.get("len", 0.03), 0, 1)
        g = np.clip((s_end - top0(th)) / max(s_end - float(E[0]), 1e-6), 0, 1) if ar else 1.0
        k = g * (1 - x * x * (3 - 2 * x))
        return v * (1 - k) - lie.get("drop", 0.0) * k
    cl = cp.get("close")
    am_out = (am or {}).get("thick", 0.0012)

    def closed(s, th):
        """ "close": how far down on her the cop is at (s, theta), 0..1: 1 along its upper edge and for `flat` down
        from it, easing to 0 over `len`; in full where that edge runs `fade` or more above the arch's ends' level."""
        x = np.clip((np.asarray(s, float) - top0(th) - cl.get("flat", 0.0)) / max(cl.get("len", 0.04), 1e-6), 0, 1)
        g = np.clip((s_end - top0(th)) / max(cl.get("fade", 0.03), 1e-6), 0, 1) if ar else 1.0
        return g * g * (3 - 2 * g) * (1 - x * x * (3 - 2 * x))
    for sd, fr in frames.items():
        base = laws[sd]["law"]
        arm_law = laws[sd]["arm_law"] if am else None

        def law_of(k, base=base, arm_law=arm_law):
            flare = bool(tf and k in tf.get("lames", []) and tf.get("rise"))

            def law(s, th):
                v = base(s, th)
                if flare:
                    v = v + tf["rise"] * np.clip((tf["from"] - np.asarray(th, float)) / (tf["from"] - tf["to"]), 0, 1.2) ** tf.get("power", 2.0)
                if k == 0:      # (the cop: a standing dome over its rim's surface)
                    v = v + stand(s, th)
                    if cl:      # (its neck end down on the arming cap's outer face, or her skin's own surface)
                        on = (arm_law(s, th) + am_out) if arm_law is not None else base(s, th) - clear
                        kk = closed(s, th)
                        v = v * (1 - kk) + np.minimum(on + cl.get("room", 0.001), v) * kk
                    if R is not None:   # (its neck rim stands off her by what it sinks at its line, over the leather)
                        a = top0(th)
                        on = (arm_law(a, th) + am_out) if arm_law is not None else base(a, th) - clear
                        # (the lowest thing at its edge is its wall's foot, `lip` under its inner face)
                        need = np.maximum(on + np.interp(np.asarray(th, float), R["th"], R["sink"]) + rc.get("room", 0.001)
                                          + cfg.get("lip", 0.0012) - base(a, th) - stand(a, th), 0.0)
                        x = np.clip((np.asarray(s, float) - a) / max(rc.get("len", 0.02), 1e-6), 0, 1)
                        v = v + need * (1 - x * x * (3 - 2 * x))
                return v
            return law if (flare or k == 0) else base

        kw = dict(clear=clear, lip=cfg.get("lip", 0.0012), step=step or cfg.get("step", 0.008),
                  step_s=step_s or cfg.get("step_s", 0.006))
        sheets = [None] * n
        # (from the last lame up: each plate reads the one beneath it)
        for k in range(n - 1, -1, -1):
            low = sheets[k + 1] if k + 1 < n else None
            zs = (lambda th, k=k: top[k + 1](th) - margin) if low is not None else None
            law = law_of(k)
            rise = tilt(law, top[k], bot[k], low, zs, per("gap", k + 1 if low is not None else k, 0.003),
                        flare=lm.get("last_flare", 0.0),
                        curl=[(tl, te, wg.get("curl", 1.0)) for tl, te in wings] if k == 0 else None)
            on = ("tb01" if k == 0 else "b01") if roll else ""
            sheets[k] = Lame(fr, law, reach[k][0], reach[k][1], top[k], bot[k], cp.get("thick", thick) if k == 0 else thick,
                             roll=crl if k == 0 else rl, ridge=cp.get("ridge") if k == 0 else None, roll_on=on, rise=rise,
                             **kw).freeze()
        spans = [(float(top[k](tm)), float(bot[k](tm))) for k in range(n)]
        # (what a plate's ride reads: her skin under its exposed band and `ride_reach` up past it, not its whole lap:
        # the band hidden under the plate above is that plate's skin; the cop: its "ride_band" when it names one)
        up = lm.get("ride_reach", 0.006)
        band = [cp.get("ride_band") or (top[0], bot[0])] + [(E[k] - min(lap[k], up), E[k + 1]) for k in range(1, n)]
        foot = [footprint(ref, fr, band[k][0], band[k][1], reach[k][0], reach[k][1]) for k in range(n)]
        arming = None
        if am:
            # the arming cap: a leather shell on her skin (a bendy part), `past` beyond the plates' OUTLINE: over the
            # cop's upper edge as it runs, down the cop's sides, then in to the lames' (never a wide flap beside them)
            arl = tuple(am.get("roll", (0.004, 0.0008))) if roll else None
            sm = lambda x: np.clip(x, 0, 1) ** 2 * (3 - 2 * np.clip(x, 0, 1))  # noqa: E731
            w = lambda s: sm((np.asarray(s, float) - E[1]) / 0.012)  # noqa: E731  (0 beside the cop, 1 beside the lames)
            ww = lambda s: sm((np.asarray(s, float) - s_end - w_end) / max(E[1] - s_end - w_end, 1e-6))  # noqa: E731  (down a wing's corner)
            w0, w1 = (ww if (lt0, t0) in wings else w), (ww if (lt1, t1) in wings else w)
            atop = lambda th: np.min([top[0](np.clip(np.asarray(th, float) + d, t0, t1))  # noqa: E731
                                      for d in np.linspace(-past[2], past[2], 5)], axis=0) - past[0]
            if yk:   # (the yoke: the leather runs on up her trapezius to its neck line, an arch down to the cop's ends)
                cap_top = atop
                atop = lambda th: np.minimum(cap_top(th), yk["to"] + (s_end - past[0] - yk["to"])  # noqa: E731
                                             * np.clip(np.abs(2.0 * np.asarray(th, float) - t0 - t1) / (t1 - t0), 0, 1) ** yk.get("power", 2.2))
            a_lo = lambda s: t0 - past[2] + (lt0 - t0) * w0(s)  # noqa: E731
            a_hi = lambda s: t1 + past[2] + (lt1 - t1) * w1(s)  # noqa: E731
            if am.get("theta"):
                # its own reach: at least "theta" round the arm all along (it covers her where no steel is: the
                # deltoid's front and back beside narrow top plates), and `past` round beyond whichever plate is at s
                ca, cb = am["theta"]
                R0, R1 = np.array([r[0] for r in reach]), np.array([r[1] for r in reach])

                def side_at(s, R):
                    s = np.asarray(s, float)
                    return np.mean([R[np.clip(np.searchsorted(E, s + d, side="right") - 1, 0, n - 1)]
                                    for d in np.linspace(-0.006, 0.006, 5)], axis=0)
                a_lo = lambda s: np.minimum(ca, side_at(s, R0) - past[2])  # noqa: E731
                a_hi = lambda s: np.maximum(cb, side_at(s, R1) + past[2])  # noqa: E731
            lr = pth[-1]
            arming = Sheet(fr, laws[sd]["arm_law"], a_lo, a_hi, atop,
                           lambda th: E[-1] + past[1] + arcf(np.clip(th, *lr), n), am.get("thick", 0.0012), roll=arl,
                           clear=am.get("clear", 0.0012), lip=am.get("lip", 0.0003), step=step or am.get("step", 0.009),
                           step_s=step_s or am.get("step", 0.009), roll_on="tb01" if roll else "")
        out[sd] = {"fr": fr, "law": base, "arm_law": laws[sd]["arm_law"], "sheets": sheets, "names": part_names(n, sd),
                   "spans": spans, "top": top, "bot": bot, "theta": reach, "foot": foot, "lap": lap, "arming": arming,
                   "lap_cut": lap_cut}
        if R is not None:
            out[sd]["reach"] = R

    return out


# ---------------------------------------------------------------- the reach rule, the yoke

def reach_line(ref, frames, laws, arch, bot, t0, t1, rc, mirror=True):
    """The reach rule on the cop ("cop.reach" {"sink_max", "clips" ("all" | "four" | [names]), "margin", "len", "room",
    "zone"}): a rigid plate reaches only as far as her skin rides with it. On an (s, theta) grid of the plate's law
    surface (riding the mean ride of its own outline) native_travel.sink reads how far each point comes down toward
    her MOVING skin over the clips; per column, from its seat (its least-travel row on the arm's side of the joint)
    toward her neck, the last row still under `sink_max` is the LINE: the cop's upper edge is cut back to it (+ margin;
    her two sides' larger; a running max and an ease round theta). The ride changes with the cut, so the line is read
    `passes` times from the joint. Returns {"th", "line" (s per column), "sink" (the travel at the line: what the rim
    stands off by), "arch" (the uncut edge), "no_seat" (columns with no row under the limit), "sides"}."""
    import native_travel as nt
    from scipy import ndimage
    lim, clips = rc["sink_max"], rc.get("clips", "all")
    th = np.linspace(t0, t1, int(rc.get("columns", 27)))
    ss = np.arange(float(np.min(arch(th))), float(np.max(bot(th))) + 1e-9, rc.get("ds", 0.004))
    SS, TH = np.meshgrid(ss, th, indexing="ij")
    own = (SS >= arch(TH) - 1e-9) & (SS <= bot(TH) + 1e-9)
    line, info, bad = np.maximum(arch(th), rc.get("start", 0.0)), {}, set()
    cut = lambda ln: (lambda t: np.maximum(arch(t), np.interp(np.asarray(t, float), th, ln)))  # noqa: E731
    for _ in range(int(rc.get("passes", 3))):
        cols, bad = [], set()
        for sd, fr in frames.items():
            rule = mean_ride(ref, footprint(ref, fr, cut(line), bot, t0, t1))
            sk = nt.sink(ref, fr.pt(SS, TH, laws[sd](SS, TH)).reshape(-1, 3), rule, clips)[0].reshape(SS.shape)
            col = np.zeros(len(th))
            for j in range(len(th)):
                rows = np.flatnonzero(own[:, j])
                arm = rows[ss[rows] >= 0.0] if (ss[rows] >= 0.0).any() else rows
                i = int(arm[np.argmin(sk[arm, j])])
                if sk[i, j] > lim:
                    bad.add(round(float(th[j]), 1))
                while i > rows[0] and sk[i - 1, j] <= lim:
                    i -= 1
                col[j] = ss[i]
            cols.append(col)
            info[sd] = {"ride": rule, "raw_mm": (col / MM).round(1).tolist()}
        raw = ndimage.maximum_filter1d(np.max(cols, axis=0), 3, mode="nearest")
        line = np.maximum(arch(th), ndimage.gaussian_filter1d(raw, rc.get("ease", 1.0), mode="nearest") + rc.get("margin", 0.004))
    at = []
    for sd, fr in frames.items():
        rule = mean_ride(ref, footprint(ref, fr, cut(line), bot, t0, t1))
        at.append(nt.sink(ref, fr.pt(line, th, laws[sd](line, th)), rule, clips)[0])
    return {"th": th, "line": line, "sink": ndimage.maximum_filter1d(np.max(at, axis=0), 3, mode="nearest"), "arch": arch(th),
            "no_seat": sorted(bad), "sides": info}


def reach_report(cfg, lay, by, rim_of, rules, ref, rep):
    """The reach rule on what was BUILT: rep["reach"] (the line, the travel at it, each checked part's sink over the
    clips), and the reasons the build fails (a plate past its line: its edge beyond it, or its edge zone sinking more
    than the limit; a rigid extra part over the limit)."""
    rc = (cfg.get("cop") or {}).get("reach")
    if not rc:
        return []
    import native_travel as nt
    R = next(iter(lay.values()))["reach"]
    lim, clips, zone = rc["sink_max"], rc.get("clips", "all"), rc.get("zone", 0.012)
    line = lambda t: np.interp(t, R["th"], R["line"])  # noqa: E731
    mm = lambda v: [round(float(x) / MM, 1) for x in v]  # noqa: E731
    out = rep["reach"] = {"limit_mm": lim / MM, "clips": clips, "theta": R["th"].round(1).tolist(), "line_mm": mm(R["line"]),
                          "uncut_mm": mm(R["arch"]), "cut_mm_max": round(float((R["line"] - R["arch"]).max()) / MM, 1),
                          "sink_at_line_mm": mm(R["sink"]), "no_seat_theta": R["no_seat"], "sides": {}, "past": []}
    over = [f"no row of the cop under {lim / MM} mm at theta {t}" for t in R["no_seat"]]
    for sd, L in lay.items():
        fr, name = L["fr"], L["names"][0]
        o = out["sides"][sd] = {"line_ride": R["sides"][sd]["ride"], "line_raw_mm": R["sides"][sd]["raw_mm"]}
        P = np.vstack([by[name].P] + [by[r].P for r, h in rim_of.items() if h == name])
        s, th, _ = fr.cyl(P)
        edge = P[s < line(th) + zone]
        q, n, _ = ref.closest(edge)
        res = nt.past(ref, edge, rules[name]["bones"], lim, clips)
        res.update({"edge_past_line_mm": round(float((line(th) - s).max()) / MM, 2),
                    "rim_rest_standoff_mm": round(float(((edge - q) * n).sum(1).min()) / MM, 2)})
        if rc.get("report_all", True) and clips != "all":
            res["all_clips"] = nt.past(ref, edge, rules[name]["bones"], lim, "all")
        o[name] = res
        if res["past"] or res["edge_past_line_mm"] > 1.5:
            over.append(f"{name}: its neck edge sinks {res['sink_mm']} mm into her (limit {lim / MM}) at {res['worst']}, "
                        f"{res['edge_past_line_mm']} mm past its line")
        for nm in L.get("extra_rules") or {}:
            o[nm] = nt.past(ref, by[nm].P, rules[nm]["bones"], lim, clips)
            if o[nm]["past"]:
                over.append(f"{nm}: sinks {o[nm]['sink_mm']} mm into her (limit {lim / MM}) at {o[nm]['worst']}")
    out["past"] = over
    return over


def yoke_names(sd):
    """The yoke's parts of a side: its leather, its bound edge, the strap that hangs the cop, the strap's buckle."""
    return [f"yoke_{sd}_cap", f"yokebind_{sd}_cap", f"yokestrap_{sd}_cap", f"yokebuckle_{sd}_cap"]


def _sub(p, name, material, T):
    used = np.zeros(len(p.P), bool)
    used[T] = True
    return Part(name, material, p.P[used], (np.cumsum(used) - 1)[T], p.uv0[used], p.uv1[used], p.col[used], p.N[used])


def yoke_parts(cfg, L, sd, p, ref=None):
    """ "arming.yoke" {"to", "power", "under", "strap" {"theta", "len", "tuck", "width", "thick", "buckle"}}: the
    arming cap GROWN up her trapezius to the line s = `to` (an arch down to the cop's ends), as parts of the one
    built sheet `p`: the arming cap as it was (under the plates), the YOKE (all of it above the cop's upper edge and
    `under` in under that edge, materials.yoke: the leather's own colour step), its BOUND edge (the sheet's rolled
    edge there, materials.binding), and with a body the STRAP that hangs the cop (from `len` up the yoke to `tuck`
    under the cop's rim, materials.strap) and its BUCKLE (skinned too: a rigid buckle on its own skin's mean ride
    sank 8-12 mm there, past the reach rule). None of these has a rule: they are skinned, they ride her skin. Nothing of hers is trimmed."""
    am, mats = cfg["arming"], cfg.get("materials", {})
    yk, fr, top, cop = am["yoke"], L["fr"], L["top"][0], L["sheets"][0]
    n = yoke_names(sd)
    s, th, _ = fr.cyl(p.P[p.T].mean(1))
    up = s < top(np.clip(th, cop.t0, cop.t1)) + yk.get("under", 0.01)
    roll = (p.col[p.T, 3] < 0.5).all(1)
    out = [_sub(p, p.name, p.material, p.T[~up]), _sub(p, n[0], mats.get("yoke", "brownleather"), p.T[up & ~roll])]
    if (up & roll).any():
        out.append(_sub(p, n[1], mats.get("binding", p.material), p.T[up & roll]))
    st = yk.get("strap")
    if st and ref is not None:
        t, a = st.get("theta", 100.0), float(top(np.array(st.get("theta", 100.0))))
        ss = np.linspace(a - st.get("len", 0.035), a + st.get("tuck", 0.008), 12)
        tt = np.full(len(ss), t)
        leather = am.get("clear", 0.0012) + am.get("thick", 0.0012)
        strap, _ = nb.skin_band(ref, fr.pt(ss, tt, L["arm_law"](ss, tt)), st.get("width", 0.016), st.get("thick", 0.0016), n[2],
                                mats.get("strap", p.material), lift=leather + 0.0004)
        out.append(strap)
        sb = np.array(a - st.get("buckle", 0.014))
        q, nq, _ = ref.closest(fr.pt(sb, np.array(t), L["arm_law"](sb, np.array(t)))[None])
        c = q[0] + nq[0] * (leather + st.get("thick", 0.0016))
        m = np.array([fr.hand, 1.0, 1.0])
        b = nb.buckle(c * m, nq[0] * m, -fr.a * m, w=st.get("width", 0.016) + 0.007, h=0.015, name=n[3], material=mats.get("rim", mats.get("plate", "steel")))
        if fr.hand < 0:
            b.P, b.N, b.T = b.P * m, b.N * m, b.T[:, ::-1]
        out.append(b)
    return out


def seat_sides(built, ref, floor, mirror=True):
    """nb.seat on a part's two sides {"l", "r"} as one: a point either side's skin stands closer to than `floor` moves
    out on BOTH by the larger need, along the two skins' mean normal (her two sides are not mirrors to the millimetre;
    the plates stay mirrors). Returns how many points moved."""
    if not (mirror and set(built) == {"l", "r"} and built["l"].P.shape == built["r"].P.shape):
        return sum(nb.seat(p, ref, floor) for p in built.values())
    m = np.array([-1.0, 1.0, 1.0])
    need, nrm = [], []
    for sd in "lr":
        q, n, _ = ref.closest(built[sd].P)
        need.append(np.maximum(floor - ((built[sd].P - q) * n).sum(1), 0.0))
        nrm.append(n if sd == "l" else n * m)
    d = nb.U(nrm[0] + nrm[1]) * np.maximum(need[0], need[1])[:, None]
    moved = int((np.abs(d).max(1) > 0).sum())
    if moved:
        built["l"].P = built["l"].P + d
        built["r"].P = built["r"].P + d * m
        for p in built.values():
            p.N = nb.vertex_normals(p.P, p.T)
    return moved


def build_parts(cfg, lay, ref=None, rivets=True):
    """The mesh parts of a layout: per plate its steel (its lap rivets joined in) and its rolled rim (its own part);
    per side the arming cap."""
    mats = cfg.get("materials", {"plate": "steel", "rim": "steel"})
    rv_ = cfg.get("rivet") or {}
    r_riv, h_riv, r_in = rv_.get("r", 0.0022), rv_.get("h", 0.0012), rv_.get("in", 0.011)
    n = len(next(iter(lay.values()))["sheets"])
    # every sheet as built, its two sides seated as one
    raw = {k: {sd: L["sheets"][k].build(L["names"][k], mats["plate"], ao=1.0 if k == 0 else 0.94) for sd, L in lay.items()}
           for k in range(n)}
    raw["arming"] = {sd: L["arming"].build(arming_name(sd), mats.get("arming", "darkleather"), ao=0.85)
                     for sd, L in lay.items() if L.get("arming") is not None}
    if ref is not None:
        for k, built in raw.items():
            seat_sides(built, ref, 0.0005 if k == "arming" else cfg.get("seat", 0.0012), cfg.get("mirror", True))
    parts, rims = [], {}
    for sd, L in lay.items():
        for k, (sh, name) in enumerate(zip(L["sheets"], L["names"])):
            plate, rim = split_rim(raw[k][sd], f"rim{k}_{sd}_rigid", mats.get("rim", mats["plate"]))
            riv = []
            if rivets and k + 1 < n:
                # the articulation rivets: on the band lapping the lame beneath, at that lame's two ends
                w = sh.roll[0] if sh.roll else 0.0
                # (the lap's two ends: where both plates are)
                a, b = max(L["theta"][k][0], L["theta"][k + 1][0]), min(L["theta"][k][1], L["theta"][k + 1][1])
                for th_e, sgn in ((a, 1), (b, -1)):
                    th_r = np.array(th_e + sgn * np.degrees(r_in / float(sh.law(L["spans"][k][1], th_e))))
                    s_r = np.array(float(sh.bot(th_r)) - max(0.5 * L["lap"][k + 1], w + r_riv + 0.0015))
                    c, nn = sh.at(s_r, th_r)
                    # (her right side's rivet is the mirror of one made on her left: the two sides stay mirrors)
                    m = np.array([sh.fr.hand, 1.0, 1.0])
                    rv = nb.rivet(c * m, nn * m, r=r_riv, h=h_riv, name=name, material=mats["plate"])
                    if sh.fr.hand < 0:
                        rv.P, rv.N, rv.T = rv.P * m, rv.N * m, rv.T[:, ::-1]
                    riv.append(rv)
            parts.append(Part.join(name, mats["plate"], [plate] + riv) if riv else plate)
            if rim is not None:
                parts.append(rim)
                rims[rim.name] = name
        if sd in raw["arming"]:
            p = raw["arming"][sd]
            if (cfg.get("arming") or {}).get("yoke"):
                parts += yoke_parts(cfg, L, sd, p, ref if rivets else None)
            else:
                parts.append(Part(p.name, p.material, p.P, p.T, p.uv0, p.uv1, p.col, p.N))
    return parts, rims


def edge_report(sh, ref, n=25):
    """Her skin's distance under a sheet's inner face along each edge and over its face, mm (min, max)."""
    ss = np.linspace(-0.2, 0.4, 61)    # (a side that is a line theta(s): the reach every s has)
    t = np.linspace(float(np.max(sh.side(0, ss))), float(np.min(sh.side(1, ss))), n)
    X, TH = np.meshgrid(np.linspace(0, 1, 9), t, indexing="ij")
    S = sh.top(TH) + X * (sh.bot(TH) - sh.top(TH))
    X = sh.fr.pt(S, TH, sh.inner(S, TH) if hasattr(sh, "inner") else sh.law(S, TH))
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


def part_bend(cfg, k):
    """Sheet k's "bend" rule (gear_native.part_blends), or None: the cop's from cop.bend, lame k's from lames.bend (one
    dict for every lame, or a list, one entry (dict or null) per lame)."""
    b = (cfg.get("cop") or {}).get("bend") if k == 0 else (cfg.get("lames") or {}).get("bend")
    if isinstance(b, list):
        b = b[k - 1] if k - 1 < len(b) else None
    return json.loads(json.dumps(b)) if b else None


def spaulder(pid, cfg, out=None, ref=None, laws=None):
    cfg = resolve(cfg)
    ref = ref or nb.Ref.her()
    lm = cfg["lames"]
    lay = layout(cfg, ref, laws=laws)
    parts, rim_of = build_parts(cfg, lay, ref)
    by = {p.name: p for p in parts}
    rules, sockets, rims, rep = {}, {}, {}, {"id": pid, "sides": {}}
    for sd, L in lay.items():
        r = rep["sides"][sd] = {"law": {"no_hit": L["law"].no_hit, "eased_mm": round(L["law"].eased / MM, 2),
                                        "lift_mm": round(L["law"].add / MM, 2), "sides_differ_mm": getattr(L["law"], "sides_mm", None)}}
        if L.get("lap_cut"):
            rep["lap_cut_mm"] = {str(k): [round(v / MM, 1) for v in ab] for k, ab in L["lap_cut"].items()}
        for k, (sh, name) in enumerate(zip(L["sheets"], L["names"])):
            given = lm.get("rides", "mean")
            rule = {"bones": mean_ride(ref, L["foot"][k])} if given == "mean" else json.loads(json.dumps(given[k]))
            if "bones" in rule:
                rule.setdefault("carry", lm.get("carry", "none"))
                bend = part_bend(cfg, k)
                if bend:
                    rule.setdefault("bend", bend)
            rules[name] = rule
            tm = 0.5 * sum(L["theta"][k])
            c, nn = sh.at(np.array(0.5 * sum(L["spans"][k])), np.array(tm))
            sockets[name[:-6]] = {"point": c.round(5).tolist(), "normal": nn.round(5).tolist(), "up": (-L["fr"].a).round(5).tolist()}
            r[name] = {"s_mm": [round(v / MM, 1) for v in L["spans"][k]], "foot_points": int(len(L["foot"][k])),
                       "ride": rule.get("bones", rule), "skin_under_mm": edge_report(sh, ref)}
        top, low = L["sheets"][0], L["sheets"][-1]
        te = np.linspace(top.t0, top.t1, 12)
        rims[f"top_rim_{sd}"] = {"points": top.at(top.top(te), te)[0].round(5).tolist()}
        te = np.linspace(low.t0, low.t1, 12)
        rims[f"arm_rim_{sd}"] = {"points": low.at(low.bot(te), te)[0].round(5).tolist()}
        if L["arming"] is not None:     # (a bendy part: no rule, it follows her skin)
            r[arming_name(sd)] = {"tris": int(len(by[arming_name(sd)].T)), "skin_under_mm": edge_report(L["arming"], ref),
                                  "under_plates_mm": arming_room(L)}
    for rim, name in rim_of.items():
        rules[rim] = {"with": name}
    for L in lay.values():      # (the yoke's buckle: a rigid part on its own skin's mean ride)
        for name, rule in (L.get("extra_rules") or {}).items():
            rules[name] = {**rule, "carry": lm.get("carry", "none")}
    over = reach_report(cfg, lay, by, rim_of, rules, ref, rep)
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
    pairs = list(zip(lay["l"]["names"], lay["r"]["names"])) + ([(arming_name("l"), arming_name("r"))] if arming_name("l") in by else [])
    rep["mirror_mm_max"] = round(max(float(np.abs(by[a].P * [-1, 1, 1] - by[b].P).max()) if by[a].P.shape == by[b].P.shape else 1e3
                                     for a, b in pairs) / MM, 3)
    piece = dict(cfg["piece"])
    piece.update({"id": pid, "native": {"rest_body": ref.rest_body, "rest_hash": ref.hashes, "builder": "tools/armor/native_build.py",
                                        "recipe": cfg["recipe"]}, "parts": rules})
    sj = {"id": pid, "slot": piece["slot"], "body_hash": ref.hashes.get("close"),
          "space": "glTF / Godot: Y up, metres, her_b's rest (native_build)", "sockets": sockets, "rims": rims, "fixings": []}
    if over:     # (a plate past its line: no piece is written, the report says which and by how much)
        d = out or os.path.join(nb.NATIVE, pid)
        os.makedirs(d, exist_ok=True)
        json.dump(rep, open(os.path.join(d, "build_report.json"), "w"), indent=1)
        raise SystemExit("native_spaulder: past the reach rule's line (cop.reach): " + "; ".join(over))
    d = nb.write_piece(pid, piece, parts, sj, out)
    rep["dir"] = os.path.relpath(d, nb.REPO).replace("\\", "/")
    rep["tris"] = int(sum(len(p.T) for p in parts))
    rep["parts"] = {p.name: [int(len(p.P)), int(len(p.T)), p.material] for p in parts}
    # the play tier's mesh: the same faces at a coarse step, no rolled edges, walls or rivets
    pl = cfg.get("play") or {}
    lod, _ = build_parts(cfg, layout(cfg, ref, pl.get("step", 0.014), pl.get("step_s", 0.012), roll=False,
                                     laws={sd: {"law": L["law"], "arm_law": L["arm_law"], **({"reach": L["reach"]} if "reach" in L else {})}
                                           for sd, L in lay.items()}), ref, rivets=False)
    import gear_native as gn
    gn.write_glb(os.path.join(d, f"{pid}.lod1.glb"), [p.node() for p in lod], {"native_build": {"piece": pid, "tier": "play"}})
    rep["play_tris"] = int(sum(len(p.T) for p in lod))
    json.dump(rep, open(os.path.join(d, "build_report.json"), "w"), indent=1)
    return rep


def arming_room(L, n=21):
    """The room between the arming cap's outer face and each plate's inner face over that plate, mm (min)."""
    am, out = L["arming"], {}
    for sh, name in zip(L["sheets"], L["names"]):
        X, TH = np.meshgrid(np.linspace(0, 1, 9), np.linspace(sh.t0, sh.t1, n), indexing="ij")
        S = sh.top(TH) + X * (sh.bot(TH) - sh.top(TH))
        out[name] = round(float((sh.inner(S, TH) - am.outer(S, TH)).min()) / MM, 2)
    return out


RECIPES = {"spaulder": spaulder}
