"""Round 4 of the look (style_r4.json): the hand is G (r3: an oil sketch on a
toned ground read as painted at 1:1; E went flat vector, F and B2 comic ink).
G2 tries G over a brush-ink drawing for the 'inked' half of the brief. The
scenes carry r3's content fixes: P1's curve far below and dim (r2 drew a clean
ornamented shell in the foreground), P4's dead man a villager in period cloth
with the light at mouth and eyes, P9 three-quarters from behind. Plus one
upscale test (img2img at 1.5x) for the plates' real resolution."""
import json
import os

FRAME = "A full-bleed illustration that fills the entire frame edge to edge, with no border, no margin and no paper edge. "
STYLES = {
    "G": ("A dark oil sketch for a book plate, painted loosely on a toned ground: thick paint where the light falls, thin transparent dark "
          "glazes in the shadows, visible brush marks, a few dark drawn lines, strong chiaroscuro, realistic proportions, grim and serious. "),
    "G2": ("A dark oil sketch for a book plate, painted loosely on a toned ground over a bold brush-ink drawing whose dark lines show through "
           "on the main contours: thick paint where the light falls, thin transparent dark glazes in the shadows, visible brush marks, strong "
           "chiaroscuro, realistic proportions, grim and serious. "),
}
P1 = ("Night, long ago. Seen from high on the rim of a vast deep cut in a hillside, looking steeply down into it. In the foreground at the "
      "top of the frame, two soldiers in rust-red cloaks and dull bronze helmets, seen from behind, hold torches high. From them a long "
      "column of soldiers with torches winds down a narrow path along the cut's steep wall, the figures growing smaller and smaller as they "
      "go down into the dark; one carries a standard on a pole. Far below, at the very bottom of the cut, half buried in the earth, lies one "
      "pale curve of something enormous: a low smooth hump the color of old bone, ridged with great ribs, larger than the cut itself, dim in "
      "the darkness; nothing else of it is visible. Torch smoke drifts and sparks fall into the dark. The orange torchlight is the only "
      "strong color; everything else is night.")
P4 = ("Night, hard frost on a field beside a road. In the middle of the picture a dead man stands upright on his feet, slack, his arms "
      "hanging at his sides, his head tilted, his face empty and slack with the mouth hanging open; a villager long dead, in a torn linen "
      "shirt and wool breeches, his skin gray; a dull orange glow shines out from inside him through his open mouth, his empty eye sockets "
      "and the wounds in his chest. To the right an old watchman with a gray beard, in a slate blue-gray hooded cloak over mail, a round "
      "wooden shield on his left arm and a small lamp on his belt, lunges at him and drives a long spear into the standing dead man's chest; "
      "from the wound the orange light pours out and falls onto the frost as a scatter of small glowing orange stones. Behind them another "
      "body lies dark on the frost. The watchman's breath smokes in the cold. The orange light is the only strong color; the rest is cold "
      "night and frost, slate and gray.")
P9 = ("Dusk, the last light: a deep blue sky over a dull rose band low on the horizon. A small camp beside a dirt road: a campfire burning "
      "high in the middle distance, a log, a bedroll unrolled with its blanket still folded on it, a pack. In the right foreground a lone "
      "traveler sits on the log facing the fire, seen three-quarters from behind: we see the back of a long hooded coat of dark weathered "
      "wool and the deep hood up, the head hidden inside it; the traveler holds up a folded letter to the firelight, a small flask on a cord "
      "wound round one gloved wrist. The traveler is a dark shape against the fire. The road runs on past the fire into the distance, where "
      "the tiny warm lamps of a waystation sit far up the road, one lamp higher than the rest. Low among the dark trees to the right, by "
      "unseen water, three small points of cold pale-blue light. The firelight is warm orange-gold; the dark around it is blue.")

jobs = []
for st, seeds in (("G", [5, 31, 77]), ("G2", [5, 31])):
    jobs.append({"name": f"p1_{st}", "prompt": FRAME + STYLES[st] + P1, "seed": seeds})
    jobs.append({"name": f"p4_{st}", "prompt": FRAME + STYLES[st] + P4, "seed": seeds,
                 "control": "tools/storybook/layouts/p4_pose.png", "strength": 0.75})
    jobs.append({"name": f"p9_{st}", "prompt": FRAME + STYLES[st] + P9, "seed": seeds})
# The upscale test: r3's p9_G_s5 at 1.5x, repainted lightly.
jobs.append({"name": "up_p9_G", "prompt": FRAME + STYLES["G"] + P9, "seed": 5, "w": 2688, "h": 1536,
             "init": "tools/storybook/out/style_r3/p9_G_s5.png", "denoise": 0.35})
here = os.path.dirname(os.path.abspath(__file__))
json.dump({"defaults": {"w": 1792, "h": 1024, "steps": 9}, "jobs": jobs},
          open(os.path.join(here, "jobs", "style_r4.json"), "w"), indent=1)
print(sum(len(j["seed"]) if isinstance(j["seed"], list) else 1 for j in jobs), "pictures")
