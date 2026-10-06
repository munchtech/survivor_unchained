"""The design doc: combat's measured build and first runs (run from the worktree root)."""
p = "docs/design/STORY_NIGHTS_AND_TIME.md"
s = open(p, encoding="utf-8").read()
reps = [
("""- **The build.** Embers are paid about 2.5 times faster (combat's number), so she meets the boss
  with about what a table night has at minute 20. That build is the boss's yardstick: about 3–4
  minutes at par, against the table rulers' 60–120 s.
  - The waves are finite and creature levels are fixed per beat. So the build at the boss is set by
    the content, a slow beat is no harder, and nothing is farmed.""",
"""- **The build.** She meets the boss with about what a table night has at minute 12 (combat's,
  measured: about ember 30 and 32 cards). Minute 20 was the first aim, but by then a table night
  has killed some 20,000, which a short night in a small place cannot feed and should not try to.
  That build is the boss's yardstick: about 3–4 minutes at par, against the table rulers' 60–120 s.
  - The waves are finite and creature levels are fixed per beat. Each stage is a finite crowd
    softened to the table minute it stands for (2, 6, 10), with an ember floor at its end, so the
    build at the boss is set by the content, a quick stage is no weaker night, and nothing is
    farmed."""),
("""- **Why this length.** It is long enough for a build to be earned and tested, and short enough to
  replay a fall without dread. It is also a third shorter than today's 20 minutes, so the story
  never sits behind long arenas.""",
"""- **Why this length.** It is long enough for a build to be earned and tested, and short enough to
  replay a fall without dread. It is also a third shorter than today's 20 minutes, so the story
  never sits behind long arenas.
- **Measured so far** (combat's first small runs of the Hollow, tier 1, plain hands): the night
  is about 5 minutes, not 12 (the way in 1.6 against 6–9, the boss 2.5–3.5); won 75%; under half
  health on the way in 50–63%, against 20–35%. Next, combat lengthens the stages with more to do
  (never more health) and moves the danger to the boss. Until the night measures 10–14 minutes,
  nothing below leans on 12."""),
("""  - With 12-minute story fights and one fight a night, an eight-day Act 1 (four story fights, four
    table nights) is about 49% days. Shorter story fights push the share up, and this is that
    cost, stated plainly.""",
"""  - With 12-minute story fights and one fight a night, an eight-day Act 1 (four story fights, four
    table nights) is about 49% days. Shorter story fights push the share up, and this is that
    cost, stated plainly. These sums assume the 12-minute target, not the 5 minutes first
    measured; they are re-done when the Hollow measures at length."""),
]
for a, b in reps:
    assert a in s, a[:60]
    s = s.replace(a, b, 1)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
