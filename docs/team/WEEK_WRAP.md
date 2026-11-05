# The week of 2-5 November 2026: the big upgrade, where it stands, and how to continue

Written by coordinator 6d561d13 (the last of the week) for the owner and for next week's first coordinator. Read this, then `RESUME.md`'s top block, then `OWNER_NOTES.md`. Everything below is on the integration branch `claude/vigilant-galileo-l6jqyx` unless a branch is named.

## 1. What this week was

Three days ago the game had a month of polished parts and no demo anyone had played start to finish. This week it got played three times, and each verdict turned into a hook pass with its own leads, judges and a tag:

| Tag | When | The owner's verdict | What answered it |
|---|---|---|---|
| demo-rc1 (be15a3570) | 3 Nov | "no hook" | H1 combat teeth, H2 the one look (R1-R4), H3 sound, H4 seams and the day stretch |
| demo-rc2 (377ca86da) | 4 Nov | "a lot better, still not polished; standing still wins" | H6 the player must move, H7 the Flare as an ultimate, H8 rc2's bugs and the tutorial fight, S1 Act 1 |
| demo-rc3 (d575f7e9d) | 5 Nov 04:10 | being played; notes not in yet | the next pass, from the notes |

Under the demo loop the owner changed how the game is built, in four decisions that now bind every lead (OWNER_NOTES, 4-5 Nov):

1. **Painted cel, as a system.** "A clever, proper art style that we can just build on": the Marvel Rivals kind of look, picked on L1's G1 target sheet ("love it"). `docs/design/LOOK_BIBLE.md` (14 rules with derivations) is law; the look is built as blocks (a shading model, a material library, lighting rigs, texture authoring, an FX language), and every frame is rebuilt to the blocks.
2. **One combat, one build.** The roguelite frame and the day/night dual ruleset are dropped. One character, one build, the same combat in town, maps and nights; the night's cards ARE the talent tree (every skill's Wick is real modifiers, lit for the night for free, lit for good at a lamp-post; the dawn card remembers what she liked).
3. **Remake over patch, tools on merit, and "make Marionette the pipe we pipeline through."** `docs/team/PIPELINE.md` is the ledger: every asset class has one source, one build command, one check, and a derivation line (nothing designed around an old hack is kept). Her body, gear, NPCs, hair and animation run through Marionette as app tools.
4. **The story as seven chains.** ChatGPT's rework is the spine (Ember Walker, the mother as the payoff, three endings); Act 1 is in data; Chid is Corvane, killable on screen.

## 2. Done and merged this week (what the player gets)

