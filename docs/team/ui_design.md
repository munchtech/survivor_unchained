# UI design (character creation first): status

Agent a26f87c39952dcd9c, branch `worktree-agent-a26f87c39952dcd9c`. It has the integration branch merged in, as of 2a1198df.
The predecessor's handoff, `docs/handoff/ui_design.md`, is the full brief.

## Current state (Godot is off-limits until the main session frees it)
**The licences, code done; the screen is not yet seen in game.**
- **`Content/Credits.cs`** turns `public/assets/CREDITS.md` into the player's credits.
  - It cuts what belongs to the workshop: paths, `-> file` tails, the fetch tools' note, review notes (the boar's "personal use", PE-0x and CR-0x) and the web game's section. Every other word is kept.
  - If a fetch tool appends a line at the end, it is put back in its section.
- **The outputs:** `godot/data/credits.json` (the screen's) and `godot/licences/CREDITS.txt` (shipped).
  - In CREDITS.txt, each CC BY work has Source, Creator, Licence and Modified lines, the form STEAM_CHECKLIST asks for.
- **`CreditsTests` (7 tests):**
  - a golden-file check; regenerate with `WRITE_CREDITS=1 dotnet test --filter CreditsTests`;
  - every link in the ledger must ship;
  - none of the workshop's words may ship;
  - each CC BY work has its creator, link and changes;
  - the export wiring is in place.
- **`godot/licences/`:**
  - the Godot 4.5.1 `LICENSE` and `COPYRIGHT`;
  - the .NET 8 `LICENSE.TXT` and `THIRD-PARTY-NOTICES.TXT`;
  - the three OFL texts;
  - `CREDITS.txt`.
- **Export:**
  - `export_presets.cfg` includes `licences/*` in all three presets;
  - `tools/godot/export.sh` copies the folder beside each build.
- **`Ui/Credits.cs`, `CreditsScreen`:**
  - a page over the blurred world;
  - the index on the left: seven credit sections I to VII, then Godot, .NET and the typefaces;
  - the reading on the right: each section's numeral and title over a rule, a CC BY seal, groups with a rail on the left and the works beside it, links that open in the browser, and long runs of short names as one line;
  - Godot's parts are read from `Engine.GetCopyrightInfo()`; the licence texts come from `res://licences`;
  - controls: LT/RT or Left/Right change section, Up/Down scroll, X opens the licences folder, B goes back.
- **How to reach it:**
  - the title's Credits, which returns to the title;
  - the pause menu's "Credits and licences", which returns to the pause menu with the world kept paused;
  - `--quick --open credits`.
- **CREDITS.md edits (player-facing):**
  - "This file lists" became "These credits list";
  - the AI section's "This is to be declared on its Steam page" became the AI-use statement.

## Next
1. **When Godot is free:**
   - take shots at 1920x1080 of each section, the three licence views and the title route;
   - fix what is drab or dense, then send the wording to the **legal lead, aab20546fe06daa89**.
2. Then, in the handoff's order:
   - the UI art lead's six pieces;
   - the map result and atlas;
   - the portrait reruns;
   - the pack's two bugs.

## Questions for legal (to send with the shots)
- The AI line: CREDITS.md lists the tools in the build (Maya1, Seed-VC, VoxCPM2, BiRefNet, DINOv3, MoGe 2). STEAM_CHECKLIST E names ElevenLabs and Pixal3D. Which wording is right?
- Does a CC BY work need "Modified" when no changes are listed? Today it is left out.

## Waiting on others
- **Face lead (ade92e8285938438f):** the new head. After `heroine.glb`, rerun `heroine_paint.py`, then `creation_portraits.py`.
- **Male hero (ab82cbe99e2937ddd):** `heroes.male` and his builder. Then run `creation_portraits.py --sex male`.

## Key decisions
- **Ship a cleaned copy, never CREDITS.md itself:** its review notes would be in the `.pck` for data-miners.
- **Clean by rules, not by hand,** so the shipped credits can't drift from the ledger; a test fails when they do.
- **The licence texts are the upstream files, byte for byte,** from the tags that match what ships (Godot 4.5.1, .NET 8).
- **Look is step II:** the calling dresses her, then she is shaped. Portraits are rendered from the game.
