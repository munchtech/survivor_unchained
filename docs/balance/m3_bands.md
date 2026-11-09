# M3 bands: round 4 (9 Nov): the maps read the world tiers; the Flare's cut counted after the build

Commands as round 3, with two changes. Veteran build: `map --callings warden --level 30 --people dead,pack --grant groundbreaker:8,heroic_leap:8,shield_charge:8,iron_vow:8 --grant-union bladestorm --bots standing,idler,human,deft --seeds 8 --tiers 3,4` (round 3's command asks seven keys of six: Cleaver and Watch Bell on top of the union; see the sim fault below). Run lines now print `life N%` after `boss`: the Flare's share of the life the bosses lost (`BossHealthBy`); the old `boss` share is of damage, which counts a gated boss's overflow past its Break and halved the Ford-Warden's real share.

## What changed (file, field, old -> new, why)
| where | what | old -> new | why |
|---|---|---|---|
| logic/Play/Zones/PackKit.cs (new), Encounters.cs | the packs' tells and the stand clock | inline in Encounters -> one class Encounters and MapRun call (same order, same draws) | the maps press through the story fights' code; Low Ford I/II with round 3's cut re-ran to round 3's table exactly |
| MapRun.Begin, Press; WorldTiers.ForMap | the maps' press | none -> the chart tier's row (kit, kitEvery, stand; tiers past IV ride IV); a roused pack's foes on foot (not its leader, not archers) cast the kit's charge at the story pack's waits (5-7 s, first 1.2 s) x kitEvery; the stand clock over roused packs | decided (maps ride the world tiers). Maps are Campaign fights (Journey.StartBattle: not arena, not ember), so the gate is `Battle.Campaign`; their health/damage stay the map's own |
| balance MapSim | StartBattle | worldTier on (tier II's health, damage, kit x2 on the ruler's script) -> off, as Game.cs starts a map | harness fault |
| logic/Sim/PressedSkills.cs GrantUnion | a union with no room | took its parts' keys, then failed -> refused before taking them | sim fault: round 3's veteran grants left the Warden without her Sunder (no grip: Resolve 0/min, ruler fights 160-580 s, the Flare 61-87% of a ruler) |
| Flare.cs StoryBossCut, FlareStaged.FlareHit, HitOpts.Cap | the cut | 0.10 of a boss's life before the build's multipliers -> 0.13 after them | before them a level-30 build's x5-x8 made it no cut on a map ruler, and it took 20-28% of the Ford-Warden's life at Low Ford (by life; round 3's 12.5% was by damage) |
| world_tiers.json III / IV | kitEvery | 0.5 / 0.45 -> 0.7 / 0.7 | at 0.5 the veteran maps cast ~250 charges a map (one every 4 s; human 69-100% falls before the build fix). 1.0 and 1.5 moved falls little; 0.7 keeps the human's median gap 50-58 s |
| world_tiers.json III / IV | stand | round 2's II numbers (1.5 s, cd 1.5, near 14, damage 1) -> I/II's (1.0 s, cd 1.0, near 16, standDamage 1.4) | the idler fell 25% (III) with the old numbers |
| | MapRun.BossHealth | 3.5 (unchanged) | the ruler's long fights were the missing Sunder, not its health: ruler TTK 80-100 s with the build whole |

## Veteran maps III/IV, 8 seeds x people dead and pack (16 runs a bot), after
| tier / bot | falls % (band) | mark gap med/worst s (band under 60/90) | Flare casts / boss share by life % (band 10-15) |
|---|---|---|---|
| III standing | 100 (80+) | 14/64 | 2 / - (never reaches the ruler) |
| III idler | 44 (70+: miss) | 29/86 | 4 / 20.5 |
| III human | 0 (no fall 100: 78-85+) | 58/110 | 3 / 20.5 |
| III deft | 0 (no fall 100: 95+) | 47.5/126 | 2 / 23 |
| IV standing | 100 | 7/42 | 2 / - |
| IV idler | 75 (70+) | 30.5/117 | 4 / 23 |
| IV human | 6 (no fall 94) | 50/84 | 3 / 22 |
| IV deft | 0 (no fall 100) | 48.5/85 | 2 / 20 |

Round 3's own command (seven keys asked; now Sunder kept, Cleaver and Bladestorm refused): idler falls 12/44%, human and deft 0%, human gap 66.5/62.5 s, boss life 20.5-25%.

## Low Ford after (rows I/II untouched; only the cut moved)
| tier / bot | falls % (band) | mark gap med/worst s | Flare casts / boss share: damage / life % |
|---|---|---|---|
| I standing | 100 (80+) | 26/119 | 7.5 / 11 / 15.5 |
| I idler | 56 (70+: miss; round 3 88) | 32.5/104 | 5 / 10.5 / 12 |
| I human | 44 at 16 seeds, 28 at 32 (no fall 72: band 78-85+, miss; round 3 81 at 16) | 22.5/301 | 4 / 7 / 12 (32 seeds: 11) |
| I deft | 0 at 16, 0 at 32 (no fall 100) | 24/45 | 4 / 8 / 12 |
| II standing | 100 | 56.5/300 | 10 / 22 / 22.5 |
| II idler | 81 (70+) | 34.5/202 | 6 / 16.5 / 20.5 |
| II human | 12 (no fall 88) | 30.5/175 | 4 / 7 / 12 |
| II deft | 0 (no fall 100) | 23/36 | 4 / 7.5 / 12 |

Tier I deft at 32 seeds: 32 of 32 no fall: round 3's 94% was noise (its one fall moved with the Warden fight). Seeds 1-16 are the unlucky half for the human at I (7 falls there, 2 in 17-32).

## Paths probe
Host crowd 1134 / (0.7 x median crowd 1568) = 1.033x, unchanged. Suite 1733 passed, 0 failed, 10 skipped (WorldTiersTests' IV kitEvery pin 0.45 -> 0.7). All of it sits behind `Battle.Campaign` (PackKit, the cut, the stand rows) or the map path; the arena keeps its own director.

## What still misses, and why
- **Map rulers: the Flare takes 20-23% of their life** (band 10-15). One cast is 13% (the cut binds at level 30); a ruler fight of 80-100 s fills a second cast about half the time. The cut is per cast; the band is per fight. Lever (a design call, not taken): later casts on the same boss take a smaller cut (e.g. the second half of it), or a per-fight budget. Not done: it changes how a press feels on a boss.
- **Low Ford I human (72% no fall at 32 seeds) and idler (56% falls)**: moved by the cut alone (round 3's cut really took 20-28% of the Warden's life; at 13% his fight is longer). StoryBossCut 0.20 gave human I 81% / idler I 75% / deft II 94% at 16 seeds with the Warden's life share ~18%. The choice is the band (0.13) or Low Ford's old feel (0.20).
- **Veteran idler III falls 44%** (band 70%+; IV 75%). kitEvery 0.5-1.5 and kit 1.8 -> 2.0 moved it 38-56%; the idler steps out of marks and III's packs die fast. Lever: the III stand row harder than I/II's (standFor under 1 s), or a denser III pack (MapRun.PackSize).
- **Worst no-mark gap 84-126 s** (band under 90) on the human and deft: the long ruler fights and the quiet altar walks.
- **Round cap:** three tune passes, over the cap of two: pass 1 (kitEvery 1.0/1.5, cut 0.20, BossHealth 1.5) was read against a build missing its Sunder; after the sim fix pass 2 set the table above, and pass 3 (III kit 2.0, kitEvery 0.5) moved the idler III 44 -> 38% and the IV worst gaps 85 -> 148 s, so it was reverted.

---

# M3 bands: round 3 (9 Nov): the stand clock in story fights, the Flare's boss share

Same commands as round 2 (below). Run lines now also print `onboss N` (casts that reached a boss) and `fills` (meters filled by source).

## What changed in round 3 (file, field, old -> new, why)
| where | what | old -> new | why |
|---|---|---|---|
| logic/Play/Zones/StandClock.cs (new), ArenaRun.Director.cs | H6's stand rule (trail, still check, first and second charger) | inline in the arena director -> one shared class, the director calls it (same order, same numbers) | one idea, not a fork |
| Encounters.cs `Standing`, Battle.StoryStand, WorldTiers.Tier.Stand | stand clock in story fights | none -> a woken pack's foe charges a stander (the kit's marked charge, second from another side held its spacing); Campaign on and the tier's `stand` only | standing must lose in story fights |
| world_tiers.json `stand` I/II (III/IV = old II numbers, unmeasured: maps do not read world tiers) | standMoved / standFor / standNear / standScale / standPair / standFrom / standCooldown / standDamage | (new) 0.6 / 1.0 / 16 / 2.2 / 2 / 7 / 1.0 / 1.4 | pass 1 (1.5 s, cd 1.5, near 14, dmg 1): idler fell 6-31%; standFor 1.0 alone: idler 12/75%; standDamage 1.6 at I one-shot the deft from 72-86% life (194 a charge), so 1.4 |
| Teeth.Director `StandDamage` (new, default 1) | a stand charge's damage over the kit's | - | read only by the story clock; the arena's casts never pass it |
| logic/Sim/Flare.cs `StoryFillHurt` (campaign only) | hurt fill per 1% of life | 0.40 -> 0.25 | a stander filled 5-6 meters a run from hurt alone |
| Flare.cs `StoryBossCut`, FlareStaged.FlareHit (campaign only) | most of a story boss's max life one Flare takes (its blows share it) | uncapped -> 0.10 | the ember's level made one Long Cut ~1700 a blow on the Ford-Warden's 3250: it was the finisher, 16-41% of his damage from ONE cast, so no fill change could reach the band (halving bossMul moved the share 25 -> 24%) |

## Low Ford, 16 seeds, after (falls = runs with at least one fall)
| tier / bot | falls % (band) | no fall % (band) | falls med | mark gap med/worst s | Flare casts / first s / share % / boss share % (min-max) |
|---|---|---|---|---|---|
| I standing | 100 (80+) | 0 | 4.5 | 27/238 | 7.5 / 15 / 13.5 / 12.5 (10-19) |
| I idler | 88 (70+) | 12 | 1 | 31/194 | 5 / 114 / 13 / 10.5 (6-18) |
| I human | 19 | 81 (78-85+) | 0 | 22.5/37 | 4 / 118 / 10 / 12.5 (8-24) |
| I deft | 6 | 94 (95+: one run short) | 0 | 24.5/64 | 4 / 114 / 9 / 13 (7-30) |
| II standing | 100 (80+) | 0 | 8 | 34.5/242 | 10 / 15 / 21 / 21.5 (11-26) |
| II idler | 88 (70+) | 12 | 1 | 43.5/240 | 6 / 59 / 12.5 / 15.5 (8-32) |
| II human | 0 | 100 (78-85+) | 0 | 25/286 | 4 / 119 / 10 / 12.5 (9-29) |
| II deft | 0 | 100 (95+) | 0 | 26/207 | 3 / 118 / 9.5 / 12 (7-30) |
| III standing | 100 | 0 | 162 (not through) | 31.5/301 | 138 / 27.5 / 43 / 47.5 |
| III idler | 100 | 0 | 5 | 156/302 | 8.5 / 66 / 26 / 35 |
| III human | 69 | 31 | 1 | 47.5/306 | 5 / 136 / 16 / 25.5 |
| III deft | 25 | 75 | 0 | 25.5/234 | 4 / 131 / 14 / 16 |

Before (round 2 re-run at HEAD 204a49d77, I/II): standing fell 50/62%, idler 0/12%, human no-fall 94/100%, deft 100/100%; Flare boss share human 31.5/39.5, deft 21/24, idler 35.5/46, standing 39/39.5.

Caught stand-clock charges (kit `c.charge` median a run, II): idler 6, human 2, deft 1, standing 17.5 (before: 2 / 1 / 0 / 5). The clock is symmetric per second stood; the idler stands about 4x more, which is the whole gap.

**The Flare (the warden's Long Cut is AoE: band 10-15%).** Human and deft 12-13% at I-II (one cast on the Ford-Warden in most runs, `onboss 1`, a second where his fight fills 1.5+ meters); the stander 12.5/21.5% (2-3 casts on him at II, hurt still fills it first, first cast 15 s). Every bot still casts 3-4 a run (human 4 at I and II).

## Veteran maps III/IV, 8 seeds x people dead and pack (16 runs a bot), warden L30, rank 8 grants + Bladestorm (no tune: maps read neither world tiers nor the story clock)
| tier / bot | falls % (band) | mark gap med/worst s (band under 45-60) | Flare casts / first s / share % / boss share % |
|---|---|---|---|
| III standing | 81 (80+) | 167/433 | 3 / 467 / 11 / 70 |
| III idler | 50 (70+) | 158/231 | 3 / 603 / 12 / 83 |
| III human | 12 (no fall 88: band 78-85+) | 174/510 | 2 / 884 / 10 / 75 |
| III deft | 0 (no fall 100) | 170/334 | 2 / 910 / 8 / 61 |
| IV standing | 100 | 205/418 | 2 / 445 / 9 / 81 |
| IV idler | 50 (70+) | 129/236 | 3 / 498 / 11 / 79 |
| IV human | 6 | 140/355 | 3 / 795 / 10 / 71 |
| IV deft | 0 | 183/608 | 2 / 884 / 9 / 73 |

People: `dead` cleared 70% / 0.20 falls a run; `pack` 17% / 0.55 (the Pack-Mother takes most falls). A map closes at its first fall (falls cap at 1 a run).

## Paths probe
BalanceTests (Campaign off): crowd median 1568 (dawn 1571, grave 1288, host 1134, hunt 1565, pyre 1915, rime 1706, steel 1536, storm 1864, weave 1852, wild 1488); host 1134 / (0.7 x 1568 = 1098) = **1.033x its floor**, the same as before round 3. Byte-same off the story path: StandClock is the arena's own code moved (same calls, same order), and the story clock, StoryFillHurt and StoryBossCut all sit behind `Battle.Campaign`. Suite 1733 passed / 0 failed / 10 skipped.

## What still misses, and why
- **Tier I deft 94% no fall** (band 95%+): 15 of 16; the one fall is a stand charge after a long stand at the lamp. standDamage 1.6 made it 88%, 1.2 left the idler at 56%: 1.4 is the knee.
- **Low Ford III with a fresh warden** (human 31% no fall) stays too hard, as round 2 said: III opens after act 1.
- **The stander's boss share at II, 21.5%**: 2-3 casts on the Warden, all from hurt fill. Inside the bot that should lose; left.
- **Veteran maps: mark gap 129-205 s median** (band under 45-60) and the idler falls 50% (band 70%+). Maps do not read world tiers' `kitEvery`/`stand` (WorldTierOn is story only), and their packs cast the kit about once a fight. The lever is the map path: give maps the story clock and a kit wait (a `map` block in world_tiers.json by tier, or the map's level scaling). Not built: past the round cap. Design question: should maps ride world tiers (pick: yes, a map's tier = the world tier's kit and stand rows) or their own rows?
- **Veteran Flare boss share 61-83%**: one map boss eats 2-3 casts at the ember's full level; StoryBossCut is Campaign only. The same budget on maps' bosses is the fix (one line in FlareHit), not done: maps are out of this round's tuned scope.
- **Round cap:** this round took four tune passes on the clock (1.5 s -> 1.0 s, standDamage 1 -> 1.2 -> 1.6 -> 1.4) and two on the Flare (bossMul 0.5 rejected, then the 0.15 -> 0.10 budget), over the cap of two.

---

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
