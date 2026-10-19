"""Round 12 (style_r12.json): the r2 content in hand H3. r11 showed a flat block-in
used as the init paints out flat (a vector or animation background), so the block-ins
now only steer the layout: text-to-image with their soft edges as the control (the
model lays its own paint), P4 from r1's edges edited (smoke and the dead man's head
cleared, the Watchman leaned in, the spear drawn, pulled back 15%, the ground's
edges halved). P7 two ways: the paint-over repainted at 0.5, or its edges as control.
Then the shared repaint (unify) over the picks makes the hand one."""
import json
import os

FRAME = "A full-bleed illustration that fills the entire frame edge to edge, with no border, no margin and no paper edge. "
HAND = ("A restrained dark tonal painting for a book plate, in loose oil paint over a bold brush-ink drawing on a warm brown "
        "toned ground: broad simple masses of shadow, thinly painted so the warm ground glows through, and a few deliberate "
        "thick opaque strokes only where the light falls; heavy dark ink contours on the figures; painterly soft edges, almost "
        "no texture in the shadows; a limited palette of umber, slate and indigo with the story's lights; quiet, grim and "
        "serious, realistic proportions. ")
CONTENT = {
    "p1": ("Night, two thousand years ago. From the near rim of a great raw cut dug into a hillside we look down across it. "
           "At the left, close to us, two ancient soldiers stand on our rim with their backs to us, dark shapes in shadow, their "
           "wool cloaks a dull dark rust-red, dull bronze helmets with crests and cheek guards; one holds a small torch low in "
           "front of him. Across the cut, a long column of tiny figures carrying torches winds down the far wall in an S-shaped "
           "path to the bottom of the picture; the torches are the brightest things in the picture. The far wall is a few big "
           "flat planes of dark rock. Above it the dark hillside rises to a crest under a strip of night sky. Torch smoke "
           "drifts. The orange torchlight is the only strong color; everything else is night."),
    "p4": ("Night, hard frost on a field beside a pale road, small ember-gold glints scattered in the frozen soil, a dark body "
           "lying in the frost behind. A dead villager stands upright, slack, arms hanging, head tilted, in a torn linen shirt; "
           "his gray face is blank, his matted hair flat, the mouth hanging open and the empty eye sockets glowing with soft "
           "golden light from inside, his skin lit from within like paper over a lamp. To the right an old watchman with a "
           "gray beard, in a slate blue-gray hooded cloak over a plain wool tunic, a matte round wooden shield with a dull iron "
           "boss on his arm, leans in with his weight forward and both hands on a plain dark spear whose head is buried in the "
           "dead man's chest; golden light bursts out around the shaft and pours down onto the frost as small glowing stones. "
           "A pale white plume of breath leaves the watchman's mouth. The golden light is the only strong color; the rest is "
           "cold night, frost and slate."),
    "p7": ("The Low Ford at night in winter: a shallow river crossing between snowy banks, thin gray ice along both edges, a "
           "trodden track coming down through the snow to a line of flat stepping stones across the shallows. Three new black "
           "iron cage lanterns on thin black iron posts stand by the water, each burning with a plain cold pale blue flame and "
           "pooling blue light on the snow at its foot. Over the stepping stones, in the middle of the river, a fourth blue "
           "light hangs in the air a little above the water in a wide cold glare, nothing visible holding it, its light "
           "trembling on the water below. Nobody is there. The cold blue is the only strong color; the rest is deep night."),
    "p9": ("Dusk, a deep blue sky over a thin dull rose band above the far hills. A small camp beside a rutted dirt track: a "
           "campfire burning high, a bedroll with its blanket folded on top, a pack. A lone traveler sits on a log by the fire "
           "with their back to us, the whole body wrapped from the hood to the ground in one plain dark wool hooded cloak, a "
           "simple cone shape, the head bowed over a folded letter held to the firelight; a small flask hangs on a cord from "
           "one wrist. Far up the track on a low rise, the waystation: a small cluster of dark roofs around a square stone "
           "tower, its windows glowing warm orange, one lantern high on the tower. Low by the water among the bare trees on "
           "the right, three small distant lamps burn cold blue, far apart from each other, each with a short blue reflection "
           "in the water below it. The fire's orange is the warm color; the rest is blue dusk."),
}
P = "tools/storybook/out/style_r12/prep/"
S4 = [11, 23, 37, 41]
jobs = [
    {"name": "p1_t", "prompt": FRAME + HAND + CONTENT["p1"], "seed": S4, "control": P + "p1b_edge.png", "strength": 0.6, "end": 0.7},
    {"name": "p9_t", "prompt": FRAME + HAND + CONTENT["p9"], "seed": S4, "control": P + "p9b_edge.png", "strength": 0.6, "end": 0.7},
    {"name": "p4_t", "prompt": FRAME + HAND + CONTENT["p4"], "seed": S4, "control": "tools/storybook/layouts/p4_edge_r2.png",
     "strength": 0.6, "end": 0.7},
    {"name": "p7_r", "prompt": FRAME + HAND + CONTENT["p7"], "seed": [11, 23], "init": P + "p7b_init.png", "denoise": 0.5,
     "control": P + "p7b_edge.png", "strength": 0.5, "end": 0.6},
    {"name": "p7_t", "prompt": FRAME + HAND + CONTENT["p7"], "seed": [11, 23], "control": P + "p7b_edge.png", "strength": 0.6,
     "end": 0.7},
]
here = os.path.dirname(os.path.abspath(__file__))
json.dump({"defaults": {"w": 1792, "h": 1024, "steps": 9}, "jobs": jobs},
          open(os.path.join(here, "jobs", "style_r12.json"), "w"), indent=1)
print(sum(len(j["seed"]) for j in jobs), "pictures")
