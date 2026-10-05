# Handoff: UI design lead

For the next UI design lead of Survivor Unchained. Read, in order:
1. `docs/team/README.md`, then `docs/team/RESUME.md` (its UI rules are yours).
2. This page.
3. `docs/team/ui_design.md`: the one-page status.
4. `docs/design/UI_RESEARCH.md`: the approved direction.
5. `docs/ui_review/build7/`: what's built, as the player sees it (20 to 23 are the old screens before their pass).

**Branch:** `worktree-agent-a565196002a51af40` (integration merged at c065304d). The main session merges it; open no PRs. 747 tests green. Older handoffs are in `git log -- docs/handoff/ui_design.md`.

## 1. The owner, in their words
- **The bar:** "we are striving for perfection." Also: "have the ui dev continue to work on unnecesary dead space and good symetry".
- **On boxes:** "the stat stuff in blocks still dosn't work for me ... they are still ai boxes." No dark rounded box may hold data, at any size.
- **On full pages:** "we like to see our beautiful game." A page that stays is "slightly see through".
- **On fades:** "the fade away isn't needed".
- **On notices:** "transparent and stylized"; tips "a centered attention grabbing thing ... just stylized readable text".
- **On the chain:** "thats the kinda soul were lookin for. SOUL".
- **On the ledger:** "more like a dnd top bit which is much better".

## 2. The brief (this session's)
1. Experience's verdict: the map result's dead column; a loss's toast over the fight; the dial by night; the fall's choices. **Done.**
2. The Journal, the Map screen, the kit switch on screen. **Done.**
3. The old screens: pause, rest, chapter, credits, creation. **Shot and judged, not yet rebuilt** (section 4).
4. Portraits when the face lead says her head has landed. **Waiting** (no message yet).
5. Strict self-critique at 1:1 against UI_RESEARCH with every set of pictures; batch shots in one Godot turn.

