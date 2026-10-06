"""C01 pass 5: 3 lifted clear of the ring's stones; 5 north of the tripod's leg; 8, 8b tighter."""


def edit(shots, f):
    shots["3"]["cam"]["pos"] = [-11.05, 0.55, 89.22]
    shots["5"]["cam"]["pos"] = [-11.7, 0.45, 89.2]
    shots["6"]["cam"]["at"] = {"actor": "her", "bone": "chest", "off": [0, 0.0, 0], "track": True}
    for sid, off in (("8", [0.08, -0.06, -1.0]), ("8b", [0.06, -0.05, -0.88])):
        shots[sid]["cam"]["pos"] = {"actor": "her", "bone": "eyes", "off": off}
        shots[sid]["cam"]["at"] = {"actor": "her", "bone": "eyes", "off": [0, -0.09, 0]}
