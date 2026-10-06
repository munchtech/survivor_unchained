"""presets_update.py <presets.json>: each preset's reference the new front one, and its shape its own key (no sliders)."""
import json
import sys

PICK = {"highborn": "highborn_23", "vixen": "vixen_23", "doe": "doe_37", "sunborn": "sunborn_23", "moonlit": "moonlit_37",
        "saffron": "saffron_23", "wildling": "wildling_37", "hardwon": "hardwon_11", "fey": "fey_37"}
p = sys.argv[1]
data = json.load(open(p, encoding="utf-8"))
for f in data:
    if f["id"] in PICK:
        f["ref"] = "front/" + PICK[f["id"]]
        f["shape"] = {}
    elif f["id"] == "own":
        f["ref"] = "front/her_23"
lines = []
for f in data:
    lines.append(" " + json.dumps(f, ensure_ascii=False))
open(p, "w", encoding="utf-8").write("[\n" + ",\n".join(lines) + "\n]\n")
print("presets", [(f["id"], f.get("ref"), f["shape"]) for f in data])
