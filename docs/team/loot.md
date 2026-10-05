# Loot and itemisation: status

Loot lead, agent `a9a9c345a35e1fcad`, branch `worktree-agent-a9a9c345a35e1fcad`.
Design: `docs/design/LOOT_DESIGN.md` (research in §1, decisions in §13). Builds on the items plan
(`docs/items/`) and crafting (`docs/CRAFTING_DESIGN.md`).

## State (2026-10-05)

- Design written. Building the rules in logic next (§11's table is the plan and its tests).

## Key decisions (why in the design, §13)

- Seven tiers; Set is new (verdigris, chain-link mark), rarity 3 underneath.
- Item level on every piece; make (Worn, Sound, Wrought, Legion, Heartwrought) scales the base, so
  a late Common beats an early Epic; affix grades rise only past level 25.
- Gear only from carriers, about a third fewer; the rest becomes the people's material or iron.
- Legendaries about 1 in 230 rolls; the first story boss beaten drops one for certain; a visible
  debt guarantees one at 120 rolls without.
- The pack holds gear only: pouch (materials, trophies), satchel (books, charts), key ring (quest
  things, tools), belt (draughts), purse.
- Filter: four presets, five toggles, rules later; Legendary, Set, Storied, quest never hidden.
- What the filter shows is gathered at a fight's end; what it hides is broken down for iron.

## Next

1. Logic: tiers, item level, make, power, drop roll and `loot.json`, stores, filter, sets.
2. Content: seven new Legendaries, two sets, base implicits.
3. Wire the four zones to `Loot.Roll`; drop event and placeholder sounds; end-of-fight gathering.

## Notes for other areas

- **UI design**: answered (handoff at ed2ea5c5); the successor gets the design when it lands.
- **Crafting**: `Inventory.Holds` and `Inventory.Remove` replace `Find(..) is { InPack: true }` plus
  `ch.Pack[i] = null` for anything that may now live in a store (trophies, charts).
