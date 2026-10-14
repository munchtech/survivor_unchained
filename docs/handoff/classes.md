# Handoff: classes (session 18: the owner's boss rules; paused by the owner after this session)

Written by the eighteenth classes lead (14 October). Branch `classes-12` (worktree `.claude/worktrees/classes-12`, `godot/assets` a junction to its own `public/assets`: never `git stash`, `reset --hard` or `checkout .` there). Last commit: the last line of git log. NOT merge-ready (see "Paused here").

## The owner (13 October, final; OWNER_NOTES "13 October 2026, evening", last bullet)
"things should hit what their tooltips say"; "we need to just buff the bosses I guess". No hidden boss-damage multipliers. A Flare's share of a boss: room-clearing (Clear, Save) 10-15%, single-target (Single; One Arrow with a boss near) 15-20%, by boss health and the Flares' own numbers. A Flare stays the hardest-hitting press on a boss; if not, change visible numbers. Act 1: never pressing within ±3% of "pre-Flare 11 Oct", good use clearly shorter.

## Done (all on classes-12)
- **bossMul and secondBoss retired** (c8a8891a): FlareStaged.FlareHit, FlareLines (Second Cut, Line of Morning's fires), GroundZone.BossMul gone; lamps_quarters.py has no bossMul.
- **Hidden boss multipliers made visible** (51c61c0a): a skill's card says what champions and bosses take (`WeaponDef.BigMul/BossNote/Card`: its BossDamage, and summons' double); Spirit Companion's text says its wolves hit them twice as hard; One Arrow's text: "A boss takes each of its hits double" (0677c1aa). Called Shot already said its 60%.
- **Harness:** `--hits 1` (each source's hardest blow and best 1.2 s / 6 s on bosses: `Battle.TrackBossHits`, result fields BossBestHit/BossBest1/BossBest6), `--bosshp`, and the solver's `--flareglow --fillboss --flaregrow --fillcrowd --bossonly --bosstiers` (dd229207). Story set pieces' blows on bosses are credited "story" (aa5b355a).
- **The bands, as defaults** (solver dd229207's candidate, made the defaults in ccdf2f5a):
  - Arena bosses: `ArenaBoss.FightHealth` = its T1 HealthMul × Toughness 2.5 at every tier (tier slope dropped; keeper/core health still read HealthMul). Arena boss fights go from ~65-85 s to ~83-153 s: the cost the owner should see.
  - While she fights a boss (struck one in the last 5 s), kills and champions don't fill the Flare (`Battle.BossOnlyFill`). Why: the arena's horde refilled it ~3× faster than Act 1; boss health alone floors near 13% at T1.
  - No lamp glow (`FlareLampGlow` 0.02 -> 0; Act 1 lights 1-2 lamps, so it fed the arena only).
  - Called Down drops its embers on frozen things only, as its lamp says (a boss keeps its four seeking embers).
  - Strike powers: Long Cut 497, Bell 597, Bill 240, Drag 937, Burns Twice 932, Branding 1154, Toll 584, One Arrow 1180 (from 1380/920/520/1590/1160/2100/2100/2990); Through the Heart "heart" 0.6 -> 0.15.
- **Why boss health alone couldn't do it (measured):** a press is 20-53% of an arena boss at ×1, more than the phase has left, so presses are cut short at the gate and raising health first gives that damage back (kindler and verge_hunter shares rose with health); and presses per arena boss stay ~2.3-2.7 because the meter fills from boss damage as a share of its health.

## Measured (scratch S = `%LOCALAPPDATA%\Temp\claude\C--Users-munch-Desktop-survivorsunchained\34daaf5d-...\scratchpad`, runs in S/out; scripts h.sh, v.py, an.py, san.py, raw.py, ttk.py, crowd.py, sweep.sh, story.sh)
- Solver's candidate (flags; S/out/c7_*, s2_*), arena Strike share T1/T2/T3/T4 (mean): sunderer 17.8/15.1/12.7/13.9 (14.9), bulwark 11.4, butcher 14.5 (Bill then 228; 240 lifts it ~1 pt), chainbound 11.8, kindler 10.1, moonweaver 12.1, roadknife 21.3/17.5/11.2/**6.9** (14.3), verge_hunter 20.3 (Arrow then 1224; 1180 lowers it). Crowd clear unchanged (99.6-99.9% in reach dead). Stands (reported): 1.7-14.9; Butcher's Hour reads 0 (its damage isn't credited to the Flare).
- Act 1 (same candidate): Strike shares 10.3-13.5 (AoE), Bill 18.4, Toll 18.7, Arrow 16.6; moonweaver at the vault 8.3; good use -15.8% vs pre-Flare (233 -> 196 s), falls 0.125 -> 0.043; never pressing unchanged (story health untouched).
- **Defaults verification launched** (b7 = 780979e8): S/out/sweep_v7.txt -> v7_<type>_{strike,stand}.jsonl (32 seeds), then S/out/story_s7.txt -> s7_<type>.jsonl. Read with `python S/an.py S/out/v7_*.jsonl`, `python S/san.py S/out/s7_*.jsonl`, and `tools/classes/act1_match.py tools/classes/out/prefl11.jsonl <s7 default types pooled>`.
- `dotnet test`: 905 passed, 8 skipped, 1 failed before 780979e8 (One Arrow's heart test, fixed to read its data; FlareLinesTests 8/8 pass). Re-run the full suite before any merge request.

## Paused here; next (in order)
1. Read the v7/s7 verification above. Roadknife T4 (6.9%): the kit's poison takes ~67% of the boss and pins it at its phase gate where the Toll can't hurt it. Butcher's Bill and One Arrow: confirm 240 and 1180 land in band in both modes.
2. **Hardest-hit floor fails in 21-28% of arena runs** (best other source in 1.2 s over the Flare's). Offenders: Whetstone (boon:serration) bleeds, open_vein (butcher lamp: the bleed burst), the roadknife's poison (×5 the Toll), the bulwark's rebuke. **Root finding, for the coordinator/owner:** damage over time double-dips. A status takes the blow's damage after every multiplier as its base (`Battle.HitEnemy` -> `ApplyStatus(e, o.Status, dmg, ...)`, procs `ctx.Damage = dmg`), and each tick runs through `HitEnemy` again (DamageMult, sunder, stagger, mark, lamp muls). So Whetstone "bleeds 30% of the blow over 3 s" deals several times that, including off the Flare's own crits (Flare hits fire procs). That breaks "hits what its tooltip says". The fix (ticks don't re-apply what the base already holds) moves every DoT build: it is phase 7's sweep, with a su-lead-high number solver.
3. A max judge on the measures and roles (sheet: the tables above, the owner's words, the arena fight lengths), then CLASSES §7 rewritten (acceptance item 1's bossMul sentence, item 2's bands, "Phase 6a, measured", the roles paragraph's "the Flare's bossMul"), full `dotnet test`, then "MERGE REQUEST: classes-12@<sha>" via the coordinator.
4. For the UI/codex lead: teach "in a boss fight your Flare fills from the boss, not the crowd" and the skill cards' boss line.
5. Phase 7 (CLASSES §7 table): the sweep (types ×1.35, on-calling ×1.25, full board ×1.25, Flare timing), never-pressing per type (sunderer +7.6%, verge hunter +3.5%), the first-hour teaching. Waves 6b/6c wait for the owner's yes.

## Gotchas
- Harness runs: `S/h.sh BUILD VARIANT OUT args`; build with `dotnet build -c Release -o S/bN balance/Balance.csproj` from godot (don't rebuild a dir a running batch uses). Arena: 96 runs ~2-2.5 min at par 16; story 512 nights ~3 min. Keep one batch at a time; not alongside `dotnet test`.
- lamps.json is generated: edit tools/classes/lamps_quarters.py, run `python tools/classes/lamps_build.py`, commit both.
- an.py's "beaten" counts runs where the Flare barely touched the boss (ratios in the thousands): read the median ratio, not the max.
