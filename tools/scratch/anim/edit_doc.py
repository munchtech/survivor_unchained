from pathlib import Path
p = Path(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa4f5fc266b043035\docs\ANIM_DESIGN.md')
s = p.read_text(encoding='utf-8')
old = """Animation Library through `HerPose` as before (the bull rush and chain
haul, for now)."""
new = """Animation Library through `HerPose` as before."""
assert old in s
s = s.replace(old, new)
old2 = """- PlayerView picks between them by her travel against her facing, turns
  her for it, and holds her facing in the air. Each art's landing gives
  way to her run as soon as she moves (`ArtTail`).
"""
new2 = """- PlayerView picks between them by her travel against her facing, turns
  her for it, and holds her facing in the air. Each art's landing gives
  way to her run as soon as she moves (`ArtTail`).
- `bull_rush` (9 m in 0.4 s): one driving stride cycle from the gait
  solver, pitched hard over it, the left shoulder and shield leading, the
  sword trailing low behind; at 0.4 s the lead foot slams down and the
  shield punches out, then the rebound into her guard.
- `chain_haul` / `chain_strike`: yanked off her feet by the chain arm and
  flown in nearly flat, legs trailing, the axe cocked high behind her
  head, held for however long the haul takes (28 m/s, 0.08 to 0.4 s); as
  the haul ends PlayerView plays the strike: feet swung down, the axe over
  and down two-handed, landing in the second frame, as the game's blow
  does on arrival.
"""
assert old2 in s
s = s.replace(old2, new2)
old3 = """- The bull rush and the chain haul still play the library's clips.
"""
assert old3 in s
s = s.replace(old3, """- The arts are keyed (no capture fitted the game's timing; Mixamo's vault
  was a vault over an obstacle). Kimodo's takes of the same prompts are
  being judged against them.
""")
p.write_text(s, encoding='utf-8')
print('ok')
