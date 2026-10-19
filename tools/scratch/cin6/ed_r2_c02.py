# Judge j2r2: C02 s8. Places are world offsets: she faces -z here, so her right is +x, the camera at -z.
def edit(shots, f):
    shots["2"]["dur"] = 2.4
    s8 = shots["8"]
    s8["cam"]["pos"]["off"] = [0.08, 0.0, -1.0]               # eyes near the upper third
    s8["cam"]["at"]["off"] = [0, 0.0, 0]
    s8["cam"]["lens"] = 90                                     # a little wider: the wet hair
    cues = s8["cues"]
    for c in cues:
        if c.get("do") == "glow" and c.get("name") == "held":
            c["where"] = {"actor": "her", "bone": "eyes", "off": [0.20, 0.0, -0.28]}   # her right, the lamp's side, eye height
            c["light"] = 0.25; c["spec"] = 1.0
    cues.insert(1, {"do": "hide", "actor": "warden"})          # his lamp-iron was a black band across the frame
    cues.insert(2, {"do": "rig", "name": "ember", "energy": 0.15, "color": "#ff6a33", "angle": 30, "range": 0.3,
                    "from": {"actor": "her", "bone": "eyes", "off": [-0.15, -0.12, -0.18]},
                    "aim": {"actor": "her", "bone": "eyes", "off": [-0.05, -0.05, 0]}})
    shots["9"]["cues"].insert(0, {"do": "hide", "actor": "warden", "hidden": False})
