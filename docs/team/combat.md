# Combat: skills, enemies, encounters, bosses, balance

Status page for the combat lead.
- **Agent:** `a5115633c7006e4d4`, successor to `afe45df4957917614`. **Handed off:** `docs/handoff/combat.md` is the successor's brief.
- **Branch:** `worktree-agent-a5115633c7006e4d4`.
- **Read first:** `docs/handoff/combat.md`, then `docs/design/STORY_BOSSES.md` §0.

## Current state (2026-10-05)

- **The Hollow and the Roost were seen at 1920x1080.**
  - Greymuzzle's moves read, but his ring didn't read as a wall: it is now thirty strong with a pale line where a step further is a shove.
  - The drive's first lesson is now said before its lane is marked.
  - The Roost reads as a crowd in the dark until arena art builds it.
- **The harness was mended.** These were flattering the old numbers:
  - the boss's first life is now a first meeting;
  - the hands read the crowd's marked circles;
  - a steering bug pinned them at the den's middle;
  - one lunge was missed the same way in every run;
  - named foes and bosses could leave the place.
- **The Dig Boils Over is built** (`Dig.cs`, `GrimtunnelStory.cs`) with the story's words, and is half tuned.
- **Tests:** 681, all green.

**Measured** (r4, 64 nights a row, plain hands):

| Fight | Won (greedy / random) | Boss first life | Under half on the way in | Way in | Boss (greedy) |
|---|---|---|---|---|---|
| Hollow | 73–80% / 69–80% | 59–75% (target 55–70) | 11–28% (20–35) | 4.6–5.8 min | 2.8–3.6 min |
| Roost | 89–92% / 81–91% | 67–84% | **38–56% (20–35)** | 3.3–5.5 min | 2.5–3.5 min |
| Dig (dig10, 32 a row) | 81–91% / 50–88% | 44–88% | **31–56%** | 3.8–4.5 min | 3.0–5.6 min; 16/256 still run to the cap |

- **The Hollow's won is below 90%:** the rise saves a third of those who fall at Greymuzzle.
- **The Roost's dips are too many,** mostly at the levy and the Pike-Captain.

## Next (in order)

1. **The Hollow's won ≥90%.** Consider scaling story bosses' blows to her health band.
2. **The Roost's way-in dips.**
3. **Finish the Dig:** the cap runs, dips, tests, and seeing it at the screen.
4. **The Vault.**
5. **Cinematics' boss hooks** (marks, and the spared part at the choice).
6. The run-ups, the Kerchiefs at tier 3, the Lamplings, the bestiary.

## Key decisions

- **A boss's first life is measured as a first meeting;** after a fall, the hands know it.
- **Hands are fixed before bosses are tuned to them.**
- **The night holds its named foes and boss inside the place, past the shut gate.**
- **Dashes carry over gaps** (cracks, sinkholes), and knockback stops at walls.
- **No padding:** stages are bounded by beats (cadences, a roof held for ten tubs, waves from the steps), never by health alone.
- **A story night is the same fight at every tier.**

## Notes for other areas

- **Experience:**
  - the Dig is ready to look at: `--night dig`;
  - `--stage N` now hands her the floors' build;
  - the ring line and thirty wolves are ready to judge.
- **Arena art:** the Dig's outline is `DigBoilsOver.Ground` (`place --fight dig`). The crack runs from (10.2,-20) to (16.8,-34), and Snib's heap is at (23,-36), outside.
- **Skills:**
  - `RiseCold` is 0.25 (your call);
  - looks are wanted for Grimtunnel's mound (`GrimtunnelStory.Under`), the tubs (`TubWay.Tub`), the barrel (an `IZoneLook.Piece`), and gaps (`Collider.Gap`).
- **Animation:**
  - slam and shot plants are in (`Ai.SlamPlant` 0.65, `ShotPlant` 0.7);
  - `levy_crossbow` and `mb_levy_sergeant` now use `kerchief_crossbow`.
- **Story:** your four lines are in.
