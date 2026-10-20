"""Round 6 (style_r6.json): P1's thing. r5's 'long smooth pale curve' drew a
giant segmented worm snaking along the floor (and one seed showed its end, the
'never the whole' rule broken). Now a broad dome wider than the cut, its sides
under the walls: the top of a back, not a tube. With and without a layout
(layouts/p1_layout_dome.png: r5 lay_s77's soldiers and column, the floor cleared,
a dome drawn wall to wall)."""
import json
import os

FRAME = "A full-bleed illustration that fills the entire frame edge to edge, with no border, no margin and no paper edge. "
G2 = ("A dark oil sketch for a book plate, painted loosely on a toned ground over a bold brush-ink drawing whose dark lines show through "
      "on the main contours: thick paint where the light falls, thin transparent dark glazes in the shadows, visible brush marks, strong "
      "chiaroscuro, realistic proportions, grim and serious. ")
P1 = ("Night, two thousand years ago. Seen from high on the rim of a vast deep cut in a hillside, looking steeply down into it. In the "
      "foreground at the top left, two ancient legionaries seen from behind, in crested bronze helmets with cheek guards and rust-red cloaks "
      "over banded armor, hold torches high. From them a long column of legionaries with torches winds down a narrow path along the cut's "
      "steep wall, the figures growing smaller and smaller as they go down into the dark; one carries a standard on a pole. Far below, the "
      "cut's whole floor is the top of something vast: one broad pale dome of smooth gray-white hide with faint broad ridges across it, far "
      "wider than the cut, its sides running in under the rock walls on both sides, so that only the top of its back shows above the earth. "
      "The tiny torches at the bottom of the path show how enormous it is. It is dim, lit only by the torches. Torch smoke drifts and sparks "
      "fall into the dark. The orange torchlight is the only strong color; everything else is night.")
jobs = [
    {"name": "p1_dome", "prompt": FRAME + G2 + P1, "seed": [5, 31, 77, 101]},
    {"name": "p1_dome_lay", "prompt": FRAME + G2 + P1, "seed": [5, 31, 77, 101],
     "control": "tools/storybook/layouts/p1_layout_dome.png", "strength": 0.4},
]
here = os.path.dirname(os.path.abspath(__file__))
json.dump({"defaults": {"w": 1792, "h": 1024, "steps": 9}, "jobs": jobs},
          open(os.path.join(here, "jobs", "style_r6.json"), "w"), indent=1)
print(sum(len(j["seed"]) for j in jobs), "pictures")
