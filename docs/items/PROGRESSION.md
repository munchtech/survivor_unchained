# Progression: the curves from level 1 to the cap

How gear grows from the Low Ford road to the bottom of the stair: the level
bands, the power each tier of gear should supply, how much an affix is worth at
each grade, how often an upgrade should come, how gear and the ember stay in
balance, and what keeps the top worth chasing.

All numbers are proposals for the balance lab, worked against the code as it
stands: `Character.XpForLevel` (120 × L^1.55), `Enemies.ScaleFor` (health
1 + 0.38l + 0.035l², damage 1 + 0.14l, where l = level − 1),
`StatBlock.ArmorReduction` (armour / (armour + 20)), weapon rank growth (+20%
damage a rank), `SkillBook.Rank` (1 + (L − 1) / 3, to 8) and
`ArenaRun.Level` (tier × 2 − 1 + oath levels + minute / 2.5).

---

## 1. The bands

There is no level cap in the code today. Proposal: **30**, reached near the end
of Act 3, with the endgame beyond it in item level and arena depth, not in
character level (a cap keeps attribute points and skill ranks finite and makes
gear the open-ended axis).

| Band | Story | Days | Char level | Arena tiers | Item level | Bases | Affix grades | Rarities that matter |
|---|---|---|---|---|---|---|---|---|
| **Road** | Prologue, Act 1 | 0–7 | 1–10 | 1–3 | 1–12 | Worn, Sound | I–III | Plain, Fine, first Rares; 4–6 Named from the story |
| **North** | Act 2 | 8–20 | 10–20 | 3–6 | 10–22 | Sound, Wrought | III–V | Rare; Marked appears (ilvl 12+); sets begin |
| **Stair** | Act 3 | 21–end | 20–30 | 6–9 | 20–32 | Wrought, Legion, Heartwrought (Act 3 opens it) | V–VI | Marked, Named, set pieces |
| **Depths** | After the ending | – | 30 | 10–12, then Depth 1+ | 32–40 | Heartwrought | VI, bright (34+) | Named, Storied, bright rolls |

Arena tier to item level: **ilvl = 3 × tier + 2** (tier 1: 5, tier 6: 20,
tier 12: 38); heralds +1, the boss +2, capped at 40. A Depth is ilvl 40.
By day, ilvl is the creature's level.

**Item level outruns character level on purpose** in the arenas: the night is
where the better gear is. A survivor who pushes a tier above their level gets
gear above it too. Base affinity (`SYSTEM.md` §5.3) keeps it honest: a Legion
plate asks 14 Might.

## 2. The power budget

### 2.1 What has to be kept pace with

| Creature level | Health × | Damage × |
|---|---|---|
| 1 | 1.0 | 1.0 |
| 10 | 7.3 | 2.3 |
| 20 | 21.8 | 3.7 |
| 30 | 41.4 | 5.1 |
| 40 | 69.0 | 6.5 |

Health grows with the square of level, damage linearly. Every source of the
survivor's power is additive or linear except the weapon's Edge and the few
named multipliers, so the budget below is built to reach about two thirds of
the creature health curve by day at level 30 (fights get a little longer as
the game goes on, which is right for a story where the dark gets worse), and
the ember covers the rest by night.

**Balance-lab flag.** Even with the Edge, day fights at level 30 take roughly
1.5 times as long as at level 1 with on-tier gear, and 4 to 5 times as long
without upgrades. If the lab wants day fights flat, flatten the quadratic term
(0.035 → 0.022 makes level 30 ×30 instead of ×41) rather than inflate gear.

### 2.2 The survivor's offence by day, on-tier gear

A worked example: a reaver at each band's top, wearing gear at the band's
typical rarity, carrying Butcher's Cleaver.

| | L1, start | L10 (Road) | L20 (North) | L30 (Stair) | L30, best (Depths) |
|---|---|---|---|---|---|
| Skill rank (by day) | 1 (×1.0) | 4 (×1.6) | 7 (×2.2) | 8 (×2.4) | 8 (×2.4) |
| Might (inc 2.5% a point) | 7 (+18%) | 12 (+30%) | 18 (+45%) | 24 (+60%) | 26 (+65%) |
| Gear "increased" damage, all slots | 0 | +35% | +80% | +130% | +170% |
| Increased, total | ×1.18 | ×1.65 | ×2.25 | ×2.90 | ×3.35 |
| Weapon Edge (more) | ×1.0 | ×1.25 | ×1.6 | ×2.1 | ×2.8 |
| Crit (chance × extra) | ×1.03 | ×1.08 | ×1.15 | ×1.25 | ×1.35 |
| Marks, Named, sets (more) | – | – | ×1.15 | ×1.3 | ×1.5 |
| **Offence ×** | **1.2** | **3.6** | **10.8** | **30.8** | **50.3** |
| Creature health at that level | 1 | 7.3 | 21.8 | 41.4 | 69 (ilvl 40 depths) |
| Time to kill, relative | 1.0 | 2.4 | 2.4 | 1.6 | 1.6 |

