# Handoff: classes (session 13: Burns Twice's aim and shove, the Toll seen with nothing near, phase-6 roles, the drift)

Written by the thirteenth classes lead (13 October). Branch `classes-10` (worktree `agent-ad0c69063d34fa8de`, from integration 3935476c), last commit on the last line of git log. Scratch `S/` = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\59a43b82-cb5d-4a5a-bb8d-db67086387ea\scratchpad\classes\`. Older: `O/` = 1515c1de-...\scratchpad\classes (base11 at `O/s2/base11.jsonl`).

## The owner (13 October)
- "why wouldn't flare shorten things? its supposed to be epic. an 'oh shit' button. a planned 'BOOM' button. a 'clear the whole room' button."
- "flares in general don't need to be big boss hits - they are specialized. *most* are for arena mode type screen clears or saves etc - but some can be single target (or one or the other based on context). but pushing a flare should always do something visible."
- Coordinator's rulings: never tune a Flare into an invisible damage bump. Balance around fights without good Flare use, not by blunting the Flare.

## Start here
1. **Batch W** (`bash S/w.sh`, may still be running; `S/w/q.out` ends "ALL"). It compares Burns with the aim fix (bal15, 46ab377d) against the old binary (bal13), arcanist kindler, on fresh seeds 201-248. Outputs: `S/w/arena.txt` (wins and deaths by tier), `crowd_13/15.txt` (look at "flare kills" a press: it should match bal13 within about 3%), `story.txt` (Act 1).
   - If deaths still rise by more than noise (first batch `S/s`: 11 deaths of 240 before, 20 after), find which part does it. `S/v/arena_A.txt` (no aim, with shove) and `arena_B.txt` (aim, no shove) each had about 15 deaths, so the old binary's 11 may have been lucky.
2. **Act 1 for the arcanist ran 7.7% shorter** with bal14 (`S/s/story.txt`). `S/v/story.txt` row st_C (no boss stagger from the shove) says whether the 0.15 boss stagger does it. If it does, and the owner's "Flares shorten things" doesn't cover it, set "shoveStagger" to 0 in lamps.json. The Flare lead only asked for the shove on survivors.
3. Then send the coordinator one **MERGE REQUEST: classes-10@<sha>** (dotnet test passed 885/893 before the last two commits; run it again). In the same message, send **the phase-6 plan for the owner**: judge 7 PASS WITH FIXES, fixes applied (f4f8d3b8). Its final owner lines are below; fill in line 6.
4. **Tell the Flare lead** (a422b108a0fdfb259, flare-1) that the ember now bends to the thickest pack within 3 m of its aim when its target fell before landing (data "aimBend" 3, default in code). They were told about aim, shove and the Toll on 440c4a90 and replied that they'll wire both once classes-10 reaches integration.
5. **The drift** (`S/bis`, `bash S/bis.sh`; it waits for nothing now). It runs Act 1 never pressing (SU_NOPRESS=1 patches UseFlare) at health 103/130/100/109, 32 seeds, at integration commits p0 9cbc654c (pre-Flare), p1 90dd4062 (the Flare added), p2 cc228199, p3 b888da5c, p4 14dda627, p5 a86814cc. Summaries are `S/bis/sum_*.txt`, and `sum_all.txt` at the end. stc.py was patched for files without a Flare share.
   - **Found:** p0, the real pre-Flare game, runs boss fights of 233 s with 0.125 falls a night. Against base11 that is +14.3%, falls 0.030 -> 0.125. Today never-pressing (`S/n/noD.jsonl`) runs 225 s with 0.089.
   - **So base11 is not the pre-Flare game,** and today's never-press game is shorter and safer than the real pre-Flare one. base11 runs 204 s; `O/s2/cur11` (the 11 Oct game with the Flare) runs 184 s. `S/peek2.py` prints these per file.
   - **Next:** read p1-p5. Where the never-press time drops toward 204 s and where it rises again tells what base11 was and whether any change since is a regression. The likely answer is that base11 was a build whose phase-1 power (dash forms, reflexes) helped without the Flare, and later tuning moved it.
   - **Report to the coordinator before anything is tuned:** the 12-13 Oct health ("back to pre-Flare length") was tuned to base11. If base11 isn't pre-Flare, the owner's Act 1 lengths need a fresh reading.

## Owner lines (judge 7's final; line 6 to fill in)
1. Flares should shorten fights, as you said. We tune each night so a player who never uses Flares well still gets through, and a good press sits on top. No Flare is ever tuned down into a damage bump you can't see.
2. Each Flare has one job. Most clear the room or save the hero (six clear, four save). Two go for the one that matters: the Butcher's Bill, and the Road's Toll, whose last four cuts go to the strongest. Four choose by what's near: the crowd, or the boss when there is one. Every press shows something, even with nothing in reach.
3. The Flares not built yet are stand-ins that hit everything in reach, so once built a few will clear less. For example, One Arrow becomes a 30 m line through the crowd instead of hitting everything within 30 m.
4. You asked for one Flare per spec. Four specs have theirs. The first wave builds the other four (the Long Cut, Drag Them Under, the Branding, One Arrow), plus the Butcher's Bill, which a new butcher starts with (the Hour opens at depth 12). Shall we build the first wave?
5. The Long Cut, Drag Them Under and One Arrow use a greatsword, a hooked chain and a longbow, which come later. For the Flare, the weapon would form in the hero's hands in the calling's color and vanish after. Is that look okay?
6. Four modifiers are replaced, so at most one of each Flare's three only changes a number. The new four: Hard Winter's Thaw-Burst (a shatter shatters the frozen within 3 m), the Branding's The Eye (the boss's brand stays 6 s and bursts again whenever a mark passes to it), Through and Through's Free Hands (press the Flare again to cut every notch now; it ends there), One Arrow's Through the Heart (it stops in the first champion or boss it hits, and its three splits turn back into it). Okay to use the new four?
7. Until Act 1 is done, Light my way suggests at most one gentle modifier per Flare, so Act 1 plays as tuned. The strongest ones, like Called Down, can still be picked by hand.
8. Each spec's second Flare (the other seven, waves 6b and 6c; 6c waits for the new weapons) will be a separate yes later.
9. Done today, on the classes branch: Burns Twice aims each ember just before it lands, and its last ember throws back whatever still stands about 3 m (a boss only staggers). The Road's Toll, pressed with nothing near, now cuts a kata of twelve along the aim.

## Done this session (classes-10)
- 440c4a90: Burns Twice "aim" and "shove" (Flare.cs TickFlare runs aims and blows in time order; FlareStaged.cs FlareAim, EmberPick, BurnsTwiceBlow, BurnsShove; lamps.json beat "aim", args shove, shoveStun, shoveStagger). 2 tests.
- 955c64d3: the Toll's empty cuts along her aim (`flareAngle` stored at the press). 1 test.
- 10740955 and f4f8d3b8: CLASSES §7 phase-6 plan: Role and "nothing near" columns, the roles paragraph and the two rules, judge 7's fixes.
- 46ab377d: the aim fix. Aiming four embers ahead had cost a press about 15% of its kills (arena crowd `S/s`, `S/v` B). Fixed by counting the ice round falling embers as broken; checked on a synthetic crowd (37.7% against 38.4% killed at x2 health).

## Gotchas
- Isolation: no `$VAR` inside commands that run git, sed or find, and no compound `cd && git`. Write a script to `S/` and `bash` it. Python scripts that take paths as arguments are fine.
- Harness copies: `S/bal13` (classes-9), `S/bal14` (440c4a90), `S/bal15` (46ab377d). Data comes from the cwd's `godot/data`, so data variants run from a copy (`S/v/<V>/godot/data`, `S/v_data.py`).
- Bisect builds: `python S/bis_prep.py <tag> <commit>` exports logic, data and balance with `git archive` (no worktree, so the cap is safe) and patches the never-press switch and the health.
- Every arena death figure at 48 runs a tier is noisy (±4 points). Read Flare kills a press (about 1,100 casts) first.
