"""P4 pose strip: a built clip drawn OFFLINE, tile by tile, without a Godot shoot (p4.py strip).

Each tile is body B's skinned surface in that frame's pose (clipcheck's poser, the one the clearance test uses), flat
shaded from one fixed light with a z-buffer, the sword (red, hilt dark) and the shield (blue face, yellow rim and boss,
navy back) as the game seats them on B (p4.pieces), a dark nose cone on her face (head pitch and turn), her left limbs
cool grey and her right limbs warm grey. Orthographic, clip space (metres; the game shows her 1.04x), one scale and one
fixed camera per view for the whole clip: the floor (y = 0) and the node origin (0, 0) are drawn, so floating, sinking
and drifting off the spot show.

Views (her travel direction, clip +Z, points screen-RIGHT in both):
  side   a pure profile from HER RIGHT at floor level (the camera looks along +X: screen right = +Z, up = +Y)
  game   the play camera's pitch (FollowCamera.cs `Pitch`, or --pitch) from the same side: she faces screen-right
  front  from in front of her (screen right = +X, her left)
  quarter  three-quarter from her front-RIGHT (45 deg between front and side), level: her forward and her left both
           run screen-right

pose_sheet(): p4.py pose's sheet: one row of four large tiles (game, front, side, quarter) per clip frame, rows stacked.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import numpy as np

SS = 3                    # supersampling (each tile is drawn 3x and box-filtered down)
LABEL = 14                # px: the label band over each tile
LIGHT = np.array([-0.40, 0.65, -0.65]) / np.linalg.norm([-0.40, 0.65, -0.65])   # to the light, view space (right, up, away)
BG, UNDER, INK = (244, 243, 238), (222, 219, 210), (40, 40, 44)
COL = {"body": (176, 176, 176), "left": (146, 164, 190), "right": (204, 182, 158), "nose": (60, 22, 22),
       "blade": (228, 44, 36), "hilt": (110, 22, 18), "face": (44, 112, 224), "rim": (244, 208, 56), "boss": (244, 208, 56),
       "back": (22, 38, 92)}
LIMB = ("upperarm", "lowerarm", "hand", "index", "middle", "ring", "pinky", "thumb", "thigh", "calf", "foot", "ball")


def game_pitch(repo):
    """The play camera's pitch (deg down from the horizontal): FollowCamera.cs's own `Pitch` (zones may override it)."""
    try:
        m = re.search(r"float Pitch = Mathf\.DegToRad\(([\d.]+)\)", (repo / "godot/src/Game/FollowCamera.cs").read_text(encoding="utf-8"))
        return float(m.group(1))
    except Exception:
        return 50.0


def basis(view, pitch):
    """Rows: screen right, screen up, away from the camera (clip space)."""
    if view == "front":
        return np.array([[1.0, 0, 0], [0, 1, 0], [0, 0, -1]])
    if view == "quarter":
        c = np.sqrt(0.5)
        return np.array([[c, 0, c], [0, 1.0, 0], [c, 0, -c]])
    p = np.radians(pitch if view == "game" else 0.0)
    return np.array([[0, 0, 1.0], [np.sin(p), np.cos(p), 0], [np.cos(p), -np.sin(p), 0]])


def raster(xy, z, col, W, H, zb, img):
    """Triangles (n,3,2) px with depths (n,3) and colours (n,3) into a z-buffer zb (W*H) and an image img (W*H,3)."""
    a, b, c = xy[:, 0], xy[:, 1], xy[:, 2]
    lo, hi = xy.min(1), xy.max(1)
    area = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    ok = (hi[:, 0] >= 0) & (lo[:, 0] < W) & (hi[:, 1] >= 0) & (lo[:, 1] < H) & (np.abs(area) > 1e-9)
    x0, y0 = np.clip(np.floor(lo[:, 0]).astype(int), 0, W - 1), np.clip(np.floor(lo[:, 1]).astype(int), 0, H - 1)
    x1, y1 = np.clip(np.ceil(hi[:, 0]).astype(int), 0, W - 1), np.clip(np.ceil(hi[:, 1]).astype(int), 0, H - 1)
    K = np.maximum(x1 - x0, y1 - y0) + 1
    k = 2
    while ok.any():
        sel = np.nonzero(ok & (K <= k))[0]
        ok[sel] = False
        oy, ox = (v.ravel() for v in np.mgrid[0:k, 0:k])
        step = max(1, 3_000_000 // (k * k))
        for i in range(0, len(sel), step):
            s = sel[i:i + step]
            px, py = x0[s, None] + ox[None], y0[s, None] + oy[None]
            cx, cy = px + 0.5 - a[s, 0, None], py + 0.5 - a[s, 1, None]
            w1 = (cx * (c[s, 1] - a[s, 1])[:, None] - cy * (c[s, 0] - a[s, 0])[:, None]) / area[s, None]
            w2 = ((b[s, 0] - a[s, 0])[:, None] * cy - (b[s, 1] - a[s, 1])[:, None] * cx) / area[s, None]
            w0 = 1 - w1 - w2
            ins = (w0 >= 0) & (w1 >= 0) & (w2 >= 0) & (px < W) & (py < H)
            zf = (w0 * z[s, 0, None] + w1 * z[s, 1, None] + w2 * z[s, 2, None])[ins].astype(zb.dtype)   # (the buffer's own type: a float64 depth never equals its float32 minimum)
            idx = (py * W + px)[ins]
            ti = np.broadcast_to(s[:, None], ins.shape)[ins]
            np.minimum.at(zb, idx, zf)
            win = zf <= zb[idx]
            img[idx[win]] = col[ti[win]]
        k *= 2


def outline(img, zb, W, H, jump=0.05):
    """Darken the far side of every depth step over `jump` m and her silhouette (limbs across the body read)."""
    Z = zb.reshape(H, W)
    e = np.zeros((H, W), bool)
    Zp = np.pad(Z, 1, constant_values=np.inf)
    fin = np.isfinite(Z)
    for dy, dx in ((0, 1), (2, 1), (1, 0), (1, 2)):
        nb = Zp[dy:dy + H, dx:dx + W]
        with np.errstate(invalid="ignore"):
            e |= fin & (~np.isfinite(nb) | (Z - nb > jump))
    ep = np.pad(e, 1)
    e = ep[1:-1, 1:-1] | ep[:-2, 1:-1] | ep[2:, 1:-1] | ep[1:-1, :-2] | ep[1:-1, 2:]
    e = e.ravel()
    img[e] *= np.where(np.ptp(img[e], axis=1) > 50, 0.75, 0.3)[:, None]      # (the pieces' colours stay: a blade is 3 px wide)


class Scene:
    """Her posed surface and pieces per frame: verts (clip space), triangles and base colours."""

    def __init__(self, p4, held):
        from motion.rig import Rig
        self.p4, self.rig = p4, Rig(p4.RIG)
        rig = self.rig
        p4.body_field()
        self.B = B = p4._bfB
        self.Xi = np.linalg.inv(B.X)
        self.keyed = set(rig.keyed)
        dom = B.dom[B.p.T[:, 0]]
        col = np.tile(np.array(COL["body"], float), (len(dom), 1))
        for i, n in enumerate(dom):
            if n.startswith(LIMB) and n[-2:] in ("_l", "_r"):
                col[i] = COL["left" if n.endswith("_l") else "right"]
        self.parts = [("body", None, None, np.asarray(B.p.T), col)]
        # (the nose cone: from the rest face's foremost point on the midline, along the Head's rest +Z)
        hj = rig.index["Head"]
        P0 = np.asarray(B.p.P0) @ self.Xi[:3, :3].T + self.Xi[:3, 3]
        hv = P0[(B.dom == "Head") & (np.abs(P0[:, 0]) < 0.015)]
        tip = hv[np.argmax(hv[:, 2])] - [0, 0, 0.01]
        ang = np.arange(6) * np.pi / 3
        ring = tip + np.stack([0.022 * np.cos(ang), 0.022 * np.sin(ang), np.zeros(6)], 1)
        cone = (np.vstack([ring, tip + [0, 0, 0.09]]) - rig.head[hj]) @ rig.R0[hj]
        self.parts.append(("nose", hj, cone, np.array([[i, (i + 1) % 6, 6] for i in range(6)]), np.tile(np.array(COL["nose"], float), (6, 1))))
        pc = p4.pieces()
        fb = p4.REPO / "tools/anim/data/arms_local_b.json"
        arms = json.loads((fb if fb.exists() else p4.REPO / "tools/anim/data/arms_local.json").read_text())
        if "sword" in held:
            v, t = pc["sword"], np.array(arms["chevalier_sword@hand_r"]["t"])
            at, d = np.array(pc["blade"]["at"]), np.array(pc["blade"]["dir"])
            al = (v - at) @ d
            guard = al[np.argmax(np.linalg.norm((v - at) - np.outer(al, d), axis=1))]
            c = np.where((al[t].mean(1) > guard + 0.015)[:, None], np.array(COL["blade"], float), np.array(COL["hilt"], float))
            self.parts.append(("sword", rig.index["hand_r"], v, t, c))
        if "shield" in held:
            v, t = pc["shield"], np.array(arms["shield_round@lowerarm_l"]["t"])
            ctr, face, R = np.array(pc["shieldp"]["at"]), np.array(pc["shieldp"]["face"]), pc["shieldp"]["radius"]
            cen = v[t].mean(1) - ctr
            n = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]])
            n *= np.sign(np.einsum("ij,ij->", cen, n)) or 1.0
            nf = (n @ face) / (np.linalg.norm(n, axis=1) + 1e-12)
            rad = np.linalg.norm(cen - np.outer(cen @ face, face), axis=1)
            c = np.tile(np.array(COL["back"], float), (len(t), 1))
            c[nf > 0] = COL["face"]
            c[(nf > 0) & (rad < 0.2 * R)] = COL["boss"]
            c[rad > 0.9 * R] = COL["rim"]
            self.parts.append(("shield", rig.index["lowerarm_l"], v, t, c))
        off, T = 0, []
        for nm, j, v, t, c in self.parts:
            T.append(t + off)
            off += len(B.p.P0) if v is None else len(v)
        self.T, self.C = np.vstack(T), np.vstack([p[4] for p in self.parts])

    def verts(self, G, P):
        """All parts' verts on one frame's globals (clip space), in self.T's order."""
        B = self.B
        B.cache.clear()
        V = B.pose(self.p4.m44(G, P), self.keyed, 0)[0]
        out = [V @ self.Xi[:3, :3].T + self.Xi[:3, 3]]
        for nm, j, v, t, c in self.parts[1:]:
            out.append(v @ G[j].T + P[j])
        return np.vstack(out).astype(np.float32)


