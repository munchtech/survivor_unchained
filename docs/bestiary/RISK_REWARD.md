# Risk and reward: cost, benefit and expected value

Counters cost something, specialising costs flexibility, and opt-in risk
must pay. This file puts numbers on each, from the code and from the
balance lab, and proposes how the oaths, Signs and endless play should pay.

## 1. What an arena pays today

From `Arena/Arena.cs` and `Play/Zones/ArenaRun.cs`:

| Reward | How much | Kept if the survivor falls before the boss? |
|---|---|---|
| Character experience for time | `minutes × 30 × (1 + 0.3 (tier − 1))` | yes |
| Experience for the win | `300 × tier` | no |
| Gear from elites | each elite killed: 30% × the oaths' gear multiplier, rarity rolled with that multiplier as luck, leaning to the map's answers | yes |
| Chests (champions, heralds) | ember upgrades for this run | (the run's) |
| The boss's spoils | `2 + tier / 2` items at least Uncommon (luck × 1.5), and a movement manual | no |
| A tome | 35% on a win (always for a story fight) | no |
| Gold | as picked up | yes |
| Skills discovered | every skill carried at the end | yes |
| After the win | experience keeps accruing; a herald with a chest every five minutes; falling costs nothing | yes, all |

Worked: a tier 2 arena won at the half hour pays 1,170 + 600 = **1,770**
experience; fallen at minute 25, **975** and no boss spoils. Ten minutes past
the half hour add 390 (+22%) and two heralds' chests, at no risk to the
win.

Two things follow:
- **The win is worth about a third of the experience and most of the gear.**
  Dying at minute 29 is a real loss, which is what makes oaths a risk.
- **After the win, risk is free.** Staying is pure upside, so the relaxed
  player loses nothing by leaving and the sweaty player gains by staying.
  That is right; keep it.

## 2. The cost of a counter

### 2.1 A slot spent

Gear damage is mostly *increased* (one additive pool per stat), but a
**slayer is its own multiplier**: `Stats.DamageMult` multiplies by
`1 + vs.<family>` after everything else. So a slayer never dilutes as the
ember's passives grow, while a general damage affix does.

| Affix in one slot (grade III) | Against its people | Elsewhere | At minute 30 with Might ×5 (+50% increased) |
|---|---|---|---|
| `grim` (+8–9% damage) | +8.5% | +8.5% | +5.7% (the pool is diluted) |
| a slayer (+32% vs a people) | **+32%** | 0 | **+32%** (its own multiplier) |
| `sturdy` (+3–4 armour) on a warden (5 armour) | damage taken ×0.88 | ×0.88 | ×0.88 |

So a slayer is worth about four `grim` affixes on its people's maps and
nothing on the others. Measured on Volley (`probe/RESULTS.md`), grade III
added 5–25% kills (fodder dies to the first hit either way; elites gained
the most).

### 2.2 Will the table offer your people?

The table offers three maps a day, each held by one of four peoples at
random (`MapOffers.Today`). The chance that at least one card is held by a
given people is `1 − (3/4)³ ≈ 58%`; for one of two peoples, `1 − (2/4)³ ≈ 88%`.

- A survivor geared for **one** people gets to use it a little over half the
  days. A slayer kit is a commitment to hunt that people, and the leaning
  loot (`Denizens.Lean`, four times as likely) pays it back in more of the
  same.
- A survivor with **two** slayer pieces for two peoples is covered most days
  at the cost of two slots.
- **Recommendation:** keep the offer random, but let the Wayfinder take a
  request ("I want the dead") for a fee or once a day, so a prepared player
  is never locked out of their preparation by the dice. Grim Dawn's infamy
  (`RESEARCH.md`) suggests a cheaper version: a people hunted often appears
  on the table more often.

### 2.3 Generalist and specialist

| Build | What it looks like | Against its matchup | Against its bad matchup | Who it suits |
|---|---|---|---|---|
| **Generalist** | Motes or Arcweb, armour, no slayer | 1.3–3.0× the median (`COUNTERS.md` §2) | never below 0.4× | the relaxed player, and the unknown table |
| **Specialist, by school** | holy for the Risen, fire for the Pack | holy vs the dead: ×1.5 from resistance alone, ×2 with Sanctify | shadow vs the dead −35% | the prepared player |
| **Specialist, by role** | area and chains for the Kerchiefs' wall | ●● against guards | ○ against nothing much | the player who reads the table |
| **Specialist, by gear** | two slayers and the people's resistance | +64% damage, −27% from them | 0 on other maps | the hunter of one people |

The healthy target: **the generalist wins, the specialist wins faster and
safer.** No people should be unwinnable for a generalist at a tier the
story expects, and no generalist should match a specialist on its matchup.
Today Motes and Arcweb come close to violating the second half (§2.3 of
`COUNTERS.md`).

### 2.4 The arts as a cost

The survivor carries **one** art. Choosing Shield Bash (interrupts, opens
guards) over Blink (escapes) is the sharpest counter choice in the game, and
it is made by day knowing the people. The probe's arts table (`COUNTERS.md`
§5) prices it: Mark Prey nearly doubles elite kills; Time Slip and Mirror
Step halve elite damage; Bulwark cuts the hurt from archers and raised ranks
by a fifth to a third. None is required (`DEPTH.md` §4), and Mirror Step is
too good at everything.

## 3. The oaths, measured

_(The balance lab's numbers follow.)_

## 4. A Weight for each oath

## 5. Champions and Signs

## 6. The half hour and beyond

## 7. Expected value, worked