So gear supplies, by the cap, about **×4.5 of the ×25** the survivor gains by
day (the rest is skill rank and attributes), and at the top end a further ×1.6
from best-in-slot. That ratio is the budget: **gear should never be more than
half the survivor's day power growth**, so levels and attributes keep their
meaning.

### 2.3 Defence by day

| | L1 | L10 | L20 | L30 | L30 best |
|---|---|---|---|---|---|
| Health (base + attributes + gear) | 205 | 360 | 560 | 790 | 900 |
| Armour (base + Resolve + gear) | 8 (29%) | 16 (44%) | 28 (58%) | 42 (68%) | 55 (73%) |
| Resistance, the map's school | 0 | 20% | 35% | 50% | 65% |
| **Effective health ×** (vs physical) | 1.0 | 2.2 | 4.6 | 8.6 | 11.6 |
| Creature damage × | 1.0 | 2.3 | 3.7 | 5.1 | 6.5 |

Defence grows a little faster than creature damage: right for a game where the
danger is the crowd's numbers, not one blow. The resistance cap stays at 80%
(`Battle.HitPlayer` clamps it); gear alone should reach 65% in one school at
most, so oaths that hit a school stay felt.

### 2.4 Budget by tier, in "slots of value"

The simplest way to tune: each slot's item, at a tier, is worth a number of
**points**, and every affix, implicit and power has a point cost. One point
is roughly 2% of the survivor's day power at that band.

