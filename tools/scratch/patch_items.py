import os
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a72467cac33063d3a"
p = os.path.join(W, "tools", "uiforge", "items.py")
s = open(p, encoding="utf-8").read()
rep = [('''OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "godot", "art", "ui", "icons", "item")''',
'''# Second takes painted from words alone (seed 1100), where the game's photograph was a poor
# start: the pelts read as the same flat skin, the root as a little man, the seeds as an onion.
T2I = {
    "pelt": "a thick grey wolf pelt folded over on itself, the wolf's head with its ears and muzzle lying on top, long "
            "shaggy grey and silver fur, tied with a leather thong",
    "hide": "a rolled boar hide, tied with twine, coarse dark brown bristles standing up along its back, the pale raw "
            "underside showing at the roll's end",
    "root": "a gnarled forked bitterroot, pale and knotted with fine hair roots, dark wet soil clinging to it, a single "
            "small green sprout at its crown",
    "seed": "a small leather drawstring pouch spilling hard black thornseeds, each seed spiked with tiny thorns, one "
            "seed split with a green bramble shoot curling out",
    "dust": "a small stoppered clay jar tipped over, fine grey-white barrow dust spilling out of it with tiny bone "
            "fragments and a cracked finger bone in the heap",
    "bomb": "a small iron-bound wooden crate charge, orange ember light glowing through the gaps between its slats, a "
            "short lit fuse sparking on top",
}

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "godot", "art", "ui", "icons", "item")'''),
('''# Which candidate each item uses (place in the batch of seed 1000); the first if not named.
PICKS: dict = {}''', '''# Which candidate each item uses: KEY -> place in the batch of seed 1000, or (seed, place).
PICKS: dict = {}


def t2i(keys=None, seed=1100, n=4):
    keys = list(keys or T2I)
    jobs = [(k, LOOK + T2I[k] + ".", seed) for k in keys]
    return krea.t2i_many(jobs, tag="items_t2i", n=n)'''),
('''    j = PICKS.get(key, 0) if j is None else j
    src = os.path.join(krea.OUT, "items", key, f"items_1000_{j}.png")''', '''    j = PICKS.get(key, 0) if j is None else j
    seed, j = j if isinstance(j, tuple) else (1000, j)
    src = os.path.join(krea.OUT, "items", key, f"items_1000_{j}.png") if seed == 1000 else \\
        os.path.join(krea.OUT, "items_t2i", f"{key}_{seed}_{j}.png")'''),
]
for x, y in rep:
    assert x in s, x[:50]
    s = s.replace(x, y)
open(p, "w", encoding="utf-8").write(s)
print("ok")
