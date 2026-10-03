# C04 · First Light

**The ember goes out; chapter one opens.** Priority 1 · Prologue to Act 1 ·
part A about 40 s, part B about 26 s · skippable

## What it does

**Part A, the north bank.** She comes up out of the river at first light, across
the ford she died trying to cross, and her wet prints come up out of the water
again, and this time go on. The sun clears the trees and the ember runs out of
her, down her body into the ground the way the river ran off her when she woke.
And then, for the first time all night, her breath smokes in the cold: she
breathes again just to see it. The cold reaches her. She is thirsty, and the
flask on her wrist smells of the river, and she drinks it anyway. She reaches for
her mother's face, and it is not quite where she left it.

**Part B, the Waystation.** The gate, the chimneys, someone baking. People stop
and look. A guard says to his mate what guards say. High in the toll tower a lamp
is still burning in a window in full sun. Rook, at her door, looks up at the tower
when the survivor comes in, and back.

- **She wants** warmth, water, a bed: the ordinary. **She gets** them, and loses
  something she will not miss until later (the face). **She changes** from a thing
  that burned to a woman who is cold.
- **Vonnra wants** to see the survivor arrive, and kept her lamp lit past dawn for
  it; **she hides** everything; the lamp burning in daylight is the only sign.
- **Rook** is paid to watch the road and tell (`rook.ford`); her glance at the
  tower is the opening's one link between them.
- **Plants:** the face going (Chid's "It always takes the names first. Then the
  faces."; Act 2's cost of the ember); the tower's lamp (Vonnra's night hub line,
  "looking south, toward the ford"; the fortune); "Dawn arrivals. We don't get many
  that live." (Act 2's turn).
- **Pays:** C01's prints (now they go on), the missing breath (it smokes now), the
  hand at the coals (the cold reaches her), the flask (she drinks the river), the
  wet waking (the ember runs off her the same way); C02's "None cross after dark"
  (it is not dark).

## Trigger and facts

- **Part A** replaces `Stage.Dawn`'s staging. It plays where she is: when she
  crosses to the north bank (`p.Z < -50`) after C03, or if she is still on the south
  bank 25 s after C03 hands back (looting the ford); shot A1 has a variant for each.
  `Douse` happens inside it (shot A4). The `Douse` announcement ("The ember goes out"
  / "It burns only in the dark") and the day tip come after the bars go out.
- **Part B** replaces the Waystation's first-arrival `Say` in `Waystation.Begin`
  (`waystation.visited` unset), after the travel fade.
- Reads: calling (shot A4).
- Sets: what `Douse`, `Finish` and the first arrival set now (`prologue.done`,
  `waystation.visited`).

## Place, time, light

- **Part A.** Lowford: the ford's north edge at about (1, -50), the road rising
  north through birch to the gate (0, -112). The `Night` to `Dawn` blend runs
  across the part (over 10 s from A2). The sun rises in the east (+x): a white-gold
  rim behind the birches, light raking across the road from the right. Frost on
  everything; it smokes where the sun touches it. Mood: the first quiet of the game.
- **Part B.** The Waystation: the south gate (0, 38), the road north to the square
  (0, 0); the toll tower to the east at (33, -8) with an upper window on its south
  face. Early morning (`Dawn` going to `Day`): chimney smoke straight up in still air,
  low sun from the east gilding the east faces, long blue shadows across the road.
  Mood: a town that has seen too many dawn arrivals to cheer one.

## Cast and marks

**Part A.** The survivor wades out of the ford at (1, -49) and walks to (0.5, -58).

**Part B.**
- **The survivor** walks in through the south gate and up the road to the square's
  south edge at (0, 7), facing north.
- **Guards:** the two at the south gate (-4.6, 34.6) and (4.6, 34.6), facing south;
  G1, the west one, speaks.
- **Townsfolk** placed ahead of her (north) so that she walks toward them: a man
  carrying a ladder across the road at (3, 18) walking west; a woman at the well
  (-1.75, 0.9) with a bucket; a child at (2, 10). The morning's other walkers as
  `Folk` places them.
- **Mother Rook** at the inn door (-11.3, 11), arms folded.
- **The toll tower's window:** on its sill, a lamp, lit.

## Shot list

