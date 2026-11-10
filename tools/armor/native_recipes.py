"""Recipes of the native armor builder: a recipe turns a piece's build.json into its piece dir with native_build's
primitives. `limb_plate`: a plate over part of a limb, articulated lames below it down to its far joint (each riding
its own blend of bones and lapping OVER the one above), lames above it where another bone owns her skin, straps and
fixings (the cuisses; any limb by its bones and params). A helm adds its own recipe here; nothing below is specific
to one piece."""
import json
import os

import numpy as np

import native_build as nb
from native_build import MM, Frame, Law, Part, Sheet, U


def climb(fr, ref, path, sheets, base=0.0004, slope=0.55, over=0.0014):
    """A strap's lift along its path: its base on bare skin, the height of the plate it crosses (+ over, clearing a
    rolled edge), easing down beside the plate at `slope`. Returns (points on the skin, lifts, on-plate rows)."""
    q, n, _ = ref.closest(path)
    s, th, rho = fr.cyl(q)
    lift, on = np.full(len(q), base), np.zeros(len(q), bool)
    for sh in sheets:
        d = sh.edge_d(s, th)
        inside = d > -0.0005
        lift = np.where(inside, np.maximum(lift, sh.outer(s, th) - rho + over), lift)
        on |= d > 0.0015
    step = np.r_[0, np.linalg.norm(np.diff(q, axis=0), axis=1)]
    for k in range(1, len(q)):
        lift[k] = max(lift[k], lift[k - 1] - slope * step[k])
    for k in range(len(q) - 2, -1, -1):
        lift[k] = max(lift[k], lift[k + 1] - slope * step[k + 1])
    return q, lift, on


def lap_room(above, law, gap, slide, n=5):
    """The lift h(s, theta) of a lame's lapping band over the sheet `above` it: `gap` clear of that sheet's outer face
    wherever the lame may lie along it, from 2 mm up-limb of its rest to `slide` down-limb (a lame that takes a share
    of the next bone slides toward the joint as it bends, onto a limb that widens there)."""
    def h(s, th):
        s, th = np.broadcast_arrays(np.asarray(s, float), np.asarray(th, float))
        top = np.max([above.outer(np.minimum(s + d, above.bot(th)), th) for d in np.linspace(-0.002, slide, n)], axis=0)
        return np.maximum(top + gap - law(s, th), 0.0)
    return h


def taper(th_a, th_b, s_b, over):
    """A side edge theta(s): th_a down to s_b - over, easing to th_b at s_b and below (a plate's side running into
    the lames under it)."""
    return lambda s: th_a + (th_b - th_a) * nb.smooth((np.asarray(s, float) - (s_b - over)) / over)


