"""Recipes of the native armor builder: a recipe turns a piece's build.json into its piece dir with native_build's
primitives. `limb_plate`: a plate over part of a limb with a lame at its far joint, straps and fixings (the cuisses;
any limb by its bones and params). A helm adds its own recipe here; nothing below is specific to one piece."""
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


def limb_plate(pid, cfg, out=None, ref=None):
    ref = ref or nb.Ref.her()
    t0, t1 = cfg["theta"]
    parts, sockets, rims, rep, rules = [], {}, {}, {"id": pid, "sides": {}}, {}
    mats = cfg.get("materials", {"plate": "steel", "strap": "darkleather"})
    for sd, hand in (("l", 1), ("r", -1)):
        fr = Frame.bones(ref, cfg["frame"]["from"].replace("*", sd), cfg["frame"]["to"].replace("*", sd), hand)
        L = fr.L
        r = rep["sides"][sd] = {}
        # --- the rim it tucks under (another built piece) and its own top line
        rim_cfg = cfg["bottom"]
        Vg, Tg = nb.read_mesh(os.path.join(nb.REPO, rim_cfg["rim_of"]), rim_cfg.get("nodes"), hand)
        sg, thg, rg = fr.cyl(Vg)
        cut = (rg < 0.25) & (sg > 0.5 * L) & (sg < 1.2 * L)
        bins = np.linspace(t0 - 8, t1 + 8, 14)
        rim_s = np.array([sg[cut & (np.abs(thg - b) < 7)].min() if (cut & (np.abs(thg - b) < 7)).any() else np.nan for b in bins])
        ok = np.isfinite(rim_s)
        rim = nb.edge_curve(bins[ok], rim_s[ok], deg=4)
        bot = lambda th: rim(th) - rim_cfg["above"]  # noqa: E731
        tt = np.linspace(t0, t1, 16)
        pts = np.array(cfg["top"]["points"], float)
        s_top = np.interp(tt, pts[:, 0], pts[:, 1])
        own = cfg["top"].get("own")
        if own:
            line = nb.owned_line(ref, fr, own["role"], own["share"], tt, np.linspace(-0.02, 0.6 * L, 90)) + own["margin"]
            r["owned_line_mm"] = [round(float(v) / MM) for v in line]
            s_top = np.maximum(s_top, line)
        top = nb.edge_curve(tt, s_top, deg=cfg["top"].get("deg", 4), side=+1)
        r["top_mm"] = [round(float(v) / MM) for v in top(np.array([t0, 0.0, 45.0, 90.0, t1]))]
        r["rim_mm"] = [round(float(v) / MM) for v in rim(np.array([t0, 0.0, 45.0, 90.0, t1]))]
        # --- her limb's surface and the smooth law above it
        lame = cfg["lame"]
        under = lame["visible"] - rim_cfg["above"]
        s_lo, s_hi = float(top(tt).min()) - 0.012, float(rim(tt).max()) + under + 0.012
        Tn = nb.near(ref.V, ref.T, fr, s_lo - 0.08, s_hi + 0.08, 0.26)
        S, TH = np.meshgrid(np.linspace(s_lo, s_hi, 64), np.linspace(t0 - 12, t1 + 12, 48), indexing="ij")
        rho, _ = nb.radial(ref.V, Tn, fr, S, TH, 0.26)
        rho = np.where(S > top(TH) - 0.012, rho, np.nan)   # (only the skin the plates lie over shapes the law)
        env = Law.envelope(S, TH, rho, deg=tuple(cfg.get("law_deg", (7, 7))), dom=(s_lo, s_hi, t0 - 12, t1 + 12),
                           over=cfg.get("law_over", 30.0))
        r["law"] = {"rms_mm": round(env.rms / MM, 2), "lift_mm": round(env.add / MM, 2), "no_hit": int(np.isnan(rho).sum())}
        lift = cfg.get("lift", {"band": 0.016, "h": 0.0015})
        plate = Sheet(fr, env.plus(cfg["clear"]), t0, t1, top, bot, cfg["thick"], roll=tuple(cfg["roll"]), ridge=cfg.get("ridge"),
                      lift=lift, clear=cfg["clear"], step=cfg.get("step", 0.011))
        Tc = nb.near(Vg, Tg, fr, 0.5 * L, 1.3 * L, 0.3)

        def cap(s, th, plate=plate, fr=fr, Tc=Tc, Vg=Vg):
            cop, _ = nb.radial(Vg, Tc, fr, s, th, 0.3)
            cop = np.where(np.isfinite(cop), cop - lame["under_gap"], np.inf)
            inner = plate.law(s, th) + lift["h"] * nb.smooth(1 - (plate.bot(th) - s) / lift["band"]) - 0.0003
            return np.where(s < plate.bot(th), inner, cop)

        knee = Sheet(fr, env.plus(lame["clear"]), t0, t1, lambda th: bot(th) - lame["overlap"], lambda th: rim(th) + under,
                     lame["thick"], roll=tuple(cfg["roll"]), cap=cap, clear=lame["clear"], lip=0.0004, step=cfg.get("step", 0.011),
                     flare={"h": lame["flare"], "band": 0.008})
        p_plate = plate.build(f"plate_{sd}_rigid", mats["plate"])
        p_lame = knee.build(f"lame_{sd}_rigid", mats["plate"], ao=0.85)
        r["seated_points"] = [nb.seat(p_plate, ref), nb.seat(p_lame, ref)]
        rules[p_plate.name] = cfg["ride"]
        rules[p_lame.name] = lame["ride"]
        # --- straps: the back strap round the bare side of the limb, the garter up to the string
        soft, tabs, rivets = [], [], []
        strap_t = cfg.get("strap_thick", 0.0018)

        def rivet_on(s, th, up):
            c, n = plate.at(np.array(s), np.array(th), up + (0.0014 if up else 0.0))   # (on a strap: the strap's own lift)
            rivets.append(nb.rivet(c, n, name=f"rivets_{sd}_rigid", material=mats["plate"]))

        bs = cfg.get("back_strap")
        if bs:
            sm = lambda th: top(th) + (bot(th) - top(th)) * bs["at"]  # noqa: E731
            Rm = float(plate.law(sm(t1), t1))
            inset = np.degrees(bs.get("inset", 0.016) / Rm)
            a0, a1 = t1 - inset, t0 + 360 + inset
            n = int(np.ceil(np.radians(a1 - a0) * Rm / bs.get("step", 0.004)))
            th = np.linspace(a0, a1, n)
            s = np.interp(th, [t1, t0 + 360], [float(sm(t1)), float(sm(t0))])
            rs, _ = nb.radial(ref.V, Tn, fr, s, th, 0.26)
            thw = np.where(th > 180, th - 360, th)
            path = fr.pt(s, thw, rs)
            q, lifts, on = climb(fr, ref, path, [plate])
            a, b = nb.skin_band(ref, q, bs["width"], strap_t, f"straps_{sd}", mats["strap"], lifts=lifts, tab=on)
            soft.append(a)
            tabs.append(b)
            half = np.degrees(0.5 * bs.get("inset", 0.016) / Rm)
            rivet_on(float(sm(t1)), t1 - half - 1.0, strap_t)
            rivet_on(float(sm(t0)), t0 + half + 1.0, strap_t)
        gt = cfg.get("garter")
        if gt:
            tg = gt["theta"]
            A, _ = plate.at(np.array(float(top(tg)) + gt.get("inset", 0.016)), np.array(float(tg)))
            Vs, _ = nb.read_mesh(os.path.join(nb.REPO, gt["to"]["mesh"]), gt["to"].get("nodes"), 0)
            ss, ths, _ = fr.cyl(Vs)
            cand = Vs[(Vs[:, 0] * hand > 0) & (np.abs(ths - tg) < gt.get("spread", 14)) & (ss < float(top(tg)) - 0.02)]
            B = cand[np.linalg.norm(cand - A, axis=1).argmin()]
            n = int(np.ceil(np.linalg.norm(B - A) / 0.004)) + 1
            path = A + (B - A) * np.linspace(0, 1.0, n)[:, None]
            q, lifts, on = climb(fr, ref, path, [plate])
            lifts[-3:] = np.maximum(lifts[-3:], gt.get("over_string", 0.002))
            a, b = nb.skin_band(ref, q, gt["width"], strap_t, f"straps_{sd}", mats["strap"], lifts=lifts, tab=on)
            soft.append(a)
            tabs.append(b)
            rivet_on(float(top(tg)) + gt.get("inset", 0.016) * 0.55, float(tg), strap_t)
            qb, nq, _ = ref.closest(B[None])
            bk = nb.buckle(qb[0] + nq[0] * (lifts[-1] + strap_t), nq[0], U(B - A), w=gt["width"] + 0.007, name=f"buckle_{sd}_rigid",
                           material=mats["plate"])
            parts_b = bk
            rules[bk.name] = gt.get("buckle_ride", {"ride": {"spine": "mean", "thigh": "mean"}})
            sockets[f"hip_{sd}"] = {"point": qb[0].round(5).tolist(), "normal": nq[0].round(5).tolist(), "up": U(B - A).round(5).tolist()}
            r["garter_mm"] = round(float(np.linalg.norm(B - A)) / MM)
        else:
            parts_b = None
        # pivot rivets of the lame, on the plate's two sides above its bottom roll
        for th_e, sgn in ((t0, 1), (t1, -1)):
            Rb = float(plate.law(bot(th_e) - 0.011, th_e))
            rivet_on(float(bot(th_e)) - 0.011, th_e + sgn * np.degrees(0.011 / Rb), 0.0)
        for name, group, mat in ((f"straps_{sd}", soft, mats["strap"]), (f"tabs_{sd}_rigid", tabs, mats["strap"]),
                                 (f"rivets_{sd}_rigid", rivets, mats["plate"])):
            group = [g for g in group if g is not None]
            if group:
                parts.append(Part.join(name, mat, group))
                if name.endswith("_rigid"):
                    rules[name] = {"with": p_plate.name}
        parts += [p_plate, p_lame] + ([parts_b] if parts_b is not None else [])
        # --- sockets and rims
        tm = 0.5 * (t0 + t1)
        for key, (s, th) in ((f"thigh_{sd}", (float(top(tm) + bot(tm)) / 2, tm)), (f"knee_{sd}", (float(bot(20.0)) - 0.02, 20.0))):
            c, n = plate.at(np.array(s), np.array(th))
            sockets[key] = {"point": c.round(5).tolist(), "normal": n.round(5).tolist(), "up": (-fr.a).round(5).tolist()}
        te = np.linspace(t0, t1, 12)
        rims[f"top_rim_{sd}"] = {"points": plate.at(top(te), te)[0].round(5).tolist()}
        rims[f"knee_rim_{sd}"] = {"points": plate.at(bot(te), te)[0].round(5).tolist()}
        se = np.linspace(float(top(t1)), float(bot(t1)), 10)
        rims[f"side_rim_{sd}"] = {"points": plate.at(se, np.full(10, float(t1)))[0].round(5).tolist()}
        # --- what the build measured on her rest
        if hasattr(ref, "body"):
            import gear_field
            for p in (p_plate, p_lame):
                c, _ = gear_field.signed_clear(ref.body, p.P, k=16)
                r[p.name] = {"tris": int(len(p.T)), "rest_clear_mm_min": round(float(c.min()) / MM, 2), "inside": int((c < 0).sum())}
        S2, TH2, _ = p_lame.grid
        copr, _ = nb.radial(Vg, Tc, fr, S2, TH2, 0.3)
        gap = copr - knee.outer(S2, TH2)
        r["lame_under_cop_mm_min"] = round(float(np.nanmin(gap)) / MM, 2) if np.isfinite(gap).any() else None
        r["lame_tucked_rows"] = int(np.isfinite(gap).any(1).sum())
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
