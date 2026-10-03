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

The balance lab (`claude/cloud-balance-lab`, its bots run on this branch's
code) played every oath alone at tier 2: four callings, four peoples, two
seeds, the deft bot, 384 runs, cut at minute 31. The cut matters: the boss
comes at 30 and takes the bot 30–45 s, so **"won" here means "killed the
boss within its first minute"**, a proxy for how strong the survivor came to
the half hour. The full tables are in `probe/lab/`.

| Oath | Asks | Gives (today) | Won by 31 | Fell before 30 | Lowest health before the win | Ember level at the end | Reads as |
|---|---|---|---|---|---|---|---|
| none | – | – | 66% | 3% | 38% | 54.5 | the baseline |
| **Blight** | poison on hit, mending −33% | ember ×1.4 | 50% | **9%** | **24%** | 53.8 | **the most dangerous** |
| **Iron** | non-crits −33% | gear ×1.5 | **38%** | 6% | 37% | 52.7 | the slowest boss kill (43 s) |
| Deep Dark | +2 levels | gear ×1.4, ember ×1.2 | 53% | 6% | 35% | 54.8 | harder |
| Winter | blows chill | gear ×1.5 | 56% | 6% | 34% | 53.7 | harder |
| Embers | dead leave fire (30%) | gear ×1.4 | 62% | 3% | 36% | 55.2 | slightly harder |
| Ruin | dead burst (22%) | ember ×1.5 | 62% | 6% | 40% | 54.1 | slightly harder |
| Swarm | packs ×1.5 | ember ×1.5 | 62% | 3% | **48%** | 57.1 | easier in the run, the ember pays it |
| Moonless | light ×0.5 | elites ×1.3, gear ×1.3 | 66% | 0% | 43% | 54.8 | no harder for a bot (a bot does not need light) |
| Vigil | events twice as often | gear ×1.3 | 66% | 3% | 42% | 54.5 | no harder |
| **Hunt** | foes ×1.2 speed | ember ×1.25, gear ×1.2 | **72%** | 0% | 43% | 57.0 | **easier**: faster foes, faster ember |
| **Champions** | elites ×2 | gear ×1.6 | **75%** | 0% | 43% | 56.1 | **easier**: more chests, a stronger build |

Thirty-two runs a row: a difference of ten points in "won" is within
chance; the rows that stand out (blight, iron, hunt, champions) stand out by
twenty or more, or in two columns at once.

**What it says.**

