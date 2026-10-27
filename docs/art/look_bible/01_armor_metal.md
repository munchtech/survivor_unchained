# 1a. Her armor metal

The board: `C:\Users\munch\Desktop\survivorsunchained_inputs\look_bible_refs\boards\01_armor_metal.jpg`. It sits outside the repo because its top row is other games' screenshots, kept for reference only and never shipped.

**The look in one line:** worn, forged metal that takes its color from the light around it. It is darker than her skin, with bright worn edges and dark cavities, and it is never a mirror and never a tinted plastic.

Tier 1 (her). Armor is loot, so it will cover more and more of her. This page is the standard for the touch-up lead's worn-metal pass and for the armor-and-weapons pipeline (smart slot parts).

## What it IS (references; what each teaches)

| Reference | What it teaches |
|---|---|
| Baldur's Gate 3, silver armor by a fire ([Steam](https://store.steampowered.com/app/1086940), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1086940/ss_b6a6ee6e046426d08ceea7a4506a1b5f44181543.1920x1080.jpg)) | The case we have in C01: a heroine in metal by firelight. The metal reflects the fire's orange. Cavities stay dark, worn edges catch the light, the trim is engraved. Nothing clips, and the metal is darker than her skin. |
| Baldur's Gate 3, dark plate ([shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1086940/ss_74d11c230ebb44ff9a69b4533a7333551d5bfc6c.1920x1080.jpg)) | Highlights sit only on edges, ridges and engraving. The flat plates reflect the dark room and stay dark. |
| Dragon's Dogma 2, steel in daylight ([Steam](https://store.steampowered.com/app/2054970), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2054970/ss_8979e7af203f7405845f76ffa73749d924540e97.1920x1080.jpg)) | Bright steel without blown highlights: broad, soft speculars, with form from fluting, rolled edges and lames. |
| Kingdom Come: Deliverance II, gauntlets ([Steam](https://store.steampowered.com/app/1771300), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1771300/ss_935ddb59f90bc2c21c706132cb9b446fe7851c19.1920x1080.jpg)) | Real steel: neutral grey with the sky in it at low contrast. Rivets, straps and plate overlaps read at a glance. (More photoreal than we aim for; it is here for the material.) |

## What ours ISN'T (our frames, 18 Oct audit, 1:1)

| Frame | What fails |
|---|---|
| `frames/c04a_sa6.jpg` (C04 A sa6) | Chrome cups and pauldrons: a mirror band and hot spots. No edge, no wear, no weight: a CG shell. |
| `frames/c03_s3b.jpg` (C03 s3b) | Candy-blue plastic. The blue is a tint on the metal itself, under one even sheen, with no history on the surface. |
| `frames/c01_s5.jpg` (C01 s5) | Firelight blows out the smooth domes (2.8% of the frame clipped). |
| `frames/c04a_sa4.jpg` (C04 A sa4) | Grey-plastic greaves; the knee plates read as dents. |

Shape matters as much as the shader. Our pieces are smooth shells with a painted gold line, and no shader alone will make them read as forged.

## The trick: one system for every slot part

1. **One shared metal family plus one detail map.** `godot/art/people/outfit_materials.json` already has steel, darksteel, iron, rivetbronze, bronze, gold and rust (kind `metal`). Add ONE tiled scratch-and-pit detail (roughness plus normal, about 2.5 repeats a meter like the rest) shared by all of them.
2. **Wear from the geometry, never hand paint.** `heroine_outfit.gdshader` already bakes edge distance, convexity and sky-seen (debug views 1-3). Drive the wear from them: edges smoother and a little brighter, cavities rougher and darker (grime and oxide), occluded areas less reflective. Every new slot part then gets its wear for free, as smart armor parts need.
3. **Roughness:**

   | Area | Roughness |
   |---|---|
   | plate, base | 0.35-0.55, broken up by the detail map |
   | worn edges and high points | 0.2-0.3 |
   | cavities | 0.6-0.8 |

   No large area goes under 0.3. Our metal was 0.18-0.3 on 11 October (performance handoff), which is why it reads as chrome. Metal reflectance stays physical: raw iron and steel near sRGB 180-200, gold warm. Darker reads come from the grime and oxide masks, not from darkening the metal's own color.
4. **Color from materials, not a tint.** Steel stays neutral, a touch cool. Trim is warm brass or gold. Color comes from leather, cloth, enamel and gems. The Warden's blue becomes **blued steel** (deep blue-black with a faint temper sheen) or **blue enamel chipped at the edges to bright steel**. Both are real finishes and keep her color.
5. **Form that reads at 1:1.**
   - Rolled edges: a 3-6 mm bevel that catches a line of light.
   - Trim raised 1-2 mm with a dark gap.
   - Rivets with a shadow, straps with buckles, lames at the joints.
   - All of it comes from one shared trim strip (rolled edge, rivet row, rope, filigree band) UV-mapped along the edges. So the tiers are adornment, as the owner asked: plain forged, etched, gilded with gems and runes.
6. **Reflections show the scene.** A reflection probe per area (the camp, the ford, the town), so metal reflects the dark and the fire, not a bright sky. Cinematics can add a dark card or a single rim source when a shot needs it.

## DONE means

At the play camera, the close-up at its closest zoom and the Look camera, at 1:1, by firelight (C01), moonlight (C02) and dawn (C04):
- No clipped metal (sRGB 250 or more) beyond pinpoint glints of a few pixels.
- The metal sits darker than her skin in the midtones, and its highlights take the scene light's hue.
- A fresh judge reads it as worn metal, not chrome and not plastic.
- From the play camera, a plain, an etched and a gilded piece can be told apart.

Owners: the touch-up lead (the worn-metal standard: items 1-4 and 6 on her current outfits) and the armor-and-weapons pipeline lead (item 5 and the tier ladder, built into the slot parts).

## As built (touch-up 3-4, 18 Oct): the worn-metal standard, for the armor pipeline to consume

Items 1-4 and 6 above, on her four outfits. Every new slot part uses the same shader and gets all of it for free; only a per-piece override is data.
- **Files:** `godot/shaders/heroine_outfit.gdshaderinc` is the only body (`heroine_outfit.gdshader` is a stub that includes it; `heroine_outfit_metal.gdshader` includes it with `OUTFIT_METAL_LIGHT`, every outfit key of kind `metal` in `outfit_materials.json`). The tiled detail is `godot/art/outfit/metal_wear_detail.png` (built by `tools/assets/metal_wear_detail.py`: RG normal, B roughness offset, A cavity). Per-piece overrides: `godot/art/people/metal_finishes.json` "pieces" (by key, then `outfit.piece`, matched by the baked piece number; feeds `piece_rough`).
- **Roughness:** `metal_rough` 0.45 (varied 0.35-0.55 by the detail), `metal_rough_wear` 0.26 on worn edges, `metal_rough_floor` 0.22; `metal_dent` 0.16, `metal_hammer` 0.09 (8 mm planishing); `metal_grime` 1.0 in recesses. Wear from the baked edge, convexity and sky-seen masks, never hand paint.
- **Color:** steel neutral; `gold_tone` #ffd891 (Filament) x `brass_dim` 0.85, `brass_rough_add` -0.18 (raised trim ~0.27, catches a line of light); blued steel `blued` (0.43, 0.44, 0.49), temper `blued_temper` (0.46, 0.43, 0.53), `blued_chip` 1.0 to bright steel at worn edges. Fully metallic keys ignore the scan's metal map (it made flecks).
- **Reflection (no probes):** `metal_env` 0.50 x `metal_env_horizon` 0.8, spec occlusion mix(0.3, 1, sky-seen); `metal_env_graze` 0.3 (the sheen that tells plate in shade from rubber); `metal_ground` 1.0 (Atmosphere's global ground_bounce, below the horizon). Probes were tried: no visible gain, +0.1 ms (commit 3548a664 if ever wanted).
- **Highlights:** `metal_spec_cap` 1.2 (never brighter than 1.2x a white matte card facing that light), `metal_spec_knee` 0.4. Look camera: `look_metal_dim` 1.0, `look_metal_rough` 0.30.
- **Enamel (body 16, 27 Oct):** steel and darksteel are now finish `enamel` (metal_finishes.json; shader finish 2): navy paint (`enamel` sRGB 0.06,0.12,0.30) at metallic 0.3, roughness 0.6, chipped to bright steel only near rims (7 mm) and in a few scuffs, grime 0.35 of bare metal's, sky reflection 0.6, highlights capped at 0.03 of a white card (0.6 where polished, roughness 0.38 or less: the cups). Fully metallic blued steel had no diffuse colour, so a plate edge-on to a bright sky read pale glassy silver. A metal-zone dye recolours the paint. Trial knobs: `METAL_TRY=name=value;...` (floats or r,g,b) and `OUTFIT_DEBUG_VIEW=14` (paint green, bare steel red).
- Dyes on enamel: colour dyes paint the enamel; metal dyes (near-neutral light, or a `:metal` suffix, e.g. `#d2b25a:metal`) keep the metal finish.
- **Example override:** the Warden's greaves and sabatons: rough 0.36, graze 0.45 (a cylinder's highlight is a line).
- **Known, left to the slot parts' shape work:** the greaves in dawn shade still read a little like dark boots (the C04 shot that showed it is cut); moonlit lames stay bluish, mostly the moon's own color (blue/red 1.92).

## Sources
- Filament's PBR notes ([google.github.io/filament](https://google.github.io/filament/Filament.md.html)) give the metal reflectances: iron sRGB about #c4c6c6, gold about #ffd891. They also cover specular occlusion, so cavities lose their reflection: "no real-world material has a reflectance lower than 2%".
- The full list, with verified quotes, is in `look_bible_refs\tricks_sources.md` (outside the repo).
