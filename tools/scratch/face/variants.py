"""variants.py <out faces.json> fit.json ... : the fits averaged, and that average with research tweaks on top."""
import json
import sys

fits = [json.load(open(p, encoding="utf-8-sig")) for p in sys.argv[2:]]
keys = sorted({k for f in fits for k in f})
avg = {k: round(sum(f.get(k, 0.0) for f in fits) / len(fits), 3) for k in keys}
avg = {k: v for k, v in avg.items() if v > 0.02}
# Feminine cues the landmarks see little of (FACE_RESEARCH.md 1): fuller lips,
# the lower fuller; a refined nose tip; a slimmer lower face; a slight lift.
fem = dict(avg)
for k, v in {"mouth-upperlip-volume-incr": 0.5, "mouth-lowerlip-volume-incr": 0.7, "mouth-cupidsbow-incr": 0.4,
             "nose-point-width-decr": 0.3, "nose-point-up": 0.2, "X-eye-scale-incr": 0.15, "X-eye-corner2-up": 0.25,
             "chin-width-decr": 0.15, "head-fat-decr": 0.2}.items():
    fem[k] = round(fem.get(k, 0.0) + v, 3)
out = {"avg": dict(avg, **{"-": True}), "fem": dict(fem, **{"-": True}), "old": {}}
json.dump(out, open(sys.argv[1], "w"), indent=1)
json.dump(fem, open(sys.argv[1].replace(".json", "_fem.json"), "w"), indent=1)
print(json.dumps(fem))
