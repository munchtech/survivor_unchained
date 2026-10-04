# Combat: skills, enemies, encounters, bosses, balance

Status page for the combat lead.
- **Agent:** `ac4ec5bbd2763a0df`.
- **Branch:** `worktree-agent-ac4ec5bbd2763a0df`.
- **Read first:** `docs/handoff/combat.md` (the predecessor's knowledge), then `docs/SKILLS_DESIGN.md` §16–17.

## Current state (2026-10-04, stopped at the owner's usage limit)

Tests green (530). Everything is committed and pushed. Merged with the integration branch at `81429e6`.

**The owner's three encounter notes are built:**
1. **The charge director** (§16.4): waves, lulls, spikes on the people's tell, and calm in breathers, the hush and duels. Charges a minute went from 123–184 to 42–59; the most at once from 15–22 to 5–7.
2. **Stretches** (§16.5): five per people, at 3, 7, 12, 16 and 22 minutes.
   - Each opens with a named miniboss wearing one verb. Its kinds join only after it comes, and its champion Signs open.
   - Two minibosses return in the long push.
   - In the long night, heralds and pairs of minibosses take turns.
   - New verbs: auras, calls, slams, chained charges, runs that end in a blast, chilling or poisoning bites, fanned lobs.
3. **Variety** (§16.5): 13 new kinds and 20 minibosses on existing rigs, told apart by scale, tint and behaviour. Nine champion Signs. A model brief for each in §16.5.
   - The story lead's names are applied, including Gutterwick for the table's Lamplings.

**Other changes:**
- **Story nights are 20 minutes** on one night clock (§16.6): ember and experience are paced to match, and they end on their boss with no long night. Every night speaks in one voice ("The dead of night").
- **Crafting's economy fixes:** arena fodder pays 2% gold; gear comes only from carriers.
- **A fix:** bad ground no longer buys the survivor a moment of grace each tick (§16.7).
- **Maps, the permanent ARPG arenas:** the mechanics are designed in §17, not built. The experience lead owns their shape and loop.

**Measured** (deft bot, tiers 1–3, greedy and random, table oaths, 96 runs each). The "after" row is before the last tuning: minibosses now carry a one-card chest, the Scorpion and the Decurion are softer, so it needs re-measuring.

| | Before (`81429e6`) | After (`71608a4`) |
|---|---|---|
| Won (greedy / random) | 98% / 92% | 88% / 94% |
| Won (tiers 1 / 2 / 3) | 97% / 94% / 94% | 94% / 94% / 84% |
| Boss TTK (Pack / Barrow / Gutterwick / Red Hand) | 99 / 90 / 97 / 77 s | 76 / 78 / 101 / 64 s |
| Herald TTK (greedy / random) | 19 / 25 s | 20 / 37 s (Signs) |
| Damage a minute at 25 (greedy) | 247k | 276k (miniboss chests: since cut to one card) |
| Miniboss TTK, median | – | 9–52 s (The Scorpion 52, the Decurion 49, both since softened) |

## Next (in order)

1. **Re-measure** with the one-card chests: `arena --callings all --policies greedy,random --seeds 4 --tiers 1,2,3 --level tier --oaths table --cap 34 --bot deft`. Compare with the "before" numbers above.
   - **Bosses fell faster after the change;** that should come back with the smaller chests. The Pack-Mother's and Red Hand's re-measure is this sweep. If TTK still runs under 90 s, raise HealthMul.
   - The baseline harness is rebuilt from `git archive 81429e6` into the scratchpad, as described in the handoff.
2. **The experience lead's briefs:**
   - From tier 3, a careless draft should lose more often than a planned one (about 60% won against 85%). Use a 6-seed sweep with greedy and random, both bots, to separate the signal from noise.
   - Check the boss floor with a late `--give` build: 35 s was seen.
3. **The full sweep, and the long night's tail** (0.004 quadratic).
4. **Build maps** (§17.7, with the experience and crafting leads).
5. **Then:** oaths on bosses, the Kindling, the Ford-Warden echo, weight as a number, and the remaining Signs (Warded, Mending, Leader).

## Key decisions

- **A verb is shown before it spreads:** one big body first, then the crowd. A held-back miniboss's kinds join after 2½ minutes.
- **Signed champions are cloned defs with their kind's id:** no special cases in the AI, the view or the bestiary.
- **The balance probe's yardstick stays the day's rank and file** (`Denizens.Horde`), so new kinds don't move every path's number.
- **Verb timers draw dice only when a creature has the verb,** and the charge director has its own stream. This keeps the fight's dice where they were.

## Notes for other areas

- **Animation (a1e3002b800ee55ac):** the motion list has been sent: a quadruped howl; kneel-to-shoot; a slam; a horn, drum or rally gesture; the shamble. Crossbow and pike gear variants are wanted.
- **Skills look and feel (a8bafe3cd8a229639):**
  - auras, calls and slams carry `Ev.Telegraph.Faction` for the people's colour;
  - the dead's spike tell is now `tell_horn`, not `tell_drum`.
- **Story (a035208561a66c171):** the renames are applied. "The dead of night" wording is used for every night.
- **Crafting (a7862117a0240deb5):** the miniboss ids have been sent, `Loot = "miniboss"`. Maps want chart items (§17.2).
- **Experience (a33f58e68e89e3ccf):**
  - story nights are built as agreed;
  - the maps' mechanics are in §17, with proposed changes to your brief in §17.7;
  - minibosses respect your Hush and the herald's duel.
- **Performance:** auras use one spatial query per pulse; enemy ground is capped at 24.
