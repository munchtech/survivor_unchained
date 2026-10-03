# C09 · The Fortune

**Chapter one closes.** Priority 1 · Act 1's last scene · about 2 to 2½
minutes by what the player did · skippable page by page

## What it does

On the roof of the toll tower, at night, with the whole valley laid out in the
dark below, Vonnra reads the survivor's palm, and what she reads is the
survivor's own chapter: the wolves, the caravan, the six crates, Pell, the
survivor, what came before the ford, and what is under the Verge. Each reading
finds its place in the dark: a lit window in the town below, a fire in the
ravine, a pump-light in the hills, the dark posts of the Low Ford. She performs
reading the hand. She knows things she can only have bought.

A survivor who has gathered enough of the lamps can say it to her face. She
does not say no. For the first time she lifts her lamp to the survivor's face,
the way the Warden did at the ford, and says her name.

Then, alone, she writes one line in a small book in violet ink, and draws a
link of chain beside it.

- **Vonnra wants** to know whether the survivor is the kind who walks into
  things (she says so: "you are the kind that does"), because she needs one who
  will walk down a stair. **She hides** everything: that her sight is bought,
  that she lit the lamps, that she made this woman. **She changes**, if accused:
  she is seen, and she answers with the only true thing she gives in Act 1, the
  name.
- **The survivor wants** her fortune, or the truth. **She learns** her own
  chapter read back, and (if she pays attention) where Vonnra's sight comes from.
- **Pays:** the whole of Act 1, reading by reading; Sella's buyers ("Vonnra pays
  for all of it", quoted back word for word if she told Sella her past); the lamp
  in the tower window (C04); the Warden's lamp to her face (C02) and
  Grimtunnel's (C03), now Vonnra's; the square coin at her throat
  (`vonnra.coin`); Tam's knocking (in the reading of what is below).
