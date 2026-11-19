# Look spec, frozen from the owner's 19 Nov night/day reference

The owner (19 Nov): "spend the remaining usage ... on art and coloring heres good night and daytime colorings. and really push our cell shader painterly overlay uniqueness."

The reference is `survivorsunchained_inputs/scratch_coord15/owner_frames/owner_ref_night_day_colors_19nov.webp` (1774x887). Night is columns 0-879 and day is columns 890-1773 (white gutter 882-889).

The reference was measured **once** on 19 Nov. Judges score game frames against this spec plus the eye, and they do not set new numbers.

- **Machine spec:** `tools/look/look_spec_ref19nov.json`. It holds all 140 night and 127 day metrics, each with its ref value and band. It is written by `look_spec.py --freeze`, which refuses to overwrite without `--force`.
- **Script:** `tools/look/look_spec.py`.
- **Regions:** `tools/look/look_spec_regions_ref.json` (ref) and `tools/look/look_spec_regions_verge.json` (Verge judge shots). Both are hand-placed boxes.

## How it measures (identical for the ref and a frame)
All pixel constants are set at 1080p and scaled by s = H/1080. The ref panel is 887 px tall, so s = .82. Colour is Oklab: L, C, and h in degrees.

- **Ink:** L < .22 and black-hat (closing 11 px) > .08, which means a thin dark line.
  - Ink width = ink area / skeleton length, in px at 1080p.
  - Ink on edges = the share of strong colour edges that carry ink. A strong edge has field dE >= .12 across 2x3 px, and it counts as inked if ink lies within 4.5 px.
- **Field:** the ink is inpainted, then median-filtered over a 27 px window (the flat colour field).
- **Marks:** pixels with |L - field L| >= .05 or |ab - field ab| >= .05, kept at least 2 px from ink and in components of at least 6 px.
  - |dh| is measured only where the mark and the field both have C >= .04.
  - Length = sqrt(12 x major-axis variance), in px at 1080p.
  - Bare = share of pixels more than 13 px from a mark.
  - Tile sd = sd of mark cover over 48 px tiles.
  - `--marks` takes the game's `--ink-dbg marks` frame instead of detecting marks (magenta = +, cyan = -).
- **Hue families** (Oklab h):

  | red | orange | gold/yellow | green | teal/cyan | blue | violet | magenta | neutral |
  |---|---|---|---|---|---|---|---|---|
  | 350-40 | 40-68 | 68-120 | 120-165 | 165-235 | 235-280 | 280-318 | 318-350 | C < .04 |

  Shares are % of panel pixels.
- **Objects** are colour classes counted on non-ink pixels:
  - Day: leaf_red (h 350-40, C >= .15), leaf_orange (h 40-68, C >= .15), gold (h 68-100, C >= .13, L >= .55), moss (h 100-135, C >= .06).
  - Night: glow (L >= .82), teal (h 165-235, C >= .09), blue_leaf (h 235-280, C >= .14), violet (h 280-318, C >= .12), magenta (h 318-350, C >= .12).
- **Shadow core:** the darkest 10% of field pixels.
- **Lit / shade** (stones, crowns): split at the Otsu L of the pooled material.
- **Glow spill:** each glow blob (L >= .82, at least 40 px) gets a ring profile of field L at distances of .5-8 source radii.
  - Half = the ring where the lift over the panel's median L falls to half.
  - The values are medians over the sources.
- **Materials:** ground, path, stones, bark and crowns, from hand-placed boxes. Overlaps resolve by priority: stones > crowns > bark > path > ground.
  - The ref boxes sit inside one painted material (a few leaf or tuft pixels may fall in).
  - On the Verge shot, the stones are the flush path slabs. Bark is not in view there, so bark metrics read n/a.

