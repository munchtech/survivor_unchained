# M3 bands: the press, the falls and the marks (round 2, 9 Nov)

Commands (from the worktree root):
- Low Ford: `dotnet run -c Release --project godot/balance -- zone --zone lowford --bots standing,idler,human,deft --seeds 16 --tiers 1,2,3` (add `--fullby 1` for Resolve-at-max by stage and distance to the Ford-Warden). Each run line now carries the fall notes (`FALL ...`: the last 5 s of blows, life, presses, marks), lowest life, damage taken by source, healing by source and the kit's blows caught/missed.
- Veteran (owed, not run this round): `... -- map --callings warden --level 30 --people dead,pack --grant cleaver:8,groundbreaker:8,heroic_leap:8,shield_charge:8,iron_vow:8,watch_bell:8 --grant-union bladestorm --bots standing,idler,human,deft --seeds 8 --tiers 3,4`. Without `--callings warden` it runs every calling (512 maps); with `--people all` 16 mixes.

## What changed (file, field, old -> new, why)
| where | what | old -> new | why |
|---|---|---|---|
| logic/Sim/Weapons.cs, resolve.json `selfAt` | a kindled spender whose key heaves (Groundbreaker, the Disc) fires itself | at its cost (40) -> only when Resolve is full, spending all of it | the press matters (decided) |
| Weapons.cs BaseCooldown | that spender's wait while Resolve pays | kindled cooldown 5 s -> its record's wait 0.5 s | the cost is the gate, as for the pressed form |
| WeaponInst.Relooking | the kindled look-again (Timer 0.1 when its condition fails) | blocked the key -> does not | sim bug: the key could never heave at a lone boss |
| PressPlan.cs | kindled "now" spender | pressed only at full -> pressed on its condition with the whole cost, and at full at the nearest foe if no pack | the plan presses as soon as she can pay |
| Battle.EnemyBlow `OwnMark`, Prologue.cs | the Ford-Warden's cleave and charge lane | bare Ev.Telegraph + HurtPlayer -> marked Battle blows (his own marks and burst unchanged) | sim fault: no hands could read them |
| teeth.json prologue.fordWarden `cleave` | his cleave's damage | 1 -> 2.5 | a stander eats it, a mover steps out |
| world_tiers.json `kit` I/II/III/IV | kit damage (share of her life) | 0.85/1/1.15/1.3 -> 2.0/2.0/1.8/2.0 | the marks kill a stander |
| world_tiers.json `kitEvery` (new) I/II/III/IV | waits of champions' affixes and packs' tells in story fights | 1 -> 0.4/0.4/0.5/0.45 | the zone cast only 4-8 kit blows a run |
| balance Pilot (campaign only) | engage distance | to a foe's center (1.8 m, inside the Warden's 2.3 m touch) -> to its edge | plan fault: human 50-72 s of the boss fight in his touch |
| balance ZoneSim | boss stage | the lamp as `onward` (dropped near a foe) -> as `goal`; stander/idler in-reach to a foe's edge | plan fault: movers never brought his charge through a lamp (fights 107-158 s on his floors) |

## The fall diagnosis (round 1's human and deft falls at the Ford-Warden)
Not balance: (1) a sim fault, his cleave and charge were not blows any hands read (deft fell standing in a marked cleave at 6% life); (2) two plan faults, the Pilot walked into his body (unmarked touch, 1.1-1.4 lives a fight) and ignored the lamps, so the fight ran 2x longer than the stander's, who walked to the lamp between them and baited his charges. After: boss stage human 61 s, deft 62 s (was 107/158), Warden damage on the human 0.3-0.7 lives (was 2.3-3.0), no Warden falls for human/deft.

## Low Ford, 16 seeds (before = round 1, 4 seeds, tier II)
| tier / bot | before no fall | after no fall | falls med/worst | mark gap med/worst s | Resolve at max % | Flare casts / first s / share / boss share |
|---|---|---|---|---|---|---|
| I human | - | 94% | 0/1 | 23/139 | 4 | 3 / 117 / 12 / 32 |
| I deft | - | 100% | 0/0 | 18/37 | 1 | 3 / 116 / 11 / 21 |
| I standing | - | 50% (falls 50%) | 0/1 | 26/107 | 28 | 5 / 110 / 22 / 39 |
| I idler | - | 100% | 0/0 | 27/70 | 30 | 4 / 113 / 19 / 36 |
| II human | 50% | 100% (pass 1: 88%) | 0/0 | 23/34 | 4 | 4 / 120 / 17 / 40 |
| II deft | 50% | 100% | 0/0 | 26/70 | 0 | 3 / 117 / 13 / 24 |
| II standing | 100% | 38% (falls 62%; pass 1: 69%) | 1/3 | 34/256 | 30 | 6 / 66 / 25 / 40 |
| II idler | 100% | 88% (pass 1: 75%) | 0/1 | 28/43 | 30 | 5 / 70 / 22 / 46 |
| III human | - | 38% | 1/2 | 28/304 | 4 | 5 / 103 / 26 / 57 |
| III deft | - | 94% | 0/1 | 24/255 | 0 | 4 / 126 / 18 / 30 |
| III standing | - | 0% (44% through) | 8/20 | 300/327 | 29 | 11 / 62 / 47 / 74 |
| III idler | - | 6% | 3/5 | 50/303 | 30 | 7 / 70 / 32 / 67 |

Pressing: human Resolve spent ~310-334/min against standing ~180-214 (round 1: 103-138 vs 119-152), at max 4% of play (round 1: 40-54%), Groundbreaker ~9-11 presses/min at tier II (8-seed runs; the table script's press column did not parse).

## What still misses, and why
- **The idler (H6's rc2 play) does as well as the human** (II: 12-25% falls, band 70%+). It reads marks with the human's eyes and steps out of them; the press buys kill speed, not survival. In the arena H6 got the gap from the director's stand clock (teeth.json `director.stand`: a pack charges one who has not moved 1.2 m in 3 s), which story fights do not have. Next lever: that stand clock in Encounters (campaign), by world tier. Not built (round cap).
- **Standing at II falls 62-69%** (band 80%+); **at I 50%** (band 80%+). More kit damage one-shots from full (kit 3: a charge is 1.2 lives; rejected), so the rest wants the stand clock too.
- **Tier III Low Ford with a fresh warden (L3-5)** is too hard for the human (38% no fall): III is health 2.5 / damage 1.8 and opens after act 1; the fresh warden is not its player. Judge III on the veteran maps.
- **The Flare's boss share is high**: 21-40% at I-II and 57-74% at III (owner band AoE 10-15%, single 15-20%); overall share 11-26%. The fill lives in logic/Sim/Flare.cs (FillHurt 0.40, FillBoss 1.8, the kills' fills); not tuned this round. A stander fills first (62-70 s vs ~117 s) because hurt fills it.
- **Veteran III/IV** not measured (command above).
- **Paths probe**: every change is behind `Battle.Campaign`/`Resolve.On` (the Pilot's edge rule checks `b.Campaign`); the BalanceTests probe in the suite stays green (the ratio itself was not printed this round).
