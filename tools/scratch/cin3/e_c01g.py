"""C01 pass 6: 5 further north of the tripod; 7 west so her head is in the frame; 8 and 8b looser."""


def edit(shots, f):
    shots["5"]["cam"]["pos"] = [-11.6, 0.45, 88.7]
    shots["7"]["cam"]["pos"] = [-9.55, 1.12, 91.45]
    for sid, off, lens in (("8", [0.08, -0.02, -1.0], 70), ("8b", [0.06, -0.02, -0.9], 85)):
        c = shots[sid]["cam"]
        c["pos"] = {"actor": "her", "bone": "eyes", "off": off}
        c["at"] = {"actor": "her", "bone": "eyes", "off": [0, -0.05, 0]}
        c["lens"] = lens
