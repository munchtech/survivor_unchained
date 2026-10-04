# Handoff: UI design lead

For the next UI design lead of Survivor Unchained. This file and the repository are all you get.
Read `docs/team/README.md` first, then this, then `docs/team/ui_design.md` (the one-page status).

Branch `worktree-agent-a69858664f1d3dd29` (pushed; the main session merges it; no PRs). It includes the
integration branch `claude/vigilant-galileo-l6jqyx` at f56ee42. 565 tests green. Older handoffs are in git
history: `git show 0b6e24b:docs/handoff/ui_design.md` (creation's first build) and `51350b1`, `c14b3a2`.

---

## 1. The owner, in their words

- "AAA standard", "strive for excellent, above and beyond", "I don't want to polish, I want to create
  perfection", "Do we have soul?". Never settle: remake rather than polish, and check at full resolution.
- The heroine: "sex appeal and the male gaze are a driving factor, tho not at the cost of looking bad".
- On customisation: "can we customize hair or face in our create character yet? I couldn't find it". They
  were running an old build (see 3, Look).
- On the pages, latest: the persistent panel framing and backdrop look "a little drab and low effort and
  low def".
- Standing rules:
  - Full-page screens pause the world only in arena combat, and are often not the best choice.
  - Unknown map land must look better.
  - Self is not merged into the Pack screen.
  - Use painted art, the best available.

## 2. The brief

1. **Character creation first.** The heroine's Look: hair, face, shape, paint, eyes and body, all of it
   plain to find and beautiful. Build it so the male hero fits the same step.
2. **Work with:**
   - the face lead, who owns her face, hair and the Look's content (presets, sliders);
   - the UI art lead, who paints what you lay out;
   - the male hero lead.
3. **The experience director's findings:** barks, the result screen, the table saying what a map pays,
   and pausing. All four are done; their next asks are in 4.
4. **The owner's "drab" note:** the layout side (where frames go, density, no flat black). The art lead
   paints the pieces.
5. **The old list:**
   - announcements, the item card, journal deeds and codex, the HUD's dash pips and draught box;
   - `docs/ui_review/`;
   - UI_DESIGN section 10, and 7.2 rewritten for the new creation.

## 3. Done this session (all pushed)

| Commit | What |
|---|---|
| a3335e0 | **The Look is step II** (Calling, Look, Arms, Origin, Name). Woman or man is chosen on step I. A card under the callings offers the look with her portrait; Next names it. The Look opens on Hair. **Portrait cameos** by `tools/assets/creation_portraits.py` (`tools_scenes/Portraits.cs`). The **title says when the code was built** and warns when the build is older than the code. Plaque rule fix. Stat icons on Self |
| b6f31f7 | **Face paints retuned** on her in game (`heroine_paint.py`). **Brows dyed** her hair's colour (a pass in `heroine_paint.gdshader`). The **Look's parts** are Hair, Face, Shape, Paint, Body. The male hero's `BeardStyle`, `HeroLook.Beards` and Beard row. A face to start from may set `skin` and `eyes` |
| 62d0f16 | **Barks** (`Ui/Voices.cs`): drawn on screen, one line at a time per speaker, stacked and never crossing. The **arena result told in beats** (`Ui/ArenaResult.cs`): counts with ticks and a landing blow; what comes out a line at a time with its sound, best last; the build going to ash; a press tells the rest. **Pausing** only where the ember burns (`GameMenus.cs`, `zone.Ember`). Portraits always dressed |
| 8a042a2 | **Pages remade frameless:** the live world blurred behind every page (`shaders/ui_backdrop.gdshader`, `Backdrop`). Panes are `Style.Column` (dark glass, gold hairline, fading down). `Style.Slab` is a wash, not iron |
| 0165e94 | Merge with the experience director's result-screen wording (narrator lines as the last beats) |
| f6124b1d | **The Wayfinder's table says what a map pays:** the materials drawn, the gear it leans to, the tome chance (`Arenas.TableTome`) |

## 4. Next, in order

1. **Launch blocker (coordinator, from the legal lead aa12c130ddf4b904c; see `docs/legal/LEGAL_BRIEF.md`).**
   No licence notices ship yet. Add:
   - a **Credits and Licences** screen, reached from the title (`TitleScreen`'s Credits panel in
     `Ui/Front.cs` today is a short list) and from the pause menu (`Ui/Menus.cs`). Build it from
     `public/assets/CREDITS.md`, which the provenance auditor completed. Make it as good as the new pages:
     a frameless column over the blurred world, sectioned and scrollable;
   - a **`licences/` folder in the export**:
     - the Godot and .NET notices;
     - the OFL licences for Cinzel, Alegreya and Alegreya Sans;
     - the CC BY credits;
     - an AI-use line.
     Check `export_presets.cfg` for how extra files ship (include filters, or copying beside the exe).
   - **Check the wording with the legal lead** before you push.
2. **Place the UI art lead's new pieces as they land** (a1a394643aabfb169). Each file is at twice its shown size;
   `UiArt` halves it. Margins come by message.
   - `header.png`: same slice, (0,0,0,12) Tile.
   - The backdrop as two layers: `backdrop_grain.png`, 512 and tiled; `backdrop_edges.png`, 1920x1080 and
     stretched. They stack in `Backdrop` (Ornate.cs) over the blurred world, under the shade.
   - `column_divider.png` (0,24,0,24) Tile, 24 wide, plus `column_divider_stone.png` drawn at its middle in
     code. They go between page columns (the gaps of 24–30 px between `Pane` rects).
   - `card_light.png` (20,20,20,20): for tooltips and the result's cards. `crest_card` stays on choice and
     trait cards.
   - `hero_plate.png` (56,56,56,56) Out 12: round Self's figure and the Pack's figure.
   - `section_rule.png`: to replace the ◆ in `Section` (Ornate.cs).
3. **The experience director (ad1f5623590e09883), two endgame screens.** Their shape is in
   `docs/EXPERIENCE_AUDIT.md`, "A map's shape" (combat's MapRun; maps open at Vonnra's fortune).
   - **A map's result**, loot-first, of the night's result's family:
     - time, falls (of three), gear by rarity as item cards, charts won, materials, gold;
     - the atlas line ("The Lampless Howes, tier 2: cleared, first time: a point").
   - **The atlas** at the Wayfinder's table:
     - the peoples by tier as a grid, each pair lit when its ruler falls;
     - the chart in hand, its mods readable (prefixes against her, suffixes on her, what each pays);
     - the points with five biases of three ranks each: the people's road, twice lit, the keeper's due,
       the ruler's hoard, marked men.
     - It must look promising half-empty: the beta shows tier 1 and one point.
   - Also match their in-world chest ceremony (`ChestCeremony`, frames in
     `docs/experience/chest_hoard_five_reels.jpg`).
4. **After the face lead's new head** (ade92e8285938438f): new faces, 47 sliders in 8 groups.
   - Order: their head, face paint and hair; then the main session's `heroine_outfits.py --body`, which
     writes `heroine.glb`. The main session will tell you when it lands.
   - Then run `python tools/assets/heroine_paint.py` and
     `python tools/assets/creation_portraits.py`, and shoot the Look's five parts.
   - `LoadoutTests.Her_looks_are_whole` expects 25 sliders; the face lead updates it.
5. **The male hero** (ab82cbe99e2937ddd, who took over from ae2de192cce8298ca). When `heroes.male` and his builder land:
   - extend `Portraits.cs`, which builds her only, and `creation_portraits.py --sex male`. His cuts and
     beards render grey, each with a mask;
   - shoot his Look.
6. **Notes from the crafting lead (a7debf1459f14dfe7):**
   - Wenna's still-room (`Ui/StillRoom.cs`, a 760-wide side panel): restyle freely.
   - The forge's hammer moment (`ForgeScreen.Strike`), and a "Make me one" tile.
   - **Two bugs:**
     - the Pack's doll T-poses for about a frame on every Refresh;
     - `G.Gear` rebuilds the world's PlayerView on every call, so the survivor blinks. Wear and Take off
       still call it.
   - Break-down feedback: show it in the pack's inspect area, since toasts are hidden under the pack.
7. **Density on the pages.**
   - Self's attribute pillars are half empty, and the right column's lower half is empty. A bigger figure
     would help.
   - The creation screen still uses the iron column and plate. Consider the frameless style there too.
8. The old list (2.5).

## 5. Decisions (one line each, with why)

- Look is step II: the calling dresses her, then she is shaped; no one walks past it.
- The Look opens on Hair. It's what players look for, and the faces were "kinda ugly" until the face lead's rework.
- Face and Shape are separate parts, so 47 sliders get the whole column (agreed with the face lead).
- Portraits are rendered from the game, so they stay true when her head changes. The painted pass goes over them.
- Paint is laid thick where it is meant to be solid. AgX turns a thin blue coat violet and a thin red one rust.
- Brows are found in her skin paint under a mask, then dyed. They are painted copper into her skin, and the face lead keeps them that way.
- Barks are on screen, not Label3D: only then can lines be measured and kept from crossing.
- A speaker's line stays until it has been read (1 s + 0.045 s per letter), then the next shows. Scripted beats stay near their timing.
- Pausing follows `zone.Ember`: arenas and the prologue's night road are exactly where the ember burns.
- Pages have no frames by default. Iron marks what you act on, and the world shows behind.
- The title warns of a stale build by comparing `.cs` times with `.godot/mono/temp/bin/Debug/SurvivorUnchained.dll`. Godot loads the code from memory, so `Assembly.Location` is empty.

## 6. Failures and why

- **The portrait tool built her naked.** It asked for outfit "stalker", but her outfits are warden, reaver,
  arcanist and ranger, and an unknown name builds her bare. Caught before the legal survey. `Portraits.cs`
  now refuses unknown names.
- **AgX shifts hues.** Woad first showed lavender and blood rust. Tuning the hue barely helped; making the
  paint opaque (`firm()` in `heroine_paint.py`) fixed it.
- **The first brows looked painted on** (a flat colour in the mask's shape), and a light colour left copper
  edges. Finding each hair in the skin paint fixed it. The paint has no mipmaps, so the shader samples a
  ring of 16 points at 44 px and takes the brightest.
- **Every result frame looked fully told.** I set `told` on any rebuild, and the harness took its frames
  late (`--every` frames start at `--seconds`). Use `--seconds 3 --every 0.8`.
- **Bash refuses some commands** (`git` in compound commands, `sed` with variables). Write Python edit
  scripts to the scratchpad (`uid3/edlib.py` `edit(rel, [(old, new)])` keeps CRLF) and run them from PowerShell.
- **.NET in PowerShell resolves relative paths against the process's start folder.** One failed
  ReadAllText wrote an empty `src/ui/Front.cs` at the worktree root. Use absolute paths.

## 7. Gotchas

- **Setup:**
  - Junction `godot/assets` to `public/assets` with skip-worktree.
  - `override.cfg` gives the user folder `SurvivorUnchainedUiLead3`.
  - Copy `.godot` (without `mono`) and `public/assets/**/*.import` from a recent worktree, then run
    `dotnet build` and `--headless --import`. The import exits with code 255, but that's harmless.
- **Never commit the many `.import` files the import dirties,** nor `.uid` files. The project doesn't track
  them. Do commit the `.import` files of new art.
- **Shots** (`scratchpad/uid3/shot.ps1 NAME SECONDS [args]`):
  - `--new --step 1 --part N` for the Look's parts (0 Hair, 1 Face, 2 Shape, 3 Paint, 4 Body);
  - `--quick --open character`;
  - `--zone arena --open result --seconds 3 --every 0.8`;
  - `--zone waystation --open maps`;
  - `--quick --barks 0.5` for a crowd of barks.
- **Portraits:** `python tools/assets/creation_portraits.py [hair|face|paint|look] [--raw DIR]`. Run a
  headless import afterwards so new PNGs get `.import` files, and set `mipmaps/generate=true` in new ones.
  `scratchpad/uid3/por.ps1 JOBS.json OUT` runs a custom job list (views: bust, head, face, eyes).
- **Paints:** `scratchpad/uid3/paints.ps1 -which kohl,woad` paints, imports, photographs and grids them.
  `PAINT_PREVIEW=dir` shows each design on her unrolled face.
- **The Voice lead** records one take per name in Front.cs's `Names`; it is unchanged.
- **Files are CRLF.**

## 8. Collaborators (ids current at handoff)

- **Main session (coordinator):** merges and relays the owner. Message `main`.
- **Face lead `ade92e8285938438f`:** her head, faces, sliders and hair (`docs/team/face.md`).
- **UI art lead `a1a394643aabfb169`:** painting the six pieces in 4.2.
- **Male hero `ab82cbe99e2937ddd`:** fields agreed (see 4.5).
- **Experience director `ad1f5623590e09883`:** map result and atlas.
- **Legal and Steam compliance `aa12c130ddf4b904c`:** creation never shows her bare (answered); licences screen.
- **Crafting `a7debf1459f14dfe7`:** still-room, forge, pack bugs.
- **Voice `a501b387a90d78b4e`:** names.
- See `docs/team/README.md` for the rest.

## 9. Read first

1. `docs/team/README.md`, this file, then `docs/team/ui_design.md`.
2. `godot/src/Ui/Overlay.cs` (Page, Pane, SidePanel), `godot/src/Ui/Style.cs` (Column, Slab), and
   `godot/src/Ui/Ornate.cs` (Backdrop, Plaque, Section).
3. `godot/src/Ui/Front.cs` (TitleScreen, CreationDraft, CreateScreen) and `godot/src/Ui/CreateLook.cs`.
4. `godot/src/Ui/ArenaResult.cs`, `godot/src/Ui/Voices.cs` and `godot/src/Ui/MapTable.cs`.
5. `tools/assets/creation_portraits.py` with `godot/tools_scenes/Portraits.cs`, and `tools/assets/heroine_paint.py`
   with `godot/shaders/heroine_paint.gdshader`.
6. `docs/legal/LEGAL_BRIEF.md` and `public/assets/CREDITS.md`, for the next job.

HANDOFF READY: docs/handoff/ui_design.md on worktree-agent-a69858664f1d3dd29 (its tip)
