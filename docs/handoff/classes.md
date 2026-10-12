# Handoff: classes (paused after phase 1; next is phase 2)

Written by the fifth classes lead. **The owner paused classes after the Echo fix** (11 October, via the main session): phase 1 is merged, phase 1b (this branch, `classes/phase1b`) carries the Echo fix and the moonweaver trim. A future lead picks up phase 2 cold from here. See the last line for the commit.

## 1. The owner's words

- 11 October 2026, on docs/design/CLASSES.md: **"go with all 8 recommendations"** (§8). The Flare: "it should be AWESOME. it should look AWESOME." The bar: "we are striving for perfection". Build order: phases 1 to 3 first.
- Story (via the main session): the twist "It takes less than it did": every rise from death costs a life in the valley. The Flare's clutch is a rise avoided. Keep `Ev.Rise`, `Ev.PlayerDeath`, `Ev.Flare.Clutch`, `Battle.FlareClutches` clean and countable; don't build the toll.

## 2. State

- Phase 1 (systems): done and merged (sessions 1-4; CLASSES §2-3, §7 "Phase 1, measured"). All 133 phase-1 lamp rules wired (`godot/logic/Sim/{Warden,Reaver,Arcanist,Stalker}Lamps.cs`), dash forms, reflexes, the Flare (`Flare.cs`), Q, the harness taught types, lamps and Flares.
- Session 5 (`classes/phase1b`, judged PASS WITH FIXES, fixes done, 818 tests green):
  - **The Echo:** its longer wait is a quarter by night, as its echo is (`ArcanistCooldownMul`; in full it was a net loss). §2.10 now names the three prices that follow their gift (Echo, Crowded Sky, Butcher's Count); every other price stays in full.
  - **Moonfire** is an arcane hit of 10% of the dead one's health (a quarter by night), not a Burn: as a Burn it seeded Pyre Burst's fire chain (14-17% of the moonweaver's full-board damage against 7-10% empty; halving its size did nothing, because the Burn's presence fed the chain). Its kills pass the mark at once, so it stops at depth 3 (`ArcanistOnDeath(e, credited, depth)`).
  - **Measured (48-seed medians, moonweaver 96):** types at T3 / T4: bulwark 0.91/0.80, butcher 0.80/0.82 (in band; 0.72 was 12-seed noise), chainbound 0.86/0.85, kindler 1.23/1.21, moonweaver 1.34/1.38 (90% 1.35-1.50), roadknife 1.16/1.18, sunderer 0.86/0.82, verge-hunter 1.09/1.15. Moonweaver full/empty 1.11/1.20/1.18/1.02 at T2/T3/T4/L30. The judge passed T4's 1.38 untrimmed: its excess is its empty board's (1.14), and a 2% trim is below what 96 seeds resolve.

## 3. Next: phase 2 (CLASSES §7 table; the beat and four Flares)

Phase 2 is the shared beat (time, grade, camera push, hitstop, last blow) and four Flares on grips we have: Bell of the Morning, Butcher's Hour, Burns Twice, The Road's Toll. It is mostly experience, VFX and animation work; the classes lead owns the logic and these open items first:
1. **Banked Flame in the pilot (L2).** Each hearth's gate-6 blue lamp (`flare.banked`) costs its price but the harness pilot never banks, so it reads as a trap: the sunderer's T4 Flare gap is 105 s with it, 72 s off (`LAMPS_OFF=flare.banked`). Teach `godot/balance/Harness/Pilot.cs` to bank when it is lit. Ask the owner (via the main session) whether "Light my way" should light it at all.
2. **The Road's Toll misses bosses on a full board (L3):** 8-11% of boss damage at T3-T4, 29% at T1. Targeting, not power: compare per-cast boss damage full vs empty before staging it.
3. **The butcher band:** in band at 48 seeds (0.80/0.82), but lowest of all; its empty board is the night skills' (phases 5 and 7). Watch, don't trim lamps.
4. Later (phase 7): the glow by day in maps is unmeasured; every blue lamp's net effect by night; Moon-Drawn reads as a slight loss (ablation 1.01-1.03 off); Moonfire's `Tag.Spell` makes each hit count in `OnSpellHit` (Forms.cs ~185: Kindling, "spells" reflexes): measure, or drop the tag.

## 4. Open with the owner (the main session relays)

1. **The Bulwark's rebuke share:** under 1% of a Bulwark's night damage; a judge asked 8-15%. Getting there needs more rebukes or a wider one (phase 5's "Wider Rebuke"), not a bigger number. Is under 1% fine (a defensive answer), or should it reach 8-15%?
2. **The home bonus:** on-calling adds little today (fitted home term median x1.03, range 0.85-1.22), because only one of each road's three signature skills exists until phase 5. Accept until phase 5?
3. **Story bosses vs the Flare:** Done (11 October, the owner's call): health raised x1.10 to x1.15 so each fight is back to its pre-Flare length (plain within 2%, deft within 5%); see CLASSES §7 "Open" (5). Falls: no rise beyond noise.

## 5. Gotchas

- Workers' and judges' completion notices go to the main session: spawn them foreground (`run_in_background: false`).
- Worktree-isolated agents: the bash guard refuses compound commands with variables; put harness loops in a script file in the scratchpad and run `bash <file>`. Never name a Python script after a stdlib module (`types.py` broke `json`).
- `dotnet test` takes 3-7 min. Harness: `dotnet build -c Release godot/balance`, then `dotnet godot/balance/bin/Release/net8.0/Balance.dll arena ...`. It reads `godot/data/content/lamps.json` at run time, so a lamp number change needs only `python tools/classes/lamps_build.py` (lamps.json is generated from `tools/classes/lamps_quarters.py`).
- **Noise:** a 12-seed cell swings about +-25%, a 48-seed cell +-8%; the harness is deterministic per seed but greedy drafts diverge after any change, so paired ablations are no less noisy. Band calls at 48 seeds for every type (all types' T3-T4 full at 48 seeds take about 25 min at `--par 20`); trims under ~5% can't be confirmed.
- Look at the per-skill split before trimming by number: the moonweaver's excess was a boon chain (Pyre Burst) a lamp unlocked, not the lamp's size.

## 6. Files and commands

- Read first: CLASSES §2.10, §3.2, §7 "Phase 1, measured"; `ArcanistLamps.cs`, `Flare.cs`, `Harness/Pilot.cs`, `godot/balance/classes_summary.py`.
- Full sweep (12 seeds, ~50 min): see the session-4 script `sweep.sh` in the main session's scratchpad `cl4b\`. Session 5's scripts and numbers: scratchpad `cl5a\` (`sheet.md`, `verdict.md`; `typeband.py <jsonl...>` types vs median, `boot.py` its bootstrap, `bys.py` per-skill split, `pick.py` a source's pick rate and share, `ablate.sh` LAMPS_OFF per rule, `exp.sh` a patched-number run).
