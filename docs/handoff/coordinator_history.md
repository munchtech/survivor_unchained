# Coordinator history (each session's state and lessons; not read at startup)

The lessons that still apply are distilled in coordinator.md "Lessons that still apply". Read here only when one points back.

## State at handoff
From the coordinator of 10 October (session 181eef02). Wave 1 restarted, ran about three hours, hit the weekly limit, resumed on usage credit, then was wound down by the owner. Integration is unchanged apart from docs (roster, OWNER_NOTES 10 October: the neck note, nipple show-through, boots). No area passed its judge except rendering's FSR 2 native, which waits to merge alongside face. Every lead stopped with a "Paused here; next:" block on its own branch; RESUME "10 October" has the four branches, the restart order and the scratch backup. Token use, measured with every judge, solver and runner (`tools/scratch/coordinator/wave_cost.py <session>`, usage_week.py's list prices): 7 October (session 0b33992d, 1 h 40 min) about $75, $45 an hour; 10 October (3 h 40 min) about $150, $41 an hour. The leads got about four times cheaper per hour (four max leads $40 in 45 min; five high leads $44 in 3 h 40 min), but judges and solvers took 70% of the spend ($104 over 15 spawns, each filling 180-366k with images and their own measuring). So the saving moved, not landed. Fix adopted in README "Working lean": lean judges.

**Coordinator 91211d34 (10 October, evening):** restarted wave 1 in the old worktrees; the owner's disk cleanup (CLAUDE.md, wt_remove.ps1); the context-budget hook; lean agent types. Wound down at 245k with rendering handed off and ready to merge with face, and the other three asked to pause (RESUME "10 October, late"). If their PAUSED lines didn't arrive, check each branch's handoff block and `ctx.py` before restarting.

