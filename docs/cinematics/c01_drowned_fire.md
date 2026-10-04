# C01 · The Drowned Fire

**The game's first image.** Priority 1 · Prologue · about 48 s · skippable

## What it does

Creation stands her by a high fire, dry, in the clothes she chose. A cut to
black is the drowning. She wakes by the same fire, burned down to embers, soaked
to the skin, river weed in her hair and caught in the cord of the flask tied to
her wrist, and does not know why. Her bedroll has not been slept in. Her own wet
prints come up out of the dark from the river; none go down to it. She breathes
out into the frost, and nothing shows. Then the frost breaks.

- **She wants** to know where she is, and to be warm. **She hides** nothing,
  because she does not know: she went down to the water at dusk to fill her
  flask, the Warden drowned her, and she rose and walked back to her fire dead.
  **She changes** from lying bewildered to standing armed.
- **Plants**, each paid later, none explained:
  - the prints up from the river: paid at dawn in C04, when new prints come up
    out of the river and this time go on; then by the sealed door's prints going
    the other way; then by Act 2's turn, *what you are*;
  - the breath that makes no smoke: paid in C04, when her first breath at dawn
    smokes; then by Keegan's chapter four;
  - the weed: paid in C02, when the Warden's lamp finds it in her hair, the same
    weed the drowned wear;
  - her hand held at the coals: paid in C04, when the cold reaches her;
  - the flask: paid in C04, when she smells the river in it and drinks anyway.
- **The narrator** says three strange, plain things and nothing they mean.

## Trigger and facts

- Plays when a new journey begins: creation confirmed (`GameFront.NewJourney`, to
  the first frame of the prologue), in place of `Prologue.Begin`'s opening `Say`
  (drop that line when this plays).
- Reads: calling (the arcanist's beat), sex, hair style and colour, background (the
  one prop that gets an insert).
- Sets nothing. The director starts at `Stage.Wake` as now.

## Place, time, light

- **Lowford, the camp:** the fire at (-10.5, 90.5) (zone light 0, `#ff9a48`); the
  title's log at (-8.45, 90.4); her bedroll at (-7.4, 92.2). The river lies 130 m
  north; the ford's three lamps (lights 4, 5, 6, `#8ac8ff`) show through the trees
  as three low points of blue.
- **Time:** past midnight, the night of the Warden. `Atmospheres.Night`.
- **Light:** the fire down to embers: a low orange key from the west, from the
  ground up, flickering slowly, a third of its strength in creation. The moon a
  cold rim from high in the south-east. Shadows graded blue-green; the embers kept
  warm. Frost on the grass in a ring beyond the embers' reach.
- **Mood:** stillness that has gone on too long. Cold. Wrongness nobody names.

## Cast and marks

- **The survivor** lies on her right side on the bare ground between the fire and
  the bedroll at (-8.7, 91.1): head to the north, feet to the south, so that,
  lying on her right side, she faces west into the fire. Wet through: hair dark
  and clumped (wetness 1.0), a ribbon of green river weed in it (bald or cropped:
  on her collar). A water flask on a cord wound twice round her right wrist, full
  and corked, a strand of the same weed caught in the cord.
- **Her prints:** one trail of wet bootprints in the frost from the north, along
  the road's verge from (-6, 72) and across the grass to her body: a long, steady
  stride, no stumble. None lead away.
- **Her things:** the bedroll, unrolled, dry, its blanket still folded on it; her
  pack against the log; her weapon leaning on the log's east end; her
  background's item by the pack (see Variants).
- **The risen:** four, still under the ground: R1 at (-17, 85) (beyond the fire,
  north-west), R2 (-3.5, 82), R3 (-14, 98), R4 (-2, 97). R1 breaks the frost in
  shot 9; all four rise in shot 11 (`SpawnStyle.Rise`), held there until play.

