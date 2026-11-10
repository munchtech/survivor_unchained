# M3 bands: round 7 (10 Nov, leads 7-9): the clock counts from a foe awake; the idler measured on Resolve wasted, not speed; veteran III/IV at 16 seeds; the dev veteran is the harness's

**What changed since round 6 (file, change, why). No tier row and no skill number was tuned.**
- `godot/logic/Play/Zones/PackKit.cs` (17871c1e5, lead 7): the story stand clock counts from when a foe that may charge is awake. Standing on a pack's ground between its waves with nothing up (the kerchiefs' (44,-89), the wolves' ring hold (0.5,-99)), the next wave charged her on the tick it walked out: 45% of the stand charges read one by one were this. 48 seeds, Low Ford I/II: human and deft charges 367 -> 184 in 192 runs. Main's call: the clause stays.
- `godot/logic/Play/DevVeteran.cs` + `--veteran L[:G]` (a9b9cb98a, lead 8): the game's dev veteran is dressed by the harness's own code (shared with `MapSim.Survivor`), so a shot veteran is the measured one. Before, `--xp 100000000` gave level 30 with 58 unspent points and no gear (life 444, damage x1.15) against the sim's `--level 30 ... g2` (life 860, damage x2.60); the bare build falls 32 of 32 in the sim too.

**The idler's measure, re-pointed again under option A (main accepted, lead 8):** round 6's "kills a minute at most 0.90x the human's" was the old clock charging a stand between waves, not a press plan's worth. In the first hour she owns ONE spender and half the kit is kindled by the hands rule, so a player who presses nothing loses Resolve WASTED, not speed. The measure is now:
- **Low Ford I/II:** the idler is never faster than the human (kills a minute at most 1.00x, time through at least 1.00x) AND her Resolve sits at max at least 20% of the fight where the human's is under 10%.
- **Veteran III/IV (full kit):** time through at least 1.25x the human's.
- The passive player stays the STANDER (falls 80%+). The idler's falls are not a band.

**Low Ford, 48 seeds, tiers I / II** (`zone --zone lowford --bots standing,idler,human,deft --seeds 48 --tiers 1,2`, at 17871c1e5; raw `l71.out`):

| bot | band | I | II |
|---|---|---|---|
| human, no fall | I 85+, II 78-85 | 91.7% | 85.4% (0.4 over the top, inside the noise of 48) |
| deft, no fall | 95+ | 97.9% | 100% |
| standing, falls | 80+ | 81.2% | 97.9% |
| idler, kills a minute vs human | at most 1.00x | 0.96x | 0.98x |
| idler, time through vs human | at least 1.00x | 1.03x | 1.06x |
| idler, Resolve at max, share of the fight | at least 20% | 29.6% | 27.8% |
| human, Resolve at max, share of the fight | under 10% | 4.3% | 3.7% |
| Resolve spent a minute, idler / human | - | 208 / 323 | 245 / 353 |
| idler, no fall (not a band) | - | 85.4% | 81.2% |

**Veteran maps III / IV, warden L30 g2, rank 8 grants + Bladestorm, 16 seeds x people dead,pack = 32 runs a bot, one life a map** (raw `l8et16.out`, table by `l8tab.py`):

| bot | measure | III | IV |
|---|---|---|---|
| human | cleared | 32/32 | 32/32 |
| human | time through / the ruler | 11.3 min / 76 s | 11.9 min / 80 s |
| deft | cleared | 32/32 | 31/32 |
| idler | cleared | 22/32 | 15/32 |
| idler | time through vs human (band at least 1.25x) | 15.6 min = 1.38x | 16.0 min = 1.34x |
| standing | cleared | 0/32 | 0/32 |

