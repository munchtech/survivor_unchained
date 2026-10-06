W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/"
FILES = {
    W + "docs/SKILLS_DESIGN.md": [
        ("""Ganger 92 → 98 s. Health per boss: Pack-Mother `30 + 5t`, Barrow Lord
`13 + 2.2t`, Gutterwick and Grimtunnel `18 + 3t`, the Red Hand `21 + 3.5t`,
times its people's champion's.""",
         """Ganger 92 → 98 s. Once minibosses carried chests the build met the boss
stronger (78 / 81 / 104 / 79 s), so three were raised again by a fifth.
Health per boss: Pack-Mother `37 + 6.2t`, Barrow Lord `15.5 + 2.6t`, Gutterwick
and Grimtunnel `18 + 3t`, the Red Hand `26 + 4.3t`, times its body's.

**The floors hold for every ending.** A boss that ends otherwise than dying
(the Barrow Lord laid down, Grimtunnel down his hole, Greymuzzle let go)
began its ending as soon as it was held at one, skipping the last phase's
floor: a strong late build laid the Barrow Lord down in about 35 s. Every
ending now waits for the floor (`ArenaBoss.Spent`). A test drives an absurd
build through the game's own wiring against all six rulers: 60–77 s."""),
        ("""### 16.8 Decisions the studies left open""",
         """- **The oaths' bites come in at dusk too.** The tier's strength and an
  oath's levels came in over the first minutes, but an oath's rule (the
  blight's poison and its cut to mending, the winter's crawl) bit from the
  first blow. At tier 3 the blight alone felled 6 of 32 runs in minutes 1–5,
  before a draft had made anything to answer it with; with its bite coming
  in over dusk, 2.

### 16.9 From the third tier, the night asks the draft

The experience lead's brief: below the third tier choice is expression; from
it, a careless draft should lose noticeably more often than a planned one
(about 60% won against 85%). Measured first, a random drafter won as often
as a greedy one at tiers 1–3 (85% against 83%), and the third tier's losses
were walls in its first five minutes, which no draft decides.

From the third tier (`ArenaRun.Asks`):
- **A longer dusk:** the tier's strength comes in over five minutes, not
  three. The night is lost to the draft, not to its first minutes.
- **The crowd softens less** with the minutes (its easing at two fifths of
  the slope): it tests the build's reach.
- **Its blows grow** from the eighth minute to twice by the half hour: a build
  that cannot clear is touched more.
- **Champions, heralds and minibosses come a quarter stronger** from the
  sixth minute (not the boss: its contract sets its health): they test what
  the build does to one.

| Deft hands, table oaths, 8 seeds a tier | Before (16 seeds, tier 3) | After |
|---|---|---|
| Won, tier 3 (greedy / random) | 93% / 87% (with the longer dusk alone) | 87% / 71% |
| Fell, tier 3 (greedy / random) | — | 9% / 19% |
| Won, tiers 1 and 2 (greedy / random) | — | 96% / 84%, 93% / 84% (no change: the levers start at tier 3) |
| Tier 4 at its own level (greedy / random) | 62% / 53% | 62% / 56%, fewer falls in its first five minutes |

Stronger levers (champions half again as strong, the crowd's easing at a
third) widened the gap no further and cost the planned draft too (71% /
56%). With the bot's noise, a careless draft falling twice as often is the
signal; the rest of a random draft's losses are bosses it cannot finish.

### 16.8 Decisions the studies left open"""),
        ("""Nothing here is built yet. This section is the design to build from.""",
         """Built (§17.8): the map's runtime, charts and their mods, packs by tier,
magic and rare packs, altar keepers, the ruler at map strength, loot, falls
and the atlas's record. The atlas's biases and chart crafting wait for the
experience and crafting leads."""),
        ("""---

## 18. Before and after""",
         """### 17.8 What was built, and measured

- **`MapRun`** (`Play/Zones/MapRun.cs`) on MapGen's winding way: packs are set
  down out of sight as the survivor nears them, rest until she is within 14 m
  (the day's Wake and Leash), and charge in waves of two. Three in four of the
  clearings' pack spots are used and one in three of the way's (a pack at
  every spot was one long fight: a pack every 8 s, a map of 14 minutes).
- **Charts** (`Maps/Charts.cs`): tier, people, seed, rarity and mods, carried
  as a `wayfinder_chart` item with its map. Prefixes are the table's oaths
  (the vigil has no turns to double here; the moonless is a suffix) and the
  map's own: Signed, Twin guardians, Contested (from tier 8), Restless,
  Hardened. Suffixes: of Thin Blood, of the Brittle, of Lead, of No Rest, of
  the Moonless, of Sour Draughts (`MapRules`). Each pays quantity, rarity and
  pack size.
- **Kinds open by tier:** the first two stretches' at tier 1, the next every
  two tiers, all by tier 9; Signs and altar keepers the same.
- **The ruler** runs its night script on floors of 0.65 (10, 13 and 10 s),
  with its body's health three and a half times over at the map's level and
  its blows as its people's champion's. The night's per-ruler multipliers
  were set against the ember's builds and their Breaks: a day build met the
  four unevenly (the Pack-Mother 173 s, the Barrow Lord 67 s). What it calls
  is softened as the half hour's horde is.
- **Loot:** gear from magic (one) and rare (two) packs and keepers (two, a
  chance of fine); the ruler drops three to five, its people's material, and
  one to three charts, the first clear of a (people, tier) always giving the
  next tier's. Gold at the day's rates.
- **Falls:** three a map; each spills half of what was picked up there and
  wakes her at the last altar she lit.
- **The atlas** (`Maps.Atlas`): a cleared (people, tier) is marked; the first
  clear of each gives a point.
- **The harness:** `map --tiers 1,2,3 --people all` plays maps with a day
  build (the calling's own path's skills at the day's rank, plain gear of a
  rarity), walking a navigation field down the way to the ruler.

| A day build at the map's level (level 10, 12, 14), gear rarity 2, 96 maps | Tier 1 | Tier 2 | Tier 3 |
|---|---|---|---|
| Cleared | 93% | 90% | 84% |
| Closed (three falls) | 3% | 6% | 12% |
| Minutes to clear (median) | 11.7 | 11.6 | 13.2 |
| The ruler's time to kill | 60 s | 65 s | 65 s |
| A pack every | 14 s | 13 s | 15 s |

Open: the maps run at the top of the experience lead's 8–12 minutes, and a
pack comes about every 14 s against their 20–40; the Pack-Mother's map
still closes one map in six; the Kerchiefs' maps pay about 700 gold at the
day's rate (crafting's to weigh); creature levels run to 40 at tier 16 while
the survivor stops at 30, so gear must carry the high tiers once item levels
exist.

---

## 18. Before and after"""),
    ],
}
