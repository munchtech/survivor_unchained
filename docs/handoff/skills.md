# Handoff: skills look and feel

For the next skills lead. Read in this order:

1. `docs/team/README.md` (the bar, how we work, heavy work takes turns).
2. `docs/team/RESUME.md`.
3. This page.
4. `docs/team/skills.md` (status, grades, the judgements waiting).

Branch: `worktree-agent-a191ed81e2df462cf` (pushed). Merge `origin/claude/vigilant-galileo-l6jqyx`
into your own worktree, then this branch if the main session hasn't merged it yet.

## The owner's words

- "we are striving for perfection". "AAA standard". "I don't want to polish, I want to create
  perfection." "Do we have soul?" Never settle: remake rather than skip.
- "leveling up all our skills ... leverage our gpu as always to create amazing effects and be
  careful of crop/squaring issues". Judge at full resolution, in a packed crowd.
- On loot (relayed by the main session): the old beams were "solid pastel tubes". The Legendary's
  was "a huge solid cream bar slanting across the screen". Lights must read as light, not geometry.

## The brief

You own how every skill looks, sounds and feels in play: arts, auto-attacks, evolutions, blessings,
her rise, the enemy's verbs, and loot's light (LOOT_DESIGN.md §8). Each skill must:
- read at a glance in a horde;
- keep its school's colour and shape;
- land every hit;
- grow with rank.

Combat owns mechanics and numbers: propose changes, never make them. Batch shots in one Godot turn
and look once. Use Krea only through the `gpu` turn. Commit and push at milestones; the main session
merges, and you open no PRs. Run `dotnet test` (in `godot/tests`) before every commit. Use British
spelling. Hand off at about 500k tokens.

## Done this round (all seen at 1920×1080; last commit 8f84a1fc)

- **Loot's light, remade** (`BattleFx.Loot.cs`, `shaders/loot_beam.gdshader`):
  - **What was wrong**: the inherited light was a world-upright cylinder. Under the 56° camera, the
    40 m pillar leaned off the screen's middle and swelled as it neared the camera. Its ember ring
    read as an orange hoop.
  - **The fix**: each light is a quad held upright on the screen at its item's depth. The kind and
    parameter ride in the basis's z scale, the half-width in x, the height in y. Kinds: 1 Rare,
    2 Epic, 3 Set, 4 Pillar (reaches just past the screen's top), 5 Strike, 6 Glow, 7 Shaft.
  - **How each light is drawn**: gaussians. The hairline core is in the band's colour, and the glow
    and pool go deeper (`deep = tint²/max`). `blend_premul_alpha` covers a little of the ground
    behind, so by day the light stays coloured instead of washing pastel.
  - **Arrivals**: driven by the pickup's own `Age`, not by Ev.Drop, because the event fires where
    the item spawns and the item then slides. Lesser lights grow out of the ground. A Legendary's
    light falls down the screen onto it, flashes, and the pillar stands up (`Struck`: embers and a
    jolt, once per pickup id).
  - **Switches**: `--loot` now takes `--loot-at T`. `--loot-tiers` items have no names
    (no Ref), so they get no labels; use `--loot` or `--hoard N` for label pictures.
- **Every other column of light** (`BattleFx.Pillar`, now in `BattleFx.Loot.cs`) is a timed Shaft
  (kind 7) in the same batch, its colour normalised to 1.1 at most. It covers a strike landing, a
  level, an evolution (that one was a solid cream bar), a chest, and the night won (now one gold
  column). The old `beams` pool now serves only `Band`.
- **Cold, Then Not's wall** (`shaders/fire_wall.gdshader`, `FireCards` in `BattleFx.Rise.cs`): a
  ring of 160 cards, each turned about the upright to the camera in the vertex shader and
  cos²-blended into its neighbours. Colours were measured: 0.95/0.5/0.1 rendered as apricot
  (236, 155, 88), so they are deeper now. Grade 4 on polish is not yet earned; it is still a
  little apricot where cards stack.
- **Burning ground** (`FirePatch`, Skills): the same cards in small, round the ground's edge.
- **The Dig**:
  - `Fx/MineTub.cs`: a riveted, flared, rusted hull with bands and straps, angular spoil, warm
    lumps, flanged wheels, and a hooded lamp with a small OmniLight.
  - Grimtunnel under the ground is sunk by his size (`CrowdView`) in a heaving mound textured from
    the Dig's clay layer (`DigLayer` reads arena art's texture array).
  - `--tubs` runs a tub past her every three seconds. `--on boss` now shoots `tubrun`, `fuse`,
    `cavein`, `fissure`, `under`, `tubtest`.
