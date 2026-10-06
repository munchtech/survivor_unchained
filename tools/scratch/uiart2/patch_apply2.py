p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\kit.py'
s = open(p, encoding='utf-8').read()
s = s.replace('''CHAIN_ART = ([f"chain/{pre}{kind}_{k}.png" for pre in ("", "warm_", "hot_") for kind in ("face", "edge") for k in range(6)] +
             ["chain/open.png", "ornaments/title_chain_l.png", "ornaments/title_chain_r.png"])''', '''CHAIN_ART = ([f"chain/{pre}{kind}_{k}.png" for pre in ("", "warm_", "hot_") for kind in ("face", "edge") for k in range(6)] +
             ["chain/open.png", "chain/eyelet.png", "ornaments/title_chain_l.png", "ornaments/title_chain_r.png"])
# The world's other small things, each made by its own tool (coals.py, embers.py): what they
# are, and the folder under tools/comfy/out/uiforge/ they are made into.
WORLD_ART = {"coal": ([f"coal/coal_{k}.png" for k in range(4)] + ["coal/dish.png", "coal/dish_rim.png", "coal/numeral_glow.png"]),
             "embers": ["hud/spark.png", "hud/glint.png", "hud/pointer_legendary.png"]}''')
s = s.replace('''    shutil.copyfile(os.path.join(ch, "links", "chain.json"), os.path.join(UI, "chain", "chain.json"))''', '''    shutil.copyfile(os.path.join(ch, "links", "chain.json"), os.path.join(UI, "chain", "chain.json"))
    for folder, rels in WORLD_ART.items():
        for rel in rels:
            srcp = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", folder, rel)
            if not os.path.exists(srcp):
                raise SystemExit(f"{rel} not made: run {folder}.py first")
            dst = os.path.join(UI, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(srcp, dst)''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
