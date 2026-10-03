# C11 · Raid on the Roost

**Redcowl: arrival and death.** Priority 3 · Act 1, optional (the Missing
Caravan by force) · arrival 10 s, death 17 s · skippable

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

- **Arrival:** the boss spawn (30 minutes) in `roost_raid`.
- **Death:** the boss's death in that arena.
- Reads: `redcowl.ashford_said` (his last line), sex (lad or lass).
- Sets: `redcowl.last_words` = `"ashford"` or `"leg"` (on its conversation's
  last node, so a skip sets it too). Rav reads it.

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

## Lines

Conversation `cin_raid_on_the_roost`, speaker `redcowl`. *Casting:* 40s, hard
Scots, a big chest voice that laughs before it threatens.

| VO id | When | Line | Note |
|---|---|---|---|
| `cin_raid_on_the_roost.bairns#0` (to a woman) | Arrival, shot 2 | Ha! HA. At night, lass. With my bairns asleep behind me. ...Mind where you swing. | Laugh, then cold on the last four words. |
| `cin_raid_on_the_roost.bairns#1` | Arrival, shot 2 | Ha! HA. At night, lad. With my bairns asleep behind me. ...Mind where you swing. | |
| `cin_raid_on_the_roost.last#0` (`redcowl.ashford_said`) | Death, shot 3 | ...Ashford. *(a laugh)* There. Now we've both said it. | The word he never says, once, to the one who said it to him: quietly, like a man telling you where he's from. Then the laugh, which costs him, and the rest as a joke between equals. It pays "You get to say that once in my camp." |
| `cin_raid_on_the_roost.last#1` | Death, shot 3 | Tell the saw-bones... the leg held. | A joke, nearly. He means more than the leg. |

And Rav, afterwards (`rav.cb_killed_redcowl`, new choice, shown when
`redcowl.last_words` is `"leg"`):

| VO id | Line |
|---|---|
| (choice, unvoiced) | He said to tell you: the leg held. |
| `rav.leg_held` | (He puts the cup down, very carefully, as if it were full.) ...Did he. (A long time.) Course it held. I'm a good doctor. ...Go on, pal. Come back tomorrow. |

## Performance

**Redcowl.** He walks into the fight like into his own camp: a host. The
laugh is the bait; "Mind where you swing" is the hook, flat and quiet, eyes on
hers. Dying, he is amused that it has come to this, and furious, and too proud
to show the second. His last line is said up at her, not to the sky.

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
weapon; sitting back on the heels; a child's cry off-screen.
