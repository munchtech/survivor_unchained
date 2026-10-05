# Crafting: status

Crafting lead, agent `ab0b263c720bdbda8`, branch `worktree-agent-ab0b263c720bdbda8` (successor to
`af01b0d61ef656dd4`, whose handoff is `docs/handoff/crafting.md`). Research: `docs/CRAFTING_RESEARCH.md`.
Design: `docs/CRAFTING_DESIGN.md` (20.2 the kits as built; 20.7 the endgame as built; 20.8 seen and measured).

## State (2026-10-05)

Phases 1–3 and the endgame's crafting are built.

**Seen at 1920×1080** (design 20.8):
- the scars' depth and scar-glass, left and fallen;
- a whole map's pay;
- a ruler's Mark coming home, and Vonnra inscribing it.

**Done since the handoff:**
- **Two kits in logic** (`Rpg/Kits.cs`). The night's goes on wherever the ember burns and holds only what differs from the day's. UI design builds the switch.
- **The atlas's pay re-measured** with the lab's map sweep:
  - the people's own cut from 74–102 a map to 15–18;
  - lamplings maps pay iron, not the scars' fire;
  - charts and Marks left lying now come home.
- **Switches:** `--clear T` (a whole map felled) and `--leave T` (the way out). A map's pay is logged.

## Next, in order

1. **The bench as two panels: built and seen** (`docs/ui_review/bench_v2/`; design 20.8). UI design is judging it. Polish from their notes; their tab art isn't merged here yet.
2. **Icons:** judge UI art's repaints (red_cord, lamp_glass, scar_glass) in the game: the haul, the satchel, Vonnra's table.
3. Break down a Legendary for 5 iron and 3 shards, once the loot lead's Legendaries are in.

## Decisions (why in design 17, 20.2, 20.7, 20.8)

- Decisions 1–30 (design 17) stand.
- **The kit follows the place, and the night kit holds only what differs.** This means no swap and no dressing twice.
- **Map materials come from what carries them** (ruler 3, keeper 2, leader 1). A quarter of every kill flooded the pouch.
- **The atlas pays iron and the scars pay fire.** Lamplings carry the Dig's iron in maps.
- **Shelf prices stand.** Maps pay about 1,000 gold an hour, mostly from Kerchief maps.
- **The bench's crafts are grouped by verb under counted tabs.** A dozen cards at once ran off the screen.

## Agreed with others

- **UI design** (`a4fdbc49786ba8b7f`):
  - the kits' switch is theirs and the logic mine;
  - I build the two-panel bench and they judge it;
  - `--clicks`: `h` is hover (theirs), `p` is press-and-hold (mine).
- **Creatures** (`af551cacc6292152f`): Vonnra's own model is on their should-make list, after the boar, the Ford-Warden and the average man and woman.
- **Loot** (`a9a9c345a35e1fcad`), told:
  - `Gather` now brings charts and Marks home;
  - `MapSpoils` misses finds sent to the storeroom (theirs);
  - lamplings' non-gear material in maps is optional for them to move to iron.
- **Combat** (`a5115633c7006e4d4`), told: the map material change in `MapRun.OnLoot`, and `ClearNow`.

## Notes for other areas

- **Pictures:**
  - `--items DEF:RARITY:AFFIX@GRADE+...:MARKS`, `--near ID`, `--open forge:ID --anvil DEF`;
  - `--clicks pX:Y` holds a press for a second;
  - `--zone map ... --lab --clear 3 --leave 16`.
- **Kits API:** `Kits.On/Piece/HasOwn/Shown/Put/Clear/Wear`, and `Journey.EquipKit/UnequipKit`. A piece in the kit not on is `Store.Kit` (`Where.Aside`).
