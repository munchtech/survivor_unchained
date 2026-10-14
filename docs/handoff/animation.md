# Handoff: animation

For the next animation lead (`su-lead-high`). Read `docs/team/README.md` ("Working lean", "Safety"), `RESUME.md`, `OWNER_NOTES.md` ("Animation: joints and motion to perfection"), then this page and `docs/team/animation.md`. Written by ae2a9884e3e51609c (branch `worktree-agent-ae2a9884e3e51609c`), handed off at about 320k on 7 October. **Read by section: grep, then `sed -n` the lines. Whole-file reads were this lead's largest context cost.** Earlier leads' ids are retired.

## 0. Paused here; next: (lead 24, 13-14 October 2026; wound down with the coordinator)
S = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\1be2d2a9-6106-4122-a964-84d08ba42428\scratchpad\anim\` (keep it). Lead 23's section 0 is in git at 58585b68. Nothing from this session is merged: the coordinator merged anim-staff-pack-1, then took it back out. The owner, on `S\staff4\mat\idle_three_glb_zoom.png`: "that image reads as in her hands to you? its not". **Lesson: never send the main session a picture a judge hasn't passed, and judge the hand first.**
**Done (branch worktree-agent-af8dbda3195e438e4; all WIP unless noted):**
- 23e2b24d `anim_review` GAMEMAT=1: held pieces drawn as the game draws them (Arms.Hold, the glb's own materials). The game path is the glb's materials (no override), byte-identical to the source atlas.
- 74f53e84 pack (dotnet test 905/0). Stale now: the fist changed after it. Re-pack before any merge request.
- 4eb83530 (fist solver): **the staff runs through her closed right fist.** FistAtR/FistDirR are refitted to the real hollow; the old pocket was 40-65 mm off, through the thumb web. keyed.py `WRAP["staff"]` holds per-finger bends: the right "grip" becomes the wrap when the clip holds a staff. idle.py and sprint_stop.py lean the staff head out of the brim. f92cc9ca + bf641436 are the thumb refit (web span 79 -> 64 mm; thumb_03 eased to 65).
- Judge j4 (`S\fist\verdict_j4.md`): items 1 and 3-5 PASS (inside the hand from every view). Item 2 FAILS: skin shows through the arcanist glove at the web, the thumb and the finger pads.
  - That's the **outfits lead's fix A** (hide the hand skin under the glove: `heroine_outfits.py` "hides") or fix B (the glove copies the hand weights). The coordinator has passed it on, along with j4's other outfits note: the right glove renders brown and the left purple.
  - Measure with `S\fist2\thumblib.py` / `svg_clip.py`: skin points not 0.5 mm inside the glove, idle 368, stop_r 2562.
- Checks on the new pocket: `S\fist\fistwrap_new.py` and `S\fist\staffgap2_new.py` (every staff mesh to skin, outfit, brim and cone, gate >= 10 mm). Idle 22.6, stop_r 24.3, stop_l 38.6 mm.
**Next, in order:**
1. **Staff:** when the outfits glove fix lands:
   - re-shoot with `S\fist2\shoot.sh`;
   - fresh lean judge, checklist: inside the closed hand from three views; no skin through the glove;
   - re-pack (`S\pack\pack.sh`; its WIP list keeps bull_rush and the Flare out), dotnet test;
   - merge request, **leading with the judge's view of the hand**. Build the request branch without the bull_rush and Flare WIP: anim-staff-pack-1 was made with `git merge-tree --write-tree` + `commit-tree`.
2. **Flare round 9** (`S\flare7\r9.sh <tag>`: build, staffgap2_new, gates.py). 5bca5171 keys the staff by the SHAFT's line and the pocket (shortest turn in `right()`), seeded from s23's world values. s28: the staff clears body and hat by >= 16.2 mm on every frame (was 0.7 mm, under on 18 frames); arm R to breast 32, staff to thigh 54.
   - **Open:** the right hand's heel is 2 mm from the hat at f16 (`S\flare7\handhat.py`). Moving f16 3 cm forward didn't help: try the hand's roll or the head's pitch at f16.
   - Also open: AIM_LET_GO (the left forearm's 44 deg spin at f20: spread it over 3-4 frames); the butt's slide; the stale comment at STAFF's planted keys; the left hand's pocket (M_L is still the old mirror).
   - Then a narrow judge, pack, and tell the Flare lead.
3. **The other staff clips** move with the new pocket. Re-check cast_bolt, cast_raise, arcanist_show, idle_arcanist_break and sprint/run_arcanist with staffgap2_new, then apply idle's upright-staff fix (lead 23's item 6). run_arcanist keys "open" fingers, so it gets no wrap.
4. **Sword trio** (lead 23's item 5): fore C5 (`Z\sw1\c.py`) and heavy H3 (`Z\sw2\b.py`) on the HAND_FRAME keyed.
5. **Grip-fist system for the sword, daggers, axe and crossbow** (j4 item 6; `S\fist\others.py`). All four have the staff's old fault:
   - chevalier_sword is "skewered through an open hand" (the face judges' mangled hilt);
   - the daggers sit in a limp open hand;
   - the axe's thumb is a hitchhiker's;
   - the crossbow can't be read.
   Per weapon: seat the grip in the fitted pocket, and give it a WRAP for its grip radius. They use Spec.Grip, not anchors, so give them anchors or a per-Kind pocket. Order: sword, daggers, axe, crossbow.
6. **bull_rush PARKED** at 9b5486fc. r7 judge `S\br7\verdict_j_r7.md`: items 1, 2, 3, 6 and 8 PASS.
   - The carry: e156b4c2's forearm-first carry passes the wrist gates.
   - The f13 forearm spin's cause: `solve_frames` averages the elbow over 13 frames, and SWORD_WAY's poles swing it 123 deg, so the arm plane turns 51 deg. Fixed by per-frame elbow planes (`_sword_way(rig=)`, ROLL_STEPS, WRIST_CUM): roll now <= 26/15.
   - **But** with the elbow high, the blade dips under and crosses to her left at f17-19 (tip +31 cm, 1-2 mm from the shield). ELBOW_BUMP brings it back, and the roll with it. **It needs a new route: SWORD_WAY's hand path or the blade's route, not the poles.**
   - Corrected gates (solve8's brief): hand pace is in degrees per frame; the guard's own wrist is -29/21 from f22.
   - Also open: N1 (the f13 shield swing), N2 (the rear foot's launch), N3 (the shield hand opens f20-30), N4.
   - Tools: `S\br7\solve8\m10.py`, `S\br7\m6.py`.
7. Then lead 22's list (the crossbow stock, the sprint's trailing foot, the hero's run) and the face judges' greatsword pommel at the close-up camera.

## 0b. Weapon anchors and sockets (12 October 2026)

Sheathed in town is a SYSTEM, not per-item work. A new asset needs only its `Arms.Spec` row (file, length, grip, **Kind**); no socket code.
- **Kind to socket** (`logic/Play/WeaponSockets.cs`, tested in `tests/WeaponSocketsTests.cs`; geometry in `src/Actors/Arms.cs` `Sockets`): Shield `back` (spine_03); Blade1H `hip_blade` (left hip, scabbarded; scabbard length from the blade); Blunt, Axe `hip_loop` (right hip, head up); Wand `hip_belt`; Dagger `belt_back`; Crossbow `sling` (across the back); Blade2H, Axe2H `back_diag` (grip over the right shoulder, tip toward the left hip); Staff none (a walking staff, stays in hand). A left-hand piece mirrors.
- **Anchors:** if the asset's scene has Node3Ds named `anchor_grip` and `anchor_sheath` (any depth), `Arms.Make` uses them: origin = the point, **-Y down the blade or haft toward the tip**, **+Z the edge or face direction**. The grip anchor replaces `Spec.Grip` (and `Flip`/`Roll`, which the axes decide). The socket puts the SHEATH point at its spot and lines the long axis with the socket's shaft. Fallback (no anchors): the principal long axis from the bounds, `Spec.Grip` and `Length`; the sheath point is the grip.
- **Kind tag in the asset:** a glTF node extra `kind` or a node named `kind_<kind>` (`blade1h blade2h blunt axe axe2h dagger wand staff shield crossbow`) beats the Spec row's Kind.
- **Clearance:** `godot/art/anim/socket_clearance.json` = `{outfit: {socket: metres}}` (outfits warden, arcanist, reaver, ranger, none; unknown = 0). The socket is pushed out of her body along its normal by the worn outfit's thickness (`Arms.Sheathed(id, left, calling)`; stalker is ranger). `python tools/anim/armscheck.py --sockets [clips] [--step N] [--keep]` refits the file (garment cover at each socket + 5 mm air) and prints worst mm into skin and into outfit per kind x outfit over idle_<calling> and any `*_town` clip. It reads the `sheathed` key of `tools/anim/data/arms_local.json` (ArmsDump writes every kind's piece there): re-run ArmsDump after a new Spec row, then `--sockets`.
- **Note for Marionette export (DONE: in `C:\Users\munch\Desktop\Marionette\HANDOFF.md`, Marionette commit 9757a13):** weapons and armour pieces exported from Marionette carry `anchor_grip` and `anchor_sheath` nodes (axes above) and a kind tag (glTF node extra `kind`, or a node named `kind_<kind>`); the game reads them and falls back to the Spec row if they are absent.

## 1. The owner and the brief
- "the motions that get scuffed are ... bad, unnatural movements with respect to wrists - follow through motion joint to joint, some elbow pinching or arms going through body or breast, some sliding. a lot is GOOD but we want perfection."
- Brief (coordinator, 7 Oct): first the elbows: build the helper bones, see them at 1:1 in motion with jiggle on, prove the fix with before/after numbers and a sheet; when verified, tell the outfits lead **a1f120018d8749c97** directly (copy the main session) so they rebuild with helpers and rerun the motion check. Then the full audit (her and the hero, every clip, four outfits), arms through her body and breasts, follow-through, wrist limits, foot locking, a walk cycle in play. Sign off per clip. Rendering (a7afb4d33cdd5efba) owns how motion is drawn; joints are ours.
- **Owed to the face lead (abe65bc929823a791): sign-off on her head's 8-degree carry in play** (step 3 below).

## 2. Done (committed; helpers still off: no `--helpers` by default)
- Built her body and outfits with the helpers (4.5 min in Blender) and checked: positions, normals, UVs identical to the committed build; only weights changed; share bones lie on their hinges (`hinge.py`: 0.00 degrees). The skeleton dump then has 81 bones, helpers in hierarchy order (indices shift; Godot binds skins by name, so fine).
- Seen at 1:1 against the true before body: elbows, shoulders, forearm turns clearly better. **But the knee came to a sharp point at 120-145 degrees, and the elbow a knob from behind at 145.** Cause: the share weights were cut as a tent (`2*min(Wa,Wb)`), so the skin over a joint is two straight runs meeting in a ridge. Not the bulge: with no bulge the point stayed.
- **Fix, decided and committed in the spec** (`tools/anim/helpers.py`): `"profile": "smooth"` (weights as a quadratic Bezier's over the point's blend x: `(1-x)^2, 2x(1-x), x^2`; each point still turns x of the bend on average) and a new bulge law, stretch `2 - cos(bend/2)` (keeps the point halfway round at its rest distance: a rounded corner), elbow and knee `bulge 1, bulge_max 2` (`helpers.bulge`, mirrored in `HerJoints.cs`). Seen at 1:1 (body only, via `reweight.py`): rounded, fuller than before, no point: `docs/team/anim_sheets/helpers_split_knee_elbow.png` (rows: before, tent, smooth+bulge, smooth no bulge). The tent build's elbow side sheet: `helpers_tent_elbow_side.png`.
- Volume kept (region round the joint, % of rest; `sweep2.py`), before -> smooth decided: elbow 90/120/145: 72.6/61.1/54.4 -> 83.3/70.4/56.1; knee 90/120/145: 74.5/64.5/59.1 -> 89.0/81.8/72.9; hip 110 knee 135: 67 -> 95; arm raised 130: 72 -> 92; upper arm turned 70: 74 -> 87; elbow 90 with the wrist turned 80: wrist 94.5 -> 100. (The tent kept more by this measure, 92/78/61 at the elbow, but its ridge is what shows.) Deep elbow volume is mostly the inner fold passing through itself, hidden.
- Garment check on the **tent** build, warden only (`tools/scratch/anim6/gap_tent_warden.txt`): skin through garment at elbow 120/145 rose (678 -> 1173, 1123 -> 2282 points; deepest 9 -> 11 mm), and at knee 145 to 21.6 mm; it fell at wrist turns (239 -> 2), knee 90 (1107 -> 499), raise 100 (113 -> 16). Rerun on the smooth build.
- Tools: `anim_review.gd` plays a JSON clip by path (test poses, unpacked clips) and reads her body and outfits from any build at run time (`BODYDIR=`, no import). Scratch tools in `tools/scratch/anim6/` (repoint `S`, `WT` paths): `build_helpers.sh` (Blender build with `--helpers`, import, skeleton dump), `rigtest.py` + `clips/` (elbow, shoulder, knee test poses; a rest frame first), `shots1.sh` (before/after sheets), `shots3.sh` + `variant.py` (spec strengths without an import), `reweight.py` (any split written into the built body: try weights without Blender; needs the helper-built body in godot/art/people), `sweep.py`/`sweep2.py` (volumes, ridges), `gapcheck.py` (garment split against skin, skin through garment per pose), `samebody.py`, `pair.py`, `rows.py`, `sidecars.py`.

## 3. Next, in order
1. Rebuild with `--helpers` (`build_helpers.sh`; it builds into the worktree's godot/art/people and dumps `tools/anim/data/heroine_skeleton.json`), run `samebody.py`, `sweep.py before built`, then `shots1.sh` (elbow, shoulder, knee, plus cast_raise, cup_hands, sword_fore) and the same clips in each outfit; judge at 1:1, jiggle on. Check the shoulder at raise 60-100 for swelling (volume 104%) and the forearm turns close (`LOOK=hand_l`).
2. `gapcheck.py` on all four outfits (about 10 min an outfit; give it to a runner). Send the split agreement and the before/after table to the outfits lead (a1f120018d8749c97), copy the main session. Then make helpers the default (`heroine_rig.apply`: drop the `--helpers` gate), commit the built body, outfits and skeleton dump, and ask them to merge, rebuild and rerun the motion check.
3. **The head carry** (face lead's ask): `HerCarriage.Level` lifts her face toward 8 degrees above level at `HeadLevel` 0.8 (`PlayerView` line ~588) in every play state but death: also through rolls, leaps, vaults and get-ups, where a tucked head lifted up to 28 degrees would look wrong. See it in play at 1:1 (run, idle, a strike, dash, leap, get_up) and likely ease `HeadLevel` to 0 while a full-body one-shot plays; then sign off to abe65bc929823a791.
4. Then the old list: the full audit (`motion.py --outfits --save`, before via `ANIM_PEOPLE`), arm clearance against her mesh, follow-through as a post-pass, foot locking (warden_show first), the in-game stride, walk cycle and runtime foot lock, the hero's helpers (with ab82cbe99e2937ddd).

## 4. Gotchas
- Worktree setup for Godot: `godot/assets` placeholder moved aside, a junction to `public/assets` made, `git update-index --skip-worktree godot/assets`; main's `godot/.godot` copied (robocopy, 2.6 GB); `sidecars.py` copies main's untracked `.import`/`.uid`; `dotnet build`. The first import still re-imported about 1000 files (10 min) and segfaulted once: retry. Tracked `.import` files then show as modified: never commit them; stage explicit paths.
- `NOJOINTS=1` on a helper-built body is **not** the body before them (an elbow's share then follows the upper arm). Compare against a copy of the old build with `BODYDIR`.
- anim_review photographs from the clip's second frame: test clips lead with a rest frame.
- Her clips' JSON (`tools/anim/out/clips`, `out/hero`) are not in git: copy them from worktree agent-a9a80800a7dae2519.
- The guard refuses heredocs and `cd && git` chains: write scripts to files.

## 5. Read first
`tools/anim/helpers.py` (`split`, `bulge`, `drive`), `godot/src/Actors/HerJoints.cs`, `tools/assets/heroine_rig.py` (`apply`), `tools/scratch/anim6/build_helpers.sh` and `shots1.sh`.
