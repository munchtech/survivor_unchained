"""C01 pass 6c check (mkt.py): the kneel, the letter and the end, her lids open (shot 3, which opens them, is cut)."""
ONLY = ["6", "6a", "6b", "6c", "9", "10", "11", "11m", "12"]
V = {}


def EDIT(shots, d):
    shots["6"]["cues"] = [{"do": "lids", "value": None}, {"do": "anim", "clip": "her/lie_side_wake", "from": 6.9, "speed": 0, "blend": 0}] + shots["6"]["cues"]
