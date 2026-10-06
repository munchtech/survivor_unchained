"""Status page: combat's story nights merged, the fall staged (run from the worktree root)."""
p = "docs/team/experience.md"
s = open(p, encoding="utf-8").read()
reps = [
("""- **Seam for combat:** `IZoneHost.StoryFall(risesLeft, rise, letGo)`; one rise in Act 1 only.""",
"""- **The fall in a story night, staged** (`Game/GameFall.cs`, on combat's `StoryNight`, merged at
  `aa68f38e`): the picture darkens and the world holds; with a rise left, "Get up" (confirm or the
  use key) or "Let the night go" (back), no page; getting up is a short fade to the checkpoint and
  the counted words (`RiseLine`); with none left, the night is lost and its result follows."""),
("""5. Pausing: the clock still in talk, the pack, the map, the shop, the rest page and cutscenes.""",
"""5. Pausing: the clock still in talk, the pack, the map, the shop, the rest page and cutscenes.
7. A fall in the Hollow (`--stage 3` for the boss): the darkening, the two choices (keys and pad),
   the fade to the checkpoint and "You get up."; then a second fall with none left."""),
("""1. The game's staging of `StoryFall` when combat's runtime lands (fade, "You get up.", the card).
""", """1. With combat: the Hollow measures 5 minutes, not 12, and 50–63% dip under half on the way in
   (target 20–35%); combat lengthens the stages (more to do, not more health). The 40% sums wait.
"""),
]
for a, b in reps:
    assert a in s, a[:60]
    s = s.replace(a, b, 1)
s = s.replace("Took over from `ad1f5623590e09883`. Tests green (631).", "Took over from `ad1f5623590e09883`. Tests green (661).", 1)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
