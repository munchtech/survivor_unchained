# Handoff: combat (skills' mechanics, enemies, encounters, bosses, balance, the maps, the story's nights)

## M3 combat systems, lead 2 (combat-m3, 9 Nov): MR READY (systems MR 1: the bands and the Flare; item 9 and the clips/judge follow as MR 2)
Brief: `tools/scratch/coordinator/briefs/M3_combat_lead1.md` (items 1-9) + lead 1's block below (items 1-5, 8 done there). Numbers: `docs/balance/m3_bands.md` (rounds 3-5 on top; commands there; veteran = variant B, six slots). Solver briefs: `survivorsunchained_inputs\scratch_combat_m3\solverS3/S4/S5_brief.md`, run scripts in `solverS5\` (`runv.sh`, harness `--over DIR` tests a data variant).
**Done this lead (rounds 3-5):**
- Stand clock in story fights and maps: `logic/Play/Zones/StandClock.cs` (H6's arena rule, one class the arena director also calls) and `PackKit.cs` (pack tells + stand clock, shared by story zones and maps); numbers per world tier in `world_tiers.json` `stand` (standGrow/standGrowMax at III/IV: a stand charge grows the longer she stands); maps pick their row by chart tier (`WorldTiers.ForMap`, past IV = IV). Maps were already Campaign fights.
- The Flare in campaign: `StoryFillHurt` 0.25, `StoryFillBoss` 1.2, `StoryFillHurtBoss` 0.06 (a boss fight = she struck/was struck by a boss in 8 s), held-back fill paid when the boss falls, `StoryBossCut` 0.13 of a boss's life per cast after multipliers (`HitOpts.Cap`): about one full-look cast per boss fight. Arena (Campaign off) byte-same; host ratio 1.033x.
- Fixed: `PressedSkills.GrantUnion` took a union's parts before checking room (refuses first now); `balance MapSim` started maps on world tier II (now `worldTier: false`, as Game.cs). RunMeter prints Flare boss casts, fill sources, boss life share.
**Final numbers (falls %; Low Ford I 32 seeds, II 16; veteran 8 x dead,pack):** Low Ford I: standing 100, idler 56 (band 70+: MISS), human 6 (no fall 94), deft 0. II: standing 100, idler 69 (77 at 48 seeds), human 19 (no fall 81), deft 12.5 (94 no fall at 48 seeds: noise). Veteran III: standing 100, idler 69 (one run short), human 0, deft 0; IV: 100/94/6/0. Flare boss life share 11-14% median for human/deft everywhere (band AoE 10-15%; a run reaching a ruler nearly full can still cast twice, max 24-28%).
**Knowns (named, not chased; round cap hit):** (1) Low Ford I idler 56%: the stand clock can't tell a melee human from the idler; the lever is a design call (a stand with no skill pressed for N s hits harder) or accept tier I as gentle: lead's pick accept, tier I is the first hour. (2) Worst no-mark gap 100-126 s at III/IV for human/deft (band under 90; lever: III/IV pack density). (3) Low Ford III with a fresh L3-5 warden too hard (III opens after act 1; judge III on maps).
**Next, in order (MR 2):** item 9 her swing arc + the heavy chop's crack scar (BattleFx.Skills.cs Swing() 246-331 only; steel family via fx_stroke or halved width/alpha, measured with tools/style/fx_measure.py); the two clips (Low Ford first 10 min with `--auto`; a level-30 veteran's 5 min via dev grants); own 1:1 look; one max judge; MR 2.
**Cost:** lead 2 ~60k; solvers S3 175k, S4 175k, S5 160k; $0 API. Total M3 ~2.2M. MR 2 est ~0.3-0.4M.

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
