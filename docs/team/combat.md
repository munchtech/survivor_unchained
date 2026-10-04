# Combat: skills, enemies, bosses, balance

Status page for the combat lead. Last session: agent `a09c5a65f5a84319e`, branch `worktree-agent-a09c5a65f5a84319e`, handed off at about 560k context. The successor reads `docs/handoff/combat.md` first. The design and its reasoning are in `docs/SKILLS_DESIGN.md` section 16 (enemies, bosses, the long night, decisions).

## Current state (2026-10-04)

Tests green (475). Everything below is committed and pushed.

- **Bosses run in the game.** They didn't before: the game copied the zone's hooks before the boss came. All four were checked on screen frame by frame (`--on boss`), and all telegraph kinds with `--marks`.
- **Fixed on screen:**
  - **bands:** now an annulus with a clear inside;
  - **stagger bar:** it was clipped and never seen;
  - **move names:** said over the boss, and no longer overwritten by damage numbers;
  - **the BREAK:** stands alone;
  - **boss bodies:** their own, about 1.4 times the champion's, named, with a softer hit flash;
  - **the people make way** at the arrival.
- **Bugs fixed:**
  - the howl crash;
  - a phase turn said "Interrupted!" and could finish an old move;
  - a stagger could be wasted while the boss was untouchable;
  - a holy blow broke the Barrow Lord's laying down;
  - oaths that promised more ember never paid it;
  - the harness read Break against a pooled body.
- **Story:**
  - the table's Lamplings field **the Ganger**, never Grimtunnel;
  - Grimtunnel goes back down the hole;
  - Greymuzzle says "he", is wordless, and is **let go** when the bible's conditions hold.
- **The bots read the bosses** (`Play/Bosses/BossSense.cs`), shared with the game's `--auto`.
- **The long night** (the owner: endless is truly endless):
  - the horde hardens smoothly, then compounds from an hour past the half hour;
  - the dark swears an oath every 5 minutes;
  - the boss returns every 15 minutes;
  - heralds come between the returns.

## Numbers (before → after)

| Measure | Before | After |
|---|---|---|
| Boss fight, deft, tiers 1–3 (Pack / Barrow / Ganger / Red Hand) | 69 / 80 / 92 / 72 s | 84 / 86 / 98 / 84 s |
| Barrow Lord won, plain hands | 21% | 90% |
| Boss blows landed / marked | 310 / 4473 | 3 / 3107 |
| Long night, deft, tier 2: minutes past 30:00, median (p10–p90), furthest | 21 (9–40), 62 | 21 (11–38), 53 |

After the boss row was measured, the Pack and the Red Hand got about a further tenth of health (now `30 + 5t` and `21 + 3.5t`). Not yet re-measured.

## Key decisions (why in SKILLS_DESIGN §16)

- **Bosses are gates, not health bars:** floors, the Break and enrages. Health is tuned so a par build takes 90–120 s.
- **One shared boss sense:** every bot, and the autopilot used for pictures, reads boss telegraphs the same way. Sweeps then measure the game, not the bot.
- **The long night's variety comes from the table's own oaths, never the moonless:**
  - the oaths about where to stand come first, the ones that grind come last;
  - the returning boss grows by a rule a player can learn;
  - compounding waits an hour past the half hour.
- **The way out stays** after the win: a player may bank and leave. The ramp has no ceiling.

## Next (in order, for the successor)

1. **The owner's encounter notes** (the brief is in the handoff):
   - a **charge director** (cap, budget, waves, spikes, lulls);
   - an **escalation schedule** that unlocks mechanics by clock and by miniboss or minion arrival;
   - **minion, elite and miniboss variety** per people, on existing rigs, with model briefs.
2. **The long night's tail:** the deft bot's best is +53. Try a 0.004 quadratic health term so great builds reach +60–75. Measure.
3. **The full sweep:** 6 seeds, 45 minutes, both bots, drafting policies. Use it to decide the balance lab's four tunings, and re-measure the Pack and the Red Hand.
4. Then the handoff's remaining items: Signs, the bestiary's new creatures, oaths on bosses, the Kindling, and the Ford-Warden echo.

## Notes for other areas

- **Experience director (a33f58e68e89e3ccf):** you own breathers and set pieces, in a new `Play/Zones/ArenaPacing.cs` that ArenaRun asks for its target, breathers and next event. Combat owns what spawns and what it does.
- **UI design:** an edge marker (skull) sits over the boss bar's title when an elite is off the top of the screen. The boss words use `Style.UiHeavy` in their own pool (`src/Fx/Hits.cs`). The stagger groove sits under the boss bar at y 76.
- **Animation and art:** bosses wear scaled champion bodies until they have their own. Variety needs a per-def tint or gear hook in `CrowdView` (Actors, yours). The model briefs will be in SKILLS_DESIGN.
- **Story:** Greymuzzle spared needs your words (the history line, Maeca's regard, C10's variant). The Ganger's name is mine; change it if it jars.
- **Performance:** the long night caps the horde at 380, ranged enemies at 24, and telegraphs at their own caps.
- **Crafting:** new creature types will want drops. Ask the successor.
