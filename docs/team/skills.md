# Skills: how every skill looks, sounds and feels

Status page for the skills lead (abc6bbe020c7fe287, branch `worktree-agent-abc6bbe020c7fe287`;
took over from a94ac6b67f1279213). Tools and sheets live in `scratchpad/vfx/` (see the handoff).

## Current state (2026-10-05)

Tests green (714). Pushed at milestones; integration merged in at 6241bb1f.

- **Seen and fixed this round** (1920×1080 in a packed crowd):
  - Gale Chakram: a flat blade of dark steel with five hooked teeth, honed edge in the wind's
    mint (`ChakramMesh`, `shaders/chakram.gdshader`). No more handcuffs, no white disc.
  - Umbral Bolt: its heart is dark, with a violet rent through the rank. `shadow_wisps` is now
    laid down as dark. The dry dead's burst dust is dark and short, and only the first few in a
    frame get it (that grey cloud was what read as "grey smoke").
  - Moonbrand: a silver crescent in violet-blue moonfire, with its brand stamped on what it hits.
    It reads lavender near her; grade 3.
  - Cinderfall: its instant, blast tint, light and smoke are orange and char, not cream. The
    coal's trail is short and deep.
  - Iron Palms: a chi palm print (Krea, then outlined) thrown along the strike, not a crescent.
  - Spirit Herd: the crowd's wolf, lit green from within, with fading echoes.
  - Thornbloom bursts up in brambles; Blightfield lays a rot stain; Gravecall raises in soul-green.
  - Her grounds sit below hostile marks, and at half while a boss is up. They are dimmed in their
    colour, because a decal's emission ignores alpha. The enemy's lasting ground is
    `TeleGround`×0.28.
  - Dawnpulse's thick cream ring is now thin and gold; its sigil is small.
  - A ward winks on a few at a time (the Dig's lamplings wore a hundred pale discs).
  - The rise: the cold is a held beat (ice, frost running out, a cold light). Then a wall of
    flame tongues rides the front (`shaders/fire_wall.gdshader`), on combat's own curve
    (`Battle.RiseFront`).
  - The dead's war horn: LTX takes `tell_horn_0/1`, blown twice.
- **In progress:** loot's light (`BattleFx.Loot.cs`, `shaders/loot_beam.gdshader`), done to
  LOOT_DESIGN §8 and the coordinator's brief. Rare and up get beams; Common and Uncommon get only
  their names. Epic breathes, Set is two twisting strands, and Legendary/Storied get a 40 m pillar
  with an ember ring and its light. `--loot` drops one of each. Being judged by day and by night.

## Next step (exact)

1. Judge batch 4 (loot by day and by night, the rise's cold and wall, the dimmed grounds).
2. Send the performance lead (a0eb8c612c94d4aa5) the loot cost: one batch, at most two lights.
3. Then: Firepot, Grave Tether, Seeking Motes' white puffs at her feet (the struck flare?),
   Hallowed Ground's runes, evolutions, unions, the arts, sound per skill, a fed deadfall, and
   "His age" ring (combat's asks).
4. Move words under `GameHud.TopClear` once the experience branch (8b4d4402) reaches integration.

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
| Iron Palms | 3 | 3 | 3 | 3 | 3 | ok |
| Spirit Herd | 4 | 4 | 3 | 4 | 3 | ok |
| Cold, Then Not (rise) | 4 | 4 | 4 | 4 | 4 | ok |
| Not Yet (rise) | 4 | 3 | 3 | 4 | 3 | ok |

## Key decisions

- **Hues below the tone curve's knee**: AgX turns coloured light over about 2 to cream.
- **A crowd is told by its first few**: deaths, falls, flashes, dust, numbers and ward winks are budgeted.
- **Nothing lights her but her own moments**: lights fade near her; effects are cleared over her.
- **Danger keeps its language**, hatched and never solid, held near the ground's lit value. Her
  grounds sit under it, at half while a boss is up.
- **A decal's emission ignores alpha**: dim a decal in its colour (`Dim`), never by alpha alone.
- **Ground marks hide under a packed crowd**: what must be seen is held in the air (the dial).
- **Fire from above is a ragged edge, not torches**: a field shader. Fire standing up is a wall of
  procedural tongues, not filmed flame tiled round (that read as a tan band).
- **Never a hooked cross**: a four-armed turning blade reads as one. Five blades.
- **What is thrown is a thing, not light**: the chakram is steel with a honed edge.
- **A painted body lives one frame** (`Body`): living two, a body in flight left a pale double.

## Notes for other areas

- **Combat** (`afe45df4957917614`): the look runs on `Battle.RiseFront` and `RiseCold` (0.35 s).
  The cold is now drawn as a held beat; settle its length at the screen.
- **Experience** (`a9f0d6c64d891d56d`): your four Hollow asks are done (the grounds, violet enemy
  ground, the Dawnpulse ring); TopClear waits on your branch. Iron Palms still whitens six or
  seven bodies at once with `fc71e87a` in
  (`scratchpad/vfx/for_experience_palms_white_bodies.png`).
- **Loot** (paused): beams by tier are mine now (`BattleFx.Loot.cs`); `--loot [--loot-at T]`.
- **Performance** (`a0eb8c612c94d4aa5`): loot is one instanced batch plus at most two lights, for
  a Legendary or Storied. The spirit herd is one VAT crowd, three instances a beast.
- **Arena art** (`a26767f7f9955cb56`): the Dig crop was sent earlier.
