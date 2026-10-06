p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a191ed81e2df462cf\docs\team\skills.md"
s = open(p, encoding="utf-8").read()
start = s.index("## Current state (2026-10-05)")
end = s.index("## Grades (now)")
new = """## Current state (2026-10-05, handed off)

Tests green (747). Pushed, last `8f84a1fc`; the handoff is `docs/handoff/skills.md`.

- **Loot's light, remade** (`BattleFx.Loot.cs`, `shaders/loot_beam.gdshader`). Seen at 1920×1080
  by day and by night, with the labels and the edge pointer:
  - Every light is a quad upright on the screen: a hairline core in gaussian glows and a pool at
    its foot. The old world-upright tubes leaned and swelled into a cream bar.
  - Rare is a low blue glow; Epic a violet line with motes; Set two twisting strands; Legendary and
    Storied a pillar past the screen's top.
  - Lights grow as their thing lands. A Legendary's light falls onto it, then the pillar stands.
- **Every other column of light** (`BattleFx.Pillar`: a strike from the sky, a level, an evolution,
  a chest, the night won) is now a shaft in the same batch, held to the knee. The evolution's was a
  solid cream bar.
- **Cold, Then Not's wall** stands on cards turned to the camera; it is deeper orange. Seen.
- **The Dig** (`Fx/MineTub.cs`, `BattleFx.Dig.cs`): a real tub with spoil and a lamp. Grimtunnel is
  sunk in a mound of the Dig's clay. Seen.
- **Hallowed Ground**: a ring of runes in the air (`shaders/rune_ring.gdshader`); holy blasts are
  gold. **Grave Tether**: a violet coil with rose motes running back. **Burning ground** stands in
  low flame. **The chakram's face** is worn steel (it read as a white cog). All seen.

## Next step (exact)

1. Moonbrand near her (lavender); the Firepot burst itself (still a soft orange fireball).
2. Evolutions and unions, the arts, sound per skill.
3. Combat's fed deadfall and "His age" ring; the Legendary's heavier fall arc (optional).
4. See the night's victory column and a chest's (built, not yet shot).

"""
s = s[:start] + new + s[end:]
reps = [
    ("| Firepot | 2 | 3 | 3 | 3 | 2 | ok |", "| Firepot | 3 | 3 | 3 | 3 | 3 | ok |"),
    ("| Grave Tether | 2 | 2 | 2 | 3 | 2 | ok |", "| Grave Tether | 3 | 3 | 3 | 4 | 3 | ok |"),
    ("| Hallowed Ground | 2 | 3 | 2 | 3 | 2 | ok |", "| Hallowed Ground | 4 | 4 | 3 | 4 | 3 | ok |"),
    ("| Gale Chakram | 4 | 4 | 3 | 4 | 3 | ok |", "| Gale Chakram | 4 | 4 | 3 | 4 | 4 | ok |"),
]
for a, b in reps:
    assert a in s, a
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
