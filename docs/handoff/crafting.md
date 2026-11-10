# Crafting: handoff

For the next crafting lead. Read these in order:
1. `docs/team/README.md`: the owner's bar, how we work, heavy work by turns.
2. This page.
3. `docs/team/crafting.md`: the one-page status.
4. `docs/CRAFTING_DESIGN.md`: section 17 is the decisions (1–30); 19 is what was seen and measured; 20 is the endgame
   (20.2 the kits as built, 20.7 the endgame as built, 20.8 seen and measured, including the bench).
5. `docs/design/LOOT_DESIGN.md`. Item level and make are loot's. Crafting's materials are what a carrier drops in
   place of gear.

The research is `docs/CRAFTING_RESEARCH.md` (C1–C30).

## The owner, in their words

- "AAA standard", "strive for excellent, above and beyond - not just good enough".
- "I don't want to polish, I want to create perfection." "We are striving for perfection."
- "item drops should *mostly* feel good": fewer drops, the rest as crafting materials.
- "end game is two types of arenas - permanent and our normal arenas. permanent is our arpg build maps like poe
  and the normal arenas are for mindless survivors fun": the Wayfinder's atlas and the ember scars.
- The latest screen rules (through UI design, for every screen):
  - no dark rounded boxes holding data ("still ai boxes" at any size);
  - no fades unless designed;
  - no dead space, and a strict grid;
  - words as type rather than buttons.
- Decided earlier:
  - remake costs old iron;
  - a fall after the half hour spills half;
  - full-page screens pause only in arenas;
  - Rook's storeroom grows by bought shelves (24, then 300, 1,000, 2,500 and 5,000 gold, up to eight);
  - the bench is two panels with the smith live in the world between them.

## Your brief

Crafting lead: research, design and build crafting, playable end to end, and seen in the running game at
1920×1080.
- Don't stop to ask. Keep `dotnet test` in `godot/tests` green before every commit.
- Short comments that say why.
- Commit and push your own branch at milestones. The main session merges it; open no PRs.
- Take a turn for Godot (`tools/turn.py`) and give it back the moment the shots are done.
- Hand off at about 500k tokens of context.


Older blocks: history/crafting.md (grep by keyword, never read whole).
