You are coordinator #12 for Survivor Unchained, starting fresh after the reset (14 Nov 2026). Opus, high effort.

Read first, in order: `CLAUDE.md`, `docs/team/README.md`, the top block of `docs/team/RESUME.md` ("WIND-DOWN 13 Nov ... COLD START HERE"), then each lane's state file named there. Run `/wave-start` before spawning anything (disk, the 8-worktree cap, brief lines).

## Part 1: close what we left open (today, before anything new)

Each lead restarts from its state file's top block, finishes, gets judged where it shows on screen, merges on a green suite, pushes, and its worktree is removed in the same turn.

1. **Skin lighting**: `skin-light@286f9e7e2`, round 4 WIP, unjudged. Finish round 4 (Look necks, NPC lilac lit side), then one judge at 1:1, day and night, whole frame, on faults 1 (apricot-orange body, pink shade), 2 (sky-only cast shadows: grey/violet neck, close_night neck hole) and NPC night. A pass merges; no carve-outs.
2. **NPC held props**: `claude/priceless-borg-d08e89@2e18dd4f3`. Base-body shots, judge, suite, merge.
3. **NPC rim / cream line**: the lead that brings the line back from integration (the under-breast cut is already in at `fcf764a4e`). Find out whether the unclaimed `rim-back` worktree is that lead's start; if not, remove it with `wt_remove.ps1`.
4. **Routed items with no lead yet** (the bd-ui, bd-ui2 and bd-sockets bullets in RESUME): her held weapon per stance; the untraced orange double ring + disc with a red bar in every fight; damage numbers on the swap glint; the bush over her at the play camera; the black bar at her feet in creation; `--unequip` with no battle leaves the world shield; the axe glyph at 26 px; dye shader (gilt mustard, silvered plaster, bronze too weak, metal dye flattens Warden greaves); gear data gaps (padded_jerkin/leather_cap with no look, plate tops share the skirt, "Forged Cuirass" draws as a bikini, Etched vs Plain, Arcanist's Hat material, unused cloak entry); foliage hard triangles under depth of field; outline ink specks beside her legs; Bladestorm has no wick; ARPG.md 3.3 line 165 still names Dawn's Judgment; Concussion/Bulwark tests; Red Hand steal-by-damage (boss lane call); story's road scene, Brannoc quench lines and the 12 great uniques' lore. Group these into at most 3-4 lanes by area, not one per item.
5. **Paired bake-off**: Opus arms done (`bo-*-a`); the Fable arms resume after 15 Nov 05:00 UTC from `survivorsunchained_inputs\scratch_usage_cmp\bakeoff\STATE.md`. Several arms cover item 4's routed items (offhand weapons, axe glyph, storm wick, Red Hand steal, metal dye, fight ring, foliage DOF): use their results there and don't build anything twice.
6. **Marionette R&D**: resumes from `Marionette\docs\rnd\HANDOFF_RND.md` (newest bullet). Its own coordinator, not yours to run; just keep the shared pieces in sync.
7. Housekeeping: old pushed branches nobody merged (armor-7, cine-8, classes-8, classes-10, ui-25, hair6-39, body-p1b): give each a disposition in `CLOSEOUT.md` (merge, keep or scrap). Ask the owner about the unclaimed stray files in the main checkout (attach.py, pb.txt, t2.py, the two heroine PNGs, tests/TeleRankTests.cs, tools/comfy/in/).

## Part 2: refocus on the week

Once Part 1's lanes are running (not finished), bring the owner a one-page proposal for the week of 14-20 Nov. Lead with your verdict and push back where you disagree (memory: owner-working-style). Ground it in `docs/design/BUILD_DIRECTION.md`, `BUILD_UNLOCKS.md`, `DEMO_PLAN.md` (the next tag is earned when the owner plays and wants another night) and the latest `OWNER_NOTES.md`. Answer:
- What playable build the owner plays at the end of the week, and what has to be true for it to "hook".
- The 3-4 lanes that get there (team cap), each with acceptance a judge or a number can check, a cost in tokens, and the order.
- What we stop or park this week, and why.
Ask the owner to pick or adjust, then spawn. Keep the owner's quotes word for word with dates in RESUME.
