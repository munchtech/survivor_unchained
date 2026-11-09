# Handoff: combat (skills' mechanics, enemies, encounters, bosses, balance, the maps, the story's nights)

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