def edges(beats, fps, n):
    """frame -> the names of the beats' edges on it (events, contact, hold> <hold, cancel, loop> <loop)."""
    out = {}
    def add(t, name):
        out.setdefault(min(n - 1, max(0, int(round(t * fps)))), []).append(name)
    for k, t in (beats.get("events") or {}).items():
        add(t, k)
    for t in beats.get("contact") or []:
        add(t, "contact")
    for k in ("hold", "loop"):
        if beats.get(k):
            add(beats[k][0], k + ">")
            add(beats[k][1], "<" + k)
    if "cancel" in beats:
        add(beats["cancel"], "cancel")
    return out


def backdrop(view, pitch, W, H, s, mid):
    """A tile's ground at SS size: the floor line (side, front) or the ground's travel line and 0.5 m ring (game),
    0.5 m ticks, and the node origin in red."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    def X(r):
        return W / 2 + (r - mid[0]) * s
    def Y(u):
        return H / 2 - (u - mid[1]) * s
    red, grey, w = (214, 40, 40), (120, 118, 112), SS
    y0 = Y(0)
    if view == "game":
        sp = np.sin(np.radians(pitch))
        d.ellipse([X(-0.5), Y(0.5 * sp), X(0.5), Y(-0.5 * sp)], outline=(196, 192, 182), width=w)
        d.line([0, y0, W, y0], fill=grey, width=w)
        d.line([X(0), Y(0.5 * sp), X(0), Y(-0.5 * sp)], fill=red, width=w)
    else:
        d.rectangle([0, y0, W, H], fill=UNDER)
        d.line([X(0), 0, X(0), y0], fill=(232, 208, 204), width=w)
        d.line([0, y0, W, y0], fill=INK, width=w)
        d.polygon([X(0), y0 + w, X(0) - 3 * w, y0 + 6 * w, X(0) + 3 * w, y0 + 6 * w], fill=red)
    for k in range(-20, 21):
        d.line([X(0.5 * k), y0, X(0.5 * k), y0 + (4 if k % 2 == 0 else 2) * w], fill=grey if view == "game" else INK, width=w)
    return np.asarray(im, np.float32).reshape(-1, 3)


def run(p4, a):
    from PIL import Image, ImageDraw, ImageFont
    t0 = time.time()
    src = Path(a.clip)
    path = src if src.suffix == ".json" and src.exists() else p4.OUT / f"{a.clip}.json"
    if not path.exists():
        raise SystemExit(f"{a.clip}: no built clip at {path}")
    clip = p4.MC.read(path)
    name = path.stem
    sp = p4.REPO / "tools/anim/p4/specs" / f"{clip.get('name', name)}.json"
    spec = json.loads(sp.read_text()) if sp.exists() else {}
    beats = clip.get("beats") or spec.get("beats") or {}
    sc = Scene(p4, spec.get("held", ["sword", "shield"]) if spec else ["sword", "shield"])
    G, P = p4.MC.globals_of(clip, sc.rig)
    n, fps = len(G), float(clip["fps"])
    fa, fb = max(0, a.frm or 0), min(n - 1, n - 1 if a.to is None else a.to)
    ev = edges(beats, fps, n)
    frames = sorted(set(range(fa, fb + 1, max(1, a.every))) | {f for f in ev if fa <= f <= fb})
    pitch = a.pitch if a.pitch is not None else game_pitch(p4.REPO)
    views = [v.strip() for v in a.views.split(",") if v.strip()]
    W, H = (int(x) for x in a.tile.lower().split("x"))
    Hd = H - LABEL
    # (pose every drawn frame once; --spin: her node's yaw to her left about its vertical axis, as the game turns her)
    Vs = []
    for f in frames:
        V = sc.verts(G[f], P[f])
        if a.spin:
            th = 2 * np.pi * a.spin * f / fps
            V = V @ np.array([[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]], np.float32).T
        Vs.append(V)
    Bs = {v: basis(v, pitch).astype(np.float32) for v in views}
    lo = {v: np.min([(V @ Bs[v][:2].T).min(0) for V in Vs] + [[0, -0.07]], 0) for v in views}
    hi = {v: np.max([(V @ Bs[v][:2].T).max(0) for V in Vs] + [[0, 0.0]], 0) for v in views}
    s = min(min((W - 6) / (hi[v][0] - lo[v][0]), (Hd - 6) / (hi[v][1] - lo[v][1])) for v in views)
    cols = min(a.cols, len(frames))
    rows = -(-len(frames) // cols)
    head, bar, foot = 34, 16, 18
    width = max(cols * W, 700)
    sheet = Image.new("RGB", (width, head + len(views) * (bar + rows * H) + foot), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    def font(size, bold=False):
        try:
            return ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf", size)
        except OSError:
            return ImageFont.load_default()
    f11, f11b, f13b = font(11), font(11, True), font(13, True)
    d.text((4, 2), f"{name}   {n} frames @ {fps:g} fps ({n / fps:.2f} s){'  LOOP' if clip.get('loop') else ''}", fill=INK, font=f13b)
    d.text((4, 19), f"labels: 60 fps frames (clip frame x {60 / fps:g})   scale {s:.1f} px/m (clip space)   every {a.every}"
           + (f"   spin {a.spin:g} turns/s to her left" if a.spin else "") + "   floor y=0, red = node origin, ticks 0.5 m", fill=INK, font=f11)
    y = head
    for v in views:
        what = {"side": "SIDE: profile from her right at floor level; she faces screen-right (+Z right, +Y up)",
                "game": f"GAME: play camera pitch {pitch:g} deg down, from her right; she faces screen-right",
                "front": "FRONT: from in front of her (her left is screen-right)"}[v]
        d.rectangle([0, y, width, y + bar - 1], fill=(52, 54, 60))
        d.text((4, y + 1), what, fill=(255, 255, 255), font=f11b)
        y += bar
        mid = (lo[v] + hi[v]) / 2
        Ws, Hs = W * SS, Hd * SS
        back = backdrop(v, pitch, Ws, Hs, s * SS, mid)
        for i, (f, V) in enumerate(zip(frames, Vs)):
            X = V @ Bs[v].T
            xy = np.stack([Ws / 2 + (X[:, 0] - mid[0]) * s * SS, Hs / 2 - (X[:, 1] - mid[1]) * s * SS], 1)[sc.T]
            tv = X[sc.T]
            nr = np.cross(tv[:, 1] - tv[:, 0], tv[:, 2] - tv[:, 0])
            nr /= np.linalg.norm(nr, axis=1, keepdims=True) + 1e-12
            nr[nr[:, 2] > 0] *= -1                                  # (toward the camera)
            shade = 0.36 + 0.64 * np.clip(nr @ LIGHT, 0, 1)
            img, zb = back.copy(), np.full(Ws * Hs, np.inf, np.float32)
            raster(xy, tv[:, :, 2], (sc.C * shade[:, None]).astype(np.float32), Ws, Hs, zb, img)
            outline(img, zb, Ws, Hs)
            tile = Image.fromarray(img.reshape(Hs, Ws, 3).clip(0, 255).astype(np.uint8)).resize((W, Hd), Image.BOX)
            x0, y0 = (i % cols) * W, y + (i // cols) * H
            names = ev.get(f, [])
            d.rectangle([x0, y0, x0 + W - 1, y0 + LABEL - 1], fill=(255, 226, 150) if names else (232, 232, 228))
            lab = f"f{f * 60 / fps:g}"
            d.text((x0 + 3, y0 + 1), lab, fill=INK, font=f11b)
            if names:
                txt, fnt = " ".join(names), f11b
                room = W - 8 - d.textlength(lab, font=f11b)
                while d.textlength(txt, font=fnt) > room and fnt.size > 7:
                    fnt = font(fnt.size - 1, True)
                d.text((x0 + 7 + d.textlength(lab, font=f11b), y0 + 1 + (11 - fnt.size) // 2), txt, fill=(170, 20, 20), font=fnt)
            sheet.paste(tile, (x0, y0 + LABEL))
            d.rectangle([x0, y0, x0 + W - 1, y0 + H - 1], outline=(150, 150, 150))
        y += rows * H
    d.text((4, y + 2), "sword red (hilt dark)   shield: blue face, yellow rim + boss, navy back   her LEFT limbs cool grey, RIGHT limbs warm grey   dark cone = nose",
           fill=INK, font=f11)
    tag = f"_spin{a.spin:g}" if a.spin else ""
    out = Path(a.out) if a.out else p4.REPO / "tools/anim/out/strips" / f"{name}{tag}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    jpg = out.with_suffix(".jpg")
    j = sheet if sheet.width <= 2000 else sheet.resize((2000, round(sheet.height * 2000 / sheet.width)), Image.LANCZOS)
    j.save(jpg, quality=88)
    print(f"{name}: {len(frames)} tiles x {len(views)} views ({', '.join(views)}), {s:.1f} px/m, game pitch {pitch:g} deg, {time.time() - t0:.1f} s")
    print(out)
    print(jpg)


POSE_VIEWS = (("game", "GAME pitch {p:g}, from her right"), ("front", "FRONT (her left = screen right)"),
              ("side", "SIDE from her right"), ("quarter", "3/4 from her front-right, level"))


def pose_sheet(p4, rows, tile, out, pitch=None):
    """p4.py pose's sheet: each row = one frame of one clip in FOUR tiles (POSE_VIEWS: game, front, side, quarter), rows
    stacked, a label over each tile (the row's name and the view), nothing else: the JPEG is 4 tiles wide, one tile
    high per row. rows: [(label, built JSON path, frame, held list)]. One scale and one camera per view for ALL rows
    (rows compare), her skin loaded once (p4.body_field's cache; a Scene per held set)."""
    from PIL import Image, ImageDraw, ImageFont
    t0 = time.time()
    pitch = game_pitch(p4.REPO) if pitch is None else pitch
    W, H = (int(x) for x in tile.lower().split("x"))
    Hd = H - LABEL
    scenes, posed = {}, []
    for label, path, frame, held in rows:
        sc = scenes.get(tuple(held)) or scenes.setdefault(tuple(held), Scene(p4, list(held)))
        G, P = p4.MC.globals_of(p4.MC.read(path), sc.rig)
        f = min(max(0, frame), len(G) - 1)
        posed.append((label, sc, sc.verts(G[f], P[f])))
    views = [v for v, _ in POSE_VIEWS]
    Bs = {v: basis(v, pitch).astype(np.float32) for v in views}
    lo = {v: np.min([(V @ Bs[v][:2].T).min(0) for _, _, V in posed] + [[0, -0.07]], 0) for v in views}
    hi = {v: np.max([(V @ Bs[v][:2].T).max(0) for _, _, V in posed] + [[0, 0.0]], 0) for v in views}
    s = min(min((W - 6) / (hi[v][0] - lo[v][0]), (Hd - 6) / (hi[v][1] - lo[v][1])) for v in views)
    sheet = Image.new("RGB", (len(views) * W, len(posed) * H), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    try:
        fnt = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 11)
    except OSError:
        fnt = ImageFont.load_default()
    Ws, Hs = W * SS, Hd * SS
    for k, (v, what) in enumerate(POSE_VIEWS):
        mid = (lo[v] + hi[v]) / 2
        back = backdrop(v, pitch, Ws, Hs, s * SS, mid)
        for i, (label, sc, V) in enumerate(posed):
            X = V @ Bs[v].T
            xy = np.stack([Ws / 2 + (X[:, 0] - mid[0]) * s * SS, Hs / 2 - (X[:, 1] - mid[1]) * s * SS], 1)[sc.T]
            tv = X[sc.T]
            nr = np.cross(tv[:, 1] - tv[:, 0], tv[:, 2] - tv[:, 0])
            nr /= np.linalg.norm(nr, axis=1, keepdims=True) + 1e-12
            nr[nr[:, 2] > 0] *= -1                                  # (toward the camera)
            shade = 0.36 + 0.64 * np.clip(nr @ LIGHT, 0, 1)
            img, zb = back.copy(), np.full(Ws * Hs, np.inf, np.float32)
            raster(xy, tv[:, :, 2], (sc.C * shade[:, None]).astype(np.float32), Ws, Hs, zb, img)
            outline(img, zb, Ws, Hs)
            x0, y0 = k * W, i * H
            sheet.paste(Image.fromarray(img.reshape(Hs, Ws, 3).clip(0, 255).astype(np.uint8)).resize((W, Hd), Image.BOX), (x0, y0 + LABEL))
            d.rectangle([x0, y0, x0 + W - 1, y0 + LABEL - 1], fill=(255, 226, 150) if i == 0 else (232, 232, 228))
            d.text((x0 + 3, y0 + 1), f"{label}  |  {what.format(p=pitch)}", fill=INK, font=fnt)
            d.rectangle([x0, y0, x0 + W - 1, y0 + H - 1], outline=(150, 150, 150))
    out = Path(out).with_suffix(".jpg")
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=90)
    print(f"pose sheet: {len(posed)} row(s) x {len(views)} views ({', '.join(views)}), {sheet.width}x{sheet.height}, {s:.1f} px/m, "
          f"game pitch {pitch:g} deg, {time.time() - t0:.1f} s")
    return out
