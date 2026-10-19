# 3. The Prologue's asset inventory: keep, rework or build

Every model, texture and shader the first 20-30 minutes show (title and creation at the Low Ford camp, C01-C04, the Low Ford road and river, the Waystation town), 323 rows, each with a tier, a verdict and the lead who owns it. The data is `12_inventory.csv` beside this page (the extract plus four columns: `tier`, `verdict`, `owner`, `board`); the tables below are generated from it (`look_bible_refs\inventory\mark.py`). Budgets are page 11; the look each row is built to is its board.

**Where we stand:** 229 of the 323 rows are free stylized kits (Quaternius Nature 74, Fantasy Props 44, Medieval Village 41, Universal Base Characters 30, plus KayKit placeholders inside our landmark files 40). That is the "low-poly asset pack" look behind the 18 October audit (1 of 54 shots passed): a realistic heroine in a flat-colored toy world. The owner: "we started with free assets, and we can still use some - but we have a way to build our own now". So the default for anything the camera dwells on is **build**, and a free asset stays only where it meets its board at 1:1.

## The verdicts

| Verdict | Means | Done when |
|---|---|---|
| **keep** | Ours, or meets its board today; no art work for launch beyond what its owner already has open. | Its owner's open list closes. |
| **rework** | The mesh or system stays; materials, LODs, shading or numbers change to meet the board and page 11. | It meets its board's DONE line at 1:1 and page 11's row for its kind. |
| **build** | Made new, ours (Marionette, the Asset Forge, code), to the board and page 11. The old row is deleted from the build when its replacement lands. | As rework, and the old asset is gone from the scene files. |
| **test** | Small background props. Decided at the first 1:1 frame of the new kit beside them: keep if it holds, else rework (new material from the shared atlas), else build. Default if nobody tests it: rework. | Its owner writes keep, rework or build in this table. |
| **cut** | Leaves the Prologue (deferred or replaced by a merged piece). | Gone from the scene and the menus. |
| **n/a** | A bookkeeping row (the whole-file duplicates of the landmark groups). | - |

## The rules (applied in this order; the first that matches wins)

