# Handoff: classes (phase 1, systems: the Lamps, the Flare, dash forms, reflexes)

Written by the second classes lead for its successor. Branch `classes/phase1`, worktree `.claude/worktrees/agent-a2a42cd8430929a76`. See the last line for the commit.

## 1. The owner's words

- 11 October 2026, on docs/design/CLASSES.md: **"go with all 8 recommendations"** (§8). The Flare: "it should be AWESOME. it should look AWESOME." (phase 2's job; ours is the logic). The bar: "we are striving for perfection".
- Story (via the main session): the twist "It takes less than it did": every rise from death costs a life in the valley, counted from the save (docs/story/TOLL_SPEC.md, being drafted). The Flare's clutch heals near death, so a Flare save is a rise avoided. Keep rise and death events clean and countable (`Ev.Rise`, `Ev.PlayerDeath`, `Ev.Flare.Clutch`, `Battle.FlareClutches`). Don't build the toll.

## 2. The brief (phase 1; CLASSES.md §7)

Battle wiring (dash forms, reflexes, the Flare's meter, window and clutch, Q firing it), the harness taught types, lamps and Flares, a plain debug readout, the road lean, the four Flare great blessings, and **every acceptance number in §7 measured**: types within ×1.35 of the median at tiers 1-4; on-calling at most ×1.25; a full board at night within ×1.25 of an empty one; Flare timing (first by ~2 min, then every 60-90 s at night, 2-3 per boss fight, 15-25% of a boss's damage). Names stay drafts for the story lead.

## 3. Done (sessions 1-2)

- Session 1: the board (`tools/classes/lamps_build.py` → `lamps.json`), `LampBook`, `LampLoadout`, Act renames, tags, Bound, save v5.
- **Dash forms** (`logic/Sim/Forms.cs` `DashForm`, called from `Battle.Dash`): the Kin rides the dash after its own wait (lamp's KinWait; learned forms: the art's Cooldown). Bull Rush 6 m behind 15% (Iron Hide 25%). Grapple's miss is a plain dash and the wait isn't spent. Vault goes the way of the dash. Mirror Step, Sprint, Wraith (1.5 s), Cinder and Echo ride the dash, and a second dash recalls the echo. The Kin's facets come only from lamps (`Character.Kit`); a learned form keeps ArtBook's.
- **Reflexes** (`Forms.cs`): `ReflexRun`, triggers crowd, swarm, low and every (ticked), big_blow and dire (on a blow; dire also when a Blow mark lands on her), swarm (a champion's blow), spells, perfect. A reflex borrows `p.AbilityCd` while it runs. Red Tide and Spellward are built. `Runs(kind)` and `HastenArt` replace the old `Ability ==` checks.
- **The Flare** (`logic/Sim/Flare.cs`): meter, Banked Flame charges, fills (hooks in HurtPlayerRaw, PerfectDodge, the warding-light block, HitEnemy, KillEnemy, spells), `UseFlare` (Strike holds ≤1.2 s, untouchable +0.4 s; Stand 1.5 s grace, pulses, guard cut/mend), burns missiles within 6 m, interrupts and staggers bosses, clutch below 25% (mends 20% over 1 s, reach +25%), hearth low-lamps, `Ev.Flare` Ready/Press/Blow/End, `FlareFreeze` 0.22 with the static `FlareFreezeScale`. Fill table tuned (solver 8b0a0fc0, then pass 3 at 482124f0); CLASSES §3.2 holds the tuned table. Damage: +8% a level, base powers ×11.5.
- Q / right-click calls `UseFlare` (WorldScene, Game). The HUD art slot shows the meter, and the `ArtNote` line shows form and reflex waits. `ArtBook.HoldKin` turns a held calling art into the Kin (in Create and the v5 migration). The Arts screen marks non-movement arts as "fires itself".
- `Character.Kit(ch, night)` folds the lamps; `Journey.StartBattle` passes `Lamps`, `ReflexRanks`, `Level`, and `FlareStart` (story fights start at 50).
- `LampLoadout`: rules stack across lamps (`Each`), with `HasOn`/`SizeOn` by skill and tags. A small lamp's rule sleeps by night.
- Road lean (`LevelUp.RoadLeaned`, ×1.25, clamp ×2 with the path lean). The four Flare greats (`Boons.FlareGreat`, offered only with a Flare). Map mods Smothered and "of the Bright" (Charts.cs). Endless: `EndlessFrom` set at the arena's Victory. MapRun is one Battle, so the meter carries between areas.
- The harness (`godot/balance`): `--type <road>|both`, `--lamps empty|suggested|full`, the Flare cast policy in `Pilot.Act`, and Flare and Types tables in the report. `Battle.BossDamageBy`.
- Tests: 787 green (HandsTests, ClassesDraftTests and LampsTests among them).

## 4. In progress

- **Rule wiring, warden quarter and crossings:** a su-worker was editing Arts.cs, Battle.cs and Weapons.cs at handoff (uncommitted). It commits with its report in the message body. Check `git log` and the working tree first; if it never committed, review its diff (`git diff`) and finish or reset it.

## 5. Next, in order

1. **Wire the remaining phase-1 rules:** reaver (32), arcanist (33), stalker (31), one su-worker per quarter, **one at a time** (they all edit Battle.cs). The shared brief is `docs/handoff/classes_rules_brief.md` (replace <CALLING>). Then add the test that every phase-1 rule id appears as a string literal in godot/logic/Sim (the generator script is in that brief's command). Check each worker's diff: sizes through `Size` (quarter by night), prices and thresholds through `Full`, counts capped at +1 by night.
2. **Re-run the acceptance sweep** (the runner's commands are in §7 below) once all rules are wired. Today's numbers (482124f0, rules mostly unwired) are a baseline only.
3. **Fix what's out of band**, then send it to a fresh `su-lead-max` judge with the reports, §7's targets and the owner's words. Known so far:
   - Casters' Flare gap is 104-116 s (target 60-90). Casters are rarely hurt. Consider a caster-friendly fill (Kindling-like spell fill in the base table) rather than raising the kill cap, which speeds up the reavers (already at 63-68 s).
   - The first Flare comes at 1.3-2.5 min. Clutches are about 0 (the deft bot is rarely low; a less deft bot would show them).
   - Types out of band: verge_hunter T4 ×1.96 and T1 ×1.39, roadknife T3 ×1.42, butcher T3 ×0.66, bulwark T2 ×0.68. Mostly the draft lean toward each road's signature skills (the skills' own balance) plus lamps without their gains. Re-measure after wiring; the skills' balance belongs to combat, so talk to them.
   - Full vs empty: today 0.63-1.24 (roadknife at level 30 is 0.63). Prices are in, gains are not. Re-measure.
   - On-calling ≤ ×1.25: not measured yet. The harness needs an off-calling run (the same skills drafted by another calling); add it.
   - Stands are unmeasured (the harness carries Strikes), as are story fights and maps.
4. Status page, roster and report.

## 6. Gotchas

- Workers' completion notices go to the main session, not to you: ask them to put the report in the commit body.
- `dotnet test` takes 3-5 min. Two agents building godot/tests at once lock `bin/`: run them in turn. The harness: `dotnet build -c Release godot/balance`, then `dotnet run -c Release --no-build ...`.
- Python edits to CRLF files are fine (git normalizes to LF).
- The context hook reads README's "Context budget: 120k" example as yours; the brief's 300k is the real one.
- Warden tests needing the Flare to fill use a reaver: Bull Rush's barrier soaks the damage.

## 7. Files and commands

- Read first: `godot/logic/Sim/Forms.cs`, `godot/logic/Sim/Flare.cs`, `godot/logic/Sim/LampLoadout.cs`, `docs/handoff/classes_rules_brief.md`, CLASSES.md §2.10, §3.2-3.4 and §7.
- Sweep (from the worktree): `dotnet run -c Release --no-build --project godot/balance -- arena --callings all --type both --lamps full|empty --tiers 1,2,3,4 --level tier --seeds 3 --policies greedy --people pack --bot deft --beyond 0 --par 16 --out <f>.jsonl`; the same with `--tiers 4 --level 30` for the end-game board; then `-- report --in <f>.jsonl`. The baseline reports are in the session scratchpad `sweep\` (they won't survive the scratch sweep, so regenerate them).

HANDOFF READY: docs/handoff/classes.md on classes/phase1@d26fb4d4
