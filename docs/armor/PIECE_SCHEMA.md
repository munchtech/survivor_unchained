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

## Dye zones (the P6 contract, armor lead 7, 20 Oct)
A piece has no zone field: **its zones come from its materials.** Each mesh of a piece is one material (mesh names end in `.<material>`), and every entry in `godot/art/people/outfit_materials.json` carries a `"zone"`, one of exactly five names:
| zone | materials (by the entry's `kind` and name) |
|---|---|
| `metal` | kind `metal`: steel, darksteel, blacksteel, iron, rust |
| `trim` | gold, claspgold, wiregold, rivetbronze, bronze, and `thread` (stitching) |
| `leather` | kind `leather` |
| `cloth` | kinds cloth, twill, satin, gloss, sheer, fur, lace, velvet, down |
| `none` (never dyed) | gems (`gem_*`), amethyst, ink, bone |
- The default is no dye: a piece draws as built (`dye_amount` 0 is bit-identical to the undyed shader).
- A new material entry must name its zone (`DyeHelmTests` fails without it). To make part of a mesh a different zone, give that part a different material: there are no painted masks.
- A piece should end up with 1 to 3 zones. Today `warden.top` and `warden.belt` have 3 (leather, metal, trim). The one-zone pieces are arcanist.gloves, arcanist.head, arcanist.legwear, reaver.collar, reaver.skirt and reaver.cloak.
- **A dye** is `zone -> "#rrggbb"` (sRGB), held per worn item in `ItemInstance.Dye`. One extra key, `"thread"`, sets leather's stitch-thread colour directly. Marionette's workshop may export a default dye in piece.json as `"dye": {"metal": "#..", "leather": "#.."}` (same shape; optional; the game reads it as the item's starting dye once the studio lands, not yet).
- The shader recolors the albedo to the dye's colour, scaled by the texel's luma over the material's mean, so the texture's variation stays (`dye`, `dye_amount` in `heroine_outfit.gdshaderinc`). On metal it sets the plate's reflectance colour. A dyed `trim` takes the dye instead of the aged-brass tone. Fur and sheer take it on their tint at its own luma. The shot flag `--dye metal=#8a2a2a,leather=#203040` dyes every worn piece, over item dyes.

## Free meshes: the import contract (`tools/armor/import_mesh.py`, built after milestone B; this contract is fixed now)
One import serves Marionette's authored meshes and artists' meshes (Blender or Maya). The game fits the mesh to her: her weights, the clearance push-out, the skin tuck, the gameplay and shadow LODs, the sockets and rims, and the armor index row. So the source mesh carries shape and materials only.
- **Files:** `generated/to_game/armor/<id>/piece.json` with `"style": "mesh"` and `"params": {"file": "<id>.glb"}`, plus the mesh file beside it. The format is glTF 2.0 binary (`.glb`, preferred). `.fbx` and `.blend` are also accepted: the import opens them in Blender and treats them like the glb. Every other piece.json field is as above (`id`, `name`, `slot`, `tier`, `covers`, `hold`, `adorn`). `material` is ignored, because materials come from the mesh.
- **Body and pose:** model it around HER BODY IN ITS REST POSE: `godot/art/people/heroine.glb` (Marionette's kit pull copies it), unposed, as that file stands. It is not a T-pose of another rig, and nothing is posed. Build against the current body. The import stamps the body hash and refuses a mesh made on an older body unless it is re-fitted.
- **Units and axes:** metres, glTF axes. +Y is up, her front faces +Z (her chest is at z about +0.11), and her left is +X. She stands with her feet on y = 0 and is centred on x = 0. Apply all transforms (identity object transforms). A file whose bounds don't overlap her body is refused with the offset it found.
- **Skeleton:** an unskinned mesh is the normal case: the import transfers her weights from her skin. If the mesh is skinned, it must be skinned to her skeleton (bone names as `tools/anim/data/heroine_skeleton.json`, the same rest pose). Even then, the import replaces the weights by default. `"params": {"keep_weights": true}` keeps them, for an artist who weighted on purpose.
- **Rigid parts:** an object or mesh whose name ends in `_rigid` (a plate, a buckle, a gem) rides one blend of bones taken from her skin at its centre, so it never bends. Everything else bends with her.
- **Materials and dye zones:** each material slot's NAME must be an entry in `outfit_materials.json` (steel, darkleather, gold, gem_garnet ...). That name gives the shader kind and the dye zone (above), so zones are tagged by material choice: no masks or vertex colours. Textures in the file are ignored for now; the game's materials draw it. An unknown material name is refused with the list of valid names. Keep it to 2-3 zones and at most 2 draws (materials) where possible (look bible 11).
- **Clearance and envelope:** the mesh may sit on or near her skin. The import pushes it out to its slot's band (lift plus thickness) and reports how far it moved anything. A piece that must pass under or over another follows the slot order (`slot_map.json` "order", the garment tuck), not hand offsets.
- **Budgets:** 30k triangles cap for a large piece (20k typical), 15-20k for a pair, 15k for head, 8k for small pieces. The import makes the LODs (gameplay at most 25%, shadow at most 10%). Mirror paired pieces yourself, or model one side and set `"params": {"mirror": true}`.
- **No flowing parts:** capes, swinging skirts and hanging trims are refused for now. A loose part must be `_rigid` or lie on her.
- **His cut later:** the same contract on his body file, when his model is replaced. A design ships as two files, `<id>.glb` (hers) and `<id>.him.glb`, one item and two cuts, so no cut is shared between bodies.
