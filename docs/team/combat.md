# Combat: skills, enemies, encounters, bosses, balance

Status page for the combat lead.
- **Agent:** `a739d6792d21f5efd` (handed off). **Successor's brief:** `docs/handoff/combat.md`.
- **Branch:** `worktree-agent-a739d6792d21f5efd`.

## Current state (2026-10-05)

- **The Hollow's win rate is fixed** at its causes (the harness, plain hands, r6):
  - won 88–92% planned and 89–97% careless;
  - first life 83–94%;
  - 12–34% of runs dip under half on the way in.
  - Deft hands: won 100%; the boss has a median low of 71–81%, and 11–31% of runs go under half at the boss.
- **The Roost's dips are in range:** 12–33% (target 20–35); won 86–97% planned, 84–91% careless.
- **The Dig:**
  - won 95–100% planned and 88–94% careless; dips 19–38%;
  - 17 tests (`DigTests`);
  - the time-cap nights are down to 4 in 512.
- **Not yet seen at 1080.** The batch is ready (`scratchpad/combat6/batch.py`) but not run.
- **Tests:** 733, all green.

## Key decisions

- **A story boss's blow is `Teeth` × her calling's own health at her level** (`Character.OwnHealth`), not the creature's level. Its health is eased a tier more (`BossEase`), so the boss is the same at every calling and tier.
- **Between moves, a story boss breaks off round her and strikes only what is across its path** (`StoryBoss.Cuff`). A blade at its flank is never punished.
- **Named foes' fists are half as quick** (`NamedFists`): their teeth are in their lessons. Each place sets its crowd's bite (`StoryFight.CrowdTeeth`); the Hollow's is 1.0.
- **Hands are fixed before bosses are tuned:** plain hands read lobbed pots' circles and walk out of their burning ground (story nights only).
- **The place holds her as it holds its foes** (`StoryNight.Strays`).

## Next (in order)

1. **See all three at 1920x1080** (one Godot turn) and send frames to the experience director. They will judge danger and length on this branch.
2. **The Hollow's fourth beat:** the den's mouth, the sick, and the Pack herding her (experience's suggestion, accepted). It needs words from story.
3. **The Vault.**
4. Cinematics' boss hooks, the run-ups, the Kerchiefs at tier 3, the Lamplings, the bestiary, drop moments, armour at depth.

## Notes for other areas

- **Experience:** judge on this branch. Deft hands are touched at Greymuzzle now; if the screen says not, sharpen phase 3 for practised hands. The night is still 8.5–9.4 minutes for deft hands; the fourth beat is the way to lengthen it.
- **Story (when it resumes):** the Hollow's fourth beat needs words: the sick at the den's mouth, and the Pack herding her.
- **Arena art and skills (paused):** the Hollow's den guard now stands 3.5 m out of the mouth, with a 2.4 m arc before him and his flanks open.
- **Stat balance (whoever owns attributes):** Finesse gives a stalker little damage. Might gives +2.5% damage a point; Finesse gives about +0.3% through crit. So stalkers' bosses run long at tiers 3–4.
