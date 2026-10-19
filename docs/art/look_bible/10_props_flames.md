# 1j. Story props and flames

The board: `C:\Users\munch\Desktop\survivorsunchained_inputs\look_bible_refs\boards\10_props_flames.jpg`. It sits outside the repo because its top rows are other games' screenshots, kept for reference only and never shipped.

**The look in one line:** every flame is a made thing that lights its surroundings: a modeled holder, a flipbook flame and a flickering light, from one shared kit. The story's own props (the heart, the Warden's lamp) get tier-1 care.

Tier 2 for lamps, torches and windows; tier 1 for a prop the story holds the camera on (the heart in C03, the Warden's lamp in C02).

## What it IS (references; what each teaches)

| Reference | What it teaches |
|---|---|
| Lies of P ([Steam](https://store.steampowered.com/app/1627720), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1627720/ss_cef0c2964b82e2b80ab0756da08f61c27d9fa33c.1920x1080.jpg)) | A lamp as a made thing (brass, glass, a flame inside) that lights the whole room around it. |
| Kingdom Come II ([Steam](https://store.steampowered.com/app/1771300), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1771300/ss_9013f64f459b341d91a4e65bcad2e9c78a9f61af.1920x1080.jpg)) | A room lit by its sources only. The window's shaft and the warm interior light fall off fast into the dark. |
| Path of Exile 2, play camera ([Steam](https://store.steampowered.com/app/2694490), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2694490/ss_03c29d83816331321cbb49dc1e7230da9207de79.1920x1080.jpg)) | Flames on the ground light the floor around them. Small and bright, they read from high up. |
| The Witcher 3 ([Steam](https://store.steampowered.com/app/292030), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/292030/ss_4b4e193c62cc367962b7b9e682e8b3824e75022a.1920x1080.jpg)) | A burning house lights its own smoke from below and turns the ground orange. |
| Kingdom Come II ([Steam](https://store.steampowered.com/app/1771300), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1771300/ss_e9a693d1027ec19c4fdbe5156abc80adac7039f8.1920x1080.jpg)) | Torches at night. Each flame lights the wall behind it, so the flame and its light read together. |

## What ours ISN'T (our frames, 18 Oct audit, 1:1)

| Frame | What fails |
|---|---|
| `frames/c01_s8a.jpg` (C01 s8a) | The lamps are white glowing eggs, where the note asks for three low blue flames. |
| `frames/c03_s6.jpg` (C03 s6) | The heart is a flat-shaded octagon, with no inner light and no water running off it. |
| `frames/c04b_sb4a.jpg` (C04 B sb4a) | The flame is a flat oval sprite that lights nothing. The sill, the frame and the glass stay unlit. |

## The trick

1. Every flame is three things: a flipbook (with motion vectors, so it never steps), a light that flickers by noise, and the surfaces it lights. One shared flame kit: candle, lamp, torch, brazier, camp fire.
2. Holders are modeled: an iron lamp frame with glass (a fresnel edge and a little emission), never a glowing ellipse.
3. The Warden's lamps burn blue: the same kit with a cold flame and a cold light.
4. The heart: stone with glowing veins (an emissive mask that pulses), water dripping off it, and a pulsing light on the water around it.
5. The camp fire: logs with ember cracks, an ash bed, sparks and smoke, and one shadowed, flickering light.

## DONE means (at the play and close-up cameras, at 1:1)

- Every flame lights its surroundings, with a flicker, at every camera.
- No flame is an ellipse or a flat sprite at the close-up, and every holder is a modeled object.
- The heart reads as stone with glowing veins at the close-up (C03 s6, s7, s8).
- Tiers: a prop the story holds the camera on (the heart, the Warden's lamp) is tier 1; the rest are tier 2.

Owners: The tutorial environment lead (the flame kit, lamps and holders, the heart); cinematics (C01 s8a, C03 s6, C04 B sb4a staging).

## Sources
- Separate control of a flame's light and color: "I would render out emissive and albedo channels separately and control those colors/intensities independently in the materials" (Justin Cherry, [Back 4 Blood VFX](https://realtimevfx.com/t/justin-cherry-realtime-vfx-reels-2021-back-4-blood/18495)).
- The full list, with verified quotes, is in `look_bible_refs\tricks_sources.md` (outside the repo).
