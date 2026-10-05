# Skills: how every skill looks, sounds and feels

Status page for the skills lead (a191ed81e2df462cf, branch `worktree-agent-a191ed81e2df462cf`; took
over from abc6bbe020c7fe287). Tools and sheets live in the session scratchpad's `vfx/` (see the
handoff).

## Current state (2026-10-05, handed off)

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

## Grades (now)

1 (poor) to 5 (at the bar), from frames in play. "Before" is in this page's git history.

| Skill | Soul | Reads in a horde | Impact | School | Polish | Crop/square |
|---|---|---|---|---|---|---|
| Oathblade | 4 | 4 | 4 | 4 | 4 | ok |
| Cleaver | 4 | 4 | 4 | 4 | 4 | ok |
| Axe Gyre | 3 | 4 | 3 | 3 | 3 | ok |
| Judgement Disc | 3 | 3 | 3 | 4 | 3 | ok |
| Seeking Motes | 3 | 4 | 3 | 4 | 3 | ok |
| Cinderfall | 3 | 4 | 4 | 4 | 3 | ok |
| Rimeshard | 3 | 4 | 3 | 4 | 3 | ok |
| Volley | 3 | 4 | 3 | 3 | 3 | ok |
| Knifestorm | 3 | 4 | 3 | 3 | 3 | ok |
| Hoarfrost | 4 | 4 | 4 | 4 | 4 | ok |
| Dawnpulse | 3 | 3 | 4 | 4 | 3 | ok |
| Arcweb | 4 | 4 | 4 | 4 | 3 | ok |
| Verdant Lance | 4 | 4 | 3 | 4 | 3 | ok |
| Reaving Arc | 4 | 4 | 4 | 4 | 3 | ok |
| Thunderhead | 3 | 3 | 3 | 4 | 3 | ok |
| Gale Chakram | 4 | 4 | 3 | 4 | 4 | ok |
| Umbral Bolt | 3 | 4 | 3 | 4 | 3 | ok |
| Moonbrand | 3 | 3 | 3 | 4 | 3 | ok |
| Iron Palms | 4 | 4 | 3 | 4 | 3 | ok |
| Spirit Herd | 4 | 4 | 3 | 4 | 3 | ok |
| Firepot | 3 | 3 | 3 | 3 | 3 | ok |
| Grave Tether | 3 | 3 | 3 | 4 | 3 | ok |
| Hallowed Ground | 4 | 4 | 3 | 4 | 3 | ok |
| Cold, Then Not (rise) | 4 | 4 | 4 | 4 | 3 | ok |
| Not Yet (rise) | 4 | 3 | 3 | 4 | 3 | ok |
| Loot's light | 4 | 4 | 4 | — | 4 | ok |

## Key decisions

- **Loot's light is upright on the screen, not in the world**: a world-upright pillar leans and
  swells under a pitched camera.
- **Light is gaussians, never an edge**: a hairline core, deeper-coloured glows and a pool. By day,
  a little of the ground behind is covered so the colour holds.
- **Arrivals follow the pickup's age**, not the drop event: the event fires where it spawns, and the
  thing slides on from there.
- **Fire standing up faces the camera**: a cylinder's edge-on sides read as a smooth stripe.
- **Measure colour, don't guess**: AgX turns wide orange at about 1 into apricot. Sample the frame.
- **Hues below the tone curve's knee**: AgX turns coloured light over about 2 to cream.
- **A crowd is told by its first few**: deaths, falls, flashes, dust, numbers and ward winks are budgeted.
- **Nothing lights her but her own moments**: lights fade near her; effects are cleared over her.
- **Danger keeps its language**: her grounds sit under it, at half while a boss is up.
- **A decal's emission ignores alpha**: dim it in its colour.
- **What is thrown is a thing, not light**: the chakram is worn steel with a honed edge.

## Judgements needed (the experience director is paused)

- **Elites flash white en masse**: the struck flare's cap of three a frame exempts elites. Eight
  elite risen hit by one Iron Palms or Hallowed Ground all go white
  (`vfx/sw1/sw1_iron_palms.png`). Cap elites too, or keep the exemption? (The cap is in
  `CrowdView.cs`, the experience director's rule.)
- **The Legendary's foot by night**: its lamp and pool make a broad warm glow on the ground, about
  300 px across. It reads as "something burns there". Keep it, or go smaller?

## Notes for other areas

- **UI design** (`a4fdbc49786ba8b7f`): the ground labels sit over the new lights and read well. A
  Rare's label covers most of its low glow; that is acceptable, since the glow is the find-me and
  the name is the what. The Legendary label's own glow is a soft rectangle; it might sit better as an
  ellipse.
- **Performance** (`a0eb8c612c94d4aa5`): loot is one instanced batch of quads (one per Rare+ item,
  plus a strike per falling Legendary) and at most two OmniLights. The wall is one 160-quad mesh.
  Each Dig tub carries one small OmniLight (four tubs at most).
- **Combat**: `--tubs` runs a tub past her for pictures. The tub runs at combat's 16 m/s.
- **Animation**: `CrowdView` sinks a script's Under body by its size (Grimtunnel 0.54 m deeper).