## Shot list

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 0 | (creation's last frame) | | | Creation's portrait: her standing by the fire, dry, the fire high. On confirm, the UI goes; hold the picture 0.5 s. | 0.5 |
| 1 | Black | | | A hard cut to black. Sound only, from silence: water closing over something, very close and then far; then nothing; then one drop on stone, and another. The river, far off. An owl, once. | 3.5 |
| 2 | ECU | 100 | Static, 0.25 m off a flat stone by the fire, level | A strand of her wet hair across the stone; a bead of water swells at its tip and drops. The embers glow out of focus behind. Focus 0.3 m. (Short hair: the drip runs down her brow from the fringe and falls from her jaw.) | 3.0 |
| 3 | CU | 85 | Push in 0.1 m over the shot | Her face on its side on the frozen ground, eyes shut, weed in her hair. Half the face lit by the embers, half moon-blue. At 2.0 s her eyes open: no gasp, no start. She looks at the fire. | 4.0 |
| 4 | MS | 35 | Static, low (0.4 m), on the fire's far (west) side, looking east through the embers at her | She pushes up onto her elbow. Water runs off her sleeve onto the ground. Her hair hangs. | 3.5 |
| 5 | INSERT | 65 | Static | Her hand comes into frame and opens toward the coals, palm down, and keeps going, closer than anyone could bear to hold a hand to coals. It stays there. (We do not see her face. We see that the hand does not pull back.) | 3.5 |
| 6 | MCU | 50 | Static, from her right at shoulder height | She sits up, legs drawn round to one side, and looks down at herself; at the cord on her wrist and the full flask; then past it, at the bedroll, dry, its blanket folded. Line N1. She puts a hand inside her coat and takes out a folded letter, wet through, and opens it: the ink has run to blue water, and no word is left. She folds it and puts it back. (The letter that brought her home: her mother was failing. The water took it, as Vonnra will say.) A 1.5 s look at her background's item by the pack (see Variants), in the shot's last third. | 7.0 |
| 7 | OTS | 28 | From behind her left shoulder, low; a slow tilt and pan north along the trail, 25° over the shot | The prints in the frost, dark and wet, coming out of the night along the road to where she lay. The camera follows them back into the dark they came from. Far off between the trunks, three points of cold blue light, low, by water. Line N2. | 5.5 |
| 8 | CU | 85 | Static, frontal, a little below her eyes, against the black of the trees | She looks from the trail to her own boots, soaked black, and breathes out: a long breath, close and audible, the kind you let go when you are tired and cold. Against the dark, in air cold enough for frost, nothing shows. Hold one beat after. | 4.0 |
| 9 | LS | 24 | Static, low (0.3 m), from the south-east at (-2.5, 97.5), looking north-west at the camp | The embers, the log, the dry bedroll, her things, her weapon on the log; her, small, by the embers. Background left, beyond the firelight, the frost goes dark in a patch, as if water were coming up through the ground, and a head comes up through it, hair streaming, the way a swimmer comes up (R1). They rise the way she did. She has not seen it. Line N3. | 5.0 |
| 10 | MCU | 50 | Static | Her head turns sharply toward the sound. She is on her feet in one movement. | 2.5 |
| 11 | MS | 35 | Static, side-on | She takes her weapon from the log (one movement for every calling; the arcanist's differs: see Calling). Around her, on three sides, the frost breaks. | 3.5 |
| 12 | MLS to high | 35 to play | Crane up and round behind her into the game's follow camera | From in front of her, the camera rises and swings behind and above her as R1 tears free and R2, R3, R4 come up on three sides. The frame opens to the game's height. Bars out over the last 0.8 s; HUD and the "Move" hint come up. Control. | 3.5 |

Total: 48.0 s.

## Performance

**The survivor** (shapes 0 to 1; gaze as `HerFaceLife.Look`):
- *Shot 3.* Lids held shut (`blink_l`, `blink_r` 1.0) to 2.0 s, open over 0.15 s;
  `eyes_wide` 0.25 as they open; `Wander` 0.05. Gaze: the fire, a little down
  (0.1, 0.3).
- *Shot 4.* Nothing on the face. The hair and the water do it.
- *Shot 6.* `brows_sad` 0.3, `mouth_open` 0.08. Gaze down to the flask (0, 0.8),
  across to the bedroll (−0.5, 0.5), a slow blink. Not panic: someone trying to
  remember, who cannot tell that she cannot.
- *Shot 8.* Gaze from the trail to her boots (0, 0.9). The exhale: `mouth_open`
  0.2 over 1.2 s, lips parted, back to 0.05. `brows_sad` rises to 0.4 and eases to
  0.2: something almost arrives, and doesn't.
- *Shot 10.* Gaze snaps to R1 (a saccade). `eyes_wide` 0.6, `brows_sad` 0,
  `brows_angry` 0.2. She rises without using her hands.
- *Shot 11 on.* `brows_angry` 0.35, `mouth_open` 0.12. Gaze on the nearest risen.

## Lines

All the narrator's (*casting:* 50s, neutral RP, low and close, a winter's tale by
the fire). Conversation `cin_drowned_fire`.

| VO id | Shot | Line | Note |
|---|---|---|---|
| `cin_drowned_fire.bedroll` | 6 | *Your bedroll has not been slept in.* | The game's first words. Plain as an inventory. |
| `cin_drowned_fire.prints` | 7 | *Prints in the frost, your own. They come up from the river. None go down to it.* | Three statements, a small pause before the last. The voice is never ominous; the picture is enough. |
| `cin_drowned_fire.lamp` | 8a | *Far up the road one lamp burns high in the dark, and a voice comes down to you over the frost, close as if she stood at your shoulder.* | Plain. The lamp is the toll tower's, and the narrator does not say so. |
| `cin_drowned_fire.call` | 8b | *Come up, traveller. ...No charge, this once.* | Speaker `far_voice`, subtitled only "A voice up the road". Vonnra, unnamed: far off and thinned by the cold, unhurried, never raised. A toll-keeper waving a traveller through, kindly; the pause before "No charge" is her deciding to. The fortune (C09) opens on the same words. (Bible, "Who tells it".) |
| `cin_drowned_fire.frost` | 9 | *Past the firelight, the frost is breaking.* | As the line of frost cracks, not before. |

## Calling (shot 11)

- **Warden, reaver, stalker:** one movement for all: she takes her weapon from the
  log by the haft or grip and comes round with it ready (`PickUp_Table`, which is
  the log's height, into the calling's idle). The weapon is whichever she chose.
- **Arcanist:** her staff or focus is on the log, but she does not reach for it
  first. She cups her hands. Nothing. Then one spark crawls across her knuckles,
  catches, and her palms fill with light in her weapon's school (Seeking Motes:
  violet-white; Cinderfall: ember red; Rimeshard: frost-white). `smile` 0.15 for
  half a second, surprise very near pleasure, gone (`smile` 0, `brows_angry` 0.3).
  Clip: `Spell_Simple_Enter`.

