import io
ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad059388f00c19f9f"


def edit(rel, pairs):
    p = ROOT + "\\" + rel
    s = io.open(p, encoding="utf-8", newline="").read()
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a[:80])
        s = s.replace(a, b)
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print("edited", rel)


edit(r"docs\team\skills.md", [
    ("""## Current state (2026-10-05)

Tests green (747). Everything below seen at 1920×1080 unless it says otherwise.""",
     """## Current state (2026-10-05, handed off; see `docs/handoff/skills.md`)

Tests green (747). Everything below seen at 1920×1080 unless it says otherwise."""),
    ("""  chains and beams make sound now (they were silent). *Built; checked only as spectrograms of the
  game's own mix (`--wav`), not heard.* The owner or main session must listen.""",
     """  chains and beams make sound now (they were silent). *Built; checked only as spectrograms of the
  game's own mix (`--wav`), not heard.* Eight skills taped: each has its own shape, none clips
  after the palm and pot were lowered (they hit 1.0). The owner or main session must listen.
- **Seen after the last fixes**: Gyrestorm's thin wind ring; Aegis Wheel's break as a shockwave;
  Thunderclap's burst blue. **Still wrong**: Rend and Mend and The Harrowing still read as hoops
  (their open sweeps are wide bright arcs); Moonfall was pink-white balls from the arcane school's
  burst under each moon (now skipped; not yet seen); Frostfire's frost ribbon drew pale squares
  even with round glints (removed; not yet seen)."""),
    ("""1. Look at the queued shots: the way out's band late in the won night, Frostfire's frost ribbon,
   the sound spectrograms.
2. Evolutions (all swept, sheets in `vfx/v1/`): the white hoops (Rend and Mend, The Harrowing,
   Whirlwind's spiral; Gyrestorm's wind ring is thinned, not yet seen), then the rest by grade.""",
     """1. Shoot Moonfall, Frostfire Comet and the won night's foot and way-out band (`won5` was shot,
   not yet looked at) after the last fixes.
2. Evolutions (all swept, sheets in `vfx/v1/`): the reaving novas' hoops (Blades arcs: thinner and
   darker, or a scythe that is seen to travel), Skybreak's and Ford Ice's white bars, Sunlance's
   cream beam, Winter Ward's and Absolute Zero's rings, the Wild Hunt's green rings."""),
])
