"""Round 14 (style_r14.json): the ONE shared repaint for judge r2. The four r13 picks
(P1 s23, P4 s37, P7 i_s11, P9 s23), with paint_r14.py's content fixes painted in, go
through unify.py prep (the warm ground in the darks, stray hues capped, soft edges),
then the same img2img pass: r13's hand words plus each plate's content, its own soft
edges as the control (strength 0.5, end 0.6), the SAME seed for all four. Two denoise
levels (0.5, 0.6) and two seeds (11, 23); one level and one seed is then picked for
all four alike. unify.py finish follows.

    python tools/storybook/paint_r14.py
    python tools/storybook/unify.py prep tools/storybook/out/style_r14/src/p{1,4,7,9}.png --out tools/storybook/out/style_r14/prep
    python tools/storybook/mkjobs_style_r14.py
    python tools/storybook/gen.py tools/storybook/jobs/style_r14.json --out tools/storybook/out/style_r14
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mkjobs_style_r13 import CONTENT, FRAME, HAND  # noqa: E402  (re-writes style_r13.json unchanged)

P = "tools/storybook/out/style_r14/prep/"
jobs = []
for k in ("p1", "p4", "p7", "p9"):
    for dn in (0.5, 0.6):
        jobs.append({"name": f"{k}_d{int(dn * 100)}", "prompt": FRAME + HAND + CONTENT[k], "seed": [11, 23],
                     "init": P + k + "_init.png", "denoise": dn,
                     "control": P + k + "_edge.png", "strength": 0.5, "end": 0.6})
json.dump({"defaults": {"w": 1792, "h": 1024, "steps": 9}, "jobs": jobs},
          open(os.path.join(HERE, "jobs", "style_r14.json"), "w"), indent=1)
print(sum(len(j["seed"]) for j in jobs), "pictures (r14)")
