# C09 · The Fortune

**Chapter one closes.** Priority 1 · Act 1's last scene · about 2 minutes by
what the player did · skippable page by page

## What it does

It is night, on the roof of the toll tower, with the whole valley laid out in the
dark below. Vonnra reads the survivor's palm. What she reads is the survivor's own
chapter: the wolves, the caravan, the six crates, Pell, the survivor, what came
before the ford, and what lies under the Verge.

She performs reading the hand. For the first two readings, the camera believes her:
her eyes are on the palm, and the valley is only a sound. Then, on the crates, her
eyes leave the hand for the first time. They go over the survivor's shoulder, east,
into the dark the survivor has her back to, and the camera goes with them. From
then on, every time Vonnra knows something, she is looking at something. She is
reading the valley from her roof, not the lines of a hand. A player who is paying
attention sees how she knows.

The seats make this possible. Vonnra faces east, over the survivor's shoulder, to
the Verge. The survivor faces west, and sees only Vonnra and, behind her, the lit
town.

A survivor who has gathered enough of the lamps can say it to her face. Vonnra
does not say no. For the first time she lifts her lamp to the survivor's face, as
the Warden did at the ford. In its light, Vonnra's breath smokes across the flame
and the survivor's shows nothing. That is what a keeper looks for, and nobody
says so. Then Vonnra says the survivor's name.

Then she is alone with her ledger. On its page are twenty-six lines struck
through, and one that is not.

- **Vonnra wants** to know whether the survivor is the kind who walks into things.
  She says so ("you are the kind that does"), because she needs one who will walk
  down a stair.
  - **She hides** everything: that her sight is a roof and a long memory, that she
    lit the lamps, that she drowned this woman.
  - **She changes** only if accused. She is seen, and she answers with the only
    true thing she gives in Act 1, the name.
- **The survivor wants** her fortune, or the truth. **She learns** her own chapter
  read back. If she pays attention, she also learns where Vonnra's sight comes
  from.
- **Pays:**
  - C01's call up the road: "No charge, this once." opens the reading, the voice that called her up the road now across a table (bible, "Who tells it");
  - the whole of Act 1, reading by reading;
  - Sella's buyers ("Vonnra pays for all of it"), paid in the reading of her past
    if she told Sella that past while Sella was still selling her
    (`sella.past_sold`: not after the night Sella would not take the money);
  - the tremors (rule `tremor`, "the ground turned over in its sleep"), which stop
    Vonnra in the middle of a sentence;
  - the lamp in the tower window (C04), now on the table;
  - the Warden's lamp to her face (C02) and Grimtunnel's (C03), now Vonnra's. The
    breath in the lamplight explains, without a word, why the keepers hold one up;
  - the square coin at her throat (`vonnra.coin`);
  - Tam's knocking (in the reading of what is below).
- **Plants:**
  - the struck ledger. In Act 3 she says "I drowned twenty-six people to find you"
    and "I wrote every one of them down", and both land on this page. In C50 she
    strikes the survivor's line;
  - the name: in Act 3, Vonnra's truth comes easier;
  - the coin she touches last (Act 3: the toll at the inner door);
  - her look south, at the ford, while reciting a past she says she cannot see.

## Trigger and facts

