# k13a pass 4 (C01): s3 stayed flat whatever the rigs did: the camp fire's own light sits right behind the lens (the fire
# mark is 1 m behind the camera, on its axis), lighting her face frontally and putting the catchlight dead centre.
# Fire light off for s3 (s6 sets it again); the rigs carry the face. s8b lips back to 0 (negative weights thinned the
# gap at -0.08 and widened it at -0.2).
def edit(shots, f):
    for c in shots["3"]["cues"]:
        if c.get("do") == "light" and c.get("light") == 0: c["level"] = 0.0
        if c.get("name") == "key": c["energy"] = 1.3
        if c.get("name") == "moon": c["energy"] = 0.8
        if c.get("name") == "fill": c["energy"] = 0.14
    for c in shots["8b"]["cues"]:
        if c.get("do") == "face" and "at" not in c: c["keys"]["mouth_open"] = 0.0
