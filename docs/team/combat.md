# Combat: skills, enemies, encounters, bosses, balance

Status page for the combat lead.
- **Agent:** `a1d4562f44c7f6feb` (successor to `ac4ec5bbd2763a0df`).
- **Branch:** `worktree-agent-a1d4562f44c7f6feb`.
- **Read first:** `docs/handoff/combat.md` (the predecessor's knowledge), then `docs/SKILLS_DESIGN.md` §16–17.

## Current state (2026-10-04, paused for the owner's machine)

Tests green (585). Everything is pushed, and the integration branch is merged in. One piece of work is parked on the side branch `combat-wip-runups`; see Next, item 1.

**Done this session** (§16.1, §16.7, §16.9, §17.8 in SKILLS_DESIGN):
- **Boss floors hold for every ending.** The test drives an absurd build through the game's wiring: 60–77 s.
- **Oaths on bosses:** winter, embers, blight, ruin, vigil, iron, champions and swarm, each named on the boss's card.
- **The tier-3 brief:**
  - from tier 3, dusk is 5 minutes, the crowd eases at 2/5, its blows grow to ×2, and champions are ×1.25;
  - the oaths' bites (poison, cut mending, chill) come in over dusk.
  - Measured: planned 87% against careless 71% at 8 seeds, and 85% / 62% at 32 seeds. The experience director accepted it.
- **The Kindling at minute 15:** an ember-core plus the ruler's keeper (`lt_*`).
  - The core broken within its minute adds a card to the great blessing; the keeper carries a full chest.
  - Planned drafts break it 54% of the time, careless ones 30%.
  - The core is drawn by `EmberCoreView` and `shaders/ember_core.gdshader`.
- **Peoples evened out:**
  - footpads are 31 health and 9 damage a blow;
  - the Lamplings' champion is `lampling_ganger`;
  - the Pack-Mother, the Barrow Lord and the Red Hand are stronger (boss kills take 80–88 s);
  - five slow minibosses are softened.
- **The long night's square is 0.004:** the median run goes 26 min past the half hour.
- **Gold, for crafting:** arena fodder 0.0015, champions 0.07.
- **Marks:** `Sim/Marks.cs`, `CombatKit.Marks` and `CombatKit.SkillMods`, with crafting's first four Marks.
- **Maps, in the experience lead's shape:**
  - `MapRun`, `Charts`, the `Atlas` with its five biases, and the strongbox event through `G.Chest`;
  - played by day;
  - `--zone map [--tier --people --mods --at boss]`;
  - harness: `map --tiers 1,2,3 --people all`.
  - Measured: 9.8 / 10.3 / 11.9 min to clear, 100% / 96% / about 90% cleared, the ruler in 59–70 s.

## Next (in order)

1. **The run-ups (the experience director's brief, in `docs/handoff/experience.md`).**
   - The target, while `pacing.Building` (7.5–10, 17.5–20, 25–28.5): 10–20% of runs under half health in each run-up, 3–5% under a quarter, and wins within two points.
   - Measure it with `python <scratchpad>/combat2_stretch.py out/X.jsonl`, on a 192-night sweep (tiers 1–3, 8 seeds, table oaths, deft).
   - Today: 10% / 2% / 4% under half.
   - Branch `combat-wip-runups` (e63e74fd) has four levers: pincer spikes, signed champions ×2, ranged and aura kinds ×2, and forerunners (two signed half-heralds from either side).
   - The results so far: 9% / 2% / 8%, with wins falling 89% → 84%. Fodder melts at these minutes, so count does nothing.
   - The exact next step: try a forerunner pair *once* per run-up at herald strength (×(4 + tier)) instead of twice at half, and drop the champion-share lever. Re-measure. If wins hold within two points, merge it in.
2. **Done:** the crossbow's aim. `RangedSpec.Aim` is 0.55 s on the levy crossbows, the Scorpion and the Levy Sergeant. The shooter kneels (Casting, `CastKind.Aim`, Anim Windup with `AnimT = 0`) with its line fixed, so a step off the line is a dodge; the deft hands read it.
3. **The Kerchiefs at tier 3** stay the hardest people (68% / 50%). Under iron, blight and embers they win 18–41%. The Lamplings stay the easiest (87% / 81%).
4. **Then:** ground hazards hurting the horde at half, the Ford-Warden echo, weight as a number, and the Signs Warded, Mending and Leader.

## The three lengths, plainly

- **A story night (20 minutes): a timer, then a goal.** You survive the horde for 20 minutes. Then the story's foe comes, and the night ends when it falls (or you do). Nothing comes after it.
- **A table night (30 minutes): a timer, then a choice.** At 30:00 what rules that people comes, and beating it wins the night. The night does not end there: the way out opens, and you can stay in the endless long night, which only gets harder, until you fall or walk out.
- **An atlas map (about 10 minutes): a goal, with no timer.** You walk a winding way through placed packs and altars to the ruler at the end and kill it. The 10 minutes is how long that usually takes. The map ends when the ruler falls and you leave, or at your third fall.

## Key decisions

- **From tier 3 the night tests the draft;** below it, choice is expression. Stronger levers cost the planned draft too.
- **A night is lost to the draft, not to its first minutes.**
- **Maps use one ruler health (3.5× its body) on 0.65 floors.** Packs are thinned from MapGen's spots (0.8 in clearings, 0.62 on the ways). The last way before the ruler is empty.
- **Endings that are not deaths wait for the last floor** (`ArenaBoss.Spent`).

## Notes for other areas

- **Experience (successor of `ad1f5623590e09883`):**
  - the strongbox emits `ChestOpened` with `ChestItemKind.Gear`, ready for staging;
  - the ruler's fall emits `Ev.Victory`;
  - the API is `Atlas.Biases`, `Rank`, `Raise`, `Unspent`, `Road`, `Follow`.
- **Crafting (`a7debf1459f14dfe7`):**
  - the Marks API is above;
  - the moonpetal draught is agreed at 60%, drunk when 55% or more is missing;
  - a Kerchief map pays about 500 gold at the day's rate.
- **Skills VFX:** the ember-core could use sparks and heat haze; its view is `EmberCoreView` in `src/Actors/BossViews.cs`.
- **Story:** placeholders need your pass:
  - names and lines for the Kindling (`ember_core`, the `lt_*` keepers);
  - the `lampling_ganger`;
  - the forerunners' shouts (still on the WIP branch);
  - the chart mods' names.
