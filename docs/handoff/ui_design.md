# Handoff: UI design lead

For the next UI design lead of Survivor Unchained. Read, in order:
1. `docs/team/README.md`, then `docs/team/RESUME.md` (its UI rules are yours).
2. This page.
3. `docs/team/ui_design.md`: the one-page status.
4. `docs/design/UI_RESEARCH.md`: the approved direction.
5. `docs/ui_review/build8/`: what's built, as the player sees it (build7 for the earlier passes).

**Branch:** `worktree-agent-aa1f430bd64b8d1ce` (integration merged at 3b508b27). The main session merges it; open no PRs. 762 tests green. Older handoffs are in `git log -- docs/handoff/ui_design.md`.

## 1. The owner, in their words
- **The bar:** "we are striving for perfection." Also: "have the ui dev continue to work on unnecesary dead space and good symetry".
- **On boxes:** "the stat stuff in blocks still dosn't work for me ... they are still ai boxes." No dark rounded box may hold data, at any size.
- **On full pages:** "we like to see our beautiful game." A page that stays is "slightly see through".
- **On fades:** "the fade away isn't needed".
- **On notices:** "transparent and stylized"; tips "a centered attention grabbing thing ... just stylized readable text".
- **On the chain:** "thats the kinda soul were lookin for. SOUL".
- **On the ledger:** "more like a dnd top bit which is much better".

## 2. The brief (this session's)
1. Rebuild the old screens on the book's rules: pause, rest, chapter, credits and creation (creation first: the first impression, and her face is about to change). **Done** (build8).
2. Portraits when the face lead (a6007bf07fd45ab0d) messages that her new head has landed: rerun `heroine_paint.py`'s brows and the creation portraits. **Waiting** (no message yet).
3. UI art (paused): note that `book/ribbon.png` is unused and the map's drawing is soft at its opening zoom. **Done** (status page).
4. Strict self-critique at 1:1 against UI_RESEARCH with every set of pictures; batch shots in one Godot turn.

