# k13a pass 6 (C01): s3 splits (top of her face moonlit, cheek and chin ember), but the moon's cone also flooded the
# throat third blue-grey: cone narrowed onto the top of her face (crown side), colour back to the paler moon.
def edit(shots, f):
    for c in shots["3"]["cues"]:
        if c.get("name") == "moon": c.update({"angle": 8, "color": "#a9bfff", "aim": {"actor": "her", "bone": "head", "off": [-0.03, 0.03, 0.06]}})
