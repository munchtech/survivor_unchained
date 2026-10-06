"""The design doc: the Hollow's lengthened numbers and the share re-done on ten minutes (run from the worktree root)."""
p = "docs/design/STORY_NIGHTS_AND_TIME.md"
s = open(p, encoding="utf-8").read()
reps = [
("""- **Measured so far** (combat's first small runs of the Hollow, tier 1, plain hands): the night
  is about 5 minutes, not 12 (the way in 1.6 against 6–9, the boss 2.5–3.5); won 75%; under half
  health on the way in 50–63%, against 20–35%. Next, combat lengthens the stages with more to do
  (never more health) and moves the danger to the boss. Until the night measures 10–14 minutes,
  nothing below leans on 12.""",
"""- **Measured** (combat's Hollow, lengthened with more to do, never more health; 64 nights, tiers
  1–4): the night is about 10 minutes planned and deft (8.8–11.2), 10.6–14.5 careless; the way in
  5–6 minutes (stages of about 105, 111 and 90–130 s), the boss 3.2–4.9; under half health on the
  way in 11–38% plain, 11–25% deft; no falls in a stage; won with the one rise 86–89% plain, 95–100%
  deft; 32 cards at the boss at every tier. **Decided: not padded to 12.** A tight ten is better
  than a padded twelve; the band is 10–14. The boss's first-life rate (78–88% for bots that never
  learn) is judged at the screen."""),
("""  - With 12-minute story fights and one fight a night, an eight-day Act 1 (four story fights, four
    table nights) is about 49% days. Shorter story fights push the share up, and this is that
    cost, stated plainly. These sums assume the 12-minute target, not the 5 minutes first
    measured; they are re-done when the Hollow measures at length.""",
"""  - With 10-minute story fights (as measured) and one fight a night, an eight-day Act 1 (four
    story fights, four table nights) is about 50% days: 160 minutes of days against 40 of story
    fights and 120 of table nights. Shorter story fights push the share up, and this is that cost,
    stated plainly. `WorldState.TimeIn` will say what players really do."""),
]
for a, b in reps:
    assert a in s, a[:60]
    s = s.replace(a, b, 1)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