- **Hallowed Ground**: `shaders/rune_ring.gdshader`, staves and twigs drawn as distance fields,
  held at waist height and turning. Holy blasts flash and burst gold, not white.
- **Grave Tether**: a violet coil round a dark core, with rose motes running back to her.
- **The chakram**: worn steel (roughness 0.55); mirror-polished, it read as a white cog in the Dig.

## Next, in order

1. Moonbrand near her (lavender). The Firepot burst itself is still a soft orange fireball.
2. Shoot the night's victory column (`--minute 29.9` and kill the boss, or `--on boss`) and a
   chest's column. Both are built, not seen.
3. Evolutions and unions; the arts; sound per skill.
4. Combat's asks: a fed deadfall, and the "His age" pale-blue ring.
5. The Legendary's heavier fall arc (optional, LOOT_DESIGN §8.2).
6. Answer the judgements on `docs/team/skills.md` when someone rules: elites flashing white en
   masse; the size of the Legendary's foot glow by night.

## Decisions (why)

- **Light upright on the screen**: under a pitched camera, a world-upright pillar leans and swells.
- **Light is gaussians, never an edge**; by day, cover a little of the ground behind.
- **Arrivals follow the pickup's age**: the drop event fires before the thing has slid to rest.
- **Fire standing up faces the camera**: a cylinder's edge-on sides read as a smooth stripe.
- **Measure colour on the frame**: AgX turns wide orange near 1 into apricot.
- Inherited, still true: hues below the knee; a crowd is told by its first few; nothing lights her
  but her own moments; danger keeps its language; a decal's emission ignores alpha.

## Failures, and why

- **The pools first veiled too much**: by day they read as dark smudges. Their veil is now 0.06.
- **`dig/albedo.jpg` is a `CompressedTexture2DArray`**: `GD.Load<Texture2D>` threw an
  InvalidCastException. Load it as a `TextureLayered` and take `GetLayerData(layer)`.
- **The mound's own dark noise** read as a black disc on the lit ground. Use the Dig's clay instead.
- **Tub spoil as smooth low spheres** read as pillows; the spoil is now boxes.

## Gotchas

- **Setting up a worktree**:
  - Make a junction from `godot/assets` to `public/assets`, then
    `git update-index --assume-unchanged godot/assets`.
  - Copy `.godot` from another worktree with robocopy (2 GB).
  - Copy `public/assets/**/*.import` from the main checkout
    (`C:\Users\munch\Desktop\survivorsunchained\public\assets`); without them, gltf files fail.
  - Run the import twice.
- **The worktree guard** refuses `cd X && git ...` chains and Python heredocs that write files.
  Write a `.py` to the scratchpad and run it, and keep git commands plain.
- **The tools** are in the session scratchpad, `.../scratchpad/vfx/`:
  - `shot.py`, `sweep.py`, `sheet.py`;
  - `crops.py OUT name:x0,y0,x1,y1 ...` (new: full-resolution crops);
  - `zoom.py`;
  - `turn_run.sh godot "<who>" bN.sh`;
  - `repoint2.py`, as the model for pointing the tools at a new worktree.
- For `sheet.py` globs on Windows, pass Windows paths (`C:\...\.shots\\name_*.png`).
- The import churns about 1100 `.import` files (line endings only). Commit only real files.

## Collaborators

- **Main session**: merges. Send it `vfx/for_main_loot_light.png` (before and after) with the
  loot result.
- **UI design** (`a4fdbc49786ba8b7f`): ground labels and the edge pointer are theirs. They sit
  well over the new lights (see the note on the status page).
- **Combat** (`a739d6792d21f5efd`): `--tubs`; the tub runs at 16 m/s.
- **Animation** (`a7dd95d00c4a6a017`): Grimtunnel's Under sink in `CrowdView`.
- **Performance** (`a0eb8c612c94d4aa5`): costs are on the status page.
- **Experience director**: paused. The judgements wait on the status page.

## Files to read first

1. `docs/team/skills.md`
2. `godot/src/Fx/BattleFx.Loot.cs` and `godot/shaders/loot_beam.gdshader`
3. `godot/src/Fx/BattleFx.Skills.cs` (Flight, SkillGround, RuneRing, FirePatch), `BattleFx.Rise.cs`
   (FireCards), `BattleFx.Dig.cs`, `MineTub.cs`
4. `godot/shaders/fire_wall.gdshader`, `rune_ring.gdshader`, `chakram.gdshader`
5. `godot/src/Fx/BattleFx.cs` (Handle, Blast, Pickups)
