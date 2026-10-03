# C08 · The Iron Marker

**Nell is buried.** Priority 2 · Act 1 · about 72 s · conditional (only if she
told Brannoc the truth) · skippable

## What it does

The morning after she told him, the town walks to the Quiet Garden behind the
shrine without being asked. Chid sings the Order's burial hymn, badly, and the
town comes in on the last line of each verse. Brannoc sets an iron marker at the
grave's head and drives it in with three strokes of his hammer. Rook takes her
mother's lamp down from over the inn door, the Order's lamp, and sets it burning
at the grave's foot in broad daylight. On the hymn's last line Chid makes the
Order's sign for the dead, finger and thumb closing on the air as a lamp-tender
puts out a chapel lamp at morning, beside Rook's lamp, which is staying lit.

Vonnra is there too, in the ring with everyone else, unremarkable, hands in her
sleeves, head bowed like everyone's. Under the ragged ring on each last line, one
voice knows every word and is in tune, a low alto. It is hers.

- **Brannoc wants** to do this right, with his hands. **He hides** nothing now.
  **He changes** if he knows she got up: on the hymn's last line ("it will wake you
  where you slept") his hand stops on the marker, and grips it.
- **Rook wants** to give something and not be seen giving it. She never cries in
  front of anyone; she sets the lamp down and goes to the back and turns away.
- **Chid wants** to sing her down properly, and cannot sing. He sings anyway, and
  his voice cracks on "risen".
- **Vonnra wants** nothing anyone can see. She came to a child's funeral, as a
  town's toll-keeper does. **She hides** everything but one thing she cannot help:
  she knows the Order's hymn by heart, and sings it as it was meant to be sung.
- **Harlan** keeps his hand on Jory's shoulder the whole time, and is the only one
  who does not sing.
- **The survivor** stands at the back: the one who put the child down, at the
  funeral.
- **Plants:**
  - the hymn ("the morning lies a little under", "your toll is paid", "the dark is
    but the day not risen", "it will wake you where you slept"). Every line is a
    comfort at a grave, and every line is true in a way the town does not know
    (Act 3);
  - the alto in tune (Act 3: the binders kept the Legion's keys beside the Order,
    and her family has sung this over its own dead for longer than the Watch has
    existed);
  - Rook's lamp (the Order's, which her mother carried up from the chapel: Act 3,
    Chid's truth);
  - the Order's sign beside a lamp left burning (the endings: let them go, or
    keep them lit);
  - Harlan not singing (Act 2, Harlan exposed);
  - the week-old grave a few stones along (the survivor's mother; Act 3).
- **Pays:**
  - C07 (the truth);
  - C02's "Lie down." (the Warden's word to the living was the Order's word for the
    dead: the hymn begins with it);
  - C03's sign, if the survivor is devout (she made it over the Warden);
  - C01's lamps, and the "toll work" of Brannoc's question;
  - the lamp over the Last Lamp's door (`rook.lamp`);
  - Chid "can't sing" (`folk.json`);
  - C14, if it played: the marker is punched with a nail because there was no time
    to forge one.

## Trigger and facts

- **Trigger.** The morning `nell.buried` becomes true (rule `nell.burial`, the
  morning after she told Brannoc the truth), the first time she is out of doors.
  That is ordinarily stepping out of the Last Lamp. After C14 she is already
  outside, at the south gate at sunrise, and C08 begins at shot 2, as she crosses
  the square.
- **Reads:**
  - `nell.told` (`risen` or `gone`);
  - `nell.brought_home` (C14 played: shot 14's variant);
  - `caravan.survivors` (Harlan and Jory, if `rescued`);
  - `met` for Maeca, Wenna, Tam and Holloway (who is there);
  - background `devout` (nothing changes here; see C03);
  - the mother's name, if the player gave one at creation (the marker).
- **Sets** nothing new.

## Place, time, light

- **The Waystation:**
  - the Last Lamp's door (-11.3, 11);
  - the lane past the shrine (-26, -25) to the gap in the hedge (about (-34,
    -32));
  - the Quiet Garden behind it (-38, -36): nettles, an old yew, the first
    Watch-captain's stone (Ashe's), and beside it a fresh grave cut in the turf.
  - A few stones along the garden's west side is a grave a week old: the turf not
    yet knitted, and a plain wooden marker with a name burned into it.
- **Time:** early morning, a still day, low sun through the yew.
- **Light:**
  - long shafts through the yew's branches; dew on the nettles; the grave's earth
    dark and wet;
  - Rook's lamp, ember in an open lamp, burning small and gold in the daylight.
- **Mood:** a town being decent. Grief kept to its size.

## Cast and marks

Ashe's stone stands at (-38.5, -37). The fresh grave is east of it at (-36.8,
-37), its head to the north. The week-old grave is at (-41.5, -35.5), its wooden
marker facing the yew.
- **Chid:** at the grave's head (-36.8, -38.6), facing south, hands folded.
- **Brannoc:** kneeling at the head beside Chid, with the iron marker and his
  hammer.
