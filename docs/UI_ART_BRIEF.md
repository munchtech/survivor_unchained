# UI art brief: every painted piece of the interface

For the artist (or art agent) who paints the interface of Survivor
Unchained. The design and its reasons are in `UI_DESIGN.md`; the research
under it in `UI_RESEARCH.md`. This document says what to paint, at what
size, in what mood, with which tools, and exactly where to put each file so
the game picks it up with no code changed.

**Everything here is already wired.** The game asks for each piece by name;
a file at the right path replaces the drawn look at once, and with no file
the drawn look stays. Art can arrive one piece at a time and the game is
whole at every step.

Contents: 1 how it plugs in · 2 the look · 3 tools and workflows · 4 every
asset · 5 icons · 6 checking your work · 7 licences.

---

## 1. How it plugs in

### 1.1 Where files go
All interface art lives under **`godot/art/ui/`** (the folder does not exist
yet: create it). Each asset's path below is relative to it. The loader is
`godot/src/Ui/UiArt.cs`; the machine-readable list of every asset (path,
size, margins, kind, a starting prompt) is **`tools/comfy/ui_assets.json`**.
If you add or rename an asset, change both.

### 1.2 Size: paint at twice the size shown
The game is laid out at 1920×1080 and scales up for 2K and 4K. **Every file
is made at twice the size it is shown**, and the loader halves it, so it is
crisp at 4K and smooth at 1080p. Sizes below are given as *file* size with
the *shown* size beside it. Exceptions, shown at file size: cursors (the
system draws them) and icons (the code sizes them; paint them large).

### 1.3 Frames are nine-sliced
A frame (a plate, a button, a slot, a card) is cut into nine: four corners
kept as painted, four edges stretched along their length, a centre stretched
both ways. The **margins** are where the cuts fall, given in *shown* pixels
(left, top, right, bottom); in the file they are twice that. Rules:

- Corners and ornament must lie **inside the margins**. Anything outside
  them is stretched.
- The painted border must lie in the **outer three quarters** of each
  margin: the inner quarter belongs to the centre. The game keeps text and
  icons clear of three quarters of the margin.
- Edges and centre must survive stretching: low-frequency texture, no
  features that look wrong drawn long (no single rivet in the middle of an
  edge, no vignette in the centre).