1. **The oaths that make the horde bigger or faster pay for themselves.**
   The hunt, the swarm and champions all bring more kills or more chests,
   and the ember and the chests make the survivor stronger faster than the
   horde gets harder. In a fight measured in isolation (the probe), the hunt
   more than doubles the damage a warden takes from wolves; over a whole
   run it is one of the easiest oaths. *A risk that feeds the build is a
   blessing in disguise.* That is fine for swarm (its answer, area, is what
   the survivor's build is for) but means **champions is over-paid**: it is
   easier *and* gives the most gear.
2. **The oaths that take away the survivor's tools cost the most.** Blight
   (healing cut and a poison that ticks) leaves the survivor lowest before
   the boss; iron (a third of every non-critical blow gone) makes the boss
   fight longest. Both are Death Must Die's and Risk of Rain's lesson: taking
   away a crutch hits some builds far harder than others (`RESEARCH.md`,
   lesson 21).
3. **The blight is under-paid.** It is the most dangerous and pays only
   ember ×1.4, which is spent inside the run; its gear multiplier is 1.

The probe and the lab disagree about the hunt, and both are right about what
they measure. The lab's answer is the one the reward should follow, and the
probe's is the one the *table's words* should follow: "They are a fifth
faster" understates how it feels in the moment.

## 4. A Weight for each oath

Hades prices each condition by how much harder it *plays*, not by its
number (`RESEARCH.md`, Hades). A Weight does the same here: an integer per
oath, summed on the table, and the reward follows the Weight rather than the
oath's own multipliers.

| Oath | Weight (proposed) | Why | Gear today | Gear at `1 + 0.2 × Weight` | Change |
|---|---|---|---|---|---|
| Blight | 3 | lowest health, most falls | 1.0 | 1.6 | **raise** (and keep ember ×1.4) |
| Iron | 3 | fewest wins | 1.5 | 1.6 | about right |
| Deep Dark | 2 | harder in every column | 1.4 | 1.4 | right |
| Winter | 2 | harder | 1.5 | 1.4 | about right |
| Embers | 1 | slightly harder | 1.4 | 1.2 | lower, or raise its fire chance to 50% and keep 1.4 (`COUNTERS.md` §8) |
| Ruin | 1 | slightly harder | (ember ×1.5) | 1.2 | add a little gear |
| Moonless | 1 for a bot, more for a person | the bot needs no light; a person does | 1.3 | 1.2 | keep, pending a human test |
| Vigil | 1 | no harder | 1.3 | 1.2 | about right |
| Swarm | 1 | easier in the run | (ember ×1.5) | 1.2 | keep: it is the area player's farm |
| Hunt | 1 | easier in the run | 1.2 | 1.2 | right, but say how it feels |
| Champions | 1 | easier, more chests | 1.6 | 1.2 | **lower** to 1.3, or give it Signs (§5) so its champions are harder, and keep 1.6 |

The table today offers 0–3 oaths by tier (`MapOffers.Today`); the Weight is
their sum. Two rules from the research:

- **Pay for new Weight** (Hades re-pays its rare currencies only for heat not
  yet beaten). The first win of a people at a tier and Weight beyond the
  survivor's best gives a **Wayfinder's mark**: a step on the Named-item
  tally of `docs/items/ACQUISITION.md` §7.1, or a guaranteed Marked item.
  Repeating a beaten Weight pays the ordinary multipliers only.
- **Show the reward table** (Diablo III's Torment): the card shows "Weight 4
  · Gear ×1.8 · Ember ×1.4" and, on hover, where it comes from.

Each oath also keeps the **loot identity** the item plan gives it
(`docs/items/ACQUISITION.md` §3: Marked chance for champions, ilvl for the
deep dark, frost Marks for winter...): the Weight sets *how much*, the
identity *what*.

## 5. Champions and Signs

A champion today costs a long fight and pays a chest (an escorted champion,
a herald) or a 30% gear chance and a 40% draught (any champion). Signs
(`COUNTERS.md` §4) make it harder; they must pay.

| | Cost to the survivor | Reward (proposed) |
|---|---|---|
| A plain champion | ×3 health, a level up | as today |
| One Sign | the Sign's verb; ~ +30% time to kill for the builds it hampers | gear chance 30% → 45%; its chest gets one more card (`OpenChest` count +1) |
| Two Signs | both, and their pairing | gear chance 60%, rarity luck ×1.3, chest +1 |
| A herald | ×(4 + tier) health, one Sign more than a champion | as today, plus the Sign's rewards |

The probe's numbers give the scale: a champion bruiser takes 6.5 s with
Arcweb and 56 s with Volley (`COUNTERS.md` §2), so the same Sign is a small
cost to one build and a large one to another. That is the point: the player
whose build answers the Sign is paid the same for less risk, and that is
the reward for preparing.

**Expected value of chasing a champion.** At tier 2 the bot meets about one
escorted champion every four to six minutes and two heralds; a chest is
1–3 ember upgrades (`ArenaRun.OnPickup`). A single upgrade early in a run
moves the build by roughly the same as one level of ember, so a champion
killed at minute 8 is worth more than the same champion at minute 28.
Signs should therefore start late (from minute 10 at tier 1, `HORDES.md`
§5), when the build can afford them and the chest is worth less.

## 6. The half hour and beyond

After the win, risk is free (§1): the arena is won whatever happens. The
balance lab's winners all stood at its cut. The reward past the half hour
should therefore be **glory and history**, not power the next arena needs:

- **Deeds** for Storied items (`docs/items/SYSTEM.md` §9): "slain an arena's
  boss beyond the half hour" is already one; add "a herald slain past the
  fortieth minute" and "an arena of the same people held for an hour".
- **A best time per people and tier** on the Wayfinder's table, and the
  arena's longest night (`arena.longest` already exists).
- **The bestiary** counts (and the knowledge it unlocks, `DEPTH.md` §5.3)
  climb fastest here.
- Experience keeps accruing at the tier's rate, and heralds' chests keep
  coming; nothing more is needed.

## 7. Expected value, worked

A survivor at the table, tier 2, deciding between an unsworn map and the
same map under one oath. Experience from the arena (`XpFor`), gear from the
boss (`2 + tier / 2` = 3 items) and from elites, with the lab's win rates.
Losses happen at the half hour (the lab's falls before 30 are 0–9%), so a
lost run earns its 30 minutes of experience (1,170) and no boss spoils.

| Map | P(win) | Experience, expected | Boss items, expected | Elite gear multiplier | Verdict |
|---|---|---|---|---|---|
| unsworn | 0.66 | 0.66 × 1,770 + 0.34 × 1,170 = **1,566** | 0.66 × 3 = **2.0** | ×1.0 | the baseline |
| blight, today | 0.50 | **1,470** (−6%) | **1.5** (−25%) | ×1.0 | **a bad bet**: less of everything, for ember spent in the run |
| blight, Weight 3 | 0.50 | 1,470 | 1.5, at ×1.6 rarity luck | ×1.6 | a fair bet for a player who can heal round it |
| iron, today | 0.38 | 1,398 (−11%) | 1.1 (−42%) | ×1.5 | a bet only for a crit build (its answer) |
| champions, today | 0.75 | 1,620 (+3%) | 2.3 (+14%) | ×1.6, and more elites | **a free lunch**: take it every time |
| hunt, today | 0.72 | 1,602 (+2%) | 2.2 (+9%) | ×1.2 | slightly better than unsworn |

The rule the table should meet: **an oath's expected reward for a player
whose build answers it should beat unsworn, and for a player whose build
does not, it should fall short.** Today champions beats unsworn for
everyone and blight falls short for everyone; both break the rule. Iron
meets it (a crit build's P(win) should be near the unsworn one; the bot's
builds are not crit builds).

These are small samples and one bot; the balance lab should re-run the
oaths with more seeds, both bots, tiers 1–3 and a cut at minute 35 (so the
boss fight finishes) before any multiplier is set from this table.