- **Trigger.** It stages Vonnra's fortune (`vonnra.fortune` through
  `vonnra.f_door`). It plays when the player chooses "Tell me my fortune." with
  `chapter.ready`.
  - The fortune is now read only after dark. By day the choice is locked ("She
    reads only after dark"), so the scene always has the night valley.
- **Reads** everything the readings read (each node's variants, in
  `dialogue.json`):
  - the wolves: `beasts.outcome`, `promise.broken`, `greymuzzle`;
  - the caravan and the crates: `caravan.survivors`, `caravan.cargo`,
    `jory.knows_be`, `be.crates`, history `burned_roost`, `knows
    clue.blasting_ember`;
  - Pell: `caravan.pell`, `pell.fate`;
  - the survivor: trait `risen_once`, `player.wanted`, trait `wolf_friend`,
    `sella.past_sold`, background;
  - below: `tam.tock`;
  - the accusation: `LAMPS_CTX` and `vonnra.accused`;
  - the calling (which hand she asks for);
  - for the backdrop's lights: `dig.pump`, `redcowl`, `roost.cleared`,
    `caravan.survivors`.
- **Sets** what the nodes set: `chapter.done` and the history, plus, if accused,
  `vonnra.accused` and `lamps/accused`. Then the chapter page (action `fortune`).

## Place, time, light

- **The toll tower's roof**, on the Waystation's east side (the tower stands at
  (33, -8)), about 14 m up.
  - A flat lead roof inside a low parapet.
  - A hatch and the head of a stair at its west side.
  - At its middle, a small square table with a cloth and two stools. Vonnra's lamp
    stands on it (the lamp from the window in C04), with her ledger closed at her
    elbow.
- **The view** (a backdrop: see What it needs). Lights only, by the world's facts.
  - **West** (behind Vonnra, and the survivor's whole view): the town below, its
    braziers, roofs and lit windows. Coyle Trading's upstairs window is lit if the
    survivors came home.
  - **East** (behind the survivor, Vonnra's view): over the wall, the Verge, a black
    mass of wood under a dark sky.
    - Low in the south-east, the ravine: the Roost's cookfires (three small lights)
      if the Kerchiefs are there, or a smear of old smoke against the stars if it
      burned.
    - High in the north-east hills, the Dig's pump-light, if the pump still runs.
  - **South** (Vonnra's right hand): the Low Ford road, a pale thread going away into
    the dark, to a faint line of river under the moon where the three posts stand
    unlit.
- **Time:** night. `Atmospheres.NightTown`, stars, and a quarter moon low in the
  west, behind Vonnra.
- **Light:**
  - Vonnra's lamp is the key light: warm and low, from the table, on two faces and
    four hands.
  - The moon puts a cold rim on Vonnra and lights the survivor's face, faintly, from
    the front.
  - Below, the town's warm points; far off, the valley's few.
- **Mood:** an audience. A ledger read aloud.

## Cast and marks

- **Vonnra** sits on the stool at the table's west side, facing east. The hatch and
  the town are at her back; the Verge is in front of her, over the survivor's
  shoulder. She wears her violet, the square coin on its cord at her throat, and
  rings on her fingers.
- **The survivor** comes up through the hatch behind Vonnra and passes her. She sits
  on the stool at the table's east side, facing west: she sees Vonnra and, below
  and behind her, the town.

## Shot list

### Arrival and the hand (`vonnra.fortune`)

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 1 | ELS | 24 | Static, high on the parapet's south-east corner, looking west | The roof, the table and its lamp, Vonnra's back. Beyond her and below, the lit town. The hatch opens behind her; the survivor comes up out of the stair into the night wind. Vonnra does not turn round. | 5.0 |
| 2 | MS | 50 | Static, past Vonnra's shoulder, looking east | The survivor comes round the table into the lamplight and sits, the black Verge behind her. Line `vonnra.fortune` (by calling) begins: "Sit. Give me your hand." Vonnra holds out both of hers, palms up, over the cloth. | 5.0 |
| 3 | INSERT | 85 | Static, from above the table | The survivor puts her hand into Vonnra's: the wrong one. "No, the other one: the one you..." The survivor gives her the other. Vonnra's thumb settles in the palm. | 4.0 |
| 4 | 2S | 50 | Static, profile from the south, the lamp between them | "No charge, this once. I have been waiting to see how it came out." Vonnra's eyes go down to the palm and stay there. | 4.0 |

### The readings

The rule: **a vista only on Vonnra's eyeline.** The camera goes into the valley
only when her eyes leave the hand, and it sees only what she could see from where
she sits: lights in the dark, at a distance, on a long lens (135 or 200). It shows
no detail that 14 m and a night could not give her. Hold a beat of the valley's
silence between readings. The narrator never speaks; Vonnra carries all of it.

**Coverage at the table** (for every reading):
- **A.** The 2S as 4.
- **B.** Over the survivor's shoulder onto Vonnra, 85. The lit town is soft behind
  her head.
- **C.** Over Vonnra's shoulder onto the survivor, 85. The black Verge is behind
  her.
- **D.** An insert of the hand in the hands, 100.

| # | Node | At the table | Her eyeline, and the vista |
|---|---|---|---|
| 5 | `f_beasts` | A, then B. Her eyes on the palm throughout. She performs, and the performance is good. | None. **Sound only:** if *cured* or *allied*, a long, far howl from the east, healthy and answered by others. It comes from behind the survivor, and the survivor does not turn. If *slaughtered*, a silence held a beat longer than the others. |
| 6 | `f_caravan` | C, then B. On "People always do" (sold) or "You know" (dead), the survivor's hand closes a little in Vonnra's, and Vonnra's thumb opens it again (D). | None. Behind Vonnra in B, soft, the town's lit windows. Nobody looks at them. |
| 7 | `f_ember` | B. On "six crates" her eyes leave the palm for the first time: up, past the survivor's shoulder, east. She says the rest of the line looking at it. | **The turn.** A 200 mm vista on her eyeline, east-south-east, into the dark the survivor has her back to: the ravine. The Roost's three cookfires if the Kerchiefs are there, or the smear of old smoke if it burned. High to the left, the Dig's pump-light if the pump runs. On "Someone always does" (or the variant's last sentence) cut back to B: her eyes come down to the palm again, unhurried. |
| 8 | `f_pell` | A. Her eyes on the palm. On "One day he will count you." (the fallback) her thumb presses once in the palm (D). | None. Pell is in the town, behind her: she does not need to look. |
| 9 | `f_self` | CU, 85, on the survivor's face for the whole line (Vonnra off). *Risen once:* "I would very much like to know what." is said to the hand. *Wanted:* Vonnra's head tilts on "It is not flattering." *Wolf-friend:* below, a dog barks once in the town. *Fallback ("the lamps lit for you"):* hold on the survivor and let the player hear it. | None. |
| 10 | `f_past` | B, then a MS at 50 from behind the survivor, the lamp in the foreground. Vonnra's head turns to her right, south, and stays there. Her thumb rests, forgotten, in the survivor's palm. *Sella's variant:* she says all of it to the south (the data's parenthesis, "She is not looking at your palm.", is this picture). *Fallback:* the same; "Most do." is the only line in the reading she says gently. | A 135 mm vista on her eyeline, south: the Low Ford road going away into the dark, and at its end the pale line of the river under the moon, where the posts stand unlit. No movement. Back to the MS: she turns back to the palm as if she had never left it. |
| 11 | `f_below` | A. On "Last." she looks down: not at the palm, at the table, as if through it. She goes on to "And the door in the hillside..." | A slow tilt down on her eyeline: past the parapet's lip, down the tower's face to the dark at its foot, where the wall meets the Verge, and on down to black as if the camera could look into the ground. *(Tam's knocking known:)* under the line, once, a deep dull knock, felt rather than heard. |
| 11a | The interruption | **The turn.** On "hillside" the roof shivers under the table. The lamp's glass rings in its frame. The flame lies over sideways, toward the east, though there is no wind. From under the town comes C03's groan, long and low, and behind Vonnra, down in the streets, every lamp in the town dips at once and comes back: every ember lamp. The braziers on the wall do not. Vonnra stops in the middle of the sentence. B, then a MCU at 85: her head comes up and turns east, past the survivor, and stays there. Her thumb has come off the palm. | A 200 mm vista on her eyeline, east: the Verge, black, nothing to see. Then the groan stops, and the town's lamps are steady again. Back on the MCU: she is still looking east, and she does not finish. The choices come up while she is looking away. Hold the 2S, the lamp's flame standing up straight again between them. (The accusation, if the survivor makes it now, lands on her off balance.) |

### The door, or the accusation

**"What about the door?"** (`vonnra.f_door`, fallback):

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 12 | MS | 50 | Static, B's side | She lets go of the hand. "The door is not for sale..." to the end. She looks at the palm she has let go of. | 7.0 |
| 13 | 2S | 50 | As 4 | The choice "Close the book on this chapter." The survivor stands. | 2.0 |

**"You lit the lamps at the Low Ford."** (`vonnra.f_accuse`, then `f_door` #0):

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 12a | MCU | 85 | Static, C's side | The survivor says it (the choice, read). She takes her hand back and stands. | 2.5 |
| 13a | MS | 50 | Static, low, past the survivor's hip onto Vonnra | Vonnra does not move for a long moment. Then she lifts the lamp from the table and holds it up to the survivor's face, as the Warden did at the ford. For the first time she looks at the survivor's face and not her hand. | 4.0 |
| 14a | 2S | 100 | Static, profile from the south, tight: two faces and the lamp between them | The lamp at the height of their mouths. Vonnra's breath smokes across the flame, slowly, twice, and the flame leans from it. On the survivor's side of the flame, nothing. The flame gutters. Nobody says anything. | 4.0 |
| 14b | ECU | 135 | Static | The survivor's eyes, the lamp's flame small in each, as at the ford. | 2.0 |
| 15a | MCU | 50 | Static, up at Vonnra past the lamp | Line `vonnra.f_accuse`: "...Sit down, {name}. I have not finished reading." She sets the lamp down. | 4.0 |
| 16a | 2S | 50 | As 4 | The survivor sits. Vonnra does not take the hand again. Line `vonnra.f_door` #0: "The door in the hillside is listening, as I am. That is all I see for free, {name}..." Then "Close the book on this chapter." | 9.0 |

### Alone (the stinger, after the chapter's choice)

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 17 | LS | 35 | Static, from the parapet's north-east corner | The survivor goes down through the hatch. Vonnra, alone at the table, draws the ledger to her and opens it at a page she does not have to look for. | 4.0 |
| 18 | INSERT | 100 | Static, over her hand, the page flat in the lamplight | A page of entries in violet ink, in one small, cramped hand, too small to read. Twenty-seven lines; twenty-six are struck through, each with one ruled line. Her fingertip comes down the page past the struck lines and stops on the twenty-seventh, which is not struck. It rests there. *(Accused:)* the line ends in a space left blank. She dips the pen and writes into it, in the same small hand, the survivor's name: the one word on the page the player can read. | 6.0 |
| 19 | MCU | 85 | Static, profile against the south | She closes the book. She looks south, to the dark ford. Her fingers find the square coin at her throat and turn it once. | 4.0 |
| 20 | Black | | | Fade to black over 1.5 s; the chapter's page (`Chapter.Summary`) comes up out of it. | 1.5 |

Total, unaccused: about 2 minutes 2 s; accused, about 2 minutes 17 s (the
interruption, 11a, runs about 7 s; each
reading's line runs 6 to 12 s).

## Performance

**Vonnra** has no face rig. Carry her with stillness, the hands, the head and the
lamp. No contractions; long pauses; never hurried; she never answers yes or no
(`VOICES.md`).

- **The first readings.** She is a performer who has done this a thousand times:
  her thumb in the palm, her eyes on it, her voice level and low. It should be
  convincing. The player should half believe her for two readings.
- **What breaks the performance**, a little at a time:
  - the look east on the crates (shot 7), the first time her eyes leave the hand,
    and how easily they come back;
  - turning south for what came before the ford (shot 10). There she is reciting,
    not reading, and she does not notice that her thumb has stopped;
  - the interruption (shot 11a): in forty years nobody has seen her not finish a
    sentence, and nobody says so. She does not startle. She stops, the way a clerk
    stops when a figure will not add up, and looks at the hill as if it owed her
    money. That is the only fear she shows in Act 1, and it is not for herself:
    it is for her arrangement.
  - The player who notices sees where she looks. Nobody in the scene says so.
- **If accused**, the stillness becomes a different stillness: someone listening
  very hard. She lifts the lamp slowly. She breathes on its flame without meaning
  to: it is cold, and she is alive. "{name}" is the only word in the game she says
  with something like warmth, and it should frighten.
- **Alone**, she is a clerk. The fingertip on the line is unsentimental, as on any
  entry not yet settled.

**The survivor.**
- *Shots 2 to 4.* `brows_up` 0.1. She offers the wrong hand without thinking (that
  is all it is).
- *Readings.*
  - Her gaze is on Vonnra's face, not the hand (`Look` on Vonnra's eyes),
    `Wander` 0.08.
  - In shot 7, when Vonnra's eyes go over her shoulder, the survivor's gaze follows
    them for an instant (`Look` past the camera, 0.3 s), then comes back. She does
    not turn round.
  - React to what is read:
    - `brows_sad` 0.3 on the dead (the cages, Greymuzzle);
    - `smile` 0.1 on "Most people never learn the difference" (cured);
    - `brows_angry` 0.2 on the ledger with her name (Pell, ally);
    - if Sella's variant plays, a frown (0.3) builds across the reading of her own
      past: she told one person that, upstairs.
- *The accusation.* `brows_angry` 0.3, `mouth_open` 0; standing, still. In the
  lamp's light (14a, 14b) she does not squint, and does not look away.

## Lines

All the lines already exist (conversation `vonnra`), except the calling variants of
the first line, which this pass added:

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

`f_accuse`'s text in the data begins with a parenthesis for the text-only
conversation ("For the first time she looks at your face... the lamp gutters."):
that is shots 13a to 14b, and it is not spoken.

**The name.** `{name}` in a VO line is the survivor's name, and saying it is the
only answer Vonnra gives (`VOICES.md`). Three lines carry it: `vonnra.f_accuse`
("...Sit down, {name}. I have not finished reading."), `vonnra.f_door#0` ("That
is all I see for free, {name}. The rest...") and `vonnra.hub#0` ("{name}. Your
chapter is written."). Each is written so the name stands alone at a pause, and
is recorded so:
- **two takes, split at the name**, each ending or starting on the pause;
- **the name as its own take**, in her voice: one for each name the creation
  screen suggests, recorded with the cast; a name the player typed is read by
  the TTS voice at play time, or rendered per save;
- **the subtitle always carries the name.**

If there is no take for the name, the pause plays empty and the subtitle carries
it. Never substitute "traveller": she has stopped calling her that, and the
change is the point. (The voice-prep pass found the name lost in the plain
takes; this is the decision.)

*Casting:* Vonnra is in her 60s, clipped and unplaceable: a low alto with a little
air. It is the most important casting in the game.

## Sound

- **Music.** The `Mystery` mood, very low, from the hatch opening: its bell, slow,
  and a held pad.
  - The first two readings have no bell: only the pad, and the valley.
  - The interruption (11a): the pad cut dead on "hillside"; the lamp's glass
    ringing; the groan (C03's, the same recording, deeper and further off); the
    town below, very quiet; then the pad back, a semitone
    lower, under the choices.
  - From the turn (shot 7), each vista brings one bell note, and the table brings
    the pad back.
  - Under the accusation, everything goes but a single held low note; then nothing
    for "{name}".
  - The stinger: no music. The page, the pen, the wind. The bell once as the book
    closes. Silence for the fade.
- **Effects.**
  - Wind on the roof (constant, light); the town below (a door, a dog, a cart late
    home, the braziers).
  - The lamp's flame; cloth; rings on wood.
  - Valley sounds from behind the survivor: the howl (cured or allied), and the
    pump's distant hum if it runs.
  - Shot 14a: Vonnra's breath, close, and the flame's flutter from it.
  - Shot 18: the fingertip on paper; the pen (accused), very close.
  - The ledger closing; the coin turning on its cord.

## VFX

- The lamp's flame, leaning from Vonnra's breath and guttering in 14a.
- **Breath.** Vonnra's breath smokes in the cold all scene; the survivor's never
  does (it is night). It is visible in every two-shot, never framed for, until 14a
  frames it. Nobody remarks on it.
- The backdrop's distant lights, set by the facts.

## In, out, skip, subtitles

- **In.** On the choice: a fade to black over 0.8 s from wherever she is (the tower's
  door), and up on shot 1.
- **Out.** Into the chapter's page (the `fortune` action), then back into the
  Waystation at night by the tower's door.
- **Skip.** Page by page: a skip advances to the next reading (the readings are the
  point). A long hold skips to the choice at `f_below`, then to the page. The stinger
  plays even after a skip: it is 15 s, and it is the plant.
- **Subtitles.** Vonnra's lines under "Vonnra". The readings are long: break them at
  sentences, two lines at a time.

## What it needs

- **A roof on the toll tower:** a set with a lead roof, parapet, hatch, table,
  stools, lamp and ledger.
- **A backdrop of the valley** seen from the roof, with lights switched by the
  world's facts: the Dig's pump, the Roost's fires or smoke, the town's windows and
  the ford's road.
  - The Verge is another zone, so it cannot be rendered live from here. A panorama
    rendered offline from the Verge's own data, or painted, with light sprites on
    it, will do.
- **Two people at a table:** sitting on stools; hands held across a table (hand
  IK); a palm read with a thumb; a lamp lifted to a face; a head turned and held
  while the hands stay still.
- **Breath:** a breath plume that a lamp's flame can lean from (a small particle
  emitter at the mouth, and a flame that takes a push).
- **The ledger insert:** a page texture with twenty-seven lines in a small violet
  hand, twenty-six of them ruled through; a fingertip; a pen writing one word.
- **A coin on a cord**, turned in the fingers.
- **A name in a voiced line.**