**Coordinator ba85aba8 (12 October):** merged Act 1 boss health, classes phase 2, her hair swing (16/18), relaxed turns (blender 3, godot 4, VRAM guard). Ran classes, face, hero, outfits and animation, then wound all five down on the owner's word (RESUME "12 October, evening"). Lessons: leads hit their ~250-300k budget in 1-4 hours, so plan a successor per lead per long stretch; a lead's report can say "merge-ready" while a merged piece later fails a check (Butcher's Hour), so ask for the before-the-owner-plays checks before merging live gameplay; another session may commit to integration in the main checkout (free_ram tools): fetch before every merge. This session's scratchpad holds leads' scratch: keep it.

**Coordinator 1515c1de (12 October, night):** ran classes, face, outfits and animation (hero held: Blender turns). Merged the get_up braid and ponytail, the Butcher's Hour fix and the Flare press-stagger fix with Act 1 retuned (RESUME "12 October, night"). Lessons: every su-lead-high lead filled 250-280k in 1.5-3.5 h, so plan a successor per lead every couple of hours and keep onboarding small; most of their spend was their own measuring and pictures, so brief successors to hand build-and-measure loops to runners and take the build to a judge before chasing every number; give a solver one item and a named route, and make it build before measuring (several solvers ran out measuring); judges rule on what the eye sees (the neck and reach_coals rulings). Run a narrow judge yourself (foreground, Context budget: 100k) when a lead hands off just before one. A lead often wakes once more after its "HANDOFF READY" when its background batch ends: check the branch head before spawning from it. Scratch to keep: this session's scratchpad (classes, face, outfits, anim).

**Coordinator 33ad5b17 (12 October, night):** restarted animation, face, classes, outfits; built the close-up camera (merged). Merged animation dd541c17, camera d31fefa6, classes 6d9a123c. Owner rules added: 125% budget grace to finish a near-done step (hook updated); face and outfits first; hero held. Lessons: a lead's background solvers report to the coordinator, so relaying is most of the coordinator's traffic (keep relays condensed); diagnose before fixing (the glove notch was the leotard edge, the clasp gap was her spine bend, not her breasts): solvers that measured first saved builds; copy sheets out of `.shots` before removing a worktree. RESUME "12 October, late night" has the running state.

**Coordinator 1be2d2a9 (13-14 October, the owner's one-session trial: three leads at 399k budgets, coordinator 300k; rules not changed).**
- **Merged:** classes-11 (the five wave-6a Flares) and outfits fin5 (all four outfits, plus the owner's "legs stuck together" fix).
- **Handed off, not merged:**
  - animation, the staff in her fist (it waits on the outfits glove fix);
  - Flare VFX (judge 4 NOT READY).
- **Measured (cmp3.py in the scratchpad):**
  - this session, 8.1 h, $123 ($15/h);
  - 33ad5b17, 4 leads, 6.5 h, $150 ($23/h);
  - 59a43b82, 5-6 leads, 14 h, $355 ($25/h).
- **Per lead-slot hour all three cost about $5:** fewer leads is a throughput dial, not a saving.
- **The bigger budget was barely used:** only 2 of 6 leads passed 300k (366k, 320k), and lead cost per slot-hour rose about 10-15%. Keep 300k.
- **Lessons:**
  - Never merge on a picture the judge hasn't ruled on (the staff merge was pulled when the owner saw the fist beside the shaft).
  - Judges check "visibly inside the closed hand" first.
  - Rebuild a lead's art on the latest integration before merging binaries (the outfits conflicted with face ship's heroine.glb).

**Coordinator 34daaf5d (14 October; the owner allowed 385k this once).** Merged the staff, the Reaver loincloth, and the rest lips B3-15. New team tools and rules: the freshness gate in turn.py (the caller's checkout or --root), half-size working pictures (tools/half.py), solvers with a numeric pass on su-lead-high, checks scoped to what changed. RESUME trimmed (RESUME_ARCHIVE.md). The owner's direction: beautification only (outfits, animation, face). Lessons: stale Godot imports and stale branches produced false faults twice (the gate fixes it); a body change ripples into every outfit's tessellation, so legal is needed on all four even for hands-only; ask a lead for proportions numbers before taste calls (the audit found the short forearm and the small head). A PC restart killed running solvers: their work is in WIP commits.

**Coordinator d7e64ca2 (14 October, night; outfits, animation, face only).** Nothing merged except docs and tools (the roster, lastmsg.py now finds any session's transcript and reads SendMessage text). The work converged on ONE body build after the owner's glove pick (RESUME "14 October, night").
- **Lessons:**
  - A fit that passes on one hand fails when the hand changes (the staff, 6-8 mm). Refit every grip after any body build, before merging.
  - Two tools disagreeing means a ground-truth measurement in Godot (grip_truth.gd), not a third model.
  - Decide body-build asks up front and merge them, so the build runs once (hand pivots, thumb, back-of-hand reshape, left hand by its own skin).
  - Pushback saved a build: anatomy said 24-28 mm where a crude model said 15.
  - Helpers launched by a lead report to the coordinator and often can't address the lead: relay every one.

**Coordinator 1cc516bc (14 October, night; outfits, animation, face).** The owner picked B1 "with style". Ran outfits 24 then 25, animation 29 then 30, face 25. Nothing merged yet: the one body build is rig-final (F0, outfits scratch 1cc516bc `prop\F0`), and animation 30 refits on it. Open: the chest_smooth round 2, the glove fixes (the elbow-fold poke-through, G1 rebuild, G2 one round or dropped), then the judged glove sheet to the owner. RESUME "14 October, night: coordinator 1cc516bc" has the state.
- **Lessons:**
  - Gate every body build on its correctives: F1's builds silently had none (a stale game-skeleton dump, "no game skeleton matches"). Grep the GLB for `elbow_point` against integration's.
  - Nearest-surface depth undersells a limb passing through the body (kd said 18 mm; the true gap along the thigh's up direction was 48-84 mm). Measure the true gap before specifying a corrective.
  - Blender lookdev can't judge the head/neck rim: the game's skin shader eases the head into the graft. Judge that area in Godot shots only.
  - Coarse sculpt triangulation (7-8 mm edges) is the root of the knuckle failure and the chest facets: one "close-up skin detail" item after F1.
  - A rig-final build lets animation start before skin-only fixes finish (outfits' pushback; gate: bones, weights and key deltas identical).

**Coordinator 1847d1a6 (14 October, night; outfits, animation, face).** Ran outfits 26 then 27, animation 31, 32 and 33, and face 26. Nothing was merged except docs. Outfits' final body and outfits are committed (dfe686ed), with the merge request HELD to land with animation's repack. The glove sheet (B1 vs G3) is with the owner. The owner set the finish line (judge critically at the game's max zoom) and picked the crossbow pistol grip. RESUME "14 October, night: coordinator 1847d1a6" has the state.
- **Lessons:**
  - Helpers can't SendMessage "parent". Leads must give each helper their agent id; otherwise the reports land on the coordinator.
  - A lead's leftover runner can overwrite newer art when its job finishes (B1c over B1j). When the art moves on, TaskStop the predecessor's runners; find them by grepping `subagents/*.jsonl` for the job.
  - A worker's `taskkill /IM python.exe` killed every lead's Python jobs. That's now a README rule, and it goes in every worker brief.
  - Leads filled about 240k in 1-1.5 hours. Plan a successor per lead per stretch, and expect the coordinator itself to reach 250k in one long evening of relays.
  - A body build that keeps the skeleton identical (F0 to B1c to B1j) let animation and face work in parallel; colour-only follow-ups were cheap to confirm by accessor diff.
