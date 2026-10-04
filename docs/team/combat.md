# Combat: skills, enemies, bosses, balance

Status page for the combat lead (agent `a09c5a65f5a84319e`, branch `worktree-agent-a09c5a65f5a84319e`).
The predecessor's full brief is `docs/handoff/combat.md`; read it first.

## Current state (2026-10-03, stopped at the owner's usage limit)

Tests green (461). Everything below is committed and pushed.

**Done this session**

- **The bosses never ran in the game.** `Game.HookBattle` copied the zone's hooks when a battle began, before the boss came, so no boss script ticked on screen (tests and harness share the zone's hooks, so they passed). Fixed with `BattleHooks.Following`; tests run a boss through the game's wiring.
- **A crash in the Pack-Mother's howl** (a channel broken from inside its own move): found by the sweep in 10 of 192 runs. Fixed and tested.
- **Move names and BREAK were invisible**: they shared the 48-slot damage-number pool and were overwritten within a frame. They have their own pool now (`Hits.Word`), held for the length of the mark, in the HUD's heavy face.
- **Bosses have their own bodies** (`boss_pack`, `boss_dead`, `boss_kerchiefs`, `boss_lamplings` in `Content/Enemies.cs`): the champion's body at about 1.4 times the size, and Named, so they glow. On screen the Red Hand was the size of a footpad before this.
- **Story constraints applied**: the table's Lamplings field **the Ganger** ("Foreman of the Deep Dig", a big sapper, one lamp carrying the three verbs, dies), never Grimtunnel or his name. Grimtunnel stays in the Dig Boils Over and still goes back down the hole. The Pack's script says "he" and "his" when it is Greymuzzle; the Pack's lines are narration, not speech (he is wordless).
- **The people make way** at the boss's arrival: the crowd beyond the 40% share falls back (fear) and is let go once it is out of sight, so the boss doesn't arrive inside a crowd (`ArenaRun.MakeWay`).
- **The bot reads the bosses** (`Play/Bosses/BossSense.cs`, shared by the harness's Pilot and the game's `--auto`):
  - it steps out of marked blows by shape, dashing when it is late;
  - it leaves ground that is about to close;
  - it stands over the Barrow Lord, chases the Red Hand's thief, and closes on Grimtunnel while a lamp flares;
  - a relaxed player misses 1 marked blow in 5, a practised player 1 in 20;
  - `--bossread 0` gives the old hands back.
- **Tools**:
  - `--on boss --until S` takes a frame of every boss move as it is marked, plus the Break, the arrival and each announcement;
  - `--give` now ranks up a weapon already in hand;
  - a skipped run-up (`--minute`) is now quiet;
  - the harness report has a "The bosses" table (blows landed and marked, Break, staggers, phase, grew wild).

**Before/after: the plain bot reading the bosses** (192 runs; all callings; greedy and random; tiers 1–3; level by tier; table oaths; cap 36. Taken before the bodies, the Ganger, making way and the 1-in-5 miss, so re-measure.)

| boss | won, old hands → reads | TTK s | blows landed / marked | grew wild (>3 min) |
|---|---|---|---|---|
| Barrow Lord | 21% → 90% | 135 → 78 | 178/1952 → 1/806 | 81% → 15% |
| Red Hand | 92% → 90% | 76 → 66 | 57/1234 → 1/1118 | 5% → 8% |
| Grimtunnel | 100% → 100% | 86 → 80 | 32/860 → 1/720 | 0% |
| Pack-Mother | 100% → 100% | 68 → 70 | 43/427 → 0/463 | 0% |

Overall win rate: greedy 70% → 92%, random 71% → 87%. Most Barrow Lord losses were the bot never laying him down.

## Next steps, in order

1. **Re-shoot all four bosses** with a late-game build (the `--give` fix makes one possible). For example: `python <scratchpad>/combat_shot.py rh kerchiefs --tier 2 --minute 29.95 --give "oathblade:8@oathkeeper,arcweb:8@tempest_coil,hoarfrost:8,seeking_motes:6,judgement_disc:6,+might:5,+haste:3,+ironhide:4" --auto --on boss --until 150 --seconds 5 --every 10 --count 14`. The scripts `combat_shot.py` and `combat_sheet.py` (a contact sheet) are in the coordinator's scratchpad.
   - Not yet seen on screen: a cone telegraph (is `ConeMark`'s rotation right?), the BREAK number, the stagger strip, the new word labels, the bigger bodies of the other three, the Ganger, Grimtunnel's lamps and pits, the cage posts and the thief, making way.
   - Every earlier frame showed the phases ending at their 60 s ceilings: an ember-4 build doesn't hurt a boss inside a full horde. Making way should help; check it does.
2. **Re-run the boss sweep** (`out/boss_plain_on`, then deft), then calibrate boss health per boss: 90–120 s at par. The Red Hand and the Pack-Mother are at 66–70 s now, so they probably need more health; the Barrow Lord at 78 s is fine.
3. Then the handoff's steps 4 onward: the full sweep and the lab's four tunings, the bestiary's bigger ideas, the rest of the bosses' build order, and the decisions recorded in SKILLS_DESIGN.md.
4. **Greymuzzle let go** (accepted narrowly; see the bible's "The nights"). Not built yet. The plan:
   - `ArenaSpec.Spare`, set in `Verge.MakeStoryFights` when `promise.pack` is set, `promise.broken` isn't, and `StreamClean()` holds;
   - the Pack script then holds him at 1 HP; he goes down, gets up and walks to the den; the arena is won;
   - `OnWin` sets `greymuzzle` = `spared` and raises Maeca's regard. The wording is for the story lead.

## Decisions

- **One sense for every bot.** The harness and the game's autopilot share `BossSense`, so pictures and numbers come from the same hands.
- **Bosses wear their own defs, not their champion's.** Size and glow make the boss the thing the eye finds. Health stays the champion's times `HealthMul`, so the numbers carry over.
- **The Ganger reuses Grimtunnel's script** (a mode, not a copy). The Dig's fight is the people's fight; what is Grimtunnel's alone (his three lamps, never dying, Snib) stays his.
- **Endless phase kept as built.** The Dawn at 60:00 waits for the owner (main session).

## Notes for other areas

- **Story**:
  - Greymuzzle's spared ending needs your words (`OnWin` history line, Maeca's regard) when it is built;
  - the Ganger's name and title are mine; change them if they jar.
- **UI**: the boss words use `Style.UiHeavy` in a pool of their own (`src/Fx/Hits.cs`).
- **Animation and art**: the bosses wear scaled-up champion bodies until they have their own.
