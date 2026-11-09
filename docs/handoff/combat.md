# Handoff: combat (skills' mechanics, enemies, encounters, bosses, balance, the maps, the story's nights)

## M3 combat systems, lead 1 (combat-m3, 9 Nov): HANDOFF READY (wind-down on the coordinator's word; see the last commit)
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

## H6 the player must move: start here (4 November, H6 lead 1; HANDOFF READY at ~250k)
HANDOFF READY combat-h6@8191d7b41 (code at 0f45049ec)

Brief: `docs/team/hook/H6_combat_move.md`. Worktree `.claude/worktrees/combat-h6`, branch `combat-h6` (from 0febc5160; integration had nothing new on 4 Nov). The coordinator that owns merges is session `local_4f5ceed0-79a5-47f5-81d6-a1ce170715d3`: send it MR READY/HANDOFF lines (5b4265e7 only relays).

**Answer to H8 (N20, the Ford-Warden; final for rc3):** teeth.json `prologue.fordWarden`, which H8 wires in Prologue.cs: floors by lamps BROKEN this fight (0 broken = 0.67, 1 = 0.34, 2+ = 0; a relight never takes a break back), ward [1, 0.7, 0.55, 0.4] by lamps lit, hpMul 1.25, minSeconds 60 and crackAfter 45 as backstops only. Band: human 60-120 s. **Not yet true in game:** H8 lead 1's last word: on the current code he fell in 11 s with three lamps lit; the unit test holds the floor, so H8's successor is finding the damage path that gets past it, then runs my two checks (an --auto run with crashes off to prove the 0.67 floor, and one at the 60 s backstop) and sends the measured times here. Check them against the band. (An "88 s" figure relayed earlier was not a run on the current code.) There is no Ford harness: careless and deft on the Ford are H8's `--auto` runs only.

**H7 (flare-h7, agent ab0d00104fc429aae) agreed:** a Flare that thins a closing's ring below 40% drops the wall ("break the ring"); the sim keeps it as is, and H7 adds no rule. Its Flare marks come from its own target queries, so the ring's foes get marked. After both merge, H7 times the wall's drop look (`Ev.ClosingWall {Up=false}` inside a Flare cast) to its shock band; nothing new to expose. Merge order: H6, H8, then H7.

**The finding that reframed the gate (approved by the coordinator):** the brief's standing bot (never moves, never dodges) already fell 98% on rc2's numbers. The owner's play is the IDLER (stands at the lamp, steps out only of what it reads; `--bot idler`): it won 41% and survived to the boss ~94% of nights. Healing from drops gave back about 6 lives a night (`HealBy` in the jsonl), and the wolves ran at her own pace (5.3 against her 5-5.6), so moving bought nothing. Gate: standing 80%+ falls; idler 70%+ falls with half before the boss; human 78-85% wins with low 0.27-0.35; deft 95%+; kiter beats standing; callings within 20 points; human ringed 2+ a night. Human read model changed (approved on one condition): kit marks read at 85% (careless 65%), lunge windups at 50/30%. **The condition: the judge must say every big mark that killed the idler is readable at the play camera with a crowd up; if one isn't, make the mark readable; never lower the bot's read rate.**

