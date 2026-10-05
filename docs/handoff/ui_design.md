# Handoff: UI design lead

For the next UI design lead of Survivor Unchained. Read, in order:
1. `docs/team/README.md`: the owner's bar, how we work, and taking turns.
2. This page.
3. `docs/team/ui_design.md`: the one-page status.
4. `docs/design/UI_RESEARCH.md`: the approved direction.
5. `docs/ui_review/build*/`: what's built, as the player sees it. build6 is the latest.

**Branch:** `worktree-agent-a4fdbc49786ba8b7f`, pushed at a724ea70. It has integration, loot, crafting and UI art merged, and 729 tests are green. The main session merges it; open no PRs. Older handoffs are in `git log -- docs/handoff/ui_design.md`.

## 1. The owner, in their words
- **The bar:** "we are striving for perfection." Also: "have the ui dev continue to work on unnecesary dead space and good symetry... it was supposed to have done a ton of research".
- **On boxes:** "the stat stuff in blocks still dosn't work for me even though you made them much shorter they are still ai boxes." No dark rounded box may hold data, at any size.
- **On full pages:** "we like to see our beautiful game." Panels sit over the live world; a page that stays is "slightly see through".
- **On fades:** "the fade away isn't needed". The whole backdrop gets an "ever so slight transparency".
- **On notices:** they "could be transparent and stylized". Tips should be "a centered attention grabbing thing... just stylized readable text".
- **On the chain:** "thats the kinda soul were lookin for. SOUL". The tab chain was "a little wimpy", so UI art made it heavier, with heated links.
- **On the ledger:** "more like a dnd top bit which is much better". A placed point shows its projected stats.

## 2. The brief
1. The approved layouts in the game: Self, Pack, Storeroom, Trader, then the Bench. **Done.**
2. The loot screens: the filter, tier colours, ground labels and the legendary pointer. **Done.**
3. UI art dresses the layouts by name (a0bff3ffe4d3ad748). This is ongoing.
4. From the earlier brief:
   - day dial, **done**;
   - the fall's choices, **done**;
   - map result, **done**;
   - Wayfinder's table and atlas, **done**;
   - title focus, **done**;
   - portraits, **waiting**;
   - the male Look, **waiting**.
5. Judge every screen at 1920x1080 and 1440p, and send the main session pictures at milestones.

## 3. Built (where to look)
- **Kit.cs** holds the plain kit, with every piece asking UiArt by name:
  - Window, PanelBox, WellBox, TileBox, RuleH;
  - Head (a section head plus its rule);
  - Tabs, Word (an action set as type), Round, Chip, Prompts;
  - Balance (even line breaks).
- **Overlay.cs:**
  - `BookPanel` is the book's 900 px right panel, with one 28 px margin and a 93% ground.
  - `Fitted` is a counter panel.
  - `TipBeside` opens cards beside an item.
  - `PromptsOnWorld` lays the foot's prompts on a soft shade.
  - `CameraShift`, `CameraNear` and `CameraLook` frame the world for a screen.
- **The screens:**
  - SelfScreen.cs: the ledger and coals, the trait track, HeldWord, the lamp.
  - PackScreen.cs: PackBlock, the doll, the kit switch.
  - FilterPanel.cs.
  - Counters.cs: the storeroom and shop.
  - ArtsScreen.cs.
  - MapTable.cs: the table and atlas as parchment sheets.
  - MapResult.cs and ArenaResult.cs, built on `TellingScreen.ResultPanel/Tally/Columns`.
- **Items:** ItemViews.cs holds tiles, cards, `TierColour` and `KindLine`; CardBox gives soft edges; TileMark covers the up, anvil, link and new marks.
- **World type:** WorldType.cs has Notice (toasts), TipLine, FallChoices and Lettering. GroundLabels.cs and EdgeMarks.cs (the legendary chevron) sit alongside.
- **Elsewhere:** ChainTabs.cs (with Title), Coals.cs (Coal, CoalDish, Lamp), DayDial.cs, and the bark-over-plate fix in Voices.Place.

