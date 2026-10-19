# k14 (C03): s3b cut (k13B_verdict.md); its sky-saturation dip and s4's reset of it dropped together.
def edit(shots, f):
    shots["4"]["cues"] = [c for c in shots["4"]["cues"] if c.get("do") != "atmosphere"]
    f["shots"][:] = [s for s in f["shots"] if s["id"] != "3b"]
