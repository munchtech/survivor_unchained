"""C01 pass 7: 5 from her front-right, north of the ring (no tripod leg across her); 8's exhale smaller."""


def edit(shots, f):
    shots["5"]["cam"]["pos"] = [-10.0, 0.42, 88.5]
    for c in shots["8"]["cues"]:
        if c.get("do") == "face" and "mouth_open" in c.get("keys", {}) and c["keys"]["mouth_open"] >= 0.2:
            c["keys"]["mouth_open"] = 0.12
