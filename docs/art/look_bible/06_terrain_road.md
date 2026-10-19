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
| Kingdom Come II ([Steam](https://store.steampowered.com/app/1771300), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1771300/ss_293abf266a1847da65bb633b9e76e851715a4b58.1920x1080.jpg)) | The forest road as a made thing. Wheel ruts, a grass strip down the middle, soft verges, a fence. |
| The Witcher 3 ([Steam](https://store.steampowered.com/app/292030), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/292030/ss_f62c314f6695b6e2b4dc2e0c94101482c9edf6ac.1920x1080.jpg)) | A track through a wheat field. The color breaks up at every distance, and no tile shows. |

## What ours ISN'T (our frames, 18 Oct audit, 1:1)

| Frame | What fails |
|---|---|
| `frames/c01_s0.jpg` (C01 s0) | Flat dark grass with hard-edged splat blobs. The black slashes read as holes in the ground. |
| `frames/c04b_sb5.jpg` (C04 B sb5) | The cobbles repeat in an obvious grid from above. |
| `frames/c04a_sa8.jpg` (C04 A sa8) | Grass planted in rows across the road, and a low-poly boulder. |

## The trick

1. Height-blended splat: every ground material has a height map, and the blend favors the higher one. Stones push through dirt, and soft blobs become crisp, natural edges.
2. Anti-tiling on every ground material: hex tiling (Mikkelsen) or random tile offsets (Quilez), plus a macro color texture at about 1/30 scale.
3. Decals and scatter for the smallest scale: ruts, puddles, leaf drifts, twigs and pebbles (MultiMesh), gathered where feet and wheels go.
4. The road as its own strip along the path spline: a worn center, ruts, and a verge that blends into the grass. The grass mask is cleared from it.
5. Frost and wetness as layers driven by slope and height (frost on the tops, wet in the hollows), never a white ground.

## DONE means (at the play and close-up cameras, at 1:1)

- No repeating pattern shows inside one play-camera frame.
- Material edges look natural (height-blended), with no blob outlines and no black slashes.
- Roads read as worn (ruts, verges), with no grass on them.
- Three scales of detail from the play camera: macro color, the material, then decals and scatter.
- Cost: one shared terrain shader, and the scatter is instanced (page 2).

Owners: The tutorial environment lead (the terrain shader, road strips, decals and scatter).

## Sources
- Anti-tiling: "to assign a random offset and orientation to each tile of the repetition" ([Quilez, texture repetition](https://iquilezles.org/articles/texturerepetition/)); hex tiling, "an adaptation of the by-example noise algorithm of Heitz and Neyret" ([Mikkelsen, JCGT 2022](https://jcgt.org/published/0011/03/05/paper.pdf)).
- Terrain at scale: Far Cry 5's GPU terrain pipeline (Moore, [GDC 2018](https://gdcvault.com/play/1025261/Terrain-Rendering-in-Far-Cry)).
- The full list, with verified quotes, is in `look_bible_refs\tricks_sources.md` (outside the repo).
