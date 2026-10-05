# C11 · Raid on the Roost

**Redcowl: arrival, and death or the spared ending.** Priority 3 · Act 1,
optional (the Missing Caravan by force) · arrival 10 s, death 17 s, spared
about 20 s · skippable

**The owner, 4 October:** the fight ends on her choice at his knee, "Spare
him" or "Finish it". The death below plays only if she finishes it. The spared
ending is its own part, after the death part.

## What it does

The night raid on the Roost (`roost_raid`). At the half hour Redcowl comes out
of the dark himself, hood back, the greataxe over his shoulder, laughing, and
tells her that his children are asleep behind him. When he falls he goes down
on one knee and laughs again, wet, and says one last thing. If she ever said
"Ashford" to his face, it is that word, and a laugh: he told her she could say it
once in his camp, and now he has said it too, and they are square. If not, it is
a message for his brother, about a leg.

- **Redcowl wants** to stand between her and forty-one mouths, and to die
  laughing if he has to. **He hides** Ashford to the end, unless she already
  said it. **He reveals**, with his last breath, either the town or the brother.
- **She wants** the cages open and the camp broken. **She pays** Rav (his
  brother), and the children asleep behind the line.
- **Pays:** C06 (the children, the standard); `redcowl.ashford` ("You get to say
  that once in my camp. You've said it."); Rav's "Redcowl owes Rav a leg" (`rav.roost`) and the sewn-on leg
  (`rav.redcowl`). **Plants:** the message carried to Rav
  (`rav.cb_killed_redcowl`, a new choice: "He said to tell you the leg held.").

## Trigger and facts

- **Arrival:** the boss's arrival in `roost_raid`, as his ground opens after
  the levy (combat's `STORY_BOSSES.md` §2). On a rise, a two-second re-entry
  (the laugh) plays instead.
- **The knee:** spent, he goes down on one knee with the axe-head in the dirt
  and laughs. That is gameplay, with no line. Two prompts wait at his side
  with no clock: "Spare him" and "Finish it".
- **Death** ("Finish it"): the death part below.
- **Spared** ("Spare him"): the spared part below. The choice's outcome is
  applied first (`redcowl` = `spared`), and the conversation's entry plays
  `spared` from then on.
- Reads: `redcowl.ashford_said` (his last line, or his spared line), sex (lad
  or lass).
- Sets, death: `redcowl.last_words` = `"ashford"` or `"leg"` (on its
  conversation's last node, so a skip sets it too). Rav reads it.
- Sets, spared: nothing of its own. The prompt's `OnSpare` sets `redcowl` =
  `spared` and `roost.cleared` (`docs/WRITING_PASS.md` §22.1).

## Place, time, light

The arena (people `kerchiefs`, theme `wood`), staged from wherever he spawns.
Night; the Kerchiefs' torches give firelight from low and to the side; the moon
cold above.

## Arrival

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 1 | LS | 28 | Static, low, from behind her | The Kerchiefs in the horde hold their ground and part, torches up. Through them, unhurried, a big man in a red hood thrown back, the greataxe over his shoulder. `WorldRate` 0.3. | 3.5 |
| 2 | MS | 50 | Handheld (0.3), slightly low | He stops. Laughs: "Ha! HA." Line R1. On "Mind where you swing" the laugh is gone from his face and his voice. | 4.5 |
| 3 | MCU | 35 | Handheld (0.5) | He brings the axe down off his shoulder into both hands. Title: **REDCOWL** / *Of the Kerchiefs*. Play. | 2.0 |

## Death

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 1 | MS | 50 | Static, low; `WorldRate` 0.2 on the blow | The blow; he goes down on one knee, the axe-head in the dirt, both hands on its haft. The Kerchiefs still standing lower their weapons and step back. | 3.5 |
| 2 | MCU | 50 | Static, at his kneeling eye-height | He laughs, and it costs him; blood at his mouth (a dark line on the beard). He looks up at her. | 3.0 |
| 3 | MS | 50 | Static, at his kneeling eye-height, a little closer than 2 | His last line (R2 or R3), said up at her. (A medium shot: he has no face rig, so the line is carried by the head, the shoulders and the hands on the haft.) | 4.5 |
| 4 | MS | 50 | Static | He lets go of the axe's haft and sits back on his heels and is still. The hood has fallen; there is grey in the beard. A torch burns down beside him. | 4.0 |
| 5 | to the reckoning | | | Into the reckoning. | 1.5 |

With the choice, shot 1's blow is hers to give: he is already on his knee
when the prompts come, and "Finish it" is the blow. Shots 2 to 5 follow as
written.

## Spared

She has chosen "Spare him". He is on one knee, the axe-head in the dirt, both
hands on its haft. His people stand round with their torches.

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 1 | MS | 50 | Static, at his kneeling eye-height | She lowers her weapon. He looks up at her, and the laugh comes back into his face before his voice: it costs him. | 3.0 |
| 2 | MCU | 50 | Static, a little closer | His spared line (R4 or R5), said up at her as an equal. | 6.0 |
| 3 | MS | 35 | Slow push in, low | He gets the sewn leg under him and stands on it. It holds; he does not let it show that it might not. He pulls the axe out of the dirt and puts it over his shoulder, as he came in. | 4.0 |
| 4 | MS | 50 | Static, from behind her | "We'll be off your road by light." (R6), cold, to her. Then he turns to the camp, and the big voice comes back: "Up, my lot! Boots on! We're flitting!" | 4.5 |
| 5 | LS | 28 | Static, from behind her, low | His people part for him, as they did on his arrival, and he walks back through them, and does not limp until he is past the fires. Behind the carts a lamp goes up; a woman's voice, low, waking the children. | 4.0 |
| 6 | to the reckoning | | | Into the reckoning (its last line, `EndSpared`, says the same thing in words). | 1.5 |

## Lines

Conversation `cin_raid_on_the_roost`, speaker `redcowl`. *Casting:* 40s, hard
Scots, a big chest voice that laughs before it threatens.

| VO id | When | Line | Note |
|---|---|---|---|
| `cin_raid_on_the_roost.bairns#0` (to a woman) | Arrival, shot 2 | Ha! HA. At night, lass. With my bairns asleep behind me. ...Mind where you swing. | Laugh, then cold on the last four words. |
| `cin_raid_on_the_roost.bairns#1` | Arrival, shot 2 | Ha! HA. At night, lad. With my bairns asleep behind me. ...Mind where you swing. | |
| `cin_raid_on_the_roost.last#0` (`redcowl.ashford_said`) | Death, shot 3 | ...Ashford. *(a laugh)* There. Now we've both said it. | The word he never says, once, to the one who said it to him: quietly, like a man telling you where he's from. Then the laugh, which costs him, and the rest as a joke between equals. It pays "You get to say that once in my camp." |
| `cin_raid_on_the_roost.last#1` | Death, shot 3 | Tell the saw-bones... the leg held. | A joke, nearly. He means more than the leg. |
| `cin_raid_on_the_roost.spared#0`, `#1` (`redcowl.ashford_said`; lass, lad) | Spared, shot 2 (R4) | (a laugh, and it costs him) Ha! ...You said a word in my camp once, and I let you. Now you've let me. That's us square, lass. ...Near enough. | He never says the word: that is spent dying. "Near enough" is the joke and the debt both. |
| `cin_raid_on_the_roost.spared#2`, `#3` (lass, lad) | Spared, shot 2 (R5) | (a laugh, and it costs him) Ha! ...You minded where you swung. That's two I owe, then, lass. The saw-bones a leg, and you the rest of me. | Pays "Mind where you swing". Amused, proud, and owing; the brother is inside "the saw-bones", unsaid. |
| `cin_raid_on_the_roost.flit` | Spared, shot 4 (R6) | (cold, to her) We'll be off your road by light. (to the camp, the big voice back) Up, my lot! Boots on! We're flitting! | Cold on the first sentence, the host again on the rest: his rally from the fight. A flitting is a move made by night. |

And Rav, afterwards (`rav.cb_killed_redcowl`, new choice, shown when
`redcowl.last_words` is `"leg"`):

| VO id | Line |
|---|---|
| (choice, unvoiced) | He said to tell you: the leg held. |
| `rav.leg_held` | (He puts the cup down, very carefully, as if it were full.) ...Did he. (A long time.) Course it held. I'm a good doctor. ...Go on, pal. Come back tomorrow. |

And Rav, if he lives (`rav.cb_spared_redcowl`, new): two cups poured before
she reaches his table. "Good work, that leg. Whoever did it. ...That one
doesn't go on the slate, pal." Told "two he owes" (`rav.owes_two`): "He's a
terrible payer. Always was."

## Performance

**Redcowl.** He walks into the fight like into his own camp: a host. The
laugh is the bait; "Mind where you swing" is the hook, flat and quiet, eyes on
hers. Dying, he is amused that it has come to this, and furious, and too proud
to show the second. His last line is said up at her, not to the sky. Spared,
he is amused that it has come to this, and owing, and too proud to show that
either; he stands on the leg as if it had never been off.

**The survivor.** *Arrival:* `brows_angry` 0.35. On "bairns", the brows ease
(0.15) for a beat, and come back. *Death:* `brows_sad` 0.25; she does not lower
her weapon until he has stopped.

## Sound

- **Music.** Arrival: the horde music ducked; the `Boss` mood in on the axe
  coming down. Death: music cut on the blow; the torches, the wind, his
  breathing; after his last line, silence; then, far off behind the arena's
  edge, the Roost's kitchen: a ladle knocks once on the rim of a pot, and stops.
- **Effects.** Torches; the axe's weight; his laugh (big, then wet); the axe-head
  into dirt; the torch burning down.

## VFX

Torchlight; slow motion on the blow; a line of blood at his mouth; breath-smoke
on him (night, cold), none on her.

## In, out, skip, subtitles

As C10. Subtitles under "Redcowl".

## What it needs

The horde's Kerchiefs told to part and to stand down; Redcowl as one model
(the greataxe; see the README); a laugh; a kneel on one knee leaning on a
weapon; sitting back on the heels; a child's cry off-screen. Spared: getting
up from the kneel onto one leg, the axe pulled from the dirt and shouldered,
and a walk away that does not limp.
