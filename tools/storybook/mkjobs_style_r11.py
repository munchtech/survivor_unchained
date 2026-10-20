"""Round 11 (style_r11.json): pick the hand's words. r10's shared repaint unified
the four but its "visible brush marks" read as confetti: colored dabs scattered
over rock, snow and shadow (an AI tell, and the judge's "no surface patterns").
Two restrained hands, H2 (old masters' method: umber ground, brown underpainting,
glazed shadows, opaque lights) and H3 (a tonal painting, broad flat shadow masses),
on: (A) the shared repaint of r1's P1 and P7 flattened first (unify.py --simplify);
(B) the r2 content: P1 and P9 from our block-ins, P7 from its paint-over;
(C) P4 from the braced pose, pulled back 15% (layouts/p4_pose_r2.json)."""
import json
import os

FRAME = "A full-bleed illustration that fills the entire frame edge to edge, with no border, no margin and no paper edge. "
HANDS = {
    "H2": ("An oil painting made in the old masters' way for a book plate: a warm raw-umber toned ground and a brown "
           "monochrome underpainting, with bold dark brush-ink contours on the figures and the main shapes. The shadows are "
           "thin, flat, transparent glazes of umber and dark blue with the warm ground glowing through; only the lit parts are "
           "painted with opaque, thicker paint. Large calm simple shapes, broad unbroken shadow masses, very little detail, "
           "deep chiaroscuro, realistic proportions, grim and serious. "),
    "H3": ("A restrained dark tonal painting for a book plate, painted in oils over a bold ink drawing on a warm brown toned "
           "ground: broad flat masses of shadow, softly brushed, with only a few deliberate opaque strokes where the light "
           "falls; heavy ink contours on the figures; almost no texture in the shadows; a limited palette of umber, slate and "
           "indigo with the story's lights; quiet, grim and serious, realistic proportions. "),
}
CONTENT = {
    "p1": ("Night, two thousand years ago. From the near rim of a great raw cut dug into a hillside we look down across it. "
           "At the left, close to us, two ancient soldiers stand on our rim with their backs to us, dark shapes in rust-red wool "
           "cloaks and dull bronze helmets with crests and cheek guards; one holds a small torch low in front of him. Across the "
           "cut, a long column of tiny figures carrying torches winds down the far wall in an S-shaped path to the bottom of "
           "the picture; the torches are the brightest things in the picture. The far wall is a few big flat planes of dark "
           "rock. Above it the dark hillside rises to a crest under a strip of night sky. Torch smoke drifts. The orange "
           "torchlight is the only strong color; everything else is night."),
    "p4": ("Night, hard frost on a field beside a pale road, small ember-gold glints scattered in the frozen soil. A dead "
           "villager stands upright, slack, arms hanging, head tilted, in a torn linen shirt; his gray face is blank, the mouth "
           "hanging open and the empty eye sockets glowing with soft golden light from inside, his skin lit from within like "
           "paper over a lamp. To the right an old watchman with a gray beard, in a slate blue-gray hooded cloak over a plain "
           "wool tunic, a matte round wooden shield with a dull iron boss on his arm, leans in with his weight forward and "
           "both hands on a plain dark spear whose head is buried in the dead man's chest; golden light bursts out around the "
           "shaft and pours down onto the frost as small glowing stones. A pale white plume of breath leaves the watchman's "
           "mouth. The golden light is the only strong color; the rest is cold night, frost and slate."),
    "p7": ("The Low Ford at night in winter: a shallow river crossing between snowy banks, thin gray ice along both edges, a "
           "trodden track coming down through the snow to a line of flat stepping stones across the shallows. Three new black "
           "iron cage lanterns on thin black iron posts stand by the water, each burning with a plain cold pale blue flame and "
           "pooling blue light on the snow at its foot. Over the stepping stones, in the middle of the river, a fourth blue "
           "light floats just above the water in a wide cold glare, nothing visible holding it. Nobody is there. The cold blue "
           "is the only strong color; the rest is deep night."),
    "p9": ("Dusk, a deep blue sky over a thin dull rose band above the far hills. A small camp beside a rutted dirt track: a "
           "campfire burning high, a bedroll with its blanket folded on top, a pack. A lone traveler sits on a log by the fire "
           "with their back to us, the whole body wrapped from the hood to the ground in one plain dark wool hooded cloak, a "
           "simple cone shape, the head bowed over a folded letter held to the firelight; a small flask hangs on a cord from "
           "one wrist. Far up the track, the warm lamps of a waystation, one lamp higher than the rest. Low through the bare "
           "trees on the right, by the water, three small points of cold blue light. The fire's orange is the warm color; the "
           "rest is blue dusk."),
}
P = "tools/storybook/out/style_r11/prep/"
jobs = []
for h, hand in HANDS.items():
    for k in ("p1", "p7"):  # (A) the shared repaint over r1's frames, flattened
        jobs.append({"name": f"A_{k}_{h}", "prompt": FRAME + hand + CONTENT[k], "seed": [11], "init": P + k + "_init.png",
                     "denoise": 0.5, "control": P + k + "_edge.png", "strength": 0.5, "end": 0.6})
    for k, dn, st, end in (("p1", 0.85, 0.6, 0.6), ("p9", 0.85, 0.6, 0.6), ("p7", 0.6, 0.55, 0.75)):  # (B) the r2 content
        jobs.append({"name": f"B_{k}_{h}", "prompt": FRAME + hand + CONTENT[k], "seed": [11], "init": P + k + "b_init.png",
                     "denoise": dn, "control": P + k + "b_edge.png", "strength": st, "end": end})
    jobs.append({"name": f"C_p4_{h}", "prompt": FRAME + hand + CONTENT["p4"], "seed": [11],  # (C) the braced pose
                 "control": "tools/storybook/layouts/p4_pose_r2.png", "strength": 0.75})
here = os.path.dirname(os.path.abspath(__file__))
json.dump({"defaults": {"w": 1792, "h": 1024, "steps": 9}, "jobs": jobs},
          open(os.path.join(here, "jobs", "style_r11.json"), "w"), indent=1)
print(sum(len(j["seed"]) for j in jobs), "pictures")
