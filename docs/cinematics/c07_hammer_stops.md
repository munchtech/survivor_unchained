# C07 · The Hammer Stops

**Brannoc asks after his daughter.** Priority 1 · Act 1 · about 45 to 80 s by
answer · skippable (the choices still come)

## What it does

The smith who never asks anything asks one thing, without looking up from the
anvil: did she pass a carter on the Low Ford road, a girl with him, twelve, red
hair, new boots. The survivor knows the answer; she put that girl down in the
ditch two nights ago. The scene is a man hammering, and the question of whether
the hammer stops.

- **Brannoc wants** to hear that Nell is safe at Low Kiln, and he knows he
  won't. **He hides** that he already half knows (Wat should have sent word; the
  ford's been bad all year; and his irons went to that ford). **He changes**: if
  told, he stops hammering, which he has never done in front of anyone; if lied
  to, he hammers on.
- **She wants**, perhaps, to spare him; perhaps to tell him. **The choice costs**
  either way: the truth takes his daughter from him in front of her; the lie
  sends him to the gate every morning to ask strangers, until Act 2 tells him
  and tells him who lied.
- **Plants:** the two lamp-irons on the rack behind him (Act 2: the hooded
  buyer); his mark (if she has shown him the Warden's lamp-iron, he looks at the
  rack); "Was it quick?" (Act 2: Brannoc and the dead who get up).
- **Pays:** the prologue's ambush ("The one with the reins was a girl, twelve at
  most: red hair under the weed, and new boots"); the folk line about the
  quietest forge in the valley; Brannoc's "Should've."

## Trigger and facts

