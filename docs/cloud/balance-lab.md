# Balance lab

The arena and day-story bots, swept across the game's space on every core,
and what the numbers say. The harness is `godot/tests/BalanceLab.cs`, now
built on the balance tool in `godot/balance` (`docs/SKILLS_DESIGN.md`
section 15). Each sweep's raw rows (`arena_runs.csv`) and summary
(`summary.md`) are kept under `docs/cloud/balance-lab/<sweep>/`. The
per-card CSVs ran to a megabyte a sweep, so they are left out; the card
tables in each `summary.md` come from them.

## Running it

Opt in with `BALANCE_LAB`; plain `dotnet test` skips the sweep and stays fast.

```
cd godot/tests
BALANCE_LAB=arena LAB_SEEDS=6 dotnet test --filter BalanceLab --logger "console;verbosity=detailed"
BALANCE_LAB=story LAB_SEEDS=3 dotnet test --filter BalanceLab
```

- **Output:** `godot/.lab/<LAB_LABEL>/`, which git ignores, holds
  `arena_runs.csv` (one row per run), `arena_cards.csv` (one row per card
  taken) and `summary.md`; a story sweep writes `story_runs.csv`.
- **Progress:** `<name>_progress.txt` grows as runs finish, so a long sweep
  can be watched.
- **The knobs** are listed at the top of `BalanceLab.cs`. The ones that
  matter most:
  - `LAB_BOT=plain|deft`: the bot's skill (below);
  - `LAB_TIERS`, `LAB_PEOPLES`, `LAB_CALLINGS`, `LAB_OATHS` (`all` gives no
    oath and then each oath alone), `LAB_SEEDS`;
  - `LAB_MINUTES`: where a run is cut;
  - `LAB_LEVEL`: the survivor's level, by default 1, 4 and 7 for tiers 1–3;
  - `LAB_THREADS`: how many runs at once.
- **Speed and determinism:** a 45-minute arena takes about a minute on one
  core, so a full 288-run sweep takes about 65 minutes on four. Runs are
  deterministic: four threads and one give identical CSVs.
- **Two sweeps side by side:** `python3 tools/balance/compare.py BEFORE AFTER`
  prints win rates by tier, calling, people, and people and tier.

### The two bots

- **Plain** is the original arena bot. It goes to the fight, gives ground
  when pressed, gathers ember, dashes out of a crush, uses its art on a
  crowd, drinks when low, and takes the first card it is offered.
- **Deft** does all of that. It also:
  - steps off the line of a telegraphed lunge, and dashes across it if the
    lunge is about to land;
  - leaves the landing circle of a lobbed pot and gets off burning ground;
  - closes on throwers when nothing presses it and there is no ember to
    gather.

  It is meant to stand for a player who has learned the fight, so a death
  the deft bot still suffers is more likely the game's fault than the bot's.

## Targets

- **Tier 1:** a first clear that is likely but not certain for every
  calling, about 80–90% for the deft bot.
- **Each tier harder:** tier 2 about 70–80%, tier 3 about 60–70%, at the
  levels a player brings to them (1, 4 and 7).
- **Callings comparable:** within about 10 points of each other at each tier.
- **Peoples comparable:** no people a wall or a walkover; within about 15
  points at each tier.
- **Threat that builds:** pressure through the half hour, not long safe
  stretches broken by sudden kills.
- **The boss:** a fight of about one to two minutes, neither a formality nor
  a wall.

## What the first sweeps found (before main's own balance pass)

These four sweeps were run on this branch before main moved: plain and deft
baselines, then tuning rounds one and two. Each has 288 runs (4 callings × 3
tiers × 4 peoples × 6 seeds, cut at 45 minutes). What they showed still
explains several of main's later changes.

- **Tier barely bit.** The deft bot won 89% at tier 1, 89% at tier 2 and
  82% at tier 3. Creature levels climbed two a tier, while the ember the
  harder creatures give paid most of it back. Main has since made a tier
  three levels; on this branch the same change took the deft bot to 94%,
  76% and 67%.
