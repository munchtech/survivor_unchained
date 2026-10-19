# k13b round 2 (C02): the globes' halos on the globes themselves (the globe cue's halo); s7 at 24 mm so his head and
# her knees fit with the near post outside the frame; s8's lamp bluer on its half.
def edit(shots, f):
    cs = [c for c in shots["1"]["cues"] if not (c.get("do") == "glow" and str(c.get("name", "")).startswith("post"))]
    for c in cs:
        if c.get("do") == "globe": c.update({"level": 0.04, "halo": 0.4, "spread": 1.0})
    shots["1"]["cues"] = cs
    for c in shots["11"]["cues"]:
        if c.get("do") == "globe" and c.get("level") == 0.07: c["level"] = 0.04
    shots["7"]["cam"] = {"pos": [-1.99, 1.3, -30.85], "at": {"abs": [2.7, 1.35, -31.85]}, "lens": 24}
    for c in shots["8"]["cues"]:
        if c.get("name") == "held": c["color"] = "#9fbde8"
