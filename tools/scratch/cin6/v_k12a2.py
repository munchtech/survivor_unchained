# k12a2: s2 and s3 on the other lying clips. D: death_back held, the clip's own head. E: death_back held, the
# head turned to the coals (HeadTurn keeps a lying head's roll with the body). P: death held (prone), head to the coals.
import importlib.util, os
spec = importlib.util.spec_from_file_location("v1", os.path.join(os.path.dirname(os.path.abspath(__file__)), "v_k12a1.py"))
v1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v1)
EYES = v1.EYES


def lying(clip, frm, mark, head_to):
    def fn(shots, f):
        f["marks"]["down"] = mark
        s1 = shots["1"]["cues"]
        for c in s1:
            if c.get("do") == "anim" and c.get("clip") == "her/lie_side_wake":
                c.update({"clip": clip, "from": frm, "speed": 0, "blend": 0})
            if c.get("do") == "head":
                if head_to is None: c.update({"amount": 0})
                else: c.update({"where": head_to, "amount": 1.0})
        s1.insert(0, {"do": "place", "where": mark[:2], "heading": mark[2]})
        shots["2"]["cues"] = [c for c in shots["2"]["cues"] if c.get("do") != "anim"]
        s3 = shots["3"]
        s3["cam"] = {"pos": {**EYES, "off": [-0.62, -0.1, 0.02]}, "at": {**EYES, "off": [0, -0.06, 0]}, "lens": 70, "focus": EYES, "fstop": 2.0}
        s3["cues"] = [dict(c) for c in v1.LIGHT] + [dict(c) for c in v1.EYES_OPEN]
    return fn


VARIANTS = {
    "D": lying("her/death_back", 1.33, [-9.65, 91.12, 0.0], None),
    "E": lying("her/death_back", 1.33, [-9.65, 91.12, 0.0], [-10.25, 0.05, 89.95]),
    "P": lying("her/death", 1.5, [-9.536, 91.561, 3.1416], [-10.3, 0.05, 90.4]),
}