**State by item:**
1. DONE. Bots `standing`, `camper`, `kiter`, `idler` (Harness/Bots.cs, Human.cs `Idle`); measures in RunResult: `Surrounds` (4 m, 3 of 6 sectors, 2 s), `Ringed` (inside a walled closing as it rises), `MarksOnHer`/`MarkGapMax`, `HealBy`/`HurtBy`, and the director's counts; danger.py columns. `tools/balance/h6_tune.py` runs a data variant (SU_TEETH/SU_TELLS).
2. DONE (sim). telegraphs.json: ring 0.70; charge 0.40 + knockdown 0.9 s (`Ev.Knockdown`); pull 0.35 + a marked slam on its heart 0.7 s later (0.45); closing a WALL except at its gap, with a crush of 0.38/s from 0.8 s for 3 s (`Ev.ClosingWall`); kit from 0:45 on tiers 1-4 at x[1, 1.1, 1.2, 1.3] (`Battle.KitDamageMul`). **No view yet** for the wall, the knockdown or the slam's mark beyond the standard blow mark (next, item 10's clip will show it).
3. DONE (sim). `ArenaRun.Director.cs` + teeth.json `tiers.1.director`: pincer flanks every 60-90 s at +-140 deg of her heading, cut-off leaders, a surround that casts the closing on her (cooldown 12 s), stand charges from foes at 7 m+ (`standFrom`; the nearest died in its windup, so charges never landed), the lamp holder draws a flank after 30 s in the pool, stuck foes recalled (spawns must be reachable: the cause of N34), the snuffer bark + callout (unseen).
4. DONE (sim). The Ironback (`boar_ironback`, slow 2.6, ~1443 hp, an elite; slams the kit ring on itself at 3.2 m), from 1:30, one at a time, bark + callout once (unseen); wolves feed 2 s on a corpse when she is 8 m+ away (once per wolf per 15 s, 3 per corpse; **no feed animation**, they stand).
5. Partly: the snuffer is explained (bark, callout); the holder draws flanks; stuck foes fixed at the cause. Unseen in Godot.
6. NOT STARTED: elite bars (N19). The code path in `FoeMarks.Show` looks right; suspects: a full bar drawn at 0.45 alpha at the foe's feet (`_Draw`, `Full`), or champions flagged `Boss`. Needs one Godot frame.
7. NOT STARTED: the turn (N27). A solver measures facing lag, the run blend and camera yaw, then fixes; a figure-eight strip before/after.
8. NOT STARTED: dash pips under her bar (N30). A su-worker job (`GameHud.cs` has the charges).
9. DONE: the Ford-Warden numbers (above).
10. Sim gate PASSES at 32 seeds (0f45049ec, tier 1, pack): standing 0/100; idler 25/75 (88 of 96 falls before the boss); kiter 9/91; human 82/18 (low 0.29; by calling 78-91); careless 73/27; deft 96/4. Human ringed 3 a night; the strict `surr` stays at 1 (movers get out in under 2 s). Before (rc2's numbers, 32 seeds): standing 2/98, idler 41/59, kiter 35/65, human 94/6, careless 88/12, deft 97/3. **Still to do:** H1's off-calling gate (`--offcalling --type both --minutes 30`, every calling at most x1.25); the full suite after items 6-8; one Godot look at the new mechanics at the play camera (wall, Ironback, callouts, the recall's jump) before the judge; then the max judge on a tier-1 clip from 0:00 with the human autopilot (the whole-frame question, "would a player have to move, and could they tell why?", and the read condition above); round cap 2.

**Flags for the coordinator:** (a) the tuner raised the Reaver's `armor` 3 to 4 in archetypes.json (every mode: the human Reaver won 47-66% against 91-100% for the others); (b) the tier-1 boss is softer (bossHp 2.5 to 2.0, bossDamage 1.1 to 0.55), because the night now carries the danger; (c) tiers 2-4 with the kit on: human/deft still win 94-100% at 8 seeds, lowest life down 0.15-0.2; (d) the kiter loses because it reads nothing, not because kiting doesn't pay.

Files: `godot/logic/Play/Zones/ArenaRun.Director.cs`, `godot/logic/Sim/Tells.cs`, `godot/logic/Content/Teeth.cs`/`Telegraphs.cs`, `godot/data/content/teeth.json`/`telegraphs.json`, `godot/balance/Harness/{Bots,Human,Pilot,ArenaSim}.cs`, `tools/balance/{danger,h6_tune}.py`. Run data: the shared scratchpad's `combat_h6/v/fin.jsonl` (gate), `base.jsonl` (rc2), `idler.jsonl`. Cost: lead ~250k; helpers ~0.45M (solver A 112k, B 138k, worker 66k, tuner 129k).


## H1 combat teeth: start here (4 November, the H1 successor lead; MR READY after judge round 2)
MR READY combat-h1@d7b609a69 (code, suite 1498 green, merged with integration on 4 Nov; this handoff commit sits on top)

Brief: `docs/team/hook/H1_combat_teeth.md`. Worktree `.claude/worktrees/combat-h1`, branch `combat-h1`. **Judge round 2 (su-lead-max, max): READY for the owner's playtest after two color fixes, done and spot-checked** (f1e8dddbd: her whirl `slash_spin` ember gold, the kit ring in danger red, the lamp's pool ring dashed warm white). The whole-frame gate is NO on every run, mostly on H2-owned looks (the flat dark ground, pale fodder): it closes as known under the round cap. Sheets: `survivorsunchained_inputs\combat_h1\r1\` (round 1), `r2\` (round 2, whole-night runs from 0:00; `spot_final.jpg` the color fix), plans `plan_s*.png`.

**State by item (all DONE):**
1. **Danger** (harness, tier 1, 32 seeds x 4 callings, HEAD): careless won 75 / fell 25 (low 0.30), human 85/15 (0.31), deft 98/2 (0.41); fodder 3 hits, champions 9-9.5; boss ~130 s at 10:00. Falls are nearly all at a boss (the Barrow Lord, the Red Hand). The kit hurts (ring 0.46 + 1 s root, charge 0.37, pull 0.58, closing 4% a ring foe); the tier-1 boss x1.1. On the Pack's board (the demo), holders fall 0-6% with lowest life ~0.33 and non-holders 0-19%. Off-calling gate (`--minutes 30`): every calling at most x1.17-1.20 (pass).
2. **Foe health** bars (FoeMarks). 3. **Telegraph kit** (`Tells.cs`, `telegraphs.json`): ring | charge | pull | closing, never renamed; closing has a lit 3.5 m gap (new Ev.Telegraph `GapAngle`, `GapWidth`) and teeth (only on the kit's tiers, `Battle.ClosingTeeth`); tells near her are spaced 1.5 s apart (`Battle.KitWait`), with at most two fodder lanes. Looks: closing in horde red with inward streaks, pull violet spirals, fodder charge in the danger style plus a head flash, ring in danger red. 4. **Hover target** (`--pick champion` for the autopilot). 5. **Bosses distinct:** one kit signature each, behind a 0.7 s cast and bark (`ArenaBoss.Signature`): Pack-Mother charge, Barrow Lord closing, Grimtunnel/Gutterwick pull, Red Hand ring. Scales 2.4-2.7, tints, `EnemyDef.CarriedLight`, an off-screen pointer (`BossPointer.cs`), boss barks in a fixed slot. 6. **Board** (`boards.json`, `ArenaBoard.cs`, `BoardGen`; read by ArenaGen, the harness and the view; `MapBuild/ZoneMeta/ArenaRun.Board`): the Pack's tier-1 Hollow is cut to 52 m. The fold has its wall 9-11 m from the lamp, three 5-6 m gaps with warm door lights, lanes and a lamp: cold until 4:30, then the Flare fills x1.3 and kills pay x1.1 ember in its 7 m pool. Snuffers come from 5:00 (`Enemy.Goal`, douse 2/s, a cold-blue diamond); it relights after 2 s at the wick. `Ev.BoardLamp {X, Z, State lit|dousing|out|relit, Life 0-1}` is H3's contract; H2 lights the lamps as pools (`B.Glow` with its new `range`; `LightDef.Core`). `Balance.dll board --people pack --tier 1 --seed N --out plan.png` draws and checks it. 7. **Night length** 12 min, boss at 10:00.
Also: the Staggered banner once a foe, at most every 30 s (H4's note); "Executed" only for champions, bosses and the priority target, at most every 0.5 s; her silhouette through what hides her (`her_xray.gdshader`, play camera only); a hostile rim floor on foes past her lamp while a boss is up (`crowd_floor`; `--floor`); the arena lip's burn calmed under a boss (`lip_calm`, H2's to keep or revert); blood pools lighter. Tools: `--on tells` frames, `--hold-lamp yes|no`, `SHOTS_TIMEOUT`, `danger.py --lamp`, LampHold/NavField now in `logic/Play/Zones`.

**Closed as known (round cap; for the next combat lead or H2):** (a) the fold's wall reads as darkness and boulders, not a wall with doors (judge: medium, the source is the unlit dressing; H2's world restyle should light its inner face); (b) the fodder charge's edge width and chevron opacity are global MarkPass tunings (a per-mark shader edit); (c) fodder lanes are not counted in the 1.5 s spacing; (d) the Pack-Mother's moon texts stack (bark, CHANNEL BROKEN, Staggered, HER DEAD RUN) and the Flare has no boss job there (make only fire or the Flare break the moon-heal); (e) the off-screen pointer and the hostile rim are built but no judge has seen them; the silhouette has never been seen with her occluded; (f) the Pack-Mother runs 25-35% longer than the others at tiers 3-4 (87-96 s, inside her 90-120 contract); (g) stalker falls about 2.5x the warden's (archetypes.json: stalker 140 hp / armor 2; try ~155 or armor 3); (h) the Pack board's careless non-holders fall less than the target's 25%; (i) the plain hands fall 44-56% at tiers 3-4 on the Kerchiefs' and Lamplings' nights (outside H1); (j) the den's collider may be turned differently from its trunks (Hollow.cs, untouched).

Cost: about 1.6M tokens across 13 helpers (5 code solvers, 3 workers, 2 runners, 2 max judges, plus the lead).

Written by `a427a874da78cba8b` for its successor.
- **State:** everything is committed and pushed on `worktree-agent-a427a874da78cba8b`, merged with `claude/vigilant-galileo-l6jqyx` at `2d052564` (the fall card's conflict: UI's dark-until-the-result kept, with the controls held).
- **Tests:** 762, all green.
- **Earlier leads:** `a739d6792d21f5efd`, `a5115633c7006e4d4` and before. Their handoffs are in git history (`git log -- docs/handoff/combat.md`).

## 1. The owner's words

- **The bar:** "we are striving for perfection"; "AAA standard"; "I don't want to polish, I want to create perfection"; "do we have soul?" Ask whether it is the best version in any game, check it at full resolution, and don't stop to ask.
- **Story nights:** "much more specialized and fun - smaller arena - and they don't need endless - they have proper arpg end bosses".
- **Decisions** (top of `docs/design/STORY_NIGHTS_AND_TIME.md`): a loss wakes her at Chid's a day on; Redcowl can be spared or killed; one rise in Act 1 only, later only with the rise skill.
- **Working rules (5 October):** 3–5 agents at once; batch the Godot shots in one turn and look once; lean handoffs at about 500k tokens.

## 2. The brief, and where it stands

1. **The 1080 batch. Done** (four turns; the first exposed the autopilot, see 5).
2. **Experience's asks. Done:**
   - the spare-or-finish choice is put to her from anywhere, with a banner and keys (seen at 1080, laid out right);
   - the autopilot answers it (`--knee finish|spare`);
   - the Dig's boss runs to length.
3. **The six capped nights. Traced** (status page): four Dig sinkholes (fixed), one weak Roost night meeting the harness cap as it lost (now bounded), one bot wedged at the levy (hands).
4. **The Vault. Built**, measured and seen at 1080 (whole night 11:25 on the autopilot).
5. **Main session's ask. Done:** a night let go stands down at once (UI design's finding).
6. **The queue. Done:** the stalker's Finesse (+2% projectile damage a point).
   - **Not started:**
     - armour at depth (see 4 below);
     - the Hollow's fourth beat (needs story's words);
     - the Kerchiefs at tier 3, the Lamplings and the bestiary (the arena harness; old notes in `git show 94e1bf59:docs/handoff/combat.md` §4–5);
     - the cinematics hand-off hooks (`docs/cinematics/README.md` §6 item 11a; the Vault's is `c13`, and `BarrowLordStory.Hand` plays sights where no cinematic can).

## 3. What was done, and why (each a cause, measured)

- **`StoryChoice`** (`Play/Zone.cs`): a choice the story puts to her is the zone's, not an interactable.
  - `IStoryArena.Ask`/`Unask`; `ZoneRuntime.Choice`/`Answer(id)`.
  - Shown by `src/Game/GameChoice.cs` and `StoryChoices` in `src/Ui/WorldType.cs`.
  - Keys: use, then her art, held 0.6 s, armed after 0.8 s; keys already down when it comes up must be let go first; her art is not cast by them. A click chooses at once.
  - The boss bar goes while it waits; notices are held (`HoldToasts`) and the zone's banners wait (UI design's check: it stands in the banner's place). His lot, a broken levy (`Redcowl.loose`), the cage's men and a broken ring (`Greymuzzle.loose`) keep back; his end clears his marks (`CancelBlows`).
- **Grimtunnel climbs out** of the hole he came up through before it opens (`GrimtunnelStory.ClimbOut`, `holeOwed`). The hands go in on him dazed (`BossSense`).
  - Boss 2:30–3:00 planned, 4:00–4:40 careless; no capped nights.
- **`StoryBoss.Grows`:** past its hard mark every story boss's blow grows 3% a second. Lives of 10–13 minutes ended; careless wins fell about 5 points, still above the 70–80% target.
- **The Vault** (`Play/Story/Vault.cs`, `Play/Bosses/BarrowLordStory.cs`, `VaultTests`, `legion_standard` in `Enemies.cs`):
  - the place: three spaces (south, hall, stair); cover lies across the hall (`Cover`, `Clear` raycasts lanes against it); `StoryFight.Furnish` stands it;
  - the stages: the Decurion behind an eight-man `Levy` (×0.15 through it); the Scorpion (three bolt lanes every 4.2 s, ×0.3 beyond 9 m); the Signifer's three standards (`VaultOpened.Standard`, 0.85 of his health each);
  - the boss: health 130, Teeth 0.22, the ranks on the walls step in at each testudo; lift the standard with `bane.pole`; the front closes to 8 m (5 m when hard), and holy pushes it back.
- **`StoryNight.StandDown`** on a let-go: `Combat` off, marks, shots and patches gone, every creature `Scripted` and still, her controls held; the result still comes 2.2 s on.
- **The camera leans toward a story boss** (`FollowCamera.Toward`, a third of the way, at most 4.5 m). Greymuzzle fought under the HUD at the screen's foot.
- **Finesse:** `Stat.DamageOf(Tag.Projectile)` +2% a point (`Character.Kit`; `SelfScreen`'s line). At tiers 3–4, stalkers' bosses went from 149–204 s to 130–153 s planned, and careless wins from 66–81% to 81–91%.
- **Tools:**
  - `Picker` moved to `logic/Sim`, and the autopilot drafts with it (`--draft`, greedy by default);
  - the harness records `BossTurns`/`BossLife` and takes `--banes`;
  - `--end` ends a picture run at the night's result;
  - `--bosshp F` makes the boss F of its health (pictures of its end).

## 4. Armour at depth (analysed, not built)

- `StatBlock.ArmorReduction = a / (a + 20)` everywhere, whatever the attacker's level.
- Loot flattened armour's make curve to keep a full Heartwrought set near 70% (`data/content/loot.json`, `curves.armor` [1, 1.8, 2.8, 3.4, 4.0]).
- A level-relative fix would pass the attacker's level into `HurtPlayer`, for example `20 × (1 + 0.1 × (level − 1))`. That needs the general make curve back and a measurement in the map harness (`map --tiers ... --gear R`).
- Joint with loot (paused). Agree the target first: what share an at-level plate set should block at depth.

## 5. Failures and gotchas

- **The autopilot is no yardstick for length.** `--quick warden` is a levelled character with gear:
  - with first cards, Greymuzzle and Redcowl ran past seven minutes and never reached the knee;
  - with greedy drafts, the Dig's boss died at its floors (1:40).
  - Judge length in the harness, and staging at 1080.
- **The first `--bosshp`** lowered only his health: the phases' marks healed him back up to them. It now scales his maximum.
- **A `Button` doesn't size to its children.** Measured before its words were in the tree, the two answers ran into each other. Sync `CustomMinimumSize` each frame.
- **KayKit pieces:**
  - the hex flag is 0.28 m tall (the standard uses it at 11×);
  - `rubble_large` is 8 m long;
  - `PieceView` rolls about X only (use `IOrb.Face` for a yaw), and a pillar's origin is its foot.
- **The worktree guard** refuses `cd` and then git, `git -C`, and shell-variable or heredoc commands that touch git. A heredoc into Python works for edits. `.import` files show as modified after an import (line endings only): never stage them, nor the untracked `.uid` files.
- **Godot:**
  - the assets junction, `.godot` copied from an older worktree, and `dotnet build SurvivorUnchained.csproj` after logic changes;
  - the first import after a merge took 8 minutes;
  - a picture run with `--on boss` saves many tagged frames;
  - tools are in `scratchpad/combat7/` (`batch*.py`, `play.py`, `sheet.py`, `phases.py`, `an.py`, `falls.py`, `rep.py`).
- **The harness:** build to a fresh folder (`dotnet build -c Release -o bin/xN`). 1,536 nights take about 18 minutes at `--par 8` beside Godot.

## 6. Collaborators

- **UI design (`a565196002a51af40`):** told about `StoryChoices` (theirs to restyle), the stand-down, and the empty "What you take out" column after a story night.
- **Experience (paused):** to judge the choice, the camera's lean, and the Vault.
- **Arena art (paused):** the Vault's place and its cover's stand-ins.
- **Story (paused):** the Vault's two sights of mine (status page); the Hollow's fourth beat.
- **Cinematics:** the boss hooks.
- **Loot (paused):** armour at depth.

## 7. Files to read first

1. `docs/team/combat.md`, then `docs/design/STORY_BOSSES.md` §0 and §8.3.2.
2. `godot/logic/Play/Zones/StoryNight.cs`, `Play/Story/StoryFight.cs`, `Vault.cs`; `Play/Bosses/StoryBoss.cs`, `BarrowLordStory.cs`, `GrimtunnelStory.cs`, `BossSense.cs`.
3. `godot/src/Game/GameChoice.cs`, `src/Ui/WorldType.cs` (`StoryChoices`).
4. `godot/balance/Harness/StorySim.cs`; tests `StoryNightTests`, `RoostTests`, `DigTests`, `VaultTests`.

## Late notes recovered from unmerged branches (10 October cleanup)

Written by woken leads on 4 and 5 October after this page, and never merged. Check each against the code and later pages before acting; some may be done or stale.

From `worktree-agent-ac4ec5bbd2763a0df` (2026-10-04 eaf57e82):

5. **The story lead's brief for C14, "The Road Back"** (`a035208561a66c171`; script in `docs/cinematics/c14_road_back.md`). Fit it into the queue; build it before the maps if story needs it for Act 1.
   - **The fight:** story fight `night:road_back`, that night only, when `nell.road` = "with". Story writes `brannoc.road` once the fight exists.
   - **Setting:** people dead, 20 minutes. The place is the Low Ford road at the wagon and ditch: the prologue's Lowford zone at night if it can be reused, otherwise an arena dressed as the road (arena art's call).
   - **Boss: Wat,** "Over the Ford by Dark":
     - a big drowned carter: a drowned or risen rig, carter's coat, a copper toll-token in his hatband;
     - the cold trail;
     - silent, with no barks;
     - lesson: "He walks where the water was. Keep off the wet."
   - **Ally: Brannoc** with his hammer:
     - holds the edge of the lantern's light and never chases;
     - never dies (goes down on one knee, gets up);
     - his kills are not credited to the survivor;
     - his blow's word is "Down."
   - **Outcomes:** OnWin sets `nell.brought_home` true and gives nothing. OnLose sets nothing.
   - **Hooks for the cinematics lead's C14 cues:** spawn at the boss's arrival, and dawn at the win.
   - Tell story when it exists. They will add `brannoc.road`, the `nell.burial` morning variant and a RouteTests play.
6. **Then:**
  - **Delivered** on `worktree-agent-a1e3002b800ee55ac@eeadae6` (the VAT cache is now v9):
    - the wolf howl as the beasts' "cast" role: wolf, wolf_alpha, wolf_blighted, wolf_spirit;
    - a rally gesture as every person visual's cast. kerchief_brute and skeleton_minion keep their windup until a slam lands.
  - **Keep its two small edits in combat code:**
    - CrowdView's Casting uses `t = e.AnimT`;
    - Ai's grave-caller raise sets `e.AnimT = 0`.
  - kneel_shoot and slam wait on the owner's Kimodo run.
  - Its tool `godot/tools_scenes/crowd_sheet.gd` (VISUAL=, ROLE=, N=, STEP=, YAW=, OUT=) renders any crowd kind's role as a contact sheet. Use it to check the new kinds on screen.
- **Crafting (now `a97e32948c5bf419d`):**
  - Its endgame design is in `docs/CRAFTING_DESIGN.md` §20: scars pay fire, the atlas pays iron and bases.
  - I agreed these for maps:
    - the chart item gets heat (plain 4, fine 6, rare 8) and a pin slot;
    - map drops carry ilvl = creature level;
    - map materials are tallied at a map's end by `Crafting.Night`'s rules, and a fall spills half;
    - two kits (night and map) are fine.
  - **Open, yours:** Sigils, gear that bends one day skill in maps. Confirm a clean per-skill modifier hook (WeaponInst's evolution `Set` and `Mods` look like the place) or decline.
  - I sent crafting the economy medians per won night (tiers 1/2/3):
    - Kerchiefs' gold went from 45k/53k/43k to 2.6k/3.3k/2.8k (champions keep the day's gold);
    - champions are 864/1052/1079, within 10% of before.

From `worktree-agent-a708da2c97bf85c95` (2026-10-04 cdfe73f8):

0. **Arena art built the Hollow's place (`worktree-agent-a26767f7f9955cb56@f7c4c43c`, 662 tests green).** Merge it before touching `Hollow.cs` or `StoryNight.cs`:
   - **The place is mirrored in z.** Every capsule, gate and point of `HollowByNight.Ground` is negated, so the way runs up the screen, away from the camera: the clough at the bottom, the den at the top. Directions in this page and in STORY_BOSSES ("north edge") now mean the top of the picture. Nothing in the stages or Greymuzzle depends on direction.
   - `StoryNight.Open(gate)` also calls `G.Look.Show("gate:{id}", false)`. A shut gate is drawn as the ember's burning line, and it goes out as the gate opens.
   - **Deadfalls use the map's own fire lights** (`map.FireLights`) where there is one for the fire's id, so lighting one sets its wood burning.
   - `--night hollow [--stage N] [--lit]` shoots any stage; `--lit` lights every deadfall.
   - **Their composition ask, yours to decide:** from `boss_start` the den's mouth is 23 m up the screen, at the very top edge of the frame. Bring `den_mouth` in to about 18 m from `boss_start` and the root plate and his way out sit in the upper third. Check the ring (12 m round `den`), the guard's arc before the mouth, and the porch still fit, and rerun `StoryNightTests`.
- **Arena art (`a26767f7f9955cb56`):** built the Hollow to `HollowByNight.Ground`, mirrored in z (§4.3). They'll tell you before moving shapes.

From `worktree-agent-afe45df4957917614` (2026-10-05 ad59feee):

6. **Loot (`a9a9c345a35e1fcad`, built on their branch at `2404bf9f`; numbers are yours, in `data/content/loot.json`):** gear drops by source (champions 45%, minibosses and heralds one roll at least Uncommon, the boss two or three rolls), item level and make (a full Heartwrought set is about 60 armour, 75% reduction: measure it, likely a cap or a softer curve at the top), seven Legendaries and two sets, the belt at 20 of each draught. Already told them: keep "standing still" (Corran's Sword); change Forty-One Mouths' "at full health" (in a horde she is never at full); don't duck the sfx bus for a legendary's toll (telegraph sounds), duck music; Kell's Lamp should scale by day too. Measure the run-ups and maps with their drops in.
7. **Crafting (`af01b0d61ef656dd4`):** their `Marks.Gyre` → `"of_the_wheel"`, `MapRun.OnLoot`'s `Crafting.RulerMark`, `Chart.Pinned` and `Journey.GiveChart`'s heat are on their branch; keep them when they reach integration.

**Run-up levers, measured and dropped (branch `combat-wip-runups` e63e74fd, archived as tag `archive/combat-wip-runups`):** over 192 nights, the share of nights under half health went 10/2/4% before to 9/2/8% after, against a target of 10-20/3-5. Not good enough, so not merged; the code is in the tag if a successor wants it.
