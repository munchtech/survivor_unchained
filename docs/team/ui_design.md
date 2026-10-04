# UI design (character creation first): status

Agent a26f87c39952dcd9c, branch `worktree-agent-a26f87c39952dcd9c`. It has the integration branch merged in, plus the predecessor's tip (a69858664f1d3dd29@29792ce3).
The predecessor's handoff, `docs/handoff/ui_design.md`, is the full brief.

## Current state (paused by the owner, 4 October)
- The worktree is set up:
  - `godot/assets` is a junction with skip-worktree;
  - `override.cfg` sets the user folder `SurvivorUnchainedUiLead4`;
  - the build and headless import are done.
- Shot tools are in `scratchpad/uid4/` (`shot.ps1`, `edlib.py`), pointed at this worktree.
- **`godot/licences/` holds the upstream texts, unchanged:**
  - Godot 4.5.1-stable `LICENSE.txt` and `COPYRIGHT.txt`, as `GODOT_*`;
  - .NET runtime `release/8.0` `LICENSE.TXT` and `THIRD-PARTY-NOTICES.TXT`, as `DOTNET_*`;
  - the three `OFL-*.txt`, copied from `godot/art/fonts`.
  Nothing ships them yet.

## Next: the licences screen (the exact next step)
1. Merge `origin/claude/vigilant-galileo-l6jqyx` again. It now has the performance lead's export work, so re-read `godot/export_presets.cfg` and `tools/godot/export.sh` before touching them.
2. In `godot/logic`, write `Credits.Parse(md)`: `public/assets/CREDITS.md` becomes sections, groups and entries, made player-facing.
   - Drop backticked paths, `-> file` tails, the fetch-tool note and the web-only section.
   - Keep any Sketchfab line that `sketchfab.mjs` appends at the end.
   - Don't ship CREDITS.md itself: its review notes (the boar's "personal use", PE-05 and PE-06) must not reach the `.pck`.
3. A golden-file test writes `godot/data/credits.json` (for the screen) and `godot/licences/CREDITS.txt` from it when `WRITE_CREDITS=1`. Otherwise it fails if either is stale, or if any CC BY or OFL link in CREDITS.md is missing.
4. Add `licences/README.txt`: an index of the folder plus the AI-use line from CREDITS.md's AI section.
5. Export:
   - add `licences/*` to `include_filter`, so the game can show the texts;
   - make `export.sh` copy `godot/licences/` beside each build.
6. `Ui/CreditsScreen.cs`, the page style (Backdrop, frameless `Style.Column`):
   - a section index on the left, the scrolling credits on the right;
   - Godot's MIT text and its components from `Engine.GetCopyrightInfo()`;
   - the .NET and OFL texts read from `res://licences`;
   - "Open the licences folder" via `OS.ShellOpen`.
7. Hook it up:
   - `Game.Open("credits")` keeps the world paused like the pause menu, and its close returns to the pause menu;
   - the title's Credits item opens it, and its close returns to the title;
   - the pause menu gets "Credits and licences";
   - `--open credits` for shots.
8. Take shots at 1920x1080. Then send the wording to the **legal lead, aab20546fe06daa89**, before pushing the screen.

After that, in the handoff's order: the UI art lead's six pieces, the map result and atlas, the portrait reruns, and the pack's two bugs.

## Waiting on others
- **Face lead (ade92e8285938438f):** the new head. After `heroine.glb`, rerun `heroine_paint.py`, then `creation_portraits.py`.
- **Male hero (ab82cbe99e2937ddd):** `heroes.male` and his builder. Then run `creation_portraits.py --sex male`.

## Key decisions
- Look is step II: the calling dresses her, then she is shaped.
- Portraits are rendered from the game, so they stay true when her head changes.
- The licence texts are the upstream files, byte for byte, from the tags that match what ships (Godot 4.5.1, .NET 8).