## 4. Next
0. **Experience's verdict** (a9f0d6c64d891d56d, at 2378e165). Tips as type and the ground labels passed. To do:
   - **Map result, "What came out":** a row of 40 px icons over a half-empty column. Lay the finds out large, each named in its tier colour (as PoE2 and D4 lay out a reward), or close the dead space. See `MapResult.cs` and `TellingScreen.Columns`.
   - **A loss's quest toast prints over the fight before the fall is staged.** Hold notices while a fall or loss is staged, using experience's `GameHud.HoldToasts` (on their branch, made for a chest's opening).
   - **The dial at the Waystation by night,** which is near-black: check it stays readable (`--clock` past dusk, at 1080 and 1440).
   - **The fall's card wasn't judged:** the pilot rose her first. Judge it from build4, or shoot `--choose` with no rise left.
1. **The Journal.** The open book stays, at an 85% ground with a lighter blur. The chain tabs are done, but its empty pages are dead space, and the right page has a placeholder "!" watermark. Fold its four section tabs into Kit.Tabs-style type and let the book hug its content.
2. **Map screen (MapScreen.cs).** Give it the same self-critique pass; it still uses old-style rows and boxes in its side list.
3. **The kit switch.** It's built but not seen on screen: it needs a save with a coal or Mark owned. `--nightkit` alone doesn't make `Kits.Shown` true.
4. **Portraits.** When the face lead says her head has landed, re-run `tools/assets/heroine_paint.py` and `tools/assets/creation_portraits.py`, then shoot the Look.
5. **The male hero's Look.** Waits until the male hero lead (ab82cbe99e2937ddd) resumes: extend `Portraits.cs` and `creation_portraits.py --sex male`.
6. **Old screens not yet on the rules:** pause, rest, chapter, credits, creation and the draft. The owner likes the draft cards.

## 5. Decisions (each with its why)
- **No boxes holding data:** type on the page, fine rules, world objects (coals, a lamp, a chain, held words). This is the owner's "ai boxes".
- **No fades:** panels end cleanly and are slightly translucent (the owner).
- **Panels over the world, not pages.** The book (Pack, Self, Arts) is one right-hand panel; counters are two fitted panels with the keeper between them. Only the Journal and Map stay full pages.
- **A spend previews everywhere until KEEP:** in ember, never green. It shows the projected stats.
- **What can't be undone is held** (HeldWord, HoldButton), never confirmed by a second dialog.
- **Colour means tier, state or the one action.** `ItemViews.TierColour` is the single table.
- **Self-critique at 1:1 before sending:** dead space, grid, symmetry, boxes, fades, type and placeholders. Send the findings list with each batch of shots.

## 6. Failures, and why
- **Shoot-look-shoot loops wasted turns.** Batch every shot a check needs into one Godot turn.
- **New art loaded as missing:** it came through git as `.import` files without a run of the importer, so `GD.Load` failed. Run `--headless --import` after merging UI art.
- **Equal-height sheets and columns made dead space.** Let each one hug its own content.
- **I equated "fewer pixels" with "no boxes".** The owner wanted the box idiom gone entirely.

## 7. Gotchas
- **The worktree guard** refuses complex shell. Use `scratchpad/uid6/sub.py FILE PAIRS.py` for exact multi-line replacements (it keeps CRLF), and keep commands simple.
- **Shots:**
  - `scratchpad/uid6/shot.ps1 NAME SECS [args]`. Set `$env:SHOT_RES="2560x1440"` for 1440p and `$env:SHOT_ENGINE="--fixed-fps 60"` for frame-exact runs.
  - `crop.py`, `cands.py` (a sheet) and `review.py` (into `docs/ui_review/buildN`).
- **My switches:**
  - `--nohud`;
  - `--toasts T` and `--tip T`;
  - `--loot legendary --far` (the edge pointer);
  - `--clicks "hX:Y"` hovers;
  - `--clock S` with `--fixed-fps 60`;
  - `--night hollow --stage 3 --auto idle --die 10 --choose rise` (the fall).
- **Merges:** a merge from UI art can be blocked by untracked `.import` files. Delete the untracked ones under `godot/art/ui` first.
- **Experience's Banner/TopClear rule** in Voices.Place isn't on my branch. When it's merged, keep both obstacles: name plates and the banner.
- **Fonts:** Alegreya Sans lacks →, ←, ▲ and ●. Draw them, as `Arrow` and `TileMark` do.

## 8. Collaborators
- **Main session:** relays the owner and merges.
- **UI art (a0bff3ffe4d3ad748):** the kit, chain/*, coal/*, lamp/*, hud/spark and glint, pointer_legendary, title chains. Tunes the chain from `art/ui/chain/chain.json`.
- **Experience:** a9f0d6c64d891d56d has handed off; their successor reads `docs/handoff/experience.md`. Their verdict is in section 4.
- **Crafting (a successor is coming):** the bench is theirs, on my kit. They know the rules (no boxes, HeldWord, PromptsOnWorld).
- **Loot:** paused. The filter and stores are done.
- **The face lead:** will message about the heroine's new head, for the portraits.

HANDOFF READY: docs/handoff/ui_design.md on worktree-agent-a4fdbc49786ba8b7f@(this commit)
