# C08 · The Iron Marker

**Nell is buried.** Priority 2 · Act 1 · about 70 s · conditional (only if she
told Brannoc the truth) · skippable

## What it does

The morning after she told him, the town walks to the Quiet Garden behind the
shrine without being asked. Chid sings the Order's burial hymn, badly. Brannoc
sets an iron marker at the head of the grave and drives it in with three
strokes of his hammer: the last hammer the town will hear from him for a while.
Rook takes her mother's lamp down from over the inn door, the Order's lamp, and
sets it burning at the grave's foot in broad daylight. On the lane beyond the
hedge, alone, a woman in violet watches, and goes before the end.

- **Brannoc wants** to do this right, with his hands. **He hides** nothing now.
  **He changes** if he knows she got up: at the hymn's last line ("it will wake
  you where you slept") his hand stops on the marker.
- **Rook wants** to give something and not be seen giving it. She never cries in
  front of anyone; she sets the lamp down and goes to the back and turns away.
- **Chid wants** to sing her down properly, and he cannot sing. He sings anyway,
  and his voice catches on the hymn's turn.
- **Vonnra** (seen only by the camera) **wants** to see what her carters' night
  crossings cost, and not to be seen seeing it. She is the only person there who
  does not come into the garden.
- **The survivor** stands at the hedge: the person who put the child down, at
  the funeral.