## 3. Built this session (where to look)
- **Results** (`Telling.cs`, `MapResult.cs`, `ArenaResult.cs`): registers down one centred panel, never columns. `Register` (a centred head with air above), `LedgerLine` (counted things and sums; spilled behind a rule; an `HFlowContainer`, so it breaks rather than widening the panel), `Counted`, `Sum`. The map's finds: the best six as `Find` cells (84 px tile, kind in small capitals, name in tier colour, two lines at most), the rest as 52 px tiles. `AtlasGrid(..., across: true)` lays the atlas wide. `Kit.HeadMid` is the centred head.
- **The fall** (`GameFall.cs`, `WorldType.FallChoices`, `GameHud.Fall`): toasts held from the fall (`HoldToasts`) until she gets up, or on a loss until Chid has spoken (`LeaveArena`'s `talkDone`); the shade stays until the result (`LiftFall`); the HUD at 40% under the choices; the choices mirrored about her.
- **Notices** (`WorldType.Notice`): past 560 px a notice's words set under its title, broken evenly.
- **Journal** (`Book.cs`): 1440 wide; `heights` per section, found by measuring until it holds (`settling`, grows only); Kit.Tabs for sections; Codex as a ledger; Deeds' tally as a ledger line. `OpenBook.Painted` cuts the painted book to any size up to 1700x852.
- **Map** (`MapScreen.cs`): `View` and `ListAt` centred together; `Line` rows as type over `LineUnder`; the list hugs; `Declutter` sets the drawing's names clear of each other each time it moves.
- **Switches:** `--load FILE` (a save read as it stands, never written back), `--journal SECTION`, `--finds N` (with `--open mapresult`), a long quest in `--toasts`.

## 4. Next
1. **Pause** (`Menus.cs` PauseScreen; build7/20): a full-height navy plate with dead space between the menu and five medallions. Make it a fitted panel on the left (the book panel's twin), hide the HUD as the book does, and put the book's `ChainTabs` where the medallions are. Its Settings and Controls open in `Style.Plate` boxes with Plaques and a boxed Back: same pass.
2. **Rest** (build7/21): three bordered cards on a plate. Make it a held moment as type on the world, like the fall's choices (title, Rook's line, three choices with glyph, word, line and price; Nav ids `rest:sleep|wait|leave` kept). The morning report is a paper panel with a boxed "Get up".
3. **Chapter** (build7/22): the tally is five coin medallions pinned to the page's foot (dead space above them). Use the Journal's ledger line after the words, the 1440 book hugging, and words (Kit.Word) for the two buttons; "Who remembers you" has the role pushed to a far column by ExpandFill labels.
4. **Creation** (`Front.cs` CreateScreen; build7/23): the first impression. Callings are boxed rows, the woman/man toggle two boxes, the calling's card a box with stat bars, the nameplate a box, Leave and Next boxed buttons. Rows as type, the card's words on the world, the stats as a ledger line.
5. **Credits** are already type on a page; check at 1:1 only.
6. **Portraits** when the face lead messages: re-run `tools/assets/heroine_paint.py` and `tools/assets/creation_portraits.py`, then shoot the Look. The male Look waits for the male hero lead.

## 5. Decisions (each with its why)
- **A results page is registers, not columns:** no column can run short, and the eye reads down once.
- **The finds are named large, six at most:** two named rows ran the panel to the screen's edges at 1080; the rest keep their cards on hover.
- **Notices wait while a fall is staged:** nothing prints over a held moment; they are told whole after.
- **The fall's choices mirror about her:** a centred row put the gap off her by the words' difference.
- **The Journal hugs its writing, measured:** an empty book was a screen of blank parchment; the book is shown only once its height holds, and grows only (a scroll bar's narrowing made two heights take turns).
- **The map and its list are one centred composition:** the sheet sat in the middle of all but the list, with bare table either side.

## 6. Failures, and why
- **Shots ran the wrong place:** `--night` needs `--zone verge` (else the prologue runs), and story shots need `--nocine` (a cinematic letterboxed them). `--people` takes ids (`dead`, not `risen`).
- **`--keys` stopped after the first press** on the Journal; `--journal SECTION` replaced it.
- **A label's size out of the tree is its first text's:** set the final text before measuring (the notice's first wrap overlapped the next notice).
- **Autowrapped labels measure short for a frame or two:** measure until it holds.
- **Import:** the first `--headless --import` on a copied cache crashed (exit 5); the second finished in 4 minutes.

## 7. Gotchas
- **Worktree:** `godot/assets` is a junction to `public/assets` (skip-worktree); the `.godot` cache was copied from a4fdbc49786ba8b7f. Never commit the `.import` files the import dirties (git shows many as modified; stage only your files by name).
- **The worktree guard** refuses heredocs piped into python and loops: write a pairs file and run `scratchpad/uid7/sub.py FILE PAIRS.py` (exact replacements, keeps CRLF).
- **Shots:** `scratchpad/uid7/shot.ps1 NAME SECS [args]` (`$env:SHOT_RES`, `$env:SHOT_ENGINE`); `crop.py`, `grid.py OUT COLS W names...`, `review.py OUTDIR name=shot`. Batches `b1.ps1` to `b9.ps1` show the switches for every screen. `fortune.json` is a day-two save for `--load`.
- **`G.After` stops while the sim is paused**, so a fall can't hold the world still before the result.
- **Fonts:** Alegreya Sans lacks →, ←, ▲ and ●.

## 8. Collaborators
- **Main session:** relays the owner and merges.
- **Experience** (successor of a9f0d6c64d891d56d): their verdict is answered in build7 1 to 9.
- **Combat / experience:** a let-go fall runs 2.2 s under the shade with her skills still striking (status page, notes).
- **UI art (paused):** `book/ribbon.png` is unused now; the map's drawing is soft at its opening zoom.
- **The face lead (a833b7942e978d994):** will message when her head lands, for the portraits.

HANDOFF READY: docs/handoff/ui_design.md on worktree-agent-a565196002a51af40@(this commit)
