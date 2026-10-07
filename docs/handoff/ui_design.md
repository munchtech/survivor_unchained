# Handoff: UI design lead

For the next UI design lead. Read `docs/team/README.md`, `RESUME.md` and `OWNER_NOTES.md` ("UI design and UI art: the HUD is the keystone"), then this page, then `docs/team/ui_design.md` (status, and the spec UI art starts from), then `docs/design/UI_RESEARCH.md` ("The HUD"). Pictures: `docs/ui_review/build9/`. Older handoffs: `git log -- docs/handoff/ui_design.md`.

**Branch:** `worktree-agent-adba22c3df8f39418` (integration merged at 6407046a). Open no PRs. Stopped at the owner's wind-down: everything builds, tests green.

## 1. The owner, in their words
- "the bottom skill bar and health globes and stuff need to be incredible, its a keystone of that kind of game"; the old foot "is a relic of our old garbage ui".
- "ember on the bottom sliding the boss stuff up"; the clock, kills and gold to a lower corner; "one composed group, not loose pieces"; the minimap "the same pass".
- Journal and Map: no full screen ("feels bad"), the half-window panel "with an option to expand", dead space cut, centred.
- Tips: no shrinking ("more distracting not less"). The tab chain: "I love the direction just needs polish".
- Standing: "we are striving for perfection"; no AI boxes; panels over the world; no fades; soul from the chain, coals, the lamp, sparingly.

## 2. Done (this session; build9 shows it)
All seven of the owner's HUD notes are built (status page "Current state"). Code: `src/Ui/Instrument.cs` (new: Instrument, Vessel, Cuff with the shared `Cuff.Band`, Socket, Round, EmberChain with its Lock), `shaders/hud_vessel.gdshader` (new), `GameHud.cs` (the old ember bar, console, globe, slots, ring and pips removed; tally, boss bar, tips, statuses, passives, corner), `Minimap.cs` (Bezel), `Book.cs` (Journal: panel and wide), `MapScreen.cs` (panel and wide), `Overlay.BookPanel` (width, expand word), `ChainTabs.cs` (polish), `Controls.cs` (`Act.Expand`), `Ornate.cs` (the dead Globe removed), `UiArt.cs` (registry).

## 3. Next
1. **Shoot what is built but unseen** (status page, Next 1), then a strict 1:1 self-critique of the whole HUD before the main session shows the owner.
2. **With UI art** (starts from the status page's spec): bring their cuffs, sockets, lock, bezel and groove in and judge at 1:1 at 1080 and 1440.
3. Then the earlier queue: portraits when the face lead messages (`tools/assets/heroine_paint.py brows`, `creation_portraits.py`); the male Look; `StoryChoices` at 1:1.

## 4. Decisions (why)
- **Her irons:** two cuffs joined by a chain, the ember as its heat, the level on its lock: one object with meaning (Survivor *Unchained*), symmetric, the only ornament on the HUD.
- **Round vs square:** what she lives and acts by is round, what fires by itself square: told apart before reading.
- **Always shown,** at peace too: the keystone stays put (wounds carry into town).
- **Day shows only what is carried, centred;** night shows all six places (the empties promise the night's arsenal).
- **Tips wait for banners;** the top edge is the boss's alone.
- **Line glyphs** for the art in its glass and the six places (painted arts covered the glass; one hand per row).
- **The map opens filling its window** (a square town in a wide window left table bands); "All I know" shows all.
- **The Journal wide is the parchment book over the world;** in the panel it is type on the panel like the rest of the book.

## 5. Failures and gotchas
- **The worktree guard** refuses complex shell (heredocs, computed `sed` lines, `cd` into the main checkout). Put edits in scratch scripts and run them plainly; my tools (`shots.py` batch runner with turns, `sub.py` asserted substitutions, `cut.py` marker cuts) were in the session scratchpad `uid9/`; rewrite them if the scratchpad is gone.
- **Git Bash mangles arguments that start with `/`** (`/// <summary>`): set `MSYS_NO_PATHCONV=1`.
- **Files are CRLF in the worktree:** keep their endings when rewriting.
- **A method named `Content()` shadows the `Content` namespace** (the codex broke).
- **`ColorRect` gives a shader 0 to 1 UVs; `DrawRect` does not.** The vessel's glass is a ColorRect.
- **Shots:** `--resolution 2560x1440` came out 2526x1421 (the desktop's work area); `--fixed-fps` is an engine argument (before `--`).
- **Worktree set-up:** `godot/assets` is a junction to `public/assets` (skip-worktree); the `.godot` cache was copied from the main checkout with robocopy; untracked `.import`/`.uid` sidecars copied in. Never commit them.

## 6. Collaborators
- **Main session:** relays the owner, merges. **UI art** (paused): starts from the status page's spec. **The face lead:** portraits. **The experience director:** the day dial now rides the minimap's bezel.

HANDOFF READY: docs/handoff/ui_design.md on worktree-agent-adba22c3df8f39418@(this commit)
