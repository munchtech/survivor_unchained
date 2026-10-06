import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
def rep(old, new):
    global s
    assert old in s, old[:80]
    s = s.replace(old, new)

rep("""- **Expected in Act 1** (`LootTests` simulates it from the counts above): about 250 gear rolls,
  three to five Legendaries (one certain), two to four set pieces, fifteen Epics.""",
"""- **Act 1, simulated** (`LootTests`, 60 runs of 18 nights and 10 days at these counts): about 215
  gear drops (39 Common, 78 Uncommon, 74 Rare, 18 Epic), 3 set pieces and 3.5 Legendaries, one of
  them certain; and in gear's place about 31 of the peoples' materials and 26 old iron.""")
rep("""| Common | small grey text | none | a dull clink: cloth thump for armour, a short iron tick for a weapon | – |
| Uncommon | green text | a low glow, 0.8 m | the clink and a soft high ring | – |
| Rare | blue text on a dark plate | 2.5 m, steady | one clear bell, struck once | small dot |
| Epic | violet, bordered plate | 5 m, a slow pulse | a struck bell held, with a low hum under it | violet diamond |
| Set | verdigris, double border, chain-link mark | 6 m, two strands that twist | two bells a fifth apart, struck together: a pair | verdigris diamond |""",
"""| Common | small grey words, near her only | none | a dull clink: cloth thump for armour, a short iron tick for a weapon | – |
| Uncommon | green words on a dark plate, near her only | none | the clink and a soft high ring | – |
| Rare | blue words on a dark plate | a low glow, 1.2 m | one clear bell, struck once | small dot |
| Epic | violet, framed plate | 3 m, thin, a slow pulse | a struck bell held, with a low hum under it | violet diamond |
| Set | verdigris, double border, chain-link mark | 4 m, two thin strands that twist | two bells a fifth apart, struck together: a pair | verdigris diamond |""")
rep("""Rules: the beam's height says the tier;""",
"""Seen at 1920×1080 (`docs/loot/`): six beams after one fight read as clutter by day (the experience
director), so Commons and Uncommons have no beam at all, only their names, as Diablo IV lights only
its best. Rules: the beam's height says the tier;""")
rep("""| Drop event and placeholder sounds | `Sim` (`Ev.Drop`), `src/Audio/Sfx.cs` | – (heard in the game) |""",
"""| Drop event and placeholder sounds | `Sim` (`Ev.Drop`), `src/Audio/Sfx.cs` | – (heard in the game) |
| Names on the ground, the screen-edge pointer | `src/Ui/GroundLabels.cs`, `Game.Labels`, `Game.Offscreen` | seen: `docs/loot/labels_night.jpg` |
| The first Legendary's moment | `Journey.FirstLegendaryTaken(item, x, z)`, once a world | the experience director stages it |
| Pictures | `--loot [legendary]`, `--hoard N` | – |""")
open(p, 'w', encoding='utf-8').write(s)
print("ok")
