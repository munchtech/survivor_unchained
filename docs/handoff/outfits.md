# Handoff: the heroine's body and outfits

From the sixth outfits lead (su-lead-high, successor 4), 11 October 2026. Read `docs/team/README.md`, `RESUME.md` and `OWNER_NOTES.md` first, then this page, then `docs/team/outfits.md`. **Never read a whole file**: `heroine_outfits.py` is 4,700 lines. Grep, then `sed -n` the lines you need.

## The owner's words and bar
- "AAA", "never settle", "we are striving for perfection"; edges "perfectly cut and tailored professionally". Sex appeal drives it, "tho not at the cost of looking bad"; full cups with "massive cleavage" are fine; the Reaver stays near-naked with underboob.
- Coverage: "pixel perfect no extra stuff hidden at all. none. not even a few pixels". Holes and see-through are "really distracting and bad". Fit means **tighter, not bigger**.
- Standing option (11 October): "can add leather trim to ranger, and white feathery trim to arcanist parts of their clothing in the bust if it makes it easier to clean them up nicely - just only increase the skin we cover slightly".

## Paused here
Branch `worktree-agent-a5ca10091b08dc429`, HEAD = this commit. **Built art in the worktree is h2 (17b08f2e: animation's elbow corrective merged, plus 5781e8cf), unjudged; never commit it until it passes.** Also uncommitted on purpose: animation's `heroine.res` + `heroine_clips.json`. `o2` = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\o2` (keep it, and `o3`, `o4_plunge` beside it).
- **Judge 5 on h1** (`o2\h1\verdict.md`). PASS: the stomach in the game look, the boning channels, the nipples (equal under matched side lights), the collarbone blister, and the skin paint on all four. FAIL: the Ranger pauldron (top-back crossing, lame 2 crumple, patchy brushing, rivets sliced), the rivets (beads), and the Reaver and Ranger top bindings (pale slivers in v_chest_f and r_chest_f). New: a red hair tuft through the plunge in chain_haul (hair collision: the face/hair lead's), and the Arcanist crotch flap below its binding.
- **h2 (built and shot, not judged):** frames in `o2\h2\` (same names as h1). Coverage in `o2\h2_qsum.txt` matches h1's, with no strip regressions. h2 has:
  - the plunge fold fitted 40 mm (`fold`, `PLUNGE_FOLD`): the crease turn at the bound edge went from 50-95 deg to 15-35. Its lift is 7.3 mm, so check the edge doesn't stand off;
  - rivets as low domes on a flange, in warm dark iron (`iron`), with `scraps=False`;
  - animation's `mend_hole` and `mend_folds`, and elbow_point_l/_r on her body and pieces.

  Lame 3 is a 56-point sliver there (the shadow clip, 5781e8cf), so **h2's pauldron is not for judging**.
- **The pauldron is stuck after two max solvers.** Both ran out of context, so it goes to the main session (README: "two honest attempts"). Root causes (solver 1):
  - The outlines drawn on her skin slide 10-18 mm when each plate is lifted off its own centre, so no tuck drawn on the skin survives.
  - The upper-arm shares (dome 0.41, lames 0.69, 0.95 and 0.98) slide the lames 7 mm out from under the plate above in the idle pose.
  - The brushing's rotated blocks are the game metal shader's 25 mm noise on the dome's polar UVs.

  Plan: build the lames directly as bands in the arm's cylindrical coordinates, under the built rim above, with shares 0.60, 0.80 and 0.98. It is in `o2\paul_t\design.txt`, with its risks: the idle-pose gap, the raised arm, and the dome lifting off her trapezius. Groundwork is in 4315f4a8 (`rivets(spots=)`, the dome's UVs round her arm); it compiles but has never been run. Fast loop: `o2\paul_s\harness.py` (82 s; TINT=1, POSE=30).
- **Plunge** (solver 1): the U edge is already symmetric (under 0.5 mm). The tooth was the fold under each breast running into the U's sides as a crease. Mirror snap made it worse. Scripts are in `o4_plunge\s2\`: `crease.py <dumpdir> <stage> 1.3257`, `meas.py`, `render.py`.
- **Animation's judge 11, item B (ours):**
  - B1: skin through the Arcanist glove's forearm underside at elbow 145, with the wrist turned 80 deg.
  - B2: a pinched dark speck on the Arcanist suit at her upper-outer left breast. Re-cut it from the mended body, and check the Warden and Ranger cups at the same spot.
  - B4: a lavender speck at the Warden pauldron's lower inner edge, in the armpit.

  Verdict: `...\scratchpad\an7\judge11\verdict.md`.

## Next, in order
1. The pauldron (above). Then a full rebuild: copy `o2\h2\run.sh` to h3 and run `b.sh h3 h2`. Then a judge on the `o2\h1` checklist, plus the plunge foot and B1, B2 and B4.
2. The Reaver bandeau's top binding (one binding mesh, and fix the UVs at its top-left corner); the Ranger top binding's pale line.
3. Arcanist: bar tacks and a raised ridge on the boning channels; the crotch flap; vault's 2 frames / 3 px.
4. The Warden's corners and raw cup edge; the gusset shards; the boots (one per solver); the gloves and stockings.

## Setup
- Scripts in `o2`:
  - `b.sh <tag> <base>`: build, motion clips, qsum.
  - `t.sh <outfit> [DUMP]`: one outfit into `o2\tx`, with a relink check first.
  - `h2\run.sh`: the full rebuild with close-ups and the Arcanist game look.

  Close-ups: `tools/scratch/outfits/closeups.sh`, with the lists `o2\h2\cu*.txt`. `lookdev.gd` takes LIGHTS=mirror|side. Game-look frames: `o3\plain.sh`.
- The build blend is `181eef02...\scratchpad\outfits\hs\heroine_built.blend`. Its images resolve (checked with `o2\blend_relink.py --dry`, taken from the face branch's 49f655f7).

## Gotchas
- The context hook reads a lead's budget as 120k; the brief's 300k holds.
- Max solvers on the pauldron spent their 200k reading. Give the next one the design file and the harness, and nothing to re-derive.
- `heroine_outfits.py` mixes line endings since the merge; Python edits should match either.
- `DUMP=<piece,...>` writes npz files to `$TEMP`: set `TEMP` for that one command.

## Collaborators
Animation a58694457cba54ade (sent the elbow corrective), face a8b147f78b1db794b, rendering a71fc38b0095fd45a (paused; the main session carries the LOD note). Reports go to the main session.
