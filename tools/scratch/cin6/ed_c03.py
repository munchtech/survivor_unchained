def edit(shots, f):
    f["shots"] = [s for s in f["shots"] if s["id"] != "13"]
    f["end"]["next"] = "c04a"
