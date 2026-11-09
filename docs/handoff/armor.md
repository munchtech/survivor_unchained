# Handoff: armor and weapons (smart slot parts)

Read README ("Working lean", Safety), RESUME's top, then this page. Worktree (lead 6) `.claude/worktrees/armor-5`; earlier `.claude/worktrees/armor-1`, branch `armor-1` (godot/assets is a junction to its own public/assets: never stash, reset --hard or checkout .). Marionette work: `C:\Users\munch\Desktop\Marionette`, branch `armor-1` (main's uncommitted edits there are not ours: never commit them).

## P2 GEAR LEAD 3 -> successor (9 Nov, coordinator wind-down): HANDOFF READY gear-p2 (see the commit that adds this block; code at c1416af53). Reach bug fixed; pauldrons: tuck-to-gone measured dead, stand-off law built and parked (passes the number at a 16-23 mm gap, fails the look); bust_up slider body built and fitted (0 flags). Next: the pauldron sweep below, then items 4-8
**Brief:** `tools/scratch/coordinator/briefs/P2_gear_lead2.md` + lead 2's block below (route, items, rules). Main approved the list at a 1.1M line for the area (this lead spent ~0.51M of it: helpers ~420k, lead ~90k; ~0.59M left). Waiting on A1's PACK SHA: when main says motion-a1 packed the P4 clips, re-run `gear_wear` on them (`--clips <P4 pack dir>`). My scratch SCR3 = `C:\Users\munch\AppData\Local\Temp\claude\2a15606791177975\487f4f5f-ecfa-41b7-8748-d3a96063626d\scratchpad\gear` (pl3 = gone trial, pl4 = stand-off loop + round.sh/vis.py/bld.py, wk3 = boots, r4 = bust_up chain/fit logs). Lead 1/2's SCR as below. Back both up to `survivorsunchained_inputs\scratch_gear_p2\` at the end.

**Done (lead 3):**
- Integration c0d134c85 merged (eeb4ac59e, junction dance). The worktree's stale Godot import (heroine.glb) was re-imported; 4 outfit_tex .import files it rewrote with new uids/mipmaps were restored to HEAD; the rest were CRLF-only. 55 untracked .uid files remain (regenerable; move aside before a merge).
- **Reach bug (291accec4):** `gear_wear` re-casts through samples on enclosing slots against the piece's whole face set (`full_cast`, chunked). Boots now: arcanist 134.8 -> 89.7, reaver 595.2 -> 541.4, ranger/warden 0, warden.greaves 146.2, cuirass control 1656.5 unchanged; 111 s. **reaver.boots' remaining 541 is a REAL through at the calf** (calf_r ~11 mm, Jog_Fwd / run_arcanist / run_reaver), a fit item, not the bug.
- **Pauldron lever (a) tuck-to-gone: DEAD, measured** (1a1ca0a5d, `tools/armor/gear_seal.py` hide/seal, gear_tuck reads `armor_hidden/`): of 540 skin points under the rigid parts only 1 is hidden from the camera set (elev -15..90 deg, all azimuths) over 1163 frames: the lames are open toward the neck and below, so removed skin shows as a hole. Code kept (the SEAL check is reusable); nothing reads hidden sets unless `armor_hidden/` exists.
- **Pauldron lever (b) stand-off law (c1416af53), PARKED:** `tools/armor/gear_standoff.py measure` gives each plate vertex a target clearance from the measured through over the clips; `gear_fit build` clears rigid parts to targets (`gear_field.rigid_fit_clear floor=`); targets in `godot/art/gear/standoff/<id>.json`; law in `rigid_roles.json slots.pauldrons.standoff_trial` (rename to `standoff` to switch on; nothing reads it now). Result after 3 rounds: plain 6845 -> 0 mm2, warden 7005 -> 90 (Jog_Fwd 0), BUT plates moved 16-32 mm out (lame 1 rest gap min 16 / median 23 mm; the cop floats 13.7 mm off the shoulder top) = a look fail. **Biggest lever found:** `tuck_bound`'s STEP (0.15 per skin edge) caps the tuck under the plates at 1.5-3 mm instead of 10; tuck alone at STEP 1.0 gives 2863/2745, at 0.4 4558/4404. Live `body_p1` and `weight` pauldrons are UNCHANGED. The experiment copy `godot/art/gear/out/body_p1_seal` (git-ignored, ~470 MB) is kept for the sweep; Recycle-Bin it after.
- **Third slider body = bust_up** (bust_size 0.5 on her_b; picked over hips because bust stretches most: bust_size+1 stress failed 23 meshes vs hips 3): built, published `godot/art/people/body_p1_var/bust_up/`, clips baked (BAKE gates True 47.4), gear built `godot/art/gear/out/bust_up` (44 units, 0 failing, 0 flagged, 465 s). Not yet imported in Godot; `--json` wrote nothing (check that flag belongs to `check`, not `build`).

