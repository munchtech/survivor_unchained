# C03 · The Heart Goes Down

**The Ford-Warden: defeat. Grimtunnel.** Priority 1 · Prologue · about 43 s · skippable

## What it does

The Warden goes down on his knees in the ford, and for the last seconds of his
long watch he is a man again: a tired voice under the giant's, asking the only
thing a man on a night watch wants to know. Is it morning. She nods (her first
mercy, to the thing that drowned her), and he lets his lamp into the water at
last. Out of the river where he fell rises his heart, a stone full of
cold light, and it drifts toward her as if it knows her. Up beside it out of the
mud comes a squat thing with a lamp strapped to its head, which snatches it out of
the air; but the light goes on straining out of his arms toward her, and he looks
from it to her, and sniffs, and for a moment stops grinning and very nearly bows.
Then he takes it down, promising it will be grateful. Under everything, the valley
groans, and every lamp along the road dips at once.

- **The Warden wants** to be relieved. **He reveals** that the monster was a man
  keeping a watch, and that the watch has been long.
- **Grimtunnel wants** the heart for his god, gleefully. **He hides** his faith
  under his greed, and it shows for a second (the near-bow) when the heart pulls
  toward her. **He reveals**, without meaning to, that she smells of the place he
  is digging toward.
- **She wants** the light that is reaching for her, and does not know why. **She
  loses** it.
- **Plants:** "Is it morning?" (the Order's word for its light: Chid's "Morning
  comes. It always has. I should know." answers it, and Act 3 says what their
  morning was); the heart reaching for her (Act 3: only the Morrow's own light can
  carry a heart); "You smell like downstairs" (Act 2's turn); the near-bow (ending
  C: Grimtunnel kneels); "ever so grateful" (paid in Act 1 by Vonnra's fortune,
  "they think it will be grateful", and in Act 3: "It isn't grateful. Why isn't it
  grateful?"); the groan and the dipping lamps: the chain's first break (the tremors
  of Act 1).
- **Pays:** C02 ("The lamp never touches the water": now it does; the trembling arm,
  let go).

## Trigger and facts

- Replaces the staging in `Prologue.OnWardenDown` / `RunVictory`: plays when the
  Warden dies.
- Reads: calling (shot 7's hand), background (the devout's sign in shot 3b).
- Sets: as `RunVictory` does now, in code, at the hand-back (`learn grimtunnel`,
  history `ford_warden_slain` and `core_stolen`, `give grimtunnels_lamp`), so a skip
  sets them too. The lamp-iron, shards and gold drop as now.

## Place, time, light

- **The Low Ford** (as C02). He falls where he dies; every mark below is relative to
  his body, W. (If he dies out of the water, on a bank, the scene plays there: the
  lamp goes into the nearest water if there is any within 3 m; otherwise it gutters
  out on the stones.)
- **Time:** the night's last minutes. Hold `Atmospheres.Night` until shot 11, then
  begin the blend toward `Dawn` under shot 12: the sky's lowest edge goes from black
  to the grey of a knife.
- **Light:** the posts are dark (the fight put them out). Only his lamp, then his
  heart, cold and very bright (`#bfe6ff`, the `Orb`), then the coming grey and
  Grimtunnel's small orange head-lamp.
- **Mood:** an execution that turns into a mercy, then a robbery.

## Cast and marks

- **The Warden** on his knees at W, facing her, lamp up in his left fist.
- **The survivor**: on the cut from shot 1 to shot 2 she is placed 4 m from W, facing
  him, if the fight left her further than 8 m away.
- **The heart** (`Orb`, `#bfe6ff`, 0.42) rises from the water at his chest.
- **Grimtunnel** (lampling, scale 1.9: squat, long-armed, a lamp strapped to his
  head and another hanging from his belt) bursts up beside the heart, a pace to its
  right, under her outstretched hand.

