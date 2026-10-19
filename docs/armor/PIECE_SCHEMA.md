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
- `mesh`: `{kind:"mesh", socket, mesh, scale, roll, offset, mat}`: one mesh at a socket; `roll` degrees about +Z; `offset` [x,y,z] m in the socket frame.
- `trim`: `{kind:"trim", rim, profile, width, height, inset, gap, mat}`: a raised band along a rim. `width` across the band, `height` above the shell surface (1-2 mm reads), `inset` m in from the rim (0 = on the rolled edge), `gap` the dark groove on each side between band and shell (default 0.001). Profiles: `rolled`, `rope`, `filigree`, `gold_band`.
- `paint`: `{kind:"paint", target:"shell", pattern, strength}`: `pattern` = `etch_<name>`, an etched pattern carried in the shell's surface detail (the game's shader renders it).

## The adornment library
`mesh` and `row` take either a file shipped beside piece.json (`<file>.glb`, life size, its origin at the socket point, +Z out) or a library id. The game's library is the truth: `godot/art/armor/lib/<id>.glb`, built procedurally by `tools/armor/lib.py` (same frame convention). Ids: rows `rivet`, `stud`, `dome`, `grommet`; meshes `gem_round`, `gem_oval`, `boss`, `rune_plate`, `filigree_plate`, `buckle`. Marionette's kit pull copies the library for its preview; its own stand-ins are previews only.