- **The threat came in spikes.** At every minute mark the bot's mean health
  was about 97%. Nearly every death came from full health inside one
  minute:
  - the herald at minute 20, against the Dead especially;
  - the boss at minute 30.

  The ordinary horde barely threatens a survivor who keeps moving. This is
  the largest open question; see "Still open".
- **The Dead were a wall and the Lamplings a walkover.**
  - Plain bot: the Dead were won 54–71% across tiers, the Lamplings 88–100%.
  - Risen bowmen did 56% of all the damage the Dead dealt. A grave-caller's
    slowing frost orb held the survivor in a barrow knight's lunge, and that
    knight was the top killer.
  - Kerchief and Lampling damage was mostly firepots, at 58–61%.
- **Glass Cannon looked bad for the plain bot only.** Its runs won 54%
  against about 85% for the other great blessings. With the deft bot they
  won 92%. It rewards a player who dodges, which is its purpose, so it was
  left alone.
- **Draft weapons.** Iron Palms and Spirit Herd were the weakest picks in
  both bots: the runs that took them early won 75–78%, against 82–91% for
  the runs that did not. Rimeshard and Judgement Disc were the strongest
  (89–96%). Main's weapon rework has since replaced all of these numbers,
  so the findings are kept only as history.
- **The endless.** Fifteen minutes past the win, about two winners in three
  were still standing. Those who fell lasted a median 8–11 minutes past it.
  The endless climbs, but slowly.

## Current main (10cd381): the baseline

This verification sweep is smaller so that it ran in about half an hour: 96
runs per bot (2 seeds per cell), cut at 32 minutes. A run counts as **won**
only if the boss died by minute 32, which is two minutes after it comes.
Each cell holds 8 runs, so a difference of one run is 12 points.

| | plain | deft |
|---|---|---|
| all | 85% | 88% |
| tier 1 | 97% | 94% |
| tier 2 | 78% | 84% |
| tier 3 | 84% | 84% |
| arcanist | 92% | 92% |
| reaver | 83% | 75% |
| stalker | 83% | 96% |
| warden | 88% | 88% |
| the Dead | 58% | 54% |
| the Kerchiefs | 92% | 96% |
| the Lamplings | 100% | 100% |
| the Pack | 96% | 100% |

Two things in this table need reading with care:

- **The Dead's losses are mostly not deaths.**
  - Of the Dead's ten or eleven losses for each bot, the survivor was alive
    at the cut in ten. The deft bot died once and the plain bot never died.
  - The Barrow Lord simply takes longer to kill: a median 65–86 s against
    27–56 s for the other three bosses. The cause is undead resisting frost
    (25%) and shadow (35%).
  - The Dead are therefore a slow boss, not a wall. With the old 45-minute
    cut, most of these runs would have won.
- **Tiers 2 and 3 come out alike here.** Main's ramp over the first three
  minutes and its weapon rework apply to all tiers. With 32 runs per tier
  this sweep cannot tell 78% from 84%; it needs the full sweep.

## The tunings on this branch

Main already has the change I made first (a tier is three creature levels),
and its weapon rework replaced my Iron Palms and Spirit Herd buffs, so I
dropped all three. I measured six tunings on top of main (the "tuned"
sweeps), then kept four of them. All are in `godot/logic/Content/Enemies.cs`
and `godot/logic/Maps/MapOffers.cs`.

| change | why | kept? |
|---|---|---|
| Lampling 16 → 20 health, 7 → 8 damage | The Lamplings were never beaten at any tier, by either bot, before and after main's pass. | kept |
| Lampling sappers weight 2.5 → 3.5, from minute 5 → 4 | Sappers are the Lamplings' only threat, through their pots and death blasts. More of them, sooner. | kept |
| Risen bowman cooldown 2.8 → 3.3 s, damage 7 → 6 | Bowmen did more than half of all damage from the Dead, so the Dead were hardest by a long way. | kept |
| Kerchief pillager cooldown 4.2 → 4.8 s | The Kerchiefs were a wall at tiers 2–3 after tiers were made to bite on this branch. | **reverted**: on main the Kerchiefs win 92–96% |
| Stalker 140 → 155 health | The stalker trailed the other callings by about 15 points. | **reverted**: on main the stalker is level with them or ahead |