## Shot list

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 1 | MCU | 85 | Static on his head and shoulders; the blow at `WorldRate` 0.15 for 0.8 s | The last hit lands on his hood and helm (an impact keyed to the hit's school: a spray of sparks, frost, fire or splinters; no weapon in frame). The light in his eyes gutters. Cut on the impact. | 2.0 |
| 2 | MLS | 35 | Static, low at water level, from the south-west | He goes down on his knees in the river; the greatsword falls from his right hand and sinks. His left arm stays up, the lamp held clear of the water, steady. | 4.0 |
| 3 | CU | 85 | Static, up at him past the lamp | He looks at the lamp, not at her. Line W4, in another voice (see Lines). The arm begins to shake. | 4.0 |
| 3b | MCU | 50 | Static, on her, his lamp's light on her face | She looks at him, and nods: once, slowly. Yes. It is the first thing she gives anyone in the game, and she gives it to the thing that drowned her. *(Devout: after the nod, she closes her hand over her heart and opens it toward him, palm out: the Order's sign for the dead. Chid makes the same sign at Nell's grave, C08.)* | 2.5 |
| 4 | INSERT | 65 | Static | The fist lowers, and the lamp goes into the river. The flame hisses out in a puff of steam. Dark. | 2.5 |
| 5 | LS | 28 | Static, from behind her, low | He folds forward into the water and is still. The mist closes over him. A beat of nothing. Then the water over his chest lightens from beneath. | 4.0 |
| 6 | MS | 50 | Slow push in toward the light | The heart rises out of the water: a stone the size of a fist, full of cold light, turning slowly, water running off it. No line: its hum, and the river. | 4.0 |
| 7 | OTS | 50 | Over her shoulder | The heart drifts toward her, like a thing finding its way. Her hand comes up into frame (see Calling). | 3.5 |
| 8 | ECU | 100 | Static, side-on | Her fingertips and the heart, a hand's breadth apart. Its light leans toward her fingers like a flame in a draught. | 2.0 |
| 9 | MS | 35 | Static; a hard shake (0.6) on the burst | The mud bursts up under her hand: Grimtunnel, up to the waist, snatches the heart out of the air and hugs it to his chest. Line G1. | 3.0 |
| 10 | MS | 50 | Static, from her eye height, down at him | In his arms the heart's light goes on straining out toward her. He looks down at it; up at her; down at it. His head-lamp swings up into her face (a lamp to the face again, small and orange this time) and his head jerks twice: sniffing. Then he goes still, toad-still, and his head dips: a small duck, very nearly a bow. Line G2. Then his whole body shakes once with a laugh and he is grinning again. | 5.0 |
| 11 | MS | 35 | Static | Line G3, broken in the middle. He dives head first, still clutching the heart; the hole folds in behind him; through the churned mud the heart's light shows for a moment going down, then is gone. | 3.5 |
| 12 | ELS | 24 | Static, 10 m up over the north bank, 60 m east of the ford, looking west along the river | The ford small in the middle of the frame, her in it; the road's lamps either side of the river (lights 12, 13 and 14). Silence. Then, from under everything, a groan: long, deep, felt in the ground. The river shivers in rings. Every lamp in the frame dips at once, and comes back. The sky's lowest edge has gone grey. She looks down at her feet. | 5.0 |
| 13 | MS to play | 35 to play | Pull back and up into the follow camera | She stands in the ford with the dawn coming. Bars out. Control. | 2.0 |

Total: 45.0 s.

## Performance

**The Warden.** In shot 3 the giant becomes a man for a line: the head lowers, the
shoulders drop. He asks it of the lamp, the way a man on the last hour of a watch
asks the one coming to relieve him. The arm, which shook once in C02 and was
mastered, shakes now and is not. He sees her nod (shot 3b), and in shot 4 the arm lowers the way a man puts down
something he has carried a very long way. He dies like falling asleep in a chair.

**Grimtunnel** (no face rig; head, body and beam). Quick jerks and dead stillness
in between, like a toad. He hugs the heart like a stolen loaf. Shot 10 is his
character in five seconds: the beam going from the heart to her face and back, the
two sniffs (a jerk of the head and snout), the stillness, the duck of the head, the
laugh that shakes him back into himself. G3 breaks off where he would say "meat"
and cannot quite say it to her now.

**The survivor.**
- *Shot 3.* Gaze on the lamp (0, -0.5). `brows_up` 0.15. Her weapon lowers.
- *Shot 3b.* The nod: head down 8°, held 0.4 s, up. `brows_sad` 0.35, `mouth_open`
  0.05. Gaze on his face (0, -0.4). Mercy, not pity; she does not know why she
  gives it. (Devout: the sign, unhurried, a thing her hands know.)
- *Shots 6 to 8.* Gaze on the heart, following it (`Wander` 0.02). `eyes_wide` 0.3,
  `mouth_open` 0.12, `brows_sad` 0.15: wonder, and something like homesickness, with
  no idea why. She reaches without deciding to.
- *Shot 9.* A flinch back (the head 10 cm), `eyes_wide` 0.7, a blink on the burst.
- *Shot 10.* `squint` 0.5 against the head-lamp, `nose_wrinkle` 0.2 (he smells of
  the Dig). On G2, the squint eases, `brows_sad` 0.3. She heard it.
- *Shot 12.* Gaze down at her feet (0, 0.9). Nothing on the face: the wide shot and
  the groan carry it.

## Calling (shot 7: the reaching hand)

- *Warden:* the shield arm lowers; the bare hand reaches past its rim.
- *Reaver:* she lets the cleaver's head rest in the water and reaches with the free
  hand.
- *Arcanist:* the fire in her palm goes small and steady as the heart comes, the way
  a candle steadies when a door is shut.
- *Stalker:* she unnocks (or turns the knife away) to free the hand.

## Lines

Conversation `cin_heart_goes_down`.

| VO id | Shot | Speaker | Line | Note |
|---|---|---|---|---|
| `cin_heart_goes_down.morning` | 3 | `ford_warden` | Is it morning? | **Not the giant's voice.** A man's: tired, sixty, no reverb, no boom, the accent worn off it. He asks it of the lamp. Quietly enough that the subtitle is the only certain thing. |
| `cin_heart_goes_down.nobodys` | 9 | `grimtunnel` | Ooh, still lit! Nobody's, is it? Nobody's! | Delight, a child's at a pie. |
| `cin_heart_goes_down.downstairs` | 10 | `grimtunnel` | ...You smell like downstairs. | The glee gone; curious; a sniff before it. Then the laugh in the breath after. |
| `cin_heart_goes_down.grateful` | 11 | `grimtunnel` | Finders keepers, surface-m— (a sniff) ...Downstairs'll be ever so grateful. | Half over his shoulder as he dives. He cannot finish "meat" at her. |

*Casting:* Grimtunnel is Snib's family, bigger and lower, a cackle in the throat,
a cave reverb that gets wetter as he goes down.

## Sound

- **Music.** The boss music stops dead on the killing blow, into a ringing silence (a
  high soft tone fading). Shot 3: nothing. Shot 6: the lamp motif (C02's bell) and a
  high glassy pad swelling as the heart rises and leans toward her, rising a semitone
  as it nears her hand; cut on the burst. Shot 12: silence 1.5 s, the groan, silence;
  a few bars of the `Night` flute, very low, only as the bars go out.
- **Effects.** The blow (heavy, wet, armour). Knees into water; the sword sinking (a
  long bubble). The lamp's hiss. The heart's hum (a wet finger round a glass rim),
  louder as it nears her. The burst: a wet explosion of earth and gravel, stones
  rattling on her. Two piggy sniffs. The laugh. His dive: earth folding, a scrabble
  going down, his cackle going down a well. The groan: below hearing first (felt;
  rumble on a pad), then a long deep sound like timber taking a load, 3 s, the
  river's rings ticking on the stones.

## VFX

- Slow motion on the blow; the impact on the helm by school.
- The lamp's steam going under.
- The heart (`Orb`): bright, cold, turning, water streaming off it; its glow drawn
  out toward her hand in shot 8, and toward her again out of Grimtunnel's arms in
  shot 10.
- The burst (mud, gravel, river spray); his head-lamp; the heart's glow through the
  mud going down.
- Shot 12: lights 12, 13 and 14 dip together for 0.6 s; the river's rings.
- The grey edge of the sky (the `Dawn` blend starting).

## In, out, skip, subtitles

- **In.** On the killing blow: bars in over 0.4 s (it is already happening). The boss
  bar off; the announcement "The Ford-Warden falls" moves to the end of shot 5, small.
- **Out.** As `RunVictory`'s end: the lore toast ("Grimtunnel took the Warden's heart"),
  `Stage.Dawn` and the gate opening. Grimtunnel's spare lamp lies in the mud where he
  went down, lit, to be found in play. C04 follows.
- **Skip.** Lands on the hand-back state.
- **Subtitles.** W4 under "The Ford-Warden" (the player should see whose voice it was,
  even if they don't hear it as his).

## What it needs

The Warden kneeling in water, a forward fall, an arm lowered; his eye-lights dimming
to nothing; his lamp's flame going out with steam. Grimtunnel bursting up
waist-deep (the burrow style is close), a snatch, two sniffs, a duck of the head, a
head-first dive. The heart's light drawn toward a point. A valley-wide dip of chosen
lights. Pad rumble.
