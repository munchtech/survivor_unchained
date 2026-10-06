import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
def rep(old, new):
    global s
    assert old in s, old[:80]
    s = s.replace(old, new)

rep("""The make is a word on the tooltip's second line""",
"""Armour has its own, gentler curve (×1, 1.8, 2.8, 3.4, 4.0): its reduction saturates
(armour ÷ (armour + 20)), and a full Heartwrought set at ×5.5 came to about 75% (combat). The
lasting answer is combat's: armour measured against the size of the blow (Path of Exile's rule),
so deep armour is worth what deep blows ask. A piece's flat rule damage (Kell's Lamp's flare, the
Drowned Coat's black water) grows with its make as its numbers do, so a deep copy is not a toy;
rules that read the blow or the weapon already grow with what they read.

The make is a word on the tooltip's second line""")
rep("""| Iron Helm (power) | Common | Uncommon | Rare | Epic |
|---|---|---|---|---|
| Worn (level 1–3) | 2.7 | 4.7 | 8.5 | 14.6 |
| Sound (10) | 5.7 | | | |
| Wrought (18) | 9.4 | | 15.6 (level 20) | |
| Heartwrought (34) | 19.5 | | | 35.4 |
""",
"""| Chain Shirt (power) | Common | Uncommon | Rare | Epic |
|---|---|---|---|---|
| Worn (level 1–3) | 3.7 | 5.8 | 9.9 | 15.7 |
| Sound (10) | 8.3 | | | |
| Wrought (18) | 14.0 | | 20.7 (level 20) | |
| Heartwrought (34) | about 24 | | | about 40 |
""")
rep("""2. **The hush.** For half a second the horde's sound drops by half (never the music), and the""",
"""2. **The hush.** For a second the music and the world's noise drop away (never the fight's own
   sounds: a warning under a hush is a blow unheard, combat's rule), and the""")
rep("""| **Forty-One Mouths** | weapon (butcher's cleaver) | 2 | the Kerchiefs | Below half health every kill mends 2% of your health; your blows bleed (15%). *You fight best hurt.* | At full health you deal 15% less. |""",
"""| **Forty-One Mouths** | weapon (butcher's cleaver) | 2 | the Kerchiefs | Below half health every kill mends 2% of your health; your blows bleed (15%). *You fight best hurt.* | Above four fifths of your health you deal 15% less (combat: "at full" is never true in a horde). |""")
rep("""| Iron Helm | +3 armour, +6 health; 2% slower |""", """| Iron Helm | +3 armour, +8 health; 2% slower |""")
open(p, 'w', encoding='utf-8').write(s)
print("ok")
