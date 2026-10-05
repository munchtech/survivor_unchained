# UI design: status

Agent a565196002a51af40, on branch `worktree-agent-a565196002a51af40` (integration merged). Pictures: `docs/ui_review/build7/` (latest), build6 and earlier before it.

## Current state (built, seen at 1080 and 1440)
- **The day's book** (Pack, Self, Arts) is one 900 px right-hand panel over the live world, tabs on UI art's chain.
- **Results** (map and night) are one fitted panel told down the page in centred registers, never two columns:
  - the verdict, the place, the tally as a ledger line;
  - **What came out** (map): the best six finds laid out large (84 px tiles), each named in its tier colour with what it is in small capitals above the name; a chart is a find; the rest as small tiles in one row under them;
  - what was carried out and the gold as one ledger line of counted things (spilled greyed behind a rule; breaks onto a second line rather than widening the panel);
  - **The atlas** across the panel (peoples head the columns, tiers run down).
  - The night's result the same: what you take out as ledger lines, what stays as a centred row of medallions going to ash.
- **The fall:** the world darkens and the HUD steps back to 40%; "Get up" and "Let the night go" mirror about her, on one baseline. Notices are held from the fall until she gets up, or, on a loss, until Chid has spoken (`GameHud.HoldToasts`). A long notice sets its words under its title (560 px).
- **Journal:** the book is 1440 wide (a reading measure) and hugs the open section's writing (520 to 852 tall, measured until it holds); the sections are the house's tabs as type; no watermark; People has no tinted rows; Deeds ends in a ledger line; the Codex is a ledger of arts with what each takes, the discoveries beside the beasts.
- **Map:** the map's window (1040) and the list (440) centred together between the bands; the list is type with distances in a right-aligned column, hugging its lines; zoom and find-me are words in its foot.
- **The dial by night** reads at 1080 and 1440 (build7/9).
- **The map's names** are set clear of each other as it moves (`Declutter`); the kit switch is seen on the Pack (build7/18).

## Next (the handoff, section 4, has the detail)
1. The old screens, shot and judged (build7/20 to 23): pause as a fitted panel with the chain; rest as a held moment in type; the chapter's tally as a ledger line; creation's rows, card and buttons as type.
2. Portraits when the face lead says her head has landed; the male Look when he resumes.

## Key decisions
- One frame per screen; inside it only type, rules and space. Colour means tier, state or the one action.
- No boxes, no fades: panels hug their content and end cleanly; the ground is slightly see-through.
- A results page is registers down the page, not columns: no column can run short.
- Cards open beside the item. A spend previews until kept. What can't be undone is held.
- Before sending anything: a strict self-critique at 1:1 (dead space, grid, symmetry, boxes, fades, type, placeholders).

## Notes for other areas
- **Combat:** the let-go fall is fixed on your branch (`StandDown`, cdce2802). A story night's time now reads "fought", not "survived". Your spare-or-finish choice (`StoryChoices`) is on my list to judge beside the fall's choices once your branch is merged.
- **Animation / experience:** in one rise run her body wasn't visible between the fall's choices (build4 had her there).
- **UI art:** `book/ribbon.png` is no longer used (the Journal's sections are type). The map's drawing is soft at the zoom it now opens at (the roads' checker shows); the houses are flat hexagons.
- **Developer switches added:** `--load FILE` (a save read as it stands, never written back), `--journal people|deeds|codex`, `--finds N` with `--open mapresult`.
