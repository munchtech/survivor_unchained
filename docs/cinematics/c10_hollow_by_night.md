# C10 · The Hollow by Night

**Greymuzzle, hunted: arrival and death.** Priority 3 · Act 1, optional (the
Beast Problem's killing road) · arrival 9 s, death 16 s · skippable

## What it does

The night's story fight in the Pack's own Hollow (`hollow_by_night`). At the
half hour the wolves of the horde break off and back away into a ring, and the
old wolf walks out to her alone. When he falls, he lies on his side breathing
hard, and looks at her, and then past her, at the mouth of his den, where his
sick are lying; and stops. Nobody speaks. If she knelt to him once and promised,
he does not look away from her.

- **Greymuzzle wants** to die on his feet, in his own place, and he does not
  get to. What he thinks of last is not her and not himself: it is the den, and
  the ones in it who cannot get up. **He reveals** that he remembers her (if she
  promised): then she is the last thing he looks at, and the player knows what
  that look is asking.
- **She wants** the bounty, or the road safe, or the thing over. **She pays**:
  Maeca (`maeca.gone`, "You went to his house. In the dark."), the Pack, the
  promise if she made one.
- **Pays:** C05 (the kneeling; the sick wolves in the dirt that do not get up;
  the promise).

## Trigger and facts

- **Arrival:** the arena's boss spawn (30 minutes) in `hollow_by_night`.
- **Death:** the boss's death in that arena, before the win's reckoning.
- Reads: `promise.pack` (his look), calling (nothing changes), the arena's own
  ground.
- Sets nothing (the arena's `OnWin` sets `greymuzzle` dead and the rest).

## Place, time, light

The arena (`Arena`, people `pack`, theme `wood`): wherever the boss spawns,
the stinger is staged from him. Night, moon high: cold white light, long
shadows, the ember's red on her.

## Arrival

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 1 | LS | 35 | Static, low, from behind her | The horde's wolves stop attacking at once and back off her, low, into a ring 12 m wide, eyes on something behind the ring. `WorldRate` 0.3. | 3.0 |
| 2 | MS | 85 | Static, low, on the ring's far side | The ring opens. Greymuzzle walks through it, slow, grey to the eyes, his breath smoking in the moonlight. He stops and looks at her. *(If she promised:)* he looks for a long moment, and his head lowers, not to attack. | 3.5 |
| 3 | MCU | 50 | Handheld (0.3) | He lifts his head and howls; the ring howls with him; the ring closes. Title: **GREYMUZZLE** / *Who Kept the Cold Off*. Back to `WorldRate` 1 and play. | 2.5 |

## Death

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 1 | MS | 50 | Static, low; `WorldRate` 0.2 on the blow, then 1 | The last blow; his legs go; he goes down on his side. The rest of the horde stops where it is and lies down. | 3.0 |
| 2 | CU | 100 | Static, at ground level, on his head | He breathes hard, his breath smoking. His eye finds her. | 3.0 |
| 3 | MCU | 50 | Static, on her, low, from his eye-line | She stands over him with her weapon down; the ember's light on her. Her breath does not smoke; his does. | 3.0 |
| 4 | CU | 100 | As 2 | His eye leaves her and goes past her, to the den: a black mouth under the roots at the Hollow's edge (the arena's set dressing; behind her, out of focus). It stays there. *(If she promised:* his eye does not leave her.*)* The breathing stops. The smoke from his muzzle thins and stops. | 4.0 |
| 4a | LS | 50 | Static, past his head toward the den | *(Not if she promised.)* The den's mouth in the moonlight. Nothing comes out of it. | 2.0 |
| 5 | to the reckoning | | | The arena's way out opens; the win's reckoning comes up. | 1.0 |

## Performance

**Greymuzzle.** Old and certain; he limps a little on the left fore. Dying, he
does not whine. The look past her is the most important beat: not a vision,
not the sky; the den, and the sick in it, and who will see to them now. It is
the same look he gave the den in C05 before he let her in. If she promised, he
does not spend it on the den: he spends it on her, and that is worse.

**The survivor.** *Arrival:* `brows_angry` 0.3, gaze on him. *Death, shot 3:*
`brows_sad` 0.3, `mouth_open` 0.05; weapon lowered (the arms' idle, low).
*If she promised:* `brows_sad` 0.6, and she looks away first.

## Sound

- **Music.** Arrival: the horde music drops out under the ring forming; on the
  howl, the `Boss` mood in on the downbeat. Death: the boss music cut on the
  last blow; nothing but his breathing, the wind, and the horde's wolves
  whining low; a single flute note (the `Night` mood's) when his breathing stops.
- **Effects.** Paws; the ring's low growl; the howl (old, cracking at the top,
  answered); his breathing, close; the last breath. In 4a, from the den, a thin
  whine, once, that nobody answers.

## VFX

Breath-smoke on him (moonlit), none on her. The ember's light on her. Slow motion
on the blow.

## In, out, skip, subtitles

- **In.** No bars for the arrival (it is mid-fight: a slowed world and a title
  are enough); bars in for the death.
- **Out.** Arrival: straight back into the fight. Death: into the reckoning.
- **Skip.** Either can be skipped at once.
- **Subtitles.** None (no lines).

## What it needs

The horde told to back off into a ring (an arena-director hook); a wolf's slow
walk and a howl; a wolf lying on its side breathing (an additive breath on the
ribs); breath-smoke on wolves at night; the death's head-turn; a den's mouth (a
set piece placed at the arena's edge behind her when the boss falls).
