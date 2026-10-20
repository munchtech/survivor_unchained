"""Round 3 of the look (style_r3.json). r2's two hands came out the same: an
inked comic with hatching spread evenly over everything (an AI tell), and our
Kuwahara pass only smeared it. So r3 asks for painted hands with simple dark
masses and detail only where the light falls, and stands P4's dead man up with
a pose layout (layouts/p4_pose.png); r2 laid him down in all six."""
import json
import os

FRAME = "A full-bleed illustration that fills the entire frame edge to edge, with no border, no margin and no paper edge. "
STYLES = {
    "E": ("A dark fantasy book illustration painted by hand in opaque gouache on rough watercolor paper: broad confident brushstrokes and "
          "dry-brush edges, forms modeled in a few flat values, the shadows laid in as large simple flat washes of deep indigo and umber with "
          "no detail inside them, bold black brush-ink contours only along the main silhouettes, the paper's rough tooth showing through the "
          "thin paint, realistic proportions, grim and serious. "),
    "F": ("A grim dark fantasy illustration in black ink wash and watercolor on rough cold-press paper: wet washes with soft blooms and hard "
          "dried edges, bold black brush lines of varied weight on the main contours, heavy blacks, the large shadows kept simple and dark, "
          "color only where the light falls, realistic proportions, grim and serious. "),
    "G": ("A dark oil sketch for a book plate, painted loosely on a toned ground: thick paint where the light falls, thin transparent dark "
          "glazes in the shadows, visible brush marks, a few dark drawn lines, strong chiaroscuro, realistic proportions, grim and serious. "),
    "B2": ("A dark fantasy storybook painting, painted by hand with rough gouache and oil over a bold black ink drawing: gritty textured "
           "brushwork, ink contours of varied weight, realistic proportions, grim and serious, dramatic chiaroscuro, heavy black shadows, a "
           "muted desaturated palette of slate, umber and rust. "),
}
P9 = ("Dusk, the last light: a deep blue sky over a dull rose band low on the horizon. A small camp beside a dirt road: a campfire burning "
      "high in the middle distance, a log, a bedroll unrolled with its blanket still folded on it, a pack. In the right foreground a lone "
      "traveler sits on the log facing the fire, seen from directly behind: we see only the back of a long hooded coat of dark weathered "
      "wool and the deep hood up, the head hidden inside it; the traveler holds up a folded letter to the firelight, a small flask on a cord "
      "wound round one gloved wrist. The traveler is a dark shape against the fire. The road runs on past the fire into the distance, where "
      "the tiny warm lamps of a waystation sit far up the road, one lamp higher than the rest. Low among the dark trees to the right, by "
      "unseen water, three small points of cold pale-blue light. The firelight is warm orange-gold; the dark around it is blue.")
P4 = ("Night, hard frost on a field beside a road. In the middle of the picture a dead man stands upright on his feet, slack, his arms "
      "hanging at his sides, his head tilted, his skin gray; a dull orange glow shines out from inside him through his open mouth, his empty "
      "eye sockets and the wounds in his chest. To the right an old watchman with a gray beard, in a slate blue-gray hooded cloak, a round "
      "wooden shield on his left arm, lunges at him and drives a long spear into the standing dead man's chest; from the wound the orange "
      "light pours out and falls onto the frost as a scatter of small glowing orange stones. Behind them another body lies dark on the frost. "
      "The watchman's breath smokes in the cold. The orange light is the only strong color; the rest is cold night and frost, slate and gray.")

jobs = []
for st in ("E", "F", "G"):
    jobs.append({"name": f"p9_{st}", "prompt": FRAME + STYLES[st] + P9, "seed": [5, 77]})
for st in ("E", "F", "G", "B2"):
    jobs.append({"name": f"p4_{st}", "prompt": FRAME + STYLES[st] + P4, "seed": [5, 77],
                 "control": "tools/storybook/layouts/p4_pose.png", "strength": 0.75})
here = os.path.dirname(os.path.abspath(__file__))
json.dump({"defaults": {"w": 1792, "h": 1024, "steps": 9}, "jobs": jobs},
          open(os.path.join(here, "jobs", "style_r3.json"), "w"), indent=1)
print(sum(len(j["seed"]) for j in jobs), "pictures")
