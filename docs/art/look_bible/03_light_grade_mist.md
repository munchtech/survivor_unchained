# 1c. Light, grade and mist

The board: `C:\Users\munch\Desktop\survivorsunchained_inputs\look_bible_refs\boards\03_light_grade_mist.jpg`. It sits outside the repo because its top rows are other games' screenshots, kept for reference only and never shipped.

**The look in one line:** dark, with pools of light from real sources. A low key (the moon, a low sun), ambient two to three stops under it, mist in layers, and a grade that keeps warm highlights over cool shadows. Darkness does not mean bleakness.

Tier 2 (the open world), and the frame around tier 1: it decides how every Prologue shot of her looks. It is the cheapest lever we have: the Atmosphere presets (`godot/logic/World/Atmospheres.cs`, `godot/data/zones/*/zone.json` "atmosphere"), the zone lights and the grade, with no new art.

## What it IS (references; what each teaches)

| Reference | What it teaches |
|---|---|
| Diablo IV, play camera ([Steam](https://store.steampowered.com/app/2344520), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2344520/ss_ee4b4e1ba9c8a07f40aff563c7c43fd04477d60c.1920x1080.jpg)) | Dark ground that still shows its detail, with light only where the action is. Luma p50 23, pools 0.57. "Darkness does not mean bleakness." |
| Path of Exile 2, play camera ([Steam](https://store.steampowered.com/app/2694490), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2694490/ss_e2d559c229fc8e66cefae1f19370fa4ccd2fc712.1920x1080.jpg)) | One fire makes an island of warm light; the rest drops near-black and still reads. The model for C01 seen from the play camera. |
| Diablo IV, play camera, low sun through dust ([Steam](https://store.steampowered.com/app/2344520), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2344520/ss_38d64c37bf2e84bbec5138cf114529eada712ebc.1920x1080.jpg)) | Every figure throws a long shadow that anchors it and gives scale, even in heavy haze. Pools only 0.24: by day the shadows do the work, not the pools. Take the shadows, not the dust. |
| Red Dead Redemption 2, a river at night ([Steam](https://store.steampowered.com/app/1174180), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1174180/ss_66b553f4c209476d3e4ce25fa4714002cc914c4f.1920x1080.jpg)) | A cool moon key and mist, with warm fires far off, both caught in the water. Our ford at night (C02, C03). |
| The Witcher 3, low sun ([Steam](https://store.steampowered.com/app/292030), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/292030/ss_c6d0b7eee8d40b55d33621fcd700151f3325b501.1920x1080.jpg)) | A warm key at grazing height rakes the road with long shadows, while the distance stays cool and hazy. Our dawn (C04). |

## What ours ISN'T (our frames, 18 Oct audit, 1:1)

| Frame | What fails |
|---|---|
| `frames/play_12.jpg` (the Low Ford road at the play camera) | The frost field is the brightest thing on screen, lit flat from above (the moon is 50-52 degrees high). Luma p50 64, pools 0.45. With no warm source anywhere, the pale mobs sink into the frost. |
| `frames/c01_s9.jpg` (C01 s9) | Flat blue over everything. The fire is a small flame with no pool of light, so the camp is not an island. The frosted ground, not the fire, is the brightest area. |
| `frames/c04b_sb1.jpg` (C04 B sb1) | Shadowless haze at dawn. No sun shapes the street, and one pink cast covers lit and shaded sides alike: no cool shadows. Pools 0.47. |

## Measured (`tools/lumstats.py`)

| Frames | Luma p50 | p95 / p50 | Pools |
|---|---|---|---|
| Diablo IV and Path of Exile 2 at night, play camera (diablo4_01/05/06, poe2_06/07/09) | 11-23 | 2.6-7.5 | 0.57-1.27 |
| Night cinematics (Tsushima, RDR2, Witcher 3, KCD II) | 5-75 | 1.6-17 | 0.44-1.45 (mist shots lowest) |
| Day frames at the play camera, p50 at least 50 (Diablo IV, Titan Quest II; 40 frames) | 50 and up | - | 0.24-0.56 (9 of 40 reach 0.55) |
| Ours, the Low Ford road at night, play camera (playc2_12, 16) | 57-64 | 1.9-2.1 | 0.45 |
| Ours, the town at dawn (playc2_54; C04 B sb1, sb5) | 58-84 | 1.5-2.1 | 0.25-0.47 |

By day, pools doesn't separate a good frame from ours (our dawn town's 0.25-0.47 sits inside the shipped range), so the dawn DONE line uses the sun's shadows instead. Luma is Rec.709 on sRGB 0-255, with the HUD and the letterbox cropped. Pools is the std/mean of luma on a 32x18 downsample: it is high when light comes in pools and low when a frame is evenly lit, and dark or pale surfaces can raise it too, so a judge reads it beside the frame. The low-ford preset is why: the moon sits 50-52 degrees high over a strong hemi ambient (0.95-1.25), with exposure 1.42-1.6 and a lifted black (`Atmospheres.Night`, lowford zone.json).

## The trick

1. A low, directional key: the moon 20-30 degrees high (now 50-52), the dawn sun 10-20, its azimuth cheated down the road toward its far end on the Low Ford (LowFordDawn; the owner, 19 October: keep it). Shadows then model the ground and the trees from the high camera. Cap the directional shadow distance to what the play camera needs and use 2 splits. Shadow draws stay at or below today's 2,246.
2. Ambient 2-3 stops under the key: lower the hemi and env intensity and the exposure, and drop the black lift (it makes blacks milky). Shadows go cool and dark, never gray.
3. Pools from real sources: the camp fire, lamps, windows, and her ember (a soft warm light on her at night, the way Diablo IV lights the player). The brightest area of a frame is a source or what it lights.
4. Mist in layers: volumetric fog for the air and the lamp halos. For thin mist on the river and in hollows, 2-3 stacked mesh planes with scrolling noise that fade softly where they meet geometry, colored by the key. Never camera-facing sprites.
5. A grade per area: AgX, warm highlights over cool shadows, saturation about 0.9, and backgrounds 1.5-2 stops under the subject (sRGB luma ratio 1.6-1.9).

## DONE means (at the play, close-up and Look cameras, at 1:1)

- Night play frames: luma p50 15-35 (Diablo IV and Path of Exile 2: 11-23; ours 57-64), p95 at least 2.5 times p50 (theirs 2.6-7.5; ours 1.9-2.1), and pools at least 0.55 (theirs 0.57-1.27; ours 0.45).
- Dawn and day: a sun 10-20 degrees high casts shadows over at least a quarter of the ground in a play-camera frame, and lit ground is at least one stop over the shadow beside it (sRGB luma ratio at least 1.35 on a patch pair). Pools isn't used by day (shipped play-camera day frames: 0.24-0.56).
- Close-up camera at closest zoom and the Look camera, night: her face reads (skin and eyes) and is the brightest area that isn't a light source, lit by a source a judge can name. The background median sits about 6x under her face (sRGB luma ratio 5-6.5, about 2.5 stops). The owner, 19 October: keep the night close-up at about 6x (the GameCloseUp exposure, built in E1), replacing the earlier 1.6-1.9.
- At most 0.5% of a frame clipped, outside flames and lamps.
- In every shot a fresh judge can say where the light comes from. Nothing is lit by ambient alone.
- Mobs and pickups stay readable (the rim light, her pool): the player never loses her or an enemy in the dark.
- Volumetric fog and the mist planes together add at most 0.5 ms GPU at 1440p.
- Measured on fixed positions (the audit's playc2_12, playc2_16 road positions, plus the ford, camp, wood road and three town frames at dawn), with the audit's HUD crop and the vignette off.
- Pools = the std/mean of luma at 32x18; docs/art/look_bible/tools/lumstats.py measures all of these.

Owners: The tutorial environment lead (the zone presets, zone lights and fog); cinematics (each shot's own key and grade: the audit's STAGING block); rendering, for readability (the body rim, her ember light) and the cost of fog and shadowed lights.

## Sources
- Diablo IV art direction: "considering the techniques classical painters like Rembrandt used, with their controlled use of detail, tonal range, and expert use of color palettes" ([Blizzard, March 2022](https://news.blizzard.com/en-us/article/23788294/diablo-iv-quarterly-updatemarch-2022)); John Mueller: "Darkness does not mean bleakness" ([PCGamesN](https://www.pcgamesn.com/diablo-4/diablo-2-art-style)).
- Ghost of Tsushima: "Lighting can deviate from physical correctness. Artists can globally adjust to achieve desired look" (Patry, [SIGGRAPH 2021](https://www.advances.realtimerendering.com/s2021/jpatry_advances2021.pdf)).
- Volumetric fog as froxels, the idea behind Godot's volumetric fog (Wronski, [AC4, GDC 2014](https://bartwronski.com/wp-content/uploads/2014/03/ac4_gdc.pdf)).
- The full list, with verified quotes, is in `look_bible_refs\tricks_sources.md` (outside the repo).
