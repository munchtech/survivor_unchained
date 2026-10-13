# Handoff: classes (session 14: Burns re-measured, the Act 1 baseline named; waiting on the owner)

Written by the fourteenth classes lead (13 October). Branch `classes-10` (worktree `agent-ad0c69063d34fa8de`, from integration 3935476c), last commit on the last line of git log. The old scratch (59a43b82's `scratchpad\classes\`) isn't needed any more: the baseline and its tools are in the repo.

## The owner (13 October)
- "why wouldn't flare shorten things? its supposed to be epic. an 'oh shit' button. a planned 'BOOM' button. a 'clear the whole room' button."
- "flares in general don't need to be big boss hits - they are specialized. *most* are for arena mode type screen clears or saves etc - but some can be single target (or one or the other based on context). but pushing a flare should always do something visible."
- Coordinator's rulings: never tune a Flare into an invisible damage bump. Balance around fights without good Flare use, not by blunting the Flare.

## Start here
1. **Wait for the owner's phase-6 answers** (the owner lines below, relayed by the coordinator), and don't start wave 6 before they come. Once they do, follow CLASSES §7's phase-6 plan. Wave 6a runs in this order: the Branding, the two line Flares, the pull, the Bill. Stage each Flare, calibrate it on Act 1 against the baseline, then judge it.
2. **Done in session 14:**
   - **Batch W** measured Burns with the aim fix (46ab377d) against its true parent 3935476c: arcanist, fresh arena seeds 201-248.
     - Flare kills a press: +12-16% at every tier.
     - Act 1: -1.4%; the variant without the boss stagger ran -2.6%, so `shoveStagger` stays 0.15.
     - Arena deaths and damage taken: within noise (T4 L30 damage taken +22%, about 1.5 SE, 100% won).
     - The merge request went in at 30899ed3 (lead 13).
     - The Flare lead (a63cfc9c8f0bf5d01) has the aim, the bend ("aimBend" 3, so a Blow can land away from its aim's target), the shove and the Toll's empty cuts.
   - **Act 1 baseline "pre-Flare 11 Oct"** (CLASSES §7 Acceptance; adopted by the coordinator): 9cbc654c at health 103/130/100/109, never pressing, seeds 1-32, runs 233 s with 0.125 falls a night.
     - Rule: never pressing stays within ±3% of it with falls no higher; good use is clearly shorter.
     - Today: never pressing -0.1% (0.093 falls), careless -7.5%, good use -17.7% (0.034), bankers -24%. No re-tune.
     - Files: `tools/classes/out/prefl11.jsonl` (git-ignored; rebuild with `tools/classes/baseline_build.py`). Compare with `tools/classes/act1_match.py`, on matched seeds only.
   - **base11 retired:** it was 90dd4062 (the Flare's first build) with the Flare pressed and the 3 s press stun still in. A re-run of that build matched it on all 2048 seeds. The "drift" was base11 plus a seed-set mismatch: seeds 1-32 against 1-96 differ by about 2%.
3. dotnet test: 885 of 893 passed (8 skipped) at 30899ed3. The code hasn't changed since 46ab377d.

## Owner lines (judge 7's final; with the owner)
1. Flares should shorten fights, as you said. We tune each night so a player who never uses Flares well still gets through, and a good press sits on top. No Flare is ever tuned down into a damage bump you can't see.
2. Each Flare has one job. Most clear the room or save the hero (six clear, four save). Two go for the one that matters: the Butcher's Bill, and the Road's Toll, whose last four cuts go to the strongest. Four choose by what's near: the crowd, or the boss when there is one. Every press shows something, even with nothing in reach.
3. The Flares not built yet are stand-ins that hit everything in reach, so once built a few will clear less. For example, One Arrow becomes a 30 m line through the crowd instead of hitting everything within 30 m.
4. You asked for one Flare per spec. Four specs have theirs. The first wave builds the other four (the Long Cut, Drag Them Under, the Branding, One Arrow), plus the Butcher's Bill, which a new butcher starts with (the Hour opens at depth 12). Shall we build the first wave?
5. The Long Cut, Drag Them Under and One Arrow use a greatsword, a hooked chain and a longbow, which come later. For the Flare, the weapon would form in the hero's hands in the calling's color and vanish after. Is that look okay?
6. Four modifiers are replaced, so at most one of each Flare's three only changes a number. The new four: Hard Winter's Thaw-Burst (a shatter shatters the frozen within 3 m), the Branding's The Eye (the boss's brand stays 6 s and bursts again whenever a mark passes to it), Through and Through's Free Hands (press the Flare again to cut every notch now; it ends there), One Arrow's Through the Heart (it stops in the first champion or boss it hits, and its three splits turn back into it). Okay to use the new four?
7. Until Act 1 is done, Light my way suggests at most one gentle modifier per Flare, so Act 1 plays as tuned. The strongest ones, like Called Down, can still be picked by hand.
8. Each spec's second Flare (the other seven, waves 6b and 6c; 6c waits for the new weapons) will be a separate yes later.
9. Done today, on the classes branch: Burns Twice aims each ember just before it lands, and its last ember throws back whatever still stands about 3 m (a boss only staggers). The Road's Toll, pressed with nothing near, now cuts a kata of twelve along the aim.

## Done in session 13 (classes-10)
- 440c4a90: Burns Twice "aim" and "shove" (Flare.cs TickFlare runs aims and blows in time order; FlareStaged.cs FlareAim, EmberPick, BurnsTwiceBlow, BurnsShove; lamps.json beat "aim", args shove, shoveStun, shoveStagger). 2 tests.
- 955c64d3: the Toll's empty cuts along her aim (`flareAngle` stored at the press). 1 test.
- 10740955 and f4f8d3b8: CLASSES §7 phase-6 plan: Role and "nothing near" columns, the roles paragraph and the two rules, judge 7's fixes.
- 46ab377d: the aim fix. Aiming four embers ahead had cost a press about 15% of its kills (arena crowd `S/s`, `S/v` B). Fixed by counting the ice round falling embers as broken; checked on a synthetic crowd (37.7% against 38.4% killed at x2 health).

## Gotchas
- Isolation: no `$VAR` inside commands that run git, sed or find, and no compound `cd && git`. Write a script to `S/` and `bash` it. Python scripts that take paths as arguments are fine.
- Harness copies: `S/bal13` (classes-9), `S/bal14` (440c4a90), `S/bal15` (46ab377d). Data comes from the cwd's `godot/data`, so data variants run from a copy (`S/v/<V>/godot/data`, `S/v_data.py`).
- Old builds: `python tools/classes/baseline_build.py <dir> <commit>` exports logic, data and balance with `git archive` (no worktree, so the cap is safe), adds the never-press switch (SU_NOPRESS=1) and sets the health. Today's harness never presses with `--flareuse 0`; `--storyhp roost=..,vault=..` sets health.
- Compare story runs on matched seeds (`act1_match.py`); `S/stc.py` compares means over whatever seeds each file has.
- Every arena death figure at 48 runs a tier is noisy (±4 points). Read Flare kills a press (about 1,100 casts) first.