### Part A: the north bank

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| A1 | MS | 35 | Static, low (0.3 m) on the north bank's edge, looking south at the water | *(Crossing:)* her boots come up out of the river into frame and onto the frosted bank; she walks on past camera, and behind her, in the frost, wet prints come up out of the water and go on north. *(Still south, looting:)* a static MS of her standing in the ford's shallows, turning toward the light that is starting in the east. | 4.0 |
| A2 | ELS | 40 | Static, from the west, across the road and up into the birches | The tops of the birches go gold one by one from the east as the sun clears the ridge; the light comes down the trunks like water filling a glass. | 5.0 |
| A3 | MS | 50 | Static, side-on from the east, the sun behind the camera | The light reaches her face and shoulders. She shuts her eyes against it. | 3.5 |
| A4 | MLS | 35 | A slow tilt from her chest to her feet (2 s), then hold | The ember goes out of her: red light runs down her body like water, off her shoulders, out of her hands, down her legs, and soaks into the frosted road at her feet and is gone. Her weapon's night-glow cools with it (see Calling). Line N5. | 5.0 |
| A5 | CU | 85 | Static, frontal, low sun from frame right, the birches' shade behind her | She breathes out, and her breath smokes in the cold: a long white plume in the sunlight. She sees it. She breathes again, to see it again. Then the cold reaches her: her shoulders lift, she shivers once, hard. | 5.5 |
| A6 | MCU | 50 | Static | She lifts the flask on its cord, pulls the cork with her teeth, and stops: smells it. The river. She drinks anyway, long, like someone who has not drunk all night; water on her chin. She lowers it. | 5.0 |
| A7 | CU | 85 | Static, frontal, very slow push in (0.05 m) | She is still. Her eyes go inward, searching. Line N6. Then nothing: hold 3 s of silence after the line. | 6.5 |
| A8 | LS | 28 | Static, low behind her on the road, looking north up the hill | She walks away from camera up the road into the light; at the top of the hill the gate stands open. Bars out over the last 0.8 s; then the `Douse` announcement and the day tip. | 5.5 |

Part A total: 40.0 s.

### Part B: the Waystation

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| B1 | ELS | 24 | Crane down (5 m to 1.8 m) just inside the south gate, looking north up the road | The town in the morning: roofs, a dozen chimneys smoking straight up, the square, the well; to the right the toll tower with the sun on it, and in its upper window, very small, a lamp still burning, pale in the daylight. She walks in under the camera and on up the road. Line N7. Title over the shot's end: **CHAPTER ONE** / *The Waystation*. | 7.0 |
| B2 | MS | 50 | Static, behind the west guard, his shoulder in frame | G1 watches her go. Line GD1, to the other guard, not to her. | 3.5 |
| B3 | MLS | 35 | Tracking behind her at her pace, over her shoulder, looking north | Ahead of her, as she comes, people stop what they are doing and look: the man with the ladder stops in the road and turns so the ladder swings; beyond him the woman at the well holds the bucket halfway; the child runs. Nobody speaks. | 5.0 |
| B4 | MS | 50 | Static, beside the inn door, Rook in the foreground right, soft at first | Focus pulls from Rook's folded arms to the survivor stopping at the square's edge, looking round at the faces. Rook looks at her; then up, east, at the toll tower's window, where the lamp has just gone out, a thread of smoke going up from it; and back at the survivor. She unfolds her arms. | 6.0 |
| B5 | MLS to play | 35 to play | Rise and swing into the follow camera | The square, the survivor in it, Rook at her door. Bars out; Rook's `!` comes up. Control. (No zone title: the chapter's card was it.) | 3.0 |

Part B total: 24.5 s (plus the travel fade before it).

## Performance

**The survivor**
- *A1.* Wading: the water to her shins; no hurry.
- *A3.* Eyes close slowly (`blink` held over 0.4 s), `brows_sad` 0.1: the face after
  a long night, not a triumph.
- *A4.* As the ember drains: `mouth_open` 0.15, `brows_up` 0.3, gaze following it
  down her body (0, 0.9). It does not hurt. It is like being set down.
- *A5.* The breath: `mouth_open` 0.25 on the exhale, then `smile` 0.1 as she sees it
  (she does not know why it pleases her; neither should the player yet). The second
  breath on purpose. The shiver: shoulders up 4 cm, a fast double tremor, `squint`
  0.2, `frown` 0.2.
- *A6.* On the smell: `nose_wrinkle` 0.3, a half-second's stillness. She drinks with
  her eyes shut.
- *A7.* Eyes open, unfocused, middle distance (0, 0); `brows_sad` rises to 0.45 and
  stays; then her eyes move left and a little up (−0.3, −0.2), the look of
  remembering; they find nothing and come back. Do not play grief. Play someone who
  has mislaid a thing she uses every day.
