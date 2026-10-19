# 1h. The town

The board: `C:\Users\munch\Desktop\survivorsunchained_inputs\look_bible_refs\boards\08_town.jpg`. It sits outside the repo because its top rows are other games' screenshots, kept for reference only and never shipped.

**The look in one line:** a lived-in town under a low sun. The street is the stage at the play camera, every screen shows life, and a small kit on trim sheets makes the variety.

Tier 2. The town closes the Prologue (C04 B) and is the first hub the player walks.

## What it IS (references; what each teaches)

| Reference | What it teaches |
|---|---|
| Titan Quest II, play camera over a town ([Steam](https://store.steampowered.com/app/1154030), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1154030/ss_810475ff9a2f935b7b2d10b53e521e46e7226301.1920x1080.jpg)) | Roofs, walls and street all read. Warm light rakes across them, and the clutter says people live here. |
| Baldur's Gate 3, a high camera ([Steam](https://store.steampowered.com/app/1086940), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1086940/ss_c73bc54415178c07fef85f54ee26621728c77504.1920x1080.jpg)) | A plaza with stalls, banners and a crowd. The street is the stage, and the buildings frame it. |
| No Rest for the Wicked ([Steam](https://store.steampowered.com/app/1371980), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1371980/ss_ba6d507f9ffba16c5fff2f89d2c6b9312ffdfdf6.1920x1080.jpg)) | A timber town at the play camera. Layered walkways, warm lamps and deep shadows. |
| Kingdom Come II ([Steam](https://store.steampowered.com/app/1771300), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1771300/ss_77abcbc203685b38a50a8cee383bd7f47488f090.1920x1080.jpg)) | A market street, lived in. Stalls, barrels and people at work, with a church spire closing the view. |
| The Witcher 3 ([Steam](https://store.steampowered.com/app/292030), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/292030/ss_ba2c8dfce29d6cca82edb1b69c2479d64cc1db23.1920x1080.jpg)) | A timber town at golden hour. The low sun runs down the street, with long shadows and warm walls against cool shade. |

## What ours ISN'T (our frames, 18 Oct audit, 1:1)

| Frame | What fails |
|---|---|
| `frames/play_w84.jpg` (the town at the play camera (a 720p capture)) | A roof fills the frame, and she shows only through a round hole cut in it. The light is flat and brown. |
| `frames/c04b_sb1.jpg` (C04 B sb1) | A low-detail town in shadowless haze, with bald hills on the skyline and no smoke or lit window. |
| `frames/c04b_sb3.jpg` (C04 B sb3) | The villagers stand idle, facing away. Nothing in the street is happening. |

## The trick

1. Roofs and walls between the camera and her fade out (a cut-away, as Baldur's Gate 3 and Diablo IV do), so the street is the stage at the play camera.
2. A modular kit: timber frame, plaster, a stone base, two roof types, all on two trim sheets. At distance, visibility ranges merge each block into one mesh.
3. The dawn sun low down the main street, with long shadows. One or two smoking chimneys and a lit bakery window (the line: "someone is baking").
4. Clutter in clusters from one shared prop kit: barrels, crates, carts, washing lines, stalls, signs.
5. The ground: cobbles with anti-tiling, mud in the gutters, puddles that catch the sky.

## DONE means (at the play and close-up cameras, at 1:1)

- At the play camera she and the street stay visible in town. No roof hides her.
- At dawn the town has a sun with long shadows (pools at least 0.55; ours 0.25).
- Every screen shows at least three signs of life: smoke, a lit window, someone at work.
- No cobble pattern repeats, and neighboring buildings differ in at least two of roof, color and height.
- Cost: the town fits page 2's draw-call budget.

Owners: The tutorial environment lead (the kit, dressing, the dawn light); rendering with the camera code (the roof cut-away); story characters (the villagers, page 1i); cinematics (C04 B staging).

## Sources
- Skyrim's modular kits and Godot's visibility ranges, as on page 1g.
- The roof cut-away is our own call from the play-camera frames (playw_60-108); the references show the street, not the roofs.
- The full list, with verified quotes, is in `look_bible_refs\tricks_sources.md` (outside the repo).
