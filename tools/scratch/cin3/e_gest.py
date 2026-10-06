"""Animation's gestures, laid over whatever she is doing: the nod (C03 3b), the shiver (C04 A5),
the exhale (C01 8). Pass the cinematic id as GEST env."""
import os

CID = os.environ["GEST"]


def edit(shots, f):
    if CID == "c03":
        s = shots["3b"]
        s["cues"] = [c for c in s["cues"] if c.get("do") != "lids"]
        s["cues"].append({"at": 0.9, "do": "anim", "clip": "her/nod", "from": 0, "speed": 1, "blend": 0.2})
    elif CID == "c04a":
        shots["A5"]["cues"].append({"at": 4.4, "do": "anim", "clip": "her/shiver", "from": 0, "speed": 1, "blend": 0.1})
    elif CID == "c01":
        shots["8"]["cues"].append({"at": 1.2, "do": "anim", "clip": "her/exhale", "from": 0, "speed": 1, "blend": 0.2})
