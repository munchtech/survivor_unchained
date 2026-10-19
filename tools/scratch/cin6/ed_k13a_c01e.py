# k13a pass 5 (C01): s3 with the fire light off splits, but the throat third went blue-grey (the scene's moon and sky)
# and the fill near the lens still put a catchlight dead centre. Sky and scene moon down (the throat into warm-edged
# shadow), the moon rig a little toward the lens so it lands on the top of her face, the fill off the lens axis on the
# camera's top side.
def edit(shots, f):
    for c in shots["3"]["cues"]:
        if c.get("do") == "atmosphere": c.update({"key": 0.05, "hemi": 0.08, "env": 0.08})
        if c.get("name") == "moon": c.update({"energy": 0.8, "angle": 14, "from": {"actor": "her", "bone": "head", "off": [-0.3, 1.0, 0.1]}})
        if c.get("name") == "fill": c.update({"energy": 0.16, "angle": 14, "color": "#ffd6b8", "from": {"actor": "her", "bone": "head", "off": [-0.55, 0.45, 0.35]}})
