# Armor piece schema (armor lead 2, 18 October 2026)

The contract between Marionette's armor workshop (which writes it) and `tools/armor/build.py` (which builds it on her body). Both sides follow this page; a change here changes both.

## piece.json
`godot/art/armor/src/<id>/piece.json` in the game; `generated/to_game/armor/<id>/piece.json` from Marionette, with any adornment meshes beside it.

| field | meaning |
|---|---|
| `id` | `[a-z0-9_]+`, unique across both armor indexes and `godot/art/armor/src/` (the game's drop checks all three; Marionette checks its kit only) |
| `name` | the player-facing name |
| `slot` | one of top, bottom, legwear, gloves, skirt, belt, collar, bracers, greaves, boots, pauldrons, cloak, head. (`ink`, the reaver's tattoos, is part of a calling's skin: never a piece slot.) |
| `base` | optional: the id of another piece whose shell this one wears unchanged. A tier variant names its plain piece as base and adds adornment only: the build reuses the base's shell geometry, weights and tuck exactly (no refit, no shell change). Without `base`, `style` + `params` define the shell. A variant's `adorn` is ADDED to its base's adornment (the base's rivet rows and fixings stay); set `base_adorn: false` to drop the base's adornment and keep only the shell. |
| `style`, `params` | the shell builder and its numbers (ignored when `base` is set) |
| `tier`, `tier_name` | 1 plain forged, 2 etched, 3 gilded |
| `material`, `tint` | a name from `godot/art/people/outfit_materials.json`; tint an sRGB hex or null |
| `adorn` | list, below |
| `covers` | visual slots it hides (defaults to `[slot]`) |
| `hold` | optional `{amount, squash}` for her jiggle under it (rigid plate: 0.55, 0) |

## Sockets and rims (`<id>.sockets.json`, written by the build)
- **Pair stem:** a socket or rim named without a side (`cup_rim`, `cup`, `strap`) means both `_l` and `_r`, mirrored; with `_l` or `_r` it means that side only. Unpaired names (`gore`, `back`) have no suffix.
- **Socket frame:** in her rest pose, glTF space (Y up, metres). `+Z` points out of the shell surface (the normal); `+Y` is world up projected onto the surface plane, squared against Z (if the normal is near vertical, world -Z, her forward, projected instead); `+X = Y x Z`. A socket stores its point and these three axes.
- **Rims** are polylines on the shell's OUTER face at its edge (the build writes them there; a preview may raycast onto the outer face as a fallback).

## Adornment kinds
Each element of `mesh` and `row` rides one blend of bones taken from the shell at its foot, so it never bends; `trim` takes the rim's weights.
- `row`: `{kind:"row", rim, mesh, spacing, inset, r, avoid, mat}`: elements along a rim, `inset` m in from the rim along the surface, `r` element radius, `avoid` (m, default 0.014) the clear radius kept around the shell's own fixings (strap anchors, buckles), where no element is placed.
- `mesh`: `{kind:"mesh", socket, mesh, scale, roll, offset, mat, gem_mat}`: one mesh at a socket; `roll` degrees about +Z; `offset` [x,y,z] m in the socket frame.
- `trim`: `{kind:"trim", rim, profile, width, height, inset, gap, mat}`: a raised band along a rim. `width` across the band, `height` above the shell surface (1-2 mm reads), `inset` m in from the rim (0 = on the rolled edge), `gap` the dark groove on each side between band and shell (default 0.001). Profiles: `rolled`, `rope`, `filigree`, `gold_band`.
- `paint`: `{kind:"paint", target:"shell", pattern, strength}`: `pattern` = `etch_<name>`, an etched pattern carried in the shell's surface detail (the game's shader renders it).
- Built by `tools/armor/adorn.py` (all but a `row` of `rivet`, which the Blender build makes): `trim` `inset` is the band's centre line; its `gap` grooves and `paint`'s pattern are a film 0.25 mm over the plate in the shell's own mesh, its sky and convexity data dropped so the outfit shader draws it dark, rough and recessed (the metal kind draws only its texture's mean colour, so a texture pattern would not show). Patterns: `etch_band_vine` (a Renaissance blackened band on each cup inside the rivets, `band` [in, out] m from the rim, with a running vine left bright in it as gaps in the film (`wave` 14, `amp` 2.2, `stem` 1.4, `leaf` 3.0 mm, a leaf off each crest), framed by fine `lines`; the gameplay LOD the dark band only). `paint` `ground`: the material its films go in (default the shell's); a leather one draws them as a matte black fill, `sky` its sky (the metal kind darkens a film only to about 0.8 of the bare plate at the close-up; blackening 0.4-0.55 needs the matte fill). A row identical to a base row that `base_adorn: false` dropped re-uses the base's own elements in its `mat` (gilt rivets).

## Material names
Every `material` and every adornment `mat` is an entry name in `godot/art/people/outfit_materials.json` (the game's one material list; the shader draws by its kind). Gems are entries there too: `gem_garnet`, `gem_amethyst`, `gem_sapphire`, `gem_emerald` (added with the tiers). A library mesh's own slots (`metal`, `gem`) are replaced by the adornment's `mat` (a gem's bezel takes `mat`, its stone takes `gem_mat`, default `gem_garnet`).

## The adornment library
`mesh` and `row` take either a file shipped beside piece.json (`<file>.glb`, life size, its origin at the socket point, +Z out) or a library id. The game's library is the truth: `godot/art/armor/lib/<id>.glb`, built procedurally by `tools/armor/lib.py` (same frame convention). Ids: rows `rivet`, `stud`, `dome`, `grommet`; meshes `gem_round`, `gem_oval`, `boss`, `rune_plate`, `filigree_plate`, `buckle`. Marionette's kit pull copies the library for its preview; its own stand-ins are previews only.

## Hair
An armor index row may carry `"hair": "hide"` (default `"keep"`). While that piece is worn in the head slot, her hair mesh is not added (her scalp skin stays as is) and the game logs `her wear: hair hidden by <id>`. Set it on closed helms only; `arcanist.head` keeps her hair. Her show-helm toggle (`CharacterData.Headgear`, shot flag `--helm 0|1`) shows nothing at all in the head slot when off: neither an equipped head piece nor her calling's fill (`Wear.Look`'s `hide` set), and her hair then shows.

## Dye zones
Every entry in `godot/art/people/outfit_materials.json` has a `"zone"`: `metal` (steels and irons), `trim` (gold, claspgold, wiregold, rivetbronze, bronze), `leather`, `cloth` (cloth, twill, satin, gloss, sheer, fur, lace, velvet, down), or `none` (gems, amethyst, ink, bone). A new material entry needs its zone (a test fails without it). A piece's dye zones are the zones of its meshes' material suffixes (the part after the last `.`); a piece should have 1 to 3 (`DyeHelmTests` prints the exceptions).
A worn item carries `ItemInstance.Dye`: zone -> `"#rrggbb"` (sRGB), plus `"thread"` for leather's stitch thread. The shader recolors the albedo to the dye keeping its texture's variation (`dye`, `dye_amount` in `heroine_outfit.gdshaderinc`); fur and sheer take it on their tint at its own luma. Shot flag `--dye metal=#8a2a2a,leather=#203040` dyes every worn piece, over item dyes.
