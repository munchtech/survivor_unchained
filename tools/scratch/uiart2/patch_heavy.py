p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\chain.py'
s = open(p, encoding='utf-8').read()
a = s.index('def links(')
b = s.index('MAKE = {"swag"')
new = '''# The tab chain's feel, read by the game (ChainTabs, from art/ui/chain/chain.json) and by
# chainanim.py: heavy forged chain (the owner: "a little wimpy"), a heavy sag, a slower start,
# a firm stop and a real swing back; five links heated under the chosen tab, cooling outward.
FEEL = {"fade": 40, "run": 72, "heat": 2, "slide": [130, 17], "sag_spring": [62, 3.6],
        "sag_rest": 6.5, "sag_dip": 8.0, "sag_speed": 200}


def deepen_shadow(img, k=1.7):
    """The shadow the shadow catcher gave, darker (a heavier link sits harder on the band)."""
    rgb, a = img[..., :3], img[..., 3]
    lum = rgb @ np.array([0.3, 0.59, 0.11], np.float32)
    shade = (lum < 0.03) & (a < 0.98)
    out = img.copy()
    out[..., 3] = np.where(shade, np.clip(a * k, 0, 0.92), a)
    return out


def links(variants=6, samples=64, link=(30, 19, 3.2), cell=(44, 34), ss=3):
    """chain/{,warm_,hot_}{face,edge}_K and open (art/ui/chain/, cells of `cell` shown px, the
    link at the centre along x): the tab chain's links, each its own sprite so the code can lay
    them along a sagging line, slide them link by link and let them sway, with no two
    neighbours alike. Each is drawn cold, warm and hot with the same geometry, so the code can
    heat a link by fading toward its hot drawing; open is the chosen tab's middle link, pried
    apart and hot. `pitch` (shown px) is where the next link's centre sits."""
    pitch = round(link[0] - 4 * link[2], 1)
    spec = {"cell": [cell[0] * 2, cell[1] * 2], "ss": ss, "samples": samples, "material": TAB_IRON,
            "link": {"length": link[0] * 2, "width": link[1] * 2, "wire": link[2] * 2},
            "pitch": pitch * 2, "variants": variants, "seed": 5, "gap": 16}
    d = os.path.join(OUT, "links")
    os.makedirs(d, exist_ok=True)
    sp = os.path.join(d, "spec.json")
    json.dump(spec, open(sp, "w", encoding="utf-8"), indent=1)
    t0 = time.time()
    for f in os.listdir(d):
        if f.endswith(".png"):
            os.remove(os.path.join(d, f))
    r = subprocess.run([BLENDER, "-b", "-P", os.path.join(HERE, "blender_links.py"), "--", sp, d],
                       capture_output=True, text=True, timeout=3600)
    names = [f"{pre}{kind}_{k}" for pre in ("", "warm_", "hot_") for kind in ("face", "edge") for k in range(variants)] + ["open"]
    made = {}
    for nm in names:
        p = os.path.join(d, nm + ".png")
        if not os.path.exists(p) or os.path.getmtime(p) < t0:
            raise RuntimeError(f"{nm} not rendered:\\n" + (r.stdout + r.stderr)[-3000:])
        img = np.asarray(Image.open(p).convert("RGBA"), np.float32) / 255
        img = deepen_shadow(F.downsample(img, (cell[0] * 2, cell[1] * 2)))
        if nm.startswith("hot_") or nm == "open":
            img = ember_glow(img, 0.7, edge=10)
        made[f"chain/{nm}.png"] = img
    meta = {"pitch": pitch, "cell": list(cell), "variants": variants, "link": list(link), **FEEL}
    json.dump(meta, open(os.path.join(d, "chain.json"), "w"), indent=1)
    return made


'''
s = s[:a] + new + s[b:]
open(p, 'w', encoding='utf-8').write(s)

p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\kit.py'
s = open(p, encoding='utf-8').read()
old = '''CHAIN_ART = ([f"chain/face_{k}.png" for k in range(6)] + [f"chain/edge_{k}.png" for k in range(6)] +
             ["chain/hot.png", "chain/open.png", "ornaments/title_chain_l.png", "ornaments/title_chain_r.png"])'''
assert old in s
s = s.replace(old, '''CHAIN_ART = ([f"chain/{pre}{kind}_{k}.png" for pre in ("", "warm_", "hot_") for kind in ("face", "edge") for k in range(6)] +
             ["chain/open.png", "ornaments/title_chain_l.png", "ornaments/title_chain_r.png"])
# Pieces the kit once made and no longer does (removed from the game on --apply).
GONE = ["chain/hot.png"]''')
s = s.replace('''    shutil.copyfile(os.path.join(ch, "links", "chain.json"), os.path.join(UI, "chain", "chain.json"))''', '''    shutil.copyfile(os.path.join(ch, "links", "chain.json"), os.path.join(UI, "chain", "chain.json"))
    for rel in GONE:
        for q in (os.path.join(UI, rel), os.path.join(UI, rel) + ".import"):
            if os.path.exists(q):
                os.remove(q)''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
