# H4: seams (experience with cinematics and a UI worker)

Lead: `su-lead-high` in worktree `seams-h4` (branch `seams-h4`). Est 1M. Read first: `docs/handoff/lead_brief.md`, `docs/team/DEMO_PLAN.md` "Phase 3 verdict" (your row), `docs/team/DEMO_GATE.md` "Phase 3" N8, N9 (the way out; the night length is H1's), N10-N15; `docs/handoff/experience.md` top (Experience 12's tools: `tools/experience/demo_run.py`, the goal system `Goals.cs` / `GoalMarks.cs`), `docs/handoff/cinematics.md` top (the cue data, Cinematics 12's list in `docs/team/CLOSEOUT.md` wave 2), `docs/team/ui_design.md` top.

## The owner's words
"the transition out of the cinematic into play is jarring". "at the lamps are lit stay where they reach part, the pan over to the side looks awkward". "the cinematic after killing warden is clunky - the walk up and stuff". "in the town cinematic I kept walking into a wheelbarrow it was funny". "first boss fight doesn't have 3 lamps, it has 1 lamp that refills". "the exit wasn't clear". "the way the skills flash is awkward". "some clunky ui stuff, missing head in inventory (lol)".

## The fixed list
1. **One rule for every cinematic-to-play cut** (the capability): the camera eases from the last shot into the play camera over about a second, her pose carries across (no pop to idle), the HUD fades in after the camera lands, control returns at the end of the ease. In the cue system (`Prologue.cs` and the C0x cue data), not per cinematic. Every cut on the demo path (SB00 > C01 > Wake, C02/C03 around the Warden, C04 > the Waystation, the arena entry after the Great Blessing) goes through it.
2. **The Ford-Warden's intro pan** (`Prologue.cs` ~1205: "Lamps are lit... stay where they reach..." at 1.4 s): restage the pan (what it shows, and why it moves), one round.
3. **C03's walk-up** after the Warden falls, with Cinematics 12's cheap data items ("THE FORD-WARDEN" labelled before his s11 reveal; the s6 title card into s8). C04 A0/A8b and the drowned-woman cue: closed as known unless they are one line each.
4. **C04's wheelbarrow:** her walk into the Waystation runs her through a prop, or hands her control with one in the way: clear the path or move the prop; a check that the walk-in path is clear of colliders.
5. **The three lamps read as three** (the fight has three pylons and a freeze callout at `Prologue.cs` ~518; the owner saw one lamp refilling): a three-mark lamp count on his bar that goes out one by one and relights when his channel finishes, and the pylons spaced and lit so all three are in the play frame; re-check the callout's aim.
6. **The way out, louder:** from the win, a banner with its line and arrow together (Experience 13's "the banner leads its arrow by 1.6 s"), a sound hook for H3 (`Ev.WayOutOpen` or the existing announcement), what leaving takes said at the ring; the Great Blessing after she has seen the place, not over the entry black.
7. **The skill ready cue** (UI worker): one cue, a glow that settles, not a flash; judged in motion (a strip).
8. **The inventory head** (UI worker): the figure is drawn without her head; fix it and add a check that the figure is whole (bounds against the figure's head bone).
9. Day 1's clock waiting on Rook (Experience's open item): a player who walks past Rook stays at "Dawn, Day 1": start the clock on arrival.

## Judge and exit
A replay of the demo path with `demo_run.py` after the fixes; one `su-lead-max` judge at xhigh on contact strips of every cut (items 1-4) and the lamp fight (5), with the whole-frame question first and "is anything clunky?" second. Round cap 2 per item. The exit: the owner's next run has no "clunky".

Rules: Godot shots only through `tools/turn.py`; commit as you go; tests green; UI looks beyond these two items belong to H2. Report to main.
