W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec'
def edit(name, pairs):
    p = W + '\\' + name
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (name, old[:90])
        s = s.replace(old, new, 1)
    open(p, 'w', encoding='utf-8', newline='').write(s)

edit(r'docs\UI_DESIGN.md', [
("""**Done**: a medallion with the level; the bar; the word under it, **EMBER**
(ember) or **EXPERIENCE** (day blue); a leading edge that brightens as the
level nears. **Next** (from the feel work, S-06): the fill eased every frame
rather than stepped at 12 Hz; a pulse from 85%; a white flash and a visible
overflow on the level.""",
"""**Done**: a medallion with the level; the bar; the word under it, **EMBER**
(ember) or **EXPERIENCE** (day blue); a leading edge that brightens as the
level nears; the fill eased every frame (not stepped at 12 Hz), breathing
from 85%, and on a level it fills, flashes white and drains to what carried
over; the kill count pops as it climbs (the feel work's S-06)."""),
("""nothing in a town); gold stays. **Next** (S-21): the night's phases named
on the clock (Dusk, Gloaming, the Witching, Ashfall, the Coming, Beyond).""",
"""nothing in a town); gold stays. The night's phases are named under the
clock, each in its colour, popping in as they turn: Dusk, Gloaming, the
Witching, Ashfall, the Coming, Beyond (S-21)."""),
("""against what stays. **Next** (S-16): the cause ("slain by a Kerchief
cutthroat at 24:13"), the near miss ("6 minutes from Redcowl"), the run's
peak. **Why**""",
"""against what stays; how it ended in a line: who brought you down and when,
and how near what ruled it was ("6 minutes before the Pack-Mother would have
come"; S-16). **Next**: the run's peak (the biggest blow, the evolution's
minute), which needs the fight to keep them. **Why**"""),
("""| Bars that flow; glow from 85%; flash on the level | feel S-06 | Adopt (4.1): presentation only |
| The night's phases named on the clock | feel S-21 | Adopt (4.2) with the countdown |
| An end screen that tells the run's story | feel S-16 | Adopt (7.9); the cause needs the killer recorded in `ArenaResult` |""",
"""| Bars that flow; glow from 85%; flash on the level | feel S-06 | **Done** (4.1) |
| The night's phases named on the clock | feel S-21 | **Done** (4.2), with the countdown |
| An end screen that tells the run's story | feel S-16 | **Done** for the cause and the near miss (7.9); the run's peak is next |"""),
("""2. The feel work's interface pieces (section 9), bars that flow first.""",
"""2. The feel work's remaining interface pieces (section 9): the chest panel, the evolution's name card."""),
])

edit(r'README.md', [
("""| Pack · Self · Journal · Map | I (Tab) · C · J · M | View · then Menu |""",
"""| Pack · Self · Journal · Map | I (Tab) · C · J · M | View · then LB / RB |"""),
])

edit(r'godot\README.md', [
("""- `--open inventory|character|journal|map|pause|rest|stash|shop:ID|chapter|all`,
  `--open talk:ID`, `--open draft`: a screen, a conversation or the level-up
  draft opened a moment in (`--every T` between several); `--bare` hides the
  world, for quick pictures of the interface;""",
"""- `--open inventory|character|arts|journal|map|maps|pause|rest|stash|shop:ID|chapter|all`,
  `--open talk:ID`, `--open draft`, `--open result` (a won arena's end, in
  an arena): a screen, a conversation or the level-up draft opened a moment
  in (`--every T` between several); `--bare` hides the world, for quick
  pictures of the interface; `--keys A,B,...` then presses those actions in
  turn (`Right`, `Confirm`, `SubNext`...), and `--pad` as from a pad (focus
  ring and pad prompts shown); `--items ID[:RARITY],...` and `--xp N` fill
  the pack and give experience first;"""),
("""- `src/Ui/`: the look shared by every screen (`Style.cs`, the icons in
  `Glyphs.cs`),""",
"""- `src/Ui/`: the look shared by every screen (`Style.cs`, the icons in
  `Glyphs.cs`, painted art by name from `art/ui` in `UiArt.cs`, with the
  drawn look as the fallback: `docs/UI_ART_BRIEF.md`), focus moved by keys
  and pad on every screen (`Nav.cs`), the corner map (`Minimap.cs`), arrows
  to what matters off screen (`EdgeMarks.cs`), slots that drag and drop
  (`SlotView.cs`); the design of all of it in `docs/UI_DESIGN.md`,"""),
])
print('done')
