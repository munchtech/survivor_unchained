# Credits

Third-party art in this folder, with its licence. CC-BY works are used with credit as below.

## Quaternius (CC0)

- Universal Base Characters, Modular Character Outfits - Fantasy, Universal Animation Library and Universal Animation Library 2, by Quaternius (https://quaternius.com), CC0 -> public/assets/people (gathered by tools/assets/people.py)
- Medieval Village MegaKit, Fantasy Props MegaKit and Stylized Nature MegaKit, by Quaternius (https://quaternius.com), CC0 -> public/assets/env/{village,props,nature} (gathered by tools/assets/env.py)


## The heroine's movement

- Her own clips (godot/art/anim/heroine.res) are keyed for the game in code by tools/anim (own work), except her idles' standing: 100STYLE dataset, Ian Mason, Sebastian Starke, Taku Komura (https://zenodo.org/record/8127870, "Real-Time Style Modelling of Human Locomotion via Feature-Wise Transformations and Local Motion Phases", 2022), CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Changes: retargeted to her skeleton, feet locked, looped, centred, and the arms re-keyed to hold her weapons. Which take each clip uses is in tools/anim/manifest.json.
- Anything she has not had made for her yet plays from Quaternius's Universal Animation Libraries (CC0, above).
- Her Crashing Leap is Mixamo's "Standing Melee Run Jump Attack" (Adobe Mixamo, used in the game under Mixamo's terms; retargeted to her and retimed; the raw files are not distributed).
- The townsfolk's walk (women's), standing idle, talk (men's), sitting on a chair and on the floor, and picking up are Mixamo motion (a feminine walk, a weight-shift idle, "General Conversation", "Sitting Looking Side To Side", sitting on the floor, picking up; Adobe Mixamo, used under Mixamo's terms; retargeted to the kit's bodies; raw files not distributed).
- The townsfolk's walk (men's), talk (women's), arms crossed, cheer, wave and work at a table are generated with NVIDIA's Kimodo (Kimodo-SOMA-RP, NVIDIA Open Model License; tools/anim/kimodo_gen.py). Each folk clip's source is in godot/art/anim/folk_clips.json.
- Motion captured from video with Meta's SAM 3D Body (SAM License; Momentum Human Rig, Apache 2.0) is credited clip by clip in tools/anim/manifest.json when it ships.

## Poly Haven (CC0)

- "sparse_grass" (the ground's grass), Poly Haven (https://polyhaven.com/a/sparse_grass), CC0 -> public/assets/ground (gathered by tools/assets/ground.py)
- "forest_leaves_02" (the ground's leaves), Poly Haven (https://polyhaven.com/a/forest_leaves_02), CC0 -> public/assets/ground (gathered by tools/assets/ground.py)
- "forest_ground_04" (the ground's dirt), Poly Haven (https://polyhaven.com/a/forest_ground_04), CC0 -> public/assets/ground (gathered by tools/assets/ground.py)
- "mud_forest" (the ground's mud), Poly Haven (https://polyhaven.com/a/mud_forest), CC0 -> public/assets/ground (gathered by tools/assets/ground.py)
- "cobblestone_05" (the ground's stone), Poly Haven (https://polyhaven.com/a/cobblestone_05), CC0 -> public/assets/ground (gathered by tools/assets/ground.py)
- "mossy_rock" (the ground's rock), Poly Haven (https://polyhaven.com/a/mossy_rock), CC0 -> public/assets/ground (gathered by tools/assets/ground.py)
- "burned_ground_01" (the ground's blight), Poly Haven (https://polyhaven.com/a/burned_ground_01), CC0 -> public/assets/ground (gathered by tools/assets/ground.py)
- "studio_small_08" (the light the items are photographed in), Poly Haven (https://polyhaven.com/a/studio_small_08), CC0 -> godot/art/studio (1k HDR)
- "medieval_blocks_03" (dressed stone: walls, the gate, towers, the crypt, pillars), Poly Haven (https://polyhaven.com/a/medieval_blocks_03), CC0 -> godot/art/materials (1k)
- "castle_wall_slates" (slate roofs, clay tiles), Poly Haven (https://polyhaven.com/a/castle_wall_slates), CC0 -> godot/art/materials (1k)
- "rock_boulder_dry" (headstones, rock), Poly Haven (https://polyhaven.com/a/rock_boulder_dry), CC0 -> godot/art/materials (1k)
- "rough_wood" (posts, crosses, timber), Poly Haven (https://polyhaven.com/a/rough_wood), CC0 -> godot/art/materials (1k)
- godot/art/materials/forest_ground_04 is the ground's dirt layer above, cut out of the atlas for graves

## Kenney (CC0)

- Particle Pack, by Kenney (https://kenney.nl/assets/particle-pack), CC0 -> godot/art/fx (the effects' sprites: smoke, sparks, flames, magic, slashes; packed into a texture array)
- Impact Sounds, RPG Audio and Interface Sounds, by Kenney (https://kenney.nl/assets/impact-sounds, /rpg-audio, /interface-sounds), CC0 -> godot/art/sound (as mono 16-bit WAV)

## OpenGameArt field recordings (CC0)

Cut to loop and made mono at 24 kHz (the game plays each wide, its right side half the take along), in godot/art/sound:

- "Park ambiences" by thimras (https://opengameart.org/content/park-ambiences), CC0 -> bed_birds_0.wav (birdsong by a copse, traffic under it filtered out) and bed_water_0.wav (a small river over a low step)
- "Fireplace Sound loop" by PagDev (https://opengameart.org/content/fireplace-sound-loop), CC0 -> bed_fire_0.wav
- "Crickets Ambient Noise - loopable" by Ted Kerr (wolfgang) (https://opengameart.org/content/crickets-ambient-noise-loopable), CC0 -> bed_crickets_0.wav
- "Blacksmith's Hammer" by vishwajai (https://opengameart.org/content/blacksmiths-hammer), CC0 -> anvil_0.wav

## Basis Universal (Apache-2.0)

- basis_transcoder.js / .wasm, from three.js's examples (Binomial LLC, Apache License 2.0) -> public/assets/basis, for the KTX2 textures

## Sketchfab

- "Chevalier Sword" by rubenve (https://sketchfab.com/rubenve), CC Attribution: https://sketchfab.com/3d-models/chevalier-sword-b2662f2666a844e8a1bd0e7c4a7672d8 -> public/assets/weapons/chevalier_sword.glb
- "Viking Sword (Game Model)" by Michael Makivic (https://sketchfab.com/makivic), CC Attribution: https://sketchfab.com/3d-models/viking-sword-game-model-a05d0bd73e9e4508b873ffd7b6a6238d -> public/assets/weapons/viking_sword.glb
- "medieval sword" by LowSeb (https://sketchfab.com/lowseb), CC Attribution: https://sketchfab.com/3d-models/medieval-sword-da574cba504e4b83a3293f3d3bd067fb -> public/assets/weapons/longsword.glb
- "Zweihander" by Siesta (https://sketchfab.com/siesta), CC Attribution: https://sketchfab.com/3d-models/zweihander-bde0f0351bf443f6bed68aeff84b4129 -> public/assets/weapons/zweihander.glb
- "Medieval Mace" by Kama Modeling (https://sketchfab.com/KamaModeling), CC Attribution: https://sketchfab.com/3d-models/medieval-mace-83217215a0c541b2956a8e87a4ae62fe -> public/assets/weapons/mace.glb
- "Viking battle axe" by Mikhail Antonov (https://sketchfab.com/xeofox), CC Attribution: https://sketchfab.com/3d-models/viking-battle-axe-b7123192adbf40f68043c57dd8ddcd15 -> public/assets/weapons/viking_axe.glb
- "Snake Axe" by Ashley Jay Thornton (https://sketchfab.com/AshleyJay), CC Attribution: https://sketchfab.com/3d-models/snake-axe-ace485ac031c4ee0a918e99d2b80560b -> public/assets/weapons/snake_axe.glb
- "Mage Staff" by RMBehan (https://sketchfab.com/RMBehan), CC Attribution: https://sketchfab.com/3d-models/mage-staff-a172d06792734bbc9b11272b4f497c2c -> public/assets/weapons/mage_staff.glb
- "Medieval Crossbow" by iedalton (https://sketchfab.com/iedalton), CC Attribution: https://sketchfab.com/3d-models/medieval-crossbow-cc36ed347db340d59bd2ec7b06ae0d63 -> public/assets/weapons/crossbow.glb
- "Medieval Shield" by Artem Mykhailov (https://sketchfab.com/CGArtem), CC Attribution: https://sketchfab.com/3d-models/medieval-shield-b98b8f64d935415aab0fe9b70074511f -> public/assets/weapons/shield_round.glb
- "Silver Bladed weapons - Fantasy weapon set" by Peter Nox (https://sketchfab.com/Peter.Nox), CC Attribution: https://sketchfab.com/3d-models/silver-bladed-weapons-fantasy-weapon-set-d5189211a1d348b0a9d7ddc052a22989 -> public/assets/weapons/daggers.glb
- "Animated Wolf Scene" by Roo (https://sketchfab.com/roo3d), CC Attribution: https://sketchfab.com/3d-models/animated-wolf-scene-5d55506494e5460eaadf04370e07cd5c -> godot/art/beasts/wolf.glb
- "Animated Realistic Boar – 3D Animal Model" by AnimalMesh 3D (https://sketchfab.com/AnimalMesh3D), CC Attribution: https://sketchfab.com/3d-models/animated-realistic-boar-3d-animal-model-f672a7fd93e84997b80a54ba30956111 -> godot/art/beasts/boar.glb
- "Goblin Ghoul" by Rodrigo Bento (https://sketchfab.com/rodrigobento), CC Attribution: https://sketchfab.com/3d-models/goblin-ghoul-a6c6fffee3d34823b6d87a7054782577 -> godot/art/beasts/lampling.glb (the lamplings; hats, lamps and satchels made in code)
- "Genshin Style Anime Female Base Mesh For Blender" by donizaki (https://sketchfab.com/donizaki), CC Attribution: https://sketchfab.com/3d-models/genshin-style-anime-female-base-mesh-for-blender-c2d6727e8c9742feb9a4a3bccac6e0e0 -> godot/art/people/anime_female.glb (a woman's body, and the skeleton the woman survivor's is fitted from; rigged to the Quaternius skeleton, arms raised to its T and hands refitted by tools/assets/anime_female.py; the Quaternius hairstyles refitted to her head by tools/assets/anime_hair.py -> godot/art/people/her_Hair_*.glb)

## Made for the game

- The interface's art (frames, cards, slots, bars, medallions, ornaments, the logo, cursors, pad buttons, map marks and every icon): made for the game by tools/uiforge, from Blender renders (blender_frames.py, blender_chain.py), forged height fields and the local ComfyUI (Krea 2 turbo with the darkbrush LoRA, BiRefNet cut-outs); item icons painted over the game's own photographs of its item models -> godot/art/ui. No third-party images; the fonts are the game's own (SIL OFL, godot/art/fonts)
- The woman survivor's body: a figure made in ComfyUI and given to the game by its owner -> godot/art/people/woman.glb (rigged to the Quaternius skeleton, brought down to a game's weight and its paint baked from the full figure by tools/assets/woman_body.py, with a mask of her skin, hair and suit, godot/art/people/woman_mask.png)

## Poly Haven models (CC0)

- "Rock Moss Set 01" by Kless Gyzen, Poly Haven (https://polyhaven.com/a/rock_moss_set_01), CC0 -> public/assets/env/polyhaven/rock_moss_set_01
- "Rock Moss Set 02" by Kless Gyzen, Poly Haven (https://polyhaven.com/a/rock_moss_set_02), CC0 -> public/assets/env/polyhaven/rock_moss_set_02
- "Boulder 01" by Rico Cilliers, Poly Haven (https://polyhaven.com/a/boulder_01), CC0 -> public/assets/env/polyhaven/boulder_01
- "Rock 07" by Jenelle van Heerden, Poly Haven (https://polyhaven.com/a/rock_07), CC0 -> public/assets/env/polyhaven/rock_07
- "Rock 09" by Jenelle van Heerden, Poly Haven (https://polyhaven.com/a/rock_09), CC0 -> public/assets/env/polyhaven/rock_09
- "Stone 01" by Dario Barresi, Rico Cilliers, Poly Haven (https://polyhaven.com/a/stone_01), CC0 -> public/assets/env/polyhaven/stone_01
- "Namaqualand Stones 01" by Greg Zaal, Jenelle van Heerden, Poly Haven (https://polyhaven.com/a/namaqualand_stones_01), CC0 -> public/assets/env/polyhaven/namaqualand_stones_01
- "Root Cluster 01" by Jenelle van Heerden, Rico Cilliers, Poly Haven (https://polyhaven.com/a/root_cluster_01), CC0 -> public/assets/env/polyhaven/root_cluster_01
- "Root Cluster 02" by Jenelle van Heerden, Poly Haven (https://polyhaven.com/a/root_cluster_02), CC0 -> public/assets/env/polyhaven/root_cluster_02
- "Single Root" by Jenelle van Heerden, Poly Haven (https://polyhaven.com/a/single_root), CC0 -> public/assets/env/polyhaven/single_root
- "Pine Roots" by Rob Tuytel, Poly Haven (https://polyhaven.com/a/pine_roots), CC0 -> public/assets/env/polyhaven/pine_roots
- "Tree Stump 01" by Rob Tuytel, Poly Haven (https://polyhaven.com/a/tree_stump_01), CC0 -> public/assets/env/polyhaven/tree_stump_01
- "Tree Stump 02" by Rob Tuytel, Poly Haven (https://polyhaven.com/a/tree_stump_02), CC0 -> public/assets/env/polyhaven/tree_stump_02
- "Dead Tree Trunk" by Rob Tuytel, Poly Haven (https://polyhaven.com/a/dead_tree_trunk), CC0 -> public/assets/env/polyhaven/dead_tree_trunk
- "Dead Tree Trunk 02" by Jenelle van Heerden, Rico Cilliers, Poly Haven (https://polyhaven.com/a/dead_tree_trunk_02), CC0 -> public/assets/env/polyhaven/dead_tree_trunk_02
- "Dry Branches Medium 01" by Rico Cilliers, Poly Haven (https://polyhaven.com/a/dry_branches_medium_01), CC0 -> public/assets/env/polyhaven/dry_branches_medium_01
- "Bark Debris 01" by Greg Zaal, Jenelle van Heerden, Poly Haven (https://polyhaven.com/a/bark_debris_01), CC0 -> public/assets/env/polyhaven/bark_debris_01
- "Moss 01" by Rob Tuytel, Poly Haven (https://polyhaven.com/a/moss_01), CC0 -> public/assets/env/polyhaven/moss_01
- "Fern 02" by Rob Tuytel, Rico Cilliers, Poly Haven (https://polyhaven.com/a/fern_02), CC0 -> public/assets/env/polyhaven/fern_02
- "Nettle Plant" by Rob Tuytel, Rico Cilliers, Poly Haven (https://polyhaven.com/a/nettle_plant), CC0 -> public/assets/env/polyhaven/nettle_plant
- "Weed Plant 02" by Rob Tuytel, Rico Cilliers, Poly Haven (https://polyhaven.com/a/weed_plant_02), CC0 -> public/assets/env/polyhaven/weed_plant_02
- "Shrub 01" by Rico Cilliers, Poly Haven (https://polyhaven.com/a/shrub_01), CC0 -> public/assets/env/polyhaven/shrub_01
- "Shrub 02" by Rico Cilliers, Poly Haven (https://polyhaven.com/a/shrub_02), CC0 -> public/assets/env/polyhaven/shrub_02
- "Shrub 03" by Rico Cilliers, Poly Haven (https://polyhaven.com/a/shrub_03), CC0 -> public/assets/env/polyhaven/shrub_03
- "Shrub 04" by Rico Cilliers, Poly Haven (https://polyhaven.com/a/shrub_04), CC0 -> public/assets/env/polyhaven/shrub_04
- "Grass Medium 01" by Rob Tuytel, Rico Cilliers, Poly Haven (https://polyhaven.com/a/grass_medium_01), CC0 -> public/assets/env/polyhaven/grass_medium_01
- "Grass Medium 02" by Rico Cilliers, Poly Haven (https://polyhaven.com/a/grass_medium_02), CC0 -> public/assets/env/polyhaven/grass_medium_02
- "Stone Fire Pit" by Sebastian Platen, Poly Haven (https://polyhaven.com/a/stone_fire_pit), CC0 -> public/assets/env/polyhaven/stone_fire_pit
- "Gothic Statue" by Benny Weimer, Poly Haven (https://polyhaven.com/a/gothic_statue), CC0 -> public/assets/env/polyhaven/gothic_statue
- "Kite Shield" by Ulan Cabanilla, Poly Haven (https://polyhaven.com/a/kite_shield), CC0 -> public/assets/env/polyhaven/kite_shield
- "Wooden Lantern 01" by James Ray Cock, Poly Haven (https://polyhaven.com/a/wooden_lantern_01), CC0 -> public/assets/env/polyhaven/wooden_lantern_01
- "Old Military Crate" by Jack Mava, Poly Haven (https://polyhaven.com/a/old_military_crate), CC0 -> public/assets/env/polyhaven/old_military_crate
- "Wooden Barrels 01" by James Ray Cock, Poly Haven (https://polyhaven.com/a/wooden_barrels_01), CC0 -> public/assets/env/polyhaven/wooden_barrels_01
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
- "Curly Teddy Natural" texture, Poly Haven (https://polyhaven.com/a/curly_teddy_natural), CC0 -> godot/art/outfit
- Her head, eyes, brows, lashes, teeth, tongue and hairstyles (long01, ponytail01, braid01, bob02, short03): MakeHuman system assets (http://www.makehumancommunity.org), made with MPFB, CC0 -> godot/art/people/heroine*.glb/gltf, godot/art/people/head_tex
- Her head's skin, "Light skin female ginger" by MargaretToigo, MakeHuman community assets, CC0 -> godot/art/people/head_tex/heroine_head.jpg
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
