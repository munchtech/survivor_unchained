"""Round 2 of the look: two grimmer hands, full-bleed, with the r1 composition faults fixed (style_r2.json)."""
import json, os

FRAME = "A full-bleed illustration that fills the entire frame edge to edge, with no border, no margin and no paper edge. "
STYLES = {
    "B2": ("A dark fantasy storybook painting, painted by hand with rough gouache and oil over a bold black ink drawing: gritty textured brushwork, "
           "ink contours of varied weight, realistic proportions, grim and serious, dramatic chiaroscuro, heavy black shadows, a muted desaturated palette "
           "of slate, umber and rust. "),
    "D2": ("A dark painterly illustration drawn by hand: bold black ink and charcoal lines on dark toned paper, with gouache color laid in only where the "
           "light falls, smudged charcoal shadows, the paper's tooth visible, realistic proportions, grim and serious. "),
}
SCENES = {
    "p1": ("Night, long ago. Seen from high on the rim of a vast deep cut in a hillside: a long column of soldiers in rust-red cloaks and dull bronze "
           "helmets winds down a narrow path along the cut's wall carrying torches, the small figures growing smaller as they go down into the dark; "
           "one carries a standard topped with VII. At the very bottom of the cut, far below, a colossal pale curved surface rises out of the earth: a "
           "low smooth ivory-white hump ridged with great ribs, larger than the cut itself, with no head, no eyes, no limbs; nothing else of it is "
           "visible. In the foreground at the top of the frame, two soldiers seen from behind hold torches high. Torch smoke drifts and sparks fall "
           "into the dark. The orange torchlight is the only strong color; everything else is night."),
    "p4": ("Night, hard frost on a field beside a road. A dead man stands upright, slack and blank-faced, arms hanging, his skin gray; a dull orange "
           "glow shines from inside him through his open mouth, his empty eye sockets and the wounds in his chest, like a lamp behind paper. An old "
           "watchman with a gray beard, in a slate blue-gray hooded cloak, a round wooden shield on his left arm, drives a long spear into the dead "
           "man's chest; from the wound the orange light pours out and falls onto the frost as a scatter of small glowing stones like coals. Behind "
           "them another body lies dark and empty on the frost. The watchman's breath smokes in the cold; the dead man breathes nothing. Small "
           "orange embers glint in the dark soil. The orange light is the only strong color; the rest is cold night and frost."),
    "p9": ("Dusk, the last light: a deep blue sky over a dull rose band low on the horizon. A small camp beside a dirt road: a campfire burning "
           "high, a log, a bedroll unrolled with its blanket still folded on it, a pack. A lone traveler sits by the fire, seen from behind, in a "
           "long hooded coat of dark weathered wool with the deep hood up, reading a folded letter, a small flask on a cord wound round one gloved "
           "wrist. Far up the road, the tiny warm lamps of a distant waystation, one lamp higher than the rest. Low among the dark trees to the "
           "right, by unseen water, three small points of cold pale-blue light. The firelight is warm orange-gold; the dark around it is blue."),
}
jobs = []
for sk, scene in SCENES.items():
    for st, style in STYLES.items():
        jobs.append({"name": f"{sk}_{st}", "prompt": FRAME + style + scene, "seed": [5, 31, 77]})
json.dump({"defaults": {"w": 1792, "h": 1024, "steps": 9}, "jobs": jobs}, open(os.path.join("jobs", "style_r2.json"), "w"), indent=1)
print(len(jobs) * 3, "pictures")
