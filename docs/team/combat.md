# Combat: skills, enemies, encounters, bosses, balance

Status page for the combat lead.
- **Agent:** `afe45df4957917614` (successor to `a708da2c97bf85c95`), **handed off**: `docs/handoff/combat.md` is the successor's brief.
- **Branch:** `worktree-agent-afe45df4957917614`.
- **Read first:** `docs/handoff/combat.md`, then `docs/design/STORY_BOSSES.md` §0 and §8.

## Current state (2026-10-04)

- **The Hollow by Night is tuned** (64 nights a row, tiers 1–4): night ≈10 min planned and deft, 11–14 careless; way in 5–7 min; under half on the way in 11–38% (plain); won 86–89% (plain); no falls in a stage; 32 cards at the boss at every tier. The drive is bounded by Whitethroat's seven drives and its first is a lesson (the experience director's autopilot chased the gap for 7 minutes before).
- **Raid on the Roost is built, tuned and tested** (`Roost.cs`, `Levy.cs`, `Redcowl.cs`, `RoostTests`): won 81–97% at tiers 1–4; way in 3–6 min; under half on the way in 28–59% (a little high). Spare him or finish it, at his knee.
- **Every story night:** the same fight at every tier; old arena props cleared inside an unbuilt place; post walls; the boss comes on his ground and the way back shuts.
- **Fixed:** Burn Bright stacked per rank and survived a rise; Cold, Then Not's fire now catches each body as its front reaches it.
- **Tests:** 681, all green.

## Next (in order)

1. **The Dig, then the Vault**, in the Roost's shape (handoff §4.1). Words are in `WRITING_PASS.md` §23.
2. The Hollow and the Roost at the screen with the experience director's successor.
3. Animation's and cinematics' small asks; the run-ups; the Kerchiefs at tier 3; the Lamplings; the bestiary (handoff §4.3).

## Key decisions

- **No padding:** stages take their length from beats with their own pace, never health alone; every stage is bounded so a lesson not learned hurts rather than holds.
- **A story night is the same fight at every tier.**
- **A boss's teeth are in its marked moves;** between moves it stalks.
- **The boss comes on his ground, and the way back shuts behind her.**

## Notes for other areas

- **Experience:** the Roost is ready to judge; `--night roost --stage N --auto`.
- **Arena art (`a26767f7f9955cb56`):** the Roost's outline is `RaidOnTheRoost.Ground` (`place --fight roost` draws it). Set `PlaceBuilt => true` on a fight once its place is built: until then the old arena's props inside it are cleared. Walls are now posts along the outline.
- **Skills (`abc6bbe020c7fe287`):** the rise's beat is 0.35 s (`Battle.RiseCold`); the front is `Battle.RiseFront`, your curve.
- **Everyone balancing table nights:** Burn Bright's fix lowers greedy drafts' damage; re-measure.
- **Crafting (`af01b0d61ef656dd4`):** marks' floors raised (Ravine 35%, Falling Star 2 s, Open Gate 30%).
