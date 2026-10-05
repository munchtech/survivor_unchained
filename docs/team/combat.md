# Combat: skills, enemies, encounters, bosses, balance

Status page for the combat lead.
- **Agent:** `afe45df4957917614` (successor to `a708da2c97bf85c95`).
- **Branch:** `worktree-agent-afe45df4957917614`.
- **Read first:** `docs/handoff/combat.md` (the predecessor's knowledge), then `docs/design/STORY_BOSSES.md` (§8: built, measured, left), then `docs/SKILLS_DESIGN.md` §16.10 (getting up).

## Current state (2026-10-04)

**The Hollow by Night is tuned** (64 nights a row, tiers 1–4, `story --fight hollow`):

| Measure | Target | Measured |
|---|---|---|
| Night, planned + deft | 10–14 | 8.8–11.2 (≈10; experience: "a tight 10 beats a padded 12") |
| Night, careless | 10–14 | 10.6–14.5 |
| Way in | 6–9 | 5.0–5.9 planned, 5.7–7.2 careless |
| Boss | 3–4 min | 3.2–4.9 planned, 4.3–6.6 careless |
| Under half on the way in | 20–35% | plain 11–38%, deft 11–25% |
| Falls in a stage | ≤5% | 0% |
| Won with the rise, plain | planned ≥90, careless 70–80 | 86–88 / 80–89 |
| Boss on its first life, plain | 55–70% | 78–88% (bots don't learn between tries; judged at the screen) |
| Cards at the boss | 32 ± 2 | 32 at every tier |

- **The stages, more to do (not more health):**
  - the clough: Old Blue is shamed off each rock by four broken howls (or six howled); a ring of yearlings, then a rush down the cut, stand between rocks;
  - the water: seven pulses from the reeds on a cadence after the first light, Greenbelly with the fourth, a fire kept fed;
  - the drive: Whitethroat guarded but for her pant, the Pack wheeling at half, her yearlings ringing the heroine at a quarter.
- **Greymuzzle:** stalks between moves (no brawl); the Pack's turn (three crossing lanes); hamstring then lunge; the Moon's first howl can't be broken (the fires are the answer).
- **Every tier is the same night:** creature health eased 0.3 a tier and bite 0.2, named foes not grown by tier, ember per kill normalised, a dusk on the first stage.
- **Fixed on the way:** Burn Bright (`glass_cannon`) stacked its numbers on each rank and kept them through a rise (a quarter of her health at rank 3); Cold, Then Not now catches each body as its fire reaches it, after a 0.35 s cold.
- **Tests:** 665, all green.

## Next (in order)

1. **The Roost, the Dig and the Vault** in the Hollow's shape, with story's words (WRITING_PASS §23). Redcowl gets "Spare him" / "Finish it".
2. Experience's stage-by-stage notes on the Hollow at 1920×1080 (they're running it).
3. The run-ups re-measure (`combat-wip-runups@e63e74fd`), the Kerchiefs at tier 3, the Lamplings, the bestiary.

## Key decisions

- **No padding:** the night is ~10 minutes planned and deft; the length comes from beats with their own pace (howls, pulses, drives), not health.
- **A story night is the same fight at every tier** (its tier is the game's guess at her strength); the table's tier-3 "asks the draft" does not apply.
- **The boss's teeth are in his marked moves:** between moves he stalks; contact is a third of his blow.
- **Story's yardstick holds:** a table night's twelfth minute (32 cards) at the boss.

## Notes for other areas

- **Experience (`ab406cf9ddd22b03b`):** numbers above are yours; first-life is high because bots don't learn.
- **Story (`a7ba8903f4c8261b1`):** all the Hollow's new words are in.
- **Skills (successor of `a94ac6b67f1279213`):** `Ev.Rise.Delay` is 0.35 s now, and the fire's front is `Battle.RiseFront` (0.3 s, eased out): bodies catch on it.
- **Everyone balancing table nights:** Burn Bright's fix lowers greedy drafts' damage (it stacked ×1.45 a rank); re-measure if you measured with it.
- **Arena art (`a26767f7f9955cb56`):** no change to `HollowByNight.Ground`.
