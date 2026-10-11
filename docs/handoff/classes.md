# Handoff: classes (phase 1, systems: the Lamps, the Flare, dash forms, reflexes)

Written by the fourth classes lead for its successor. Branch `classes/phase1`, worktree `.claude/worktrees/agent-a2a42cd8430929a76`. See the last line for the commit.

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

## 3b. Session 4

- `--flare stand` (harness; carries the road's Stand). The pilot fires a ready Flare after 15 s with four foes within 10 m (a kiting moonweaver sat full with its 5 m Stand).
- Game fixes: **the Flare grows 2% a lamp lit** (`Flare.FlareLampGlow`, `LampLoadout.Lit`; the full board's boss share had fallen to 14% at T4 and 9% at L30); **Moonmarked's mark is a quarter by night** (`ArcanistOnHit`; it lifted every blow on the marked by 30% at night); **a Crowded Sky the cap leaves nothing to loose stays dark** (`CrowdOn`; it was seeking for free beside Many Lights). CLASSES §2.10, §3.2 and §7 "Phase 1, measured" carry them. 813 tests green.
- Checks: Bulwark T4 and chainbound T2 full/empty are noise (x1.00, x1.01 at 48 seeds). Seeking Motes on arcanists isn't weak (probe: highest of all hosts); in runs it fuses into Starfall and the arcanist's other spells take the crowd first.
- Re-judge (su-lead-max, verdict in the main session's scratchpad `cl4berdict.md`): PASS WITH FIXES. F1-F3 done: chainbound 48 seeds x1.01; Banked Flame is the sunderer's slow T4 (gap 105 s, 72 s off); story bosses fall 14-29% sooner than on main (deft hands; listed, risk 4).

## 4. Measured (12 seeds, 1f4bc98f; scratchpad `cl4b\`: summary.txt, flare_table.txt, extras.txt)

See CLASSES §7 "Phase 1, measured". Types: butcher 0.72 (night skills), moonweaver 1.37-1.40 at T3-T4 and 1.46 at L30. Full/empty median x1.00. On-calling home 0.85-1.22. Flare first 54-123 s, gap 52-81 s, 3 per boss, 15-23% of boss damage.

## 5. Next, in order

1. If the main session hasn't merged classes/phase1, ask it (the judge passed).
2. **L1, before phase 3: the Echo.** In `ArcanistLamps.cs` `WaitMul` (~line 143) its wait shrinks with its echo by night: `m *= 1 + l.Full("the_echo", "longer", 0.25) * (l.Night ? Content.Lamps.NightSize : 1);` (a test beside `The_echos_wait_is_kept_in_full_by_night...`, which changes). Then moonweaver full vs empty at T3-T4, 48 seeds, and a trim if over x1.25 (Many Lights' +1 on a one-projectile spell is the next biggest: Rimeshard x1.25 in the probe). A short judge.
3. L2 (phase 2's pilot): bank when Banked Flame is lit; ask the owner (via the main session) whether "Light my way" should light it.
4. L3 (phase 2): why the Road's Toll misses the boss on a full board (per-cast boss damage, full vs empty).
5. L4-L5: the glow by day in maps; every blue lamp's net effect by night (phase 7).
6. Owner questions still open: the rebuke share; home x1.03.

## 6. Gotchas

- Workers' and judges' completion notices go to the main session: spawn them foreground (`run_in_background: false`) so the report returns to you.
- `dotnet test` takes 3-5 min; one build at a time in this worktree (workers run in turn). Harness: `dotnet build -c Release godot/balance`, then `dotnet run -c Release --no-build ...`. Never `-o`.
- lamps.json is generated: edit tools/classes/lamps_quarters.py and regenerate.
- Greedy arena runs are noisy (+-30% per run): 6 seeds for a look, 12 for a verdict. Python here needs C:/ paths.
- Signature skills: only one of each road's three exists; unions (Starfall) and evolutions change what a road's skill looks like in DamageBy (unions have their own id; evolutions keep the base id).

## 7. Files and commands

- Read first: the four `*Lamps.cs`, `Flare.cs` (fill table ~59), `godot/balance/Harness/Pilot.cs` (Flare policy, Bulwark stance), `classes_summary.py`, CLASSES §2.7, §2.10, §3.2, §7.
- Sweep (12 seeds, ~50 min): A = `--callings all --type both --seeds 12 --policies greedy --people pack --bot deft --beyond 0 --par 16`; `arena A --lamps full|empty --tiers 1,2,3,4 --level tier`, the same with `--tiers 4 --level 30`, and `--lamps full --tiers 1,2,3,4 --level tier --offcalling`; concatenate full+empty into fe.jsonl, `report --in` it (pipe through `iconv -f cp1252 -t utf-8` or the summary can't read it), then `python godot/balance/classes_summary.py <dir>` (needs off.jsonl, full.jsonl, fe.md, fe30.md).
- Last numbers: main session scratchpad `cl4b\` (and `cl4c\`: the 48-seed and story checks; `mainh\` is main's harness, exported by git archive, delete it when done).