- **Rook:** on the ring's west side, the inn's lamp in her hands.
- **Vonnra:** on the ring's north-east side, between two townswomen. She wears
  violet, but plain, with her hands folded in her sleeves. Nobody gives her room
  and nobody looks at her.
- **Holloway and two watchmen:** on the east side, helmets under their arms.
- **Wenna**, with a bunch of rosemary; **Tam** beside her (if met), holding her
  skirt.
- **Harlan and Jory** (if the survivors were rescued): south-east, Harlan's hand
  on Jory's shoulder.
- **Maeca** (if met and not cold to the survivor): at the back by the yew,
  barefoot, apart.
- **Townsfolk:** a dozen in their good clothes, in a loose ring.
- **The survivor** stops at the hedge gap (-34, -32), then comes three paces in and
  stands at the back, south of the ring. The week-old grave is behind her left
  shoulder; she never turns to it.

## Shot list

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 1 | MS | 35 | Static, outside the inn, low | She steps out of the Last Lamp into the morning. Over the door, the old lamp's hook is empty. *(Not after C14.)* | 3.0 |
| 2 | LS | 28 | Static, across the square | The square nearly empty; people in their good clothes walking, all the one way, north-west past the shrine, quietly. She follows. *(After C14 she comes into the square from the south gate, the lantern still in her hand; she looks at the empty hook over the inn door as she passes it.)* | 4.0 |
| 3 | MLS | 35 | Tracking behind her along the lane to the hedge gap | The hedge; the gap; through it, the Quiet Garden in the yew's shade, the town in a ring round a fresh grave beside the old captain's stone. | 5.0 |
| 4 | LS | 24 | Static, wide, from inside the garden by Ashe's stone | The whole ring, Vonnra in it, one face among many. At the frame's left edge, a few stones along, the week-old grave with its wooden marker, unremarked. Chid begins to sing (H1). Brannoc kneels at the head with the marker. | 7.0 |
| 5 | MCU | 50 | Static, on Chid | He sings with his eyes shut, off the note, with his whole heart. On the verse's last line the ring comes in under him, low and ragged: "and it will wake you where you slept." Under the ragged voices, one is in tune. | 6.0 |
| 6 | INSERT | 85 | Static, low, at the grave's head | The iron marker: a plate of black iron on a stake. Punched into it with a nail, letter by letter: **NELL**. Below, small: a ring with a hammer across it. | 3.0 |
| 7 | MS | 50 | Static, side-on, low | Brannoc sets the marker's point in the turf and drives it with his hammer: one stroke, two, three. Iron into earth, dull; no anvil's ring. The third stroke is the last. | 6.0 |
| 8 | MS | 50 | Static | Rook comes forward with the lamp, lit, and sets it at the grave's foot. She steps back, and back, to the edge of the ring, and turns her face to the yew. | 6.0 |
| 9 | 2S | 85 | Static, across the ring, long | *(Rescued:)* Harlan with his hand on Jory's shoulder; the ring sings H2 round him and his mouth does not move. *(Otherwise:)* Wenna with the rosemary, and Tam holding her skirt, singing the wrong words. | 4.0 |
| 10 | MCU | 50 | Static, on Chid, Rook's lamp burning in the foreground, soft | H2's last two lines. His voice cracks on "risen", and he smiles at himself, embarrassed, and goes on. As the ring comes in on the last line he makes the Order's sign over the grave: his finger and thumb close slowly on the air, as a lamp-tender puts out a chapel lamp at morning. In the foreground Rook's flame stays lit. | 5.0 |
| 11 | CU | 85 | Static, on Brannoc's hand on the marker | "...and it will wake you where you slept." *(If `nell.told` is `risen`:)* his hand, resting on the marker, stops, and grips it. *(If `gone`:)* it rests there. | 3.0 |
| 12 | LS | 135 | Static, from behind the survivor across the grave, compressed; a slow push in over the line | Every head in the ring bowed for the last line, Vonnra's too, between the two townswomen. The push finds her by sound, not by look: under the ragged ring one voice knows every word and is in tune, and as the camera arrives her bowed head is the only one whose lips are moving with it. | 4.0 |
| 13 | MCU | 50 | Static, on the survivor | She has heard it. Her eyes go across the grave to Vonnra. Vonnra's head stays bowed. The hymn is over; silence. | 3.5 |
| 14 | MCU | 50 | Static, on Brannoc | *(Not after C14:)* he lifts his head and looks at the survivor across the grave. Just looks. She holds it. *(After C14, `nell.brought_home`:)* he doesn't look up. He doesn't need to. | 4.0 |
| 15 | LS | 24 | Static, as 4 | People go, in twos and threes, back through the hedge; Vonnra among them, unhurried, one more back in the lane. Brannoc stays kneeling. The lamp burns in the daylight at the grave's foot, beside the old captain's stone. At the left edge the week-old grave's marker, nearer now. If the player named their mother at creation, her name can just be read on it. Nobody looks at it. Bars out. | 6.0 |

Total: about 72 s (69 s after C14, from shot 2).

## Lines

Conversation `cin_iron_marker`, speaker `chid`. The hymn is the Order of the
Morning Light's burial hymn, "Lie Down". It is **sung**, badly and with love, and
the ring joins the last line of each verse.