| Rarity | Implicit | Affixes | Power | Points (at the band's top) |
|---|---|---|---|---|
| Plain | 3 | – | – | 3 |
| Fine | 3 | 1–2 × 3 | – | 6–9 |
| Rare | 3 | 3–4 × 3 | – | 12–15 |
| Marked | 3 | 3 × 3 | Mark 5 | 17 |
| Named | 3 (base) | fixed, worth ~10 | power 6–8 | 19–21 |
| Named in a set | 3 | fixed ~8 | its share of the set's bonuses ~6–10 at 4 pieces | 17–21 |
| Storied | as Named, lifted a grade | | | 23–26 |

A slot's points at a band scale with the grades available: an affix at grade I
is 1.0, at VI 4.5 (`SYSTEM.md` §6.2). So the budget per item roughly
multiplies by the band: Road ×1.5, North ×2.5, Stair ×4, Depths ×4.5 to ×5.

## 3. Affix value scaling

Every affix's value at grade *g* is **base × m(g)**, with
m = 1.0, 1.5, 2.1, 2.8, 3.6, 4.5 (and bright up to 5.6). The base is set so that
grade VI on its best slot is worth **about 4 to 5 points**. A few anchors:

| Affix (best slot) | Grade I | Grade III | Grade VI | Bright | Point check at VI |
|---|---|---|---|---|---|
| +flat health | 12–14 | 25–29 | 54–62 | up to 75 | ~8% of a L30 pool |
| +armour (body) | 1–2 | 3–4 | 7–8 | 10 | ~4% damage taken at 40 armour |
| +% school damage | 6–7% | 13–15% | 27–31% | 38% | inc: ~8% of L30 inc total |
| +% damage (all) | 4% | 8–9% | 17–19% | 23% | |
| +crit chance | 1.5% | 3% | 6.5–7% | 8.5% | |
| +% crit damage | 10% | 21% | 45% | 56% | |
| +% weapon speed | 2.5% | 5% | 11% | 14% | more (cooldown) on gear today: change to inc, `CATALOGUE.md` §3 |
| +% area | 4% | 8% | 18% | 22% | |
| +% move speed | 2% | 4% | 9% | 11% | |
| +attribute | +1 | +2 | +4 | +5 | |
| +% resistance | 6% | 12–13% | 26–28% | 34% | |

The existing affixes (`Items.Affixes`) map onto grades I–IV today
(tier 0–3); most of their values sit near this curve already. `CATALOGUE.md` §3
lists every affix.

## 4. Upgrade cadence

How often should the survivor change a piece of gear?

| Band | A visible upgrade (any slot) | A new Rare-or-better worn | A new power (Mark, Named, set bonus) | Play time per arena |
|---|---|---|---|---|
| Road | every arena, and every second day-zone visit | every 2 arenas | the story's Named gifts (4–6 across Act 1) | 15–30 min (many fall before the half hour) |
| North | every 1–2 arenas | every 2–3 arenas | every 3–4 arenas (Marked from ilvl 12) | 30–40 min |
| Stair | every 2–3 arenas | every 3–4 arenas | every 3 arenas | 30–45 min |
| Depths | every 4–6 arenas | every 6–10 arenas | a new Named every ~3 hours; a Storied lift every few sessions; a bright roll is news | 30–60 min |

These come out of the drop tables in `ACQUISITION.md` §2. Two checks the lab can
run by simulation: (a) median arenas to the first Marked item after ilvl 12: ~3;
(b) median hours to own 50% of the Named catalogue at the cap: ~25.

**The smoothing rule.** If the survivor has gone four arenas in a band without
an upgrade to any slot (judged by the compare score), the next boss drop is
rolled twice and the better kept. Invisible, but it never lets a dry spell run
long. (Visible pity is for Named items, `ACQUISITION.md` §7.)

## 5. Gear and the ember: keeping the two halves in balance

This is the part of the plan the balance lab should read twice.

### 5.1 Two dials

- **Gear sets the floor and the lean.** It decides how strong the survivor is
  at minute zero, what they draft toward, and how fast they get going.
- **The ember sets the ceiling.** It decides how strong they are at minute
  thirty and beyond.

Targets, at a tier the survivor is "on" (gear of that tier's band):

| | Minute 0 | Minute 15 | Minute 30 (boss) | Beyond, minute 45 |
|---|---|---|---|---|
| Survivor power, on-tier gear (× a gearless survivor at minute 0) | ×3.0 | ×10 | ×22 | ×30 |
| The same survivor with no gear at all | ×1.0 | ×6 | ×14 | ×20 |
| **Gear's share** (on-tier ÷ gearless) | **×3.0** | **×1.7** | **×1.6** | **×1.5** |
| With best-in-slot (Depths) gear | ×4.5 | ×2.2 | ×2.0 | ×1.9 |

Gear matters most at the start of the night and settles to a steady ×1.5–2 by
the half hour. It is never zero and never the whole.

### 5.2 Why this holds without special cases

1. **Gear damage is *increased*.** The ember's passives (Might, Precision...)
   add into the same increased sum. As they grow through the run, gear's +130%
   is a smaller part of a larger sum. No arena-only dampener is needed.
2. **Gear skills stop at rank 4.** The gear weapon starts ahead and the ember
   catches the others up; ranks 5 to 8 and evolutions are earned.
3. **Edge only multiplies its kind.** A Steel weapon's Edge helps the Steel cards
   the survivor drafts and nothing else; drafting off-kind is a choice with a
   cost.
4. **Kindled affixes are capped** per effect and per kit (`SYSTEM.md` §6.4).
5. **Gear never grants blessings, evolutions or ember past its caps.**

### 5.3 What the lab should measure

- Time to win a tier-T arena at the half hour, with on-tier gear and the
  autopilot draft (`--auto`), across the four callings: the target is that the
  boss falls between minute 30 and 33 on the tier the survivor's band ends on,
  and the survivor dies before 30 one tier higher about half the time.
- The share of total damage dealt by gear-brought skills at minutes 5, 15 and
  30: targets 70%, 35%, 20%.
- Minute at which the first evolution happens with and without a catalyst
  suffix: the catalyst should bring it 1 to 3 minutes earlier, not more.

### 5.4 The prologue night

The Low Ford night has ember with starting gear only. It must stay winnable
with nothing but a Worn weapon. No item in this plan touches the prologue.

## 6. What keeps the top fresh

At the cap, character level stops; gear and depth do not.

1. **The Depths.** After the ending, the Wayfinder's table goes down: Depth 1, 2,
   3... Each Depth is ilvl 40 and stacks one more oath, from a pool that grows
   to include Act 3's people (the Legion's dead, the Vigil, the Morrow's own
   things). Gear's value in a Depth is measured by *how deep*, not by ilvl,
   which is capped: the chase becomes bright rolls, Storied lifts, and the right
   Named items, not bigger numbers.
2. **Echoes.** Named foes of the story come back as **echoes** at the table
   (the Ford-Warden, Greymuzzle, Redcowl, Grimtunnel, the Barrow Lord, Sallow's
   champion), each with its own Named drops at a raised rate: the game's
   pinnacle bosses and its surest target farm (`ACQUISITION.md` §4).
3. **Vonnra's fortune.** Every seventh day she reads the survivor's fortune at
   the Toll Tower (she already does at Act 1's end): a foretold item that is five
   times as likely for the next seven days, and a foretold oath that pays double.
   A rotation that gives every week a target, in her voice (`ACQUISITION.md` §5).
4. **The binders' book.** Collecting every Mark at its best strength; the
   book's pages are Vonnra's family's, and filling them is a long, quiet goal.
5. **Storied items.** History accrues only by doing things worth writing down;
   lifting a Named item to Storied is a project per item.
6. **Watchwords.** Recipes found in the world, one at a time; some only in the
   Depths.
7. **Bright rolls.** A Named item with every range bright is the known jackpot.
8. **Looks.** Heartwrought and set appearances unlocked for the tailor are a
   collection of their own (`VISUALS.md` §7).

What is **not** proposed: an unlimited paragon-like level (a slow, invisible
power climb that buries gear, `RESEARCH.md` §2), seasons (a single-player story
game), or a stat squish budget (the Inc-not-More rule is meant to make one
unnecessary).
