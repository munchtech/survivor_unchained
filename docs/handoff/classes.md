# Classes 18 starts here (2 Nov): Phase 2, session 1 of 3. The board v2 LAYOUT is in (fe334726c); next = the sim side

Read CLASS_IDENTITY_AND_TALENTS.md §3.2-3.6 and §6.1-6.2, then docs/design/PHASE2_SCOPE.md. MR2 (Phase 1) is merged (integration cdedeb76f). The owner hasn't yet answered PHASE2_SCOPE's order question (board+screen in parallel, then the Warden's wave; or the wave first). Main asked for the sim side to continue either way.

## Done in Phase 2 so far (classes-17, not merged; nothing in the game reads it yet)
- **fe334726c** `godot/data/content/board_v2.json` from `tools/classes/board_v2.py` (deterministic; it asserts every count, edge, reachability, spacing >= 38 and no edge grazing a lamp). It holds 574 lamps: id, kind, region, group, calling, v1 name, `v1` (kept from lamps.json), x/y (y up, the Ford at 0,0), `at`, and v2 gate (Strike 4; notables and links 8; blues and the Stand 16).
  - Kept from v1: 288 lamps, by their v1 id (the 72 `skill` lamps left for wicks).
  - New: 286 lamps, with ids like `{road}.s8/s9/n6/rite1-4/link1-2`, `{calling}.hand1-4`, `{calling}.hearth.p1/p2`, `{calling}.bridge.rite1/2`, `{cid}.rite1/2/blue/link`, `vigil.*`, `poachers.*`, `ford.*` and `path.{id}.*`.
  - Kinds: blue 45, rite 72, link 32, hand 16. Preview: survivorsunchained_inputs/scratch_classes17/board_v2.png.
  - Main has the sha; UI's design brief starts from it once the owner answers.
- §3.4 now says 32 links (main agreed: the region table's count).

## Next: the sim side (sessions 2-3, from §6.1's Lamps v2 row)
1. **Texts and effects for the 286 new lamps.** Extend `lamps_build.py` / `lamps_quarters.py` to emit v2 lamps.json from board_v2.json's ids, kinds and `at`, and add positions to lamps.json, so one source holds everything.
   - Rites: the calling's mechanic onto a tag; they dim with no such skill carried.
   - Links: a trigger that fires a carried skill she picks, one pick per link, its wait shown as a HUD arc.
   - Hand lamps: they deepen the Hand (`Content/Hands.cs`, `Sim/Hands.cs`, hands.json).
   - New blue lamps: the doc's examples (Iron Pilgrim, Drowned Lung, The Pack Remembers, Bell and Blade, Unhoused).
   - Smalls are never a bare +n%.
   - Rites and links need sim rules (new `R(...)` effect kinds read in `Sim/*Lamps.cs`).
   - Names: ask main for the story writer with a list (about 290).
2. **Gates 4/8/16** (`LampBook` reads `gate`).
3. **Points:**
   - levels, story bosses and atlas 30 (`LampBook.AtlasLamps` is 8 today);
   - Act 1's four relit lamp-posts (a world fact each; the posts' placement is Env/story's, so ask main).
4. **Three layouts**, each a whole build: board, wicks, carried skills, Flare (`LampState.Layouts` holds 2 board-only layouts today; DaySlotsTests pins the layout behavior). This goes with **save v6** (`World/Save.cs` Version 5): refund lamps, wicks on the suggested strands, off-calling skills to the storeroom as tomes.
5. **The functional pages** (ArtsScreen BuildLamps/BuildWicks behind `--board`) keep working on v2 until UI's screen lands.
6. **Acceptance:**
   - `--pair board` at x1.25 for every calling (`tools/scratch/classes/board_ratio.py`; the warden reads x1.53/x1.41 on v1);
   - Act 1 within ±3% of integration, with cells inside ±6%;
   - types within x1.35 of the median.
   - Gate scripts: survivorsunchained_inputs/scratch_classes16_b9e8a09f (gate.sh, bycall.py).

## Phase 1 record (MR2, merged)
- Hooks a/b (426ce9d64): art keys `rebuke`/`watch_bell` and `Ev.Barrier`; WARDEN_SKILLS_VFX_HOOKS.md.
- The P8 pages were fixed and shot at 1:1.
- Dawnpulse Turns S: Pulse 1.04/1.05, Linger 1.00/1.02, Fire 0.95/0.96 (deft/plain), all in band.
  - Phase 3 note: Fire on a warden's Dawnpulse reads P 0.80 because it drops the sear, and the card doesn't say so. School Turns should name what they replace.
- Open known: the warden ~7% slow on pressing (Flare fill); host probe 0.703 vs 0.70.
- Experience owes a verge-day re-run since the L1 grant.
- **Gotcha: a fresh worktree has no `.godot/imported`.** Robocopy the main checkout's `godot\.godot\imported` in (`/E /MT:8`), then `--headless --import` (about 2 min). Shoot scripts: survivorsunchained_inputs/scratch_classes17 (shoot2.sh: `--xp 3000` levels the quick warden, `--clicks X:Y` presses).

## Measuring
- Harness: `dotnet build -c Release -o <scratch>/bal balance/Balance.csproj` from godot. `story --fight all --callings all --seeds 96 --policies greedy,random --bot plain,deft --par 20 [--flareuse 0] [--storyhp roost=116]`, then `python tools/classes/act1_match.py REF X --cells` (about 20 + 19 min). Rule: overall within ±3% of integration, no fight x pilot cell past ±6%; confirm a cell near the edge on fresh seeds (`--seeds 192 --seed0 97`) before tuning it.
- An integration reference: build the integration tree's harness, run it with cwd at a folder holding `git archive <int> godot/data` extracted as `data/` (DataFiles searches the DLL's folder, then cwd).
- Hand measure: `tools/scratch/classes/hand_measure.sh` + `hand_ratio.py`; Turn measure: `turn_measure.sh` + `turn_ratio.py`. Map: `map --tiers 1,2,3,4 --seeds 8 --par 20` (`--maphp P,B` overrides).
- Last session's scripts and logs: `C:/Users/munch/Desktop/survivorsunchained_inputs/scratch_classes14_29e4fcb8` (story.sh, roost.sh, roost2.sh, fin2.out).
- Gotchas: harness runs need NO turn. Never launch with a trailing `&` (use run_in_background). Don't edit data JSON while a batch runs; the harness reads it at run time.

# Handoff: classes (session 17: wave 6a passes Act 1 and its judge; merge requested)

Written by the sixteenth classes lead (13 October), wound down at the coordinator's request. Branch `classes-11` (worktree `agent-af76b344999b70629`). Last commit: the last line of git log.

## The owner (13 October)
- "yes to the four questions" (OWNER_NOTES "Phase 6, the Flare plan"): (1) build wave 6a: the Long Cut, Drag Them Under, the Branding, One Arrow, and the Butcher's Bill for a new butcher; (2) the greatsword, hooked chain and longbow form in her hands in the calling's color for the Flare and vanish after (look item, the Flare lead's); (3) the four new modifiers (Thaw-Burst, The Eye, Free Hands, Through the Heart); (4) waves 6b and 6c are a separate yes later: DON'T start them.
- Standing: one role per Flare; every press seen; balance never blunts a Flare; Act 1 against "pre-Flare 11 Oct" (never pressing within ±3%, falls no higher; good use clearly shorter). Flares "are specialized ... pushing a flare should always do something visible"; a "planned 'BOOM' button".

## The coordinator's ruling
classes-11 does NOT merge until all five 6a Flares are measured (the Long Cut and the Bill sit on Act 1's default roads). Then: early modifiers, one su-lead-max judge on the wave's measures and roles, CLASSES §7, full `dotnet test`, then "MERGE REQUEST: classes-11@<sha>" with the event-format note below (sent through the coordinator, not to the Flare lead directly).

## Measured (session 16; S = scratchpad `cl11` of session 59a43b82; runs in S/out)
At `bossMul` 1.0, Act 1 seeds 1-96 pooled (1536 nights a side), staged against plain form:
- **Long Cut** (warden sunderer, default road): -9.0%, every cell -6 to -12%. Baseline: staged -19.2%, plain -12.7%, never +7.6% (falls 0.111 against 0.162; the sunderer type's own, not this branch). Crowd: story same as plain (96% in reach dead); arena kills a press 43 against 30, screen cleared 92% against 83%.
- **Butcher's Bill** (reaver butcher, default road; Single): -11.4%, falls 0.014 against 0.033. Baseline: staged -28.6%, never -1.1%. Crowd falls by design (kills a press 1.1 against 14).
- **One Arrow** (stalker verge_hunter; Context): -10.4%. Baseline: staged -29.1%, never +3.5%. Arena: in reach dead 78% against 100%, kills a press 12 against 85, won 90 of 96 against 94 (report it to the judge: the line isn't a room clear).
- **Drag Them Under** (reaver chainbound; Clear): pooled 1-96 -2.0%, cells -3.8 to +1.9%, falls 0.021 against 0.027: **passes at bossMul 1.0**. Baseline: staged -19.9%, never -0.7% (falls 0.152 against 0.125, the type's own). Arena share 28.8/25.0/25.9/22.9% (in band). But as a Clear it clears less than its stand-in in the arena: in reach dead 81% against 99.8%, screen cleared 51% against 99%, kills a press 25 against 39 (story: same as plain). Put this to the judge: a Clear should clear the room (the hooks' 24 cap, or what the knot leaves outside the slam's 4 m?).
- **Branding:** passes (session 15). Its dig/deft cell pooled b1+b2: +5.7% ± 3.6% (1.6 sigma), inside ±6%: noise, closed.
- **Arena share, full board (all three modifiers lit), deft, T1-T4:** Long Cut 35.5/36.2/36.2/32.8% (plain 28/24/26/24); Bill 25/30/29/35 (at bossMul 0.5: 22/25/24/27); One Arrow 30/27/31/26; Branding 23/21/24/22.

## bossMul found (rule 1: within ±3% of plain, no cell past ±6%)
- **Bill 0.5:** pooled 1-96 +0.9%, cells -1.5 to +5.0%, falls 0.022 against 0.033. Passes. (0.35: +5.4%.)
- **One Arrow 0.45:** pooled +0.9%, cells -4.6 to +5.4%, falls 0.038 against 0.029 (1.4 sigma). Passes. (0.55: -4.3% on 1-32.) 0.5 would sit about -2.5%: the judge may prefer it.
- **Long Cut 0.6:** passes. Fresh seeds 97-288 (3072 nights a side): -1.0%, vault/plain -2.5% (the -7.5% on 1-96 was noise); pooled 1-288: -1.3%, cells -4.2 to +2.1%, falls 0.024 against 0.021. (0.55: -0.7%; 0.5: +0.4%.) Its arena share is the open problem below.
- **Drag:** none needed (1.0 passes).

## Session 17 (done; merge requested)
- Commits: 08b3b8c1 bossMul fits; 677fffea and 6a799463 (solver: Line of Morning's fires take bossMul on a boss, GroundZone.BossMul; Through the Wall early); cf72d6a7, 39a1576e early picks; 841ef688 §7.1 wording; a158c433 Drag uncapped ("hooks" 0 = every one), Second Cut whole on a boss again (secondBoss stays in code, default 1).
- Numbers: S/sheet_6a.md (the judge's sheet), S/out/w17rep.txt, w17c.txt (early re-runs), w17d.txt (Drag cap 24/48/all), w17e.txt (final data). Verdict: S/verdict_6a.md. Long Cut full board 35.2/32.7/34.4/31.5% (near 35); one modifier alone at most 32.1%. Drag uncapped: 99.9% in reach dead, 100% rooms cleared, share at most 29.3%, Act 1 identical to cap 24.
- The "stalled" Through the Wall run (vault s1 random, 910 s) is a fall: every fight over 600 s in these runs has a fall (6 of 6). No bug.
- The story harness doesn't light early modifiers on its own: current data (early marks in) matches dt_staged run for run.
- `dotnet test tests/Tests.csproj`: 904 passed, 8 skipped, 0 failed.

## Next, in order
1. The owner's answer on single-target Flares (the judge's question, in S/verdict_6a.md item 2; sent via the coordinator). If yes: the Bill and One Arrow (and the Toll) rise until their arena share sits near 35%, measured on Act 1 against pre-Flare. If no: raise the Bill and One Arrow bossMul until Act 1 pools at about -2% against plain (first tries 0.6 and 0.55; 96 seeds; then the arena at 48 seeds, trimming Through the Heart's own number if it passes 35% at T4).
2. Early pick on the Long Cut's road: the judge asked for a visible one; Line of Morning (-8.2%, after the fix) and Second Cut (-8.1%, cell -15.4%) both fail Act 1, so Through the Wall stays unless one is retuned.
3. Never pressing against pre-Flare per type: sunderer +7.6%, verge hunter +3.5% (the types', in plain form too): phase 7, on RESUME.
4. Waves 6b and 6c wait for the owner's yes.

## Note for the Flare lead (through the coordinator; one event-format line each)
New Parts: brand, burst, pass (Branding); sweep, cleave, burnline, arrow, split (lines); hook, knot, grind, slam (Drag); leap, land, vault, chop (Bill). For "pass", "split", "leap", "land" and "vault", X/Z is where it starts (not her), TX/TZ where it ends. Line parts carry Angle and Radius = half-width. The look of the formed weapons (owner item 2) is theirs.

## Gotchas
- Write scripts to S and run them (the worktree blocks `$VAR` heredocs in some commands). `S/h.sh BUILD VARIANT OUT args...` runs a harness build from the worktree's godot dir (`-` = no variant, so the worktree's lamps.json). `S/v.py NAME plain=<id>` or `args.<flare>.<key>=v` makes a variant. Builds: `S/bal3` (all 6a), `S/bal4` (plus `--dark`): `dotnet build -c Release -o S/bal4 balance/Balance.csproj` from godot.
- "Full board" in the arena lights all three of a Flare's modifiers from level 1 (`Balance.dll suggest --lamps full`), so `--light` adds nothing there: use `--dark` to put them out.
- The baseline `tools/classes/out/prefl11.jsonl` holds seeds 1-32 only; read fresh seeds against the plain form.
- A story run of 512 nights takes 2.5 min alone, 5-8 min when two batches share the CPU.
- Harness runs need no turn (`turn.py` has no CPU lane); don't run two batches at par 20 with `dotnet test`.