**How the bands were set** (the ref's own variation, with no taste involved):
- **Panel metrics:** [min, max] over 9 re-framed crops of the ref, each 60% of the panel at 3x3 positions. This is the spread that re-framing the same painting gives.
- **Material metrics:** [min, max] over that material's boxes.
- **Glow metrics:** [min, max] over the glow sources.
- **Resolution floor:** every band is at least ref +- the floor, so that 1 px or 1% of a frame is not a look difference. The floors are 1 pt for shares, .02 for L, .01 for C, 4 deg for hue and 1 px for sizes.

**Scale check:** the ref panels resized to 1080 px tall pass 127/127 (day) and 139/140 (night). The one miss is night ground len50 (11 against a band of 12-14 px).

## Panel metrics (ref value [band])
| metric | night | day |
|---|---|---|
| neutral C<.04 % | 7.4 [4.3-8.8] | see json |
| families % | blue 58 [50-70], violet 21 [11-28], teal 11 [8.9-17], magenta 2.9 [.5-4.8], red .6, orange/gold/green 0 [0-1] | orange 40 [32-61], red 37 [24-42], violet 6.4 [4.0-7.6], magenta 5.7 [2.1-7.8], gold 4.7 [2.8-6.6], teal/green 0 [0-1] |
| C p50 | .106 [.096-.116] | .124 [.114-.134] |
| L <.2 % / p50 | 11 [6.4-15] / .372 [.352-.413] | 5.7 [2.7-8.6] / .514 [.472-.606] |
| ink cover % / on edges % / width px@1080 | 7.6 [5.8-9.1] / 39 [35-45] / 3.4 [2.4-4.4] | 5.8 [3.0-8.3] / 35 [22-42] / 3.2 [2.2-4.2] |
| shadow core L, C, h | .243 [.220-.282], .082, h273 [269-277] | .349 [.329-.392], h343 [332-349] (violet-rose) |
| objects % of panel | glow 6.1 [2.6-8.4] (L .90, C .09), teal 7.0 [6.0-12] (L .68, C .127, h224), blue_leaf 16 [11-17], violet 13 [3.9-18] (L .48, C .22, h295), magenta 1.2 | gold 4.7 [2.5-7.2]; leaf_red, leaf_orange, moss: see json |
| glow (night) | source L .91 [.84-.97], lift .23 [.11-.37], half radius 2.0 [1-3] source radii, spill C .109, spill h 243 [225-301] | - |

## Material metrics, marks and field (ref value [band]; full list in the json)
| night | cover % | abs dL p50 | abs dh p50 | dh>=30 % | len px@1080 | bare % | L sd | field L / C / h |
|---|---|---|---|---|---|---|---|---|
| ground | 27 [16-39] | .101 [.073-.128] | 8.5 [4.3-12] | 4.0 [0-9.5] | 13 [12-14] | 6 [0-9] | .131 [.061-.151] | .40 / .110 / 256 |
| path | 18 [13-28] | .092 [.078-.108] | 9.5 [3.8-13] | 7.2 [.6-18] | 9.9 [8.4-12] | 16 [5-20] | .107 | .40 / .105 / 265 |
| stones | 13 [6-17] | .093 [.082-.103] | 7.8 [5.5-11] | 3.5 [.3-6.3] | 9.4 [6.9-16] | 31 [17-64] | .136 | lit .51/.199/269, shade .30/.104/270 |
| bark | 32 [24-63] | .088 | 24 [14-28] | 38 [15-45] | 10 | 6 | .124 | .40 / .096 / 300 |
| crowns | 23 [15-37] | .096 [.076-.106] | 9.5 [2.3-11] | 3.3 [0-4.3] | 8.4 [7.4-9.4] | 16 [3-22] | .171 | lit .62/.242/301, shade .34/.120/277 |

| day | cover % | abs dL p50 | abs dh p50 | dh>=30 % | len px@1080 | bare % | L sd | field L / C / h |
|---|---|---|---|---|---|---|---|---|
| ground | 16 [11-29] | .104 [.068-.124] | 10 [6.8-12] | 9.1 [1-16] | 9.5 [7.2-16] | 21 [7-26] | .138 [.043-.158] | .48 / .075 [.065-.145] / 42 |
| path | 18 [17-20] | .102 [.089-.115] | 5.2 [3.8-6.7] | 5.1 [0-11] | 14 [12-24] | 18 [14-24] | .081 | .69 / .130 / 47 |
| stones | 18 [15-24] | .105 [.094-.124] | 12 [6-16] | 29 [17-35] (moss) | 9.0 [7.8-13] | 14 [2-17] | .158 | lit .73/.128/58, shade .42/.059/336 |
| bark | 30 [17-40] | .109 | 9.7 | 18 [13-21] | 12 | 9 | .162 | .46 / .103 / 31 |
| crowns | 25 [19-36] | .105 [.095-.131] | 7.6 [5.4-9.3] | 5.8 [3.6-12] | 8.9 [7.1-10] | 11 [2-18] | .154 | lit .64/.198/43, shade .43/.153/17 |

**In words:** marks change value by about .10 L and stay within about 10 deg of the field hue. Under 10% of mark pixels turn 30 deg or more; stones by day reach 29% only because of moss. Saturated colour lives in objects: leaves, gold tufts, teal ferns and moss, violet fronds, and the glows. Stone shade is violet-rose by day (h336) and indigo by night.

## Camera note (comparable or not)
The ref is a closer, lower view. The game uses the PoE/Diablo camera, which is never moved to match concept art. Metrics marked `~` in the script output depend on that difference:

- **Comparable as a style of the canvas (read in px at 1080p):** ink width, mark length, bare and tile sd. These are brush properties.
  - If the game anchors marks to the world, they read smaller from the higher camera. In that case use mark length / ink width as the proxy (ref about 2.6-4).
- **Composition, not comparable 1:1:** family shares, object shares, L bins and box ink cover. The game shows more ground and less canopy.
  - Proxy: compare per-material field colour and the mark metrics, which are measured inside each material.
  - Ink cover inside a box scales with form size on screen. Proxy: inner lines per form, counted by eye (ref stones 2-4).
- **Scale-free:** glow half radius (in source radii), all colour, value and hue-turn metrics, and mark cover.

## Baseline: r7 and r8 Verge judge shots (vdayN / vnightN, 1920x1080)
| frame | in | OUT | n/a |
|---|---|---|---|
| ref day / night (self) | 127 / 140 | 0 / 0 | 0 |
| r7 day | 57 | 52 | 18 |
| r7 night | 67 | 58 | 15 |
| r8 day | 47 | 62 | 18 |
| r8 night | 59 | 66 | 15 |

The script agrees with judge r8: r7 is closer to the ref, and r8 regressed. r8 marks turn hue and barely change value.

| r8 worst | band | r8 | r7 |
|---|---|---|---|
| day path abs dh p50 | 3.8-6.7 | 36 | - |
| day path dh>=30 % | 0-11 | 64 | 2.6 |
| day ground abs dh p50 | 6.8-12 | 32 | 20 |
| day stones abs dh p50 / dh>=30 | 6-16 / 17-35 | 46 / 94 | - / 10 |
| day path abs dL p50 | .089-.115 | .014 | - |
| night stones dh>=30 % | .3-6.3 | 55 | .1 |
| night crowns dh>=30 % | 0-4.3 | 36 | 8.7 |
| night ground dh>=30 % / abs dh p50 | 0-9.5 / 4.3-12 | 75 / 50 | .1 / 7.3 |
| night ground abs dL p50 | .073-.128 | .020 | .071 |

**Both rounds miss these:**
- Night ground mark cover is 8-11% against a band of 16-39.
- Night ink on edges is 27-29% (35-45) and night ink cover is 3% (5.8-9.1).
- Night L < .2 is 18% (6-15), and the night shadow core is L .15-.17 (.22-.28).
- Day violet is 0% (4-7.6), and the day shadow core hue is h1-12 against the violet-rose 332-349.
- Night stone lit L is .72 (.48-.55).
- Night glow objects are 1.1-1.2% of the frame (2.6-8.4).
- Day ground field C is .142 (.065-.145, at the edge).
- Day gold tufts are .9-1.5% (2.5-7.2).

## How a judge uses this
1. Run `python tools/look/look_spec.py FRAME.png --panel day|night` (Verge shots use the default regions; other shots need a regions json) and add `--marks` when the `--ink-dbg marks` frame exists.
2. Quote the summary and the OUT lines as they are printed.
3. Then judge with the eye: forms, painterly read and uniqueness. The numbers say how far the frame is from the ref; the eye says whether it reads.
4. Do not invent targets. A band moves only if the owner gives a new reference, which means a new frozen spec.
