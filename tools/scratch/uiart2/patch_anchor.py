p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\chainanim.py'
s = open(p, encoding='utf-8').read()
s = s.replace('''Its feel comes from art/ui/chain/chain.json, as the game's does (made by chain.links):
  pitch, fade, run       link spacing; the ends fade over `fade` px, `run` px past the end tabs''', '''The chain is anchored, not faded (an alpha fade reads as an effect, not a thing): each end runs
into a forged eyelet set in the band, `run` px past the end tabs, and the links feed through it
as the chain slides, going into the dark of its hole; the eyelets are what the sag hangs from.

Its feel comes from art/ui/chain/chain.json, as the game's does (made by chain.links):
  pitch, run             link spacing; the eyelets sit `run` px past the end tabs''')
s = s.replace('''    S["open"] = ld("open")
    return meta, S''', '''    S["open"] = ld("open")
    S["eyelet"] = ld("eyelet")
    return meta, S''')
s = s.replace('''def lay(canvas, pm, cx, cy, ang, alpha, s):
    """Draw a premultiplied sprite centred at (cx, cy) shown px, turned by ang radians."""''', '''def lay(canvas, pm, cx, cy, ang, alpha, s, clip=None):
    """Draw a premultiplied sprite centred at (cx, cy) shown px, turned by ang radians, only
    between clip's x0 and x1 (shown px) if given: the links between the eyelets."""''')
s = s.replace('''    out = cv2.warpAffine(pm, M, (canvas.shape[1], canvas.shape[0]), flags=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    a = out[..., 3:4] * alpha''', '''    out = cv2.warpAffine(pm, M, (canvas.shape[1], canvas.shape[0]), flags=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    if clip is not None:
        xs = (np.arange(canvas.shape[1], dtype=np.float32) + 0.5) / s
        m = ((xs >= clip[0]) & (xs <= clip[1])).astype(np.float32)[None, :, None]
        out = out * m
    a = out[..., 3:4] * alpha''')
s = s.replace('''    p, fade, heat = meta["pitch"], meta["fade"], meta["heat"]''', '''    p, heat = meta["pitch"], meta["heat"]''')
s = s.replace('''        a = np.clip(min(x - x0, x1 - x) / fade, 0, 1) ** 1.3
        if a <= 0:
            continue''', '''        if x < x0 - p or x > x1 + p:
            continue
        a = 1.0''')
s = s.replace('''    for _, n, x, y, ang, a, kind, k, h in sorted(order, key=lambda o: o[0]):
        if n == chosen:
            lay(img, shrink("open", S["open"], s), x, y, ang, a, s)
        else:
            lay(img, shrink(f"{kind}_{k}", S[f"{kind}_{k}"], s), x, y, ang, a, s)
            if h > 0:
                # Cold to warm to hot: the same link drawn in each state.
                if h < 0.6:
                    lay(img, shrink(f"warm_{kind}_{k}", S[f"warm_{kind}_{k}"], s), x, y, ang, a * h / 0.6, s)
                else:
                    lay(img, shrink(f"warm_{kind}_{k}", S[f"warm_{kind}_{k}"], s), x, y, ang, a, s)
                    lay(img, shrink(f"hot_{kind}_{k}", S[f"hot_{kind}_{k}"], s), x, y, ang, a * (h - 0.6) / 0.4, s)
        if h > 0:
            glow(img, x, y, p * 0.7, p * 0.45, heat_colour(h), 0.24 * h * fl, s)
    return img''', '''    clip = (x0, x1)
    for _, n, x, y, ang, a, kind, k, h in sorted(order, key=lambda o: o[0]):
        if n == chosen:
            lay(img, shrink("open", S["open"], s), x, y, ang, a, s, clip)
        else:
            lay(img, shrink(f"{kind}_{k}", S[f"{kind}_{k}"], s), x, y, ang, a, s, clip)
            if h > 0:
                # Cold to warm to hot: the same link drawn in each state.
                if h < 0.6:
                    lay(img, shrink(f"warm_{kind}_{k}", S[f"warm_{kind}_{k}"], s), x, y, ang, a * h / 0.6, s, clip)
                else:
                    lay(img, shrink(f"warm_{kind}_{k}", S[f"warm_{kind}_{k}"], s), x, y, ang, a, s, clip)
                    lay(img, shrink(f"hot_{kind}_{k}", S[f"hot_{kind}_{k}"], s), x, y, ang, a * (h - 0.6) / 0.4, s, clip)
        if h > 0 and x0 < x < x1:
            glow(img, x, y, p * 0.7, p * 0.45, heat_colour(h), 0.24 * h * fl, s)
    # The eyelets over the chain's ends: the links go into their dark.
    for ex in (x0, x1):
        lay(img, shrink("eyelet", S["eyelet"], s), ex, y0, 0.0, 1.0, s)
    return img''')
open(p, 'w', encoding='utf-8').write(s)
print('ok', s.count('clip)'))
