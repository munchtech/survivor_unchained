# Classes 22 (3 Nov): wave-1 fixed list done; MR READY; read this, then "Classes 21" below

Branch classes-22 (junction to its own public/assets). Scratch backed up to survivorsunchained_inputs/scratch_classes22 (solver/: ab.sh, pb.sh, j2.sh, v.py, st.py, pr.py, gate.py, ty.py; eq/eq.sh the sim byte check).

## Fixed list
1. **Moonweaver full board over the x1.35 types band: CLOSED AS KNOWN (round 1 of 2, no change shipped).** No single carrier: Echo ~2.5% of damage, the night's +1 projectile ~3% (Many Lights, or Crowded Sky in its place), the mark lamps together ~1.3%; all 15 road lamps dark is only -8.6%. Board pair lift (`--pair board --type moonweaver --level tier --bot deft --offwicks 1`, 64 seeds, about ±0.7%): T1/T3/T4 1.096/1.115/1.108, kindler T4 1.030. The gate (median dmg/min at 25, x1.35 of the median type) splits by faction at T4 (lamplings 592, dead 847, kerchiefs 1499, pack 1694k), so its CI90 there is about ±15%: real 2-3% trims swing it ±10%. On means the full board is 1.27/1.22/1.26/1.31 (T1-T4), in band; at 24 seeds kindler T4 full is 1.37 and reaver T4 empty 0.72 too. Variants (lamps_v2.json; k1 = Echo share 0.5->0.25, longer 0.25->0.5) read 96-seed T4 1.44, fresh seeds 1.32: not taken, picking by seeds would be cherry-picking. **For the next classes pass:** gate types on means or the median of per-faction medians (main's call); if a cut is still wanted, k1 plus a moonweaver-only rule for Many Lights' night +1 (`ArcanistProjectiles`, e.g. every second cast) is the route. Runs: solver/out (ab_*, w_ab_*, x_ab_*, f_ab_* fresh 97-192, pb_*, fe0).
2. **Lamps §14 signatures: DONE (89ac1ab3f).** In SurvivorUnchained.Rpg: `LampBook.PathTo/LightPath/Suggested/Sleeps/LinkPick/LinkChoices/SetLinkPick` (LampBook.cs; `LampBook.Check` = CanLight's rules without the spare count, shared by CanLight, PathTo, Suggest, Suggested), `WickBook.Sum` (+ `Weapon`, `RankIn`), records `LampSleep` and `WickSumView` in Rpg. LampAsk.cs: every ask a one-line call except CopyLayout (not on the list, still UI-side); its records deleted. Sim refactors, behavior-identical: `Battle.LinkPick(carried, pick, hint)` static (BoardRules.cs), `Character.GearSkills/DaySkills` (Kit's code factored). Tests godot/tests/LampAskTests.cs (6).
   - What the screen shows differently (for UI 31): Sleeps follows the sim, so ~54 `Feeds` lamps (Frenzy and the like, whose effects work on every skill) no longer dim, while tag, rite and link lamps now dim correctly; tag-only sleeps list matching skills in Skills plus Tags (LampBoard words only Skills); LinkPick names what the link would fire when she has no pick, LinkChoices includes gear skills; the wick-sum line now draws (Sum was null; LampWick calls it day only); PathTo finds far-lamp paths the stand-in missed. Sum's parts: base, rank growth, wick lead-ins as one +x%, each lit Turn last (multiply to Total exactly); no Hand or rite part, since nothing in the sim changes this number by Hand or rite.
3. **Acceptance and tests:** see "Acceptance" below.

## Acceptance (unchanged from Classes 21 by construction)
No balance number changed (item 1 shipped nothing) and the sim refactors are behavior-identical: harnesses built at f9372bbd9 and at 89ac1ab3f give the same records, sorted line for line (types full T1/T4 all callings 6 seeds, 96 lines; board pair T1/T4 all callings, 48; story all fights both pilots, 128). So the Classes 21 table below stands as measured (board alone max 1.22, warden T4 1.237 at 256; Act 1 -2.5%; types in band but the moonweaver full board, closed as known above). Rerunning it at its seed counts (~3 h CPU) would only reproduce identical records, so it was not rerun. Byte check: scratch eq/eq.sh.
- Tests (godot/tests/Tests.csproj, full run at 89ac1ab3f): 1459 passed, 0 failed, 10 skipped.