**NEXT, in order:**
1. **Pauldron sweep (a su-worker, tight; my planned brief):** score "where it shows": through > 2 mm on town/idle/look clips (close cameras ~1 mm/px) and > 6 mm on combat/run clips (play camera 13 mm/px at 23 m: add `--out-mm` to gear_wear). Run on the seal copy with an alternate roles file (an env/CLI override, so the repo `rigid_roles.json` stays untouched while other builds run), targets frozen (score with gear_wear, not standoff measure): configs = live baseline; STEP 1.0 tuck only; cap_mm 6/8/10/12 at STEP 1.0 with a `seat_cap_mm` ~3 on the topmost component (the cop stays seated); cap 10 at STEP 0.4. Table: total per pauldron vs lame 1 rest gap (min/median) and cop min clearance. Pick the smallest gap with both scores under 1k per pauldron; switch the law on, rebuild live body_p1 + weight + bust_up pauldrons, `gear_tuck control`. If nothing under ~10 mm gap passes, ship the best and let the one judge decide at 1:1 (the visible gap and the STEP 1.0 dent under the lame edge are its questions); body-side note for P1/A1: the share law + arm correctives push 14-19 mm under the deltoid, and the trap aim helper lifts into the cop.
2. Slider proof in game: import bust_up's gear, then the proof numbers (gear_field rows ok/flagged for her_b, weight, bust_up); strips wait for the 3-set shoot (rule 4).
3-8. As lead 2's list: native cuisses + hair-hiding helm (`gear_fit bind --native`, PIECE_SCHEMA; `survivorsunchained_inputs\scratch_armor10\b_design_spec.md` 3b, 4); the mixed-look rulings; the Marionette gear tool; the gloves fist check; the 3-set shoot + ONE su-lead-max judge (own half-size look first); the `--body p1` default flip with main's word, suite, MR READY (merge note: the 47a71157c bind blob).

