# k12b (C02): s4 and s8 keys off cyan toward a pale steel, the ember a little wider as the warm shadow edge.
def edit(shots, f):
    for c in shots["4"]["cues"]:
        if c.get("name") == "key": c.update({"color": "#a9b6cc", "energy": 0.7})
        if c.get("name") == "ember": c.update({"energy": 0.45, "angle": 20})
    for c in shots["8"]["cues"]:
        if c.get("name") == "held": c.update({"color": "#c6cede", "light": 0.6})
        if c.get("name") == "ember": c.update({"energy": 0.3, "angle": 18})
