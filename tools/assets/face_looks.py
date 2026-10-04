"""Her face's sliders and faces written into the game's looks
(godot/data/content/looks.json, heroes.female), from face_shapes.py, so the
game's sliders are always the keys her head was made with.

    python tools/assets/face_looks.py [faces.json]

faces.json (face_presets.py's): [{"id", "name", "words", "shape": {slider: v}}, ...],
her faces to start from, in order (the first her own). Without it her
faces are kept, any slider they name that is gone dropped.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import face_shapes as fs  # noqa: E402

LOOKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "godot", "data", "content", "looks.json")


def sliders():
    """Each slider as the game reads it (Lore.FaceSlider): every one runs
    the whole way, -1 to 1 (its reach is in its keys: face_shapes.REACH)."""
    out = []
    for group in fs.SLIDER_GROUPS:
        for sid, (g, name, low, high, _p, _m) in fs.SLIDERS.items():
            if g == group:
                out.append({"id": sid, "name": name, "group": g, "low": low, "high": high})
    return out


def fmt(o, level=0, key=None, under_heroes=False):
    """The file as it is written by hand: indented a space a level, and the
    heroes' choices one to a line."""
    pad, sub = " " * level, " " * (level + 1)
    if isinstance(o, dict):
        items = [f'{sub}{json.dumps(k)}: {fmt(v, level + 1, k, under_heroes or k == "heroes")}' for k, v in o.items()]
        return "{\n" + ",\n".join(items) + "\n" + pad + "}" if items else "{}"
    if isinstance(o, list):
        if under_heroes and all(isinstance(x, dict) for x in o):
            lines = [sub + json.dumps(x, ensure_ascii=False) for x in o]
        else:
            lines = [sub + fmt(x, level + 1, None, under_heroes) for x in o]
        return "[\n" + ",\n".join(lines) + "\n" + pad + "]" if lines else "[]"
    return json.dumps(o, ensure_ascii=False)


if __name__ == "__main__":
    looks = json.load(open(LOOKS, encoding="utf-8"))
    her = looks["heroes"]["female"]
    her["sliders"] = sliders()
    ids = {s["id"] for s in her["sliders"]}
    if len(sys.argv) > 1:
        her["faces"] = json.load(open(sys.argv[1], encoding="utf-8-sig"))
    for f in her["faces"]:
        f["shape"] = {k: round(float(v), 3) for k, v in f["shape"].items() if k in ids}
    with open(LOOKS, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(fmt(looks) + "\n")
    print(len(her["sliders"]), "sliders,", len(her["faces"]), "faces ->", os.path.normpath(LOOKS))