- **Plants:** the hymn ("Go down, go down, the morning's under... it will wake you
  where you slept": Act 3, the Order's morning was the Morrow under them; and the
  dead do wake); Vonnra at the funeral (Act 3, her truth); Brannoc's smith's mark
  on the marker (the same mark as the Warden's lamp-iron); Rook's lamp (the Order's,
  which her mother carried up from the chapel: Act 3, Chid's truth); Harlan's hand
  on Jory's shoulder (Act 2, Harlan exposed: he sent a boy down a road too).
- **Pays:** C07 (the truth); the burial report; the lamp over the Last Lamp's door
  (`rook.lamp`); Chid "can't sing" (`folk.json`).

## Trigger and facts

- The morning `nell.buried` becomes true (rule `nell.burial`, the morning after
  she told Brannoc the truth), the first time she steps out of the Last Lamp.
  (The rule's report now says they are burying her "this morning", so she can go.)
- Reads: `nell.told` (`risen` or `gone`); `caravan.survivors` (Harlan and Jory
  there if `rescued`); `met` for Maeca, Wenna, Tam, Holloway, Sella (who is there);
  `shrine.lit` (the shrine's lamp lit or not in shot 2); `brannoc.saw_iron` or the
  survivor having carried the Warden's lamp-iron (nothing changes; the insert
  in shot 6 simply means more to her).
- Sets nothing new (`nell.buried` is set by the rule).

## Place, time, light

- **The Waystation**: the Last Lamp's door (-11.3, 11); the lane past the shrine
  (-26, -25) to the gap in the hedge (about (-34, -32)); the Quiet Garden behind
  it (-38, -36): nettles, an old yew, the first Watch-captain's stone (Ashe's), and
  beside it a fresh grave cut in the turf. Beyond the far hedge, a lane.
- **Time:** early morning, a still day, low sun through the yew.
- **Light:** long shafts through the yew's branches; dew on the nettles; the
  grave's earth dark and wet. Rook's lamp, burning in daylight, small and gold.
- **Mood:** a town being decent. Grief kept to its size.

## Cast and marks

At the grave (Ashe's stone at (-38.5, -37), the fresh grave east of it at
(-36.8, -37), its head to the north):
- **Chid** at the grave's head, (-36.8, -38.6), facing south, hands folded.
- **Brannoc** kneeling at the head beside Chid, with the iron marker and his
  hammer.
- **Rook** in the ring's west side, the inn's lamp in her hands (taken down from
  its hook over the inn door).
- **Holloway** and two watchmen, east side, helmets under their arms.
- **Wenna**, with a bunch of rosemary; **Tam** beside her (if met), holding her
  skirt.
- **Harlan and Jory** (if the survivors were rescued), south-east, Harlan's hand on
  Jory's shoulder.
- **Maeca** (if met, and not cold to the survivor): at the back by the yew,
  barefoot, apart.
- **Sella** (if met): at the hedge gap, not coming in. Her hair is the same red as
  the child's was.
- **Townsfolk**: a dozen in their good clothes, in a loose ring.
- **The survivor** stops at the hedge gap (-34, -32), then comes three paces in and
  stands at the back, south of the ring.
- **Vonnra**: outside the far (west) hedge on the lane at (-46, -40), standing
  still, facing the grave across the hedge; violet.

## Shot list

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 1 | MS | 35 | Static, outside the inn, low | She steps out of the Last Lamp into the morning. Over the door, the old lamp's hook is empty. | 3.0 |
| 2 | LS | 28 | Static, across the square | The square nearly empty. People in their good clothes walking, all the one way, north-west past the shrine, quietly. She follows. | 4.0 |
| 3 | MLS | 35 | Tracking behind her along the lane to the hedge gap | The hedge; the gap; through it, the Quiet Garden in the yew's shade, the town standing in a ring round a fresh grave beside the old captain's stone. | 5.0 |
| 4 | LS | 24 | Static, wide, from inside the garden by Ashe's stone | The whole ring. Chid begins to sing (H1). Brannoc kneels at the head with the marker. | 7.0 |
| 5 | MCU | 50 | Static, on Chid | He sings with his eyes shut, off the note, with his whole heart. His voice catches on "turning". | 6.0 |
| 6 | INSERT | 85 | Static, low, at the grave's head | The iron marker: a plate of black iron on a stake. Punched into it with a nail: **NELL**. Below, small: a hammer struck through a B. | 3.0 |
| 7 | MS | 50 | Static, side-on, low | Brannoc sets the marker's point in the turf and drives it with his hammer: one stroke, two, three. The anvil's ring is not there; it is iron into earth, dull. The third stroke is the last. | 6.0 |
| 8 | MS | 50 | Static | Rook comes forward with the lamp, lit, and sets it at the grave's foot. She steps back, all the way back, to the edge of the ring, and turns her face to the yew. | 6.0 |
| 9 | 2S | 85 | Static, across the ring, long | *(If rescued:)* Harlan with his hand on Jory's shoulder. On H2's "wake you", Harlan takes his hand away and looks at it. *(Otherwise:)* Wenna with the rosemary, and Tam holding her skirt. | 4.0 |
| 10 | LS | 135 | Static, from inside the garden across the far hedge, compressed | Beyond the hedge on the lane, a woman in violet, standing very still, watching the grave over the hedge. As the second verse begins she turns and walks away up the lane, unhurried, and is gone. Nobody in the garden sees her. | 5.0 |
| 11 | CU | 85 | Static, on Brannoc's hand on the marker | Chid sings the last line of the second verse: "and it will wake you where you slept." *(If `nell.told` is `risen`:)* Brannoc's hand, which has been resting on the marker, stops, and grips it. *(If `gone`:)* his hand rests there. | 4.0 |
| 12 | MCU | 50 | Static, on the survivor at the back | The hymn is over. Silence. Brannoc, across the grave, lifts his head and looks at her. Just looks. She holds it. | 5.0 |
| 13 | LS | 24 | Static, as 4 | People go, in twos and threes, back through the hedge. Brannoc stays kneeling. The lamp burns in the daylight at the grave's foot, beside the old captain's stone. Bars out. | 6.0 |

Total: about 68 s.

## Lines

Conversation `cin_iron_marker`, speaker `chid`. The hymn is the Order of the
Morning Light's burial hymn, called "Go Down". **Sung**, badly and with love.

| VO id | Shot | Line |
|---|---|---|
| `cin_iron_marker.verse1` | 4 to 5 | *Go down, go down, the morning's under, / down where the lamps are kept; / and when the day has done its turning, / it will wake you where you slept.* |
| `cin_iron_marker.verse2` | 9 to 11 | *Go down, go down, and do not wonder, / down where the light is kept; / the dark is only day not happened, / and it will wake you where you slept.* |

*Casting:* Chid (sounds 30s, Irish-tinged; his voice catches on joy, and here it
catches on the opposite). The tune is plain, old, four lines in a minor key that
lifts on the last line; he sings it a little flat, slowing on the turn of each
verse, and cracks on "turning" in verse one. Local TTS will not sing it well:
record it sung (a human voice, or a singing synthesis), or have Chid half-sing,
half-say it, which is also true to him.

The hymn says, to anyone at a funeral, that the dead are going down to the
morning and will wake. It means, in Act 3, that the Order's morning was the
thing under the ground, and that the dead it touches do wake. Nell did. Nobody in
the garden knows that but the survivor and, if she told him, Brannoc.

## Performance

**Brannoc.** He kneels as a smith kneels at work, not in prayer. Three strokes,
measured, each the same. In shot 12 the look he gives her has no thanks in it
and no blame: she was there; nobody else here was. (No face rig: a slow lift of
the head, the hearth-less daylight on him, held.)

**Rook.** She carries the lamp in both hands the way you carry a full bowl. She
sets it down without kneeling (bends from the waist, sharp, the way she does
everything), steps back, keeps stepping back, and turns away from everyone.

**Chid.** Eyes shut; the whole of him in it; the crack on "turning" makes him
smile, embarrassed, mid-line, and go on.

**Harlan.** Holds Jory's shoulder through verse one as if Jory might go
somewhere. On "wake you", he takes the hand away and looks at it.

**Vonnra.** Stillness. Hands folded in her sleeves. When she turns away it is not
haste; she has seen what she came to see.

**The survivor.**
- *Shot 3.* `brows_sad` 0.2; she comes in quietly.
- *Shot 7.* At each of the three strokes, a small `blink`.
- *Shot 12.* She meets Brannoc's look. `brows_sad` 0.45, `frown` 0.1, jaw set,
  `mouth_open` 0; no tears. She does not look away first.

## Sound

- **Music.** None but the hymn, unaccompanied. After it, the garden's silence:
  birds, the yew, a distant cart.
- **Effects.** The town's morning hushed; footsteps on the lane; the hedge;
  nettles brushing; the marker going into turf (three dull strokes: iron into
  earth, not iron on iron, and the absence of the anvil's ring is the point);
  Rook's lamp set down on stone; the lamp's small flame; people leaving.

## VFX

- Sun shafts through the yew; dew; breath-smoke in the cold morning on everyone
  (her too: it is day).
- The lamp's flame in daylight.

## In, out, skip, subtitles

- **In.** As she steps out of the inn: bars in, the square's folk on the walk to
  the shrine.
- **Out.** Into play in the Quiet Garden. Brannoc stays kneeling there until
  noon; the lamp stays lit at the grave for the rest of Act 1 (and the hook over
  the inn door stays empty).
- **Skip.** Lands in the garden, people leaving.
- **Subtitles.** The hymn in italics under "Chid", a line at a time.

## What it needs

The Quiet Garden made a place a crowd can stand in; a fresh grave; the iron
marker prop (the plate with NELL and the mark); a lamp prop for Rook's lamp
(the same as over the inn door) and its empty hook; driving a stake with a
hammer while kneeling; a crowd placed in a ring (Folk in good clothes); helmets
under arms; Vonnra standing on the lane and walking away; a sung VO.
