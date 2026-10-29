# Classes 15 starts here: Phase 1 P5b-P8 (P1-P5a are MERGED, integration 2fb912c2, 28 Oct)

Start a fresh worktree from integration (classes-13 is removed after the merge). Read CLASS_IDENTITY_AND_TALENTS.md §2.2, §3.3, §3.7, §6.2 (the Phase 1 row) first. The owner approved all 10 recommendations.

## Merged (Classes 13-14; numbers in the commits)
- P1 skills to data; P2 access + Act 1 days at 2/3/4 slots (levels 1/4/8); P3 six day slots + map retune (`MapRun.PackPerSlot 0.9`, `BossPerSlot 0.4`); P4 the four Hands (4184f71c); P5a Wicks and the 7 Turns in x0.90-1.15 (a8adb973; tier-1 Split/Wide/Linger 1.18-1.23 and Wide on the reaver 1.15 closed as known).
- Story bosses: hollow 113, roost 116 (37db3ebe), dig 131, vault 147. Act 1 gate (seeds 1-96 vs integration c2cf3a4b): never +0.6%, pressing +0.6%, cells -3.2 to +3.7%, falls lower. Tests 1259/0/10.
- Routed by main: the Act 1 DAYS playtest (not simulated; +1 slot and the Hands) is Experience's, in RESUME.

## Next, in order (Phase 1's remaining items; P7/P8 are this handoff's split of the §6.2 row)
1. **P5b:** Pulse and On-kill Turns at runtime, union lead-ins; full board + wicks at night within x1.25 of an empty board.
2. **P6:** the warden's 4 planned skills (Sunder, Groundbreaker, Rebuke, Watch Bell; lamp effects already in data) with wicks. Send the VFX list to main (skills VFX lead).
3. **P7:** wicks on the valley skills she starts with; the type pick at creation.
4. **P8:** the plain functional board and wick screen behind a flag (looks are UI's, later); the harness taught it; the Act 1 check, then MR.

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
