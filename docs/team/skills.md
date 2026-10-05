# Skills: how every skill looks, sounds and feels

Status page for the skills lead (a191ed81e2df462cf, branch `worktree-agent-a191ed81e2df462cf`; took
over from abc6bbe020c7fe287). Tools and sheets live in the session scratchpad's `vfx/` (see the
handoff).

## Current state (2026-10-05)

Tests green (747). Pushed: `f1951824` (loot's light), `56df2c8c` (the wall, the tub, the mound).

- **Loot's light, remade** (`BattleFx.Loot.cs`, `shaders/loot_beam.gdshader`). Judged at 1920×1080
  by day (the Verge) and by night (the arena), with the ground labels and the edge pointer:
  - The inherited light was a world-upright cylinder. Under the 56° camera the Legendary's 40 m
    pillar leaned off the middle and swelled toward the camera (the slanted cream bar), and its
    ember ring read as an orange hoop. The short beams read as tubes.
  - Now every light is a quad held upright on the screen at its item's depth: a hairline core in
    gaussian glows, palest at the heart and deepest at its edges, a pool on the ground at its foot,
    and a little of the ground behind covered, so it stays coloured by day.
  - Rare: a low blue glow. Epic: a taller violet line with motes. Set: two twisting strands, the
    front one brighter. Legendary and Storied: a pillar to just past the screen's top, embers at its
    foot, a lamp on what stands near.
  - Lights grow out of the ground as their thing lands. A Legendary's light falls down the screen
    onto it, flashes, and the pillar stands up out of it. All of this follows the pickup's own age,
    so it tracks the item as it slides to rest. No rings or hoops.
  - Labels sit over the lights and stay legible. Off screen, the amber chevron points. A pillar whose
    item lies below the screen still rises into view.
- **Cold, Then Not's wall** (`shaders/fire_wall.gdshader`) now stands on a ring of cards turned to
  the camera, so the ring's sides show tongues, not a smooth stripe. It is deeper orange, with heat
  only at the tall tongues' hearts. Seen; better, but still a little apricot where cards stack (grade
  below).
- **The Dig**: the tub is a real tub (`Fx/MineTub.cs`), seen by day and in the Dig. Grimtunnel under
  is sunk by his size in a mound of the Dig's clay. Seen; the mound reads as earth, not strongly.
- **Built, not yet seen**: the tub's darker angular spoil and broader rust; the chakram's worn face
  (it read as a white cog in the Dig's lamplight).
- **Swept at rank 4** (`vfx/sw1/`): Iron Palms' hands read well (grade up). Grave Tether's thread is
  barely seen. Hallowed Ground is a plain gold circle. Firepot is a soft orange blob. Judgement Disc
  is fine.

## Next step (exact)

1. Look at the tub's spoil and the chakram in the Dig (`--night dig --stage 1 --lab --tubs --on
   boss`, and the chakram given there).
2. Grave Tether: a coil you can see, and the heal running back up it to her.
3. Hallowed Ground: runes in its ring (soul, not a plain circle).
4. Firepot: burning ground with a ragged flame edge (the field shader), not a soft blob.
5. Then: Moonbrand near her; evolutions and unions; the arts; sound per skill; combat's fed
   deadfall and "His age" ring; the Legendary's heavier fall arc (LOOT_DESIGN §8.2, optional).

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
| Gale Chakram | 4 | 4 | 3 | 4 | 3 | ok |
| Umbral Bolt | 3 | 4 | 3 | 4 | 3 | ok |
| Moonbrand | 3 | 3 | 3 | 4 | 3 | ok |
| Iron Palms | 4 | 4 | 3 | 4 | 3 | ok |
| Spirit Herd | 4 | 4 | 3 | 4 | 3 | ok |
| Firepot | 2 | 3 | 3 | 3 | 2 | ok |
| Grave Tether | 2 | 2 | 2 | 3 | 2 | ok |
| Hallowed Ground | 2 | 3 | 2 | 3 | 2 | ok |
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
