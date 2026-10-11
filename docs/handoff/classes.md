# Handoff: classes (phase 1, systems: the Lamps, the Flare, dash forms, reflexes)

Written by the third classes lead for its successor. Branch `classes/phase1`, worktree `.claude/worktrees/agent-a2a42cd8430929a76`. See the last line for the commit.

## 1. The owner's words

- 11 October 2026, on docs/design/CLASSES.md: **"go with all 8 recommendations"** (§8). The Flare: "it should be AWESOME. it should look AWESOME." (phase 2's job; ours is the logic). The bar: "we are striving for perfection".
- Story (via the main session): the twist "It takes less than it did": every rise from death costs a life in the valley, counted from the save (docs/story/TOLL_SPEC.md, being drafted). The Flare's clutch heals near death, so a Flare save is a rise avoided. Keep rise and death events clean and countable (`Ev.Rise`, `Ev.PlayerDeath`, `Ev.Flare.Clutch`, `Battle.FlareClutches`). Don't build the toll.

## 2. The brief (phase 1; CLASSES.md §7)

Battle wiring (dash forms, reflexes, the Flare's meter, window and clutch, Q firing it), the harness taught types, lamps and Flares, a plain debug readout, the road lean, the four Flare great blessings, and **every acceptance number in §7 measured**: types within ×1.35 of the median at tiers 1-4; on-calling at most ×1.25; a full board at night within ×1.25 of an empty one; Flare timing (first by ~2 min, then every 60-90 s at night, 2-3 per boss fight, 15-25% of a boss's damage). Names stay drafts for the story lead.

## 3. Done (sessions 1-3)

- Sessions 1-2: the board, `LampBook`, `LampLoadout`, dash forms, reflexes, the Flare (`Flare.cs`), Q, `Character.Kit`, road lean, Flare greats, the harness's types/lamps/Flares (details in git log and CLASSES §2-3).
- Session 3: **all 133 phase-1 rules wired**, one file per quarter: `WardenLamps.cs`, `ReaverLamps.cs`, `ArcanistLamps.cs`, `StalkerLamps.cs` (thin hooks in Battle/Weapons/Arts/Forms). `LampsTests.Every_phase_one_rule_is_read_by_the_fight`. Debug switch `LAMPS_OFF=id,id` (LampLoadout) for bisecting.
- Harness: `--offcalling` (policy `road:<id>` holds to a road's signature skills, `RunSpec.For`), `godot/balance/classes_summary.py <dir>` (types, full/empty, on-calling three ways incl. the judge's calling x road fit), `Probe.Lamped` (fixed-build probe: `dotnet godot/balance/bin/Release/net8.0/Balance.dll lamped --seeds 12 [--evo mote_cascade]`).
- Fixes from the sweep: crowded_sky/the_echo/moon_drawn crippled motes; adders_patience cancelled every crit; boss fill counted a gate's whole Break (now health + Break up to 10% of health); the pilot fires the Flare by its reach (kiting casters sat full) and spares a shielded boss; path probes at 12 seeds.
- A su-lead-max judge (verdict "pass with fixes") then: block chance and Long Chain reach read in full by night (new §2.10 sentence: a rule's defining number stays in full); every block (Warding too) lays a stone; the lull is 6 s of calm, stones fall one a second, Mortar holds; Butcher's Count price shrinks with its gain; nights and maps start at 25, FillHurt 0.40, FillBoss 1.8, Strike powers raised (Burns Twice 1160, Branding 2100, Road's Toll 700, Drag Them Under 1590). A solver made the rebuke max health x10 x (1+8%/level) and the harness pilot plays a Bulwark standing its ground. 811 tests green.

## 4. Measured (12 seeds before the judge's fixes; Flare after them)

- Types (tiers 1-4): in band but T2 chainbound 0.72 and T4 moonweaver 1.42 (full). Level 30: arcanists 1.50, reavers 0.69-0.76. The empty-board spread is the night skills' (combat, phases 5 and 7); the judge says moonweaver's lamps add 8-13% more than the median type's, and chainbound's less (Long Chain reach now fixed).
- Full vs empty: 0.86-1.20 at tiers 1-4 (bulwark T4 1.26-1.34 after the solver, seed noise per it).
- On-calling, fitted home term: 0.87-1.20, median ~1.03. Never over x1.25; under 1.00 in 13 of 32 cells.
- Flare (ad68ee76): first 72-126 s (reavers 72 s: hurt fill), gap 66-81 s, boss casts 2.5-3.1, share 15-19%.
- Bulwark (7b97858e): 1.8-6.3 blocks/min, 5-17 rebukes a night, rebuke share 0.05-0.83% (judge asked 8-15%: the solver says unreachable without more rebukes or a wider one, a design question; CLASSES §2.8 has it).

## 5. Next, in order

1. **A full 12-seed re-sweep** (runner; commands in §7) on the current head, then `classes_summary.py`.
2. **The judge's remaining measurements:** e3 damage by source full vs empty for moonweaver T4 and kindler L30 (which rule gives +10-17%); e5 naive-hands (`--bot plain`) rows at T2-T3 (clutches, answers, falls); e6 `Probe.Lamped` for Oathblade, Axe Gyre, Dawnpulse full vs empty by night (over x2 means a rule does a size's job); e7 a Butcher's Hour (Stand) row: the harness carries only Strikes, so add a `--flare stand` option.
3. Moonweaver's motes in arenas are still 0.4-0.97 of other callings' (the probe says fixed): look at Starseeker (single-target evolution) vs Mote Cascade in the arcanist's drafts.
4. A short re-judge (su-lead-max) of the new numbers, the reavers' 72 s first Flare and the rebuke share question; then the main session takes the rebuke share and "home under 1.00" to the owner if the judge agrees.
5. Status page, roster, report.

## 6. Gotchas

- Workers' and judges' completion notices go to the main session: spawn them foreground (`run_in_background: false`) so the report returns to you.
- `dotnet test` takes 3-5 min; one build at a time in this worktree (workers run in turn). Harness: `dotnet build -c Release godot/balance`, then `dotnet run -c Release --no-build ...`. Never `-o`.
- lamps.json is generated: edit tools/classes/lamps_quarters.py and regenerate.
- Greedy arena runs are noisy (+-30% per run): 6 seeds for a look, 12 for a verdict. Python here needs C:/ paths.
- Signature skills: only one of each road's three exists; unions (Starfall) and evolutions change what a road's skill looks like in DamageBy (unions have their own id; evolutions keep the base id).

## 7. Files and commands

- Read first: the four `*Lamps.cs`, `Flare.cs` (fill table ~59), `godot/balance/Harness/Pilot.cs` (Flare policy, Bulwark stance), `classes_summary.py`, CLASSES §2.7, §2.10, §3.2, §7.
- Sweep (12 seeds, ~50 min): A = `--callings all --type both --seeds 12 --policies greedy --people pack --bot deft --beyond 0 --par 16`; `arena A --lamps full|empty --tiers 1,2,3,4 --level tier`, the same with `--tiers 4 --level 30`, and `--lamps full --tiers 1,2,3,4 --level tier --offcalling`; concatenate full+empty into fe.jsonl, `report --in` it, then `python godot/balance/classes_summary.py <dir>` (needs off.jsonl, full.jsonl, fe.md, fe30.md).
- Last numbers: scratchpad `sweep12c\summary.txt` (won't survive the scratch sweep).


HANDOFF READY: docs/handoff/classes.md on classes/phase1@1fb99f6f
