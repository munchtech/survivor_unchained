# 1e. Foliage

The board: `C:\Users\munch\Desktop\survivorsunchained_inputs\look_bible_refs\boards\05_foliage.jpg`. It sits outside the repo because its top rows are other games' screenshots, kept for reference only and never shipped.

**The look in one line:** trees as volumes, not cut-outs. A small kit of our own species, lit through by the low sun and the fire, varied per instance, moving in the wind, with undergrowth tying every trunk to the ground.

Tier 2. Grass and trees fill most of every road and forest frame, and grass is already the biggest primitive cost in the perf run, so the kit is built to a budget (page 2).

## What it IS (references; what each teaches)

| Reference | What it teaches |
|---|---|
| Titan Quest II, play camera ([Steam](https://store.steampowered.com/app/1154030), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1154030/ss_5abcf6cb8f6b168484898cbefa159a0018b63d28.1920x1080.jpg)) | A dark wood with varied crowns, undergrowth that hides every trunk's base, and mist between the trees. |
| Titan Quest II ([Steam](https://store.steampowered.com/app/1154030), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1154030/ss_3ef8aed42ee7bd8623835611832c21d48219db08.1920x1080.jpg)) | Bushes and grass grow in clumps along the road. The road stays clear, and the verge is a soft edge. |
| No Rest for the Wicked, play camera, a dark wood ([Steam](https://store.steampowered.com/app/1371980), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1371980/ss_56066f44f29e8b042c482e0b0680bc101bf1ecd5.1920x1080.jpg)) | Bushes and crowns read as volumes, lit on top and dark beneath, with back-lit leaves along the path. Stylized, and it still reads as a real wood. |
| Kingdom Come II ([Steam](https://store.steampowered.com/app/1771300), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1771300/ss_27e006df1aef43380ae7db0d0b08538b26b49daa.1920x1080.jpg)) | Depth through air. Each layer of trees is paler and bluer, with sun shafts through the mist and ferns in front. |
| SpellForce 3, high camera ([Steam](https://store.steampowered.com/app/311290), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/311290/ss_5063cd683cdc4ea046b4c928b7b8d62d6ed9e8ef.1920x1080.jpg)) | Spruces from above read as stacked whorls, lit tips over dark gaps, each with its shadow on the ground. Never a flat star. |

## What ours ISN'T (our frames, 18 Oct audit, 1:1)

| Frame | What fails |
|---|---|
| `frames/play_20.jpg` (the road through the wood at the play camera) | Flat dark-green pine shapes with no lit side and no undergrowth. |
| `frames/c01_s7.jpg` (C01 s7) | Paper-cut pines under flat blue light. It reads as a low-poly asset pack. |
| `frames/c04a_sa2.jpg` (C04 A sa2) | Cartoon pines with peg-like branches, where the note asks for birches. |

## The trick

1. A small kit of our own: three species for the Prologue (pine, birch, alder) in three sizes, plus ferns, bushes and grass clumps, built in the Asset Forge with card canopies.
2. Crown volume: broadleaf cards get normals bent out from the crown's center. Pines get stacked whorls of branch cards, normals taken from the trunk axis tilted up, and AO baked into vertex color (dark inside and under each whorl, lit tips).
3. Back light (translucency) on leaves and grass, so the low sun and the fire glow through them.
4. A hue and value jitter per instance, so no two neighbors match. Wind from vertex colors: trunk sway, branch bend, leaf flutter (Crysis).
5. Undergrowth hides every trunk's base. Grass grows in clumps from a noise mask, never in rows and never on the road. In the distance, LODs and then impostors. Grass takes the terrain's color at its root.
6. Grass clumps are MultiMesh cards with a visibility-range fade and cast no shadows (SSAO and a darker root color ground them). Trees cast shadows through a low shadow-only LOD.

## DONE means (at the play and close-up cameras, at 1:1)

- From the play camera, crowns read as volumes, never as flat cut-outs: on a crown the lit side is at least one stop over the shadow side (sRGB luma ratio at least 1.35).
- No two identical trees stand side by side in a frame, and every trunk has undergrowth at its base.
- Grass grows in clumps and never on the road. Everything moves in the wind.
- Birches where the shot notes say birches (C04 A sa2).
- Cost: at the Low Ford play camera at 1440p with the new kit in, primitives at or below 4.9M and shadow draws at or below 2,246.

Owners: The tutorial environment lead (the kit, built with the Asset Forge, and the scatter rules); rendering (wind and back light in the foliage shader, LODs and impostors).

## Sources
- GPU grass: "generating individual blades of grass on the GPU that could each have their own procedural appearance and animation" (Wohllaib, [Procedural Grass in Ghost of Tsushima, GDC 2021](https://gdcvault.com/play/1027214/Advanced-Graphics-Summit-Procedural-Grass)).
- Wind from painted vertex color: "This color gives us extra information about the detail bending" ([GPU Gems 3, ch. 16, Vegetation in Crysis](https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-16-vegetation-procedural-animation-and-shading-crysis)).
- Horizon Zero Dawn's vegetation talk (Sanders, [GDC 2018](https://gdcvault.com/play/1025066/Between-Tech-and-Art-The)) and octahedral impostors ([Brucks](https://www.shaderbits.com/blog/octahedral-impostors)) for the far distance.
- The full list, with verified quotes, is in `look_bible_refs\tricks_sources.md` (outside the repo).
