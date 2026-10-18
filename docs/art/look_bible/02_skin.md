# 1b. Her skin

The board: `C:\Users\munch\Desktop\survivorsunchained_inputs\look_bible_refs\boards\02_skin.jpg` (outside the repo: its top row is other games' screenshots, for reference only).

**The look in one line:** real skin response on an idealized face. Light passes through her skin, pores break up the shine, and color varies by zone. Her complexion stays even and flawless, and pores show only at the close-up and Look cameras. It is never wax, plaster or mannequin, and never hyper-real.

Tier 1 (her). Owner: the touch-up lead (after the armor metal, per the owner's order), with the face lead's measures.

## What it IS (references)
| Reference | What it teaches |
|---|---|
| Baldur's Gate 3, by a fire ([shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1086940/ss_b6a6ee6e046426d08ceea7a4506a1b5f44181543.1920x1080.jpg)) | A warm red band where light turns to shadow, and the sheen broken up. Ears and nose glow. Our C01 case. |
| Dragon's Dogma 2, soft daylight ([shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2054970/ss_ef263c112e274dc73a4bb00596aee1ebfc2b0ed8.1920x1080.jpg)) | Mostly matte skin with color zones: cheeks, nose and lips redder. Shine only on the nose bridge and lips. |
| Stellar Blade ([shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/3489700/ss_9d4d62e118a167333d53db94354671e10416b25d.1920x1080.jpg)) | Idealized beauty that is still skin: an even complexion, soft light passing through, wet eyes, lips with real gloss. The nearest match to her appeal. |
| God of War, firelight ([shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1593500/ss_1351cb512d008f7e47fc50b74197f4f8eb6f3419.1920x1080.jpg)) | Pores and cavities kill the shine in tiny dots, so the highlight reads as skin. |
| A Plague Tale: Requiem, low light ([shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1182900/ss_029c5cfa427cf6d5f0d9f96ae7ea0f3e69f2e88d.1920x1080.jpg)) | Skin in shadow stays warm and alive, never grey or blue. |

## What ours ISN'T (18 Oct audit frames, 1:1)
| Frame | What fails |
|---|---|
| `frames/c02_s4.jpg` (moonlight) | A cool-blue mannequin. The freckles are saturated and stamped on top, and the tan ear looks stuck on. |
| `frames/c02_s8.jpg` (lamp) | Plaster-white, overexposed and flat; the ear stays mid-tan. |
| `frames/c04a_sa7.jpg` (dawn) | One broad, smooth sheen over the forehead, nose and cheeks: wax. |
| `frames/c01_s8.jpg` (fire) | A flat frontal key and an even orange. Shadow edges go grey-brown, not red. |

The audits' finding is that this is mostly the material, and flat lights make it worse: the same waxiness shows under fire, moon, lamp and dawn.

## The trick (all in her one skin shader; no new geometry)
1. **Light passes through:** Godot's skin scattering plus transmittance, so shadow edges get a warm red band and the ears, nostrils and fingers glow when backlit. Today's quality settings run skin SSS "low" on high (PERF_AUDIT). Measure "medium" on her alone before raising it.
2. **Pores break the shine:** the tiled pore detail (`godot/art/people/skin_pores.png` exists), plus a cavity map that removes highlights inside the pores (Jimenez, GDC 2013: "you can't have reflections inside of a pore"). The broad sheen becomes fine sparkle.
3. **Roughness zones:**

   | Zone | Roughness |
   |---|---|
   | forehead and nose | 0.35-0.45 |
   | cheeks | 0.5-0.6 |
   | lips (wet) | 0.3-0.4 |
   | ears | matte |

   Specular about 0.35 (F0 about 0.028).
4. **Color zones, faint:** cheeks, nose and ears redder, the forehead a touch yellow. The ear matches the face under every light. Freckles are low-contrast paint under the scattering, never stamped on top.
5. **Light for close-ups:** never a flat frontal key. Use a three-quarter key, a fill at 1/4 to 1/8 of it, and a warm bounce. Under the moon the light is cool, but her shadow edges stay warm (the grade's toe already keeps dark hues).
6. **Stylized means idealized:** an even complexion with no blemishes, and pores only at the close-up and Look cameras. No hyper-real micro-detail: it costs and it fights her appeal.

## DONE means
At the Look camera, the close-up at its closest zoom and the cinematic close-ups, at 1:1, by fire (C01), moon (C02) and dawn (C04):
- a fresh judge reads skin, not wax, plaster or mannequin;
- face, ears and neck match;
- the shadow edges are warm;
- the highlights are broken up, not one smooth sheen.

## Sources
Penner's pre-integrated skin (SIGGRAPH 2011), Jimenez's separable SSS and his GDC 2013 pore-cavity trick, and Godot 4's subsurface scattering with transmittance. Links and quotes are in `look_bible_refs\tricks_sources.md`, topic 2.
