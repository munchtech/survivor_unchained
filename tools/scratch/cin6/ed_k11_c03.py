# k11b (C03 s3b): the key is his lamp (frame left, eye height, hard), the moon a back rim; sky 40% less colour; 15% tighter.
def edit(shots, f):
    s = shots["3b"]
    s["cam"]["lens"] = 58
    c = [x for x in s["cues"] if x.get("do") != "rig"]
    s["cues"] = [{"do": "atmosphere", "preset": "now", "skySat": 0.6},
        {"do": "rig", "name": "lamp", "energy": 1.0, "color": "#8ac8ff", "angle": 10, "from": {"actor": "her", "bone": "eyes", "off": [0.85, 0.05, -0.25]}, "aim": {"actor": "her", "bone": "eyes", "off": [0, -0.03, 0]}},
        {"do": "rig", "name": "moon", "energy": 0.4, "color": "#9fb8ff", "angle": 28, "from": {"actor": "her", "bone": "eyes", "off": [-0.8, 0.9, 0.6]}, "aim": {"actor": "her", "bone": "eyes", "off": [0, -0.03, 0]}}] + c
    shots["4"]["cues"].insert(0, {"do": "atmosphere", "preset": "now", "skySat": 1.6667})