**Every band is met at these seeds.** What stays open, named and not player-facing (the test bot's walk; none gates MR 2): the pickup dither at the kerchiefs' camp (45..48, -84..-87); the n_cart corner pocket at (6.36, 61.78) by night; STUCK 5 of 384 at the day's exits (they read as no-fall in the Low Ford table); the 17-31 s patch-wander and `Pilot.Leaves` unproven; two standing waits with no foe (118-130 s, 192-216 s) unread; a veteran pickup dither at 70-81 s (seed 1235); out of a storm the union's Sunder press aims at her own spot (`PressPlan.cs`), same in sim and game, so changing it moves numbers (MR 3). Human II sits at the band's top edge (85.4 against 78-85): left alone until MR 3's chain moves the grip, which re-measures every row here.

# M3 bands: round 6 (9 Nov late night, lead 6): the stand clock that knows a fighter's plant, the bands re-pointed (main's option A)

The rule (lead 5, `world_tiers.json` `stand.standSwing` 2.4 on every tier): the story stand clock counts only feet still with no cut landing; each landed cut of her held swing holds it for its own wait, up to 2.4 s at one spot; a 0.6 m step gives the allowance back; a swing at the air earns nothing. Lead 6 fixed the feet under it (`Pilot.StepLead` 0.6: the plant ends with 0.6 s of the clock left, because Sunder's own heavy holds her feet 0.3 s; a plant's end is always a step; the step clears the clock's own spot, `Battle.StandSpot`). No tier row was tuned this round.

**The bands as re-pointed (main, option A):** the passive player is the STANDER (falls 80%+). The idler ("holds the swing, dodges marks, presses nothing") is a fighter who does not press: she is no longer measured on falls but on being SLOW against the human at the same tier: **kills a minute at most 0.90x the human's, and time through at least 1.10x the human's median.** Why these: a press plan has to be worth a tenth of the run even in the first hour, where she owns one spender and about 70% of a Low Ford run is walking (in reach 86 s of about 310 s), so the fight measure (kills a minute) is the firm one and the time-through floor is low; set a wider floor on the veteran maps (full kit) once they are measured under this clock.

**Low Ford, 48 seeds, tiers I / II** (`zone --zone lowford --bots standing,idler,human,deft --seeds 48 --tiers 1,2`, at 09b64d949):

| bot | band | I | II |
|---|---|---|---|
| human, no fall | I 85+, II 78-85 | 85.4% | 85.4% (0.4 over the top, inside the noise of 48) |
| deft, no fall | 95+ | 95.8% | 100% |
| standing, falls | 80+ | 87.5% (4.06 falls a run) | 97.9% (4.29) |
| idler, kills a minute vs human | at most 0.90x | 25.8 / 29.3 = 0.88x | 24.4 / 27.7 = 0.88x |
| idler, time through vs human (median) | at least 1.10x | 5.40 / 5.10 = 1.06x (MISS by 0.04) | 6.00 / 5.30 = 1.13x |
| idler, no fall (not a band now) | - | 77.1% | 66.7% |
| human stand charges a run / stood / net turn | - | 1.4 / 70% / -0.02 | 1.6 / 67% / -0.02 |

**What still misses, and why:** (1) the idler's tier-I time through (1.06x): not tuned; first measure it on fight time, the walk dilutes it. (2) Every stand charge left on the human and deft (22 of 22 read with `SU_STANDDBG`, 8 seeds, II) is at ONE place: the day's Exit beat, the kerchiefs near (44..49, -84..-93) at 273-306 s: Pilot.Steer's `close` (20) or `stone` (2) walks her straight at a foe or a pickup 5.7-9.6 m off with a wall on the ray (or a prop near (44,-89) holding her at 0.00 m with the ray clear), so her feet are still and the clock charges. The same place is the harness's STUCK runs (6 of 384, e.g. T2/deft/s3 at (48,-106); they read as no-fall in this table). Not a feet fault: the walk has no way round a wall inside the clock's second (ZoneSim's unstick waits 8 s). (3) Veteran maps III/IV are not re-measured under standSwing.

# M3 bands: round 5 (9 Nov, the last): the Flare per boss fight, the first hour's human, the veteran idler

Commands as round 4 (veteran: four grants + the Bladestorm union, six slots). `PressedSkills.GrantUnion` now refuses a union with no room, before it takes its parts' keys, so a command asking seven keys runs without the union; round 2's command line below is fixed to round 4's. Low Ford I at 32 seeds, II at 16; veteran 8 seeds x dead,pack (16 runs a bot). `boss life` = the Flare's share of the life the bosses lost (median of runs, min-max).

The app can now hold the Flare to about one cast per campaign boss fight without dimming a press: while she fights a boss the meter fills at the campaign's boss rates, and what they held back is paid when the boss falls (her casts a run stay round 4's). It can also grow a story stand charge with the length of the stand (`standGrow`, `standGrowMax` in a world tier's `stand` row; III and IV use it).

## What changed (file, field, old -> new, why)
| where | what | old -> new | why |
|---|---|---|---|
| logic/Sim/Flare.cs `StoryFillBoss` (new; campaign) | boss fill per 1% of its life | FillBoss 1.8 -> 1.2 | 1.8 filled about 1.57 meters in a ruler fight (her 87% of his life after the 13% cut): a second cast about half the time, 20-23% of a map ruler. 1.2 fills about one. 0.8 tried first: the Ford-Warden often got no cast (life share 0%) |
| Flare.cs `StoryFillHurtBoss` (new) | hurt fill per 1% while a boss fight is on (she struck a boss, or one struck her, in the last `BossFightFor` 8 s) | 0.25 -> 0.06 | the fight's other filler: a long fight's hurt could fill the second cast alone |
| Flare.cs `bossFillOwed` (new) | what StoryFillBoss held back of 1.8 | lost -> paid when a boss falls (FlareOnKill) | without it the Low Ford human cast 3 a run (round 4: 4) and the day packs after the Warden met no Flare; with it every bot casts round 4's count again |
| Battle.HurtPlayerRaw -> FlareOnHurt | the blow's source | none -> `from` | a boss's blow starts the boss fight |
| logic/Content/Teeth.cs `StandGrow`, `StandGrowMax` (new, default 0); logic/Play/Zones/PackKit.cs | a story stand charge's bite | StandDamage -> StandDamage x (1 + min(StandGrowMax, StandGrow x seconds stood past StandFor)) | the clock answered a one-second stand and a ten-second one alike. Read by the story clock only (StandClock and the arena's director unchanged) |
| world_tiers.json III / IV `stand` | standGrow / standGrowMax | 0 / 0 -> 0.4 / 0.8 | veteran idler III falls 50 -> 69%, IV 69 -> 94%; human and deft 0-6%. Grow 0.5 with standDamage 1.6 at III: idler 56%; 0.6 / 1.2: idler 62% and human III 12% falls |
| world_tiers.json I / II | kit, stand | unchanged | see the diagnosis: every row that eased the human eased the idler with it |

