# Classes 19 starts here (2 Nov): Phase 2, session 3 of 3 (acceptance). Lamps v2 data, sim, points, layouts and save v6 are in, behind a flag

The owner answered PHASE2_SCOPE (2 Nov): "Board + Lamps first". UI 25 (worktree ui-25) designs the Lamps screen from `board_v2.json`: keep its ids, kinds and positions FROZEN (tell main in one line if one must change). The contract between data and sim is **docs/design/LAMPS_V2_RULES.md** (read it first; its "As built" section says how the code reads it).

## Done (Classes 18)
- **Data:**
  - `tools/classes/lamps_v2.py` reads lamps.json (v1) and board_v2.json, and writes `godot/data/content/lamps_v2.json`. It holds 574 lamps with positions, groups, texts, effects, `price` on blues, and `draft: true` on the 286 new names.
  - Run order: `lamps_build.py`, then `board_v2.py`, then `lamps_v2.py`.
  - board_v2 fixes: road links gate 8 (35d221d27). Small groups' gates scaled to their size (428adf41f): hearth blue 8; bridge 2/4; crossing 3/5; Ford 1/3; Old Roads 3/4/7. A reachability check asserts that all 574 can be lit.
- **Sim:**
  - `Sim/BoardRules.cs` holds rites (9 mechs), links (11 triggers, picks in `LampLayout.Links`, Light my way's default pick, `Weapons.Echo`, `Ev.Link`, `Battle.LinkWait`/`LinkSkill`), Hand lamps (deltas on hands.json; off when Unhoused), the `tags.*` smalls and 16 of the 17 blues. Iron Pilgrim is phase 5 (it waits on the Return Turn).
  - LampBook on v2: Unhoused; unknown lit ids dropped on load. The `--board` pages compile and run on v2.
  - By night, smalls give only the road's lean (as v1).
- **The flag:** `SU_LAMPS_V2=1`, `Lamps.UseV2(true)`, harness and game `--lampsv2`. With it off, the Act 1 story sweep (24 seeds, all fights, callings, policies and bots) is byte-identical to integration 6c9c3a213. Tests 1394/0/10 at ead0ae9f4. Gate logs: Temp scratchpad `45b9ec4e.../scratchpad/classes18/gate`.
- **Open notes:**
  - The stalker Hand ladder may run hot (window 2 to 3 s plus pierce 2 plus a refund); trim `stalker.hand3` if the measure says so.
  - `Hands.Line` (the card) doesn't show Hand-lamp deltas yet (UI/card follow-up).
  - The Old Roads' `hand` rite lines list all four callings' versions; UI## Done (Classes 18, session 2; MR2 at classes-17)
- **Points:**
  - `AtlasLamps` is 30 on v2 (8 on v1). `Maps.Atlas.Complete` now adds a lamp on each tier's first clear (fact `atlas.tier.<n>`; nothing set `lamps.atlas` before).
  - Tiers 1-16 give 16; **the other 14 need atlas bosses, which don't exist yet** (known; for the endgame lead).
  - Relit posts: `LampBook.RelightPost(w, id)` sets the fact `lampposts.<id>`, which is a point (v2 only).
  - The four Act 1 posts are `PostDef`s in lamps_v2.json `posts`, each with a draft anchor (lowford, verge, waystation, lowford; x/z 0). Env places them, and the story writer writes the scenes (main noted both in RESUME).
  - Debug: `--relight id,id|all` (Game.cs, next to `--xp`).
- **Three layouts, each a whole build:** `LampLayout.Carried` holds the day slots. `LampBook.Switch(ch, i, world, zone)` works only in town (`LampBook.Towns`), not at night (dawn and dusk count as day), and not in a map or arena. Tests are in `LampLayoutsTests.cs`.
- **Save v6** (`LampBook.MigrateSix` from `Saves.Migrate`) runs on v1 too:
  - 3 layouts;
  - lamps refunded;
  - wick plans and link picks cleared (Light my way's strands);
  - skills she can't carry go to `World.Stash` as tomes;
  - carried skills copied into every layout.
- Tests 1402/0/10 at c0b2e1954. Flag-off story sweep identical before and after (4 seeds; MR1's was 24 seeds).
- **Board-full night measure** (`arena --pair board --callings all --seeds 64 --par 22 [--lampsv2]`, plain, tier 1; `tools/scratch/classes/board_ratio.py`):

  | | Warden | Reaver | Stalker | Arcanist | All |
  |---|---|---|---|---|---|
  | v1 | 1.62 | 1.13 | 1.10 | 1.04 | 1.19 |
  | v2 | **1.65** | 1.12 | 1.09 | 0.99 | 1.18 |

  The warden's P is mostly damage taken (x1.50; dealt x1.10, top source judgement_disc). Her defensive lamps (block, barrier, stones) carry into the night in full as rules. Raw data: Temp scratchpad `45b9ec4e.../scratchpad/classes18/board` (backed up to survivorsunchained_inputs/scratch_classes18).

## Next (session 3: acceptance, then flip the default)
1. **Warden board-full to x1.25 on v2.**
   - Find which lamp rules cut her damage taken by night (`--pair board` with LAMPS_OFF=id,... bisection, LampLoadout.cs).
   - Then rule how they cross into the night: a price-like "in full" vs Size. A block chance is a size, so a quarter by night.
   - Also run deft.
2. **Act 1 on v2:** within ±3% of integration, cells within ±6% (story sweep with `--lampsv2`, `act1_match.py`). Types within x1.35 of the median.
3. **Names:** ~290 `draft: true` names (and unnamed smalls) to the story writer via main.
4. When all three pass, flip `Lamps.V2` to default on (ask main), and delete v1 only after UI's screen lands.

_classes16_b9e8a09f.

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
