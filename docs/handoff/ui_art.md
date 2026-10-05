# Handoff: the interface's art (UI art lead)

For the next agent carrying on the UI art of Survivor Unchained. Read these in order:
1. `docs/team/README.md`: the team's bar, how we work, safety, the roster, and **taking turns for heavy work**.
2. This whole file.
3. `docs/team/ui_art.md`: the one-page status.

Earlier handoffs are in this file's git history (bfa7bdb1, a2bd171). What still matters from them is folded in here.

- **Branch:** `worktree-agent-aa9c11f1e40170a4d`, at 5b815c9d plus the handoff commit. 661 tests are green. The main session merges it.
- **Worktree:** `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa9c11f1e40170a4d`.

**Before any build, copy the cached paintings and renders.** They're about 2 GB, ignored by git, and every build reuses them.
- Copy `...\worktrees\agent-aa9c11f1e40170a4d\tools\comfy\out\uiforge\` into your own worktree's `tools/comfy/out/uiforge/`.
- Use `robocopy /E`. Its exit code 1 means "copied".
- Copy it; never move or delete it.

**Also copy `godot\.godot`** from this worktree (or any recent one), skipping `mono`. A fresh `--import` of the whole project:
- took hours with other agents importing at the same time;
- crashed from lack of memory three times.

With the cache, the import only redoes what changed.

---

## 1. The owner's bar (quotes)

- "I don't want to polish, I want to create perfection." "We are striving for perfection." AAA, "above and beyond".
- "Do we have soul?": unique to this world, never generic.
- On the pages' persistent framing and backdrop (before this session): "looks a little drab and low effort and low def".
- **On this session's result, the latest and the one that rules:**
  - "those borders are just ugly, adding more of them dosn't make them better";
  - the inventory and character page look "ai looking" and "not rooted in ui research";
  - the arena cards (the draft's cards) "look pretty cool": keep them.

## 2. The brief, in full

The coordinator's (main session's) orders, latest first.

**A. The restraint rule (now the law):**
- **Frames:** at most one ornamental frame per screen, the outer window.
- **Inside it:** quiet tonal panels and thin rules.
- **Slots:** empty slots are subtle recessed tiles; rarity colour goes only on filled slots.
- **Materials, not ornament:** the outer frame should feel grounded in the world (worn iron, leather, bound vellum), with less filigree on everything.
- **The backdrop:** depth and texture at 1080p and 1440p, not flat muddy brown.
- **Accent:** one accent colour (ember), used for meaning only.
- **Research:** study how Diablo IV, PoE 2, Last Epoch, BG3 and Hades II restrain their ornament. Study only: never copy their art.
- **Greyboxes:** UI design (aab47bfdab5955dac) is redoing Self, Pack, Storeroom and Trader from research as greyboxes. Put art on them **only after the coordinator and the owner approve the layouts**.

**B. On the reduced Self crop:** "The restraint is the right direction." But the panels are "plain to a fault": flat dark rectangles read as a generic web dark mode. Give them the world through material:
- a faint grain of vellum or leather inside;
- worn light on the top edge;
- a slightly warmer, more varied tone than the page.

Not frames. Next in the same restraint: the medallion rings, the iron tabs, buttons and keycaps, and the Pack's side plate. Don't apply yet: the tall empty pillars and the six identical empty trait boxes are a layout problem, and the layout is changing.

**C. The original list for this session:**
1. Render the hero plate and light card. **Done.**
2. Import the new page images. **Done.**
3. Send the slice margins to UI design. **Done.**
4. Before/after shots at 1920x1080 for the owner. **Done;** the verdict was A.
5. Then:
   - Crashing Leap's new concept (**drafted, not painted**);
   - the crafting lead's three item icons (**refitted; the flask still needs a repaint**);
   - the legal lead's pre-launch icon check against other games (**not started**).

**Standing rules:**
- **Tests:** `dotnet test` in `godot/tests` before every commit.
- **Commits:** commit and push your own branch at milestones. Open no PRs.
- **Spelling:** British.
- **ComfyUI** is shared. Batch your paintings and `POST /free` after each batch. Never kill it.
- **Taking turns:** heavy work takes a turn.
  - Run `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take gpu "ui art: <job>"` for ComfyUI or big Blender renders.
  - Use `take godot ...` for Godot shots.
  - Exit 1 means busy: do light work and try again.
  - Give the turn back the moment the job ends; giving back the GPU frees ComfyUI.
  - Keep batches under an hour.
- **Handoff:** at about 500k tokens.

## 3. The soul (locked; `docs/UI_ART_BRIEF.md` 2.6)

Brannoc's iron, the binders' gold, the Morrow's light:
- **The iron:** smith's work from the Waystation.
- **The gold:** the binders' twisted wire, and their square coin with its round hole.
- **The light:** the ember asleep in the holes, awake where there is power.
- **The page:** this session's addition is "the day's book", written on the binders' black vellum.

Under the restraint rule, the soul has to live in **material and light, not in ornament everywhere**.

## 4. What is in the game now (merged by the main session from this branch)

| piece | file | notes |
|---|---|---|
| header | `frames/header.png` 1024x200 | gilt morocco: a twisted gold wire roll with coins, a forged rail with wire. **Ornate: the kit replaces it** |
| foot band | `frames/footer.png` 1024x136 | the header's twin. UI design's hook lays it at y 1016, before the content, with its top 16 px quiet; the prompts sit at y 1044 |
| ground | `page/vellum.png` 1024x1024, tiled | black vellum laid at 0.9 alpha over the blurred world, only on full pages (`Backdrop(page: true)` in `Overlay.Page`). **Keep** |
| band shades | `Ornate.cs` `Backdrop.Shade` | the header's shade falls down the page, the foot band's rises. **Keep** |
| backdrop shader | `shaders/ui_backdrop.gdshader` | a cubic B-spline read of the blur's mips (the old bilinear read was blocky, the "low def"); grades shadows into cool iron and keeps light warm; `shade` has a default. **Keep** |
| page light | `page/backdrop_edges.png` | cool smoke at the edges; the ember low and orange under the last 160 px above the foot band (UI design asked it be quieter). **Keep** |
| column | `frames/column.png` (12,16,12,8), stretched | gilt double rules with coins, fading down. **Ornate: the kit replaces it** |
| hero plate | `frames/hero_plate.png` | strap iron, wire, coins. **Ornate: the kit replaces it** |
| light card | `frames/card_light.png` | dark vellum with an iron bead, on the map result's finds. Likely too framed under the rule |
| item icons | `icons/item/{flask,moon_draught,fur_braid}.png` | refitted from 0.98 to the set's 0.82 fill. The **flask still drifts**: cool flat light, and a stamped mark that reads as a letter. Repaint it |

UI design (a26f87c39952dcd9c, the earlier lead) approved and wired the column hook (`Style.Column` → `UiArt.Frame("column", ...)`) and `Backdrop(page: true)`. The kit swaps art by the same names, so it needs no code.

## 5. The reduced kit (built, NOT applied) — your main line of work

`tools/uiforge/kit.py` draws flat pieces in numpy at 2x. Nothing here needs a render, except the plain bands.
- `python tools/uiforge/kit.py` writes to `tools/comfy/out/uiforge/kit/` for judging.
- `python tools/uiforge/kit.py --apply` lays the pieces over the named frames. It also moves `column_divider_stone` into `kit/dropped/`, which removes the stone.

The pieces:
- **tonal** (raised): pillar 212x364 with Out 12; slab 64 with its light within the 14 px slice; hero_plate 256 with Out 12.
- **recessed**: well and slot.
- **column**: shade only.
- **rule**: the gutter.
- **header and footer worn plain**: `pages.header_plain` and `pages.footer_plain`, via `binding(..., gilt=False, rail_wire=False)`.

Seen on Self:
- `godot/.shots/kit_crop_self.png`: ornate left, kit right, at 1:1.
- `kit_beforeafter_self.png`: the integration branch against the kit.

The coordinator approved the direction.

**What to do next, in order:**
1. **Material in the panels**, per brief B:
   - a faint vellum or leather grain inside each tonal panel, at 1:1. Tile it, or let the panel stay translucent over the vellum, which it already is at 0.42. Either way the grain must not stretch.
   - worn light on the top edge;
   - a warmer, more varied tone (fbm variation, a touch of oxblood).
   Judge at 1080 **and 1440**.
2. **Pare the rest** to the same restraint:
   - the medallion rings (`medallion/ring.png`, `hud/medal_level.png`, and the attribute medallions drawn by `Medallion` in `Ornate.cs`; check what's art and what's code);
   - tabs, buttons and keycaps (`frames/tab*.png`, `button*.png`, `keycap.png`);
   - the Pack's side plate (`frames/plate.png`, the panel's one outer frame: worn iron or leather, plain);
   - slots: an empty slot is a recessed tile; `slot_0..5` keep rarity colour only on filled slots.
3. **Wait for the greyboxes** (aab47bfdab5955dac). Then apply, shoot Self, Pack, Storeroom and Trader at 1080 and 1440, and send before/after crops to the coordinator.
4. Don't touch the draft's cards (`card_0..5`, `card_evolve`): the owner likes them.

## 6. Other open work

- **Crashing Leap (`leap`)** is weak at 90 px: a grey arc on a dark disc.
  - `emblems.d_leap2` is a second concept (a hard-edged arc into a burst, with a crown of dark slabs). Its guide (`tools/comfy/out/uiforge/emblems/leap2_guide.png`) still fogs into cream, so it is not painted.
  - To fix: cut `e.glow`, drop the light fan rays, and make the slabs near-black against a small hot burst. Ground cracks lit gold (`crack_web`) read better than rays.
  - Leap is the Reaver's (barbarian) leap-slam. Its affix "of the Long Fall" leaves the ground broken, so the broken ground is core.
  - Paint with `emblems.paint_many(["leap2"], 0.55, 1340)` (take the gpu turn first). Pick it into `PICKS`, `fit`, and judge at 128, 44 and 17 px on a dark disc.
- **The flask** (`items.py`): add a T2I entry (a pewter hip flask in a stitched leather sleeve, warm light from the upper left, **no marks or letters**), paint, then `fit` at 0.84 → 0.82.
- **The legal lead's pre-launch check:** lay every shipped icon and frame side by side with the named commercial sets, and remake any close to a specific one.
  - The legal lead is now aab20546fe06daa89 (see the roster).
  - Prompts never name a product.
- **From earlier handoffs, still open:**
  - the soft icons in the old painted family (zone_*, nova_*, tether2, siphon, herd_great/_hunt, command, kindling, living_flame, scent, execute, beam_*);
  - the stat marks' wiring (UI design's);
  - `Plaque._Draw` mirroring;
  - hover-state shots;
  - portrait cards for creation.

## 7. Decisions (why)

- **One frame per screen; material over ornament.** The owner's verdict. Ornate frames nested in a frame read "AI fantasy".
- **The page's ground is black vellum** with the world faint through it. The blur alone was low in definition and brown, and a crafted surface at 1:1 gives detail at any resolution. It fits the soul: the day's book, written in gold on black, like the black books of hours.
- **The blur shader uses a cubic B-spline over the mips.** Bilinear reads of small mips are blocky. The grade is cool iron in the shadows and warm only in the light, because the old warm tint plus grey made everything brown.
- **The ember stays low and orange**, under 160 px above the foot. Higher and redder, it washed the page in oxblood (UI design's catch).
- **Relief renders are keyed by a hash of their inputs** (`relief.Relief.render` writes a `.key`). A failed Blender run (out of memory) used to hand back the previous picture silently. Now you can re-grade after a render without a Blender pass.
- **`pages.regrade`** grades one material's pixels in linear light after the render. The softbox's sheen greys dark hide and vellum, and changing the albedo alone can't take that out.
- **Headers and bands are exactly periodic.** Use `pages.tiled`: make the fields over one tile and tile them, with wire pitches that divide the tile. The middle of three rendered tiles is then cut out, with no seam to blend.

## 8. Failures and why

- **Header v2's first render:** a black stripe from NaNs (`sin` slightly below 0 raised to 0.7). Clip before taking powers.
- **Blender ran out of memory** (`Malloc returns null`) while ComfyUI held 26 GB, and the stale PNG came back as if new. That's why renders are now keyed and stale outputs deleted.
- **Godot `--import` crashed** with a null `mem` on large glTF scenes under memory pressure, three times. Copying a recent `.godot` cache and retrying when commit memory was over 12 GB worked (`scratchpad/import_when_free.ps1`, a loop).
- **Lamp pool on the vellum** (a warm radial lift): it turned the page grey-brown again. Removed. Broad warm light over violet-black reads as mud; only concentrated, saturated light reads as light.
- **Vellum v2 with ridged-noise creases** read as cracked leather or dried mud. v3 has soft cockle and mottling instead.
- **PowerShell gotchas:**
  - `git commit -m` with a here-string containing double quotes split into pathspecs. Use `git commit -F <file>`.
  - `Set-Content` writes ANSI; use `[IO.File]::WriteAllText` or the Edit tool.
- **Leap2's guide fogs.** The school's halo and the strong light fan flood it; see section 6.

## 9. Gotchas

- `godot/assets` must be a junction to `public/assets`. A fresh worktree checks it out as a symlink text file. Remove it, then `New-Item -ItemType Junction`, then `git update-index --skip-worktree godot/assets`.
- **Stray `.import` changes:** Godot rewrites many `.import` files. Most are autocrlf noise with an empty `git diff`. Stage only your own paths, and restore real stray changes (e.g. `godot/art/people/...`) with `git checkout --`. Filter `git status` (`Where-Object { $_ -notmatch '\.import$|\.uid$' }`), or the output floods.
- **Imported files win over disk:** `UiArt.Tex` loads the imported resource when a `.import` exists, else the PNG from disk. For a clean "before", move a piece's PNG **and** its `.import` away.
- **Shots:** `python tools/uiforge/shots.py <screens> --prefix P` writes to `godot/.shots/P_<screen>.png`, which is ignored. It imports first.
  - Take the godot turn first.
  - Build C# first: `dotnet build godot/SurvivorUnchained.csproj`.
- **My viewing scripts** live in my session's scratchpad. Each is a few lines of PIL, so recreate them as needed:
  - `look.py` composites over a colour;
  - `sheet.py` makes contact sheets;
  - `try_piece.py` renders a `pages.py` piece to a scratch path, not into the game;
  - `refit_items.py` handles the 0.82 fill.
- **The roster changes.** UI design for the page greyboxes is now **aab47bfdab5955dac**. The earlier UI design lead is a26f87c39952dcd9c (credits, map result, atlas, Self density). Check `docs/team/README.md`.

## 10. Collaborators

- **Coordinator / main session:** `main`. It approves art going onto layouts, with the owner.
- **UI design:**
  - aab47bfdab5955dac: the greyboxes for Self, Pack, Storeroom and Trader.
  - a26f87c39952dcd9c: owns `Overlay.cs`, `Style.cs` and `Ornate.cs` changes; approved the vellum and column hooks.
- **Crafting lead:** a7debf1459f14dfe7.
- **Legal lead:** aab20546fe06daa89.

## 11. Read first

1. `docs/team/README.md`
2. this file
3. `docs/team/ui_art.md`
4. `docs/UI_ART_BRIEF.md`: 2.2 materials, 2.6 the soul. Read them under the restraint rule.
5. `tools/uiforge/kit.py`, `pages.py` (`binding`, `vellum`, `backdrop_edges`, `regrade`, `tiled`), `relief.py`.
6. `godot/src/Ui/UiArt.cs` (frames and slices), `Ornate.cs` (`Backdrop`, `OrnateBox.ArtId`, `Medallion`), `Style.cs` (`Column`, `Slab`), `Overlay.cs` (`Page`).
7. The shots in `godot/.shots/`:
   - `b0_*`: before (the integration branch at the session's start);
   - `a8_*`: the ornate pass;
   - `k1_self`: the kit;
   - `kit_crop_self.png`.
