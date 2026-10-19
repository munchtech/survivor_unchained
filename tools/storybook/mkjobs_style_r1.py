"""Round 1 of the look: three SB00 frames in four candidate hands (style_r1.json)."""
import json, os

STYLES = {
    "A": ("An ink and watercolor wash illustration on toned paper. Loose, confident black ink brush lines with dry-brush texture; "
          "layered transparent washes of deep indigo, umber and slate gray; the paper grain shows through the washes; highlights left as bare paper; "
          "large simple shapes, deep shadows, detail only where the light falls."),
    "B": ("A painted storybook illustration: opaque gouache brushwork over a rough ink drawing, visible brushstrokes and textured edges, "
          "hand-drawn ink outlines of varied weight, muted earthy palette, dramatic chiaroscuro, a dark vignette, aged paper texture."),
    "C": ("An etching and aquatint print, colored by hand with watercolor: fine cross-hatched ink lines, sepia and black ink on cream paper, "
          "soft plate tone in the shadows, the lights tinted by hand."),
    "D": ("A charcoal and chalk pastel drawing on dark gray paper: bold gestural charcoal lines, smudged soft shadows, "
          "the light laid in with warm pastel strokes, paper tooth visible everywhere."),
}
SCENES = {
    "p1": ("Night on a steep hillside, long ago. A column of legionaries in rust-red cloaks and dull bronze helmets carries torches down a path into a great deep cut in the hill, "
           "small figures in a long line descending from the upper left; one carries a standard marked VII. Far below at the bottom of the cut, one enormous pale ribbed curve "
           "breaks out of the dark earth, like the back of a sleeping whale breaking the sea, bigger than the cut itself; only that curve is seen. Torches close in the foreground, "
           "torch smoke and falling sparks, the column in the middle distance, the pale curve far below in darkness. "
           "The only strong color is the orange-gold torchlight; everything else is night."),
    "p4": ("Night, hard frost on a field beside a road. Small orange embers glint in the dark soil like coals in ash. A dead man stands slack and blank-faced, his skin gray, "
           "a warm orange light glowing from inside his open mouth, his eye sockets and his wounds, like a lamp behind paper. An old watchman with a gray beard, in a slate "
           "blue-gray cloak, with a round wooden shield on his arm, drives a spear into the dead man's chest; the light pours out of the wound onto the frost as a scatter of small "
           "glowing stones. The watchman's breath smokes in the cold air. The orange-gold light is the only strong color; the rest is cold night and frost."),
    "p9": ("Dusk, the last light: a deep blue sky over a dull rose band low on the horizon. A small camp beside a dirt road: a campfire burning high, a log, a bedroll unrolled "
           "with its blanket still folded on it, a pack. A lone traveler sits by the fire with the hood of a long coat up, seen from behind, reading a folded letter, a small "
           "flask on a cord wound round one wrist. Far up the road, the tiny warm lamps of a distant waystation, one lamp higher than the rest. Low through the dark trees to the "
           "right, by unseen water, three small points of cold pale-blue light. The firelight is warm orange-gold; the dark around it is blue."),
}
jobs = []
for sk, scene in SCENES.items():
    for st, style in STYLES.items():
        jobs.append({"name": f"{sk}_{st}", "prompt": style + " " + scene, "seed": [11, 23]})
json.dump({"defaults": {"w": 1792, "h": 1024, "steps": 9}, "jobs": jobs}, open(os.path.join("jobs", "style_r1.json"), "w"), indent=1)
print(len(jobs) * 2, "pictures")
