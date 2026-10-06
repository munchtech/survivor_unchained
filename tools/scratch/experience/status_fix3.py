"""Status page: the waking on Chid's bench, story's final lines (run from the worktree root)."""
p = "docs/team/experience.md"
s = open(p, encoding="utf-8").read()
reps = [
("""- **A story fight lost** (`ArenaResult.WakesInTown`): she wakes at the Last Lamp a day on,
  healed, with the morning's news (`Journey.WakeAfterLoss`, Waystation arrival `carried`).""",
"""- **A story fight lost** (`ArenaResult.WakesInTown`): she wakes on Chid's bench in the shrine a
  day on, healed (`Journey.WakeAfterLoss` calls story's `CarriedHome`); Chid's conversation tells
  the waking for that fight, then the town's morning lines.
- **Story's final words** in `Journey.DayLines`; a rise counted (`RiseLine`, story.rises); a
  second fight answered the same night says "straight on" (`FoughtTonight`); the night's card
  lists "Also out tonight"."""),
("""4. A story fight lost: the result, then the Last Lamp's door at dawn, healed, with the lines.""",
"""4. A story fight lost: the result, the shrine at dawn, Chid's waking, then the morning lines."""),
("""- **Story** (`a54dc034ed29f2e02`): owns OnSpare and the spare choice (Greymuzzle, Redcowl), now
  in `StoryFights.Spec`; the four `EndLost` lines need rewriting (she wakes in town a day on); the
  placeholders `DayLines.Nudge` and `DayLines.Carried`; the `Called` rules to check.""",
"""- **Story** (`a54dc034ed29f2e02`): its spare choices and lost lines are ported into
  `StoryFights.Spec` (`415e16f3`); edit the story fights' specs there, not in the Verge."""),
]
for a, b in reps:
    assert a in s, a[:50]
    s = s.replace(a, b, 1)
s = s.replace("Took over from `ad1f5623590e09883`. Tests green (624).", "Took over from `ad1f5623590e09883`. Tests green (631).", 1)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
