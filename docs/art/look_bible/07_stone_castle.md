# 1g. Stone and the castle

The board: `C:\Users\munch\Desktop\survivorsunchained_inputs\look_bible_refs\boards\07_stone_castle.jpg`. It sits outside the repo because its top rows are other games' screenshots, kept for reference only and never shipped.

**The look in one line:** stone that reads as built and weathered: a modular kit with beveled edges and grime rising from the ground, under a silhouette that says castle before any surface detail does.

Tier 2. The castle is seen far off (C01 s8a, across the river at night); stone is seen up close in the town's footings and the ford's stepping stones.

## What it IS (references; what each teaches)

| Reference | What it teaches |
|---|---|
| Titan Quest II, play camera ([Steam](https://store.steampowered.com/app/1154030), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1154030/ss_9cbc6ee69e6d5dc3029855c3c07bafb2cbae2881.1920x1080.jpg)) | Stone blocks with beveled, chipped edges, worn steps and rubble at the base. The joints read from high up. |
| Titan Quest II ([Steam](https://store.steampowered.com/app/1154030), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1154030/ss_4b751330f5032bcb6c5f7943ee2063fa0cd18236.1920x1080.jpg)) | A temple on a cliff. The tops of the stones take the warm light, mist softens what lies behind, and grime gathers at the base. |
| Lies of P ([Steam](https://store.steampowered.com/app/1627720), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1627720/ss_436fc8fb935dbdb2fb3d98e191633264ce5c94ce.1920x1080.jpg)) | A stone city at dusk. Warm windows and braziers punctuate dark masonry, and the silhouettes carry the shot. |
| Elden Ring ([Steam](https://store.steampowered.com/app/1245620), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1245620/ss_ef61b771ee6b269b1f0cb484233e07a0bfb5f81b.1920x1080.jpg)) | The castle as a silhouette. Towers, crenellations and roofs break the skyline, and mist sets the far walls back. |
| No Rest for the Wicked ([Steam](https://store.steampowered.com/app/1371980), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1371980/ss_8533050c266fea833bed9d0567b7185abd87fc33.1920x1080.jpg)) | Stone walls at night lit warm from below, against dark rock and a cold sky. The light on the stone makes the masonry read. |

## What ours ISN'T (our frames, 18 Oct audit, 1:1)

| Frame | What fails |
|---|---|
| `frames/c01_s8a.jpg` (C01 s8a) | A castle wall built from boxes and a plain black slab for the tower, with no crenellations, roofs or windows. White egg lamps. |
| `frames/c04a_sa1.jpg` (C04 A sa1) | The stepping stones are faceted low-poly shapes, with no wet line, moss or wear. |

## The trick

1. A modular kit (Skyrim: "kits are systems"): wall, tower, crenellation, gate, buttress and roof pieces with beveled edges, all on one stone trim sheet plus one tiling stone.
2. Grime from the ground up: a vertex-color or world-height gradient darkens and mosses the base of every wall. Wear on the edges from a curvature mask, as on her armor.
3. Silhouette before surface: crenellations, roofs, chimneys and broken tops make the skyline. At night a few warm windows and the three blue lamps do the rest.
4. Distance: visibility ranges (HLOD) merge the far castle into one mesh. Cliffs and rocks use triplanar stone.
5. The same stone material for the castle, the town's footings and the river's stones.

## DONE means (at the play and close-up cameras, at 1:1)

- From C01 s8a's distance the castle reads as a castle: towers with roofs, crenellations, a gate, lit windows.
- Mortar lines and edge wear read at the close-up, and every wall's base is darker than its top.
- No box primitives, and no stone with flat facets at the close-up.
- Cost: the far castle is one draw at distance (page 2).

Owners: The tutorial environment lead (the kit, the stone materials, HLOD); cinematics (C01 s8a's exposure and the three blue lamps).

## Sources
- "Kits, first and foremost, are systems" (Burgess and Purkeypile, [Skyrim's Modular Approach to Level Design, GDC 2013](https://www.gamedeveloper.com/design/skyrim-s-modular-approach-to-level-design)).
- Merging far buildings: "you can have a group of houses that uses individual MeshInstance3D nodes (one for each house) when up close" ([Godot, visibility ranges](https://docs.godotengine.org/en/stable/tutorials/3d/visibility_ranges.html)).
- The full list, with verified quotes, is in `look_bible_refs\tricks_sources.md` (outside the repo).
