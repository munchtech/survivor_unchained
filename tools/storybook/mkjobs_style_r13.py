"""Round 13 (style_r13.json): r12's content fixed. The hand drops "a warm brown toned
ground" (it browned every sky; the umber goes in by unify.py's ground step instead)
and asks for a night palette of indigo, slate and umber. P1: the S starts below the
far rim (r12's run along the rim read as runway lights again), the near soldiers as
dark silhouettes. P4: the spearhead's edges cleared so it reads buried; the dead as a
corpse. P9: the blue lamps far apart (r12 made pairs, read as eyes), a squat tower.
P7: r12's pick (p7_r_s11) with the ford's stones and open iron cages inpainted (its
lanterns read as park lamps)."""
import json
import os

FRAME = "A full-bleed illustration that fills the entire frame edge to edge, with no border, no margin and no paper edge. "
HAND = ("A restrained dark tonal painting for a book plate, in loose oil paint over a bold brush-ink drawing: broad simple "
        "masses of shadow thinly glazed, a few deliberate thick opaque strokes only where the light falls; heavy dark ink "
        "contours on the figures; painterly soft edges, almost no texture in the shadows; a night palette of deep indigo, "
        "slate and umber with the story's lights; quiet, grim and serious, realistic proportions. ")
CONTENT = {
    "p1": ("Night, two thousand years ago. From the near rim of a great raw cut dug into a hillside we look down across it. "
           "At the left, close to us, two ancient soldiers stand on our rim with their backs to us, seen only as dark "
           "silhouettes edged with a thin line of torchlight, their wool cloaks a dull dark rust-red, dull bronze helmets with "
           "crests and cheek guards; one holds a small torch out in front of him, half hidden by his body. Across the cut, a "
           "long column of tiny figures carrying torches winds down the far wall in an S-shaped path from just below the far "
           "rim to the bottom of the picture; the torches are the brightest things in the picture. The far wall is a few big "
           "flat planes of dark rock, cold slate and indigo where the torchlight doesn't reach. Above it the dark empty "
           "hillside rises to a crest under a strip of deep indigo night sky. Torch smoke drifts. The orange torchlight is the "
           "only strong color; everything else is night."),
    "p4": ("Night under a dark slate-blue sky, hard frost on a field beside a pale road, small ember-gold glints scattered in "
           "the frozen soil, a dark body lying in the frost behind. A dead villager stands upright, slack, arms hanging, head "
           "tilted, in a torn linen shirt: a corpse, gray waxy skin, sunken cheeks, matted hair flat, the jaw hanging open and "
           "the eyes gone, the mouth and the two empty sockets glowing with soft golden light from inside, his skin lit from "
           "within like paper over a lamp. To the right an old watchman with a gray beard, in a slate blue-gray hooded cloak "
           "over a plain wool tunic, a matte round wooden shield with a dull iron boss on his arm, leans in with his weight "
           "forward and both hands on a plain dark spear; the spear's head is hidden deep inside the dead man's chest, and "
           "golden light bursts out around the shaft where it enters and pours down onto the frost as small glowing stones. A "
           "pale white plume of breath leaves the watchman's mouth. The golden light is the only strong color; the rest is "
           "cold night, frost and slate."),
    "p7": ("The Low Ford at night in winter: a shallow river crossing between snowy banks, thin gray ice along both edges, a "
           "trodden track through the snow. Three new open cages of crude hand-forged black iron bars on thin black iron "
           "posts, no glass, each with a cold pale blue flame burning inside, pooling blue light on the snow at its foot. A "
           "line of large flat dark stepping stones with snow on their tops crosses the shallows; over them, in the middle of "
           "the river, a fourth blue light hangs a little above the water in a wide cold glare, nothing visible holding it. "
           "Nobody is there. The cold blue is the only strong color; the rest is deep night."),
    "p9": ("Dusk, a deep blue sky over a thin dull rose band above the far hills. A small camp beside a rutted dirt track: a "
           "campfire burning high, a bedroll with its blanket folded on top, a pack. A lone traveler sits on a log by the fire "
           "with their back to us, the whole body wrapped from the hood to the ground in one plain dark wool hooded cloak, a "
           "simple cone shape, the head bowed over a folded letter held to the firelight; a small leather flask hangs on a "
           "cord from one wrist. Far up the track on a low rise, the waystation: a small cluster of dark roofs beside a squat "
           "square stone watchtower with a flat top, its windows glowing warm orange, one lit window high on the tower. Low "
           "among the bare trees by the water on the right, three tiny cold blue lamp flames, far apart from each other, each "
           "with a short blue reflection in the water. The fire's orange is the warm color; the rest is blue dusk."),
}
P = "tools/storybook/out/style_r13/prep/"
L = "tools/storybook/layouts/"
jobs = [
    {"name": "p1_t", "prompt": FRAME + HAND + CONTENT["p1"], "seed": [11, 23, 37], "control": P + "p1b_edge.png",
     "strength": 0.6, "end": 0.7},
    {"name": "p9_t", "prompt": FRAME + HAND + CONTENT["p9"], "seed": [11, 23, 41], "control": P + "p9b_edge.png",
     "strength": 0.6, "end": 0.7},
    {"name": "p4_t", "prompt": FRAME + HAND + CONTENT["p4"], "seed": [11, 23, 37, 41], "control": L + "p4_edge_r3.png",
     "strength": 0.6, "end": 0.7},
    {"name": "p7_i", "prompt": FRAME + HAND + CONTENT["p7"], "seed": [11, 23], "inpaint": "tools/storybook/out/style_r12/p7_r_s11.png",
     "mask": L + "p7_fix_mask.png"},
]
here = os.path.dirname(os.path.abspath(__file__))
json.dump({"defaults": {"w": 1792, "h": 1024, "steps": 9}, "jobs": jobs},
          open(os.path.join(here, "jobs", "style_r13.json"), "w"), indent=1)
print(sum(len(j["seed"]) for j in jobs), "pictures")