## Capability (the app can now)
- answer the Lamps screen from the rules themselves: the path to any lamp (lit all or nothing), why a lamp sleeps (the sim's own predicate), what a link fires and may bind, Light my way's next n without lighting, and a wick's whole sum that multiplies to the fight's number, day and night;
- prove a refactor leaves the sim unchanged in ~20 min (eq/eq.sh: two harness builds, three batches, sorted compare).

## Cost (Classes 22)
About 0.38M: lead ~60k, solver ~167k (round 1, ~4 h CPU), coder ~156k; no judges.


# Classes 21 (3 Nov): Phase 2 acceptance closed; MR READY; read this, then "Classes 20" below

Branch classes-17 (junction to its own public/assets; integration merged at 16bf3eeff). Scratch backed up to survivorsunchained_inputs/scratch_classes21 (j1.sh, j1b.sh, j2.sh, j3.sh, ct_table.py; fe.md and fe96/fe.md tables).

## Acceptance (Lamps v2 the default)
| Gate | Measured | Verdict |
|---|---|---|
| Board alone, every calling x T1-T4 at most x1.25 (64 seeds; Classes 20 run C) | max 1.22 except warden T4 1.24 | pass |
| Warden T4 at 256 seeds | **1.237** (bootstrap CI90 1.208-1.265) | pass |
| Act 1, never pressing vs "pre-Flare 11 Oct" (seeds 1-32, matched, `--flareuse 0`), within ±3%, falls no higher | boss 233->227 s (**-2.5%**), falls 0.125->0.057, won 95.6->98.4% | pass |
| Act 1, good use (Flare pressed), clearly shorter | -19.3%, falls 0.015 | pass |
| Act 1, v2 vs `--lampsv1` (pressing, 2048 runs) | +0.0% in every fight x hands cell (byte-equal: story fights light no board) | pass |
| Types within x1.35 of the median, T1-T4, lamps full and empty (deft, 24 seeds; arcanist and reaver roads 96) | all in band but **moonweaver, full board: T3 1.37, T4 1.45** (T1 1.35) | known, closed (below) |

- Act 1 cells (never pressing, 32 seeds a cell, noisy): dig +2.7/+7.4 (plain/deft), hollow -6.5/-5.2, roost -5.7/-4.1, vault -0.2/-6.3. The same on v1 and v2 (story nights light no board), so they are integration's, not this area's.
- **Moonweaver (known, after the demo):** v1 on matched seeds reads 216.7/811.4/1174.7k at T1/T3/T4 against v2's 229.0/831.1/1210.4k, so v2 adds 2-6%; the overage is the type's own (empty board T3/T4 1.25/1.16, its board lifting it x1.14/x1.21, as CLASSES §7 noted on 12 Oct at 1.38). It is 7% over at T4, not a hair, so no rule round. The fix would be a medium solver finding its carrier (likely the Echo or Moonfire rules), about 100k tokens and 1-2 h of CPU.
- The Long Cut's clip was missing from lamps_v2.json (Animation 61 put it back in v1 only): added, so the Flare plays its clip on the v2 default.
- Tests (godot/tests/Tests.csproj, full run at f6ccf883e): 1402 passed, 0 failed, 10 skipped.

## Night against day, by calling (what still visibly fires)
Every reflex fires by night on its full trigger and with its own hit; what changes is its numbers (a quarter) and a reflex barrier (a sixteenth).
- **Warden:** Shield Bash still bashes and stuns, a quarter as long; Concussion's stun a quarter; Shield Wall still rises, thin; Braced and Rallying Stand fire on their windows, with a quarter of their numbers.
- **Reaver:** War Cry still roars and frightens, a quarter as long, +% a quarter; Terror and Bloodlust fire as facets at a quarter; Red Tide still washes red with a quarter of its mend and +%.
- **Arcanist:** Time Slip still slows the world, about 0.833 instead of a third; Borrowed Time and Deep Slip at a quarter; Spellward still forms, a sixteenth thick.
- **Stalker:** Smoke Bomb still blooms, unseen and sure strikes a quarter as long; Mark Prey still marks, at a quarter of its strength and execute line; Executioner at a quarter; Choking Smoke's poison in full.

## Capability (the app can now)
- play the Lamps v2 board by night with every lamp's rule intact and its size quartered (facets, blue gifts, barriers, reflex numbers, statuses), held by the harness at x1.25 of an empty board for every calling and tier (`dotnet Balance.dll arena --pair board --offwicks 1`, read with scratch ct_table.py);
- check Act 1 against the named baseline on matched seeds, pressing or never pressing (`tools/classes/act1_match.py`, `story ... --flareuse 0`);
- `--lampsv1` keeps v1 for one release (LAMPS_V2_RULES "The flag").

## Not done
- The Lamps §14 MR ("Classes 20", Next 5): no signatures came through main during this session; it waits for after the demo.
- Deft board-alone report (Classes 20 Next 1): skipped; not a gate.

## Cost (Classes 21)
About 60k lead tokens, no helpers, no judges; CPU about 2.5 h of harness runs.

# Classes 21 starts here (2 Nov, coordinator wind-down): Phase 2 session 3 (acceptance): the board-alone band passes at 64 seeds; confirm warden T4, then Act 1, types, docs, MR; read this, then "Classes 20" and "Classes 19" below

Branch classes-17 (junction to its own public/assets; integration 0564eded0 merged at 716c6e85b). Scratch: survivorsunchained_inputs/scratch_classes20 (scripts t34.sh, k1-k3.sh, acc.sh, st.sh, wd.sh; tier_table.py `<dir> '<glob>'` per tier, ct_table.py `<jsonl>` calling x tier; runs by folder).

## Rules in (all v2, by night only; day and v1 byte-identical; main approved each as a rule by kind)
- **c20bb5e95:**
  - a reflex's lamp barrier (Shield Wall, Spellward) runs at a quarter of the quarter (`LampBarrier(..., reflex: true)`);
  - Frostfire's chill and burn run at a quarter (a status a rule lays carries its size);
  - Always Bleeding's price follows its gift: mends stop at 7/8 (`MendCeiling`). At half, the pilot held low played safe enough to read P 1.31 on the price alone; with no ceiling it read 1.21.
- **12c7f2cdd (medium solver), lamp facets and blue gifts keep their rule, not their size:**
  - helpers `Ward`, `NightCut`, `GiftSize`;
  - facet sizes are quartered: nimble, light_feet's speed, concussion and pile_driver stuns, snare hold (Battle.cs), cold_glass, terror, executioner, deep_slip, borrowed_time, second_hook, reel, bloodlust;
  - blue gifts are quartered: wall_holds, bearer_of_blows, flare.banked (only the banked BONUS; the Flare's own base hit is unchanged, which main required), plus the BoardRules draft blues;
  - prices stay in full;
  - facet own damage (gore's bleed, choking's poison) is kept in full on purpose.
- **c0c3a75e2 (worker), a lamp reflex's numbers are sizes, a quarter by night** (`ReflexSize`, applied only inside `RunReflex`; a Hand art keeps its numbers):
  - shield_bash stun; bulwark cut (`Player.BulwarkSize`);
  - warcry fear and +%; red_tide mend and +%;
  - time_slip world rate (about 0.833); smoke_bomb unseen and sure;
  - mark_prey strength and execute line (`Enemy.PreySize`).
  - The trigger (count, radius, wait) and its own hit damage stay. Spellward's barrier is the sixteenth above.

## Measured (plain, board alone `--offwicks 1`, 64 seeds a tier; CI90 of a 64-seed cell is about ±0.05)
- With c20bb5e95 only (acc/A_all):

  | | T1 | T2 | T3 | T4 |
  |---|---|---|---|---|
  | arcanist | 1.13 | 1.18 | 1.18 | 1.19 |
  | reaver | 1.15 | 1.13 | 1.21 | 1.22 |
  | stalker | 1.13 | 1.22 | 1.22 | 1.32 |
  | warden | 1.20 | 1.26 | 1.24 | 1.29 |

- With 12c7f2cdd: stalker T4 1.279, warden T2 1.215, warden T4 1.282. What still carried them was the reflexes' own numbers: Shield Bash's stun (warden T2/T4 1.12/1.20 with it dark), braced (about 0.04), smoke_bomb (about 0.05). That led to c0c3a75e2.
- **c0c3a75e2, the full measure (acc/C_all.jsonl): every cell ≤1.25.**

  | | T1 | T2 | T3 | T4 |
  |---|---|---|---|---|
  | arcanist | 1.14 | 1.17 | 1.19 | 1.20 |
  | reaver | 1.12 | 1.14 | 1.22 | 1.18 |
  | stalker | 1.10 | 1.22 | 1.18 | 1.22 |
  | warden | 1.16 | 1.18 | 1.21 | **1.24** |

  Warden T4 is within noise of 1.25: confirm it at 256 seeds.

## Next
1. **Acceptance:**
   - C passed every cell (above). Confirm warden T4 at 256 seeds (su-runner), from godot: `dotnet <bal>/Balance.dll arena --pair board --tiers 4 --seeds 256 --par 22 --offwicks 1 --callings warden --out w4_256.jsonl`. Build bal with `dotnet build -c Release -o <bal> balance/Balance.csproj`; it runs about 12 min. If T4 is truly over, the next carrier is braced's 3 s window, or Shield Bash itself.
   - Main's gate: every cell ≤1.25. For a borderline cell, rerun it at 256 seeds (su-runner) for a CI of about ±0.025. Only if a cell is still within noise of 1.25 at 256 seeds, propose "no cell significantly over" to main, with the numbers.
   - Medium solver only if a carrier has no rule-by-kind fix.
   - Also run deft as a report.
2. **Act 1:**
   - `story --fight all --callings all --seeds 96 --policies greedy,random --bot plain,deft --par 20` on this build (v2 default), plus `--lampsv1`.
   - `python tools/classes/act1_match.py <main checkout>/tools/classes/out/prefl11.jsonl X --cells` (prefl11 is seeds 1-32: match seed sets), and v1 vs v2 with --cells.
   - Say what moved and why. The facet, blue and reflex rules touch story nights too.
3. **Types:** `arena --type both --lamps full` and `--lamps empty`, `--tiers 1,2,3,4 --level tier --bot deft --callings all --seeds 24`, read with balance/classes_summary.py. The band is x1.35 of the median.
4. **Docs:**
   - LAMPS_V2_RULES "By night" (all rules above) and "The flag" (v2 default, `--lampsv1`); CLASSES §2.10 lines (lamp barriers, reflex numbers, facets, Always Bleeding's price follows its gift).
   - Main wants the MR to list, for each calling, the night-vs-day feel: which reflexes still visibly fire.
   - Then the full test once (godot/tests/Tests.csproj) and MR READY to main.
5. **Then the second small MR, the Lamps screen's §14 asks** (main approved; decided changes go to su-worker). The signatures are agreed with the Lamps build lead (agent aaee520051cff5068, worktree lamps-1; stand-ins in lamps-1 godot/src/Ui/LampAsk.cs). In namespace SurvivorUnchained.Rpg:
   - `IReadOnlyList<string> LampBook.PathTo(ch, w, id)`: the fewest unlit lamps, in lighting order, honoring gates (incl. Ungated) and home; empty if lit or unreachable; no Spare check. Plus `bool LightPath(ch, w, id)`: all or nothing.
   - `LampSleep? LampBook.Sleeps(ch, id)`, with `record LampSleep(string[] Skills, string[] Tags)`: null if it feeds something carried or nothing named. It must match the sim.
   - `string? LinkPick(ch, link)` (her pick, else what Battle.LinkSkill fires); `IReadOnlyList<string> LinkChoices(ch, link)`; `bool SetLinkPick(ch, link, skill)`.
   - `IReadOnlyList<string> Suggested(ch, w, n)`: no mutation.
   - #7 session undo is the UI's own. I told them that Unlight may reset `Now(ch).Flare`, and to undo newest first.
   - `WickSumView? WickBook.Sum(ch, skill, night)`, with `record WickSumView(string Stat, double Total, IReadOnlyList<(string What, string Value)> Parts)`.
   - Put both records in Rpg and tell that lead so it deletes its copies.

## Cost (Classes 20)
About 175k lead, plus a medium solver (99k) and a worker (58k). CPU only.

# Classes 20 starts here (2 Nov, wound down by the coordinator): Phase 2 session 3 (acceptance) half done; read this, then "Classes 19 starts here" below

Branch classes-17 (junction to its own public/assets). Scratch: survivorsunchained_inputs/scratch_classes19 (scripts abl.sh, ow.sh, f4.sh, t14.sh; abl_table.py; all .jsonl runs by folder).

## Done (Classes 19, all committed; tests 1402/0/10 with the flip, before the barrier rule)
- **Bug fixed (3ffdfecc3):** a v2 link (kills/status_kill/heavy) re-fired itself inside its own echo's blows: stack overflow on the warden's full v2 board. `Battle.RunLink` now starts the wait before `Firing.Echo`.
- **Why classes18's x1.65 is stale:** MR2's atlas points (30) made `--lamps full` a 37-lamp board (was 15). Same measure today: warden **x2.73**, arcanist x1.85.
- **The measure, board alone (`--offwicks 1`, Program.cs):** the off run keeps Light my way's wicks too. Wicks light by the ember's ranks at night on any board (CLASS_IDENTITY §3.3), so counting them only in the on run credited the board with them (warden: x1.97 without wicks vs 2.73 with). Report both readings in the MR; acceptance reads board alone.
- **The night rule for lamp defenses (Arts.cs `Ward`, `LampFacet`, `LampBarrier`; v2 only, v1 byte-identical):**
  - a lamp facet's barrier or mend runs at a quarter by night (shield_wall, iron_hide, rallying, unbroken, glass_heart, battle_trance, second_wind, stolen_moments, hunger, full_echo, soul_tithe, anchor); art-chosen facets keep theirs;
  - **a lamp's barrier is added to a held barrier without renewing its time** (Shield Wall, Spellward, anchor, perfect.barrier). It's the Shield of Morning precedent: renewed every bash, it kept every other barrier up for good.
- **The flip is in (5e2e12b6a, WIP until acceptance):** `Lamps.V2` defaults on; v1 via `SU_LAMPS_V2=0`, game/harness `--lampsv1`. LampsTests is pinned to v1 (a Balance-collection fixture); the `finally`s restore `UseV2(true)`.
- Harness: board pairs log `OnIds` (the lit lamp ids); `--dark id,..` is the lamp-level ablation.

## Measured (plain, T1, 64 seeds, board alone; P = dealt x taken)
| | before rule | after rule |
|---|---|---|
| warden | 1.49 | **1.27** (A 1.30 / B 1.24); deft 1.50 |
| arcanist | 1.85 | **1.25** |
| reaver | 1.19 | 1.19 |
| stalker | 1.13 | 1.13 |
- What's left for both is one reflex barrier on a fixed wait. Warden, Shield Wall dark: 1.07 (a sweep of its night size: 0.10 gives 1.21, 0.05 gives 1.15). Arcanist, Spellward dark: 1.08. At T1 her intake is about 0.7-0.9 hp/s, so even a quarter barrier every 7-8 s absorbs most contact damage.
- Every other warden lamp is within noise (hand, hold_fast, iron_hide+unbroken, braced, last crossing). Arcanist: frostfire and links add about 0.05 each; mirrors, time_slip, ash_walker and stand_in_fire are noise.
- **T1-T4 (f4/t14_all.jsonl, 32 seeds a tier, board alone, plain): higher tiers are WORSE, so the median doesn't save it.** Warden 1.30/1.32/1.35/1.37 (all 1.35); arcanist 1.28/1.26/1.39/1.30 (1.32); reaver 1.14/1.18/1.32/1.30 (1.27); stalker 1.14/1.20/1.20/1.26 (1.22). Taken carries it everywhere (dealt 0.96-1.07).

## Next
1. Not one lamp now: the band fails at T3-T4 for warden, arcanist and reaver. Ablate at T3-T4 first (`--tiers 3,4 --dark ...` per calling; the reaver hasn't been ablated yet). The likely shared cause is v2 rules read in full by night that cut damage taken. Then rule by kind: reflex barriers at half their art numbers (by night 1%/struck to 5% for the Wall, 5% for the Spellward; about P 1.21 at T1 by the sweep), plus whatever the T3-T4 ablation names. Target: every calling x1.25 at every tier T1-T4, plain, 64 seeds; deft as a report. If two rounds don't land it, send it to a medium solver (su-lead-high, effort medium) with this section as the brief.
2. Act 1 on v2 (now the default): `story ... --seeds 96` on this build, plus `--lampsv1` (equals integration). Run act1_match against tools/classes/out/prefl11.jsonl in the MAIN checkout (seeds 1-32) and v1 vs v2 with --cells. Say what moved and why.
3. Types: `arena --type both --lamps full` and `--lamps empty`, `--tiers 1,2,3,4 --level tier --bot deft --callings all --seeds 24`, read with balance/classes_summary.py (fe.md). Band x1.35 of the median.
4. Docs: LAMPS_V2_RULES "By night" and "The flag" (v2 default, --lampsv1), CLASSES §2.10 one line (lamp barriers). Full tests, then MR READY.

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
