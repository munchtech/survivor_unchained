# 1f. Terrain and road

The board: `C:\Users\munch\Desktop\survivorsunchained_inputs\look_bible_refs\boards\06_terrain_road.jpg`. It sits outside the repo because its top rows are other games' screenshots, kept for reference only and never shipped.

**The look in one line:** ground with three scales of detail and no visible tile: height-blended materials, roads worn into it, and frost or wet as layers on top.

Tier 2. From the play camera the ground is most of the screen, all the time.

## What it IS (references; what each teaches)

| Reference | What it teaches |
|---|---|
| Diablo IV, play camera ([Steam](https://store.steampowered.com/app/2344520), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2344520/ss_f6bf337468fdf3963cb249fc2d3c58a81eafd2a5.1920x1080.jpg)) | Three scales of detail. Broad color shifts, then blended dirt and stone, then roots, ruts and debris on top. Nothing repeats. |
| Path of Exile 2 ([Steam](https://store.steampowered.com/app/2694490), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2694490/ss_578654a7e1e88e6e186ffe1d3c055e9c1ceb0300.1920x1080.jpg)) | The ground under a wood. Dirt, litter, roots and bones run into each other, with no hard edge between materials. |
| Titan Quest II, play camera ([Steam](https://store.steampowered.com/app/1154030), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1154030/ss_41c07a1fb922b6ddab5febf5aa8fcbcbadc0be24.1920x1080.jpg)) | A worn path with grass clumps along its edges, low stone walls and bushes. Every transition is soft. |
| Diablo IV, play camera ([Steam](https://store.steampowered.com/app/2344520), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2344520/ss_14880a1527241507d9a2d26f439f83fac20c4246.1920x1080.jpg)) | The ground isn't flat. Ledges and outcrops rise out of it with no seam, and their shadows give scale. |
| Kingdom Come II ([Steam](https://store.steampowered.com/app/1771300), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1771300/ss_293abf266a1847da65bb633b9e76e851715a4b58.1920x1080.jpg)) | The forest road as a made thing. Wheel ruts, a grass strip down the middle, soft verges, a fence. |
| Farthest Frontier, high camera ([Steam](https://store.steampowered.com/app/1044720), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1044720/ss_fdd54849ddce1d2d26ba0ae6cff518cacb9889df.1920x1080.jpg)) | A cobbled street of varied stones with no visible repeat. Dirt and weeds gather at the walls, where feet don't go. |
| Farthest Frontier, high camera ([Steam](https://store.steampowered.com/app/1044720), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1044720/ss_630013acd6eec95b55db558765faf85caeec6472.1920x1080.jpg)) | A thin snow lies on the flats and the roofs, while the paths, grass and litter show through dark. Take the broken layer, not the brightness: at night our frost stays under the lights (1c). |

## What ours ISN'T (our frames, 18 Oct audit, 1:1)

| Frame | What fails |
|---|---|
| `frames/c01_s0.jpg` (C01 s0) | Flat dark grass with hard-edged splat blobs. The black slashes read as holes in the ground. |
| `frames/c04b_sb5.jpg` (C04 B sb5) | The cobbles repeat in an obvious grid from above, and one clean stone covers everything: no dirt, wear, puddles or gutters. |
| `frames/c04a_sa8.jpg` (C04 A sa8) | Tufts spread evenly over road and verge alike, so no road reads, and a low-poly boulder sits on the ground with no blend. |

## The trick

1. Height-blended splat: every ground material has a height map, and the blend favors the higher one. Stones push through dirt, and soft blobs become crisp, natural edges.
2. Anti-tiling on every ground material: hex tiling (Mikkelsen) or random tile offsets (Quilez) on the albedo and normal of the two strongest layers per pixel only, over a macro color and value texture repeating every 30-60 m (base materials tile every 2-4 m). Exception, cobbles and paving: a large tile of varied stones (4 m or more, in two or three variants picked by a world-space mask), dirt, wet and moss masks in world space that follow traffic and gutters, decals for worn and missing stones, and no hex blending.
3. Decals and scatter for the smallest scale: ruts, puddles, leaf drifts, twigs and pebbles (MultiMesh), gathered where feet and wheels go.
4. The road spline writes into the terrain's control and height maps (road material, ruts as shallow dips) and clears the grass mask. A sunk mesh strip with an edge-blend decal is used only for paved roads.
5. Frost and wetness as layers: frost on exposed tops (grass tips, litter, stone tops, taken from the material height maps), none under the canopy or the eaves (a baked sky-exposure mask), and wet and dark in the hollows and ruts. Never a white ground, never a noise-blotch pattern.
6. Rocks, walls, stumps and buildings blend in: their lowest 20-40 cm take the terrain material, with a contact-AO decal and scatter at the base.

## DONE means (at the play and close-up cameras, at 1:1)

- No repeating pattern shows inside one play-camera frame.
- Material edges look natural (height-blended), with no blob outlines and no black slashes.
- Roads read as worn (ruts, verges), with no grass on them.
- Three scales of detail from the play camera: macro color, the material, then decals and scatter.
- No hard line where a rock, wall, building or trunk meets the ground.
- Frost sits on the tops and the litter, the hollows are dark and wet, and frost is never the brightest area at night (1c). Frost follows the shelter and the ground's height, never a blotch mask.
- Cost: at the Low Ford play camera at 1440p, terrain, decals and scatter add at most 1.0 ms GPU over today's ground (or page 2's number). Scatter casts no shadows, and shadow draws stay at or below 2,246.

Owners: The tutorial environment lead (the terrain shader, road strips, decals and scatter).

## Sources
- Anti-tiling: "to assign a random offset and orientation to each tile of the repetition" ([Quilez, texture repetition](https://iquilezles.org/articles/texturerepetition/)); hex tiling, "an adaptation of the by-example noise algorithm of Heitz and Neyret" ([Mikkelsen, JCGT 2022](https://jcgt.org/published/0011/03/05/paper.pdf)).
- Terrain at scale: Far Cry 5's GPU terrain pipeline (Moore, [GDC 2018](https://gdcvault.com/play/1025261/Terrain-Rendering-in-Far-Cry)).
- The full list, with verified quotes, is in `look_bible_refs\tricks_sources.md` (outside the repo).