Before and after on main, at 96 runs per bot. The tuned sweep still
included the two changes that were later reverted, which explains the
Kerchief and stalker columns.

| | plain, main | plain, tuned | deft, main | deft, tuned |
|---|---|---|---|---|
| all | 85% | 85% | 88% | 90% |
| the Dead | 58% | 62% | 54% | 62% |
| the Lamplings | 100% | 96% | 100% | 100% |
| the Kerchiefs | 92% | 92% | 96% | 96% |
| the Pack | 96% | 92% | 100% | 100% |
| tier 1 | 97% | 97% | 94% | 94% |
| tier 2 | 78% | 84% | 84% | 84% |
| tier 3 | 84% | 75% | 84% | 91% |

These changes are deliberately small. They move the Dead a few points
toward the other peoples, and that is within this sweep's noise. The
lampling change has not yet made the Lamplings a fight: the deft bot still
won all 24 of their runs. The honest summary is that these tunings point
the right way but are not proven. A full sweep (6 seeds, 45 minutes, both
bots) is the check, at about 2 × 65 minutes.

## Where the bots distort the picture

- **Card choice.** Both bots take the first card offered. The draft puts a
  combat skill first whenever it has one, so the bots fill six weapons and
  take passives only once the weapons are full (a median minute of about
  24). As a result:
  - the card tables say little about passives;
  - "taken early" means weapons, and evolutions are rare (5–46 times in
    288 runs).

  Main's harness now has drafting policies (`LAB_POLICY=greedy|path:ID`),
  which are the way to test this.
- **Dodging.** The plain bot never dodges a telegraph, so it overstates
  deaths to lunges from barrow knights, enforcers and the Pack-Mother. The
  deft bot is closer to a player but is no expert: it never takes a perfect
  dodge on purpose and never aims its art.
- **Melee.** The deft bot gives ground to dodge, which costs melee builds
  damage against the boss. This shows as longer boss kills for oathblade
  runs.
- **No gear and no growth.** Every run starts from a fresh character at a
  fixed level, with no gear and no learned traits. That understates tier 3
  for a real player who arrives dressed for it.
- **The cut.** With a short cut, a slow boss reads as a loss. The Dead above
  are the example.

## Still open (recommendations not applied)

1. **The Barrow Lord's length.** It lasts one and a half to three times as
   long as the other bosses. Either cut its health multiplier for the Dead
   (to about 0.75 of the others) or soften undead frost and shadow resist
   on the boss alone. A player should feel which works; the numbers only
   show the gap.
2. **Spikes rather than pressure.** The horde barely threatens a moving
   survivor, and deaths come in one-minute bursts at the herald (minute 20)
   and the boss (minute 30). One option is to raise ordinary creatures'
   damage over the half hour and soften the herald. That changes the
   game's feel, so it needs a human at the controls before it goes in.
3. **The Pack and the Lamplings are still easy.** Both are won 96–100% at
   every tier. One more step each is likely needed: wolf damage, or Lampling
   numbers at tier 3. Measure it with the full sweep.
4. **The endless.** It ramps slowly; a run that wins tends to survive a long
   while. Whether that is a reward or a lull is a design call. If it is a
   lull, steepen the past-the-half-hour health growth from `0.1·m` toward
   `0.15·m`.
5. **The day-story walk** across callings, levels 1–5 and days 1–4 is built
   into the harness (`BALANCE_LAB=story`). Its sweep was stopped when main
   moved and has not been re-run, so this report has no day-story numbers.
   It is the next run to make, before and after the lampling and bowman
   changes, since both creatures also appear by day in the Verge.
6. **Glass Cannon** is a trap for a careless player and good for a careful
   one, which is as designed. Its card text could say so, perhaps by naming
   the perfect dodge.
