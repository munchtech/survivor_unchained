def edit(shots, f):
    # Her walk to the top outlasts the shot by a second: play takes her mid-stride, and she walks on into it.
    for c in shots["A8"]["cues"]:
        if c.get("do") == "move":
            c["dur"] = 6.5
