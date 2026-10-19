# 1i. NPCs and crowds

The board: `C:\Users\munch\Desktop\survivorsunchained_inputs\look_bible_refs\boards\09_npcs.jpg`. It sits outside the repo because its top rows are other games' screenshots, kept for reference only and never shipped.

**The look in one line:** NPCs that belong in her world without her detail: one shared base, variety from data, and staging (light, mist, silhouette) wherever a close-up would show what a tier-2 head lacks.

Tier 2 for the story NPCs (the Warden, Grimtunnel, the villagers) and tier 3 for the fodder (the drowned, the risen). The bar is "looks good in the shot and runs well", not "matches her".

## What it IS (references; what each teaches)

| Reference | What it teaches |
|---|---|
| Kingdom Come II ([Steam](https://store.steampowered.com/app/1771300), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1771300/ss_b863918a1655050ee6200846cf8abb71137fa13e.1920x1080.jpg)) | Real proportions and plain clothes with weight. Take those; the scanned faces are beyond tier 2. |
| Dragon's Dogma 2 ([Steam](https://store.steampowered.com/app/2054970), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2054970/ss_ef263c112e274dc73a4bb00596aee1ebfc2b0ed8.1920x1080.jpg)) | A warm key from one side and a soft fill. On a tier-2 face the light does half the work. |
| Banishers ([Steam](https://store.steampowered.com/app/1493640), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1493640/ss_d955784e3e58baa3ae037a7cbab886e27af01980.1920x1080.jpg)) | Villagers at mid distance. Varied silhouettes and a muted palette from a small kit of clothes; no face detail is needed at this size. |
| Titan Quest II, play camera ([Steam](https://store.steampowered.com/app/1154030), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1154030/ss_59840410d4676c83c292960be63bc13550643128.1920x1080.jpg)) | People read from high up through proportion, cloth value and their shadow on the ground, not face detail. |
| Banishers ([Steam](https://store.steampowered.com/app/1493640), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1493640/ss_c309ec41b66ba62ab7c7c54a257f58f7a5d2a4ee.1920x1080.jpg)) | Faces lit by one candle and falling off into the dark. Staging hides what a tier-2 head lacks. |
| Lords of the Fallen ([Steam](https://store.steampowered.com/app/1501750), [shot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1501750/ss_ecb5a5df054344bf681282edb3ed76499e675605.1920x1080.jpg)) | A figure backlit in cold blue mist, a silhouette with a lit edge. Our drowned and the Warden, staged. |

## What ours ISN'T (our frames, 18 Oct audit, 1:1)

| Frame | What fails |
|---|---|
| `frames/c02_s1.jpg` (C02 s1) | Cartoon drowned standing in a grid in flat water, every figure the same model, a green-faced zombie in front, no mist. |
| `frames/c03_s1.jpg` (C03 s1) | The Warden as a cartoon: a clay beard shell and blank white eyes in a flat blue fill. |
| `frames/c03_s10.jpg` (C03 s10) | Grimtunnel's untextured, polka-dot skin; a faceted brim hides his eyes. |
| `frames/c04b_sb4b.jpg` (C04 B sb4b) | A cartoon villager with chunky hair, plastic skin and a clay-smooth bodice. |
| `frames/play_54.jpg` (the town at the town camera) | Brannoc at his anvil. Flat orange skin, a dark blob for a head and nothing grounding him; only the "!" marker says he matters. |

## The trick

1. One shared base for every human: the shared human base (hers), with male and female body morphs and face morphs for variety, through Marionette, and one atlas material per story NPC and one per crowd type. At an NPC LOD (Godot's import LODs; check they hold on the skinned mesh), with hair cards at page 2's NPC card count.
2. Variety from data, not new models: a tint per instance (skin, hair, cloth), a small kit of clothes, hair cards from the style library. Beards and brows are cards too: a small beard set (stubble, short, full), never a sculpted shell.
3. Tier 3 (the drowned, the risen): instanced, with animation baked to textures (VAT) and LODs. A wet shader (darker, glossier, strands of weed) tells the drowned's story. Each drowned figure in water gets a ripple ring at the waterline (one shared flipbook decal). Each instance gets its own clip offset and ±10% speed (INSTANCE_CUSTOM in the VAT shader), so no two move in step. A shared blob decal (or a blob quad in the MultiMesh) grounds crowd and background NPCs.
4. Staging over detail: mist, backlight and silhouette for crowds; a deep hood that keeps the Warden's face in shadow, with "two blue points" for eyes: small glints the size of a pupil and the brightest thing in the hood, never glowing eye shapes; a hero head only where a close-up needs one.
5. A face in close-up gets a three-quarter key and a darker background, as hers does.
6. Tier-2 surfaces. Skin comes from her base's skin set, tinted, with roughness variation and a tiled micro-normal. Cloth comes from a few tiling weaves (linen, wool, leather), with folds baked to the normal map and darker AO in the folds. Eyes have an iris and an off-white sclera. One atlas material per story NPC.

## DONE means (at the cameras each NPC is shown at, 1:1)

- Next to her in the same frame, no NPC has flat-albedo skin, single-shell hair or beard, cloth without folds or weave, a pure-white sclera or faceted silhouette edges.
- Crowds stand in staggered depth, never a grid: uneven spacing and facing, each rank lighter in the mist, the nearest with a lit edge (C02 s2, s10).
- Every NPC face in a close-up is a hero head, or is staged so the eyes still read (two lit points, a catchlight under the hood or brim, a rim on the brow), never a blank shape.
- At the town camera at 1:1, day and night, every NPC reads as a person: real proportions, at least two cloth values, hair that isn't one shell, a contact shadow, and a work loop or conversation pose.
- In any crowd, no two neighbors share height, build and garment, and none move in step.
- At the play camera at 1:1, at night, each drowned or risen figure reads from its silhouette and wet sheen against the water or ground, with its ripple ring, and never loses to the background (page 1c's readability line).
- Cost: each story NPC is one atlas material plus its hair cards, at an import LOD past about 10 m. Each crowd type is one MultiMesh draw. Crowd and background NPCs cast no shadow: a shared blob decal (or a blob quad in the MultiMesh) grounds them. Only the story NPCs in a shot cast real shadows.

Owners: The story characters lead through Marionette (the base, morphs, the clothes kit, hair cards); animation (VAT for crowds, the story clips); cinematics (staging).

## Sources
- Crowds: "we could successfully create a scene where 10,000 crowd NPCs are on screen at the same time" (Cournoyer, [AC Unity, GDC 2015](https://gdcvault.com/play/1022141/Massive-Crowd-on-Assassin-s)); instanced crowds with animation in textures: "almost 10,000 characters, independently animating ... at 30 frames/sec" ([GPU Gems 3, ch. 2](https://developer.nvidia.com/gpugems/GPUGems3/gpugems3_ch02.html)).
- Staging that hides a low-detail face (hoods, backlight, silhouette) has no public source; it is our own craft.
- The full list, with verified quotes, is in `look_bible_refs\tricks_sources.md` (outside the repo).
