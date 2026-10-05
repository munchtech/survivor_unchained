# UI design (character creation first): status

Agent a26f87c39952dcd9c, branch `worktree-agent-a26f87c39952dcd9c` (integration branch merged at 524e25c0).
The predecessor's handoff, `docs/handoff/ui_design.md`, is the full brief.

## Current state: code done, nothing yet seen in game (Godot is the owner's until the main session frees it)
- **Credits and licences** (178768aa, db9f434b):
  - `Content/Credits.cs` turns `CREDITS.md` into `data/credits.json` and `licences/CREDITS.txt`. It cuts paths, fetch-tool notes and review notes.
  - `CreditsTests` is a golden file. Regenerate with `WRITE_CREDITS=1 dotnet test --filter CreditsTests`.
  - The `licences/` folder ships the Godot, .NET and OFL texts, packed (`include_filter licences/*`) and copied beside the build (`export.sh`).
  - The screen is `Ui/Credits.cs`, opened from the title's Credits and from the pause menu's "Credits and licences". Shots: `--quick --open credits`.
- **The pack's bugs** (d2750bfc):
  - `Loadouts.Look`: the world's figure is rebuilt only when what shows changes, and then follows the old one's place and pose;
  - the pack's doll is kept across refreshes while it looks the same;
  - `PersonView.Settle` poses a new figure as it is readied, so there is no T for a frame.
- **Page pieces** (c3c3f1fc), each falling back to the drawn look while its file is missing:
  - the backdrop's edges and grain;
  - a column rail with its stone between page panes (`Overlay.Dividers`);
  - `section_mark` in `Section`;
  - `hero_plate` behind the figure on the pack and the self;
  - `card_light` on the map result's finds.
  The new PNGs have no `.import` yet: the UI art lead's step 2.
- **Map result and atlas** (8aa77414):
  - `MapResultScreen` tells the verdict, the time, falls, slain and packs, then the loot (best last), then the atlas line and grid. It shares `TellingScreen` with the night's result.
  - The `MapSpoils` diff gives what the map paid.
  - `IZoneHost.MapOver` hands a map's end to the game.
  - The atlas is the Wayfinder's table's second page: the great atlas, the chart in hand with its oaths and the way in, and the points on the five biases.
  - Shots: `--zone map --open mapresult [--fell]`; `--zone waystation --charts 3 --lit pack:1 --open atlas`.

## Next
1. **When Godot is free:**
   - run `--headless --import`;
   - shoot at 1920x1080: credits (each section, the three licences, the title route), the map result (cleared and `--fell`), the atlas (empty, the beta's tier 1 and a point, several charts), the pack's wear and take-off (no blink, no T), and the pages with the new pieces (Self, Pack, Arts, Forge, credits);
   - fix what is drab or dense.
2. Send legal the screenshot of the credits page.
3. Rerun the portraits after the face lead's head, and his portraits once his body lands. Then do Self's density and the frameless creation.

## Legal (aab20546fe06daa89): answered, applied at a185aea3
- Unshipped works are out of the credits (the anime body, its hairstyles, the older woman's body). KayKit stays (its meshes are in the landmarks).
- The AI list is STEAM_CHECKLIST E's text, naming only what ships. Each new line (voices, music, the hero) joins when what it covers ships.
- "Modified" isn't needed on an unchanged work. Every entry has one anyway.
- Open: "AccuRIG rigged the heroine's and the hero's bodies" (his body isn't in the release); asked. Legal wants a screenshot of the page.

## Notes for other areas
- **Combat:** `MapRun.Finish` now calls `G.MapOver(Result, alive)`. Its default in `IZoneHost` is the old travel back. `Charts.TakeOut`, `Charts.Carried` and `Atlas.IsOpen` are new.
- **Story:** the atlas opens once a chart is carried. Vonnra's fortune should give the first (`Journey.GiveChart`).
- **UI art:** the six pieces are wired by name, so drop files in and they show. `card_light` and `hero_plate` still want rendering.
- **Experience:** the map result and the atlas follow "A map's shape". Judge them from the shots.

## Key decisions
- **Ship a cleaned copy of CREDITS.md, never the file:** its review notes would reach the `.pck`. It is cleaned by rule, and a test fails if it drifts.
- **The licence texts are the upstream files** at the shipped versions (Godot 4.5.1, .NET 8).
- **A map's loot is read from before and after,** not counted in the fight: one source of truth, no bookkeeping in combat's code.
- **The atlas lives at the Wayfinder's table as a second page,** not a new screen: it is the same table, and LT/RT turn it.
- **The figure is rebuilt only when its look changes:** most gear doesn't show, so rebuilding for it was only a blink.
