# Handoff: combat (skills' mechanics, enemies, encounters, bosses, balance, the maps, the story's nights)

## M3 combat systems, lead 3 (combat-m3, 9 Nov evening): HANDOFF READY at ~200k. MR 2 still open on this branch
Brief: `tools/scratch/coordinator/briefs/M3_combat_lead1.md` + lead 2's block below (its "Next" list is still the order; its item 1 is done here). Owner, 9 Nov evening: no budget, "just make it awesome"; the waste rules stay (own look before a max judge, scrap at first FAR, half-size pictures, hand off at ~200k).
**Done this lead (the app can now play its own clips with the harness's feet):**
- d0eff97e7: `Pilot` and `Human` moved from godot/balance/Harness to `godot/logic/Play/Pilots/` (namespace `SurvivorUnchained.Play.Pilots`): the game, the harness and the tests share ONE set of feet. `Pilot.Act`/`Human.Act` got `drinks` (additive).
- 693aa563f + d433f7aca: `src/Game/Autopilot.cs`: campaign fights under `--auto` (human) / `--auto deft` steer by `Human.Steer`/`Pilot.Steer` and act by `Human.Act`/`Pilot.Act` in the `PlanStep` hook (dash, Flare, presses, draught: the same Battle calls the keys make). Low Ford: ZoneSim's goals (pack-first rule, Warden's lamp as goal); maps: `PilotField` on a NavField to the ruler (MapSim's 20 s walk-on rule); quiet-time GroundPath routing and an arrive-stop (not on maps). Arena, story nights and idle/toward/away/across/talk are untouched. `--old-feet` = the old orbit for comparison. `--clip` prints a `pilot trace` line each second (position, nearest foe, in-reach seconds, net/abs angle round the nearest foe, foe-within-22 m seconds, togo, ruler).
- 52fdb3bff: `DevGrants.MakeRoom`: a dev grant or union with no room frees the last key that is not the grip nor the union's part (MapSim.GiveGrants shares it); `--grant-union bladestorm` works in game (watch_bell gives up its key; storm on keys 6 and 1). Test `tests/DevGrantTests.cs`.
- Suite 1734/0/10 twice, no host abort (the owed rerun is paid). Coordinator branch merged (724341c4c, junction rule).
**Proof numbers (2 min veteran map, seed 1234, new feet | `--old-feet`):** togo to the ruler 841 -> 685 | 841 -> 853; a foe within 22 m 75% | 19% of seconds; longest gap with no non-grip press 13.9 s | 86.9 s; presses/min storm 4, groundbreaker 7, leap 2, charge 3, dash 7.5 | groundbreaker 1.5; Flares 1 | 0; no 10 s+ aimless walk | 81 s of it. Low Ford 3 min: groundbreaker 6.7/min, dash 6/min, 1 Flare, 0 falls, hp min 0.38. Clips: `survivorsunchained_inputs\combat_m3\m3fix_map_2min`, `m3old_map_2min`, `m3fix_lowford_3min` (each: clip.mp4, presses.txt, rhythm.txt, log.txt, strip_half.jpg); measure script `survivorsunchained_inputs`-bound scratch `scratchpad\combat_m3\nums.py` (back it up).
**NOT DONE / open, in order for lead 4:**
1. **Own look at the two strip_half.jpg FIRST (nobody has looked).** The trace says that with a foe in reach she sweeps 2.2-2.3 full turns per 10 s round the nearest foe (net 0.5 on the map, 1.3 in the Low Ford; old feet 1.1): the Pilot's in-reach branch (`Pilot.Steer`: "else if (nearest != null) { mx = -(nearest.Z - p.Z) ...") strafes at right angles to the nearest foe without pause. If that still reads as circling, change it in the shared Pilot, campaign only (step a quarter turn, stand and swing ~1 s under the stand clock's `standFor` 1.0 s / `standMoved` 0.6 m, step again; read marks as now), then re-measure the bands (docs/balance/m3_bands.md commands; one runner round) because the human's feet are what the numbers ran on. Do not send a clip to the owner or the judge before this look.
2. Low Ford t 17-31 s: she stays in a 5 m patch between targets that change each second (two 1 s stands): find which targets (trace `to`), fix at the cause.
3. `Pilot.Leaves` (d433f7aca) never fired (`left 0`): written on a guess for hidden or pack-refused loot; prove it with a test or take it out. `--quick` on the Low Ford clip was inferred (old log has no args). 6 `RenderingServer::get_singleton() is null` lines per log, not placed.
4. The ruler is not reached in 5 min on the veteran map (togo 841 -> 499): for the judge's veteran clip shoot the road 5 min AND a ruler segment (`--at boss`), or a shorter chart.
5. Then lead 2's list from its (2): reshoot `lowford_10min` + veteran 5 min; item 9 measured on a skill_clip.py grip shot; own half-size look; one max judge; merge integration (ui-m4 merges first: expect M4's Journey.cs:324 hunk, the calling banner: answer A, M4 owns that line and its wording); suite; push; MR 2 READY.
6. **MR 3 (new, the owner's "slashing back and forth instead of reset slash reset slash"): the held swing as a chain.** Today (solver's read, file:line in its report, not re-checked by me): no chain state; each swing is its own press on the weapon's cooldown (`Weapons.cs:401`, `Resolve.cs:198`), the blow lands at the clip's contact frame 0.04-0.07 s after the press (`Contact.cs:54,73-77`), then ~1 s (Oathblade 1.05 s interval) or ~1.5 s (Sunder 1.6 s) of nothing: that gap is the reset; attack speed scales only the interval; the view restarts the clip per swing (`PlayerView.cs:1074`), `Swing()` toggles `mirror` per slash; release does nothing. Sim work (mine): per-weapon cut index kept while held and 0.4 s after (replacing the global `clipSwing`), `chain`/`recover` on `PressDef`, clip rate = authored length / cut period so attack speed scales contact and cancel with the interval, `Cut`/`Side` on `AttackAnim` and `Ev.Slash`, a release event, move-cancel after the cut's `cancel` beat, a dash before contact drops the blow, tests (index cycles/resets, contact per cut, speed invariance, recover on release, cancel). View (P7 lead 3 / A1 through main): PlayerView blends instead of restarting and plays the recover; BattleFx `mirror` from `e.Side`. The timing contract sent to main for A1 lead 9 is in the 9 Nov message (cuts A/B 42 frames at 60 fps, contact 14, cancel 22; finisher 54/20/30; recovers <= 18 frames, cancellable from frame 0; grace 0.40 s; the sim scales the rate). Open design call, lead's pick: the grip's interval comes down toward 0.70 s a cut with damage and Resolve per blow scaled so both per second stay the same and the finisher's count per second stays the same; bands re-measured.
**Uncommitted on purpose:** the `.import`/`.uid` churn (as lead 2's note), stale untracked `godot/balance/Harness/Pilot.cs.uid` and `Human.cs.uid`.
**Cost:** lead 3 ~195k; solvers 179k + 168k + 120k; $0 API.

## M3 combat systems, lead 2 (combat-m3, 9 Nov): HANDOFF READY (superseded by lead 3 above; wind-down on the coordinator's word). MR 1 (c6de22367) MERGED into integration; MR 2 open on this branch
Brief: `tools/scratch/coordinator/briefs/M3_combat_lead1.md` (items 1-9) + lead 1's block below (items 1-5, 8 done there). Numbers: `docs/balance/m3_bands.md` (rounds 3-5 on top; commands there; veteran = variant B, six slots). Solver briefs: `survivorsunchained_inputs\scratch_combat_m3\solverS3/S4/S5_brief.md`, run scripts in `solverS5\` (`runv.sh`, harness `--over DIR` tests a data variant).
**Done this lead (rounds 3-5):**
- Stand clock in story fights and maps: `logic/Play/Zones/StandClock.cs` (H6's arena rule, one class the arena director also calls) and `PackKit.cs` (pack tells + stand clock, shared by story zones and maps); numbers per world tier in `world_tiers.json` `stand` (standGrow/standGrowMax at III/IV: a stand charge grows the longer she stands); maps pick their row by chart tier (`WorldTiers.ForMap`, past IV = IV). Maps were already Campaign fights.
- The Flare in campaign: `StoryFillHurt` 0.25, `StoryFillBoss` 1.2, `StoryFillHurtBoss` 0.06 (a boss fight = she struck/was struck by a boss in 8 s), held-back fill paid when the boss falls, `StoryBossCut` 0.13 of a boss's life per cast after multipliers (`HitOpts.Cap`): about one full-look cast per boss fight. Arena (Campaign off) byte-same; host ratio 1.033x.
- Fixed: `PressedSkills.GrantUnion` took a union's parts before checking room (refuses first now); `balance MapSim` started maps on world tier II (now `worldTier: false`, as Game.cs). RunMeter prints Flare boss casts, fill sources, boss life share.
**Final numbers (falls %; Low Ford I 32 seeds, II 16; veteran 8 x dead,pack):** Low Ford I: standing 100, idler 56 (band 70+: MISS), human 6 (no fall 94), deft 0. II: standing 100, idler 69 (77 at 48 seeds), human 19 (no fall 81), deft 12.5 (94 no fall at 48 seeds: noise). Veteran III: standing 100, idler 69 (one run short), human 0, deft 0; IV: 100/94/6/0. Flare boss life share 11-14% median for human/deft everywhere (band AoE 10-15%; a run reaching a ruler nearly full can still cast twice, max 24-28%).
**Knowns (named, not chased; round cap hit):** (1) Low Ford I idler 56%: the stand clock can't tell a melee human from the idler; the lever is a design call (a stand with no skill pressed for N s hits harder) or accept tier I as gentle: lead's pick accept, tier I is the first hour. (2) Worst no-mark gap 100-126 s at III/IV for human/deft (band under 90; lever: III/IV pack density). (3) Low Ford III with a fresh L3-5 warden too hard (III opens after act 1; judge III on maps).
**MR 2 state (on this branch past c6de22367, not merged):**
- a22b850b7 item 9 CODE: `Ev.Slash.Held` (Weapons.ConeHit sets it from `w.Hold`; campaign only, arena byte-same); BattleFx.Skills.cs Swing(): a held `slash_heavy` (Sunder as the grip) in steel colors (SteelWhite core, OathGold*0.55 glow, hue #d8a24a 0.95), depth 0.44 -> 0.22, echo 0.55 -> 0.3, sparks halved, NO crack scar or clods, dust 4/1.8g, trauma 0.02; the every-fourth line swing and Cleaver unchanged. Suite 1733/0/10. NOT MEASURED: tools/style/frames.py frame 06 is not deterministic (before: her after the fight; after: foliage) and shows no swing; measure on a skill_clip.py shot of the grip instead (`tools/fx/skill_clip.py`, a Sunder hold).
- bedd364a0 + 7b3f2de53: `tools/combat/play_clip.py NAME --minutes M --godot-args "..."` (1:1 mp4, presses.txt, rhythm.txt per minute, moments/ at press/contact, strip.jpg) and the Autopilot's `--clip` press print (`skill press frame N slot S t T skill ID kind ... resolve V/M`). Suite after: 1723 passed/0 failed then the test host aborted at the very end: rerun once to confirm.
- Shots (survivorsunchained_inputs\combat_m3\): `lowford_10min` (3 Flares at 98/242/332 s; Groundbreaker 5/3/13/1/6/1 a minute; presses stop at ~344 s; longest non-grip gap 263 s), `vet30_map_5min` and `vet30_map_union_5min` (presses only in the first 15 s, then 287 s of walking; 0 Flares). NONE is usable for the judge.
**Lead 3, first item: "they are just running in circles" (the owner, watching the vet map render).** Diagnosis (read, not fixed): the game's `--auto` is the old crude Autopilot (src/Game/Autopilot.cs header: "out in a fight circles a patch of ground keeping the crowd in front of it"; `orbit` targets at ~222-298). M3 only gave it the press plan's KEYS (PressPlan.Run ~63); its MOVEMENT is still the orbit, and it has no map route, so on a map with no foe in sight it circles; in the Low Ford it presses until ~344 s and then walks on. The numbers came from the balance harness's Pilot (godot/balance), which engages to a foe's edge, follows MapGen's packs and steps out of marks: the game never ran that. Fix: the Autopilot's campaign movement for `--auto human|deft` = the Pilot's rules (engage to the edge, map route to the next pack/ruler, step out of marks, the dash on a telegraph), shared rather than copied if the Pilot's code can live in logic/; then reshoot with play_clip.py. Also: `--grant-union bladestorm` failed in game ("no two slots free"): TaughtBuilds.Grant fills the six slots in a campaign fight before DevGrants; grant the union first or let dev grants replace taught slots. The game has no level flag (`--xp 100000000` showed 30 on the HUD).
**Next, in order (MR 2):** (1) the Autopilot movement above + the union grant order; (2) reshoot `lowford_10min` and a veteran map 5 min (`--zone map --tier 3 --people pack --seed 1234`, grants, `--xp 100000000`; maybe `--at boss` for the ruler) with play_clip.py; (3) measure item 9 on a skill_clip.py grip shot (fx_measure before/after, same box); (4) your own half-size look; (5) one max judge (whole-frame question: "is this Diablo's rhythm: generator, spender, cooldown; does every press matter?"); (6) merge integration (junction rule; M4 merged after MR 1: Game.cs Ev.DashStep arm and the Journey Level line are theirs), suite, push, MR READY.
**Uncommitted on purpose:** ~36 tracked `godot/art/**/*.import` files rewritten by a headless reimport (W9) and untracked .uid files: import churn, not work; discard or leave, never commit wholesale.
**Cost:** lead 2 ~90k; solvers S3 175k, S4 175k, S5 160k; workers W9 ~110k, clips ~120k; $0 API. Total M3 ~2.4M. MR 2 left: about 0.35-0.45M (Autopilot movement ~120k, reshoots ~60k, judge ~180k).

## M3 combat systems, lead 1 (combat-m3, 9 Nov): HANDOFF READY (superseded by lead 2 above)
Brief: `tools/scratch/coordinator/briefs/M3_combat_lead1.md` (items 1-9). Helper briefs and raw outputs: `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_combat_m3\` (solverA/B/C/C2/E/R2_brief.md, c2_*.txt, final*_zone/map.txt, summ.py). Usage rules (owner, lead_brief "Usage rules"): your own 1:1 look + numbers before the max judge, spawn it only when you'd bet on PASS; FAR = rebuild the block; helpers orient <=60k and stop at 80k if not building; no shots before their inputs exist. **Put exactly one `Context budget:` line in a helper prompt** (a second number in the prompt capped solver C at 100k). Integration NOT merged since ed1485134 (junction rule before any merge).
**Done (suite 1733/0/10 at df5b71112, run 9 Nov):**
- 1 Press path: `BattleSetup.Campaign` = `combat && !arena && !ember` (Journey.StartBattle). Off = arena/probe/old tests byte-same (the SEAM for M8: the arena keeps self-firing). Per-skill `press` record in skills.json (kind hold/press/channel/kindle, `kindled` option, aim hover/point/self, reach, walk 0.7, castTime, plant <=0.3 `Battle.MaxPlant`, wait, resolve, builds, clip/clipRate); `HoldSkill(slot, held, x, z)`/`AimSkills`; WorldScene.Skills feeds the pointer (bindings are M4's, via Controls).
- 2 Resolve: `logic/Sim/Resolve.cs` (M4's API block at its top: STABLE, M4 builds on it; tell main before any change); numbers in `data/content/resolve.json` (selfAt 1: a kindled spender fires itself only when full).
- 3 Kindled presses (riposte 2 s, flare 3 s, now, command hook); 7/14 of the kit offered kindled; `data/content/taught_builds.json` (coordinator-approved: Sunder held; Groundbreaker kindled spender; Leap 4 and Charge 5 pressed; Iron Vow 7 and Watch Bell 9 kindled; Dawnpulse later) + `HandsRuleTests`; `TaughtBuilds.Grant` gives it in campaign fights and on each level (`Ev.Taught`, `CharacterData.TaughtUpTo`); ARPG.md fixed at source (03e562d21). Iron Vow now leans on Might (SkillBook.Attribute: shield tag).
- 4 Union bond: halves keep their parts' lamps (`CarryTurns`, also GrantUnion); break Grow from Resolve spent in the storm; Bladestorm drains 28/s, no cap or cooldown.
- 5 All 42 P7 lamps wired (`logic/Sim/WardenWicks.cs`) + `WickRulesTests` (data-driven: an unwired lamp fails). New view hooks nothing draws yet (Ev names _rupture/_spatter/_landslide/_wave): P7 lead 3, main told.
- 8 Contact frames: `tools/anim/contact_measure.py` -> `godot/data/anim/her_events.json` (M3 interim; A1's P4 pack replaces it by clip name); `logic/Sim/Contact.cs` lands campaign blows at contact/60/clipRate after the press; view: PlayerView.cs ~1078-1080 only; `ContactFrameTests`.
- 6 Bots: `data/content/press_plan.json` + `logic/Sim/PressPlan.cs` (hands deft/human/careless/grip), used by Pilot (zone and map sims) and the game's Autopilot (`--auto` = human hands in a campaign fight, `--auto deft`; never watched in game yet); `balance/Harness/RunMeter.cs` prints presses, Resolve spent/full, shares, Flare, mark gap, fall notes. MapSim takes --bot(s)/--grant/--grant-union (`--callings warden` required).
**Numbers (`docs/balance/m3_bands.md`; Low Ford, 16 seeds, no-fall %):** I: human 94, deft 100, standing 50, idler 100. II: human 100, deft 100, standing 38 (fell 62%), idler 88. III (fresh level 3-5): human 38, deft 94. Human presses Groundbreaker 9-11/min; Resolve at max 3-8% of play (round 1: 40-54%). Tuned: world_tiers kit I-IV -> 2.0/2.0/1.8/2.0, new kitEvery 0.4/0.4/0.5/0.45, teeth fordWarden.cleave 2.5; the Warden's cleave/charge are now real marked blows; Pilot engages to a foe's edge in campaign; ZoneSim's boss-stage goal = the lamp.
**Next, in order:**
1. Standing/idler bands (II: standing falls 80%+, idler 70%+; now 62% and 12%): the lever is a STAND CLOCK in story fights (H6's `teeth.json director.stand`, built for the arena director) in `logic/Play/Zones/Encounters.cs`, by tier. One numeric solver (su-lead-high, effort high).
2. The Flare: boss share 21-40% at I-II (owner's band AoE 10-15%, single 15-20%); a stander fills first because damage taken fills it (`logic/Sim/Flare.cs` FillHurt 0.40, FillBoss 1.8). Same solver.
3. Veteran III/IV not measured: `dotnet run -c Release --project godot/balance -- map --callings warden --level 30 --people dead,pack --grant cleaver:8,groundbreaker:8,heroic_leap:8,shield_charge:8,iron_vow:8,watch_bell:8 --grant-union bladestorm --bots standing,idler,human,deft --seeds 8 --tiers 3,4` (round-1 smoke, tier III dead people: 0 falls, mark gap 180-360 s: too easy).
4. Paths probe: print the host's ratio (~1.033x expected; Campaign off, so byte-same).
5. Item 9 NOT STARTED: her swing arc + the heavy chop's crack scar (BattleFx.Skills.cs Swing() lines 246-331 only, named to main; the scar at 309-315 is the judge's brown "crater"); steel family via fx_stroke or halved width/alpha, measured with tools/style/fx_measure.py; the pale "coins" are probably loot (M9).
6. Merge integration (junction rule), then the two clips (Low Ford first 10 min with `--auto`; a level-30 veteran's 5 min via dev grants), your own 1:1 look first, then one max judge; MR READY.
**Cost so far:** ~1.6M (lead ~150k; solvers A 227k, B 225k, E 145k, C 123k, C2 186k, R2 272k; $0 API). Est. to MR: ~0.8-1.2M.

## P6 Corvane in the doorway: MR READY (5 November, P6 lead 1)
Brief: `tools/scratch/coordinator/briefs/P6_lead1.md`; story: `docs/handoff/story.md` "Line items" (P6). Phase 1 of story night `vault_opened`: a new first stage, the court, in front of the door.

**Judge** (xhigh, API, 3 rounds, $2.50): r1 and r2 FAILED; **r3 gave PASS WITH KNOWN**. "The fight now reads at 1:1. The tell, pull, slam, knockdown, the Flare and the fall all land, and the round-2 failures are fixed." Verdicts: `survivorsunchained_inputs\combat_p6\verdict_r1..3.md`. Clips and frames: `r4`-`r8` (r8 is the one that passed).

**Harness** (`story --fight vault --stage court --bot standing,human,deft`, tier 1, 8 seeds x 4 callings):
| bot | result | kill time |
|---|---|---|
| standing | falls 100% | – |
| human | wins 100% | median 96 s, min 61 s, none under 60 s |
| deft | wins 100% | median 80 s |

The human Warden is slow (median 188 s). Scratch tools: `court.py`, `sum.py`.

**What is built (all numbers are data):**
- **The stage and the boss:** the stage is `Doorway` (`logic/Play/Story/Corvane.cs`); his script is `CorvaneStory` (`Bosses/`). His numbers are in `teeth.json story.corvane`; the court outline is in `boards.json story.vault_court`.
- **The talk and the choice:**
  - The engine can now open a conversation at a node and report the node it ended on: `IGame.Converse`.
  - `door_night` plays from `go_home`. "(Raise your weapon.)" starts the fight; he does not strike for 2.5 s after it. `go` lets the night go (`LetNightGo`, ArenaSpec.WalkedAway, the header "The night let go").
- **His one signature, "Lie down.":**
  - A 0.7 s tell: the lamp is raised, its light ramps up, and the bark stays over his head (signature barks are exempt from the bark band).
  - Then the kit pull (7 m, 7.5 below half life) and the heart slam, which knocks her down.
  - Below half life the only sign is the lamp burning brighter.
  - Between signatures he holds the doorway with lamp-swing cuffs. One bar, no phase bar.
- **The kill:**
  - `corvane.rose` is set.
  - Then the film, through P9's contract: `StoryNight.Cinematic("door", done, marks{corvane, her})`.
  - Without a film, the fallback runs: a 2 s hold on his body (`HoldOn`: the camera on him, no HUD, her controls held), "He gets up." as a caption, `Ev.Cue "door_sigil"`, `Ev.Fade`, the body gone and his lamp left lit at his mark, the gone caption, then the door opens.
- **A loss here:** the stage's OnLose sets `corvane.carried`, with no `shut` and no `corvane.rose`. `chid.carried_chid` now keys on rose OR carried.
- **Ground (agreed with P9):** the stand-in space `court`, gate `door` and points `court_in` (0,31) and `corvane` (0,25) are P9's lines too. P9's `--door-kill` `if` in `StoryNight.Begin` is removed when both branches meet.
- **Tests:** `godot/tests/CorvaneTests.cs`.
- **Tooling:**
  - The clip tool `tools/combat/court_clip.py`.
  - The autopilot answers dialogue choices (`--answers`).
  - `--cast-low` aims the Flare at the boss.

**Flags:**
- **Corvane's model, for P3:** the judge's distance is medium (about her height, no boss silhouette, a stiff raise). P3 remakes him with the Warden; the fight ships on the town model at 1.25 (PIPELINE P3).
- **For the C2 build lead:** "swing damage at the clip's contact frame" (A1's routing) is not in this item.

**Known (round cap):**
- Narrator captions are small and dim (the UI lead's caption style).
- The left-behind lamp is dimmer in the gone frame than in the hold.
- Damage numbers sit on his lamp during the tell (UI).
- The below-half change is modest (no pulse).
- The ring's top crosses the boss bar.
- The heart's brown-red under the night grade (H6's kit look).
- The arrival title card is drawn over him (UI).
- The Long Cut has no per-boss hit flash (H7).
- The talk portrait has no lamp.
- The set (door, sigil, court) is P9's.

**Cost:** about 1.1M tokens: lead ~270k; helpers code 239k, clip 86k, views 202k + 194k, r1 fixes 198k, r2 fixes 183k. API judges: $2.50.

## H6 the player must move: MR READY (4 November, H6 lead 2)
MR READY combat-h6@d7b977945 (code at 59ef5fc13)

**Judge (max, API, 2 rounds, $4.29):** round 1 FAILED on 8 exact fixes (the closing's gap off screen, marks under rocks, the knockdown's cause unread, a ring cast on her as she rose, small pips, the lane's outline-only start, barks across the fight, the gap's grid look). All 8 were made. Round 2 gave **PASS WITH KNOWN (8)**: every mark that killed the idler reads at the play camera at 1:1 with a crowd up (the ring, the charge lane + knockdown, the pull + red slam, the closing + wall + gap, the Ironback's slam), and "would a player have to move, and could they tell why? Yes, and yes." The whole frame is not yet AAA, but only for other leads' reasons. Verdicts: `survivorsunchained_inputs\combat_h6\verdict_r1.md`, `verdict_r2.md`.

**Gate (sim, 32 seeds x 4 callings, tier 1, the Pack's board; won/fell %):**
| bot | rc2 before | after |
|---|---|---|
| standing (never moves) | 2/98 | 0/100 |
| idler (the owner's play) | 41/59 | 28/72 (most falls before the boss) |
| kiter (reads nothing) | 35/65 | 9/91 |
| human | 94/6 | 84/16, lowest life median 0.27 |
| careless | 88/12 | 74/26 |
| deft | 97/3 | 97/3 |

The human is ringed 3 times a night. Strict "surrounded" (4 m, 3 of 6 sectors, 2 s) stays at 1, because movers get out in under 2 s. From minute 3 to the boss the human takes a median of ~30 kit marks a minute (`MarksPerMin` in the harness). Off-calling gate (`--offcalling --type both --minutes 30`, 8 seeds): dmg/min at 25 min is at most x1.14 (sunderer); PASS. The signature column shows inf/2.67 only where a road's skills can't be carried off-calling (carry rules, by design). Suite: 1526/0/10.

**Lead 2 did, beyond lead 1's sim items 1-5 and 9:**
- **6 Elite bars (N19):**
  - Cause: the code path was right, but a champion's bar sat at its FEET at 45% alpha while it had over 70% life, and read as no bar.
  - Now it sits over its head, bronze-framed, at full strength from spawn (`FoeMarks.EliteBar`).
- **8 Dash pips (N30):** 11 px copper beads under her bar, ready or spent, with a flare when a charge comes back (`HerLight.Bar.Pips`).
- **7 The turn (N27):**
  - Cause: her facing followed her eased velocity, not the stick.
  - Facing time on a 90/180 went from 250/267 ms to 67/100 ms. The lean now comes from her travel's curve, so there is none on a 180's plant, and the run blend follows her ground speed. The camera never yawed.
  - Code: `PlayerView.Update/Carry`, `PlayerState.StickX/Z`, plus `--fig8` and `tools/combat/turn_measure.py`. Strip: `combat_h6\turn\`.
- **5 Views for lead 1's mechanics:**
  - The closing's wall stands for its life.
  - The knockdown plays her `death_back` fast, then `get_up_back`. The caught lane is held and faded over 0.5 s, with dust along it and "Knocked down!".
  - The pull's slam is marked in the ring's danger red.
  - The closing's gap is placed on screen nearest her heading (the sim models the play camera: `Battle.OnScreen`/`GapOnScreen`). It has a cyan edge chevron when off screen, and a lit floor strip with a light curtain.
  - Red marks' decals also land on rocks. A charge lane shows a 25% wash from its first frame. Barks stay clear of her and of live marks, else they go to a band above the HUD.
  - Files: `BattleFx.cs`, `BattleFx.H6.cs`, `MarkPass.cs`, `Voices.cs`, `PlayerView.Knock.cs`, `Game.H6Shots.cs` (`--on h6` frames).
- **Sim fixes:**
  - A stand charge on her while she lay down chained 10 knockdowns 1.5 s apart. There is now a 2.5 s get-up grace and no stand clock while she is held (`Tells.KnockPlayer`, `Director.Standing`).
  - No new kit mark is aimed at her during a knockdown and its grace (`KitWait`). Boss scripts that call `Tell` directly are not covered.

**Derivation (PIPELINE rule 4):**
- From the game's need, the owner's demo-rc2 notes: the bars over the head, the pips, the knockdown and slam reads, the wall's view, the gap on screen, the bark placement.
- From a named reference, Hades and Diablo IV: the turn (facing within ~100 ms, the body after it, no camera yaw). The ARPG convention: the elite bar over the head.
- Inherited, each named: H1's telegraph kit and styles (`BattleFx`, `TelegraphRead`, 3 Nov); her bar's iron and copper (UI 15, `HerLight.Bar`); her `death_back`/`get_up_back` clips standing in for a knockdown clip (a stand-in, flagged below).
- Nothing was found built around an old hack.

**Flags for the coordinator (kept):**
- Accepted: the Reaver's armor 3 to 4 (every mode) and the softer tier-1 boss (bossHp 2.5 to 2.0, bossDamage 1.1 to 0.55).
- Known for rc3: tiers 2-4 are tuned at tier 1 only, and human/deft win 94-100% there.
- The kiter loses because it reads nothing, not because kiting doesn't pay.

**Known (judge r2, round cap):**
- H6's own:
  - Raised objects (a ledge, a log) still cover strips of a lane; both lanes still read end to end.
  - "Knocked down!" is salmon on a salmon lane and relies on its outline.
  - Unverified in stills: the edge chevron, the refill flare, the 2.5 s window with no new mark (a unit test covers the window).
- Other owners: the EMBER banner across rings and gaps (UI); crit numbers over the bark band (combat text); the HUD statues over the bottom ~190 px (HUD); an unlit black foreground shape (world/camera); the Flare's purple ring brighter than the closing band (Flare/H7).
- Animation items: a real knockdown clip (hers is a stand-in), a wolf feed clip (feeding wolves stand).
- Not covered: recalls from 14 m may be on screen; the two seen were off screen at both ends.

**Worktree note:** this worktree's `public/assets` had NO `.import` files (it had never rendered). Its 408 were copied from the main checkout's untracked ones and `--import` was run. Other fresh worktrees may lack them too.

**Sheets:** `survivorsunchained_inputs\combat_h6\` `night\` (r1 night), `look\` (each mechanic), `turn\`, `r2\` (r2 night + fix frames), `eb\`.

**Cost:** about 1.0M in all. Lead 2 ~165k. Helpers ~0.52M: worker 33k, turn solver 115k, views solver 168k, fix solver 204k. API judges $4.29. Off-calling and gate runs were CPU only.


Older blocks: history/combat.md (grep by keyword, never read whole).