- *B3.* Gaze moves from face to face (`Wander` 0.2): the ladder, the well, the child.
  `brows_up` 0.15. Too tired to be wary.
- *B4.* She notices Rook last, and holds there.

**Rook.** In her doorway watching the road, as she does every dawn (she is paid to).
Her look up at the tower is quick, a check, the way you glance at a clock. She
unfolds her arms the way you put down a tool when work arrives, and waits for the
survivor to come to her.

**G1.** A watchman of forty with a cold, leaning on his spear. He says GD1 the way
men say what they always say, and watches her too long after.

## Calling (shot A4)

- *Warden:* the ember-red that ran along her shield's rim at night cools to plain
  iron, ticking.
- *Reaver:* the red heat along her cleaver's edge cools to grey steel, ticking.
- *Arcanist:* the light in her palms goes out like a pinched wick; a thread of smoke
  rises from each hand. She closes her fingers on nothing.
- *Stalker:* the ember-red at her arrowheads (or along her knives) dies to dull iron.

## Lines

Conversation `cin_first_light`.

| VO id | Shot | Speaker | Line | Note |
|---|---|---|---|---|
| `cin_first_light.back` | A4 | `narrator` | *The sun clears the trees, and the ember goes back into the ground.* | As weather. "Back" is the only weighted word, and only a little. |
| `cin_first_light.face` | A7 | `narrator` | *You try to call up your mother's face, and find it is not quite where you left it.* | The prologue's own line. The most important line in the opening. No weight on it at all. Then silence. |
| `cin_first_light.baking` | B1 | `narrator` | *Somewhere up the street, someone is baking.* | Warmer than any line of the night. The camera can't smell; the narrator can. |
| `cin_first_light.dawn` | B2 | `guard` | Dawn arrivals. We don't get many that live. | Flat, to his mate, a thing said every week. (The guard bark in `npcs.json` says the same.) |

The mechanics the prologue's dawn line used to explain ("What you carry, and what
you have learned, are still yours...") are said by the interface: the `Douse`
announcement and the day tip, after the bars go out.

## Sound

- **Music.** Part A: the `Night` flute alone, slow, carried from C03, until A3; at
  the draining a soft descending figure on the lamp motif's bell, inverted, and the
  pad thinning to nothing; A5 to A7 in silence but for breath and the birds
  starting; on A8 the first gentle figure of `Explore`, a pluck, as she walks up the
  hill. Part B: `Town` mood on B1 at half its usual intensity, out under B4 (the
  lamp's smoke in silence), back as the bars go out.
- **Effects.** Part A: wading (water to the shins, then frost underfoot); the river
  behind her fading; the first birds (one, then three, then many); frost ticking as
  it melts; the ember draining (a soft rush like poured sand, falling in pitch, a
  hiss at her feet); her breath, in and out, close; the shiver (teeth, cloth); the
  cork; a sniff; swallowing. Part B: the gate's hinges; the town (a cart, a dog, a
  door); Brannoc's hammer from the smithy, steady (the hammer is the town's clock);
  the ladder's creak as the man turns; the bucket's chain stopping halfway; the
  child's feet.

## VFX

- The sunrise: god-rays through the birches; frost steaming where light falls.
- Wet prints from the water's edge going north (A1).
- The ember draining (A4): red light running down her like water into the road; the
  weapon's glow cooling.
- Breath-smoke (A5 on, and by day in the cold from now on; never by night while the
  ember burns).
- Water on her chin.
- Chimney smoke; the lamp in the tower window, pale in daylight, then out with a
  thread of smoke.

## In, out, skip, subtitles

- **Part A in.** Captured where she is (crossing, or 25 s after C03 on the south
  bank); bars in. **Out.** Bars out as she walks up the hill; the announcement and
  the tip; control for the walk to the gate. `Finish` and the travel as now.
- **Part B in.** Under the travel fade, on first arrival. **Out.** Into play at the
  square's edge; Rook's mark up.
- **Skip.** A lands on her on the north bank, ember out. B lands on her at (0, 7).
- **Subtitles.** As written; the guard under "Watchman".

## What it needs

The ember-draining effect. Breath-smoke (and its absence at night). An additive
shiver. A flask on a cord: uncorking with the teeth, smelling, drinking (`Consume`
is close). Wet prints that start at a water's edge. A lamp on the toll tower's
window sill that can be put out (from inside: the flame and its smoke only). Folk who
can be told to stop and turn. The `Night` to `Dawn` blend on the cinematic's clock.