| VO id | Shots | Line |
|---|---|---|
| `cin_iron_marker.verse1` | 4 to 5 | *Lie down, lie down, the lamps are tended, / and all the dark is kept; / the morning lies a little under, / and it will wake you where you slept.* |
| `cin_iron_marker.verse2` | 9 to 11 | *Lie down, lie down, the road is ended, / your toll is paid and kept; / the dark is but the day not risen, / and it will wake you where you slept.* |

**Casting.**
- **Chid** (sounds 30s, Irish-tinged; his voice catches on joy, and here on the
  opposite). He sings a little flat, slowing on the turn of each verse.
- **The tune:** plain and old, four lines in a minor key that lifts on the last.
  The player has heard it once before, as a single instrument on the walk home in
  C14, if C14 played.
- **The ring:** a dozen ordinary voices, out of time, under him on each last line.
- **Vonnra:** a low alto, in tune, every word right, never louder than the rest:
  mixed so that a listener finds her rather than hears her.
- Local TTS will not sing it. Record it sung (a human voice, or a singing
  synthesis). A half-sung, half-said Chid is also true to him.

**What it means.**
- **At the grave:** the lamps are kept, the dark is guarded, morning is only just
  under the hill, the road is over and paid for, and she will wake.
- **To the player who has been paying attention:** the Order's "morning" is the
  thing under the ground; Nell was on toll work; and she did wake.
- **In Act 3, a third time:** the morning under the ground keeps every one of the
  valley's dead, and at the bottom of the stair Nell is there, saying "Da".

Nobody in the garden knows any of it but the survivor, Brannoc if she told him so,
and the woman in violet who knows every word.

## Performance

**Brannoc.** He kneels as a smith kneels at work, not in prayer. Three strokes,
measured. In shot 14 the look has no thanks in it and no blame: she was there, and
nobody else here was. After C14 there is nothing left to say with a look, and he
doesn't spend one. (No face rig: a slow lift of the head, held; or none.)

**Rook.** She carries the lamp in both hands, the way you carry a full bowl. She
sets it down without kneeling, with a sharp bend from the waist, then steps back,
keeps stepping back, and turns away from everyone.

**Chid.** Eyes shut; the whole of him in it. The crack on "risen" makes him smile,
embarrassed, mid-line. The sign is old and unhurried: his hands have put out a
great many lamps at morning.

**Vonnra.** Stillness, hands in her sleeves, head bowed exactly as low as the
townswomen's either side of her: she has watched how they do it. She sings only
the last lines, with the ring, and sings them right, because she cannot sing them
wrong. She does not look at the survivor at all.

**Harlan.** His hand on Jory's shoulder throughout, as if Jory might go
somewhere. He does not sing, and nobody notices but the camera.

**The survivor.**
- *Shot 3.* `brows_sad` 0.2; she comes in quietly.
- *Shot 7.* A small blink at each stroke.
- *Shot 13.* At the in-tune voice, gaze across to Vonnra (`Look` on her bowed
  head); `brows_up` 0.15, then `brows_sad` 0.3. She keeps looking a moment after
  the hymn ends.
- *Shot 14.* She meets Brannoc's look: `brows_sad` 0.45, `frown` 0.1, jaw set,
  `mouth_open` 0; no tears. After C14: she watches him not look up.

## Sound

- **Music.** None but the hymn, unaccompanied. After it, the garden's silence:
  birds, the yew, a distant cart.
- **The mix.** The ring is ragged and close; Vonnra's alto sits a little under it
  and a little behind, true, never louder. In shot 12 the push brings it forward
  by a few decibels, no more.
- **Effects.**
  - the town's morning, hushed; footsteps on the lane; the hedge; nettles
    brushing;
  - the marker going into turf: three dull strokes, and the absence of the anvil's
    ring is the point;
  - Rook's lamp set down on stone; the small flame;
  - people leaving.

## VFX

- Sun shafts through the yew; dew. Everyone's breath smokes in the cold morning,
  hers too: it is day.
- The lamp's flame in daylight, gold.

## In, out, skip, subtitles

- **In.** As she steps out of the inn, bars in, with the square's folk on the walk
  to the shrine. After C14, from the gate: bars stay in from C14's last shot.
- **Out.** Into play in the Quiet Garden. Brannoc stays kneeling there until noon.
  The lamp stays lit at the grave for the rest of Act 1, and the hook over the inn
  door stays empty.
- **Skip.** Lands in the garden, with people leaving.
- **Subtitles.** The hymn in italics under "Chid", a line at a time.

## What it needs

- **The Quiet Garden** made a place a crowd can stand in: a fresh grave; a
  week-old grave with a wooden marker that can carry the mother's name from
  creation.
- **The iron marker** (the plate with NELL and the mark).
- **Rook's lamp** (the one over the inn door) and its empty hook.
- **Driving a stake with a hammer while kneeling.**
- **A crowd placed in a ring:** Folk in good clothes, with Vonnra among them;
  helmets under arms.
- **The Order's sign:** finger and thumb closing on the air (a hand pose).
- **A sung VO** with a crowd under its last lines, and one voice in tune under the
  crowd.
