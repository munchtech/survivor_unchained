# Credits

Survivor Unchained is made by Munchtech. Its world, lore and combat roots are The Ember Watch.

These credits list everything in the game that others made, with each licence. The audit behind it, with sources, risks and what we plan to replace, is `docs/legal/ASSET_PROVENANCE.md` (2026-10-04). Works under CC BY are used with the credit required below. Works under CC0 need no credit, and we give it with thanks.

Some lines below are written by the fetch tools and checked by them before they add another, so keep their exact form:

- `tools/assets/ambientcg.py`: `- <id>: ambientCG (...), CC0`
- `tools/godot/arena_ground.py`: `- <id>: Poly Haven (...), CC0`
- `tools/assets/polyhaven.py`: looks for `polyhaven.com/a/<id>)`
- `tools/assets/sketchfab.mjs`: appends at the end

## Engine and runtime

- **Godot Engine** 4.5 (with C# support). Copyright (c) 2014-present Godot Engine contributors; copyright (c) 2007-2014 Juan Linietsky, Ariel Manzur.
  - MIT licence: https://godotengine.org/license
  - It includes third-party components under their own licences, listed in Godot's `COPYRIGHT.txt`. Among them are Jolt Physics (MIT), FreeType, HarfBuzz, ICU, mbedTLS and ENet.
- **.NET** 8 runtime and GodotSharp. .NET Foundation and contributors; MIT. Third-party notices are in .NET's `THIRD-PARTY-NOTICES.TXT`.

## Typefaces (SIL Open Font License 1.1)

All three ship in `godot/art/fonts`, each beside its licence, `OFL-*.txt`.

- **Cinzel**: Copyright 2020 The Cinzel Project Authors (https://github.com/NDISCOVER/Cinzel).
- **Alegreya**: Copyright 2011 The Alegreya Project Authors (https://github.com/huertatipografica/Alegreya).
- **Alegreya Sans**: Copyright 2013 The Alegreya Sans Project Authors (https://github.com/huertatipografica/Alegreya-Sans).

## Used under Creative Commons Attribution 4.0 (credit required)

Licence: https://creativecommons.org/licenses/by/4.0/. Each work is provided as is, without warranty, by its creator. Our changes are listed with it.

### Weapons, from Sketchfab (`public/assets/weapons`)

Changes for every weapon:

- turned and scaled to one grip convention in code (`godot/src/Actors/Arms.cs`);
- photographed in the game, and the photograph painted over, for its item icon (`godot/art/ui/icons/item`).

- "Chevalier Sword" by rubenve (https://sketchfab.com/rubenve), https://sketchfab.com/3d-models/chevalier-sword-b2662f2666a844e8a1bd0e7c4a7672d8 -> chevalier_sword.glb
- "Viking Sword (Game Model)" by Michael Makivic (https://sketchfab.com/makivic), https://sketchfab.com/3d-models/viking-sword-game-model-a05d0bd73e9e4508b873ffd7b6a6238d -> viking_sword.glb
- "medieval sword" by LowSeb (https://sketchfab.com/lowseb), https://sketchfab.com/3d-models/medieval-sword-da574cba504e4b83a3293f3d3bd067fb -> longsword.glb
- "Zweihander" by Siesta (https://sketchfab.com/siesta), https://sketchfab.com/3d-models/zweihander-bde0f0351bf443f6bed68aeff84b4129 -> zweihander.glb
- "Medieval Mace": designed by Kama Modeling (https://sketchfab.com/KamaModeling); modelled and textured by Yavuz Temel. https://sketchfab.com/3d-models/medieval-mace-83217215a0c541b2956a8e87a4ae62fe -> mace.glb
- "Viking battle axe" by Mikhail Antonov (https://sketchfab.com/xeofox), https://sketchfab.com/3d-models/viking-battle-axe-b7123192adbf40f68043c57dd8ddcd15 -> viking_axe.glb
- "Snake Axe" by Ashley Jay Thornton (https://sketchfab.com/AshleyJay), https://sketchfab.com/3d-models/snake-axe-ace485ac031c4ee0a918e99d2b80560b -> snake_axe.glb
- "Mage Staff" by RMBehan (https://sketchfab.com/RMBehan), https://sketchfab.com/3d-models/mage-staff-a172d06792734bbc9b11272b4f497c2c -> mage_staff.glb
- "Medieval Crossbow" by iedalton (https://sketchfab.com/iedalton), https://sketchfab.com/3d-models/medieval-crossbow-cc36ed347db340d59bd2ec7b06ae0d63 -> crossbow.glb
- "Medieval Shield" by Artem Mykhailov (https://sketchfab.com/CGArtem), https://sketchfab.com/3d-models/medieval-shield-b98b8f64d935415aab0fe9b70074511f -> shield_round.glb
- "Silver Bladed weapons - Fantasy weapon set" by Peter Nox (https://sketchfab.com/Peter.Nox; listed as Asylum Nox when downloaded), https://sketchfab.com/3d-models/silver-bladed-weapons-fantasy-weapon-set-d5189211a1d348b0a9d7ddc052a22989 -> daggers.glb

### Creatures, from Sketchfab (`godot/art/beasts`)

Changes: scaled and tinted per kind. Each creature plays its own clips, and moves it lacks are composed in code over its poses. It is baked into the crowd's animation textures.

- "Animated Wolf Scene" by Roo (https://sketchfab.com/roo3d), https://sketchfab.com/3d-models/animated-wolf-scene-5d55506494e5460eaadf04370e07cd5c -> wolf.glb
- "Animated Realistic Boar – 3D Animal Model" by AnimalMesh 3D (https://sketchfab.com/AnimalMesh3D), https://sketchfab.com/3d-models/animated-realistic-boar-3d-animal-model-f672a7fd93e84997b80a54ba30956111 -> boar.glb. **Under review**: its page also restricts this version to personal use (see `docs/legal/ASSET_PROVENANCE.md`, CR-02).
- "Goblin Ghoul" by Rodrigo Bento (https://sketchfab.com/rodrigobento), https://sketchfab.com/3d-models/goblin-ghoul-a6c6fffee3d34823b6d87a7054782577 -> lampling.glb. Changes: the lamplings' hats, lamps and satchels are made in code and carried on its bones.

### Motion: the heroine's idles (`godot/art/anim/heroine.res`)

- 100STYLE dataset by Ian Mason, Sebastian Starke and Taku Komura, "Real-Time Style Modelling of Human Locomotion via Feature-Wise Transformations and Local Motion Phases" (2022), https://zenodo.org/records/8127870.
  - Takes used: Heavyset, Strutting, Angry and Crouched (and Followed as reference for one glance).
  - Changes:
    - retargeted to her skeleton;
    - feet locked;
    - looped;
    - centred;
    - arms re-keyed to hold her weapons.
  - Each take and stretch is recorded in `tools/anim/manifest.json`.

## Used under service terms or model licences

- **Adobe Mixamo** motion, used in the game under Mixamo's terms; the raw files are not distributed.
  - The heroine's Crashing Leap: "Standing Melee Run Jump Attack", retargeted and retimed.
  - The townsfolk:
    - a feminine walk;
    - a weight-shift idle;
    - "General Conversation" talk;
    - sitting on a chair and on the floor;
    - picking up.

  All are retargeted to the kit's bodies. Each folk clip's source is in `godot/art/anim/folk_clips.json`.
- **NVIDIA Kimodo** (Kimodo-SOMA-RP): generated motion for the townsfolk's men's walk, women's talk, arms crossed, cheer, wave and work at a table (`tools/anim/kimodo_gen.py`). Kimodo is licensed by NVIDIA Corporation under the NVIDIA Open Model License.
- **Reallusion AccuRIG** rigged the heroine's body. Her weights were then folded onto our own skeleton; no Reallusion content ships.

## Third-party works under CC0 (no credit required; credited with thanks)

### Quaternius (https://quaternius.com)

- Universal Base Characters, Modular Character Outfits – Fantasy, and Universal Animation Library 1 and 2 -> `public/assets/people` (gathered by `tools/assets/people.py`). The game's skeleton is the Animation Library's.
- Medieval Village MegaKit, Fantasy Props MegaKit and Stylized Nature MegaKit -> `public/assets/env/{village,props,nature}` (gathered by `tools/assets/env.py`), and their sRGB copies in `godot/art/srgb`.

### KayKit by Kay Lousberg (https://www.kaylousberg.com)

Gathered by `tools/assets/build.mjs`. Their meshes are also inside the zones' landmarks (`godot/data/zones/*/landmarks.glb`). The Adventurers' licence file is `public/assets/LICENSE-KayKit.txt`.

- KayKit Character Pack: Adventures 1.0 -> `public/assets/characters/{barbarian,knight,mage,rogue,rogue_hooded}.glb`, `props/adventure_items.glb`, `anim/humanoid.glb`
- KayKit Character Pack: Skeletons 1.0 -> `public/assets/characters/skeleton_*.glb`
- KayKit Dungeon Remastered 1.0 -> `public/assets/props/dungeon.glb`
- KayKit Medieval Hexagon Pack 1.0 -> `public/assets/props/hex_buildings.glb`, `hex_nature.glb`
- KayKit Halloween Bits 1.0 -> `public/assets/props/halloween.glb`

### Kenney (https://kenney.nl)

- Particle Pack (https://kenney.nl/assets/particle-pack) -> `godot/art/fx`. These are the effects' sprites: smoke, sparks, flames, magic and slashes, packed into a texture array, plus embers, puff and runes.
- Impact Sounds, RPG Audio and Interface Sounds (https://kenney.nl/assets/impact-sounds, /rpg-audio, /interface-sounds) -> `godot/art/sound`, as mono 16-bit WAV.

### OpenGameArt field recordings

Cut to loop and made mono at 24 kHz (the game plays each wide, its right side half a take along), in `godot/art/sound`:

- "Park ambiences" by thimras (https://opengameart.org/content/park-ambiences) -> bed_birds_0.wav (birdsong by a copse, traffic under it filtered out) and bed_water_0.wav (a small river over a low step)
- "Fireplace Sound loop" by PagDev (https://opengameart.org/content/fireplace-sound-loop) -> bed_fire_0.wav
- "Crickets Ambient Noise - loopable" by Wolfgang_, recording by Ted Kerr (https://opengameart.org/content/crickets-ambient-noise-loopable) -> bed_crickets_0.wav
- "Blacksmith's Hammer" by vishwajai (https://opengameart.org/content/blacksmiths-hammer) -> anvil_0.wav

### MakeHuman (http://www.makehumancommunity.org), made with MPFB

- The heroine's head, eyes, brows, lashes, teeth and tongue, and the targets that shape her face: MakeHuman system assets, CC0 -> `godot/art/people/heroine.glb`, `godot/art/people/head_tex`. (The hero's join when his body ships: `docs/legal/STEAM_CHECKLIST.md` E.)
- The heroine's head skin, "Light skin female ginger" by MargaretToigo (http://www.makehumancommunity.org/node/1130), CC0 -> `godot/art/people/head_tex/heroine_head.jpg`, `heroine_graft.jpg`.

### Poly Haven (https://polyhaven.com)

Each Poly Haven asset is credited to its scanners and artists, by name.

The Verge's ground (`godot/art/ground`, and `public/assets/ground` for the web game; gathered by `tools/assets/ground.py`, stacked by `tools/godot/ground_atlas.py`):

- "Sparse Grass" by Amal Kumar (https://polyhaven.com/a/sparse_grass): grass
- "Forest Leaves 02" by Rob Tuytel (https://polyhaven.com/a/forest_leaves_02): leaves
- "Forest Ground 04" by Rob Tuytel, Rico Cilliers (https://polyhaven.com/a/forest_ground_04): dirt; also cut out for graves in `godot/art/materials/forest_ground_04`
- "Mud Forest" by eye-candy.xyz (https://polyhaven.com/a/mud_forest): mud
- "Cobblestone 05" by Rob Tuytel (https://polyhaven.com/a/cobblestone_05): stone
- "Mossy Rock" by Rob Tuytel (https://polyhaven.com/a/mossy_rock): rock
- "Burned Ground 01" by Rob Tuytel (https://polyhaven.com/a/burned_ground_01): blight

Building materials, 1k (`godot/art/materials`):

- "Medieval Blocks 03" by Rob Tuytel (https://polyhaven.com/a/medieval_blocks_03): dressed stone for walls, the gate, towers, the crypt and pillars
- "Castle Wall Slates" by Rob Tuytel (https://polyhaven.com/a/castle_wall_slates): slate roofs, clay tiles
- "Rock Boulder Dry" by Dimitrios Savva, Rico Cilliers (https://polyhaven.com/a/rock_boulder_dry): headstones, rock
- "Rough Wood" by Rob Tuytel (https://polyhaven.com/a/rough_wood): posts, crosses, timber

Outfit materials (`godot/art/outfit`, `godot/art/people/outfit_tex`; tinted copies `outfit_*_diff.jpg` made by `tools/assets/heroine_outfits.py`):

- "Brown Leather" by Rob Tuytel (https://polyhaven.com/a/brown_leather)
- "Curly Teddy Natural" by colormass, Rico Cilliers (https://polyhaven.com/a/curly_teddy_natural)
- "Fabric Leather 02" by Rob Tuytel (https://polyhaven.com/a/fabric_leather_02)
- "Faux Fur Geometric" by colormass, Rico Cilliers (https://polyhaven.com/a/faux_fur_geometric)
- "Leather Red 02" by Rob Tuytel (https://polyhaven.com/a/leather_red_02)
- "Metal Plate" by Rob Tuytel (https://polyhaven.com/a/metal_plate)
- "Metal Plate 02" by Rob Tuytel (https://polyhaven.com/a/metal_plate_02)
- "Rough Linen" by colormass, Rico Cilliers (https://polyhaven.com/a/rough_linen)
- "Rusty Metal 02" by Rob Tuytel (https://polyhaven.com/a/rusty_metal_02)
- "Velour Velvet" by colormass, Rico Cilliers (https://polyhaven.com/a/velour_velvet)

The light the items are photographed in (`godot/art/studio`, 1k HDR):

- "Studio Small 08" by Sergej Majboroda (https://polyhaven.com/a/studio_small_08)

The arenas' grounds (`godot/art/arena/<place>`, by `tools/godot/arena_ground.py`; each place's layers are in its `layers.json`). Their authors, per Poly Haven:

- Rob Tuytel: brown_mud_02, brown_mud_03, brown_mud_leaves_01, burned_ground_01, forest_leaves_04, grass_path_3, ground_grey, mossy_rock, red_mud_stones, rocks_ground_06; dry_mud_field_001 and river_small_rocks with Rico Cilliers; forest_leaves_03 with Dimitrios Savva
- Amal Kumar: dark_rock, gravel_road, gravel_stones, muddy_tracks, rocky_terrain, rocky_trail, stone_pathway_02
- eye-candy.xyz: mud_forest, wood_chips
- Dimitrios Savva: quarry_wall; roots with Dario Barresi
- Charlotte Baglioni: withered_grass

- brown_mud_02: Poly Haven (https://polyhaven.com/a/brown_mud_02), CC0
- brown_mud_03: Poly Haven (https://polyhaven.com/a/brown_mud_03), CC0
- brown_mud_leaves_01: Poly Haven (https://polyhaven.com/a/brown_mud_leaves_01), CC0
- burned_ground_01: Poly Haven (https://polyhaven.com/a/burned_ground_01), CC0
- dark_rock: Poly Haven (https://polyhaven.com/a/dark_rock), CC0
- dry_mud_field_001: Poly Haven (https://polyhaven.com/a/dry_mud_field_001), CC0
- forest_leaves_03: Poly Haven (https://polyhaven.com/a/forest_leaves_03), CC0
- forest_leaves_04: Poly Haven (https://polyhaven.com/a/forest_leaves_04), CC0
- grass_path_3: Poly Haven (https://polyhaven.com/a/grass_path_3), CC0
- gravel_road: Poly Haven (https://polyhaven.com/a/gravel_road), CC0
- gravel_stones: Poly Haven (https://polyhaven.com/a/gravel_stones), CC0
- ground_grey: Poly Haven (https://polyhaven.com/a/ground_grey), CC0
- mossy_rock: Poly Haven (https://polyhaven.com/a/mossy_rock), CC0
- mud_forest: Poly Haven (https://polyhaven.com/a/mud_forest), CC0
- muddy_tracks: Poly Haven (https://polyhaven.com/a/muddy_tracks), CC0
- quarry_wall: Poly Haven (https://polyhaven.com/a/quarry_wall), CC0
- red_mud_stones: Poly Haven (https://polyhaven.com/a/red_mud_stones), CC0
- river_small_rocks: Poly Haven (https://polyhaven.com/a/river_small_rocks), CC0
- rocks_ground_06: Poly Haven (https://polyhaven.com/a/rocks_ground_06), CC0
- rocky_terrain: Poly Haven (https://polyhaven.com/a/rocky_terrain), CC0
- rocky_trail: Poly Haven (https://polyhaven.com/a/rocky_trail), CC0
- roots: Poly Haven (https://polyhaven.com/a/roots), CC0
- stone_pathway_02: Poly Haven (https://polyhaven.com/a/stone_pathway_02), CC0
- withered_grass: Poly Haven (https://polyhaven.com/a/withered_grass), CC0
- wood_chips: Poly Haven (https://polyhaven.com/a/wood_chips), CC0
- dry_decay_leaves: Poly Haven (https://polyhaven.com/a/dry_decay_leaves), CC0
- excavated_soil_wall: Poly Haven (https://polyhaven.com/a/excavated_soil_wall), CC0
- mud_cracked_dry_03: Poly Haven (https://polyhaven.com/a/mud_cracked_dry_03), CC0
- red_dirt_mud_01: Poly Haven (https://polyhaven.com/a/red_dirt_mud_01), CC0
- stony_dirt_path: Poly Haven (https://polyhaven.com/a/stony_dirt_path), CC0
- dry_ground_rocks: Poly Haven (https://polyhaven.com/a/dry_ground_rocks), CC0
- grassy_cobblestone: Poly Haven (https://polyhaven.com/a/grassy_cobblestone), CC0
- gray_rocks: Poly Haven (https://polyhaven.com/a/gray_rocks), CC0
- leaves_forest_ground: Poly Haven (https://polyhaven.com/a/leaves_forest_ground), CC0
- forest_ground_06: Poly Haven (https://polyhaven.com/a/forest_ground_06), CC0

## Poly Haven models (CC0)

Fetched by `tools/assets/polyhaven.py` to `public/assets/env/polyhaven/<id>`. The game loads the simplified copies in `godot/art/world/<id>.glb`, made by `tools/assets/game_ready.py`.

- "Rock Moss Set 01" by Kless Gyzen, Poly Haven (https://polyhaven.com/a/rock_moss_set_01), CC0 -> godot/art/world/rock_moss_set_01.glb
- "Rock Moss Set 02" by Kless Gyzen, Poly Haven (https://polyhaven.com/a/rock_moss_set_02), CC0 -> godot/art/world/rock_moss_set_02.glb
- "Boulder 01" by Rico Cilliers, Poly Haven (https://polyhaven.com/a/boulder_01), CC0 -> godot/art/world/boulder_01.glb
- "Rock 07" by Jenelle van Heerden, Poly Haven (https://polyhaven.com/a/rock_07), CC0 -> godot/art/world/rock_07.glb
- "Rock 09" by Jenelle van Heerden, Poly Haven (https://polyhaven.com/a/rock_09), CC0 -> godot/art/world/rock_09.glb
- "Stone 01" by Dario Barresi, Rico Cilliers, Poly Haven (https://polyhaven.com/a/stone_01), CC0 -> godot/art/world/stone_01.glb
- "Namaqualand Stones 01" by Greg Zaal, Jenelle van Heerden, Poly Haven (https://polyhaven.com/a/namaqualand_stones_01), CC0 -> godot/art/world/namaqualand_stones_01.glb
- "Root Cluster 01" by Jenelle van Heerden, Rico Cilliers, Poly Haven (https://polyhaven.com/a/root_cluster_01), CC0 -> godot/art/world/root_cluster_01.glb
- "Root Cluster 02" by Jenelle van Heerden, Poly Haven (https://polyhaven.com/a/root_cluster_02), CC0 -> godot/art/world/root_cluster_02.glb
- "Single Root" by Jenelle van Heerden, Poly Haven (https://polyhaven.com/a/single_root), CC0 -> godot/art/world/single_root.glb
- "Pine Roots" by Rob Tuytel, Poly Haven (https://polyhaven.com/a/pine_roots), CC0 -> godot/art/world/pine_roots.glb
- "Tree Stump 01" by Rob Tuytel, Poly Haven (https://polyhaven.com/a/tree_stump_01), CC0 -> godot/art/world/tree_stump_01.glb
- "Tree Stump 02" by Rob Tuytel, Poly Haven (https://polyhaven.com/a/tree_stump_02), CC0 -> godot/art/world/tree_stump_02.glb
- "Dead Tree Trunk" by Rob Tuytel, Poly Haven (https://polyhaven.com/a/dead_tree_trunk), CC0 -> godot/art/world/dead_tree_trunk.glb
- "Dead Tree Trunk 02" by Jenelle van Heerden, Rico Cilliers, Poly Haven (https://polyhaven.com/a/dead_tree_trunk_02), CC0 -> godot/art/world/dead_tree_trunk_02.glb
- "Dry Branches Medium 01" by Rico Cilliers, Poly Haven (https://polyhaven.com/a/dry_branches_medium_01), CC0 -> godot/art/world/dry_branches_medium_01.glb
- "Bark Debris 01" by Greg Zaal, Jenelle van Heerden, Poly Haven (https://polyhaven.com/a/bark_debris_01), CC0 -> godot/art/world/bark_debris_01.glb
- "Moss 01" by Rob Tuytel, Poly Haven (https://polyhaven.com/a/moss_01), CC0 -> godot/art/world/moss_01.glb
- "Fern 02" by Rob Tuytel, Rico Cilliers, Poly Haven (https://polyhaven.com/a/fern_02), CC0 -> godot/art/world/fern_02.glb
- "Nettle Plant" by Rob Tuytel, Rico Cilliers, Poly Haven (https://polyhaven.com/a/nettle_plant), CC0 -> godot/art/world/nettle_plant.glb
- "Weed Plant 02" by Rob Tuytel, Rico Cilliers, Poly Haven (https://polyhaven.com/a/weed_plant_02), CC0 -> godot/art/world/weed_plant_02.glb
- "Shrub 01" by Rico Cilliers, Poly Haven (https://polyhaven.com/a/shrub_01), CC0 -> godot/art/world/shrub_01.glb
- "Shrub 02" by Rico Cilliers, Poly Haven (https://polyhaven.com/a/shrub_02), CC0 -> godot/art/world/shrub_02.glb
- "Shrub 03" by Rico Cilliers, Poly Haven (https://polyhaven.com/a/shrub_03), CC0 -> godot/art/world/shrub_03.glb
- "Shrub 04" by Rico Cilliers, Poly Haven (https://polyhaven.com/a/shrub_04), CC0 -> godot/art/world/shrub_04.glb
- "Grass Medium 01" by Rob Tuytel, Rico Cilliers, Poly Haven (https://polyhaven.com/a/grass_medium_01), CC0 -> godot/art/world/grass_medium_01.glb
- "Grass Medium 02" by Rico Cilliers, Poly Haven (https://polyhaven.com/a/grass_medium_02), CC0 -> godot/art/world/grass_medium_02.glb
- "Stone Fire Pit" by Sebastian Platen, Poly Haven (https://polyhaven.com/a/stone_fire_pit), CC0 -> godot/art/world/stone_fire_pit.glb
- "Gothic Statue" by Benny Weimer, Poly Haven (https://polyhaven.com/a/gothic_statue), CC0 -> godot/art/world/gothic_statue.glb
- "Kite Shield" by Ulan Cabanilla, Poly Haven (https://polyhaven.com/a/kite_shield), CC0 -> godot/art/world/kite_shield.glb
- "Wooden Lantern 01" by James Ray Cock, Poly Haven (https://polyhaven.com/a/wooden_lantern_01), CC0 -> godot/art/world/wooden_lantern_01.glb
- "Old Military Crate" by Jack Mava, Poly Haven (https://polyhaven.com/a/old_military_crate), CC0 -> godot/art/world/old_military_crate.glb
- "Wooden Barrels 01" by James Ray Cock, Poly Haven (https://polyhaven.com/a/wooden_barrels_01), CC0 -> godot/art/world/wooden_barrels_01.glb

## ambientCG (CC0)

Outfit leathers and metals (`godot/art/outfit`, `godot/art/people/outfit_tex`; fetched by `tools/assets/ambientcg.py`). Created using these materials from ambientCG.com, licensed under the Creative Commons CC0 1.0 Universal License.

- Metal038: ambientCG (https://ambientcg.com/view?id=Metal038), CC0
- Metal048C: ambientCG (https://ambientcg.com/view?id=Metal048C), CC0
- Metal046B: ambientCG (https://ambientcg.com/view?id=Metal046B), CC0
- Metal053C: ambientCG (https://ambientcg.com/view?id=Metal053C), CC0
- Leather037: ambientCG (https://ambientcg.com/view?id=Leather037), CC0
- Leather034C: ambientCG (https://ambientcg.com/view?id=Leather034C), CC0
- Leather024: ambientCG (https://ambientcg.com/view?id=Leather024), CC0
- Leather014: ambientCG (https://ambientcg.com/view?id=Leather014), CC0
- Leather026: ambientCG (https://ambientcg.com/view?id=Leather026), CC0
- Leather021: ambientCG (https://ambientcg.com/view?id=Leather021), CC0

## Made with AI tools (disclosure)

Parts of the game were made with generative AI during development. Some images, 3D models, effects, sounds, motion and text in it were generated by AI, then reviewed and edited by the developer. Nothing is generated by AI while you play. Each tool's licence is listed in `docs/legal/ASSET_PROVENANCE.md`; what this list names (only what the release ships), and when a line joins it, is in `docs/legal/STEAM_CHECKLIST.md` section E.

- **Images:** most of the interface's painted art and icons, the ground marks of blows and spells, the heroine's face paint and irises, and the picture her body was sculpted from were made with Krea 2 (Krea 2 Community License); the interface's with Krea's darkbrush LoRA. Cut-outs used BiRefNet (MIT).
- **3D:** the heroine's base body was sculpted by TRELLIS 2 (Microsoft, MIT) with DINOv3 (Meta), then rebuilt and rigged for the game.
- **Effects video and some combat sounds** were made with LTX 2.5 (Lightricks, LTX-2.x Community License), with Gemma 4 as its text encoder (Apache-2.0). This content is machine generated.
- **Motion:** NVIDIA Kimodo (above).
- **Code and writing** were written with Claude (Anthropic) under the owner's direction.

## Made for the game

- The interface's art: frames, cards, slots, bars, medallions, ornaments, the logo, cursors, pad buttons, map marks and every icon.
  - Forged in code and modelled in Blender by `tools/uiforge`.
  - Most of it was then painted over on the local ComfyUI (Krea 2 turbo with the darkbrush LoRA; see above).
  - The item icons paint over the game's own photographs of its item models.
- The heroine's hair, outfits and face-paint designs, the skin's pores, the town well, the glyphs, the app icon, the shaders, the synthesised sounds and music, and every keyed animation.
- The heroine's body comes from a figure given to the game by its owner (provenance under review: `docs/legal/ASSET_PROVENANCE.md`, PE-06). It was rigged with AccuRIG and laid on the Quaternius skeleton by `tools/assets/build_heroine.py`.

## The web game only (not in the Godot build)

- `basis_transcoder.js` / `.wasm`, from three.js's examples (Binomial LLC), Apache License 2.0 -> `public/assets/basis`, for the KTX2 textures.
- The npm packages in `package.json`: three (MIT), postprocessing (Zlib), n8ao (CC0), preact and @preact/signals (MIT), meshoptimizer (MIT), @fontsource (the same OFL fonts), and Electron (MIT, with Chromium's notices) for the desktop wrapper.
