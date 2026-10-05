# UI design: status

Agent a4fdbc49786ba8b7f, on branch `worktree-agent-a4fdbc49786ba8b7f`, which has the integration branch, loot, crafting and UI art merged. Pictures are in `docs/ui_review/build3/` (the latest), `build2/` and `build/` (before and after).

## Current state (built, seen at 1080 and 1440)
- **The day's book** (Pack, Self, Arts) is one 900 px right-hand panel over the live world. Her figure is framed nearer in the world beside it (`CameraNear`). The tabs ride UI art's chain, fixed in eyelets, with a heated span and a rattle (`ChainTabs`, feel from `art/ui/chain/chain.json`).
- **Self:** the attributes are a ledger line. Points are coals in a dish, and a coal given lights its numeral. Every number it moves shows its projected value in ember until KEEP or UNDO. The traits are a level track, and offers are held type (`HeldWord`). The standing is four aligned columns, with sources on hover.
- **Pack:**
  - the doll with engraved empty places;
  - the carried grid, showing the rows in use plus one;
  - the stores as tabs (Pouch, Satchel, Key ring, Belt), and the purse;
  - Filter beside Sort (`FilterPanel`: presets, promises, drop sounds).
  - Cards open beside the item with the worn piece, and each line carries its own change. Click holds the card, and holding Del breaks the item down.
- **Counters** (Storeroom, Trader, crafting's Bench) are fitted panels with the keeper live in the gap; the camera looks at them.
- **Results** (map and night) are one fitted panel: a ledger tally, the best finds first, and a telling under six seconds.
- **Notices and tips** are type on the world: sparks, glints and tier light, with no boxes (`WorldType.cs`).
- **Rules applied everywhere:**
  - no boxes holding data;
  - no fades; panels end cleanly with one 28 px margin and a 93% ground;
  - words as type: Close, UNDO and KEEP, held words;
  - prompts lie on the world over a soft shade (`PromptsOnWorld`).

## Next (see docs/handoff/ui_design.md, 4)
1. The Journal on the rules (its empty pages, its tabs); MapScreen's self-critique pass.
2. The kit switch seen on screen (needs a save with a coal or Mark).
3. Portraits when her head lands; the male hero's Look when he resumes.
4. The old screens: pause, rest, chapter, credits, creation.

Also built since: ground labels and the legendary chevron, the day dial, the fall's choices, the table and atlas as sheets, the title's focus, barks clear of plates, the kit switch, Arts on the book panel, full pages lighter (build4 to build6).

## Key decisions
- One frame per screen; inside it only type, rules and space. Colour means tier, state or the one action.
- No boxes, no fades: panels hug their content and end cleanly; the ground is slightly see-through.
- Cards open beside the item, never in an inspect panel. A spend shows its preview everywhere until it's kept.
- What can't be undone is held, never confirmed by a second dialog.
- Before sending anything: a strict self-critique at 1:1 (dead space, grid, symmetry, boxes, fades, type, placeholders).

## Notes for other areas
- **Crafting** (successor): merge my branch (f82f7497 or later). `ForgeScreen.Deed` already uses `HeldWord`; the bench's foot uses `PromptsOnWorld`; Close is type.
- **UI art:** names in use: `side`, `panel`, `slot*`, `tooltip`, `chip`, `rule_h`, `tab*`, `keycap`, `nodes/*`, `chain/*`, `coal/*`, `hud/spark`, `hud/glint`, `ornaments/title_chain_*`, and `icons/glyph/up`, `anvil` and `link_set_*`.
- **Experience:** `--toasts T` and `--tip T` show the notices and a tip, for pictures.
