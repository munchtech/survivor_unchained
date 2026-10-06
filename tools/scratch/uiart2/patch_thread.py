p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\chain.py'
s = open(p, encoding='utf-8').read()
s = s.replace('''def links(variants=6''', '''def eyelet_parts(cell=(52, 44), hole=12.5 * 2):
    """The eyelet in the parts a chain is threaded through it with (the owner: the links must
    truly go through it): its ring cut down the middle, the half the chain comes from drawn
    under the links and the far half over them, and the dark of its hole over them too.
      eyelet_left / eyelet_right   the ring's left and right halves (each a whole cell)
      eyelet_hole                  the hole's dark alone
    A left-hand eyelet (the chain coming from its right) draws eyelet_right under the links,
    then eyelet_left and eyelet_hole over them; a right-hand one the other way round."""
    raw = os.path.join(OUT, "links", "eyelet.png")
    img = np.asarray(Image.open(raw).convert("RGBA"), np.float32) / 255
    ring = deepen_shadow(F.downsample(img, (cell[0] * 2, cell[1] * 2)))
    h, w = ring.shape[:2]
    xx = (np.arange(w, dtype=np.float32) + 0.5)[None, :]
    soft = np.clip((xx - w / 2) / 2.0 + 0.5, 0, 1)       # a two-pixel seam, so the halves meet clean
    left, right = ring.copy(), ring.copy()
    left[..., 3] *= 1 - soft
    right[..., 3] *= soft
    dark = hole_dark(np.zeros_like(ring), hole)
    return {"chain/eyelet_left.png": left, "chain/eyelet_right.png": right, "chain/eyelet_hole.png": dark}


def links(variants=6''')
s = s.replace('''    meta = {"pitch": pitch, "cell": list(cell), "variants": variants, "link": list(link), **FEEL}''', '''    made.update(eyelet_parts(cell))
    meta = {"pitch": pitch, "cell": list(cell), "variants": variants, "link": list(link), **FEEL}''')
s = s.replace('''FEEL = {"eyelet": True, "fade": 0, "run": 72, "heat": 2,''', '''FEEL = {"eyelet": True, "fade": 0, "run": 72, "heat": 2, "hole": 12.5,''')
open(p, 'w', encoding='utf-8').write(s)

p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\chainanim.py'
s = open(p, encoding='utf-8').read()
s = s.replace('''    S["open"] = ld("open")
    S["eyelet"] = ld("eyelet")
    return meta, S''', '''    S["open"] = ld("open")
    for k in ("eyelet_left", "eyelet_right", "eyelet_hole"):
        S[k] = ld(k)
    return meta, S''')
s = s.replace('''def lay(canvas, pm, cx, cy, ang, alpha, s, clip=None):
    """Draw a premultiplied sprite centred at (cx, cy) shown px, turned by ang radians, only
    between clip's x0 and x1 (shown px) if given: the links between the eyelets."""
    h, w = pm.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), -math.degrees(ang), 1.0)''', '''def lay(canvas, pm, cx, cy, ang, alpha, s, clip=None, sx=1.0, shade=1.0):
    """Draw a premultiplied sprite centred at (cx, cy) shown px, turned by ang radians, only
    between clip's x0 and x1 (shown px) if given; `sx` foreshortens it along its length (a link
    turning to dive into an eyelet), `shade` darkens it (going down into the hole's dark)."""
    h, w = pm.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), -math.degrees(ang), 1.0)
    if sx != 1.0:
        F_ = np.array([[sx, 0, w / 2 * (1 - sx)], [0, 1, 0], [0, 0, 1]], np.float32)
        M = (np.vstack([M, [0, 0, 1]]) @ F_)[:2]''')
s = s.replace('''    a = out[..., 3:4] * alpha
    canvas[..., :3] = canvas[..., :3] * (1 - a) + out[..., :3] * alpha''', '''    a = out[..., 3:4] * alpha
    canvas[..., :3] = canvas[..., :3] * (1 - a) + out[..., :3] * alpha * shade''')
