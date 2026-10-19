# k11b pass 2 (C03 s3b): tighter still, framed higher, so only the pauldron tops show.
def edit(shots, f):
    shots["3b"]["cam"]["lens"] = 66; shots["3b"]["cam"]["at"] = {"actor": "her", "bone": "eyes", "off": [0, 0.03, 0]}