- **Combat (P6, P7):** foes with teeth and bars, a telegraph kit (ring, charge, pull, the Closing), a hover target, bosses with signatures and a carried light, the arena board with a lamp fold and lanes, a 12-minute tier-1 night with the boss at 10 (H1); the player must move: kill-or-cripple marks, a surround director, kiting as a pay-off, a standing bot that falls in 100% of tier-1 nights (H6); every Flare an ultimate from data (`flare_family.json`: the stop, the marks, the blow, two beats of sound; H7); the Corvane boss in the Vault's forecourt, fight as data, judged PASS at 1:1 (P6, 758fecd38).
- **Experience (H4, H8):** the seams between film, fight and town; the Low Ford day stretch; the shut gate until the ring is down; the Ford-Warden fight at a lesson's length (88-112 s); the dawn card as a click-through; the arena map; the boss camera; the x-ray legs fixed; C04b's walk in place fixed.
- **The look (H2, L1):** the ground painted from nothing through one preset (R2), the night crowd as dark forms with a cold rim (R4); the G1 painted-cel targets picked; Stage B built (the material library with audit 0 in all 13 frames, lighting rigs as data, the ink under effects, the FX band language); Stage C wave 1 built and judged ON TRACK (the painted ground system, eight of eleven marks, the wild kit: spruce, alder, rocks).
- **Sound (H3, P8):** the palette generated at -20 LUFS, the Flare's two beats, bells, steps, beds.
- **Story (S1):** Act 1 in data by node: beats 5-14, 59 new voiced lines, 0 re-records, 498 lines survived word for word; the P6 and P9 line items written from it.
- **Classes (C2 design, 34bd83b96):** `docs/design/ONE_BUILD.md` (the owner's page, the rule, the offer, dawn, the data model, a 16-item migration list, the harness note) and `godot/data/content/skill_lamps.json` (the Warden's 7 Wicks, 84 lamps, all real modifiers, two Unions; the checker enforces the judge's rules). The game does not read it yet: that is the build lead.
- **Marionette:** a private remote (`https://github.com/munchtech/Marionette`), 10 branches and tags pushed.

## 3. In flight at the week's end (branches, not merged; every lead handed off clean, nothing running)

| Branch (final sha) | Lead | Where it stopped | Step one next week |
|---|---|---|---|
| body-p1@7c32a9d92 | P1 lead 3 (handed off) | the topology ours (close 76.7k tris, play 21.5k), the build ours, her forms TIGHT (p95 1.73 mm), UVs, the bake DONE, in game behind `--body p1`, the skeleton placed by anatomy (five joints redone), the hip at best-known with a soft-tissue FEM route approved but not started; elbow/knee at round 2 of 3. Build output lost to a bad cleanup and rebuilt byte-for-byte (backed up to `survivorsunchained_inputs\body_p1_out\`). P1 ~9.65M | the A|B bare-shape gate (`docs/handoff/body.md` top): publish, reshoot the four pairs, the sheet, one max judge, the hip open on the sheet; the owner picks; then merge, the P2 chain and A1 Stage B |
| look-l1@46cb4d5ea | L1 lead 5 (handed off) | Stage C wave 2 BUILT, unjudged: the light, the ground forms, the wild kit, staging, the town kit, water, the campfire, the bolt, the UI bronze, and the color chain that derives every rig and surface color from the boards. Structure toward the targets, color not there (a mauve day cast, a brown night pool); only frame 02 would ship. Stage C ~3.2M + $2.13 | the day key's warm cast at its root in the grade, re-run the chain; the ground check on the Hollow and Barrow; then the 13-frame shoot, one judge, Stage D, `GATE G2 READY` (~1.0M + $12-17) |
| films-p9@5d24d74b5 | P9 lead 2 (handed off) | the hooks, the Vault set, C15 PASS WITH KNOWN as one 7.2 s shot; the three C13 films WIP and far from the bar because the placeholder Corvane and Barrow Lord wreck the frames (the blockers under them fixed); VO placeholders, the `mother` singer generated, unheard. P9 ~4.9M + $0.89 | the owner's call: do C13's door and arrival films wait for P3's remakes? (the lead's pick: build c13_end now, door and arrival on P6's fallback until P3) |
| motion-a1@3f0f35851 | A1 (stopped clean) | GATE M1 PICKED: the bible, 13 boards, the plan (REBUILD 108, RETARGET 10, CUT 37), MotionBricks + Kimodo, Marionette's remote | Stage B after P1's pick (`briefs/A1_stageB_lead1.md`) |

Integration at the wrap commit; the suite last green 1571/0/10 at 758fecd38 (the leads' branches: 1567, 1593, 1590 of theirs). Two incidents this week to carry into every helper brief: a P1 solver's cleanup permanently deleted a worktree's build output (the delete rule is in `lead_brief.md`), and a P9 helper force-closed every Godot process by name while it held the turn (README's never-kill-by-name rule) and installed `dotnet-stack` globally.

## 4. Where we still have to go (the order, from PIPELINE "The order" and DEMO_PLAN)

1. **The owner's rc3 notes** onto `DEMO_GATE.md` (Phase 3c, N39+) and a "demo-rc3 verdict" block in `DEMO_PLAN.md`; leads for the weight. The demo loop continues until a run passes start to finish.
2. **P1's gate pick**, then the P2 chain (gear re-fit on the base, the hair re-attach as a Marionette tool, R10 her painted pass: `briefs/P2_chain.md`) and **A1 Stage B** (her core motion rebuilt on the new rig, the Warden slice first, ~4.3-6.2M).
3. **C2 the build** (`briefs/C2_build_lead1.md`): the game reads `skill_lamps.json`; the offer, the dawn card, the Lamps screen, the harness bands, swings on the clip's contact frame; then the other callings' Wicks.
4. **L1 to GATE G2**, then the held restyles (R5 HUD "The Drowned Girl", R6-R9 the screens as one language, R12 the Warden remake) and P5's floors through the new kit.
5. **P9 merged**, then story Act 2 (chains 3-4), the storybook lore intro before C01.
6. **P3 NPCs on the base** through the Marionette fixer: the Warden boss-tier remake (the proof), Corvane's model (judged MEDIUM, ships on the placeholder at 1.25 until then), the dialogue-camera gate.
7. After the hook holds: the items pass (every equippable on her, every card says its job), her fight idle, her hits in audio, music as its own pass.

## 5. Costs this week (approximate, from the leads' reports)

Tokens: H1 ~1.6M, H2 R1-R4 ~1.8M, H4 ~1.7M, H6 ~1.0M, H7 ~3.0M, H8 ~0.9M, S1 ~0.9M, L1 ~5-6M so far (Stage B ~3.1M, Stage C wave 1 ~1.1M, lead 5 running), P1 ~9.25M so far (three leads; the topology, build, bake and skeleton are ours now), A1 ~0.5M, C2 design ~1.27M, P6 ~1.1M, P9 ~2.3M so far; coordinators ~0.2-0.25M each, about fourteen of them. API: under $30 in judges across the week; ElevenLabs credits for H3 and H7. Every pipeline's cost line is in PIPELINE.md so the second asset of each kind can be seen getting cheaper.

## 6. Housekeeping for next week

- **Disk:** C: was 136 GB free on 5 Nov at 02:30 and 61 GB at the wrap with four worktrees (32 GB), 8.7 GB of Temp scratch, `.git` at 6.2 GB and `godot/.godot` at 4.6 GB; the Recycle Bin is empty. The rest is the main checkout's growth (each `publish_p1.py` adds ~112 MB of glbs to git; `godot/.godot/imported`) and `survivorsunchained_inputs`. First job next week: `python tools/scratch/coordinator/wt_audit.py`, then find the 50 GB (`du` on the main checkout, `.git`, inputs); P1's glbs should move to a git-ignored build folder or LFS before more republishes.
- The main checkout shows hundreds of modified `.import` and untracked `.uid` files from Godot imports: noise, not work; never commit them by accident (`git add` by path).
- Worktrees at the wrap: main + body-p1, look-l1, motion-a1, films-p9 (cap 8). Remove each the turn its branch merges (`wt_remove.ps1`).

## 7. The prompt to continue next week

Paste this as the first message of a new top-level session in `C:\Users\munch\Desktop\survivorsunchained` (the coordinator; it spawns leads as its own subagents):

```
You are the main session (the coordinator) for Survivor Unchained, restarting the team after the week of 2-5 November 2026. Read, by section with grep and sed -n, never whole files: CLAUDE.md; docs/team/README.md (the bar, "Working lean", Safety, the roster); docs/team/WEEK_WRAP.md (the week's account, where we still have to go, section 3's branches); docs/team/RESUME.md top block (the wrap state: each branch's final sha and its lead's last line); docs/team/OWNER_NOTES.md top blocks; docs/team/PIPELINE.md (the ledger you keep; "Marionette is the pipe"; rules 4 and 6); the briefs in tools/scratch/coordinator/briefs/ (C2_build_lead1.md, A1_stageB_lead1.md, P2_chain.md) and docs/handoff/lead_brief.md. Owner calls pending at the restart, ask them in one line each before spawning: (a) do C13's door and arrival films wait for P3's remakes of Corvane and the Barrow Lord (P9 lead 2's pick: build c13_end now with a su-lead-max staging director, door and arrival on P6's fallback until P3); (b) the three C2 answers (the design lead's picks stand unless overruled).

First actions: (a) mcp__ccd_session_mgmt__get_session "self" for your own local_ id; put it in a takeover block at the top of RESUME.md (write doc blocks with the Write tool as a python script with forward-slash paths and run it with python -I, never through a Bash heredoc), commit and push; (b) the disk: python tools/scratch/coordinator/wt_audit.py, free space on C: (the 50 GB guard), find where the week's 50 GB went (WEEK_WRAP section 6); (c) bash tools/scratch/coordinator/watch_mr2.sh in the background (Bash, run_in_background): it exits on the first MR / GATE / HANDOFF READY line for body-p1, motion-a1, classes-c2, combat-p6 or films-p9, skipping lines in .claude/worktrees/watch_seen.txt; restart it after each hit.

Then, in this order, five leads at most at once, each spawned as YOUR subagent with the Agent tool (su-lead-high for P1/P2/P6/P9, su-lead-max for L1/A1/C2), brief = docs/handoff/lead_brief.md plus the area brief, with "Spawning: allowed" and "Context budget: 300k" as the FIRST LINES of the Agent prompt itself (the spawn guard reads only the prompt): (1) the owner's demo-rc3 notes, if they are in: onto docs/team/DEMO_GATE.md (Phase 3c, N39+, the Phase 3b table's shape) and a "demo-rc3 verdict" block in docs/team/DEMO_PLAN.md (the rc2 block's shape), then leads for the weight; (2) resume the four branches from their handoff tops: P1 (worktree body-p1, docs/handoff/body.md top) to GATE READY body-p1@ with the A|B at half size (python tools/half.py) to the owner, the MakeHuman-derived vs ours line; on the pick merge body-p1, then the P2 chain (briefs/P2_chain.md) and A1 Stage B (briefs/A1_stageB_lead1.md, worktree motion-a1); L1 (worktree look-l1, docs/handoff/art_style.md top) to GATE G2 READY look-l1@, the A|B to the owner the same way; P9 (worktree films-p9, docs/handoff/cinematics.md top) to MR READY films-p9@; (3) the C2 build lead (briefs/C2_build_lead1.md, a new wt_new.ps1 worktree classes-c2) on the owner's three answers (the design lead's picks are the defaults: skills by level, slots 2/3/4/5/6, Unions as one shared lamp). Merge each MR as it lands: git ls-tree <branch> godot/assets = 120000, bash tools/scratch/coordinator/merge_lead.sh <branch> then dotnet test in godot/tests in ONE background Bash (~6 min; last green 1571/0/10 at 758fecd38), push, powershell -NoProfile -ExecutionPolicy Bypass -File tools/scratch/coordinator/wt_remove.ps1 .claude/worktrees/<name>, the PIPELINE row's state and cost, the roster row, one line to the owner. Keep PIPELINE.md and RESUME.md current at every merge and milestone; quiet relays to the owner (decisions, pictures, merges, areas done, restarts only); commit as you go; never cd your shell into a worktree; cap 8 worktrees; hand off at ~200k with a RESUME block and start your successor the same way.

Standing rules: remake over patch; tools on merit; Marionette is the pipe; judges at 1:1 game-camera frames with the whole-frame question first; American spelling in game text; the 18+ tone; the owner: "permissions are bypassed ... you may automatically start new sessions when you need to."
```