old_start = s.index('    order = []\n    for n in range(n0, n1 + 1):')
old_end = s.index('    return img\n\n\ndef run(')
new = '''    # Each link threads into an eyelet at either end: when it reaches the hole it turns from
    # lying along the band to diving into it, its far end going down first, so it shortens as
    # seen (sx = cos) and darkens; its near end runs on at the chain's speed, so nothing pops.
    L = meta["link"][0]
    R = meta.get("hole", 12.5)
    reach = L / 2 + R * 0.6

    def dive(x):
        """(angle 0..pi/2, the visible centre's x) of a link centred at x."""
        if x - x0 < reach:
            th = (1 - np.clip((x - x0) / reach, 0, 1)) * math.pi / 2
            near = x + L / 2
            return th, near - L / 2 * math.cos(th)
        if x1 - x < reach:
            th = (1 - np.clip((x1 - x) / reach, 0, 1)) * math.pi / 2
            near = x - L / 2
            return th, near + L / 2 * math.cos(th)
        return 0.0, x

    order = []
    for n in range(n0, n1 + 1):
        x = phase + n * p
        if x < x0 - p or x > x1 + p:
            continue
        th, vx = dive(x)
        if th >= math.pi / 2 - 1e-3:
            continue
        ang = math.atan2(y_at(x + 1) - y_at(x - 1), 2)
        kind = "face" if n % 2 == 0 else "edge"
        k = (n * 7 + 3) % var
        d = abs(n - chosen)
        h = 1 - d / (heat + 1) if d <= heat else 0.0
        order.append((0 if kind == "face" else 1, n, vx, y_at(x), ang, kind, k, h, math.cos(th), 1 - 0.8 * math.sin(th)))
    # The eyelets' near halves (the side the chain comes from) lie under the links.
    lay(img, shrink("eyelet_right", S["eyelet_right"], s), x0, y0, 0.0, 1.0, s)
    lay(img, shrink("eyelet_left", S["eyelet_left"], s), x1, y0, 0.0, 1.0, s)
    # Face-on links first; those on edge pass through them and lie over their ends.
    for _, n, x, y, ang, kind, k, h, sx, sh in sorted(order, key=lambda o: o[0]):
        if n == chosen:
            lay(img, shrink("open", S["open"], s), x, y, ang, 1.0, s, sx=sx, shade=sh)
        else:
            lay(img, shrink(f"{kind}_{k}", S[f"{kind}_{k}"], s), x, y, ang, 1.0, s, sx=sx, shade=sh)
            if h > 0:
                # Cold to warm to hot: the same link drawn in each state.
                if h < 0.6:
                    lay(img, shrink(f"warm_{kind}_{k}", S[f"warm_{kind}_{k}"], s), x, y, ang, h / 0.6, s, sx=sx, shade=sh)
                else:
                    lay(img, shrink(f"warm_{kind}_{k}", S[f"warm_{kind}_{k}"], s), x, y, ang, 1.0, s, sx=sx, shade=sh)
                    lay(img, shrink(f"hot_{kind}_{k}", S[f"hot_{kind}_{k}"], s), x, y, ang, (h - 0.6) / 0.4, s, sx=sx, shade=sh)
        if h > 0 and x0 < x < x1:
            glow(img, x, y, p * 0.7, p * 0.45, heat_colour(h), 0.24 * h * fl * sx, s)
    # Their far halves and the dark of their holes over the links going in.
    for ex, far in ((x0, "eyelet_left"), (x1, "eyelet_right")):
        lay(img, shrink("eyelet_hole", S["eyelet_hole"], s), ex, y0, 0.0, 1.0, s)
        lay(img, shrink(far, S[far], s), ex, y0, 0.0, 1.0, s)
'''
s = s[:old_start] + new + s[old_end:]
open(p, 'w', encoding='utf-8').write(s)
print('ok')