- Stages Brannoc's conversation entry `nell` (met Brannoc, day 2 or later, not
  at night, not yet asked): plays when she talks to him or comes within 4 m of
  him while it holds. (It must catch her at the anvil, not at the door: if she
  "Visits" the smithy's door, he comes out to the anvil first.)
- Reads: `brannoc.saw_iron` (shot 9's look at the rack).
- Sets: as the conversation does (`nell.told`, `asked_nell`, `lamps/nell`, the
  history, the later effect). Answering is what marks it asked; walking away
  before answering lets him ask again another day.

## Place, time, light

- **The Waystation, Brannoc's smithy**, the open front of the forge on the east
  side of the south road: the anvil at (11.6, 14.6) with Brannoc behind it facing
  west across it (heading -pi/2); the forge's hearth glowing behind him at
  (13.4, 14.2); on the wall left of the door (12.3, 12) a rack with two black
  lamp-irons hanging from hooks.
- **Time:** day, morning or afternoon (the forge is lit).
- **Light:** daylight from the road (west) on his front; the hearth's orange
  from behind him rimming his shoulders and his cropped head; sparks on
  every strike. When the hammer stops, the forge's glow keeps going: it is the
  only thing in the shot still moving.
- **Mood:** work. Then the absence of work.

## Cast and marks

- **Brannoc**, stripped to the waist (his outfit: peasant legs and feet, a
  leather apron added for this scene), at the anvil, hammering a bar with the
  mace he uses as a hammer, short strokes (`1H_Melee_Attack_Chop` at 0.55
  speed, his idle).
- **The survivor** comes up the road and stops across the anvil from him at
  (9.8, 14.6), facing east (heading pi/2).
- **The street:** two townsfolk passing behind her on the road, out of focus,
  who matter only in shot 12.

## Shot list (the question)

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 1 | INSERT | 85 | Static, low beside the anvil | The hammer coming down on hot iron: sparks; again. The rhythm the whole town hears every day. | 3.0 |
| 2 | MS | 50 | Static, from behind her shoulder, low | Brannoc across the anvil, head down, working. He does not look up. The rack with the two irons is in frame left, in shadow. Line `brannoc.nell` begins, in time with the strokes: one phrase between blows, five phrases (to "...by dark."). | 13.0 |
| 3 | CU | 85 | Static, from the hearth side, on his hands and the iron | His hands and the hammer; the iron going from yellow to orange. "Girl with him." Stroke. "Twelve." Stroke. "Red hair." Stroke. "New boots." Stroke. | 5.0 |
| 4 | MLS | 35 | Static, side-on, both of them, the anvil between | "Going to her aunt at Low Kiln." The hammer comes up for the next stroke and stays up. | 3.0 |
| 5 | MCU | 50 | Static, on her | The hammer's sound has stopped. The forge roars softly in the quiet. She looks at him. (She knows the girl. Let the player know she knows.) | 3.0 |
| 6 | MS | 50 | Static, on him, from her side, his face in shadow under the hearth's rim-light | "Mine. Nell." The hammer is still raised. "...You pass them?" The choices come up. Hold: the iron on the anvil is losing its colour. | 4.0 + choice |

### By her answer

**"There was a wagon on its side, south of the ford. A girl had the reins."**
(`brannoc.nell_ditch`, then the second answer.)

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 7 | INSERT | 65 | Static | He lays the hammer down on the anvil, beside the cooling iron. Very carefully. | 3.0 |
| 8 | MS | 50 | Static, from her side | Line `brannoc.nell_ditch`. He stands with his hands flat on the anvil's face, as if holding it down. | 6.0 |
| 9 | LS | 35 | Slow push in, from the road | *(If `brannoc.saw_iron`: before he speaks he turns his head and looks at the two irons on the rack, a long look, and then looks at nothing.)* The forge, the man, the anvil, the street behind. The second choice comes up. | 4.0 + choice |
| 10a | MCU | 85 | Static, on her, then on him (cut on his line) | *"She was gone before I came. The water took her."* Line `brannoc.nell_gone`: he picks the hammer up and holds it, and doesn't use it. | 6.0 |
| 10b | CU | 85 | Static, low, up at him: the one close shot of his face, half in the hearth's light, eyes catching it | *"She'd got up with the others. I put her down."* He looks at her properly, for the first time. Silence. (The close-up is for the look, not for a line: he has no face rig yet.) | 2.5 |
| 10c | MS | 50 | Static, from her side | Line `brannoc.nell_risen`: "Got up. ...Got up, and you put her down. ...Was it quick?" Choice. | 5.0 + choice |
| 11b | MS | 50 | Static, on him | *"It was quick."*: Line `brannoc.nell_quick`. "...Thank you." The forge ticking as it cools. *"It wasn't."*: Line `brannoc.nell_slow`: he nods once, as at a price. | 5.0 |
| 12 | LS | 28 | Static, from across the road, wide | She goes. He stays at the anvil with the hammer down, not working. The forge glows. Behind her, as she walks out of frame, two townsfolk passing in the road slow, and stop, and look toward the smithy: the hammer has stopped, and in this town that is news. | 6.0 |

**"I passed nobody on that road."** (`brannoc.nell_lie`.)

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 7c | MS | 50 | Static, from her side | The hammer comes down. Line `brannoc.nell_lie` between strokes: "Low Kiln, then. Good." Stroke. "Aunt'll feed her up." Stroke. "She's thin." | 6.0 |
| 8c | LS | 28 | Static, from across the road | She walks away. The hammer keeps time behind her all the way out of frame, steady as ever. The townsfolk pass without looking. | 5.0 |

**"I didn't look at the dead."** (`brannoc.nell_look`.)

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 7d | MCU | 85 | Static, on him | "Didn't look." The hammer comes down. "No." Stroke. "...Nobody looks." He does not look at her either. | 5.0 |
| 8d | LS | 28 | As 8c | As 8c. | 5.0 |

## Performance

**Brannoc.** The fewest words in town (`VOICES.md`): every line is fragments
with the hammer between them, and the hammer is how he breathes. He asks the
question the way he would quote a price, flat, to the iron. "Mine." is the only
word with weight on it, and only a little; he puts the weight on "Nell" by
saying it quieter. When he lays the hammer down it is the most violent thing
he does in the game. "Was it quick?" is asked like a smith asking whether a
weld held. "Thank you" (the only time he says it) comes after a long silence
and lands on nothing: he says it to the anvil.

**The survivor.**
- *Shots 2 to 4.* Gaze on his hands and the hammer (−0.1, 0.3); on "Red hair"
  her gaze stops moving (`Wander` 0). On "New boots" `brows_sad` begins, 0 to
  0.4 over 2 s. She remembers the ditch.
- *Shot 5.* `brows_sad` 0.5, `mouth_open` 0.06, eyes on his face; a slow
  blink. She is deciding, and the player is deciding with her.
- *10a / 10b / 10c.* On her answer she holds his gaze (he is not looking; she looks at
  him anyway). For "I put her down": `frown` 0.2, jaw set, no tears. For
  "It was quick" or "It wasn't": the truth or the kindness should be readable
  only from whether she looks away (`It was quick`: gaze stays on him;
  `It wasn't`: gaze drops (0, 0.6), then comes back).
- *7c.* The lie: she looks at the iron, not at him (0.2, 0.5). Nothing else
  gives her away.

## Lines

All existing, conversation `brannoc` (*casting:* 50, Cornish, deep and slow):
`brannoc.nell`, `brannoc.nell_ditch` (#0 when he has seen his mark on the
lamp-iron, #1 otherwise), `brannoc.nell_gone`, `brannoc.nell_risen`,
`brannoc.nell_quick`, `brannoc.nell_slow`, `brannoc.nell_lie`, `brannoc.nell_look`.
The parentheses in those lines are stage directions: nobody speaks them. Every
one of them is in the picture (the hammer laid down in shot 7 is "You have
never seen him put the hammer down"), so the cinematic needs no narrator at
all.

VO direction for the long first line: record it as phrases with gaps of about
1.2 s, cut to the strokes in shots 2 to 4: "You came up the Low Ford road." /
"...Carter went south a fortnight back." / "Wat, with the grey mare." / "Toll
work." / "Said he'd be over the ford by dark." / "Girl with him." / "Twelve." /
"Red hair." / "New boots." / "Going to her aunt at Low Kiln." / [the hammer
stops] / "Mine. Nell." / "...You pass them?"

## Sound

- **Music.** None. The hammer is the score: a strike every 1.2 s, ringing
  (anvil ring, a little different each time), with the forge's breath under it.
  When the hammer stops (shot 4) everything else in the mix drops 6 dB for
  three seconds and comes back slowly: the town, the street, a cart; the forge
  louder now that nothing covers it. In the truth endings, a single low cello
  note enters under shot 12 and holds to the end. In the lie and the evasion,
  no music at all: the hammer carries her out.
- **Effects.** Hammer on hot iron; sparks; the iron hissing as it cools on the
  anvil (louder as the scene goes on); the forge's roar and its tick as it cools;
  the hammer laid down (a soft iron clunk); the street's sounds coming back in
  shot 12; the two townsfolk's footsteps stopping.

## VFX

- Sparks on every strike; the bar on the anvil cooling from yellow through
  orange to grey across the scene (it is the scene's clock if the hammer stops).
- Heat shimmer over the hearth.

## In, out, skip, subtitles

- **In.** Bars in; the street's folk keep walking (they matter in 12).
- **Out.** Bars out on the last shot; Brannoc stays at the anvil not working (if
  told), his idle swapped to a still stand for the rest of the day (`Idle` with
  the hammer resting on the anvil), or hammering (if lied to). The next morning
  the burial (C08) if told.
- **Skip.** Skips to the next choice; after the last, to the end state.
- **Subtitles.** Brannoc's lines under "Brannoc", broken where he breaks them.

## What it needs

The anvil and the hearth at the smithy's front, and the rack with two black
lamp-irons (visible all through Act 1); Brannoc in an apron; his hammering idle
cut to a rhythm the VO can be timed to; laying a hammer down; standing with
both hands on the anvil; his head turned to the rack; the bar on the anvil as a
prop with a cooling colour; a still stand at the anvil for the rest of the day;
townsfolk who can be told to stop and look. One close-up of his face, silent (shot 10b)
needs at least a lit face that can hold a look: even without a rig, his eyes
catching the hearth will do.