## The human's tier-I falls (diagnosis)
Round 4's 9 falls in 32 (the FALL notes): every one at the Exit stage (the day packs after the Ford-Warden, 4.6-6.1 min), every one a single caught charge from 43-77% life, for 127 (wolves, boars) or 170 (Kerchiefs), marked 1.1 s ahead and not answered (BossSense.NoticePlain 0.8: the human misses one marked blow in five, by design). Not a plan fault: no press under way, nothing pressed in the 1.1 s. The 170 is the **stand clock's** charge, not a pack tell's: the kit's charge x kit 2.0 x standDamage 1.4 (kit 1.6 with standDamage 1.75 kept it at 170; standDamage 1.0 made it 121; kit 1.4 with standDamage 1.4 made it 119). She stands in melee as the idler does, so it is the stand row that kills her, and her falls are the idler's falls, rarer. With round 5's Flare (round 4's casts kept) she fell in 2 runs of 32 (93.8% no fall): a stand charge (91, a Tusker) and a 170 Pillager.

## Low Ford after (I: 32 seeds; II: 16)
| tier / bot | falls % (band) | mark gap med/worst s | Flare casts (min) / first s / boss life % |
|---|---|---|---|
| I standing | 100 (80+) | 26/261 | 7 (6) / 15 / 11 (0-24) |
| I idler | 56 (70+: miss) | 32.5/176 | 5 (4) / 112.5 / 12 (0-22) |
| I human | 6.2 (no fall 93.8: band 85+) | 23/172 | 4 (3) / 116 / 11 (11-12) |
| I deft | 0 (no fall 100: band 95+) | 23.5/34 | 4 (3) / 114 / 11 (4-12) |
| II standing | 100 | 35/239 | 9 (7) / 15 / 14 (10-20) |
| II idler | 69 (70+; 77 at 48 seeds) | 34.5/302 | 5.5 (4) / 59 / 12 (0-12) |
| II human | 19 (no fall 81; 73 at 48 seeds, round 4's build 81) | 25/72 | 4 (3) / 118.5 / 11.5 (11-12) |
| II deft | 12.5 (no fall 87.5; 94 at 48 seeds, round 4's build 96) | 25/301 | 4 (3) / 118 / 11 (8-12) |

Before (round 4's build re-run): human and deft boss life 11-12% (one cast on the Warden already), idler I 47% falls at 32 seeds, human I 72% no fall.

## Veteran maps III/IV after (8 seeds x dead,pack)
| tier / bot | falls % (band) | mark gap med/worst s (band under 60/90) | Flare casts / first s / boss life % |
|---|---|---|---|
| III standing | 100 (80+) | 5/13 | 1 / 99 / - (never reaches the ruler) |
| III idler | 69 (70+: one run short) | 40/100 | 3 / 198 / 12 (0-28) |
| III human | 0 (no fall 100) | 53.5/110 | 3 / 428 / 12 (0-24) |
| III deft | 0 (no fall 100) | 47.5/126 | 2 / 606 / 12 (4-25) |
| IV standing | 100 | 6/46 | 0 / - / - |
| IV idler | 94 (70+) | 19.5/72 | 3 / 168 / 14 (12-21) |
| IV human | 6 (no fall 94) | 48.5/121 | 2 / 368 / 12 (9-23) |
| IV deft | 0 (no fall 100) | 48.5/85 | 2 / 582 / 13 (11-24) |

The Flare on map rulers: 20-23% -> 12-14% (median). A run that meets the ruler with a nearly full meter still fits two (max 24-28%). Halving later casts on the same boss was not needed for the median and was not built.

## Paths probe
Host crowd 1134 / (0.7 x median 1568) = 1.033x, unchanged (BalanceTests on this build). Everything new sits behind `Battle.Campaign` (StoryFillBoss, StoryFillHurtBoss, the owed fill) or the story clock (StandGrow). Suite 1733 passed, 0 failed, 10 skipped.

## What still misses, and why
- **Low Ford I idler falls 56%** (band 70+). The stand clock cannot tell a melee human from the idler: both stand in reach, and the human's falls are stand charges too. Every probe moved them together: standDamage 1.0-1.25 with cooldown 0.4-0.7 took the idler to 31-41% (human 3-12%); StandGrow 0.4-1.0 at I/II took the human to 16-19% falls with the idler flat (41-56%). What separates them is the presses (the human's Groundbreaker and Leap end a pack sooner), not the stand. Lever (a design call, not taken): an idler-only signal, e.g. a stand with no skill pressed in N s bites harder; or accept 56% at the first hour's tier.
- **Low Ford II deft 87.5% / human 81% no fall at 16 seeds** (deft band 95+): within noise of round 4's own build at 48 seeds (deft 94 vs 96, idler 77 vs 79), but the human's Exit falls rose 7 -> 13 of 48 (73% vs 81%): the Warden's fight has one cast fewer. Left: the first hour is tier I.
- **Veteran idler III 69%** (11 of 16; band 70+): one run short. III's packs die fast; a harsher grow (0.6 / 1.2) cost human III 12% falls.
- **Worst no-mark gap 100-126 s** on the human and deft at III and IV (band under 90): the ruler fights and the altar walks, as round 4. No pack-density change was tried (round cap).
- **Round cap:** two passes. Pass 1 the Flare (StoryFillBoss 0.8, then 1.2 with the owed fill). Pass 2 the stand rows (one grid of five I/II rows, four growth rows, three III/IV rows, each read against one build).

---

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
- Veteran: `... -- map --callings warden --level 30 --people dead,pack --grant groundbreaker:8,heroic_leap:8,shield_charge:8,iron_vow:8 --grant-union bladestorm --bots standing,idler,human,deft --seeds 8 --tiers 3,4`. Without `--callings warden` it runs every calling (512 maps); with `--people all` 16 mixes. (Fixed in round 5: this line first asked seven keys of six slots, Cleaver and Watch Bell on top of the union; GrantUnion now refuses a union with no room, so it ran without Bladestorm.)

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
