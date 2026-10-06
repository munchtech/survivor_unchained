from ed import sub
D = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab0b263c720bdbda8\docs\CRAFTING_DESIGN.md"
T = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab0b263c720bdbda8\docs\team\crafting.md"
sub(D, [
("""- Every bench is seen: Brannoc (and "Make me one" as the anvil's other tab), Wenna, Vonnra, Snib and the
  Wayfinder's table. A piece worn by night says so on the anvil.
""",
"""- Every bench is seen: Brannoc (and "Make me one" as the anvil's other tab), Wenna, Vonnra, Snib and the
  Wayfinder's table. A piece worn by night says so on the anvil.
- **Then remade as type** (the owner's tightened rules, through UI design: no boxes holding words, words
  as type rather than buttons): the seams are ledger rows (the grade's numeral, a fine rule, a thin ember
  mark at the anvil's seam); each craft's name is its act (held for what cannot be undone), with before
  and after (the after in ember) and its cost in small type; the likeness fades into the panel.
- **The heat is a chain** of UI art's links, a link a point: hot for what is left, cold iron for what is
  spent. A craft under the pointer warms the links it would take; struck, they cool, the last first. The
  chain is the game's motif doing a job here: a piece's working life is its hot links.
- A Legendary breaks down for five old iron and three shards, wherever it is broken (`Crafting.Yield`),
  and Brannoc has his own words over it (the story lead's).
"""),
])
sub(T, [
("""1. **The bench as two panels: built and seen** (`docs/ui_review/bench_v2/`; design 20.8). UI design is judging it. Polish from their notes; their tab art isn't merged here yet.
2. **Icons:** judge UI art's repaints (red_cord, lamp_glass, scar_glass) in the game: the haul, the satchel, Vonnra's table.
3. Break down a Legendary for 5 iron and 3 shards, once the loot lead's Legendaries are in.""",
"""1. **The bench**: two panels, then remade as type with the heat as a chain (design 20.8). Waiting on UI design's push (even 28 margins, bare grids, engraved worn slots, `HeldWord` for the held acts); merge it, swap the held acts to `HeldWord`, reshoot every bench and send 1:1 shots.
2. **Icons:** judge UI art's repaints (red_cord, lamp_glass, scar_glass) in the game: the haul, the satchel, Vonnra's table.
3. Measure the endgame's economy (scars and maps mixed, hours): shards and iron in against charts, marks, cages and rekindles out."""),
])