def limb_plate(pid, cfg, out=None, ref=None):
    """build.json: "theta" [t0, t1] and "top" {"through": [[theta, s], ..]} the plate (its top edge runs through its
    points); "bottom" {"rim_of", "nodes", "below"}: the piece ends `below` under another built piece's rim (the spec
    bottom); "spec_top" {"points"}: the top its length is counted from; "lames" {"count", "plate_share" (the plate's
    share of the spec length), "under" (the plate's hidden band under the first lame), "overlap", "theta", "taper"
    (the plate's sides ease to the lames' over its lowest `taper`), "rides" [a part rule each], "clear" / "gap" /
    "slide" (a number, or one a lame: its clearance, the room between its lapping band and the sheet above, how far
    it slides down that sheet in motion), "ease", "flare" {h, band} of the last one's end}: lames from the plate
    down to the spec bottom, the lower over the upper; "hip_lames" [{"theta", "top" {"points"},
    "under", "ride", ..}]: lames above the plate, the plate's top band over them; straps as before."""
    ref = ref or nb.Ref.her()
    t0, t1 = cfg["theta"]
    lm, hips = cfg.get("lames") or {}, cfg.get("hip_lames") or []
    n_l = int(lm.get("count", 0))
    lt0, lt1 = lm.get("theta", (t0, t1))
    th_lo = min([t0, lt0] + [h["theta"][0] for h in hips])
    th_hi = max([t1, lt1] + [h["theta"][1] for h in hips])
    parts, sockets, rims, rep, rules = [], {}, {}, {"id": pid, "sides": {}}, {}
    mats = cfg.get("materials", {"plate": "steel", "strap": "darkleather"})
    roll, lip, step = tuple(cfg["roll"]), cfg.get("lip", 0.0012), cfg.get("step", 0.011)
    at5 = np.array([lt0, 0.0, 45.0, 90.0, lt1])
    mm = lambda v: [round(float(x) / MM, 1) for x in np.atleast_1d(v)]  # noqa: E731
    for sd, hand in (("l", 1), ("r", -1)):
        fr = Frame.bones(ref, cfg["frame"]["from"].replace("*", sd), cfg["frame"]["to"].replace("*", sd), hand)
        L = fr.L
        r = rep["sides"][sd] = {}
        # --- the spec bottom (under another built piece's rim), the plate's top line, the lames' lines
        rim_cfg = cfg["bottom"]
        Vg, Tg = nb.read_mesh(os.path.join(nb.REPO, rim_cfg["rim_of"]), rim_cfg.get("nodes"), hand)
        sg, thg, rg = fr.cyl(Vg)
        cut = (rg < 0.25) & (sg > 0.5 * L) & (sg < 1.2 * L)
        bins = np.linspace(t0 - 8, t1 + 8, 14)
        rim_s = np.array([sg[cut & (np.abs(thg - b) < 7)].min() if (cut & (np.abs(thg - b) < 7)).any() else np.nan for b in bins])
        ok = np.isfinite(rim_s)
        rim = nb.edge_curve(bins[ok], rim_s[ok], deg=4)
        end = lambda th: rim(th) + rim_cfg.get("below", 0.0)  # noqa: E731
        pts = np.array(cfg["top"]["through"], float)
        top = nb.edge_points(pts[:, 0], pts[:, 1])
        if n_l:
            sp = np.array(cfg["spec_top"]["points"], float)
            tt = np.linspace(th_lo, th_hi, 24)
            spec = np.interp(tt, sp[:, 0], sp[:, 1])
            a1 = nb.edge_curve(tt, spec + lm["plate_share"] * (end(tt) - spec), deg=4)   # the plate's visible end
            line = lambda k: (lambda th, k=k: a1(th) + (k / n_l) * (end(th) - a1(th)))  # noqa: E731
            bot = lambda th: a1(th) + lm["under"]  # noqa: E731
        else:
            a1 = bot = end
        r["top_mm"], r["plate_end_mm"], r["end_mm"], r["rim_mm"] = mm(top(at5)), mm(a1(at5)), mm(end(at5)), mm(rim(at5))
        # --- her limb's surface and the smooth law above it (the skin a part lies over shapes it; the rest guides it)
        hip_lines = []
        for h in hips:
            hp = np.array(h["top"]["points"], float)
            hip_lines.append((nb.edge_points(hp[:, 0], hp[:, 1]), (lambda th, u=h["under"]: top(th) + u)))
        s_lo = min([float(top(np.linspace(t0, t1, 40)).min())] + [float(f(np.linspace(*h["theta"], 20)).min()) for (f, _), h in zip(hip_lines, hips)]) - 0.012
        s_hi = float(end(np.linspace(th_lo, th_hi, 40)).max()) + 0.012
        dom = (s_lo, s_hi, th_lo - 12, th_hi + 12)
        Tn = nb.near(ref.V, ref.T, fr, s_lo - 0.08, s_hi + 0.08, 0.26)
        S, TH = np.meshgrid(np.linspace(s_lo, s_hi, 72), np.linspace(dom[2], dom[3], 56), indexing="ij")
        rho, _ = nb.radial(ref.V, Tn, fr, S, TH, 0.26)
        over = (S > top(TH) - 0.012) & (TH > t0 - 9) & (TH < max(t1, lt1) + 9)
        near = S > top(TH) - 0.04
        for (f, g), h in zip(hip_lines, hips):
            ins = (TH > h["theta"][0] - 9) & (TH < h["theta"][1] + 9)
            over |= ins & (S > f(TH) - 0.012) & (S < g(TH) + 0.012)
            near |= ins & (S > f(TH) - 0.04)
        rho = np.where(near, rho, np.nan)
        env = Law.envelope(S, TH, rho, deg=tuple(cfg.get("law_deg", (7, 7))), dom=dom, over=cfg.get("law_over", 30.0), soft=~over)
        r["law"] = {"rms_mm": round(env.rms / MM, 2), "lift_mm": round(env.add / MM, 2), "no_hit": int((np.isnan(rho) & over).sum())}
        # --- the sheets: the plate, the lames below it (each over the one above), the lames above it (under its top)
        sides = [t0, t1]
        if n_l and lm.get("taper"):
            sides = [taper(a, b, float(a1(b)), lm["taper"]) if a != b else a for a, b in ((t0, lt0), (t1, lt1))]
        ridge = dict(cfg["ridge"], stop=(lm["under"] + 0.002) if n_l else 0.0) if cfg.get("ridge") else None
        lift_top = None
        if hips:
            h0 = hips[0]
            lift_top = {"band": h0["under"] + 0.002, "ease": h0.get("ease", 0.012), "theta": [h0["theta"][0] - 10, h0["theta"][0] - 2],
                        "h": h0.get("clear", cfg["clear"]) + h0["thick"] + roll[1] - cfg["clear"] + h0.get("gap", 0.0008)}
        plate = Sheet(fr, env.plus(cfg["clear"]), sides[0], sides[1], top, bot, cfg["thick"], roll=roll, ridge=ridge, clear=cfg["clear"],
                      lip=lip, step=step, roll_on="t01" if n_l else "tb01", lift_top=lift_top)
        p_plate = plate.build(f"plate_{sd}_rigid", mats["plate"])
        rules[p_plate.name] = cfg["ride"]
        sheets, built = [plate], [p_plate]
        Tc = nb.near(Vg, Tg, fr, 0.5 * L, 1.3 * L, 0.3)

        def cap(s, th, fr=fr, Tc=Tc, Vg=Vg):   # (the last lame's end stays under the piece whose rim it tucks under)
            cop, _ = nb.radial(Vg, Tc, fr, s, th, 0.3)
            return np.where(np.isfinite(cop), cop - lm.get("under_gap", 0.0008), np.inf)

        per = lambda key, k, d=None: (lm[key][k] if isinstance(lm.get(key), list) else lm.get(key, d))  # noqa: E731
        for k in range(n_l):
            last = k == n_l - 1
            lap = lm["under"] if k == 0 else lm["overlap"]
            law_k = env.plus(per("clear", k))
            sh = Sheet(fr, law_k, lt0, lt1, line(k), end if last else (lambda th, k=k: line(k + 1)(th) + lm["overlap"]),
                       lm["thick"], roll=roll, cap=cap if last else None, clear=per("clear", k), lip=lip, step=lm.get("step", step),
                       step_s=lm.get("step_s"), flare=lm.get("flare") if last else None, roll_on="tb01" if last else "t01",
                       lift_top={"band": lap + 0.002, "ease": lm.get("ease", 0.012),
                                 "h": lap_room(sheets[-1], law_k, per("gap", k, 0.0008), per("slide", k, 0.0))})
            p = sh.build(f"lame{k + 1}_{sd}_rigid", mats["plate"], ao=0.92)
            # its pivot rivets, on its lapping band at each side: part of the lame (they ride its blend)
            riv = []
            for th_e, sgn in ((lt0, 1), (lt1, -1)):
                s_r = float(line(k)(th_e)) + 0.5 * lap + 0.001
                c, n = sh.at(np.array(s_r), np.array(th_e + sgn * np.degrees(0.010 / float(sh.law(s_r, th_e)))))
                riv.append(nb.rivet(c, n, name=p.name, material=mats["plate"]))
            grid = p.grid
            p = Part.join(p.name, mats["plate"], [p] + riv)
            p.grid = grid
            rules[p.name] = lm["rides"][k]
            sheets.append(sh)
            built.append(p)
        hip_sheets = []
        for j, ((f, g), h) in enumerate(zip(hip_lines, hips)):
            sh = Sheet(fr, env.plus(h.get("clear", cfg["clear"])), h["theta"][0], h["theta"][1], f, g, h["thick"], roll=roll,
                       clear=h.get("clear", cfg["clear"]), lip=lip, step=h.get("step", step), roll_on="t01")
            p = sh.build(f"hip{j + 1 if len(hips) > 1 else ''}_{sd}_rigid", mats["plate"], ao=0.92)
            rules[p.name] = h["ride"]
            hip_sheets.append(sh)
            built.append(p)
        r["seated_points"] = [nb.seat(p, ref, cfg.get("seat", 0.0012)) for p in built]
        # --- straps: the back strap round the bare side of the limb, the garter up to the string
        soft, tabs, gtabs, rivets = [], [], [], []
        strap_t = cfg.get("strap_thick", 0.0018)

        def rivet_on(sheet, s, th, up, name):
            c, n = sheet.at(np.array(s), np.array(th), up + (0.0014 if up else 0.0))   # (on a strap: the strap's own lift)
            return nb.rivet(c, n, name=name, material=mats["plate"])

        bs = cfg.get("back_strap")
        if bs:
            s_b = bs["s"]
            ta, tb = float(plate.side(0, s_b)), float(plate.side(1, s_b))
            Rm = float(plate.law(s_b, tb))
            inset = np.degrees(bs.get("inset", 0.016) / Rm)
            a0, a1_ = tb - inset, ta + 360 + inset
            n = int(np.ceil(np.radians(a1_ - a0) * Rm / bs.get("step", 0.004)))
            th = np.linspace(a0, a1_, n)
            s = np.full(n, s_b)
            rs, _ = nb.radial(ref.V, Tn, fr, s, th, 0.26)
            thw = np.where(th > 180, th - 360, th)
            path = fr.pt(s, thw, rs)
            q, lifts, on = climb(fr, ref, path, [plate])
            a, b = nb.skin_band(ref, q, bs["width"], strap_t, f"straps_{sd}", mats["strap"], lifts=lifts, tab=on)
            soft.append(a)
            tabs.append(b)
            half = np.degrees(0.5 * bs.get("inset", 0.016) / Rm)
            rivets += [rivet_on(plate, s_b, tb - half - 1.0, strap_t, f"rivets_{sd}_rigid"),
                       rivet_on(plate, s_b, ta + half + 1.0, strap_t, f"rivets_{sd}_rigid")]
        gt = cfg.get("garter")
        parts_b = None
        if gt:
            tg = gt["theta"]
            host, host_top, p_host = (hip_sheets[0], hip_lines[0][0], built[1 + n_l]) if hips else (plate, top, p_plate)
            A, _ = host.at(np.array(float(host_top(tg)) + gt.get("inset", 0.016)), np.array(float(tg)))
            Vs, _ = nb.read_mesh(os.path.join(nb.REPO, gt["to"]["mesh"]), gt["to"].get("nodes"), 0)
            ss, ths, _ = fr.cyl(Vs)
            cand = Vs[(Vs[:, 0] * hand > 0) & (np.abs(ths - tg) < gt.get("spread", 14)) & (ss < float(host_top(tg)) - 0.02)]
            B = cand[np.linalg.norm(cand - A, axis=1).argmin()]
            n = int(np.ceil(np.linalg.norm(B - A) / 0.004)) + 1
            path = A + (B - A) * np.linspace(0, 1.0, n)[:, None]
            q, lifts, on = climb(fr, ref, path, [host])
            lifts[-3:] = np.maximum(lifts[-3:], gt.get("over_string", 0.002))
            a, b = nb.skin_band(ref, q, gt["width"], strap_t, f"straps_{sd}", mats["strap"], lifts=lifts, tab=on)
            soft.append(a)
            (gtabs if hips else tabs).append(b)
            rv = rivet_on(host, float(host_top(tg)) + gt.get("inset", 0.016) * 0.55, float(tg), strap_t, p_host.name)
            if hips:   # (the garter hangs from the hip lame: its rivet is the lame's own, its tab rides the lame)
                k = built.index(p_host)
                built[k] = Part.join(p_host.name, mats["plate"], [p_host, rv])
                built[k].grid = p_host.grid
            else:
                rivets.append(rv)
            qb, nq, _ = ref.closest(B[None])
            parts_b = nb.buckle(qb[0] + nq[0] * (lifts[-1] + strap_t), nq[0], U(B - A), w=gt["width"] + 0.007, name=f"buckle_{sd}_rigid",
                                material=mats["plate"])
            rules[parts_b.name] = gt.get("buckle_ride", {"ride": {"spine": "mean", "thigh": "mean"}})
            sockets[f"hip_{sd}"] = {"point": qb[0].round(5).tolist(), "normal": nq[0].round(5).tolist(), "up": U(B - A).round(5).tolist()}
            r["garter_mm"] = round(float(np.linalg.norm(B - A)) / MM)
        for name, group, mat, host_name in ((f"straps_{sd}", soft, mats["strap"], None), (f"tabs_{sd}_rigid", tabs, mats["strap"], p_plate.name),
                                            (f"gtab_{sd}_rigid", gtabs, mats["strap"], built[1 + n_l].name if hips else None),
                                            (f"rivets_{sd}_rigid", rivets, mats["plate"], p_plate.name)):
            group = [g for g in group if g is not None]
            if group:
                parts.append(Part.join(name, mat, group))
                if host_name:
                    rules[name] = {"with": host_name}
        parts += built + ([parts_b] if parts_b is not None else [])
        # --- sockets and rims
        low, p_low = sheets[-1], built[n_l]
        tm = 0.5 * (t0 + t1)
        for key, (s, th) in ((f"thigh_{sd}", (float(top(tm) + a1(tm)) / 2, tm)), (f"knee_{sd}", (float(a1(20.0)) - 0.02, 20.0))):
            c, n = plate.at(np.array(s), np.array(th))
            sockets[key] = {"point": c.round(5).tolist(), "normal": n.round(5).tolist(), "up": (-fr.a).round(5).tolist()}
        te = np.linspace(t0, t1, 12)
        rims[f"top_rim_{sd}"] = {"points": plate.at(top(te), te)[0].round(5).tolist()}
        te = np.linspace(lt0, lt1, 12)
        rims[f"knee_rim_{sd}"] = {"points": low.at(low.bot(te), te)[0].round(5).tolist()}
        se = np.linspace(float(top(t1)), float(a1(lt1)), 10)
        rims[f"side_rim_{sd}"] = {"points": plate.at(se, plate.side(1, se))[0].round(5).tolist()}
        # --- what the build measured on her rest
        for p in built:   # (grid: its outer face is its first rows x columns points, row by row from its top edge)
            r[p.name] = {"tris": int(len(p.T)), "grid": list(p.grid[0].shape)}
        if hasattr(ref, "body"):
            import gear_field
            for p in built:
                c, _ = gear_field.signed_clear(ref.body, p.P, k=16)
                r[p.name].update({"rest_clear_mm_min": round(float(c.min()) / MM, 2), "inside": int((c < 0).sum())})
        S2, TH2, _ = p_low.grid
        copr, _ = nb.radial(Vg, Tc, fr, S2, TH2, 0.3)
        gap = copr - low.outer(S2, TH2)
        r["end_under_rim_mm_min"] = round(float(np.nanmin(gap)) / MM, 2) if np.isfinite(gap).any() else None
        r["end_tucked_rows"] = int(np.isfinite(gap).any(1).sum())
    piece = dict(cfg["piece"])
    piece.update({"id": pid, "native": {"rest_body": ref.rest_body, "rest_hash": ref.hashes, "builder": "tools/armor/native_build.py",
                                        "recipe": cfg["recipe"]}, "parts": rules})
    sj = {"id": pid, "slot": piece["slot"], "body_hash": ref.hashes.get("close"),
          "space": "glTF / Godot: Y up, metres, her_b's rest (native_build)", "sockets": sockets, "rims": rims, "fixings": []}
    d = nb.write_piece(pid, piece, parts, sj, out)
    rep["dir"] = os.path.relpath(d, nb.REPO).replace("\\", "/")
    rep["tris"] = int(sum(len(p.T) for p in parts))
    rep["parts"] = {p.name: [int(len(p.P)), int(len(p.T)), p.material] for p in parts}
    json.dump(rep, open(os.path.join(d, "build_report.json"), "w"), indent=1)
    return rep


RECIPES = {"limb_plate": limb_plate}