## P2 GEAR LEAD 2 -> successor (9 Nov, coordinator wind-down): HANDOFF READY gear-p2 (see the commit that adds this block; code at cda432cf0). Bindings out of git with a stale check; integration merged; pauldron twist measured (no gain: the cause is clearance and B's laws); next: the pauldron fit lever, the reach bug's real cause, then lead 1's items 3-8
**Brief:** `tools/scratch/coordinator/briefs/P2_gear_lead2.md` (the coordinator's calls: second body waits for P3's source-sculpt route; bindings are build outputs; gloves fist check). Main approved the list at a 1.3M line. Lead 1's block below still holds for the route, the game wiring and items 3-8. Scratch SCR = `...\scratchpad\gear` (lead 1's s1-s7 briefs, `pl\` pauldron diag, `wk\` worker before/after, `uid_aside\` = 55 untracked Godot .uid files moved aside before the merge: regenerable, delete at the end).

**Done this session (lead 2, ~80k + helpers ~165k):**
- **Bindings are build outputs** (bd3fda14d): `godot/art/gear/bind/` git-ignored and out of the index. `gear_fit.py` stamps `BIND_VERSION` (=1); `python tools/armor/gear_fit.py stale` exits 1 on a missing/old-version/src-changed/body-changed binding and warns on orphans; `build` rebinds stale units in-process first (`--no-bind` skips), so `build` is the one command (28800615c, 8c8baf350; test_gear_fit 9 pass). The current bindings on disk are fresh (44/44, stale = 0). MERGE NOTE: the stale 52 MB bind blob stays in 47a71157c's history (no rewrite on a shared branch).
- **Integration merged** (e59ba0ad6, clean, junction dance done). The branch is at integration 1174d51a8 + ours.
- **Reach bug, half (cda432cf0):** `wearcheck.signed_gap` now skips the backward hits when an unclipped forward inner hit lies past the reach (test in test_gear_wear.py). It moved NO number (boots: arcanist 134.8 mm2, reaver 595.2, ranger/warden 0, warden.greaves 146.2; cuirass control 1656.5). The real cause per the worker: `rest_footprint` (~gear_wear.py l.487) and `_measure` (~l.654) hand signed_gap only the K0 nearest triangles, so a toe-box face 30 mm ahead is never a candidate. NEXT (worker): widen the candidate set for enclosing slots (or cast against the piece's whole inner shell when the K0 set has no forward hit), then re-measure the boots. Results: SCR\wk\before, after.
- **Pauldron lames on the twist chain: measured, NO change made** (solver, medium, 113k). The lames are already separate rigid parts and `one_bone` already puts each on its strongest bone by height (cop and lame 1 ride upperarm_share, lame 2 twist_02). plate_pauldrons_plain over 32 clips (no Jog_Fwd): 6845 mm2 (lame 1 3113, lame 2 1591, cop 2143, worst 35.4 mm); every twist variant measured worse (10.8-12.3k); even a per-frame ORACLE rigid fit leaves 6491. plate_pauldrons_warden 7005 (worst 51 mm, trap under the cop in idle_arcanist_town). Jog_Fwd separate: 1602 / 1552. Worst clip daggers_heavy. **Cause:** lame 1's rest clearance is ~4 mm (p5 -1.4..0.9 mm) while the deltoid band deforms 14-19 mm non-rigidly (the P1 share law: share follows half the lift; and the arm correctives, ~1.0k of lame 1 and ~1.3k of the cop come from blend shapes). The cop's rest is the trap aim helper lifting into it. Godot/.shots/gear_p2/wear/gear_wear.json is OLDER than the current build (it shows 37 at rest; the build shows 0): re-run before quoting it.
  - **My call for the next step (not started):** the gear-side lever is the fit, not the bones: (a) under rigid plates, skin the plate's footprint fully covers gets tuck "gone" like the enclosure rule (the lames hide it from every game camera; check the lame's lower edge stays sealed at the arm-raise frames), and/or (b) build lame 1 with more rest clearance per body (the rigid made-to-measure LP gets a target clearance from the measured deformation band, e.g. 4 -> 12 mm at the lame's lower edge, with the visible gap judged at 1:1). Try (a) first: it is general, data-only in gear_tuck, and the judge sees no gap. Relay to A1/P1 only as a note: the share law and arm correctives push 14-19 mm under the deltoid. Diag tools: SCR\pl\diag.py (ORACLE/BONE/NOSHAPES switches), exp.py.
- Target stays under 1k mm2 per pauldron "where it shows": with (a), score only skin outside the tucked-gone set.

**NEXT, in order:** (1) pauldron lever (a) above, a medium solver, gear_wear pauldrons before/after; (2) the reach bug's candidate set (worker); (3)-(8) as lead 1's list below: third slider body (hips or bust_up, pick by stretch) + in-game slider proof; plate cuisses + hair-hiding helm built natively on B (`gear_fit bind --native`, PIECE_SCHEMA; design `survivorsunchained_inputs\scratch_armor10\b_design_spec.md` sections 3b and 4); the mixed-look rulings (one line each); the Marionette gear tool; the 3-set shoot (reaver, ranger, plate: every slot, play camera + dialogue close-up, day + night, in motion) and ONE su-lead-max judge at max, whole-frame question first; the gloves fist close-up check (open-fingered gloves keep their fingers; a test on the index); `--body p1` default flip (People.cs ~l.370), suite (`dotnet test` in godot/tests, last 1697/0/10 on integration), MR READY with merge notes (the 47a71157c blob). Estimate left ~1.1M.

## P2 GEAR LEAD 1 -> successor (9 Nov): HANDOFF READY. B wears her gear in game (--body p1); the fit, tuck, motion check and slider follow are built. Next: pauldron lames, the plate set's cuisses and helm, the Marionette tool, the judge, the flip
**Brief:** `tools/scratch/coordinator/briefs/P2_chain.md` item 1, plus the coordinator's spawn prompt. Main approved:
- the route, the 10 items, ~1.3-1.8M;
- built pieces over 100 MB stay OUT of git: bindings go in git, built meshes are git-ignored and made by `gear_fit build`;
- test with `--body p1` until item 10.

Worktree `.claude/worktrees/gear-p2` (a junction to its OWN public/assets). Never stash, reset --hard, checkout . or merge without the rmdir/mklink dance in lead_brief.md. Integration has not been merged since 11fa1fb75. Scratch (briefs s1-s7, solver tools, numbers): `C:\Users\munch\AppData\Local\Temp\claude\52c6646a0254d2b9\832e8ec3-f768-4cf4-ae4e-45ed6fe4230b\scratchpad\gear` (call it SCR). At the end, back its texts up to survivorsunchained_inputs\scratch_gear_p2.

**The route (built):** one binding per gear unit to the base topology, made once from A's files.
- Each binding holds: the triangle in [topology T ; HeroineHead T], barycentrics, the offset in the local frame, and the rigid component.
- `tools/armor/gear_fit.py bind` makes them (~3 min; A is posed into B's rest by her_a's maps).
- `gear_fit.py build --body <published dir>` evaluates them on any body: ~45 s on her_b, 5-7 min on other bodies.
- Output goes to `godot/art/gear/out/<body>/` (git-ignored; 464 MB on body_p1): 44 units (30 calling rows, 10 armor, 4 `<calling>.lod` play units), `gear_index.json` (rows plus `fit` ok/flagged and `fit_fail`), `armor_tuck/`, `armor_cover/` and sockets.
- A's node and mesh names are kept, so HerWear, materials and dye work unchanged.
- Bindings: `godot/art/gear/bind/*.npz` (52 MB). The first set went into 47a71157c and is stale (pre-fix). The CURRENT ones are uncommitted on purpose: commit them ONCE at MR, or squash, since 47a71157c's 52 MB is dead weight.

**Key fix (lead, 683fb65ca):** the stage npz T indexes the glb's UV-split vertices, so the topology triangles are `src[T]`.

**Game (s2, 98358b0e0..ad76a010c):**
- Under --body p1, `ArmorIndex.GearDir` = `gear/out/<folder of P1Body.Dir>`; variant folders go by name with --p1-dir. A missing folder gives one log line and falls back to A's indexes.
- B's pieces carry meta p1_gear: never hidden, swapped or rebound.
- One tuck map covers both tiers (`tuck_offset` instance uniform in heroine_skin.gdshader). Full sets attach `<calling>.lod`.
- GearIndexTests (5). dotnet is 1593/0/10 by arithmetic only: RE-RUN the full suite before the MR.
- A's path is proven unchanged (smoke_r1 a_old/a_new).
- Smoke sheet (half size, town: all 4 callings dressed on B, mixed, helm, swap, dye): `godot/.shots/gear_p2/smoke/sheet_half.jpg`.
- Live swap: worst frame 448 ms, a hitch (A not measured).

**Tuck and cover (gear_tuck.py, s2 + s7 3bf09ec2a):** A's general rule runs natively on B, and general rules replace A's per-piece hacks:
- through-at-rest skin gets a full tuck;
- skin within 6 mm of a rigid plate gets a full tuck, easing out to 10 mm;
- enclosure "gone" for boots, gloves, greaves, bracers and head (hemisphere rays, 3% escape, 15 mm from open skin);
- rows whose A tuck was empty tuck nothing.

Run it with `python tools/armor/gear_tuck.py write|control`. **OPEN RISK, gloves:** ranger has ~2000 points not drawn (arcanist also has finger points not drawn), and the fist clips push the fingers out. Check a fist close-up: if a glove is open-fingered, its fingers vanish.

**Rigid roles (data in `tools/armor/rigid_roles.json`, read by `rigid_blend`):** top rides one spine bone, pauldrons one upper-arm bone, bracers the forearm mean, greaves the calf mean. Rigid components are sized per body (per-axis scale 0.85-1.25, then an LP clear).

**Motion check (`tools/armor/gear_wear.py`, s5 07fe5292f/bca702b9e):**
- It runs B's lbs poser plus the laws over the clip dumps (`tools/body/out/clips`, 33 bridge clips; `--clips` takes the P4 pack later), with skin, control, mixed and show tests.
- Use `--jobs 3` at most (1.8 GB each); a full run takes ~16 min. Results after s7 are in SCR\..\s7\wear1 and wear2.
- Boots, gloves and bracers are about 0.
- plate_cuirass_plain went from 53k to 1.7k mm2 (what's left: the clavicle shrug and Jog_Fwd).
- **Plate pauldrons: 7.2k mm2 each at 35 mm.** Upper-arm skin comes through under the lower lames as the arm lifts, because a rigid lame can't follow the twist. Next: put each lame on the twist chain by height.
- warden.pauldrons: 5.4k (bendy, untouched).
- mar_her_* are unshipped A-era pieces, flagged, low priority.
- KNOWN gear_wear bug: a forward hit past the 25 mm reach takes the face behind, so boot toes read as through. A worker can fix it.
- **Jog_Fwd is a broken clip** (spine_03 against spine_04 bent 35-50 deg every frame): tell A1.
- Re-measure on the P4 clips once motion-a1 packs them. Per A1's note, B has its own held frames, a girdle law, and HerShrug off.

**Every slot shows:** all 43 looks pass; the lowest is reaver.bottom at 33% under ranger.top. Rulings due: plate_gstring_plain is dropped whenever a reaver or ranger belt or skirt goes on, and reaver.skirt drops under another source's belt. No proof set fills head or cloak.

**Follow sliders (gear_field.py, rounds 1-3, at the cap; last commit 19b48af6d):**
- An affine kernel field, one smooth correction solve (follow_solve), rigid parts made to measure, and refuse-or-flag per row.
- weight body (her plus a slider): 2/24 proof rows flagged (ranger.gloves.thread 20%; reaver.bottom 31% / 17% at the butt cleft). The stress bodies (hips, bust) are mostly fine.
- **second body (another woman): 18/24 flagged.** Mostly the body's OWN skin stretches past 2x, plus a field fold at the toe box (G's smallest singular value 0.02-0.09).
- Lead's call: second is a pure-slider body already judged FAR at the close cameras (body.md), so its flags are correct refusals. The slider proof is her_b + weight + a third slider spec on her: hips or bust_up, built with SCR\r2\chain.sh from specs/var/*.json.
- One cheap field fix is left if wanted: where G's smallest singular value is under half of Gk's, blend to Gk (stops the toe-box fold).
- r3's last background runs wrote SCR\r3\final_second.json and final_stress.json; the her_b identity is measured there.

**Bodies built:** `godot/art/people/body_p1_var/weight/` and `.../second/` (clips baked, rig_map, springs). Their gear is in `godot/art/gear/out/<name>/` and has not been imported yet. Inputs copied from body-p1: tools/body/out/round_36, clips, her_a_maps_work, topo.

**NEXT, in order:**
1. Pauldron lames on the twist chain (medium solver), with gear_wear before and after on the pauldrons.
2. The gear_wear reach bug (worker).
3. A third slider body and the in-game slider proof shots: `--body p1 --p1-dir res://art/people/body_p1_var/<name>/`, import first.
4. The plate set's missing pieces, as the first BASE-NATIVE pieces: cuisses, and an open-face helm with `"hair": "hide"`. The design is in `survivorsunchained_inputs\scratch_armor10\b_design_spec.md`. They need a native bind path, `gear_fit bind --native <piece dir>`: a mesh at her_b's rest, `_rigid` parts and materials by name (the import contract on B). Update PIECE_SCHEMA to stamp the base topology.
5. The mixed-look rulings, and s7's item 3.
6. The Marionette tool: worktree `C:\Users\munch\Desktop\Marionette_gear`, branch gear-p2 off main, /api/gear/* calling gear_fit bind/build/check, plus a panel. Push both repos.
7. Shoot the 3 sets on B at the play camera, the close-up and the Look, plus the swap, dye, helm and the slider proof. ONE su-lead-max judge at effort max, whole-frame question first.
8. Flip the `--body p1` default (People.cs ~l.370) in the same MR. Write the merge notes, commit the bindings once, and post MR READY here and to main.

Estimate left: ~0.7-1.0M.

**Costs so far:** 7 solvers, ~1.65M subagent tokens (s1 234k, s2 263k, s3 221k, s4 230k, s5 217k, s6 247k, s7 242k), plus this lead at ~300k.

## Paused here (Armor 18, 22 Oct, shoulder-only session); the arm root became a BODY item
**Update 23 Oct:** the owner approved the arm-root source fix and it ran on armor-7. Its state and next steps are in `docs/handoff/body.md` ("Arm root (Body 1)"). BJ1 passed the arm at 1:1; an owner-angle reshoot is still due. The armor items below still stand: the R1/R2 clips are unjudged, and nothing is merged.
Worktree `.claude/worktrees/armor-7`, branch armor-7 (junction worktree). Scratch: `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\543ece4a-9bcd-4cea-b6df-915822bec5eb\scratchpad\armor18` (texts backed up to `survivorsunchained_inputs\scratch_543ece4a\armor18`): cj2.md and rj1.md (judge briefs), r1/r2/d1 briefs and their scripts (r1\araise.py torso A per frame; r2\hl.py, axe.py, wpn.py; d1\m1-m4.py mesh, weights, collapse), run.sh with list1-3.txt (shoots), sheet2.py.
- **CJ2 (max) on C2: FAIL, far** (`godot/.shots/armor17/c2/verdict_cj2.md`). Correctives can't make the shape.
- **R1 (d2eb0c5c, a34f735f): reaver_show, catch_breath and flask_drink restaged to A <= 90** (117/117/99 -> 83/89/88). RJ1 (max) passed the shoulder; **the owner and main overturned it on reaver_show's peak.** These crops in `owner_frames_22oct\` are all FAIL; calibrate every judge on them: reaver_show_shoulder_top_facets_r1.png, reaver_show_armpit_notch_r1.png, reaver_show_shoulder_r1_1to1.png, reaver_show_upper_arm.png.
- **R2 (e65deb17), unjudged and unshot:**
  - catch_breath plays only with both hands free (`logic/Play/FreeHand.cs` Both, FreeHandTests); held pieces had gone 60-90 mm into her thigh. Its hair push is polished.
  - reaver_show's axe head stays in frame.
  - New `--sheathed` shot arg (PlayerView's hold line).
  - Judge list `list3.txt`. dotnet 1076/0/8.
- **D1 diagnosis (numbers): the ARM ROOT is the mesh first, then the weights. FAR.**
  - The arm is the coarsest skin on her (decimated triangles, no loops). Median edge: upper arm 1.27 cm (slivers to 6.2 cm), deltoid 0.96, breast 0.74, face 0.18.
  - At the close-up (2.80 m, 24 deg, 9.4 px/cm, LOD0, smooth normals) the outline chords are 11-13 px with 14-22 deg corners.
  - The bicep crease is the twist hand-off across one 6.2 cm sliver.
  - The pit is at the 4-bone cap and already pinched in the bind pose.
  - Upper-arm section keeps 0.79/0.70 of rest at A 82.
- **Proposed source-fix round (NOT started; the owner decides):**
  - Remesh a patch from mid-clavicle and the pit to the elbow crease at about 0.4 cm, with a deltoid cap and an opened pit.
  - Transfer the weights and smooth the twist band; project the UVs and re-bake; rebuild the correctives.
  - Then the lead-8 chain: NAPE=0, nape_post, neck graft restore (check it), build.py --all, cover.py, heroine_lod.py, reimport. Re-judge the arms-down frames too.
  - Cost 300-400k, 8-12 h; risk high.
  - The lead suggests it become a body item with its own lead, and asks whether a clean MakeHuman/Marionette arm could be grafted instead.
- **MR state: nothing to merge.**
  - armor-7 holds the earlier judged pieces, the C1/C2 art and the R1/R2 clips, unjudged as a whole.
  - heroine.res and heroine_clips.json are packed locally, not committed.
- Wearcheck over 22 clips, correctives off vs on: `armor18\wc_off` and `armor18\wc_on` tables.

## Paused here (Armor 17, 22 Oct, coordinator wind-down); history
Worktree `.claude/worktrees/armor-7`, branch armor-7 (junction worktree: remove `godot\assets` before merging integration, remake after). Scratch: `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\67a4f142-1816-491a-be2f-c6d6488eb39a\scratchpad\armor`. Subfolders: a1 = leak audit and AJ1; c1, c2 = corrective briefs and frames; n3, n5, s1 = solver briefs; `shoot2.sh` and `run.sh` = shoot with a turn (run.sh's 4th arg `import` reimports first). API judges are blocked until 1 Nov (usage limit): every judge is a su-lead-max subagent.

**1. TOP: her raised shoulder and armpit** (the owner on reaver_show's armpit: "oof thats bad").
- Calibration frame: `survivorsunchained_inputs\owner_frames_22oct\reaver_show_armpit.png`. It shows a flat shoulder top breaking into a hard corner, no armpit hollow (a single crease line), and no deltoid.
- It is NOT parked: it leaks into close-range poses. The torso-axis sweep is `godot/tools_scenes/arm_raise_scan.gd`; A = upper arm vs the torso's down axis, 90 = level. Close-range clips above level: reaver_show (A 117), catch_breath (117), flask_drink (115, C04's cinematic), warden_show (104). lie_side_wake (157) is in no cinematic. Combat clips are play camera only.
- Diagnosis: the skinning, not the r2 fold morphs.
- r1 (C1, 40ad9164): delta-mush pose-space shapes (`tools/assets/shoulder_psd_post.py`, body post step 7c; `Play/ShoulderPsd.cs`, driven by HerRaise). Max CJ1: FAIL, medium. "Smoothed targets can't add shape." Keepable: zero effect up to level.
- r2, the approved REBUILD (C2: afc69dfd code, aefb019e art), installed and **UNJUDGED**:
  - a clavicle lift of 0.36*(A-90), the larger of the clip's own and the target, with the hands kept (`Play/ClavicleLift.cs`, `Actors/HerShrug.cs`, `helpers.shrug`);
  - sculpted targets: deltoid cap ellipsoid, pec/lat 30 mm webs, a 16 mm hollow, an untangle pass; samples at A 117/140/175;
  - the neck partly in the region;
  - the shoulder fill follows under the pauldrons; wearcheck is back below pre-C1, apart from two slight regressions (warden.top 47 to 51, the reaver collar's worst point 13.9 to 20.1 mm).
  - Fix 3 (armpit weights) is NOT done: changing weights moves arms-down poses.
  - C2's own read: rv medium-close, cb close if the fleck is gone, fd medium (no lift added), cr and lp medium.
  - Sheets: `godot/.shots/armor17/c2/sheet_*.png` (17). BEFORE = C1's build.
- Next: ONE max judge, CJ2, brief modelled on `c1\judge.md`. Calibrate on the owner's reaver_show_armpit.png. Include fix 5 (warden and stalker frames: no skin through the pauldrons) in the judge set.
  - **If CJ2 isn't "close": restage the three close-range clips** (reaver_show, catch_breath, flask_drink) so the upper arm stays at or below level, stop, and report the cost.
  - If close: one fix round on its notes (armpit weights with arms-down measured), then the MR.
- Cost so far: C1 213k, CJ1 116k, C2 231k, AJ1 94k.

**2. Arcanist caps become wide flat straps** (the owner: "straps are fine if you think they are better!"): 4-5 cm, flat along the neck-to-shoulder slope, deltoid bare, armhole inside the shoulder point.
- N3's source re-cut (aabe7f2b, 34969907; CAP_MAX etc. in heroine_outfits.py; arc_fit_post retired) failed OJ2 (medium): any cap over the deltoid reads as a pad.
- The neckline mirror from N3 PASSED: keep it.
- Rebuild `--only arcanist` plus the post chain after item 1 settles (both touch the chain).

**3. Small items:**
- **Warden top strap sawtooth at the Look** (look_f, screen-right strap inner edge; NJ3 whole-frame fail). S1 (nothing committed) ruled out alpha, tuck, AA mode, normal map, sheen and stitches. Likely cause: a 0.4 mm gap between the gold piping tube and the band. Next: a post-step closing the gap row by row (`extras.strap_rows`), before heroine_lod.
- **Arcanist hat brim underside:** a flat black disc when the camera looks up (OJ1, OJ2). No rendering lead is staffed; main is putting it in RESUME.
- **fan_fill:** wired into build.py (42a71ab3). Installed pieces with fans left: plate_pauldrons_plain (43; the fill about doubles its steel mesh), and lod1 meshes (1-4 each). Fill them on their next rebuild.

**Closed this session:**
- Steel-cup bug (6468b40f: HerRaise read "../HerJiggle", a sibling; HerJiggle is the skeleton's child).
- OJ2: plate night cup PASS, neckline PASS, reaver fur PASS, satin gloves PASS-WITH-NOTES (the night tint knob left open as optional).
- NJ3: Look pauldrons PASS-WITH-NOTES, closed (fan_fill.py, 82393b1d).

**MR state:** nothing merged yet.
- The judged-PASS pieces (the cup fix 6468b40f; OJ2's passes from N4 2822c6bb; the N3 collar; the NJ3 pauldrons 82393b1d) sit on armor-7 with the unjudged C1/C2 art (heroine.glb plus the four outfits).
- So the MR waits for CJ2, or cherry-picks the code-only pieces (6468b40f, 82393b1d, 42a71ab3, 68a80250).

**4. B2** (the cuirass passed K5; the g-string is WIP), its own MR later.


Older blocks: history/armor.md (grep by keyword, never read whole).
