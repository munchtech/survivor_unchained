# k10 (C03 s3b): a side key from the moon (south-west, high), the far side of her face falling away.
def edit(shots, f):
    shots["3b"]["cues"].insert(0, {"do": "rig", "name": "moon", "energy": 1.2, "color": "#9fb8ff", "angle": 28,
        "from": {"actor": "her", "bone": "eyes", "off": [-0.8, 0.9, 0.3]}, "aim": {"actor": "her", "bone": "eyes", "off": [0, -0.03, 0]}})
