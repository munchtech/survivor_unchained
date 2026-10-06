"""C01 pass 4: she faces west-north-west, lying and kneeling. 3 and 5 look back along her face across the
ring's edge; 6 is front three-quarter from her left across the embers; 10 from the south-west."""


def edit(shots, f):
    s = shots["3"]
    s["cam"]["pos"] = [-11.05, 0.3, 89.22]
    s["cam"]["at"] = {"actor": "her", "bone": "eyes", "off": [0, -0.02, 0]}
    s["cam"]["lens"] = 100
    s = shots["5"]
    s["cam"]["pos"] = [-11.6, 0.42, 89.8]
    s = shots["6"]
    s["cam"]["pos"] = [-11.1, 0.85, 91.6]
    for sid in ("8", "8b"):
        shots[sid]["cam"]["at"] = {"actor": "her", "bone": "eyes", "off": [0, -0.16, 0]}
    s = shots["10"]
    s["cam"]["pos"] = [-10.4, 1.1, 92.1]
