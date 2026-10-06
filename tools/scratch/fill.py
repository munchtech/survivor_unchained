import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c')
p = 'docs/SKILLS_DESIGN.md'
s = open(p, encoding='utf-8').read()

pace = """Measured at tier 1 (median of 144 runs):

| Minute | 1 | 2 | 3 | 5 | 10 | 15 | 20 | 25 | 30 |
|---|---|---|---|---|---|---|---|---|---|
| Ember level | 6 | 9 | 11 | 15 | 24 | 31 | 38 | 45 | 50 |
| Drafts that minute | 7 | 3 | 3 | 2 | 2 | 2 | 2 | 2 | 2 |

Cards a minute over a whole night: 1.95. `Harness/Targets.EmberByMinute`
holds this pace, so a probe at an ember level meets the horde of the minute
it is usually reached."""

targets = """| Measure | Target | Measured |
|---|---|---|
| Win at the survivor's tier (planning drafts: greedy, first) | tier 1 ≥ 95%, tiers 2–3 ≥ 85% | tier 1: 96%, 96%; tier 2: 96%, 94%; tier 3: 92%, 88% |
| Win drafting at random | below planning drafts, so the draft matters | tier 1 98%, tier 2 85%, tier 3 90%; the boss takes half as long again or longer (49 / 77 / 81 s against 35 / 36 / 48 s) |
| A tier above the survivor's level (level 10: tier 3 is the band's top) | each tier above a real step; three above mostly lost | tier 3: 92% won; tier 4: 79% (16% fell before the boss); tier 5: 80% (18%); tier 6: 49% (41%) |
| Every path at tier 2, its own bot | ≥ 80% | 82% (the Host) to 100% (the Hunt, the Long Winter, the Storm, the Weave) |
| Boss fight, median | 30–90 s (R§9) | tier 1: 42 s, tier 2: 57 s, tier 3: 57 s; by path at tier 2: 20 s (the Hunt, the Weave) to 78 s (Dawn) |
| Herald fight, median | under the boss's | 26 / 44 / 58 s |
| Ordinary creature's time to kill, minutes 5 / 15 / 25 (tier 2) | falls through the night | 0.45 / 0.23 / 0.13 s (it rose, 0.43 / 0.69 / 0.95 s, before) |
| Champion's time to kill, minute 15 | seconds | 1.2 to 2.0 s |
| First evolution, median | earned: about ten minutes when planned | greedy 7–10 min, first 10–15, random 17–20 |
| Evolutions a night | three or four when planned | 3.6–4.2 planned, 1.8–2.0 at random |
| Build complete (six skills evolved) | the last third | 22–28 min |
| Cards a minute | 0.5–3 (R§9) | 7 in the first, then 2–3, 1.95 over the night |
| Largest share of a build's damage by one skill (mean where carried) | no skill carries the game | 21% (Judgement Disc; 39% before) |
| Largest share by one rule (probes) | ≤ 45% | 31% (Shatter, after its chain was paced) |
| Path probes at the fifteenth minute's ember (`BalanceTests`) | crowd 0.7–1.35 of the median, champion ≥ 0.25, toughness ≥ 0.55, power index ≤ 1.9 | crowd 1106–1823 (0.75–1.23), champion 177–1045, toughness 184–430: within every bound |
| Great blessings, first choice (small samples) | none a trap | 78% (Hold the Crossing, 9 runs) to 100% won |"""

before_after = """"Before" is the game as this work found it, measured by the harness's first
bot (plain hands, level 1, no oaths); "after" is the finished design. The
last rows are the same measure, before and after.

| | Before | After |
|---|---|---|
| Tier 1 won (first / greedy / random), plain bot, level 1, no oaths | 94% / 88% / 91% | 100% / 96% / 98% (with the boss's longer fight) |
| Tier 2 won (greedy / random), plain bot, level 1, no oaths | 88% / 71% | 94% / 85% |
| Tier 2 at the story's level and the table's oaths, deft hands (greedy / random) | not measurable (no oaths, no levels, no deft hands in the harness) | 96% / 85% |
| A tier above the survivor's (level 10, tier 4) | 86% (one tier counted for two levels) | 79%, and 49% three tiers above |
| Paths at tier 2, their own bot | 58% (the Wild) to 100% | 82% to 100% |
| Path probes: crowd spread / champion spread | ×2.0 / ×6.9 (level 35) | ×1.65 / ×5.9 (the fifteenth minute's ember), every path inside the bounds |
| One skill's mean share of the builds that carry it | 39% (Judgement Disc) | 21% |
| Ember at minutes 1 / 15 / 30 | 7 / 37 / 53 | 6 / 31 / 50 |
| Ordinary creature's time to kill at minutes 5 / 15 / 25, tier 2 | 0.43 / 0.69 / 0.95 s (rising) | 0.45 / 0.23 / 0.13 s (falling) |
| Boss fight | not measured; bots killed it in 10–30 s once measured | 42–57 s by tier |
| Great blessings | 12, random hands | 20 in four roles, hands dealt by role, a calling's own once a night |
| Passives | 22 stat names | 25 things of the valley, most with a rule of their own |
| Day to night | the weapon only | banked skills, familiar skills, the calling's paths, kindled gear, the codex, the tome |
| Rare drought in the draft | up to twenty levels | at most ten |
| Tests | 309 | 419 |"""

open_items = """- **The middle of the night is safe.** Lowest health is about 90% from minute
  ten to the boss; the threat is champions, heralds and the boss. The feel
  study's floods and breathers (S-12) would put pressure back mid-run, and
  its boss ceremony (S-11) would make the boss the peak; both are arena
  pacing beyond the spawner that keeps up, and are not built.
- **The boss-killers kill the boss fast.** The Hunt and the Weave fell the
  tier-2 boss in about 20 s, under research's 30 s. That is their identity;
  if the boss is to be the peak for them too, give it a phase (S-11), not
  more health (which would drag Dawn and the Wild past 90 s).
- **Most falls at tier 3 come before minute fifteen**, even with Dusk. A
  softer first quarter hour at the higher tiers is the next lever if
  playtests agree.
- **The Edge is not built.** When it is, apply section 14's night cap and
  lean (`Battle.Night`).
- **Icons.** The new great blessings and the callings' own reuse existing
  glyphs (embers, static, thorn, howl, aegis, drain, arcane, mark); they
  should have their own in the UI art manifest.
- **Small samples.** The callings' own greats were first choices in 9 runs
  each; a dedicated sweep (each calling, many seeds) should confirm them.
  Cinderwake and Burn Bright have each sat lowest in one sweep or another:
  watch them.
- **The Grave's crowd** is the lowest in the probes (0.75 of the median),
  though it wins 92% of its arenas; a small lift to Umbral Bolt is the
  obvious one.
- **Probes and arenas measure crowds differently**: the probe's crowd is the
  level's full strength (a yardstick that does not saturate), the arena's is
  softened by the minute.
- **The day story's balance** (the balance lab's walk of the Verge) was not
  part of this work."""

for key, val in [('PACE_TABLE', pace), ('TARGETS_TABLE', targets), ('WIN_RANGE', '82% to 100%'),
                 ('BEFORE_AFTER', before_after), ('OPEN_ITEMS', open_items)]:
    assert s.count(key) == 1, key
    s = s.replace(key, val)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