## 3. Built this session (where to look)
- **Creation** (`Front.cs` CreateScreen, `CreateLook.cs`): `Fitted` panels of `PanelW` 560 at `Inset` 16, mirrored. `Row` (a choice as a line of type; `Choice` and `Recall` use it), `Words` (choices as the house's tabs), `Foot` (`Kit.Keyed` back and on), `Plate` (the name as lettering at her feet), `D*`, `Line`, `Ledger` for the right panel. `Question` is each step's title. `GameFront.DressFigure` stands her at `Fire.X + 0.95` so she is in the middle of the screen.
- **Pause** (`Menus.cs` PauseScreen): its panel and the settings or controls panel in an `HBoxContainer` (`Plate`), so each is as wide as it needs. `SettingsPanel` rows are `Kit.Tab` words; `ControlsPanel` is a ledger with movable keys as caps.
- **Rest** (`Menus.cs` RestScreen): `Hush` (the world darkened, no shape), `Said` (what is said, ending above her head at `Over`), `Lay` (choices in equal columns from `Under`), `Choice` (key, word, line, price, refusal), `Morning`.
- **Chapter** (`Menus.cs` ChapterScreen): one centred column; the `OpenBook` measured until its height holds (the Journal's way).
- **Credits** (`Credits.cs`): the slab and seal unboxed. **Title** (`Front.cs` TitleScreen): its panels fitted, the name hidden while one is open; the adults' notice a fitted panel.
- **Kit:** `Kit.Keyed` (key and word, measured again in the tree), `Kit.Tab`, `Kit.TabFlow` (words in centred lines), `Kit.Quiet` (let the pointer through). `WorldType.Keyed` (the same in lettering). `ChainTabs`: `on = -1` (none open, cold), `ends` (turning keys outside the eyes), `gap`; laid out in `_Ready`. `Glyphs.Icon(..., line: true)`.
- **Switches:** `--sex male`, `--panel load|settings|controls`, `--adults`.

## 4. Next
1. **Portraits** when the face lead messages: `python tools/assets/heroine_paint.py brows`, then `python tools/assets/creation_portraits.py` (takes a Godot turn), then shoot the Look's parts (`--new --sex female --step 1 --part 0..4`) and the calling (the invite's `look.png`). Sunborn, Moonlit and Saffron have no cameo yet (build8/3).
2. **The male Look** waits for the male hero lead (his invite and cut cameos are glyphs: build8/10, 11).
3. **Review at 1:1:** combat's new `StoryChoices` (`WorldType.cs`, the knee's choice, merged at 3b508b27) against the held-moment rules.
4. **Candidates I judged and left:** the credits' reading measure (text wraps near 950 px while its heads' rules run the page's width); the creation rows' room to their right (a list's nature; a 2x2 grid was too narrow for the tags).

## 5. Decisions (each with its why)
- **Creation is two mirrored panels with her in the middle:** strict symmetry; she is the hero of the screen; the fire stays in view at her right hand.
- **The chain means the tabs, wherever they are** (book, pause, creation's steps): one object under the hand; a title beside it has no chains of its own.
- **Held moments are type over and under her, never a plate:** the fall set the language; the lamp and the morning follow it, the words above her head, the choices below her feet.
- **The chapter's leaves split past from future:** the past (what was done, what the world says, the tally) on the left, the living and what waits on the right; it also evens their heights.
- **Line glyphs in rows:** the painted glyph set mixes full colour and white line; a row of them looked unfinished.
- **No glyphs on the lamp's choices:** the painted ones were purple beside a plain arrow; the fall has none either.
- **The pause's chain is cold:** a heated link means an open page.

## 6. Failures, and why
- **Out-of-tree measures run wide:** a key cap measured before it is in the tree takes the default theme's type, so a button sized from it left its word 30 px short of the panel's edge, and a chain's width came out wrong. Measure again in `Ready` (`Kit.Keyed`, `ChainTabs.Lay`).
- **A rich label expands by default:** the credits' seal took half its heading's line until set `ShrinkEnd` with its own width.
- **The chapter measured once was short** (wrapped words settle late): a scroll bar showed and cut the tally. It now measures until it holds.
- **`--keys` only presses once while the world is paused** (the tour's timer stops): use one `--clicks` for the pause's panels.
- **One `--adults` run hung at start with no output;** the same run again went through (a stall, not the code). Run shots that might hang under a time limit.
- **Clicks need `--open`:** without it the tour returns before them; hence `--sex male` and `--panel`.

## 7. Gotchas
- **Worktree:** `godot/assets` is a junction to `public/assets` (skip-worktree); the `.godot` cache and the import sidecars were copied from a565196002a51af40's worktree (`scratchpad/uid8/copyimports.py`). Never commit the `.import` or `.uid` files the import dirties; stage your files by name.
- **`CreateScreen` has a property `Hero`** (the hero's own look); `Kit` there is the static class.
- **Shots:** `scratchpad/uid8/shot.ps1 NAME SECS [args]` (`$env:SHOT_RES`), `crop.py`, `grid.py OUT COLS W names...`, `review.py OUTDIR name=shot`, batches `b1.ps1` to `b7b.ps1`. `fortune.json` is a day-two save for `--load`; `poor.json` the same with 2 gold (the lamp refusing). PowerShell's `ReadAllText` with a relative path reads from the process's folder, not the location: use full paths.
- **`G.After` stops while the sim is paused**; fonts: Alegreya Sans lacks →, ←, ▲ and ●.

## 8. Collaborators
- **Main session:** relays the owner and merges.
- **The face lead (a6007bf07fd45ab0d):** will message when her head lands, for the portraits. `CreateLook.cs` changed in presentation only.
- **Combat (a427a874da78cba8b):** added `StoryChoices` to `WorldType.cs`.
- **UI art (paused):** see the status page's notes.

HANDOFF READY: docs/handoff/ui_design.md on worktree-agent-aa1f430bd64b8d1ce@(this commit)