## Variants

- **Hair.** Long, braid, ponytail: shot 2 is the strand on the stone. Bob and
  pixie: the fringe dripping. A male survivor with short hair or none plays the
  pixie version; a beard holds water at the chin; the weed is on his collar.
- **The background's item** (shot 6's look; one insert-length glimpse, never
  mentioned):
  - *Hunter:* a hare she snared at dusk, hung by its hind legs from the log, not
    yet skinned.
  - *Scholar:* the Cracked Lens lying open on a closed book, its crack catching
    the ember-light.
  - *Outcast:* the red kerchief knotted round the pack's strap.
  - *Devout:* the Pilgrim's Ember-Lantern on the ground, the only light in the shot
    burning steady. In shot 12 the risen nearest it (R3) turns its face from it as
    it rises.
- **Pronouns.** None spoken. Nothing else changes for a male survivor.

## Sound

- **Music.** None until shot 9. At the frost's crack a single low drone (the
  `Night` mood's root, a bowed, breathy pad) rises from nothing over 4 s; one hit
  (a deep drum under a scrape of metal) as she takes her weapon; `Combat` takes
  over from the drone without a gap at the hand-back.
- **Effects.** The water closing (shot 1: close, muffled, a bubble, then the river
  far off and level); the drip on stone (close, a little pitch drift each drop);
  the embers ticking as they cool; the river distant and wide; one owl and no
  others; frost crunching under her elbow; water running off cloth; the flask's
  cord creaking. Her breath in shot 8, close-miked, the loudest thing in the scene
  so far. The crack: frost splitting in a line, a low thump felt more than heard,
  roots tearing. A risen rasps as it comes up: breath with no breath in it.
- **Mix.** Shots 2 to 8 close and quiet: embers left, river right and far.

## VFX

- Embers drifting up, sparse.
- Water: a bead forming and falling; drips from her hair and sleeve as she moves.
- Frost on the grass beyond the embers' reach; cracking in a line where R1 rises.
- **No breath-smoke on her** (shot 8 is built to show it: an exhale against a dark
  background in frost). Nobody else here breathes.
- The ford's lamps, far off, steady blue, haloed in the river mist.
- Ground bursts at the four rise points.
- The arcanist's ignition.

## In, out, skip, subtitles

- **In.** A match: creation's last frame (her, dry, the high fire) holds 0.5 s and
  cuts hard to black (the drowning), then wakes her soaked by the same fire burned
  down, 0.4 m from where she stood. The title music cuts with the picture.
- **Out.** Shot 12 blends into the follow camera over its last 2 s; the world, held
  at `WorldRate` 0 with the risen mid-rise since shot 11, runs from the blend's end.
  `Stage.Wake` begins as now.
- **Skip.** From 1.5 s (always, on a later journey). Lands on her standing at
  (-7.5, 87.5) facing north with her weapon, the risen half out of the ground.
- **Subtitles.** The narrator's three lines in italics, no name.

## What it needs

Lying on the side to sitting (missing); sitting on the ground (the game maps it to
a crouch); wetness on hair, skin and cloth, drying over the first minutes of play;
a weed strand on the head (and the collar); wet-footprint decals in the frost;
frost on grass that can crack in a line; the breath system (none on her); a
bedroll prop with a folded blanket; the hare, the lens on a book, the kerchief on
a strap, the lantern; water-closing and drip sounds. The title screen's hooded
stranger by this fire is the survivor at dusk, before the water, and must read as
any survivor: hood up, back to the camera, no calling's silhouette. (Today it is a
female stalker model, which reads as one survivor in particular.)
