import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
def rep(old, new):
    global s
    assert old in s, old[:80]
    s = s.replace(old, new)

rep("""- **Epic is finer, not only fuller**: its grades roll from the top of its band twice and keep the
  better (section 4.3).
""", "")
rep("| **Sound** | 8–15 | ×1.6 | +10% |", "| **Sound** | 8–15 | ×1.8 | +10% |")
rep("| **Wrought** | 16–23 | ×2.4 | +25% |", "| **Wrought** | 16–23 | ×2.8 | +25% |")
rep("| **Legion** | 24–31 | ×3.4 | +45% |", "| **Legion** | 24–31 | ×4.0 | +45% |")
rep("| **Heartwrought** | 32+ | ×4.6 | +70% |", "| **Heartwrought** | 32+ | ×5.5 | +70% |")
rep("""Every base gets two implicits so a Common has something to scale (section 10.3). Measured with the
power score (4.4), the owner's claims hold, and a test holds them (`LootTests`):
- a **Sound Common** beats a **Worn Uncommon** of the same base;
- a **Wrought Common** beats a **Worn Rare**;
- a **Heartwrought Common** beats a **Worn Epic**.""",
"""Every armour base gets implicits worth about one and a half affixes, so a Common has something to
scale (section 10.3). Measured with the power score (4.4) over 200 rolls of each, the owner's claims
hold for every helm, body and cloak base, and a test holds them (`LootTests`):

| Iron Helm (power) | Common | Uncommon | Rare | Epic |
|---|---|---|---|---|
| Worn (level 1–3) | 2.7 | 4.7 | 8.5 | 14.6 |
| Sound (10) | 5.7 | | | |
| Wrought (18) | 9.4 | | 15.6 (level 20) | |
| Heartwrought (34) | 19.5 | | | 35.4 |

- a **Sound Common** beats a **Worn Uncommon** of the same base;
- a **Wrought Common** beats a **Worn Rare**;
- a **Heartwrought Common** beats a **Worn Epic**;
- and a deep Rare or Epic is still far better than a deep Common: rarity keeps its meaning.

Rings and amulets are where affixes live: their small implicits scale too, but a Common ring never
beats a good roll. A late Common ring is a base for the forge, as in Path of Exile.""")
rep("""A drop's grades come from its rarity, as today (Uncommon I–II, Rare II–III, Epic III–IV, the Epic
rolling twice and keeping the better), **raised one grade from level 25 and two from level 35**,""",
"""A drop's grades come from its rarity, as today (Uncommon I–II, Rare II–III, Epic III–IV; the finer
of the two oftener the deeper it was made, crafting's `FinerGrade`), **raised one grade from level 25
and two from level 35**,""")
rep("`Loot.Power(item)` sums", "`Drops.Power(item)` sums")
rep("`Loot.Roll` (logic, `Rpg/Loot.cs`), for each gear roll:", "`Drops.Roll` (logic, `Rpg/Loot.cs`), for each gear roll:")
rep("""A Legendary owned before can still drop (a better make is a better copy). Breaking one down gives
crafting's Legendary yield (5 old iron) and 3 ember shards; crafting prices it.""",
"""A Legendary owned before can still drop (a better make is a better copy); a never-owned one is
four times as likely. An old copy sells, or waits on Rook's shelves. The forge never works a
Legendary or a set piece, and does not yet break one down (crafting's call; they have agreed 5 old
iron and 3 ember shards when it does).""")
rep("| **Belt** | draughts and remedies (health, moonpetal, antidote, bandages) | counts, a carry limit of 10 each (a balance number, not places) |",
    "| **Belt** | draughts and remedies (health, moonpetal, antidote, bandages) | counts, a carry limit of 20 each (combat's number to move, not places) |")
rep("""| Leather Cap | +1 armour, +8 health |
| Iron Helm | +3 armour, +4 health; 2% slower |
| Padded Jerkin | +2 armour, +10 health |
| Chain Shirt | +5 armour, +6 health; 4% slower |
| Traveller's Cloak | +3% speed, +1 armour |""",
"""| Leather Cap | +2 armour, +16 health |
| Iron Helm | +3 armour, +6 health; 2% slower |
| Padded Jerkin | +3 armour, +12 health |
| Chain Shirt | +5 armour, +6 health; 4% slower |
| Traveller's Cloak | +3% speed (never scaled), +3 armour, +12 health |""")
rep("| Sets and Legendaries | `items.json`, `Rpg/Loot.cs` (`Sets`), `Character.Kit` |", "| Sets and Legendaries | `items.json`, `loot.json` (`sets`), `Character.Kit` |")
open(p, 'w', encoding='utf-8').write(s)
print("ok")
