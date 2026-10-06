"""Final handoff and status edits (run from the worktree root)."""
p = "docs/handoff/experience.md"
s = open(p, encoding="utf-8").read()
a = s.index("## In progress, and next")
b = s.index("## Decisions (with why)")
new = """## In progress, and next

1. **The Hollow at full resolution** with combat (`afe45df4957917614`). Seen whole on the game's
   autopilot (`scratchpad/experience/merge_runs.sh hollow`): clough 0–2:00, water 2:30–4:50, the
   drive 5:00–11:50, the boss from 11:50; ember about 25 at the boss. The drive was the problem
   ("go through the wolves, never the gap" is against instinct and untaught); combat is fixing it
   (bounded by drives, a first lesson drive, barks). Judge their push at the screen: the drive,
   the deadfalls (no wood or flame yet), the ring, the cold, his lying down and the two prompts,
   the camera at 27 m on the den floor. Frames: `docs/experience/hollow_drive.jpg`.
2. **The screen's noise in the Hollow and late nights:** big salmon hatched hostile discs, the
   warden's white ringed projectiles, damage numbers overlapping in clusters (skills' branch
   `a94ac6b67f1279213@8447124b` has its number fixes, not yet merged here: judge together).
3. **Judge the rest of the landed merges:** combat's maps and the strongbox through the chest
   ceremony (`merge_runs.sh map`; `ChestCeremony.ColourOf/DetailOf` want Gear's rarity colour and
   name); animation's death poses (seen once in the dark, varied; judge in light, 30 bodies).
4. **The run-ups' danger** with combat: 10–20% of runs under half health in 7–10, 17–20, 25–28.
5. **UI design** (`aab47bfdab5955dac`) builds the day dial and the fall's two choices next; judge
   their frames (`--clock 590/710/890/1070`; the fall switches are in the status page).
6. **Still to see on the clock:** a full day on the autopilot for the dawn-to-day turn; Maeca and
   the Verge's day packs change only on re-entry (after a night out in the wood).

"""
s = s[:a] + new + s[b:]
s = s.replace("""- **Fixed from frames:** dusk darker than night (now a golden hour), moths drawn a metre across
  (`BillboardKeepScale`), the fall's fade greying its choices, the crowd's status read (rime and
  fire over char, `vat.gdshaderinc`), the struck flare's white capped at four bodies a frame
  (`CrowdView`).""", """- **Fixed from frames:** dusk darker than night (now a golden hour), moths drawn a metre across
  (`BillboardKeepScale`), the fall's fade greying its choices, the crowd's status read (rime and
  fire over char, `vat.gdshaderinc`), the struck flare's white capped at four bodies a frame
  (`CrowdView`), the crit's burst (warm gold, three a breath, small at her elbow), the ember
  stones (gems, not popcorn: glow at their colour, not 2.6 times it), every ruler painted with
  the nemesis's orange (now only a true nemesis, `Named.SourceHero`).""")
s = s.replace("""- **Evidence** in `docs/experience/`: `dusk_gold_town`, `nightfall_town`, `fall_choices`,
  `frozen_rime`, `burning_char`.""", """- **Evidence** in `docs/experience/`: `dusk_gold_town`, `nightfall_town`, `fall_choices`,
  `frozen_rime`, `burning_char`, `hollow_drive`, `greymuzzle_grey`, `ember_gems`.""")
s = s.replace("""3. Scratchpad `experience/`: `clock_runs.sh`, `tod.sh`, `status_runs.sh`, `crit_runs.sh`,
   `ba.py`, `runlog.py`, `play.py`, `tsheet.py`, `crop.py`, `keep.py`.""", """3. Scratchpad `experience/`: `clock_runs.sh`, `tod.sh`, `status_runs.sh`, `crit_runs.sh`,
   `merge_runs.sh`, `ba.py`, `runlog.py`, `landed.sh`, `play.py`, `tsheet.py`, `crop.py`,
   `keep.py`.""")
s = s.replace("""- **Skills** (successor to `a94ac6b67f1279213`): the crit burst was left to us; Cinderfall's blast
  is theirs.""", """- **Skills** (successor to `a94ac6b67f1279213`): the crit burst and the struck flare are ours, done;
  Cinderfall's blast, the hostile discs and the projectiles are theirs.""")
open(p, "w", encoding="utf-8", newline="").write(s)

p = "docs/team/experience.md"
s = open(p, encoding="utf-8").read()
a = s.index("**Next:**")
b = s.index("**Harness**")
new = """**Since:** the crit's burst (warm gold, three a breath, small at her elbow); the ember stones as
gems, not popcorn; rulers in their own colour (Greymuzzle grey, not orange); the Hollow seen whole
(`hollow_drive.jpg`, `greymuzzle_grey.jpg`, `ember_gems.jpg`): the drive was the problem, combat
is fixing it.

**Next:** see `docs/handoff/experience.md` "In progress, and next" (the Hollow after combat's push,
the screen's noise with skills, maps and the strongbox, the run-ups, UI's dial and fall).

"""
s = s[:a] + new + s[b:]
s = s.replace("Took over from `ad1f5623590e09883`. Tests green (661).", "Took over from `ad1f5623590e09883`. Tests green (665). **Handed off** at the context limit:\n`docs/handoff/experience.md`.", 1)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
