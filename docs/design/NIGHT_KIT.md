# The night kit: what stands in the night's light (L1 lead 13, 9 Nov)

One block of the look system, designed once here and built as reusable pieces. It extends the four-step night
(`survivorsunchained_inputs\look_l1\work\brief_l11_common.md`: S1 shade, S2 moonlit ground, S3 moon tops, S4 fire)
from the ground and the foes to everything that stands on the board. Law for every helper on the kit.

## Why
Frame 09 (the Deep Shaw, rig `arena_night`) is dark and empty beside the owner's picked target: the leafy black
blobs are the Quaternius kit's `Bush_Common` and `Fern_1`, drawn by the plain kit path with an arena-only albedo cut
(`src/World/ZoneData.cs:205-210`, Shade 0.42, recolor to `#24382e`); the boulders are `Rock_Medium_*` with no top
light. Arenas never go through `Dressing.Own`, so none of our own flora (`godot/art/world/flora/*.gltf`, made by
`tools/assets/env_trees.py` and `env_rocks.py`) is on the board. The owner: own assets over free kits; building blocks.

## The play camera decides (main, 9 Nov: the camera stays)
The game frames 1.6x wider than the target paintings: about 78 px per meter at 1920x1080, figures 0.6x the
target's. Every piece is designed for that framing: no feature under 12 px (0.15 m), a top tone that covers at least
a fifth of the piece's footprint, a thin bright rim line on its moon side. A read that fails at the play camera is
fixed with rim and value separation, never with zoom.

## K1 Three tones and a line, as levels (the standing material)
Every standing piece is painted in hard steps, never a gradient, measured FROM target 09
(`survivorsunchained_inputs\look_l1\g1\full\pick2_09_arena_night.png`; Oklab L / C / hue on screen, after the grade):

| family | contact (ink, base) | S1 side | S2 body | S3 top | rim line |
|---|---|---|---|---|---|
| stone | 0.12 / 0.03 / 266 | 0.18 / 0.05 / 268 | 0.27 / 0.085 / 261 | 0.41-0.45 / 0.12 / 255 | 0.68 / 0.14 / 234, about 3% of the piece |
| leaf | 0.11 / 0.02 / 267 | 0.14 / 0.035 / 254 | 0.23 / 0.063 / 250 | 0.34-0.37 / 0.075 / 234-240 | on the top leaves' moon edges only |
| bark | 0.10 / 0.02 / 268 | 0.15 / 0.035 / 262 | 0.20 / 0.05 / 272 | 0.28 (thin) | 0.45, cyan-blue |

Fire on what stands (her ramp at the piece's ground distance, as two hard bands on the faces toward her; the moon
gives way on those faces only):

| family | fire mid | fire lit | fire top |
|---|---|---|---|
| stone | 0.43 / 0.065 / 5 | - | 0.63 / 0.15 / 48 |
| leaf | 0.36-0.42 olive (C 0.03, h 73-120) | 0.50-0.57 / 0.08-0.12 / 61-78 | 0.60-0.71 / 0.12-0.16 / 58-84 |

Rules:
- **The tones are the rig's levels, not the albedo's luck.** A piece's paint is pulled to one night luminance per
  family (as `foe_moon` does for the foes); the albedo keeps only its hue family and low-contrast dabs. No piece can
  render black: nothing outside ink goes under L 0.10 (R3).
- **Tones step where normals step.** The shader picks the tone from the normal (up and toward the moon: top; away:
  side; the rest: body), from leaf shade (a piece under canopy shade shows no top and no rim: S1/S2 only, R3 one
  shade), and from a contact band at the foot. So the MESH carries the painting: flat facets on stone, flat cards on
  leaves, with the generator baking which cards are top (normal within 30 degrees of up), body (45-70 degrees out)
  and inner or low (horizontal or down). No tone noise inside a facet or a card.
- **One implementation.** The tone, rim and fire functions live in `shaders/cel.gdshaderinc` as the standing block
  (`cel_stand_*`, beside lead 12's `CEL_S3` block, which they use) and are called by `shaders/kit.gdshader`'s own
  `light()`. The foes adopt the same functions in wolves round 2. Rig key `stand` on `arena_night` only; every other
  rig is untouched (a unit test says so, like `WhatStandsIsArenaNightsAlone`). The plan's numbers live in
  `godot/data/look/night_plan.json` under `stand`, and `tools/look/night_values.py` checks a piece's pixels by family.
- **Arenas draw our own flora** through `Dressing.Own` under a rig that has `stand`; the arena-only Shade 0.42 and
  dark recolor go. `--flora-kit` stays as the way back.
- **Contact.** Each piece sits on a hard S1 contact shape (its real cast shadow at the `shadow` level, plus a dark
  foot band); never a soft blob.

## K2 The pieces (our own generators; each a reusable species or preset)
All flat-shaded, all with dab-only albedo, sized for the play camera.
- **Boulders, three sizes** (`tools/assets/env_rocks.py` presets `boulder_s` 0.5-0.9 m, `boulder_m` 1.2-1.8 m,
  `boulder_l` 2.4-3.4 m; two, three and three variants): block-rounded, one near-flat top facet group covering
  35-45% of the top-down footprint, five to eight large planar sides with beveled hard creases (the ink pass draws
  creases), no small surface noise.
- **Leaf clump** (`env_trees.py` species `clump`, three variants): a dome of leaf cards 1.2-2.2 m across and
  0.7-1.2 m tall; pointed, lobed leaves 0.22-0.32 m, so the outline is leaf-shaped scallops, never a ball of dots.
- **Bough** (species `bough`, three variants): the edge foliage and crown mass: a low hanging leaf mass 4-7 m across
  at 2.5-4 m, larger leaves (0.45-0.7 m) with gaps that show the ground; it frames the board's edge and overhangs
  the outer play area at a few points; it takes our flora's existing fade when it would cover her.
- **Seedling** (0.3-0.6 m tufts; the bracken retagged or a new species): the small teal plants between the masses.
- **Trunk and roots** (`trunk_root`): a trunk base 0.5-0.9 m across with three to five flaring roots 1.5-3 m long,
  bark family, large planes.

## K4 The painted ground dab layer (in place of the litter chips and speckle)
A term in `shaders/arena_ground.gdshader`, not geometry: world-anchored angular dabs at two scales (about 0.25 m and
0.7 m), each a flat value offset of one step (about 0.025 L, same hue) under the moon and under the fire alike (the
target's orange field has darker orange dabs). The leaf-litter MultiMesh (`ArenaGround.LeafLooks`) and the macro
speckle are off under a rig that has the dab key.

## K5 Placement (`ArenaGen.Builder.Masses`, `logic/Maps/Arenas/Hollow.cs`)
Groups, not scatter. A stone group is one large, one or two medium and two or three small boulders touching, with
seedlings at the foot; a leaf group is two or three clumps. At least one group of each stands 6-12 m from the start
(in the first frame), nothing inside 2.5 m, small stones may sit inside her fire. Boughs and trunk-and-roots go on the
board's edge (`Hollow.Wall`/`Fringe`) and at three or four overhang points. Open lit fields stay open: the masses
gather where the canopy's shade already is.

## Order and owners
Wave 1: K1 the standing material and the arena's routing (proved on the existing own meshes); K2 the pieces; the
dapple layout (light track). Wave 2: wolves round 2 on the standing functions; K4; K5 with 09's staging. Then the
ground's blue. Each step: numbers, the helper's own half-size look, the lead's look; no judge before a bet.