- The centre's tone must match the fallback's (dark iron near #16131a; paper
  near #e4d6b6), because text colours are chosen for it.

### 1.4 What the loader does
- A file the editor has imported loads as a resource; one dropped in without
  importing still loads straight from disk while developing. **Before a build,
  import**: `godot --headless --path godot --import`, then commit the PNG
  *and* its `.import` file. In the editor set the folder's import preset to
  *Lossless* (no VRAM compression) so edges stay clean.
- Halving is done once on load; the file's own size sets everything.
- A missing file is not an error: the drawn look stays.

### 1.5 Formats
PNG, sRGB, 8-bit, straight (not premultiplied) alpha, transparent where
nothing is. No text baked into any asset except the logo. No drop shadow
painted outside a frame's bounds (the game adds its own).

---

## 2. The look

### 2.1 In one line
**Forged night-iron, a thread of gold, ember light where there is power,
parchment where something is written.** Ornament on the edges, calm in the
middle, so what is read is always clear (Hades' "clarity under pressure and
personality everywhere else").

### 2.2 Materials, and where each belongs
| Material | Where | Notes |
|---|---|---|
| **Blackened iron** | Plates, slots, buttons, bar casings, medallions | Hammered, slightly pitted, cool violet-black (#15131a to #2a2631); bevels catch light from the upper left |
| **Gold inlay** | Rims, hairlines, filigree, the interface's own marks | Thin. Warm (#d9b56a, highlights #f3d9a0). Gold means *the interface* and *yours* |
| **Ember** | Things with power at night, the primary button, the focus ring, "new" | Molten orange to gold (#ff8a3a to #ffd07a), glowing from cracks and seams, never flat fills |
| **Blood** | Health, danger, the enemy | Deep glossy red (#c8323a), brighter at the top edge |
| **Moonlight** | The day's growth: experience | Pale cool blue (#86b0d8 to #d8ecff), calm |
| **Parchment** | The journal, hints, the morning report, the map's paper | Warm cream (#e4d6b6), deckled edges, foxing at the rims only |
| **The Verge** | Uncommon rarity, nature | Moss, thorn, bramble, wet bark: for rarity frames and nature icons |
| **The Waystation** | Map frame, tabs | Weathered timber, brass caps, wax, ledger leather |

### 2.3 References
- **Diablo IV**: forged-iron frames, restrained gold, item icons from the
  models, rarity carried in the border (not the fill).
- **Hades / Hades II**: lavish edge ornament with plain centres; rarity
  and source told by the frame.
- **Grim Dawn, Path of Exile 2**: grimy dark fantasy metal, legible at small
  sizes.
- **Darkest Dungeon**: hand-painted grime and ink line, for parchment.
- The concept frames in **`docs/concepts/ui/`** (made on the local ComfyUI
  for this brief): `plate`, `minimap`, `slots`, `bars`, `icons`, `logo`.
  They show the target mood; they are not finals.

### 2.4 Rarity ladder
Common · uncommon · rare · epic · legendary · relic. Colour, but **never
colour alone**: the game also writes the name and shows one to six small
diamonds. In art, rarity rises in *richness* as well as hue:

| | Hue | Frame treatment |
|---|---|---|
| 0 Common | bone grey #c8c0b0 | plain iron rim |
| 1 Uncommon | moss green #6fd46a | thorny vine at the corners |
| 2 Rare | sapphire #5aa8ff | frost-edged corners, a faint glow |
| 3 Epic | violet #c070ff | filigree corners, small gems |
| 4 Legendary | amber #ffb040 | flame-wrought corners, warm glow |
| 5 Relic | blood-orange #ff6a3a | cracked rim leaking ember light |

### 2.5 Dos and don'ts
- **Do** keep silhouettes readable at 18 px (icons) and 24 px (keycaps).
- **Do** light from the upper left, everywhere, consistently.
- **Do** keep centres flat and quiet; text sits there.
- **Do** keep gold for the interface and for "yours"; rarity hues only on
  rarity frames.
- **Don't** put letters, numbers or runes that read as letters on anything
  but the logo.
- **Don't** paint a vignette or a gradient across a frame's centre (it
  stretches badly and fights the text).
- **Don't** let a frame's ornament exceed its margins.
- **Don't** use pure white or pure black in the art; the darkest iron is
  #0b0a0d, the brightest highlight #fff2d8.
- **Don't** strobe or animate (the code animates; art is still).

### 2.6 The soul, as painted (locked)
**Brannoc's iron, the binders' gold, the Morrow's light.** The interface is
smith's work from the Waystation, not a jeweller's: the same hand that forged
the twelve lamp-irons for the Low Ford.

- **The iron** is strap iron drawn out under the hammer, ragged at its edges,
  planished, never milled. Frames *hang*: a plate or a card is held at its top
  corners by lamp-iron brackets (scrolls curling outward, as the brackets of
  the Waystation's signs do) and nailed at its foot.
- **The gold** is the binders': a thin twisted wire set into the strap, and
  the square coin with its quatrefoil hole, nailed at every corner.
- **The light** is the Morrow's. Ember sleeps in the coins' holes (a dull
  smoulder, never a flat fill: it must never read as a sign) and wakes where
  there is power: the ember bar, the primary action, the focus, the draft,
  the evolution. By day it sleeps; at night it burns.
- **The emblem** is the opened link: one link of the seven-link chain pried
  apart, ember at the break. It rides the top of every draft card, stands at
  the head of the art's ring of seven links, and divides the great headings.
- **Rarity is a road through the world**: common is plain road iron; uncommon
  the Verge (bramble, thorn, moss); rare the Low Ford at night (river rime,
  cold blue); epic the binders (violet stones, square-cut sigil lines);
  legendary the Order of the Morning Light (dawn gold, lamp flames); the
  evolution the chain breaking, gilded, ember pouring from the breaks.
- **Paper** is the Waystation's ledger: deckled, foxed at the rims, iron
  corner caps, a nail and a drop of wax.
- **The hand**: every painted piece is painted on the local Krea with the
  darkbrush LoRA over a forged guide that fixes its geometry, then cleaned in
  `tools/uiforge` (silhouette, calm middles, light in the holes, the house
  grade). Exact shapes too small to paint (pad buttons, map marks, keycaps,
  cursors, the interface's own marks) are forged in the same light
  (`tools/uiforge/matcaps`) so the two halves are one family.

Before and after, every screen at 1920×1080 (the drawn look left, the art right): `docs/concepts/ui/style/` (`tools/uiforge/compare.py`).

---

## 3. Tools and workflows

All local; no paid services. The GPU is shared: keep batches small (four
candidates at a time is the default).

### 3.1 The pipeline in one tool: `tools/comfy/ui_art.py`
```
python tools/comfy/ui_art.py list                         # every asset and which are in place
python tools/comfy/ui_art.py paint plate --seeds 4        # four candidates, tools/comfy/out/ui/plate/
python tools/comfy/ui_art.py fit plate tools/comfy/out/ui/plate/cand_4201.png
python tools/comfy/ui_art.py icon glyph_color flame "a burst of fire" --seeds 4
python tools/comfy/ui_art.py fit-icon glyph_color flame tools/comfy/out/ui/glyph_color_flame/cand_4200.png
```
`paint` uses each asset's prompt (and the house style line) from
`ui_assets.json`; `--prompt "..."` overrides it. `fit` does the rest:
- **frame**: cut out with BiRefNet, cropped to the frame, remade at its exact
  file size by *nine-slice remapping* (corners and border thickness kept as
  painted, only the space between margins stretched), so a square painting
  becomes a wide button without fat edges;
- **strip** (bar fills): cropped to proportion and made seamless left to
  right (its overhang cross-faded into its start);
- **cut** (medallions, rings, ornaments, the logo, cursors): cut out and
  centred in its box; rings get their middle opened;
- **light-keyed** (the focus ring, dividers): alpha from brightness, for
  glows and gold lines on black.

The result lands at `godot/art/ui/<path>`; run the game to see it (section 6).
Candidates and cut-outs stay in `tools/comfy/out/` (ignored by git).

### 3.2 ComfyUI (local)
- Server: `http://127.0.0.1:8188`. If it is not running, start it headless
  with `%USERPROFILE%\ComfyUI-Installs\ComfyUI\ComfyUI\.venv\Scripts\python.exe`
  and the extra model paths yaml in `%APPDATA%\Comfy Desktop\instance-model-paths`.
  Models are in `%LOCALAPPDATA%\Comfy-Desktop\ComfyUI-Shared\models`.
- Client: `tools/comfy/comfy.py` (`run GRAPH --set NODE.INPUT=VALUE --out DIR`,
  `upload`).
- **Krea 2 turbo** (`graphs/krea_t2i.json`): UNET `krea2_turbo_fp8_scaled`,
  CLIP `qwen3vl_4b_fp8_scaled` (type krea2), VAE `qwen_image_vae`, 8 steps,
  cfg 1, euler/simple, the **darkbrush LoRA** at 0.8 (node `30:15`;
  `--set 30:15.strength_model=0.6` for cleaner, less painterly results). Set
  `30:24.value=false` to skip the prompt enhancer (keeps prompts literal);
  prompt in `30:19.value`; seed `30:3.seed`.
- **Aspect ratios** (node `49.aspect_ratio`), exactly as named:
  `1:1 (Square)`, `2:3 (Portrait Photo)`, `3:2 (Photo)`, `3:4 (Portrait Standard)`,
  `4:3 (Standard)`, `9:16 (Portrait Widescreen)`, `16:9 (Widescreen)`,
  `21:9 (Ultrawide)`. (`16:9 (Panorama)` does not exist and fails.)
- **Known behaviour**: at 2:3 with frame prompts Krea turbo returned
  dithered noise; use 3:4 for cards. It spells short words well ("SURVIVOR
  UNCHAINED" came out right first time) but check every letter.
- **BiRefNet** cut-outs: core nodes `LoadBackgroundRemovalModel`
  (`birefnet.safetensors`) then `RemoveBackground`, which returns a *mask*
  (save it through `MaskToImage` and apply it as alpha; `ui_art.py` does).
- **img2img clean-up** (symmetry, straighter lines, matching a set): the
  pattern in `tools/assets/heroine_face.py` `paint()`: `LoadImage` →
  `VAEEncode` → `KSampler` with `denoise` 0.3-0.45 → `VAEDecode`. Mirror one
  half in PIL first for perfect symmetry, then img2img at 0.3 to heal the
  seam.
- **qwen3vl** (the CLIP model is a vision-language model; the graph's
  `TextGenerate` node) can describe a candidate: useful to check "is there
  text in this?" or "is it symmetrical?" on a batch.

### 3.3 Blender 4.5 (`C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe`)
For anything that should look *forged*: medallions, the minimap ring, the
skill ring, keycaps, pad buttons, rivets and corner bosses. Model with
bevels, gold inlay as a separate material, render orthographic with a
transparent film (Cycles, 128 samples), key light from the upper left, a
cool rim from behind. Renders are exact and symmetric; paint over them with
img2img at 0.25-0.35 and the darkbrush LoRA to bring them into the painted
style. Corner pieces for frames rendered this way and composited onto a
painted edge give the cleanest nine-slices.

### 3.4 The game's own item studio
Items are already photographed from their 3D models by the game
(`godot/src/Ui/ItemPhotos.cs`; run the game with `--icons` to retake them all,
or `--icons a,b`). Those photographs are the best base for painted item
icons: img2img over the photo at denoise 0.4-0.5 with the darkbrush LoRA
keeps the item's real shape and colours and gives it the painted finish.

### 3.5 Post-processing
Python with Pillow and numpy (installed). For hand work, any editor that
keeps straight alpha. Check every frame at its *shown* size and at 2× before
fitting.

---

## 4. Every asset

Columns: **path** under `godot/art/ui/`; **file** size (shown in brackets);
**margins** (shown px, L T R B) for frames; **where** it is seen and the code
that loads it. States are separate files where the game swaps them.

### 4.1 Plates, paper and tooltips (every screen)
| Asset | Path | File (shown) | Margins | Where, and notes |
|---|---|---|---|---|
| Plate | `frames/plate.png` | 512×512 (256) | 28 28 28 28 | Every screen's back: pack, self, arts, shops, pause, rest, conversation, the table, the arena's end, creation, the map's list (`Style.Plate`). Shown from 460×300 to 1500×790. Riveted corner bosses, thin gold inlay, quiet iron centre |
| Paper | `frames/paper.png` | 512×512 (256) | 32 32 32 32 | The journal, the morning report, the chapter's end (`Style.Paper`). Cream centre, deckled darker rim |
| Tooltip | `frames/tooltip.png` | 256×256 (128) | 16 16 16 16 | Item cards, stat breakdowns (`ItemViews.Card`, `SheetScreen.Breakdown`). Near-black, gold hairline |
| Tooltip, worn | `frames/tooltip_worn.png` | 256×256 (128) | 16 16 16 16 | The worn item's card beside a comparison: the same, quieter (pewter, not gold) |
| Map frame | `frames/map_frame.png` | 256×256 (128) | 20 20 20 20 | The atlas's map (`MapScreen`). Carved dark wood, brass corner caps; the centre is covered by the map, so only the border shows |

### 4.2 Buttons, tabs and focus (every screen)
| Asset | Path | File (shown) | Margins | Where, and notes |
|---|---|---|---|---|
| Button | `frames/button.png` | 192×64 (96×32) | 12 10 12 10 | Every ordinary button (`Style.Button`) |
| Button, hovered | `frames/button_hover.png` | same | same | Brighter rim, faint ember inner edge |
| Button, pressed | `frames/button_pressed.png` | same | same | Pressed in: inner shadow at the top |
| Button, disabled | `frames/button_disabled.png` | same | same | Tarnished, matte |
| Primary button | `frames/button_primary.png` | same | same | The one thing to do (Begin, Buy, Enter the arena): bronze with an ember seam |
| Primary, hovered | `frames/button_primary_hover.png` | same | same | |
| Primary, pressed | `frames/button_primary_pressed.png` | same | same | |
| Segment, on | `frames/segment_on.png` | 128×48 (64×24) | 10 8 10 8 | The chosen option in a row (settings, filters, the arts' pages). Bright gold: **dark** text sits on it |
| Tab | `frames/tab.png` | 160×72 (80×36) | 14 10 14 6 | The book's tabs (Pack, Self, Arts, Journal, Map) above each page (`Overlay.BookTabs`). Rounded top, flat bottom |
| Tab, open | `frames/tab_on.png` | same | same | The open page's tab |
| Chosen row | `frames/row_on.png` | 512×96 (256×48) | 12 10 12 10 | A chosen line in a list (creation's choices, the arts list) |
| Keycap | `frames/keycap.png` | 48×48 (24) | 6 6 6 6 | Every keyboard key shown (`Style.Key`): HUD, hints, footers, tabs |
| Focus ring | `frames/focus.png` | 128×128 (64) | 14 14 14 14 | Round whatever has focus with keys or a pad (`Nav`, `Style.FocusFrame`). Glowing ember-gold line, **empty middle**; drawn 4 px outside the thing; it breathes (the code pulses it) |

### 4.3 Item slots (pack, shop, storeroom, the body)
| Asset | Path | File (shown) | Margins | Notes |
|---|---|---|---|---|
| Empty slot | `frames/slot.png` | 160×160 (80) | 10 10 10 10 | A recessed well. Shown 62-82 px. The code draws a faint glyph of what goes there (helm, ring...) on the body's slots |
| Common | `frames/slot_common.png` | same | same | Rarity rims, section 2.4. The code adds a soft pool of the rarity's light inside, the item's picture, NEW, price and count |
| Uncommon | `frames/slot_uncommon.png` | same | same | |
| Rare | `frames/slot_rare.png` | same | same | |
| Epic | `frames/slot_epic.png` | same | same | |
| Legendary | `frames/slot_legendary.png` | same | same | |
| Relic | `frames/slot_relic.png` | same | same | |

States the code draws over any slot: selected (2 px rarity rim), focused
(the focus ring), being dragged (dimmed), a drop that would be taken (lit),
refused or filtered out (dimmed), too dear (red price). No extra files.

### 4.4 The draft's cards (the night's level-up)
Shown 320×452, three or four side by side; lifted 12 px and glowing in its
rarity when focused; the chosen one swells to 106%.

| Asset | Path | File (shown) | Margins |
|---|---|---|---|
| Common | `frames/card_common.png` | 640×904 (320×452) | 40 56 40 40 |
| Uncommon | `frames/card_uncommon.png` | same | same |
| Rare | `frames/card_rare.png` | same | same |
| Epic | `frames/card_epic.png` | same | same |
| Legendary | `frames/card_legendary.png` | same | same |
| Evolution | `frames/card_evolution.png` | same | same |

Layout inside (the code places these; keep the frame calm under them): a
ribbon at the top (what it is, and NEW), a 112 px disc with the skill's icon
in its school's colour at 16-140 px down, the name, a rank strip, the text,
tags, the rarity word and diamonds and the key at the foot. The top margin is
taller (56) for a gem or crest at the top centre. The evolution card is the
finest thing in the night: gilded, a broken chain, light through the breaks.

### 4.5 HUD
| Asset | Path | File (shown) | Margins | Where, and notes |
|---|---|---|---|---|
| Level medallion | `hud/medal_level.png` | 140×140 (70) | | Left end of the ember/experience bar, round the level number (46 px medal, the art centred on it). The number is drawn by the code: keep the middle dark and flat |
| Heart medallion | `hud/medal_heart.png` | 128×128 (64) | | Left of the health bar (41 px medal); beats when health is low (the code scales it) |
| Art ring | `hud/ring_art.png` | 200×200 (100) | | Over the ready-ring of the art in hand (89 px); **middle open** (radius at least 74% of the half size): the art's icon and the countdown show through |
| Bar track | `bars/track.png` | 128×32 (64×16) | 8 6 8 6 | The groove of the ember/experience bar (900×12) and health (362×26), the self's experience bar |
| Boss track | `bars/track_boss.png` | 256×40 (128×20) | 24 8 24 8 | The boss's bar (744×16): horned end caps |
| Ember fill | `bars/ember_fill.png` | 128×20 (64×10) | | **Tiles** left to right (seamless): molten ember |
| Experience fill | `bars/experience_fill.png` | 128×20 (64×10) | | Tiles: moonlit blue |
| Health fill | `bars/health_fill.png` | 128×48 (64×24) | | Tiles: blood, brighter at the top edge |
| Skill slot | `frames/weapon_slot.png` | 134×134 (67) | 12 12 12 12 | The six skill places at the bottom centre. The code draws the icon, a shade that sweeps as it readies, a rank badge at the corner and a rank strip along the foot (keep the bottom 8 px calm) |
| Chip | `frames/chip.png` | 64×64 (32) | 8 8 8 8 | Status effects above health (icon and seconds), blessings above the skills |
| Toast | `frames/toast.png` | 256×96 (128×48) | 14 10 10 10 | Notifications at the left. The kind's colour is carried by its icon: paint the plate neutral |
| Prompt | `frames/prompt.png` | 256×80 (128×40) | 22 12 22 12 | "E Talk Mother Rook": the pill that floats over what it is for |
| Hint | `frames/hint.png` | 512×256 (256×128) | 16 16 16 16 | The parchment note bottom left that teaches a thing the first time |

### 4.6 The minimap (top right, by day and on the story's roads)
| Asset | Path | File (shown) | Notes |
|---|---|---|---|
| Rim | `minimap/frame.png` | 480×480 (240) | Round the 200 px map disc, centred on it: the band is the outer 20 px each side. **Middle fully transparent** (radius 83.5% of the half size). North is up: a north mark at the top is welcome |
| You | `minimap/you.png` | 48×48 (24) | The survivor's arrow at the centre, **pointing up** (the code rotates it) |
| Marks | `icons/map/*.png` | see 5.3 | The same marks as the big map |

### 4.7 Ornaments, title, cursors
| Asset | Path | File (shown) | Notes |
|---|---|---|---|
| Divider | `ornaments/rule.png` | 960×24 (480×12) | Under headings in every screen (`Style.Rule`), shown at its height and centred: gold filigree fading at both ends, a small ember stone at the middle |
| Flourish | `ornaments/flourish.png` | 720×64 (360×32) | Under the great headings: the draft (EMBER 12), the arena's end, the chapter's end (`Style.Flourish`) |
| Logo | `title/logo.png` | 1400×440 (700×220) | The title screen, top left, replacing "SURVIVOR / UNCHAINED" set in Cinzel. Carved gold capitals, a broken chain through the letters, embers; transparent background. Shown over a dark forest at night: it must read against dark green and black |
| Pointer | `cursors/pointer.png` | 32×32 (32) | Shown as drawn (not halved). Tip at (3, 2) |
| Hand | `cursors/hand.png` | 32×32 | Over anything to press. Fingertip at (11, 2) |
| Forbidden | `cursors/forbidden.png` | 32×32 | Over what cannot be done. Centre at (16, 16) |

### 4.8 As delivered (the art pass)
Where the delivered art differs from the tables above (`UiArt.cs` and
`tools/comfy/ui_assets.json` agree with this list):

| Asset | Change | Why |
|---|---|---|
| Plate | margins 64, `Tile`, `Out: 12`, `Clear: 21` | The corner coins and brackets need room; the strap repeats rather than stretches; content keeps its old 21 px |
| Paper, tooltips, buttons, row, toast, prompt, bar groove, map frame | `Tile` | Hammered iron and laid paper stretched look smeared; repeated, they look made |
| Hint | margins 40, `Tile`, `Clear: 14` | The nail and the wax sit in the corners; the text keeps its old distance |
| Cards | 736×1000, margins 64 80 64 64, `Out: 24` | The card hangs from brackets that reach past it; the row is spaced 52 (not 28) when painted |
| Map frame | `Out: 8`, laid over the map's edge (not under it) | The wooden frame overlaps the map as a real frame does |
| Level medallion | 116 (58 shown) | At 70 it covered the bar's word beside it |
| The art's ring | 220 (110 shown), open below 79% | Six of the binders' coins and the seventh link, pried open, round the ready-ring |
| Bar casings (new) | `bars/casing.png`, `bars/casing_boss.png`, laid over the bars by `GameHud.Casing` | Forged iron round the groove; the boss's with horned ends. Drawn only when present |
| Fills | 512 wide | A longer repeat: the slag and the motes do not visibly repeat along a 900 px bar |
| Empty skill places | use `frames/slot.png` (at 70%) | A place to come, in the same iron as a held skill |

Stat icons (5.5) are not made: they are not wired, and wiring them changes the
standing's layout (the designer's). Everything else in sections 4 and 5 is in place.

### 4.9 The redesign's pieces (the second design pass)
The second design pass recomposed every major screen as full pages and a
console HUD (`UI_DESIGN.md` section 11), drawn in code by `godot/src/Ui/Ornate.cs`
so the game reads as itself before the art lands. Each piece below is asked for
by name and is **wired**: a file at its path replaces the drawn piece, as in
section 1. All are in `tools/comfy/ui_assets.json` (`made_by: not yet made`).
The soul (2.6) holds for every one: smith's work from the Waystation, hung from
lamp-iron brackets, the binders' wire and coins, the ember asleep in the coins.

| Asset | Path | File (shown) | Margins | Where, and notes |
|---|---|---|---|---|
| Well | `frames/well.png` | 256×256 (128) | 12 12 12 12, tiled | A tray sunk into a plate for a grid or a list (`Style.Well`): the pack's, stores' and storeroom's slot wells, the map's list, the journal's list. Shown 200×120 to 1100×560. Sunk, so darker than the plate and lit along its **foot**, not its top; no brackets |
| Slab | `frames/slab.png` | 256×256 (128) | 14 14 14 14, tiled | A raised group inside a plate (`Style.Slab`): the standing's groups, the stores' sub-plates, the map's tools, the draft's build strip. Lit top edge, a dull hairline, **no brackets or coins** (those mark a plate) |
| Page header | `frames/header.png` | 512×200 (256×100) | 0 0 0 12, tiled | The band across the top of every full page (`Overlay.Page`), 1928×100: the book's tabs at its left, the title plaque in the middle, Close at the right. Only its foot is a border; it repeats along its length, so no ornament may land mid-band |
| Banner | `frames/banner.png` | 512×192 (256×96) | 24 14 24 14 | A verdict or a name cut in metal (`OrnateBox.Kind.Banner`): THE ARENA IS WON (470×100), who the survivor is becoming in creation (380×100), a speaker's name in conversation (250×64). Oxblood-stained iron, hung from two brackets, an ember stone at the top's middle; the words are the code's |
| Attribute pillar | `frames/pillar.png` | 424×728 (212×364) | 32 100 32 36, `Out: 12`, `Clear: 14` | Self's four attributes, 188×340 each (with the 12 the brackets may reach past it). A narrow standing stele: a round seat at its head (10-130 px down) for the 120 px medallion with the number, the name and words below, a + button at its foot when there are points to spend. The code draws an ember hairline when points wait: keep the iron neutral |
| HUD console | `frames/console.png` | 512×308 (256×154) | 48 28 48 28, tiled, `Out: 12` | The plate along the HUD's foot (`GameHud.BuildVitals`) the skills stand on, 130 high and 300-720 wide with the skill count; only its top ~98 px are on the screen. Its ends meet the health globe (left) and the art's ring (right): turn them down into round fittings. Plain middle: the skill sockets sit on it |
| Open book | `book/open.png` | 3400×1704 (1700×852) | whole | The Journal (`OpenBook`): the leather cover and both pages. The words sit 78 px in from the cover's outer edges, 34 from the spine, 68 from top and foot: keep the pages blank and even there. The silk ribbons (the sections) are drawn over its top edge by the code |
| Medallion ring | `medallion/ring.png` | 440×440 (shown 44-220) | whole | Every medallion (`Medallion`): levels, the four attributes, the arts' grid and great medallion, facet sockets, creation's step road, the arena's numbers, the draft cards' icon discs. Drawn into the medallion's square: the band from 80% to 100% of the half size, **transparent inside 78%**, where the code draws the core in the school's or rarity's colour, a hairline of it just inside the ring, the progress arc at 88%, and the number or glyph. Must read at 44 px |
| Globe rim | `hud/globe_rim.png` | 288×288 (144) | whole | The health globe's rim (`Globe`, liquid radius 66): the band from 92% to 100% of the half size (may reach in to 83%), transparent inside. A lamp-iron bracket at its top is welcome; the shield's arc is drawn just outside it by the code |
| Globe glass | `hud/globe_glass.png` | 288×288 (144) | whole | Over the liquid, under the number: the glass's reflections only (a soft highlight upper left, a thin rim of light lower right), the rest transparent. The liquid's level, colour, trail and pulse are the code's |

Drawn by the code and **not** asked for by name yet (say if you want to paint
them, and the hook is added): the crested card used by the arts' facets and
creation's choices (`OrnateBox.Kind.Card` with a crest band in the school's or
rarity's colour, 287×280 and 470×92); the Journal's silk ribbons (`RibbonBox`,
132×66-86, one silk per section); the title plaque's gold rules and ember stones
(`Plaque`; a title without words already uses `ornaments/rule.png`).

Pieces that changed their place in the redesign:

| Asset | Now | Why |
|---|---|---|
| Health bar, its casing, `hud/medal_heart.png` | Not shown: health is the globe | The console HUD (Diablo IV's band): health reads at a glance as a level in a vessel, beside the skills, where the eye drops from the fight |
| `frames/map_frame.png` | Not shown on the map, which is now full bleed | The map is opened to find something: the whole screen, no frame. The wooden frame and brass caps suit the Wayfinder's table, where three maps lie on a table: it moves there when that screen is rebuilt |
| `frames/plate.png` | Also the creation and pause columns (which run off the screen's edge, so only the plate's inner edge shows) | One iron for every surface the survivor reads from |
| Draft cards | Now 320×500 (was 452 high): the painted card stretches 48 px in its middle; the card's words keep 40 px inside its iron | The crested card's medallion sits in the card's crest; the card is taller for the reasons and the path at its foot |

---

## 5. Icons

Icons are not halved: paint them large, the code sizes them. All on
transparent backgrounds, no frame (the code frames them), readable at 18 px.

### 5.1 Skills, blessings, statuses and the interface's marks
Two ways; use one per key:

- **`icons/glyph/KEY.png`** (256×256): *value art*, white and greys on
  transparent. The code colours it (a school's colour, a rarity's, grey when
  not ready), so every state keeps working. Best for small marks (statuses,
  slot captions, the HUD's tally).
- **`icons/glyph_color/KEY.png`** (256×256): *full colour*, as Diablo IV's
  skill icons. Kept as painted; greyed and darkened by the code when not
  ready or not known. Best for skills, blessings and evolutions (the draft's
  discs, the HUD's skill slots, the arts and skills lists).

`fit-icon glyph ...` makes value art from a painting (keeps the light, drops
the hue); `fit-icon glyph_color ...` keeps it as painted.

**Keys.** Any key in `godot/data/content/glyphs.json` (90; the current line
glyphs, so you can see what each one is: run the game with `--open arts` or
look at the draft) and the keys below, which the game asks for and which
today fall back to a family's glyph (123):

> aegis, arc, arc_fork, arc_sky, arcane, arrow, arrow_mark, arrow_rain,
> axe_blood, axe_storm, beam_gaze, beam_green, beam_sun, bleed, blink, bolt,
> bolt_bone, boot, chain, chakram, chakram_hail, chakram_razor, cinder, claw,
> coin, command, consecrate, crescent_holy, crosshair, dagger_blood,
> dagger_flurry, disc, disc_aegis, disc_reckon, drain, echo, embers, execute,
> expand, eye, feint, firepot, fist, flame, frost_orb, frostaura, hand,
> heart, herd, herd_great, herd_hunt, horns, hourglass, howl, kindling, leaf,
> leap, living_flame, lock, magnet, mark, mirror, moon_brand, moonfall, mote,
> mote_cascade, mote_star, nova_blood, nova_dawn, nova_harrow, nova_holy,
> nova_rend, nova_sun, palm, palm_storm, palm_temple, perennial, plague, pyre,
> relic, retaura, risen, ruin, sanctify, scent, shard, shard_deep, shatter,
> siphon, skull, slash_blood, slash_heavy, slash_holy, slash_quake,
> slash_spin, slash_steel, smoke, spear, spear_ice, spiritwolf, star, static,
> tether, tether2, tether_mark, thorn, triple, umbral, venom_smoke, wing,
> wraith, zone, zone_blight, zone_blight2, zone_bloom, zone_fire_enemy,
> zone_holy, zone_plague, zone_pyre, zone_root, zone_sanct, zone_thorn,
> zone_venom

Priorities, most seen first: the starting skills (`slash`, `slash_heavy`,
`disc`, `axe`, `mote`, `cinder`, `shard`, `arrow`, `dagger`), the four
starting arts per calling, the statuses (`flame` burning, `plague` poisoned,
`boot` slowed, `aegis` shielded, `shield` bulwark, `smoke` unseen,
`hourglass` time slowed, `howl` war cry, `arcane` other buffs), the tally
(`skull` kills, `coin` gold), then blessings, then evolutions.

**School colours** (the code tints value art with these; match them in
full-colour art): physical #e8dcc4, fire #ff8a4a, frost #8fd0ff, storm
#9ab8ff, nature #8ae05a, arcane #cc88ff, holy #ffd46a, shadow #a87aff.

### 5.2 Items (`icons/item/KEY.png`, 256×256, full colour)
Replace the photographs everywhere an item is shown (slots, cards, toasts,
creation). Three-quarter view, light from the upper left, the object filling
about 80% of the square. Base them on the game's own photographs (3.4). Keys
(47): antidote, armor, armor_heavy, armor_light, axe, bandage, bomb, bone,
book, bow, censer, chest, circlet, cleaver, cloak, dagger, dust, ember,
fang, flower, helm, helm_light, hide, kerchief, key, lamp, lantern, lens,
map, mask, moon, pelt, picks, potion, ring, root, scroll, seed, shield,
sigil, staff, sword, totem, vial, vial_orange, wand, wand_dark.

### 5.3 Map marks (`icons/map/KIND.png`, 64×64)
Used on the big map, its legend and the minimap, shown 15-22 px. Ink on a
small pale parchment disc, so they read on paper and on dark ground alike.
**Keep the hues** (the legend and the code's text use them): quest and turn
red-brown #a8321e, danger dark red #6a1a10, mystery violet #5a3a7a, exit
green-black #2a4a3a, person and place brown #3a2414.

| File | Means | Today's glyph |
|---|---|---|
| `quest.png` | Someone needs you | quest (!) |
| `turn.png` | The next step of a quest | quest |
| `exit.png` | The way out | next (arrow) |
| `danger.png` | Hostile; your belongings where you fell | skull |
| `mystery.png` | Unexplained | eye |
| `person.png` | Someone you can talk to (shown as a dot on the minimap) | talk |
| `place.png` | A named place (the big map writes these as words) | map |

### 5.4 Controller prompts (`icons/prompt/*.png`)
Shown wherever a pad button is meant (footers, the HUD's hands, prompts,
tabs) at 26×26 (face buttons) or 34×26 (the rest). Paint at 104×104 or
136×104. Face buttons are a dark disc with the letter **in its colour**:
A #6bc45a, B #ec5a50, X #4a9cf0, Y #f2c440 (the letter must be there: never
colour alone). Files: `pad_a`, `pad_b`, `pad_x`, `pad_y`, `pad_lb`,
`pad_rb`, `pad_lt`, `pad_rt`, `pad_view`, `pad_menu`, `pad_dpad` (all four
arms), `pad_dpad_up`, `pad_dpad_down`, `pad_dpad_left`, `pad_dpad_right`
(the one arm lit), `pad_lstick`, `pad_rstick`. These are the only icons that
may contain letters (A, B, X, Y, LB, RB, LT, RT).

### 5.5 Currencies and stats
Gold is the `coin` glyph (5.1). Ember is shown as a bar, not an icon. The
standing's lines are words today; stat icons are not wired yet (a future
addition: `icons/glyph/stat_*.png`, would need a line in `SheetScreen`).

---

## 6. Checking your work

1. `python tools/comfy/ui_art.py list` shows what is in place.
2. Run the game on the screen the asset belongs to; screenshots land in
   `godot/.shots/`:
   ```
   GODOT=".../Godot_v4.5.1-stable_mono_win64_console.exe"
   $GODOT --path godot -- --shot plate --seconds 5 --quick warden --zone waystation --open character
   $GODOT --path godot -- --shot draft --seconds 6 --quick reaver --zone arena --open draft
   $GODOT --path godot -- --shot pack --seconds 5 --quick warden --zone waystation --items chain_shirt:2,silver_ring:3,wolf_pelt --open inventory --pad --keys Right,Right
   $GODOT --path godot -- --shot hud --seconds 14 --quick reaver --zone arena --auto idle
   $GODOT --path godot -- --shot title --seconds 6
   ```
   `--pad --keys A,B` presses actions in turn as a pad would (focus ring,
   pad prompts); `--open` takes `inventory character arts journal map pause
   rest stash shop:harlan maps chapter result draft talk:rook`.
3. Look at every screenshot at full size. Check: corners crisp and unstretched;
   text clear of borders; the centre's tone matches; rarity readable without
   colour; nothing beyond the frame; the 1080p downscale clean.
4. Import (`--headless --path godot --import`), commit the PNGs and their
   `.import` files, push.

---

## 7. Licences

Everything must be our own generation (the local ComfyUI, Blender) or CC0.
Anything third-party (a CC0 texture used as a base, a font) is credited in
`public/assets/CREDITS.md` and, if visible, in the game's credits
(`godot/src/Ui/Front.cs`). No paid cloud nodes (they spend the owner's
credits); no API keys in files.
