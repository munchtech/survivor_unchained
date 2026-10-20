"""Round 5 (style_r5.json): the style frames' content fixes, in hand G2.
P1: r4 drew WWI tin hats and a beast's skeleton ("bone", "ribs"); now ancient
legionaries and a hide-covered curve filling the cut's floor, plain and with an
edge layout taken from r4's p1_G2_s31 with the skeleton replaced by the hump
(layouts/p1_layout_edges.png). P4: the dead man's head repainted on r4's
p4_G2_s5 (he read as a startled living youth): slack, sockets and mouth lit."""
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
      "whole floor of the cut is filled from wall to wall by the top of something enormous breaking out of the earth: one long smooth pale "
      "curve of gray-white hide, ribbed with broad shallow folds, running on under the rock on both sides; only this curve of it shows, the "
      "rest is buried. It is dim, lit only by the torches far above. Torch smoke drifts and sparks fall into the dark. The orange torchlight "
      "is the only strong color; everything else is night.")
P4 = ("Night, hard frost on a field beside a road. In the middle of the picture a dead man stands upright on his feet, slack, his arms "
      "hanging at his sides, his head tilted; a villager long dead, in a torn linen shirt and wool breeches; his face is gray, slack, blank "
      "and empty, the eyes gone to dark hollow sockets with a dull orange glow deep inside them, the mouth hanging open with dull orange "
      "light inside it. To the right an old watchman with a gray beard, in a slate blue-gray hooded cloak over mail, a round wooden shield "
      "on his left arm, drives a long spear into the standing dead man's chest; from the wound the orange light pours out. The watchman's "
      "breath smokes in the cold. The orange light is the only strong color; the rest is cold night and frost, slate and gray.")

jobs = [
    {"name": "p1_G2", "prompt": FRAME + G2 + P1, "seed": [5, 31, 77]},
    {"name": "p1_G2_lay", "prompt": FRAME + G2 + P1, "seed": [5, 31, 77],
     "control": "tools/storybook/layouts/p1_layout_edges.png", "strength": 0.45},
    {"name": "p4_G2_head", "prompt": FRAME + G2 + P4, "seed": [5, 31, 77],
     "inpaint": "tools/storybook/out/style_r4/p4_G2_s5.png", "mask": "tools/storybook/layouts/p4_head_mask.png"},
]
here = os.path.dirname(os.path.abspath(__file__))
json.dump({"defaults": {"w": 1792, "h": 1024, "steps": 9}, "jobs": jobs},
          open(os.path.join(here, "jobs", "style_r5.json"), "w"), indent=1)
print(sum(len(j["seed"]) for j in jobs), "pictures")
