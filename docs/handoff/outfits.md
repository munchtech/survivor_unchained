# Handoff: the heroine's body and outfits

From the seventh outfits lead (su-lead-high, successor 5), 11 October 2026. Read `docs/team/README.md`, `RESUME.md` and `OWNER_NOTES.md` first, then this page, then `docs/team/outfits.md`. **Never read a whole file**: `heroine_outfits.py` is 5,000 lines. Grep, then `sed -n` the lines you need.

## The owner's words and bar
- "AAA", "never settle", "we are striving for perfection"; edges "perfectly cut and tailored professionally". Sex appeal drives it, "tho not at the cost of looking bad"; full cups with "massive cleavage" are fine; the Reaver stays near-naked with underboob.
- Coverage: "pixel perfect no extra stuff hidden at all. none. not even a few pixels". Holes and see-through are "really distracting and bad". Fit means **tighter, not bigger**.
- Standing option (11 October): "can add leather trim to ranger, and white feathery trim to arcanist parts of their clothing in the bust if it makes it easier to clean them up nicely - just only increase the skin we cover slightly".

## Paused here
Branch `worktree-agent-a5ca10091b08dc429`. **Built art in the worktree is h3 (built from 1789e863), judged FAIL; it is uncommitted on purpose: never commit built art until a judge passes it.** Also uncommitted on purpose: animation's `heroine.res` + `heroine_clips.json`. `o2` = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\o2` (keep it, and `o3`, `o4_plunge` beside it).
- **Judge 6 on h3** (`o2\h3\verdict.md`, read it first). PASS: the pauldron crumple, its rivet clearances and front read, the Reaver binding, the rivet shape, B4 (Warden armpit), and every judge 5 pass. FAIL, with fixes committed since but **not yet built** (commits 13428a51 to 2526b621):
  - Ranger pale neckline line: the lookdev rim light on a satin binding (NORIM=1 and SPECULAR=0 both clear it; roughness 0.8 does, 0.65 doesn't). Rolled bindings now draw matte through a vertex flag: COLOR.a 0 = `_bind`, 0.5 = `ranger.pauldron<digit>` (brushed along its UV u), 1 = neither; written in the detail writer, read in `heroine_outfit.gdshader`.
  - Dome brushing blocks: the metal brushing ran on object y, flat across the dome's top. Pauldron plates now brush along their ring UVs.
  - Rivets read as black dots: `_rivets` AO is now eased twice instead of up to 200 times (keeps the contact ring); iron level is 88, up from 72.
  - B1, the skin speck: it is at the inside of her elbow (sleeve), not under the glove. The Arcanist full tuck (10 mm) now runs from ELBOW_S-0.05 to WRIST_S-0.01.
  - B2, the breast notch: `mend_folds(body.data, body)` now runs before the pieces are cut (line ~310) as well as at export.
- **Running when I handed off (their results come to me or to the main session; each also writes a report file):**
  - **The pauldron's idle-pose items are stuck after two more solvers** (round 2: the loop and numbers; round 3, d938b1b3, WIP with defaults unchanged: `o2\paul_veport2.txt`). Lame 1 turns 14 deg against the dome at idle, so its back top rises into the dome. Changing the blend trades this for lame 1 meeting her skin, so the fix is a trim. `pl_lame(cut=...)`, env PL_CUT, is off by default. At PL_CUT=0.013,0.044,0.022 the skin gap and hidden points pass, but the clearance (-0.9 mm) and the inset (1.6 mm) fail, and +30 got worse. The medial flare is not started: it needs a hook in piece() after clear_of_skin, and a check that it doesn't cross the dome UV's pole. Its loop is `bash o2\paul_vun.sh <dir>` (98 s, the game's Idle as POSE g0; MEASURE=m_s3.py). measure2's "overlap min" has a sign bug.
    **The coordinator's two-attempts rule now applies: don't send another solver.** Propose a simpler pauldron that reads as well or better, either fewer lames or a leather pauldron with a few steel plates riveted on, as a judged side-by-side for the owner, against h3's pauldron (which passed judge 6 except for these two items and the straps).
  - Plunge solver 3: the coordinator's option (a), "taut-string" rim pinning about 2 mm off her skin. Report: `o2\plunge_w\report.txt`. The foot today is a flat shelf 13-16 mm off her sternum (the 40 mm fold fit plus a 7.4 mm lift). The teeth are the sheet poking through a binding with 0.3 mm of clearance. **Coordinator's ruling: if (a) doesn't land cleanly at 1:1, no fourth attempt: build (b), the white feathery trim along the plunge, as a judged side-by-side for the owner, covering only slightly more skin.**
- Pauldron leather straps down the lames' back ends (judge 6 wants them: "a loose staircase with nothing holding them"): not started. Solver 2's plan: segments rigid with each lame, the weight hand-over hidden under the lame above, end rivets reused; finish() reweights, so set weights after it; don't name it `ranger.pauldron<digit>`.

## Next, in order
1. Collect both solvers' results. Then the full rebuild h4: copy `o2\h3\run.sh` to h4 (replace h3 with h4 and `b.sh h3 h2` with `b.sh h4 h3`) and run it in the background (about 40 min; it stops at BUILDFAIL on a traceback). Then a judge on the `o2\h3\verdict.md` checklist. Judge 6 asked for numbers too (lame 1 overlap at idle and at clip extremes, the foot's stand-off, the pose of arcanist_arm_side cell 6).
2. The pauldron straps. Then the Arcanist crotch flap, the channels' bar tacks and ridge, vault's 2 frames / 3 px.
3. The Warden's corners and raw cup edge; the gusset shards; the boots; the gloves and stockings.

## Setup
- `o2\b.sh <tag> <base>` (build, motion clips, qsum), `o2\t.sh <outfit> [DUMP]` (one outfit into o2\tx), `o2\h3\run.sh` (full: build, close-ups `cu*.txt`, Arcanist game look into `h3\plain`, arm sheets like animation's judge 11). Debugging a material: closeups with EXTRA="OUTFITVIEW=1" (edge-distance view), NORIM=1, NOSKYREFL=1.
- The build blend is `181eef02...\scratchpad\outfits\hs\heroine_built.blend`. Its images resolve.
- From face (0cface69): `heroine_seam.py`, `heroine_throat.py` and `heroine_face/jaw_zone.png` are on this branch (the nape weight weld). Animation's 388e6dbc (hands kept out of mend_folds) is in.

## Gotchas
- Killing a run's bash leaves its children and their turns: find them by command line (worktree path), stop them, then `turn.py give` the names left in `turn.py show`.
- `heroine_outfits.py` mixes line endings; Python edits should match either.
- A solver's completion notice goes to the main session; brief it to SendMessage the lead (this lead's address was af07affeb22637bb5) and to write a report file.

## Collaborators
Animation a4e62fc358dc5214a, face a564d5c3b5d4dac62. Reports go to the main session.
