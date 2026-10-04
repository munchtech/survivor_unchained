# Crafting: status

Crafting lead, agent `a7debf1459f14dfe7`, branch `worktree-agent-a7debf1459f14dfe7`
(successor to `a97e32948c5bf419d`). Research: `docs/CRAFTING_RESEARCH.md` (lessons C1–C30).
Design: `docs/CRAFTING_DESIGN.md` (sections 1–20; 19 is what was seen and measured, 20 the endgame).

## State (2026-10-04)

**Phases 1 and 2 are built and seen running at 1920×1080** (design 19.1, 19.3). Tests green (570).
- **The arena's gold is cut** (combat built it): champions 7%, fodder 0.15%, bosses and minibosses
  in full. A Kerchief night pays about 350 gold (it paid 2.5k–3.3k). `CraftingEconomy` reads the
  arena's real rates and holds every target (weapon Epic by day 8; crafting takes 67% of the gold).
- **Phase 2**: Wenna's still-room (a side panel) and flask; her bench after the cure; Brannoc's
  commissions ("Make me one"); Greymuzzle's fang set outside the seams; Maeca's braid of shed fur.
  The story lead's words, verbatim. Tests: `tests/CraftersTests.cs`.
- **Seen and fixed**: the forge's hammer moment (flare, sparks, the heat burning out); work in with
  nothing to offer said why; painted icons for the new things; the pack's break down says what it
  came to; crafts no longer dress the figure again; **an arena fall now spills half** (it kept all).

## Next, in order

1. **Phase 3, in progress** (paused for the owner). The rules are in: `Crafting.Bind`/`Donors`,
   `BuyJar`/`Buy`, `Steep` (odds, the bright grade V, three slurry affixes), Snib's "slurry" action
   (buys a jar, the talk goes on), Vonnra's "craft" choice. The story lead's words are merged in from
   `worktree-agent-a73ca9d35d0c487a9@d132033f`, but the conflict in `crafting.json` was resolved to
   ours. **Exact next step:** copy their `crafters.vonnra.lines` and `crafters.snib.lines` verbatim
   into our entries (`git show d132033f:godot/data/content/crafting.json`), keeping our `verbs`.
   - Vonnra: their `when` (met and `toll.paid`) and `closedLine`; place "The Toll Tower"; `bind.coal` becomes `bind.caged`; her easier line from `terms.accused`.
   - Snib: `when` (met, pump not broken/blown/moved) and `closedLine`. The outcome "slurry" becomes "affix" (`steep.affix`). The jar's lore is their `jar` line.
   - Slurry affixes: "seeping" becomes **Fevered** (`fevered`), "green_veined" becomes **Pipe-Lad's** (`pipe_lads`).
   - Their choice for Vonnra: "Can you move what's in one thing into another?". Snib's "Sell me a jar of that." should open **his bench** (`forge:snib`: a jar tile and a Steep tile with the odds, his `first.steep` lines), not just buy.
   - Then: the forge's Bind section (donors per seam, a two-step confirm because the donor is unmade), the pack's Steep (two-step, odds shown, outcome said), a `slurry_jar` painted icon, `CraftersTests` for bind and steep, and pictures.
2. **Endgame** (design 20.6): combat's maps and Marks hook exist (09b6b03, 5c50de1). Two kits; item
   level and grade caps; chart verbs at Ysolde's table (`ItemInstance.Chart`, quality field ready);
   Marks on the item side (`CombatKit.Marks`, `CombatKit.SkillMods`, grade 0–5 to strength 0–1; four
   proven: of the Ravine, of the Falling Star, of the Open Gate, of the Gyre).
3. Re-measure shards with 20-minute story nights; minibosses' +2 of the people's material (owed).

## Decisions (why in design section 17)

- Heat caps working; the forge's ceiling is a lucky drop's grade; work in makes answers.
- Three coals offered; the night pays at its end and a fall spills half (owner).
- Remake costs old iron (owner); one remake a piece a day; break down halved.
- Arena gold cut, by combat (18). Wenna brews from the start, tinctures after the cure (19).
- The still-room is a side panel (20). The moonpetal draught only for a deep wound (21).
- A trophy is set outside the seams (22). Crafts never dress the figure again (23).

## Agreed with others

- **Combat** (`a1d4562f44c7f6feb`): the gold cut; the moonpetal draught at 60% (heal source
  "draught" so map suffixes catch it); the Marks hook built, item side mine.
- **Story**: phase 2 words received and wired; phase 3 (Vonnra, no `{name}`) waits on my hooks.
- **UI design** (`a69858664f1d3dd29`): told of the still-room, the forge's moment, and a pack bug
  (the doll T-poses a frame on every refresh; `G.Gear` rebuilds the world figure).
- **UI art** (`a1a394643aabfb169`): three item icons painted with their pipeline.

## Notes for other areas

- **Pictures**: `--items DEF:RARITY:AFFIX@GRADE+AFFIX@GRADE`, `--facts k=v,k=v`, `--met a,b`,
  `--clicks X:Y,rX:Y` (`--click-every S`), `--won` with `--minute M` (a night won where she stands;
  `--die T` then falls her), `--make --pattern DEF` (the forge's commission page), `--focus ID`
  on the still-room too.
- **A worktree runs the game** once `godot/assets` is a junction to the main checkout's
  `public/assets` (skip-worktree set), the main `godot/.godot` is copied in, untracked art is
  copied from the main `godot/art`, and `dotnet build` is run in `godot/` (else the old DLL runs).
  A headless `--import` rewrites hundreds of `.import` files: revert them, keep only your own.
