from ed import sub
D = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab0b263c720bdbda8\docs\CRAFTING_DESIGN.md"
T = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab0b263c720bdbda8\docs\team\crafting.md"
sub(D, [
("""- **To see it**: `--zone map --tier T --people P --lab --clear 3 --leave 16` fells a whole map at once and
  logs what it paid ("map paid: ..."); `--zone arena --minute 95 --won --facts stream.clear=true --lab
  --leave 2` is a scar left an hour past the win.
""",
"""- **To see it**: `--zone map --tier T --people P --lab --clear 3 --leave 16` fells a whole map at once and
  logs what it paid ("map paid: ..."); `--zone arena --minute 95 --won --facts stream.clear=true --lab
  --leave 2` is a scar left an hour past the win.

**The bench as two panels** (the owner-approved greybox; `Forge.cs`; shots in `docs/ui_review/bench_v2/`):
- Theirs at the left: the person as a strip (likeness, name, where, mood and prices, what they say), the
  anvil (the piece, where it is worn, its heat), its seams, then what they can do as cards two to a row,
  their terms along the foot. Yours at the right: worn (with the kits' switch once there are two),
  carried, the stores and the purse (UI design's `PackBlock`). The crafter stands live in the world between:
  the view looks at them (`Overlay.CameraLook`), nearer, set in the gap.
- **The crafts are grouped by what is done**, under tabs that count what can be done now (Temper 1 ·
  Work in 4 · Cage 4 · The piece 3). All of a smith's crafts at once ran to a dozen cards and off the foot
  of the screen; one kind at a time keeps the panel on the screen, and the counts say the rest. Snib's
  steeping is one wide card with the odds inside it.
- Every bench is seen: Brannoc (and "Make me one" as the anvil's other tab), Wenna, Vonnra, Snib and the
  Wayfinder's table. A piece worn by night says so on the anvil.
"""),
])
sub(T, [
("""1. **The bench as two panels** (greybox_bench.png), built in `Forge.cs` on UI design's kit (`Fitted`, `Kit.*`, `PackBlock`, `TipBeside`):
   - left: the person as a strip, the anvil, and the crafts as two-column cards;
   - right: your gear with the kit switch;
   - the smith live in the world between.
   UI design judges the shots.
2. **The Mark card** shows the ruler's thing's painted icon (the Tally-Bone), not a glyph.
3. **Icons:**""",
"""1. **The bench as two panels: built and seen** (`docs/ui_review/bench_v2/`; design 20.8). UI design is judging it. Polish from their notes; their tab art isn't merged here yet.
2. **Icons:**"""),
("""4. Break down a Legendary for 5 iron and 3 shards, once the loot lead's Legendaries are in.""",
"""3. Break down a Legendary for 5 iron and 3 shards, once the loot lead's Legendaries are in."""),
("""- **Shelf prices stand.** Maps pay about 1,000 gold an hour, mostly from Kerchief maps.""",
"""- **Shelf prices stand.** Maps pay about 1,000 gold an hour, mostly from Kerchief maps.
- **The bench's crafts are grouped by verb under counted tabs.** A dozen cards at once ran off the screen."""),
])
