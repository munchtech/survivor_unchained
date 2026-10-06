"""C01 pass 3: a touch nearer the fire; 3 from above her face; 5 and 6 clear of the tripod; 6 wider for her
hands; 8 and 8b back off and down."""


def edit(shots, f):
    m = f["marks"]
    lx, lz, lh = m["lie"]
    m["lie"] = [round(lx - 0.12, 2), round(lz - 0.03, 2), lh]
    s = shots["3"]
    s["cam"]["pos"] = {"actor": "her", "bone": "eyes", "off": [-0.42, 0.5, 0.12]}
    s["cam"]["lens"] = 70
    s = shots["5"]
    s["cam"]["pos"] = [-11.4, 0.45, 91.5]
    s = shots["6"]
    s["cam"]["pos"] = [-10.3, 0.9, 92.2]
    s["cam"]["at"] = {"actor": "her", "bone": "chest", "off": [0, 0.12, 0], "track": True}
    s["cam"]["lens"] = 40
    s["type"] = "MS"
    for sid, off in (("8", [0.08, -0.06, -1.2]), ("8b", [0.06, -0.05, -1.05])):
        s = shots[sid]
        s["cam"]["pos"] = {"actor": "her", "bone": "eyes", "off": off}
        s["cam"]["at"] = {"actor": "her", "bone": "eyes", "off": [0, -0.1, 0]}