- **Plants:** the ledger and the chain link (Act 3: she means to bind the
  survivor into the chain); the name (Act 3: Vonnra's truth comes easier); the
  coin she touches last (Act 3: the toll at the inner door).

## Trigger and facts

- Stages Vonnra's fortune (`vonnra.fortune` through `vonnra.f_door`): plays
  when the player chooses "Tell me my fortune." with `chapter.ready`. The
  fortune is now read only after dark (the choice is locked by day: "She reads
  only after dark."), so the scene always has the night valley.
- Reads everything the readings read (each node's variants, `dialogue.json`):
  `beasts.outcome`, `promise.broken`, `greymuzzle`, `caravan.survivors`,
  `caravan.cargo`, `jory.knows_be`, `be.crates`, `history burned_roost`,
  `knows clue.blasting_ember`, `caravan.pell`, `pell.fate`, trait `risen_once`,
  `player.wanted`, trait `wolf_friend`, `sella.heard_past`, background,
  `tam.tock`, `LAMPS_CTX` (the accusation), `vonnra.accused`; calling (the
  hand); and, for the vistas, `dig.pump`, `redcowl`, `roost.cleared`,
  `beasts.outcome`.
- Sets: as the nodes do (`chapter.done`, the history, and if accused
  `vonnra.accused`, `lamps/accused`); then the chapter page (action `fortune`).

## Place, time, light

- **The toll tower's roof**, the Waystation's east side (the tower at (33, -8)),
  about 14 m up: a flat lead roof inside a low parapet, a hatch and the head of a
  stair at its west side, a small square table and two stools at its middle, a
  cloth on the table, Vonnra's lamp on it (the lamp from the window in C04), her
  ledger closed at her elbow.
- **The view** (a backdrop: see What it needs): west, the town below, its
  braziers, roofs and lit windows; south, the Low Ford road going away into the
  dark to three dead posts by a faint pale line of river; east, over the wall,
  the Verge, a black mass of wood under a dark sky, with points of light in it
  that depend on what the player did: the Dig's pump-light in the north-east
  hills (if the pump still runs), the Roost's cookfires in the south-east (if the
  Kerchiefs are there), nothing (if not); north, the dark road past the north gate
  and the small light of Keegan's brazier.
- **Time:** night. `Atmospheres.NightTown`, stars, a quarter moon low in the
  west.
- **Light:** Vonnra's lamp is the key: warm, low, from the table, on two faces
  and four hands. The moon a cold rim. Below, the town's warm points; far off,
  the valley's few.
- **Mood:** an audience. A ledger read aloud.

## Cast and marks

- **Vonnra**, seated on the stool at the table's east side (facing west, toward
  the hatch and the town, the Verge at her back), in her violet, the square coin
  on its cord at her throat, rings on her fingers.
- **The survivor** comes up through the hatch (west side), crosses, and sits on
  the stool at the table's west side, facing Vonnra and, over Vonnra's shoulder,
  the Verge.

## Shot list

### Arrival and the hand (`vonnra.fortune`)

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 1 | ELS | 24 | Static, high on the parapet's south-west corner | The roof, the table and its lamp, Vonnra seated, the Verge black beyond her. The hatch opens; the survivor comes up out of the stair into the night wind. | 5.0 |
| 2 | MS | 50 | Static, behind Vonnra's shoulder | The survivor crosses to the table. Vonnra does not look up. Line `vonnra.fortune` (by calling): "Sit. Give me your hand." She holds out both of hers, palms up, over the cloth. | 5.0 |
| 3 | INSERT | 85 | Static, from above the table | The survivor's hand into Vonnra's: the wrong one. "No, the other one: the one you..." The survivor gives her the other. Vonnra's thumb settles in the palm. | 4.0 |
| 4 | 2S | 50 | Static, profile, the lamp between them | "No charge, this once. I have been waiting to see how it came out." Vonnra's eyes go down to the palm and stay there. | 4.0 |

### The readings (each `f_` node: a vista, then the table)

Each reading is two or three shots: **a vista** (a long lens, 135 or 200, from
the roof into the dark, finding the reading's place and its light; 3 to 4 s),
then **the table** (the 2S or a single on either face; 4 to 7 s) for the rest
of the line. The narrator never speaks; Vonnra carries it all. Hold a beat of
the valley's silence between readings.

| # | Node | Vista (by the reading's variant) | At the table |
|---|---|---|---|
| 5 | `f_beasts` | *Cured:* north-east, the Verge; a long, far howl, healthy, answered by others; a pale thread of moonlit stream through black trees. *Allied:* the same howl, nearer, and the town's dogs answering it below. *Slaughtered (and Greymuzzle dead):* the Verge in total silence; the camera holds on the black for longer than is comfortable. *Ignored:* down at the east gate below: eyes in the dark beyond it, low, many. *Exploited:* the north-east hills, the Dig's pump-light still burning, moved. *Broken promise:* north, the Hollow's dark, and one wolf's howl that stops short. *Unsettled:* nothing; the dark. | Vonnra reading, eyes on the palm; the survivor watching her, not the hand. |
| 6 | `f_caravan` | Down into the town: Coyle Trading below. *Rescued and returned:* a lit upstairs window; through it, a man sitting up beside a sleeping boy. *Jory knows:* the same window; the boy is not asleep: sitting up, his back to his uncle. *Rescued and sold:* a lit window, and in the yard a gap where a strongbox would stand. *Dead:* the shutters closed and dark. *Unsettled:* the east road beyond the gate, empty. | On "People always do" (sold) or "You know" (dead), the survivor's hand closes a little in Vonnra's; Vonnra's thumb opens it again. |
| 7 | `f_ember` | South-east, the ravine. *Redcowl keeps them:* the Roost's cookfires, three small lights low in the dark. *Harlan's:* down in the town: Coyle's yard, a covered wagon by a lantern. *Burned:* the ravine dark, a smear of old smoke against the stars. *Otherwise:* the Roost's fires, and one more light moving away from them along the ravine toward the hills (somebody carrying something). | Vonnra's eyes on the palm; on "Someone always does." she glances up, east, past the survivor's shoulder, the first time her eyes leave the hand. |
| 8 | `f_pell` | Down: Pell's warehouse. *Exposed:* a watchman's lamp at its sealed door. *Fled or taken:* the door standing open, the inside dark. *Ally:* an upstairs light; a man's shadow at a desk. *Otherwise:* the same light. | Neutral. On "One day he will count you." (the fallback) her thumb presses once in the palm. |
| 9 | `f_self` | No vista. The camera stays at the table. | CU, 85, on the survivor's face for the whole line. *Risen once:* Vonnra's thumb is still on the palm; "I would very much like to know what." is said to the hand. *Wanted:* Vonnra's mouth moves (no rig: her head tilts) at "It is not flattering." *Wolf-friend:* below, a dog barks once in the town. *Fallback ("the lamps lit for you"):* hold on the survivor; let the player hear it. |
| 10 | `f_past` | South: the Low Ford road going away into the dark, and at its end the three dead lamp-posts by the pale line of the river. | *Sella's variant:* Vonnra speaks it looking south, at the ford, not at the palm. The narrator's parenthesis is the picture: a MS at 50 from behind the survivor shows Vonnra's face turned away to the south while her thumb rests, forgotten, in the survivor's palm. *Fallback:* the same, said to the south; "Most do." is the only line in the reading she says gently. |
| 11 | `f_below` | Down: the cobbles at the foot of the tower; then the camera tilts slowly down past the parapet as if it could look into the ground. *(Tam's knocking known:)* out over the town to the dark beyond the Old Road where the farms are; one small light (a farm window) and nothing else. | Vonnra: "And the door in the hillside..." She stops. The choices come up. Hold on the 2S, the lamp between them. |

### The door, or the accusation

**"What about the door?"** (`vonnra.f_door`, fallback):

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 12 | MS | 50 | Static, on Vonnra | She lets go of the hand. "The door is not for sale..." to the end. She looks at the palm she has let go of. | 7.0 |
| 13 | 2S | 50 | As 4 | The choice "Close the book on this chapter." The survivor stands. | 2.0 |

**"You lit the lamps at the Low Ford."** (`vonnra.f_accuse`, then `f_door` #0):

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 12a | MCU | 85 | Static, on the survivor | She says it (the choice, read). She takes her hand back and stands. | 2.5 |
| 13a | MS | 50 | Static, low, past the survivor's hip onto Vonnra | Vonnra does not move for a long moment. Then she lifts the lamp from the table and holds it up to the survivor's face, the way the Warden did at the ford. For the first time she looks at the survivor's face and not her hand. It goes on long enough that the lamp gutters. | 5.0 |
| 14a | ECU | 135 | Static | The survivor's eyes with the lamp's flame small in each, as at the ford. | 2.5 |
| 15a | CU | 85 | Static, up at Vonnra past the lamp | Line `vonnra.f_accuse`: "...Sit down, {name}. I have not finished reading." She sets the lamp down. | 4.0 |
| 16a | 2S | 50 | As 4 | The survivor sits. Vonnra does not take the hand again. Line `vonnra.f_door` #0: "The door in the hillside is listening, as I am. That is all I see for free, {name}..." Then "Close the book on this chapter." | 9.0 |

### Alone (the stinger, after the chapter's choice)

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 17 | LS | 35 | Static, from the parapet's north-east corner | The survivor goes down through the hatch. Vonnra, alone at the table, draws the ledger to her and opens it. | 4.0 |
| 18 | INSERT | 100 | Static, over her hand | A page of small entries in violet ink, out of focus, many lines. Her pen writes the last line in focus: *The one from the ford* (or, if accused, the survivor's name). Beside it she draws, small and careful, a single link of chain. | 5.0 |
| 19 | MCU | 85 | Static, profile against the south | She closes the book. She looks south, to the dark ford. Her fingers find the square coin at her throat and turn it once. | 4.0 |
| 20 | Black | | | Fade to black over 1.5 s; the chapter's page (`Chapter.Summary`) comes up out of it. | 1.5 |

Total, unaccused: about 2 minutes 5 s; accused, about 2 minutes 20 s (the
readings' lines run 6 to 12 s each).

## Performance

**Vonnra** (no face rig: carry her with stillness, the hands, the head, and the
lamp). No contractions; long pauses; never hurried; never answers yes or no
(`VOICES.md`). Through the readings she is a performer who has done this a
thousand times: her thumb in the palm, her eyes on it, the voice level and low.
What breaks the performance, a little at a time: the glance east on "Someone
always does" (shot 7); turning to the south for what came before the ford (shot
10), where she is reciting, not reading, and does not notice she has stopped
looking at the hand. If accused: the stillness becomes a different stillness,
someone listening very hard. She lifts the lamp slowly. "{name}" is the only
word in the game she says with something like warmth, and it should frighten.

**The survivor.**
- *Shots 2 to 4.* `brows_up` 0.1; she offers the wrong hand without thinking
  (that is all it is).
- *Readings.* Gaze on Vonnra's face, not the hand (`Look` on Vonnra's eyes),
  `Wander` 0.08. Let her react to what is read: `brows_sad` 0.3 on the dead
  (the cages, Greymuzzle, Aldo); `smile` 0.1 on "Most people never learn the
  difference" (cured); `brows_angry` 0.2 on the ledger with her name (Pell
  ally); on her own past, if Sella's variant plays, a frown (0.3) building
  across the line: she told one person that, upstairs.
- *The accusation.* `brows_angry` 0.3, `mouth_open` 0; standing, still; in the
  lamp's light (shot 14a), she does not squint.

## Lines

All existing (conversation `vonnra`), except the calling variants of the first
line, added in this pass:

| VO id | Line |
|---|---|
| `vonnra.fortune#0` (arcanist) | Sit. Give me your hand. No, the other one: the one you burn with. No charge, this once. I have been waiting to see how it came out. |
| `vonnra.fortune#1` (stalker) | ...No, the other one: the one you draw with. ... |
| `vonnra.fortune#2` (warden, reaver) | ...No, the other one: the one you hold the blade with. ... |
| `vonnra.f_beasts#0` to `#7` | the wolves (see `dialogue.json`) |
| `vonnra.f_caravan#0` to `#5` | the caravan |
| `vonnra.f_ember#0` to `#4` | the crates |
| `vonnra.f_pell#0` to `#4` | Pell |
| `vonnra.f_self#0` to `#3` | the survivor |
| `vonnra.f_past#0` to `#4` | before the ford |
| `vonnra.f_below#0`, `#1` | below |
| `vonnra.f_accuse` | ...Sit down, {name}. I have not finished reading. |
| `vonnra.f_door#0`, `#1` | the door |

`{name}` in a VO line is the survivor's name: render the line twice, once with
"traveller" in its place (for the subtitle-only fallback) and once as two
recordings spliced round a gap the name is read into by TTS at play time, or
render it per save. (A name in a voiced line is the only place the game needs
this; it is worth it here.)

*Casting:* Vonnra, 60s, clipped and unplaceable, a low alto with a little air:
the most important casting in the game.

## Sound

- **Music.** `Mystery` mood, very low, from the hatch opening: its bell, slow,
  and a held pad. Each vista brings one bell note; the table brings the pad back.
  Under the accusation: everything out but a single held low note, then nothing
  for "{name}". The stinger: the bell once as she draws the link. Silence for the
  fade.
- **Effects.** Wind on the roof (constant, light); the town below (a door, a
  dog, a cart late home, the braziers); the lamp's flame; cloth; rings on wood;
  the vistas' own sounds (the howl, dogs answering, the pump's distant hum if it
  runs, a far fire); the pen on paper (shot 18), very close; the ledger closing;
  the coin turning on its cord.

## VFX

- The lamp's flame (guttering in 13a).
- Breath: Vonnra's breath smokes in the cold; the survivor's does not (it is
  night, and the ember burns in her). Nobody remarks on it. Somebody watching
  the two-shots for a whole reading might.
- Distant lights on the backdrop, by facts.

## In, out, skip, subtitles

- **In.** On the choice: a fade to black over 0.8 s from wherever she is (the
  tower's door), and up on shot 1.
- **Out.** Into the chapter's page (the `fortune` action), then back into the
  Waystation at night by the tower's door.
- **Skip.** Page by page: a skip advances to the next reading (they are the
  point); a long hold skips to the choice at `f_below`, then to the page.
- **Subtitles.** Vonnra's lines under "Vonnra"; the readings are long: break at
  sentences, two lines at a time.

## What it needs

**A roof on the toll tower** (a set: lead roof, parapet, hatch, table, stools,
lamp, ledger). **A backdrop of the valley** seen from it, with lights that can be
switched by the world's facts (the Dig's pump, the Roost's fires, a farm window,
Keegan's brazier, the ford's posts): the Verge is another zone, so it cannot be
rendered live from here; a panorama rendered offline from the Verge's own data,
or painted, with light sprites on it, will do. Windows in the town that can be
lit and seen into at a distance (Coyle Trading's, Pell's). Two people at a
table: sitting on stools, hands held across a table (hand IK), a palm read with a
thumb, a lamp lifted to a face. A pen writing (an insert of a hand, a pen and a
page; the page texture with lines of violet entries). A coin on a cord turned in
the fingers. A name in a voiced line.