1. **Hers (tier 1): keep, except where listed.** Her body, face textures and shaders: keep (the touch-up lead owns the skin, the worn metal and the next body build: neck, fingers, the painted-out anatomy). Braid, ponytail and pixie: keep (the face lead). Long and bob: **cut** from the Prologue (they leave creation until rebuilt; OWNER_NOTES 18 Oct). Her four calling outfits: **rework** into slot parts at page 11's dressed budget (the armor-and-weapons pipeline lead; the metal standard from the touch-up lead, board 1a). Her weapons (Sketchfab CC-BY): **build** in Marionette's weapon workshop, at most 15k each (the armor-and-weapons pipeline lead).
2. **Bosses (tier 1, later):** the Ford-Warden (ours, code) **rework**, and the Grimtunnel and its lampling base (Sketchfab CC-BY) **build**; budgets 150k / 40k / 10k (page 11). Owner: a bosses lead, when the classes and creatures unpause; until then the cinematics lead keeps them shootable.
3. **Anything third-party with attribution (Sketchfab CC-BY): build.** It is the owner's standing rule to replace third-party assets with our own, and CC-BY can't stay silently.
4. **Story NPCs (tier 2): build** through Marionette (one shared base, morphs, the clothes kit, hair and beard cards, one atlas, at most 40k), board 1i. The Quaternius Universal Base Characters parts go once the Marionette base replaces them. The shared clip libraries (UAL1, UAL2, CC0) are **keep** for now (the animation lead). Owner: the story characters lead.
5. **Fodder (tier 3): build** (the risen, the risen warrior and archer, the barrow knight, the grave caller and the drowned extras): the same Marionette base, cheap (at most 8k at LOD0, 2k in play, VAT, no shadow). Owner: the story characters lead with animation (VAT).
6. **Trees, bushes, grass and undergrowth (tier 2): build** with the Asset Forge to board 1e (our own species, volumes not cut-outs, wind and back light, 3 LODs and an impostor). Owner: the tutorial environment lead; rendering for LODs, impostors and the foliage shader.
7. **Rocks:** the Quaternius rocks **build**; the Poly Haven scans (CC0) **rework** (decimate to page 11's 3k, LODs, re-grade to board 1f). Owner: the tutorial environment lead.
8. **Buildings, walls, roofs, windows, doors and the KayKit placeholders inside our landmark files (towers, wall, gate, hex buildings, shrine, crypt): build** as merged buildings with two trim sheets to boards 1g and 1h. Owner: the tutorial environment lead.
9. **Terrain, road, water and sky (ours, code): rework** to boards 1c, 1d and 1f: one terrain shader with at most 4 layers per pixel (today a 7-layer array), road strips and decals instead of splat-only paint, the water shader, shore foam and the ford's flow map, the zone presets. The Poly Haven CC0 ground and castle textures **rework** (kept as sources where they meet the board at 1:1; replaced by our own over time). Owner: the tutorial environment lead; rendering for fog and light cost.
10. **Lamps, flames and fire FX: build** to board 1j (the flame kit, lamps and holders; lamps unshadowed except one per frame). The code-made light rigs (`lights_fires`) **rework** to the same rule. Kenney particle sheets: **build** (our own flipbooks). Owner: the tutorial environment lead; the cinematics lead for `fx.cinematic`.
11. **Story props** (seen in a cinematic or at the close-up: C01's camp, the fire pit, the wagon, the heart, the Well, the stall's books and scrolls): **build** to board 1j. Owner: the tutorial environment lead.
12. **Small background props** (crates, barrels, buckets, bags, pots, vases, fences, bricks, chimneys, tools; seen only at the play or town camera): **test**. Owner: the tutorial environment lead.
13. **Our shaders and code systems not named above** (the kit, unlit, end-grain, glowing, ghost, ember core, coals shaders): **keep**; rendering owns their cost.
14. **Whole-file rows** (`*.landmarks.WHOLE_FILE`): **n/a**.

<!-- generated below by mark.py: counts, then every row by kind -->

## Counts

Verdict by tier:

| Verdict | Tier 1 | Tier 2 | Tier 3 | Tier - | Total |
|---|---|---|---|---|---|
| keep | 23 | 3 | 0 | 9 | 35 |
| rework | 5 | 23 | 0 | 5 | 33 |
| build | 9 | 193 | 6 | 0 | 208 |
| test | 0 | 43 | 0 | 0 | 43 |
| cut | 2 | 0 | 0 | 0 | 2 |
| n/a | 0 | 0 | 0 | 2 | 2 |
| **total** | 39 | 262 | 6 | 16 | 323 |

Owner by verdict:

| Owner | keep | rework | build | test | cut | n/a | Total |
|---|---|---|---|---|---|---|---|
| animation lead | 2 | 0 | 0 | 0 | 0 | 0 | 2 |
| armor-and-weapons pipeline lead | 0 | 4 | 7 | 0 | 0 | 0 | 11 |
| bosses lead (later) | 0 | 1 | 2 | 0 | 0 | 0 | 3 |
| cinematics lead | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| face lead | 3 | 0 | 0 | 0 | 2 | 0 | 5 |
| rendering lead | 9 | 0 | 0 | 0 | 0 | 0 | 9 |
| story characters lead | 0 | 1 | 30 | 0 | 0 | 0 | 31 |
| story characters lead + animation (VAT) | 0 | 0 | 6 | 0 | 0 | 0 | 6 |
| touch-up lead | 20 | 0 | 0 | 0 | 0 | 0 | 20 |
| tutorial environment lead | 0 | 20 | 102 | 43 | 0 | 0 | 165 |
| tutorial environment lead + rendering | 0 | 7 | 61 | 0 | 0 | 0 | 68 |
| - | 0 | 0 | 0 | 0 | 0 | 2 | 2 |

## Every row, by kind

### heroine

| id | tris | instances | verdict | tier | owner | board | why |
|---|---|---|---|---|---|---|---|
| shader.heroine_skin |  | n/a | keep | 1 | touch-up lead | 1b | rule 1: her body/texture/shader |
| shader.heroine_outfit |  | n/a | keep | 1 | touch-up lead | 1b | rule 1: her body/texture/shader |
| shader.heroine_eye |  | n/a | keep | 1 | touch-up lead | 1b | rule 1: her body/texture/shader |
| shader.heroine_hair |  | n/a | keep | 1 | touch-up lead | 1b | rule 1: her body/texture/shader |
| shader.heroine_teeth |  | n/a | keep | 1 | touch-up lead | 1b | rule 1: her body/texture/shader |
| shader.heroine_paint |  | n/a | keep | 1 | touch-up lead | 1b | rule 1: her body/texture/shader |
| shader.sheer |  | n/a | keep | 1 | touch-up lead | 1a | rule 1: her shader |
| shader.fur_shell |  | n/a | keep | 1 | touch-up lead | 1a | rule 1: her shader |
| her.body | 93608 | 1 | keep | 1 | touch-up lead | 1b | rule 1: her body/texture/shader |
| her.outfit.arcanist | 484865 | 1 | rework | 1 | armor-and-weapons pipeline lead | 1a | rule 1: outfit to slot parts |
| her.outfit.ranger | 652666 | 1 | rework | 1 | armor-and-weapons pipeline lead | 1a | rule 1: outfit to slot parts |
| her.outfit.reaver | 420414 | 1 | rework | 1 | armor-and-weapons pipeline lead | 1a | rule 1: outfit to slot parts |
| her.outfit.warden | 942325 | 1 | rework | 1 | armor-and-weapons pipeline lead | 1a | rule 1: outfit to slot parts |
| her.hair.braid | 101521 | 1 | keep | 1 | face lead | 1b | rule 1: shipping hairstyle |
| her.hair.ponytail | 129261 | 1 | keep | 1 | face lead | 1b | rule 1: shipping hairstyle |
| her.hair.pixie | 93269 | 1 | keep | 1 | face lead | 1b | rule 1: shipping hairstyle |
| her.hair.long | 174148 | 1 | cut | 1 | face lead | 1b | rule 1: long/bob leave Prologue |
| her.hair.bob | 115856 | 1 | cut | 1 | face lead | 1b | rule 1: long/bob leave Prologue |
| her.tex.heroine_head.jpg |  | 1 | keep | 1 | touch-up lead | 1b | rule 1: her body/texture/shader |
| her.tex.heroine_features.png |  | 1 | keep | 1 | touch-up lead | 1b | rule 1: her body/texture/shader |
| her.tex.heroine_ao.png |  | 1 | keep | 1 | touch-up lead | 1b | rule 1: her body/texture/shader |
| her.tex.heroine_eye.png |  | 1 | keep | 1 | touch-up lead | 1b | rule 1: her body/texture/shader |
| her.tex.heroine_iris.png |  | 1 | keep | 1 | touch-up lead | 1b | rule 1: her body/texture/shader |
| her.tex.heroine_lashes.png |  | 1 | keep | 1 | touch-up lead | 1b | rule 1: her body/texture/shader |
| her.tex.heroine_freckles.png |  | 1 | keep | 1 | touch-up lead | 1b | rule 1: her body/texture/shader |
| her.tex.heroine_grain.png |  | 1 | keep | 1 | touch-up lead | 1b | rule 1: her body/texture/shader |
| her.tex.hair_strands.png |  | 1 | keep | 1 | touch-up lead | 1b | rule 1: her body/texture/shader |
| her.tex.hair_scalp.png |  | 1 | keep | 1 | touch-up lead | 1b | rule 1: her body/texture/shader |
| her.skin_pores |  | 1 | keep | 1 | touch-up lead | 1b | rule 1: her body/texture/shader |

### creature

| id | tris | instances | verdict | tier | owner | board | why |
|---|---|---|---|---|---|---|---|
| beast.lampling | 4226 | n/a | build | 1 | bosses lead (later) | 1i | rule 2: boss base, build |
| boss.ford_warden |  | 1 | rework | 1 | bosses lead (later) | 1i | rule 2: Ford-Warden, ours |
| boss.grimtunnel |  | 1 | build | 1 | bosses lead (later) | 1i | rule 2: boss base, build |

### fodder

| id | tris | instances | verdict | tier | owner | board | why |
|---|---|---|---|---|---|---|---|
| shader.person |  | n/a | rework | - | story characters lead | 1i | rule 5: person shader |
| enemy.risen |  | n/a | build | 3 | story characters lead + animation (VAT) | 1i | rule 5: fodder via Marionette, VAT |
| enemy.risen_warrior |  | n/a | build | 3 | story characters lead + animation (VAT) | 1i | rule 5: fodder via Marionette, VAT |
| enemy.risen_archer |  | n/a | build | 3 | story characters lead + animation (VAT) | 1i | rule 5: fodder via Marionette, VAT |
| enemy.barrow_knight |  | n/a | build | 3 | story characters lead + animation (VAT) | 1i | rule 5: fodder via Marionette, VAT |
| enemy.grave_caller |  | n/a | build | 3 | story characters lead + animation (VAT) | 1i | rule 5: fodder via Marionette, VAT |
| enemy.risen_ally |  | n/a | build | 3 | story characters lead + animation (VAT) | 1i | rule 5: fodder via Marionette, VAT |

### story_npc

| id | tris | instances | verdict | tier | owner | board | why |
|---|---|---|---|---|---|---|---|
| people.Superhero_Female_FullBody | 52074 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Superhero_Male_FullBody | 14318 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Female_Peasant_Arms | 6848 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Female_Peasant_Body | 19017 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Female_Peasant_Legs | 14778 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Female_Peasant_Feet | 2588 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Female_Ranger_Arms | 8508 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Female_Ranger_Body | 30266 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Female_Ranger_Legs | 7228 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Male_Peasant_Arms | 5338 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Male_Peasant_Body | 3856 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Male_Peasant_Legs | 1112 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Male_Peasant_Feet | 2588 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Male_Ranger_Arms | 4928 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Male_Ranger_Body | 4606 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Male_Ranger_Legs | 1128 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Female_Ranger_Feet | 9172 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Female_Ranger_Head_Hood | 2136 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Female_Ranger_Acc_Pauldrons | 1376 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Male_Ranger_Feet_Boots | 9172 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Male_Ranger_Head_Hood | 2136 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Male_Ranger_Acc_Pauldron | 1376 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Hair_Buns | 3284 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Hair_Buzzed | 830 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Hair_BuzzedFemale | 830 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Hair_Long | 2906 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Hair_SimpleParted | 1301 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Hair_Beard | 1034 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Eyebrows_Female | 1480 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.Eyebrows_Regular | 984 | n/a | build | 2 | story characters lead | 1i | rule 4: Marionette base replaces |
| people.UAL1 | 13744 | 1 | keep | 2 | animation lead | 1i | rule 4: shared clip library |
| people.UAL2 | 13744 | 1 | keep | 2 | animation lead | 1i | rule 4: shared clip library |

### tree

| id | tris | instances | verdict | tier | owner | board | why |
|---|---|---|---|---|---|---|---|
| lowford.flora.autumn.CommonTree_1 | 6265 | 45 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.autumn.CommonTree_2 | 5648 | 26 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.autumn.CommonTree_3 | 3505 | 40 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.autumn.CommonTree_4 | 4066 | 36 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.autumn.CommonTree_5 | 3182 | 42 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.broadleaf.CommonTree_1 | 6265 | 118 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.broadleaf.CommonTree_2 | 5648 | 125 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.broadleaf.CommonTree_3 | 3505 | 126 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.broadleaf.CommonTree_4 | 4066 | 115 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.broadleaf.CommonTree_5 | 3182 | 124 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.dead.DeadTree_1 | 6169 | 48 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.dead.DeadTree_2 | 6557 | 37 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.dead.DeadTree_3 | 5802 | 51 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.dead.DeadTree_4 | 5702 | 41 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.dead.DeadTree_5 | 5648 | 45 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.pine.Pine_1 | 3947 | 641 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.pine.Pine_2 | 3648 | 583 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.pine.Pine_3 | 4964 | 562 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.pine.Pine_4 | 3370 | 572 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.pine.Pine_5 | 1646 | 597 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| waystation.flora.autumn.CommonTree_1 | 6265 | 9 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| waystation.flora.autumn.CommonTree_2 | 5648 | 5 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| waystation.flora.autumn.CommonTree_3 | 3505 | 7 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| waystation.flora.autumn.CommonTree_4 | 4066 | 5 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| waystation.flora.autumn.CommonTree_5 | 3182 | 7 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| waystation.flora.broadleaf.CommonTree_1 | 6265 | 7 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| waystation.flora.broadleaf.CommonTree_2 | 5648 | 6 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| waystation.flora.broadleaf.CommonTree_3 | 3505 | 6 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| waystation.flora.broadleaf.CommonTree_4 | 4066 | 9 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| waystation.flora.broadleaf.CommonTree_5 | 3182 | 5 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| waystation.flora.pine.Pine_1 | 3947 | 19 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| waystation.flora.pine.Pine_2 | 3648 | 11 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| waystation.flora.pine.Pine_3 | 4964 | 16 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| waystation.flora.pine.Pine_4 | 3370 | 12 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| waystation.flora.pine.Pine_5 | 1646 | 12 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| swap.nature/DeadTree_1 | 6169 | see notes | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| swap.nature/DeadTree_2 | 6557 | see notes | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| swap.nature/DeadTree_3 | 5802 | see notes | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| tex.Bark_DeadTree |  | 1 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| tex.Bark_DeadTree_N |  | 1 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| shader.canopy |  | n/a | rework | 2 | tutorial environment lead + rendering | 1e | rule 6: ours, rework |

### grass_undergrowth

| id | tris | instances | verdict | tier | owner | board | why |
|---|---|---|---|---|---|---|---|
| lowford.flora.berry.Bush_Common_Flowers | 1368 | 128 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.bramble.Bush_Common | 900 | 223 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.bush.Bush_Common | 900 | 321 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.clover.Clover_1 | 379 | 35 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.clover.Clover_2 | 615 | 28 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.fern.Fern_1 | 288 | 867 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.flowers.Flower_3_Group | 755 | 30 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.flowers.Flower_4_Group | 1690 | 30 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.mushroom.Mushroom_Common | 880 | 116 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.pebble.Pebble_Round_1 | 136 | 58 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.pebble.Pebble_Round_2 | 114 | 58 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.pebble.Pebble_Round_3 | 128 | 49 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.pebble.Pebble_Round_4 | 126 | 67 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.pebble.Pebble_Round_5 | 124 | 69 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.pebble.Pebble_Square_1 | 104 | 60 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.pebble.Pebble_Square_2 | 78 | 78 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.pebble.Pebble_Square_3 | 52 | 54 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.flora.plant.Plant_1_Big | 360 | 105 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| waystation.flora.berry.Bush_Common_Flowers | 1368 | 14 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| waystation.flora.bush.Bush_Common | 900 | 25 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: Quaternius, build to 1e |
| lowford.grass |  | n/a | rework | 2 | tutorial environment lead + rendering | 1e | rule 6: code grass, rework |
| waystation.grass |  | n/a | rework | 2 | tutorial environment lead + rendering | 1e | rule 6: code grass, rework |
| shader.grass |  | n/a | rework | - | tutorial environment lead + rendering | 1e | rule 6: foliage shader |

### rock

| id | tris | instances | verdict | tier | owner | board | why |
|---|---|---|---|---|---|---|---|
| lowford.flora.boulder.Rock_Medium_1 | 342 | 18 | build | 2 | tutorial environment lead | 1f | rule 7: Quaternius rock, build to 1f |
| lowford.flora.boulder.Rock_Medium_2 | 244 | 12 | build | 2 | tutorial environment lead | 1f | rule 7: Quaternius rock, build to 1f |
| lowford.flora.boulder.Rock_Medium_3 | 522 | 9 | build | 2 | tutorial environment lead | 1f | rule 7: Quaternius rock, build to 1f |
| lowford.flora.cliff.Rock_Medium_1 | 342 | 28 | build | 2 | tutorial environment lead | 1f | rule 7: Quaternius rock, build to 1f |
| lowford.flora.cliff.Rock_Medium_2 | 244 | 22 | build | 2 | tutorial environment lead | 1f | rule 7: Quaternius rock, build to 1f |
| lowford.flora.cliff.Rock_Medium_3 | 522 | 20 | build | 2 | tutorial environment lead | 1f | rule 7: Quaternius rock, build to 1f |
| lowford.flora.rock.Rock_Medium_1 | 342 | 79 | build | 2 | tutorial environment lead | 1f | rule 7: Quaternius rock, build to 1f |
| lowford.flora.rock.Rock_Medium_2 | 244 | 85 | build | 2 | tutorial environment lead | 1f | rule 7: Quaternius rock, build to 1f |
| lowford.flora.rock.Rock_Medium_3 | 522 | 80 | build | 2 | tutorial environment lead | 1f | rule 7: Quaternius rock, build to 1f |
| swap.nature/Pebble_Round_1 | 136 | see notes | build | 2 | tutorial environment lead | 1f | rule 7: Quaternius rock, build to 1f |
| swap.nature/Pebble_Round_2 | 114 | see notes | build | 2 | tutorial environment lead | 1f | rule 7: Quaternius rock, build to 1f |
| swap.nature/Pebble_Round_3 | 128 | see notes | build | 2 | tutorial environment lead | 1f | rule 7: Quaternius rock, build to 1f |
| swap.nature/Pebble_Round_4 | 126 | see notes | build | 2 | tutorial environment lead | 1f | rule 7: Quaternius rock, build to 1f |
| swap.nature/Pebble_Round_5 | 124 | see notes | build | 2 | tutorial environment lead | 1f | rule 7: Quaternius rock, build to 1f |
| mat.castle_wall_slates |  | n/a | rework | 2 | tutorial environment lead | 1f | rule 7: Poly Haven, rework to 1f |
| mat.forest_ground_04 |  | n/a | rework | 2 | tutorial environment lead | 1f | rule 7: Poly Haven, rework to 1f |
| mat.medieval_blocks_03 |  | n/a | rework | 2 | tutorial environment lead | 1f | rule 7: Poly Haven, rework to 1f |
| mat.pine_bark |  | n/a | rework | 2 | tutorial environment lead | 1f | rule 7: Poly Haven, rework to 1f |
| mat.rock_boulder_dry |  | n/a | rework | 2 | tutorial environment lead | 1f | rule 7: Poly Haven, rework to 1f |
| mat.rough_wood |  | n/a | rework | 2 | tutorial environment lead | 1f | rule 7: Poly Haven, rework to 1f |

### terrain

| id | tris | instances | verdict | tier | owner | board | why |
|---|---|---|---|---|---|---|---|
| lowford.terrain | 135200 | 1 | rework | 2 | tutorial environment lead | 1f | rule 9: terrain/road/ground, rework |
| lowford.splat |  | 1 | rework | 2 | tutorial environment lead | 1f | rule 9: terrain/road/ground, rework |
| waystation.terrain | 64800 | 1 | rework | 2 | tutorial environment lead | 1f | rule 9: terrain/road/ground, rework |
| waystation.splat |  | 1 | rework | 2 | tutorial environment lead | 1f | rule 9: terrain/road/ground, rework |
| ground.albedo.jpg |  | 1 | rework | 2 | tutorial environment lead | 1f | rule 9: terrain/road/ground, rework |
| ground.normal.jpg |  | 1 | rework | 2 | tutorial environment lead | 1f | rule 9: terrain/road/ground, rework |
| ground.arh.jpg |  | 1 | rework | 2 | tutorial environment lead | 1f | rule 9: terrain/road/ground, rework |
| shader.terrain |  | n/a | rework | - | tutorial environment lead | 1f | rule 9: terrain/road/ground, rework |

### road

| id | tris | instances | verdict | tier | owner | board | why |
|---|---|---|---|---|---|---|---|
| lowford.road | 0 | 1 | rework | 2 | tutorial environment lead | 1f | rule 9: terrain/road/ground, rework |

### water

| id | tris | instances | verdict | tier | owner | board | why |
|---|---|---|---|---|---|---|---|
| lowford.water | 2 | 1 | rework | 2 | tutorial environment lead | 1d | rule 9: water, rework |
| waystation.water | 2 | 1 | rework | 2 | tutorial environment lead | 1d | rule 9: water, rework |
| shader.water |  | n/a | rework | - | tutorial environment lead | 1d | rule 9: water, rework |

### sky_atmosphere

| id | tris | instances | verdict | tier | owner | board | why |
|---|---|---|---|---|---|---|---|
| shader.sky |  | n/a | rework | - | tutorial environment lead + rendering | 1c | rule 9: sky/fog, rework |
| sky.lowford.night |  | 1 | rework | 2 | tutorial environment lead + rendering | 1c | rule 9: sky/fog, rework |
| sky.waystation.day |  | 1 | rework | 2 | tutorial environment lead + rendering | 1c | rule 9: sky/fog, rework |

### building

| id | tris | instances | verdict | tier | owner | board | why |
|---|---|---|---|---|---|---|---|
| waystation.prop.village/Corner_Exterior_Brick | 3102 | 292 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Corner_Exterior_Wood | 12 | 64 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/DoorFrame_Flat_WoodDark | 56 | 2 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/DoorFrame_Round_WoodDark | 320 | 32 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Door_1_Flat | 314 | 2 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Door_1_Round | 470 | 32 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Roof_Front_Brick4 | 252 | 12 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Roof_Front_Brick6 | 328 | 20 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Roof_Front_Brick8 | 364 | 8 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Roof_RoundTiles_4x6 | 2520 | 6 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Roof_RoundTiles_6x10 | 4300 | 1 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Roof_RoundTiles_6x6 | 3244 | 5 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Roof_RoundTiles_6x8 | 3796 | 4 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Roof_RoundTiles_8x10 | 4480 | 1 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Roof_RoundTiles_8x12 | 6356 | 2 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Roof_RoundTiles_8x8 | 3888 | 1 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Roof_Tower_RoundTiles | 4024 | 12 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Wall_Plaster_Door_Round | 137 | 4 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Wall_Plaster_Straight | 86 | 74 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Wall_Plaster_Straight_Base | 64 | 27 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Wall_Plaster_Window_Thin_Round | 166 | 33 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Wall_Plaster_Window_Wide_Flat | 96 | 31 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Wall_Plaster_Window_Wide_Round | 124 | 35 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Wall_UnevenBrick_Door_Flat | 74 | 2 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Wall_UnevenBrick_Door_Round | 136 | 28 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Wall_UnevenBrick_Straight | 56 | 944 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Wall_UnevenBrick_Window_Thin_Round | 158 | 55 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Wall_UnevenBrick_Window_Wide_Flat | 88 | 56 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Wall_UnevenBrick_Window_Wide_Round | 116 | 55 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/WindowShutters_Thin_Round_Open | 112 | 15 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/WindowShutters_Wide_Flat_Open | 120 | 9 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/WindowShutters_Wide_Round_Open | 136 | 13 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Window_Thin_Round1 | 418 | 88 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Window_Wide_Flat1 | 160 | 87 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.prop.village/Window_Wide_Round1 | 354 | 90 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.landmarks.kk-halloween-shrine | 94 | 1 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.landmarks.kk-hex_buildings-building_grain | 460 | 2 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.landmarks.kk-hex_buildings-building_watermill_blue | 1921 | 1 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |
| waystation.landmarks.kk-hex_buildings-building_windmill_blue | 2653 | 1 | build | 2 | tutorial environment lead | 1h | rule 8: build merged building |

### castle_wall

| id | tris | instances | verdict | tier | owner | board | why |
|---|---|---|---|---|---|---|---|
| lowford.landmarks.gate | 820 | 1 | build | 2 | tutorial environment lead | 1g | rule 8: build merged building |
| lowford.landmarks.kk-hex_buildings-building_tower_base_blue | 3076 | 2 | build | 2 | tutorial environment lead | 1g | rule 8: build merged building |
| lowford.landmarks.kk-hex_buildings-wall_straight | 5040 | 10 | build | 2 | tutorial environment lead | 1g | rule 8: build merged building |

### prop

| id | tris | instances | verdict | tier | owner | board | why |
|---|---|---|---|---|---|---|---|
| lowford.prop.props/Bag | 858 | 1 | build | 2 | tutorial environment lead | 1j | rule 11: story prop, build to 1j |
| lowford.prop.props/Barrel | 824 | 1 | build | 2 | tutorial environment lead | 1j | rule 11: story prop, build to 1j |
| lowford.prop.props/Chair_1 | 496 | 1 | build | 2 | tutorial environment lead | 1j | rule 11: story prop, build to 1j |
| lowford.prop.props/Chest_Wood | 2546 | 2 | build | 2 | tutorial environment lead | 1j | rule 11: story prop, build to 1j |
| lowford.prop.props/Crate_Wooden | 1576 | 3 | build | 2 | tutorial environment lead | 1j | rule 11: story prop, build to 1j |
| lowford.prop.props/Table_Large | 986 | 1 | build | 2 | tutorial environment lead | 1j | rule 11: story prop, build to 1j |
| waystation.prop.custom/Well | 4146 | 1 | build | 2 | tutorial environment lead | 1j | rule 11: story prop, build to 1j |
| waystation.prop.props/Anvil_Log | 3808 | 1 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.props/Bag | 858 | 8 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.props/Barrel | 824 | 5 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.props/Barrel_Holder | 2676 | 3 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.props/Bench | 404 | 2 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.props/Bucket_Metal | 540 | 1 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.props/Bucket_Wooden_1 | 976 | 4 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.props/Chain_Coil | 3744 | 1 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.props/Chest_Wood | 2546 | 1 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.props/Crate_Wooden | 1576 | 11 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.props/Dummy | 2858 | 2 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.props/FarmCrate_Apple | 4028 | 2 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.props/FarmCrate_Carrot | 5262 | 1 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.props/FarmCrate_Empty | 1928 | 2 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.props/Pot_1 | 1068 | 3 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.props/Rope_1 | 1748 | 1 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.props/Vase_2 | 598 | 2 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.props/Vase_4 | 598 | 1 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.props/Vase_Rubble_Medium | 1113 | 1 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.props/WeaponStand | 2084 | 1 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.props/Workbench | 1368 | 1 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.village/Prop_Brick2 | 94 | 1 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.village/Prop_Brick3 | 126 | 1 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.village/Prop_Chimney | 618 | 18 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.village/Prop_WoodenFence_Extension1 | 32 | 24 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.prop.village/Prop_WoodenFence_Single | 40 | 12 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| swap.props/Banner_1 | 448 | see notes | build | 2 | tutorial environment lead | 1j | rule 11: story prop, build to 1j |
| swap.props/Crate_Metal | 2738 | see notes | test | 2 | tutorial environment lead | 1j | rule 12: background prop, test |
| way.stall.Stall_Empty | 1496 | 1 | build | 2 | tutorial environment lead | 1j | rule 11: story prop, build to 1j |
| way.stall.Scroll_1 | 512 | 1 | build | 2 | tutorial environment lead | 1j | rule 11: story prop, build to 1j |
| way.stall.Scroll_2 | 672 | 1 | build | 2 | tutorial environment lead | 1j | rule 11: story prop, build to 1j |
| way.stall.Book_Stack_1 | 208 | 1 | build | 2 | tutorial environment lead | 1j | rule 11: story prop, build to 1j |
| way.stall.Book_Stack_2 | 446 | 1 | build | 2 | tutorial environment lead | 1j | rule 11: story prop, build to 1j |
| way.stall.Table_Large | 986 | 1 | build | 2 | tutorial environment lead | 1j | rule 11: story prop, build to 1j |
| way.stall.Stool | 152 | 1 | build | 2 | tutorial environment lead | 1j | rule 11: story prop, build to 1j |
| way.stall.BookStand | 1526 | 1 | build | 2 | tutorial environment lead | 1j | rule 11: story prop, build to 1j |
| way.stall.Chest_Wood | 2546 | 1 | build | 2 | tutorial environment lead | 1j | rule 11: story prop, build to 1j |
| swap.stone_fire_pit | 3887 | 1 | build | 2 | tutorial environment lead | 1j | rule 11: story prop, build to 1j |
| lowford.landmarks.baked_unnamed | 1928 | 50 | test | 2 | tutorial environment lead | 1j | rule 12: background prop, test |
| lowford.landmarks.kk-dungeon-banner_thin_red | 83 | 1 | test | 2 | tutorial environment lead | 1j | rule 12: background prop, test |
| lowford.landmarks.kk-dungeon-pillar | 272 | 2 | build | 2 | tutorial environment lead | 1g | rule 8: KayKit structure, build |
| lowford.landmarks.kk-dungeon-rubble_half | 390 | 1 | test | 2 | tutorial environment lead | 1j | rule 12: background prop, test |
| lowford.landmarks.kk-dungeon-rubble_large | 788 | 1 | test | 2 | tutorial environment lead | 1j | rule 12: background prop, test |
| lowford.landmarks.kk-dungeon-wall_broken | 784 | 1 | build | 2 | tutorial environment lead | 1g | rule 8: KayKit structure, build |
| lowford.landmarks.kk-dungeon-wall_cracked | 2010 | 1 | build | 2 | tutorial environment lead | 1g | rule 8: KayKit structure, build |
| lowford.landmarks.kk-dungeon-wall_half | 272 | 1 | build | 2 | tutorial environment lead | 1g | rule 8: KayKit structure, build |
| lowford.landmarks.kk-halloween-candle_triple | 198 | 1 | test | 2 | tutorial environment lead | 1j | rule 12: background prop, test |
| lowford.landmarks.kk-halloween-crypt | 952 | 1 | build | 2 | tutorial environment lead | 1g | rule 8: KayKit structure, build |
| lowford.landmarks.kk-halloween-fence | 3040 | 8 | test | 2 | tutorial environment lead | 1j | rule 12: background prop, test |
| lowford.landmarks.kk-halloween-fence_broken | 1338 | 3 | test | 2 | tutorial environment lead | 1j | rule 12: background prop, test |
| lowford.landmarks.kk-halloween-grave_A | 323 | 1 | test | 2 | tutorial environment lead | 1j | rule 12: background prop, test |
| lowford.landmarks.kk-halloween-grave_A_destroyed | 416 | 1 | test | 2 | tutorial environment lead | 1j | rule 12: background prop, test |
| lowford.landmarks.kk-halloween-grave_B | 380 | 2 | test | 2 | tutorial environment lead | 1j | rule 12: background prop, test |
| lowford.landmarks.kk-halloween-gravemarker_A | 168 | 3 | test | 2 | tutorial environment lead | 1j | rule 12: background prop, test |
| lowford.landmarks.kk-halloween-gravemarker_B | 136 | 1 | test | 2 | tutorial environment lead | 1j | rule 12: background prop, test |
| lowford.landmarks.kk-halloween-gravestone | 542 | 2 | test | 2 | tutorial environment lead | 1j | rule 12: background prop, test |
| lowford.landmarks.kk-halloween-pillar | 282 | 3 | build | 2 | tutorial environment lead | 1g | rule 8: KayKit structure, build |
| lowford.landmarks.kk-halloween-skull_candle | 542 | 1 | test | 2 | tutorial environment lead | 1j | rule 12: background prop, test |
| lowford.landmarks.kk-halloween-tree_dead_large | 256 | 1 | build | 2 | tutorial environment lead + rendering | 1e | rule 6: KayKit dead tree, build to 1e |
| lowford.landmarks.WHOLE_FILE | 16431 | 1 | n/a | - | - | - | rule 14: whole-file duplicate |
| waystation.landmarks.baked_unnamed | 3096 | 123 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.landmarks.kk-halloween-grave_B | 190 | 1 | test | 2 | tutorial environment lead | 1h | rule 12: background prop, test |
| waystation.landmarks.WHOLE_FILE | 14920 | 1 | n/a | - | - | - | rule 14: whole-file duplicate |
| shader.kit |  | n/a | keep | - | rendering lead | 1h | rule 13: our shader |
| shader.endgrain |  | n/a | keep | - | rendering lead | 1j | rule 13: our shader |
| weapon.viking_sword | 916 | n/a | build | 1 | armor-and-weapons pipeline lead | 1a | rule 1: CC-BY weapon, build in workshop |
| weapon.shield_round | 4970 | n/a | build | 1 | armor-and-weapons pipeline lead | 1a | rule 1: CC-BY weapon, build in workshop |
| weapon.crossbow | 9512 | n/a | build | 1 | armor-and-weapons pipeline lead | 1a | rule 1: CC-BY weapon, build in workshop |
| weapon.zweihander | 3066 | n/a | build | 1 | armor-and-weapons pipeline lead | 1a | rule 1: CC-BY weapon, build in workshop |
| weapon.mace | 12698 | n/a | build | 1 | armor-and-weapons pipeline lead | 1a | rule 1: CC-BY weapon, build in workshop |
| weapon.daggers | 2700 | n/a | build | 1 | armor-and-weapons pipeline lead | 1a | rule 1: CC-BY weapon, build in workshop |
| weapon.mage_staff | 19726 | n/a | build | 1 | armor-and-weapons pipeline lead | 1a | rule 1: CC-BY weapon, build in workshop |

### story_prop

| id | tris | instances | verdict | tier | owner | board | why |
|---|---|---|---|---|---|---|---|
| waystation.prop.village/Prop_Wagon | 1672 | 1 | build | 2 | tutorial environment lead | 1j | rule 11: story prop, build to 1j |

### lamp_flame_fx

| id | tris | instances | verdict | tier | owner | board | why |
|---|---|---|---|---|---|---|---|
| waystation.prop.props/Candle_1 | 212 | 1 | build | 2 | tutorial environment lead | 1j | rule 10: lamp/flame, build to 1j |
| waystation.prop.props/Candle_2 | 210 | 1 | build | 2 | tutorial environment lead | 1j | rule 10: lamp/flame, build to 1j |
| waystation.prop.props/Lantern_Wall | 2822 | 21 | build | 2 | tutorial environment lead | 1j | rule 10: lamp/flame, build to 1j |
| waystation.prop.props/Torch_Metal | 970 | 6 | build | 2 | tutorial environment lead | 1j | rule 10: lamp/flame, build to 1j |
| swap.props/Torch_Metal | 970 | see notes | build | 2 | tutorial environment lead | 1j | rule 10: lamp/flame, build to 1j |
| swap.props/CandleStick_Triple | 2528 | see notes | build | 2 | tutorial environment lead | 1j | rule 10: lamp/flame, build to 1j |
| lowford.landmarks.glow | 1556 | 12 | build | 2 | tutorial environment lead | 1j | rule 10: lamp/flame, build to 1j |
| lowford.landmarks.kk-dungeon-torch_mounted | 834 | 3 | build | 2 | tutorial environment lead | 1j | rule 10: lamp/flame, build to 1j |
| lowford.landmarks.kk-halloween-lantern_standing | 264 | 1 | build | 2 | tutorial environment lead | 1j | rule 10: lamp/flame, build to 1j |
| lowford.landmarks.kk-halloween-post | 96 | 1 | build | 2 | tutorial environment lead | 1j | rule 10: lamp/flame, build to 1j |
| lowford.landmarks.kk-halloween-post_lantern | 4544 | 8 | build | 2 | tutorial environment lead | 1j | rule 10: lamp/flame, build to 1j |
| lowford.landmarks.pylon_flame | 420 | 3 | build | 2 | tutorial environment lead | 1j | rule 10: lamp/flame, build to 1j |
| lowford.lights_fires |  | lights 15, fires 1, chimneys 0, moths 0 | rework | 2 | tutorial environment lead | 1j | rule 10: code light rig, rework |
| waystation.landmarks.glow | 5112 | 41 | build | 2 | tutorial environment lead | 1j | rule 10: lamp/flame, build to 1j |
| waystation.landmarks.kk-halloween-lantern_standing | 264 | 1 | build | 2 | tutorial environment lead | 1j | rule 10: lamp/flame, build to 1j |
| waystation.landmarks.kk-halloween-post_lantern | 4544 | 8 | build | 2 | tutorial environment lead | 1j | rule 10: lamp/flame, build to 1j |
| waystation.landmarks.night | 792 | 33 | build | 2 | tutorial environment lead | 1j | rule 10: lamp/flame, build to 1j |
| waystation.lights_fires |  | lights 41, fires 5, chimneys 18, moths 29 | rework | 2 | tutorial environment lead | 1j | rule 10: code light rig, rework |
| fx.fire_loop.png |  | n/a | build | 2 | tutorial environment lead | 1j | rule 10: Kenney sheet, own flipbook |
| shader.unlit |  | n/a | keep | - | rendering lead | 1j | rule 13: our shader |
| shader.flame |  | n/a | keep | - | rendering lead | 1j | rule 13: our shader |
| shader.flame_loop |  | n/a | keep | - | rendering lead | 1j | rule 13: our shader |
| shader.glowing |  | n/a | keep | - | rendering lead | 1j | rule 13: our shader |

### fx

| id | tris | instances | verdict | tier | owner | board | why |
|---|---|---|---|---|---|---|---|
| fx.embers.png |  | n/a | build | 2 | tutorial environment lead | 1j | rule 10: Kenney sheet, own flipbook |
| fx.puff.png |  | n/a | build | 2 | tutorial environment lead | 1j | rule 10: Kenney sheet, own flipbook |
| fx.sprites.png |  | n/a | build | 2 | tutorial environment lead | 1j | rule 10: Kenney sheet, own flipbook |
| fx.ember_motes.png |  | n/a | build | 2 | tutorial environment lead | 1j | rule 10: Kenney sheet, own flipbook |
| shader.coals |  | n/a | keep | - | rendering lead | 1j | rule 13: our shader |
| shader.ember_core |  | n/a | keep | - | rendering lead | 1j | rule 13: our shader |
| shader.ghost |  | n/a | keep | - | rendering lead | 1j | rule 13: our shader |
| fx.cinematic |  | n/a | keep | 2 | cinematics lead | 1j | rule 10: cinematic fx |

