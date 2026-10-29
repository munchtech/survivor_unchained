# Cinematics: handoff

## HANDOFF: Cinematics 9 (29 Oct, at ~255k), branch cine-8; next: Cinematics 10 does C01
**Done and merged or MR READY:** MR 1 merged (C02 night + C03 cut). MR 2 = cine-8@HEAD (C04 A), tests 1308/0/10.
- **C03:** s8y (empty hands) CUT (max judge FAIL medium); s8 cuts on the burst (3.27 s) to s12, which carries G1, the sniffs, G2, G3. The rig cue gained `"fade": true` (80d9747f).
- **C02:** s1/s10 use C03 s2's atmosphere, grade and haze (same night); cool back key on her in s1; s11 rigs off; s11 the boss title WITHOUT her (`hide`; her head fell on his crotch line from every camera height), she is back at s12 (place (1.5, -31.83)). Three xhigh rounds, cap used. **Waits for Warden 6's model (main agreed):** s7 (lamp to her face, true profile), his tired stance (`folk/m_idle_armed` looked at ease but its sword crossed her), his lantern flame (flat cyan in play light at s12) and warm wash in play light (routed).
- **C04 A:** A7 (face CU), A0 (lamp) and A8b (letter) CUT after the final max judge (cap 4 used). Order A1s, A8a, A8. `lamp_out` is the conversation's entry and plays first over A8a, then reeds/back; the face line over A8 from behind PASSED. Kept for a later try (judge r2 marks): A0 PROP SOLVED with Poly Haven's `art/world/wooden_lantern_01.glb` on its side, scale 0.5 (see git show db791839); its fail was the place: needs pebbles under it and a wet band, reframed along the shore with water at most a third of the frame and the pillar base out. A8b was CLOSE: the line must look like ink (stroke weight, faint bleed, fold shading over it), paper muted ivory with a falloff, ribbing/flecks to a third (`tools/assets/letter_prop.py`; camera in git show 145dd039). `lamp_dropped.glb` (procedural) is superseded by the wooden lantern.
**C01 (NOT STARTED by me; item 1 of the fixed list, the biggest):** follow Cinematics 8's survey and plan below (lieB, fire 0.7, the 1.1 m bedroll camera, prints low and tight in firelit earth, restage s10/s12 by hand). Brief a su-lead-high MEDIUM solver to build and shoot (no max solvers: main, 29 Oct), then ONE max judge per round (her frames). Scrap rule: medium/far after round 1 = restage or cut, tell main.
**Tools (scratchpad `...61174ebb.../scratchpad/cine9/`, also the solvers' `c04/`, `c04r2/`):** `shoot_nb.py RUNS.json [--nobuild]` (one godot turn per batch), `mk98.py SRC edits.py [c98|c97]` (test copies; delete before commit), `jedit.py CID edits.py` (edits the real file in its format), `proj.py` (bone screen positions; 36 mm horizontal gate), `sheet.py`. Merge integration: set aside untracked .uid/.import the incoming tree tracks, `cmd /c rmdir godotssets`, merge, remake the junction to the worktree's own public/assets, `git update-index --assume-unchanged godot/assets`.

## HANDOFF: Cinematics 8 (29 Oct, coordinator wind-down), branch cine-8, nothing judged yet
**Fixed list (from 7050fc3c, order kept):** (1) C01 new opening per `docs/cinematics/c01_opening_beat.md` (bedroll, shadow, prints, rising, play); (2) C03 s8 reshoot as a high over-the-shoulder past her empty hand; (3) C04 A inserts: letter, dropped lamp + `cin_first_light.lamp_out` node AND cue together, A7 face hold; (4) C02 Warden: wash, grade, s7 true profile, s11 tired stance. Then one max judge on her shots (xhigh without her), owner before|after half-size sheet, MR. Main approved moving her lying spot in cinematic data. Main on prints: put them where they read at 1:1 (firelit earth/ash, not frost); if they fail round 1, restage, and let her shadow crossing the bedroll carry the beat.
**Built (the game can now):** a `fingers` cue (HerPose.CineCurlL/R, per hand, eased; 43ce23c5; right-hand sign worked out on paper only, so check it on screen). `prop` cue `"scene": "res://..."` places any GLB on layer 1 (abd33beb). Props (7c10b3ab, unjudged, never imported): `art/props/letter/letter_open.glb` (`tools/assets/letter_prop.py`, Hershey script, "Come home by the Low Ford." legible) and `art/props/lamp_dropped/lamp_dropped.glb` (`tools/assets/lamp_dropped.py`, on its side, cracked pane). The builder flags two risks: the crisp line may look overlaid, and the lamp iron may read uniform black.
**C01 surveys (scratch `cine8`, test file `c99_v3.json`, a copy of c01's setup with test shots; copy it to godot/data/cinematics/c99.json to reuse it and delete it before tests, since CinemaTests fail on it):**
- Today she lies at `down`/`lie`, east of the fire. Her shadow falls east, onto the log, away from the bedroll (zone bedroll at (-12.9, 92.4), south-west).
- The test that read best is v2 `sb1`/`sb2`: she lies on her side (`her/lie_side_wake` frame 0, speed 0) at lieB (-11.24, 91.08), heading 2.305, between the fire and the existing bedroll. Settings: fire `light 0 level 0.7, size 0.15`, atmosphere night `key 0.12, hemi 0.15, env 0.15`. A clear shadow band then crosses the bedroll. At 0.24 / key 0.4 the shadow doesn't read.
- Moving the bedroll east onto the old spot's shadow line, to (-7.5, 93.2) (v3), was too far from the fire and black. Reverted; don't do it.
- The bedroll camera at grass height (0.5 m) is blocked by grass blades. Use about 1.1 m looking down (v2 a2/b2: pos (-13.9, 1.1, 93.6) at (-12.75, 0.05, 92.3), 50 mm).
- Prints have not read yet in any test (v2 a3/b3, v3 c4): aim lower and tighter at the last 3-4 prints in the firelit earth.
- Consequence: with lieB, s8 (bone-relative camera, fine), s10 (abs camera) and s12 (crane, `reach`/`end`) must be restaged on her side of the fire. Rotating about the fire by -116.7 deg in heading moves R1 onto the end mark, so don't rotate blindly. Restage s10/s12 by hand and keep R1-R4 where they rise.
**C01 plan (approved by main):** black (s1, keep) -> s2 bedroll MS, N1 `bedroll` at about 1.0 s -> s3 a pan along the shadow to her boot at the frame edge -> s4 prints, N2 `prints` -> s5 the rise (lie_side_wake then reach_coals, hair over the face, hand at the coals) -> s8 frontal breath CU with no line (judged before) -> s8a lamp ELS + call (keep) -> s10 snap to stand + turn -> s12 crane, play. s3's face CU goes. Update `docs/cinematics/shoot/c01.md` and c01_drowned_fire.md when it lands.
**C03 s8y (12bb615c, WIP, unjudged):** s8 is cut at 3.27 s and s8y is the remaining 4.73 s. The head dip is removed, and the heart is placed in her hand, then moved under over 0.35 s while its glow fades over 1.1 s. `fingers` curl 50 over 1.0 at 0.55. The v3 frame is dark: her forearm and gauntlet show, the hands barely. Next: light the hands (the skin rig onto `hand_l`, plus a stronger spill from the heart for 0.3 s), raise or pull the camera back so both open hands and the water under them read (cam abs (3.99, 1.97, -37.41) at (4.71, 0.6, -38.37) now; she faces heading 2.18, mark her (4, -38)), and check Grimtunnel stays dark.
**C04 A plan:** new A0 (low on the north bank's stones, `lamp_dropped` via the prop cue, the lamp_out line; add the dialogue node `lamp_out` as the entry with `next` reeds, in `godot/data/content/dialogue.json` `cin_first_light`, in the SAME commit as the cue) -> A1s -> A8a (reeds/back) -> the letter insert (letter_open.glb filling about 70% of frame in dawn light, no hands, silent) -> A7 CU face hold over the `face` line (move it from A8; gaze held, no ear, no tilt) -> A8 she sets off.
**C02 plan:** the cause per Warden 4 (warden-1 handoff): the night atmosphere cues use hemi 0.45 / env 0.45 against C03 s2's 0.18 / 0.2, and the lamp light sits at his sleeve. Not light layers (he's on layer 2). Try hemi 0.18 / env 0.2 on c02 s1 and s10, and a less saturated grade. s7 is cut on integration: restore it from `warden-1/godot/data/cinematics/c02w.json` s7 (folk/m_bend_lift) in true profile (camera due west, square to their line). s11: give the Warden a tired idle clip (find one in his library).
**Turns:** none held. **Scratch:** `...7050fc3c.../scratchpad/cine8/` (shoot.py, jedit.py, sheet.py, ed_c03_8y*.py, v1-v3 runs, c99_v3.json), backed up to `survivorsunchained_inputs\scratch_cine8`. Frames v1/v2/v3 are in the worktree's `godot/.shots`. The worktree is imported. Untracked/modified `.import` and `.uid` files come from the first import: don't commit them.

## MR READY: Cinematics 7 (28 Oct): face motion to a minimum (C01's eye darts), DONE
**Owner:** "the opening cinematic when here eyes dart is comically not good"; then "keep our cutscenes face movements to a minimum ... we can't express the movements fluidly enough at the moment for face stuff". Rule from now on: hold her gaze and expression through a shot (set at the cut), let the head, the body or the cut carry looks, and use no eye darts or face-key morphs mid-shot. Where a beat needs her face to act, frame it wider or from behind.
**Judges (max, item "C01 eye darts", 3 rounds, all used):** r1 s3/s8 PASS, s10 FAIL (head pop); r2 (face-minimum) s3, s8 and C03 s8 PASS, s10 FAIL medium (braid fold, a leftover pose on the cut, a one-frame whip); r3 s10 PASS. The final judged strips (j3, j4) are backed up in `survivorsunchained_inputsscratch_cine7`; the frames are in the worktree's `godot/.shots` (a1..a5, b0..b2). The owner sheet is `survivorsunchained_inputs\cine7\cine7_before_after_half.jpg`.
**Code (the game can now):**
- `HeadTurn.Glide`: a head cue's new aim glides there (smoothstep at its `over`) instead of popping when the head is already turned. A head cue at a cut is taken at once and re-hangs her hair (`HairSway.Settle`). Glide is cinematics only and switches off at Finish.
- `Play/GazeShift` + `GazeCarry` (11 tests): saccades timed by size (25 deg per iris radius, measured), a gaze cue `over` glide, a look set at once at a cut, the upper lids following vertical gaze a little, and a blink with a jump of 0.4+ radii (`blink` true/false). Head carry and reach clamp happen only when a cue gives `head`; it's inert otherwise.
- A cinematic's end restores her play wander (0.13); C01 left it at 0.02.
**Face/eye cues per shot (removed / kept):**
- C01 s1 (black): kept lids shut and gaze [0.15,0.3].
- C01 s3: gaze set while shut to [0.35,0.05] (was [0.9,0.05]); the lids open over 0.35 s at 2.0 s (kept); removed eyes_wide 0.1 / 0 morphs.
- C01 s8: gaze held at [0,0.3] (removed the 0.7 s drop to 0.9); brows_sad 0.25 set at the cut (removed the 1.2 s morph to 0.4 and the 2.5 s change); kept only mouth_open 0.05 over 1.2 s with the exhale.
- C01 s10: gaze [0,0.05] from the cut (removed the 0.05 s dart from [0,0.8]); startle face set at the cut (was a 0.15 s morph); opens mid-turn (head aim [-11.02,0.65,89.03]), finishes the turn over 0.2 s from 0.03 s; dur 0.4 (was 0.35).
- C01 s12: expression set at the cut (was a 0.3 s morph); removed the arcanist smile flick (1.95 s) and its reset.
- C03 s8: face (eyes_wide 0.3, mouth_open 0.12, brows_sad 0.15) set at the cut (was a 1.0 s morph); removed the snatch's startle morph (eyes_wide 0.7, mouth_open 0.22 in 0.12 s); kept the startle blink and gaze [0,0.6]; the head's dip at 3.3 s now glides.
- C03 s12: gaze [0,0.9] kept (from behind).
- C02, C04a, C04b: no face cues; added a first-shot `gaze wander 0.04` so her eyes don't flick in close-ups.
**Open (owner/next cinematics):** C03 s8's look down "at Grimtunnel" now passes on motion, but r2's judge says the face can't carry the beat (she bows a notch lower, the frame fills with hair). Its restage: cut at the yank (about 3.27 s) to a high-angle over-the-shoulder shot past her empty hand as the glow is pulled under, Grimtunnel in shadow, her fingers closing, no dip. That's one new shot and one judge, about 100k. **Routed to Face:** waxy flat skin, grey-mauve lids, near-black sclera at C01 s3, the moulded hair shell and braid card gaps (s10), a hard face edge under C01 s8's frontal key. Body: an armpit crease at s10's rise (already in the shipped build). Later: C01 s10's rise has a spring in its first frame (the clip; ease the hips' peak).
**Scratch:** shoot/jedit/sheet/crops tools and edit scripts are in `scratchpad/cine7`, backed up to `survivorsunchained_inputs\scratch_cine7`.

## MR READY: Cinematics 6 (21 Oct): C03 done, four shots ship; next: merge, then STOP until the boss Warden / new Grimtunnel
**State:** C03 round 3 (the last) applied, judged and closed by two confirmations. Ships: **s2, s6, s8, s12** (31.6 s; `docs/cinematics/shoot/c03.md` "As shot" lists each shot, the cuts and what restores them). Judges: r3 `a25ec932` (2/12: s2, s12 end), confirmation `a93b6ca3` (s2, s6, s8, s12 SHIP; s9 CUT twice: placeholder Grimtunnel), final `a2cb8db1` (s8 with the snatch folded in SHIP x4, s12 end SHIP, s12 opening SHIP with a 4-degree nudge, applied: `c6r3p_c03_s12_1`). Frames `godot/.shots/c6r3*`. Edit scripts `tools/scratch/cine5/ed_r3a.py`..`ed_r3p.py` (apply with `jedit.py`; scratch `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\c4134bd3-ebec-4f59-ad97-c6010364bcd4\scratchpad\cine6`, texts backed up to `survivorsunchained_inputs\scratch_cine6`).
**Shots after r3a were taken `--stale-ok`:** integration's npc_guard commits (896878c6, 02d0ed88) weren't merged; C03 shows no guard.
**Cut and logged (restore on new art):** the boss Warden: s1, s3, s4, s5. The new Grimtunnel: s9, s10, s11 and s12's dive close (his lines play off-screen in s8 and over the crane).
**Routed:** env (see-through water at low cameras, the black slab by the ford, puck stepping stones, straight banks, the repeating pine ridgeline); Grimtunnel's hat lanterns blown white discs (new model); optional anim: her fingers closing on nothing after the snatch (s8).
**Warden placeholder rule (owner, 21 Oct):** stage him low and wide; a close-up on him is cut and listed here. `judge_common.md` (scratch) carries the two-placeholder rule.

## HANDOFF: Cinematics 4 (C03, the heart scene), 21 Oct, at ~255k. Round 3 of 3 is next
**Worktree** `.claude/worktrees/cine-4`, branch cine-4 (merged integration 72e1c575, Armor B1). `godotssets` is a JUNCTION to its own publicssets (assume-unchanged): never stash, reset --hard or checkout .; before merging integration, `cmd /c rmdir godotssets`, merge, then remake it and run `git update-index --assume-unchanged godot/assets`. After a merge with new art, run one `--import` under a godot turn (a crash at the end of the first import is normal: run it again).
**Scratch** (the coordinator's pad): `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\6a6cb394-317c-45d7-aa08-3523481011e7\scratchpad\cine4`. Tools: `shoot.py RUNS.json` (builds C#, one godot turn; `--stale` adds --stale-ok), `jedit.py c03 ed_X.py` (edits shots by id; every edit script `ed_*.py` is kept there), `import.sh`, `judge_common.md` (gate, tiers, scene), `j1_brief.md`, `j2_brief.md`, `j2_verdict.md` (READ THIS: the round-2 verdict and its fixes), `light_brief.md`, `light\` (the light solver's meas.py). Sheets: `python tools/scratch/cin6/sheet.py OUT COLS W files` (absolute paths).
**Owner rules for this item:** Grimtunnel's model is a placeholder (the owner, 21 Oct): stage him so the shot passes (wider, backlit, weighted on her) and tell the judge to judge staging, not his surface. Judges at xhigh, foreground su-lead-max. Round cap 3: round 3 is the last; a shot that can't pass is CUT or restaged, never closed as known.
**Done (commits 0dff5165..540cb367 on cine-4):** C03 has its own night (shot 2's first cues: atmosphere "now" with less fill and a silver moon; grade sat 0.88 plus cinematic-only grade palette fields: moonSat, shade violet #2e2452). **s1 CUT** (the Warden's face can't hold a close-up; its setup cues moved to s2). s2 over her right shoulder; s3 his profile with the lamp; s4 the lamp stays lit going under; s5 side-on; s6 2.8 s, the heart lifts at once; s7/s8 sword and shield set down (`hold all null`, back `@own` at s9), `her/cup_hands` with her heading 2.18 (the clip is yawed 55 degrees), head cue to the heart; s8 side MCU, the heart over her palm with a blue `spill` rig; skin `rig` on her as the key in s5 and s7-s11 (energies 3.2/0.8/0.6/2.2/1.0/1.7, #f7ece6; the light solver's 2x read tan-orange); s9/s10 her head to him; s10 a dirty single on her over his hat; s11/s12 tilted up; s12 dawn `from: now`, k1 0.35. Code: `--cine` runs skip the zone name card (Game.AnnounceZone); `skin` cue + People.HerEarWarmth; `grade` cue palette fields (Atmosphere.SetCineGrade); `atmosphere` takes hemiSky/hemiGround/rimColor; `--cinebones` prints `cinepx` (screen positions). **Crowd shader bug fixed (d992b30c, kept by the coordinator):** vat.gdshaderinc ROUGHNESS = min(rough, 0.9); roughness-1 crowd surfaces had Godot's RIM washing the whole body (Grimtunnel cyan-white). The night-horde pair `godot/.shots/c4hordeB.png` (before) / `c4hordeA.png` (after) PASSED in judge r1 at fodder level.
**Judges:** r1 0/15 (cyan skin, flat blue, framing); r2 0/11 (`j2_verdict.md`): skin no longer blue but waxy gray-beige with a cut-out halo; s8 is closest (the reach reads, the hand passes at 1:1: the faceted-knuckles and split-hand marks are CLOSED, no mesh solver needed). Latest frames `godot/.shots/c4r2_c03_s*`.
**Round 3, in order (the judge's list, with the cuts agreed):**
1. CUT s4, s7, s11 (fold the beats: the lamp glowing under the water in s5; the heart drifting in from frame right at the head of s8; s12 opens on the dive, a mud plume, the glow sinking). Check line timings with tools/scratch/cin6/pace.py and the StoryLint/Cinema tests (the s11 line `cin_heart_goes_down.grateful` must still play somewhere: move it onto s10's end or over s12's opening).
2. Her light in s8/s10: people key ~4200 K, +1/2 stop; the rim (atmosphere rim 1.0 plus the back moon) narrower/dimmer: the halo; DOF edge bleed (fstop 2.8 -> 4?); double the heart's light on her palm, fingers, chin (spill rig 1.0 -> 2.0).
3. The Warden lit low in s2/s3/s5/s6: lamp as the source (a `rig` can't reach him unless he's on the people layer: check), moon rim, -1 stop ambient, flame halo/flame cue (`lamp` cue flame/halo) instead of a clipped disc. He stands in s2 (the kneel clip doesn't take: check `folk/m_kneel_lamp` on the boss). If s2/s3 still can't pass, consider CUT s3 and play "Is it morning?" over s2.
4. s9: the heart visible and glowing in his claws (glow up; it's 0.2), her recoil (her/flinch exists) with her face to camera.
5. s10: MCU from his eye line, face in the upper third, key lower and frontal with a catchlight (the `eyes` cue sets catchlights), the hat a soft sliver.
6. s12: reframe off the black plinth slab, dawn ~1/4 of the frame.
Then judge r3 (xhigh), the full test run (`dotnet test` in godot/tests), MR "MERGE REQUEST cine-4@<commit>". Whatever still fails after r3 gets cut; the scene must still tell the story (minimum: s2 kneel, s5 fold, s6 heart, s8 reach, s9 snatch, s10 talk, s12 groan).
**Routed (tell main in the MR):** the Warden's model to boss-tier art (r2: "no light makes it full-detail boss art"); env: see-through water at low cameras (legs/shins show), the black plinth slab by the ford (s2, s5, s12), the puck stepping stones, canal-straight banks at s12; Grimtunnel's hat lamps clip white (his new model). Her ear reads more saturated than her cheek (1.33-1.65x, the light solver couldn't move it): face/skin, if the judge still sees it.

## MR READY: cinematics 3 done (successor a688d6f8e4fca8912, 18 Oct); next: merge, then STOP until the new art
**State:** items 1-4 finished; three judged rounds (k10 1/33, k12 2/32, k13 the confirmation with SHIP-or-CUT). Tests 942/0/8. Verdicts: `tools/scratch/cin6/judge/k12A_verdict.md`, `k12B_verdict.md`, `k13A_verdict.md`, `k13B_verdict.md`. Final frames `godot/.shots/k14c0*` (all four, plus hand-overs `k14c0*_ho_*`).
**What ships (as the cinematics now play):** C01 s1 (black), s3 (the wake; eye rig added), s8, s8a (blue ford lamps as halos), s10 (0.35 s snap), s12 (face key 0-2 s) and the hand-over: 38 s. C02 s1, s2 (the call line), s10 (lie_down), s11, s12, hand-over: 21.4 s. C03: every shot but s3b. C04 A: A8 only (the back and face lines on it, 21.8 s; the reeds line kept for players who haven't heard it, StoryLint needs it).
**New cues and code:** `grade` (per-shot saturation), `globe` color/halo/spread, `lamp` flame/flameColor/halo, `light` size (soft shadows), follow `followFrom`, V3.ToString (test crash), the warden waits 1.0 s after the C02 hand-over (Prologue.WardenUp: he hit her the frame play started).
**Unjudged, applied exactly as the k13 judge wrote them:** C01 s3's eye rig and s12's face key, and the line moves for the cuts (pace.py: no clips or overlaps).

**Cut, and the owner whose art brings each back (restage in the next wave, step 4):**
- **TOUCH-UP (her):** C01 s6 (armor hot spots, waxy arms, parted lips), s8b (no lip-close shape, waxy forehead, hairline); C02 s4, s8 (ashen face vs orange ear and neck, hairline, pauldron highlights); C03 s3b (same, mouth open); C04 A A5, A7 (hairline cap, balloon pauldrons, orange ear), A4 (leg skin). Every close-up of her fails on these, so stage her beats wider and backlit until touch-up lands.
- **NPC:** C02 s5, s6, s7 (the warden's flat model; his lantern lights nothing: give it a real light), s9 (his face won't hold a close-up: blue eye points, beard).
- **ENV:** C01 s7 (prints that read in the frost; grass flattened on the trail), s9 (log end caps, grass cards); C04 A A1 (trunk through the frame, flat stepping stones), A2 (pines, not birches; no gold treetops), A3 (cartoon trees; she should be in the shallows); the coal bed (a domed lava pie); top-down frost reads as cotton wool at the C01 hand-over; s8a needs a keep under the gold lamp.
- **ANIM:** C01 s2's lying pose (death_back's end pose with the head 25-35° more to her left, the left cheek on the ground, the flung arm out of the face-coals line, chin down 10°), s6a (a flat palm-down hover, fingers together), s11 (a pickup with a visible grab and no shield pop, ending in a guard; the stiff, hunched step over the log), s9 (a rise that reads, head and shoulders through the frost); the warden's rise (C02 s5, sits up rather than translating); sa7's eye search or blink; flask_drink plus a flask prop (C04 A sa6).
- **FX:** the risen rise burst in `godot/src/Fx/BattleFx.cs` ~935 shows a pale square sprite with white specks (C01 s12, over the sack; in play too); C04 A sa4's ember is a flat orange disc with a hard white dot.
- **STAGING, on the new art:** C01 s12's turn in its first second (the player body after `play`; check it isn't a one-frame spin); C02 s7 as a true profile; C04 A as a scene again (it is one shot now).

## Earlier: paused here (cinematics 3 successor, ac7e54435a82fff12, 18 Oct)
1. **Two k11 max staging solvers were still running at the pause, finishing on their own.** Read their reports with `python tools/scratch/coordinator/lastmsg.py <id> <out>`; the transcripts are in `C:\Users\munch\.claude\projects\C--Users-munch-Desktop-survivorsunchained\4b7b1da3-62bc-4cd2-ab49-a52d9a8367dc\subagents\`. They commit their own work as "WIP cinematics 3 k11". Check `git status` for leftovers and commit them with their diff checked.
   - `ac62b6269fc9eedaf`: C01 (brief `tools/scratch/cin6/judge/s5a_brief.md`). It covers s3, s10 and s6 (o1-o3), s11's pickup, the s8/s8b fire keys, the night (s7, s8a, s9), thinning the s12 mist, the s11 to s12 exposure ramp, and cutting s0. Shots `k11ac01_*`.
   - `a11ffa156dc106d9c`: C02, C03 s3b and C04 A (brief `s5b_brief.md`). It covers the s8 and s4 keys, s3b's key from the lamp, the sa5/sa7 dawn keys, the sa8 mist, C02's water, mist and framing, and dimming the post globes in cinematics only. **Plus the two cuts the coordinator agreed: C02 s3, and C04 A sa6** (flask_drink exists only as a clip script in `tools/anim/clips/story_c04.py`; the shot doesn't use it and there's no flask prop). Shots `k11bc02_*`, `k11bc03_*`, `k11bc04a_*`.
2. Then **judge round 2** on items 2-4 (max; reuse `judge/k10_brief.md` with the k11 frame names; split C01 from the rest, as k10A/k10B did). A solver round for whatever staging still fails; at the round cap, restage or cut. Nothing that staging controls closes as known.
3. **Run the tests (`dotnet test`), then the MR** ("MR READY cinematics-1@<commit>" to main). Include one line comparing pass counts: k10 passed 1/33, against round 2's count. Carry the backlog below in the MR and here, then STOP.

**Backlog by owner (from the k10 verdicts; none is closed as known):**
- **ANIMATION (blocked-by-clip):** a prone face-down wake and push-up (C01 s2, s5); the risen tearing free (C01 s12); her pickup and turn on stepping feet with no root slide (C01 s11); the warden's rise from the water (C02 s5); the warden's guard (C02 s12, C01 s11); flask_drink plus a flask prop (C04 A sa6, cut until then).
- **CINEMATICS items 5-6 (blocked-by-art, restaged on the new art):**
  - C01: s2's pose and frost; s6a over the coals; s7's prints as the leading line; s9's rising head.
  - C02: s5, s6 and s9's framing on the warden; s7 as a profile two-shot from the west; s11's beats; s12's guard before the crane.
  - C04 A: sa2's gold on the trees; sa4's ember draining; sa5's breath plume.
  - C03: s4's steam; s6's heart light (cut if not built).
  - C04 B: sb4a's smoke.
- **TOUCH-UP (her):** waxy skin, the ear's tone, oversized glossy lips, the hairline cap edge, the braid tab's herringbone, the throat, glossy plastic armor (blown highlights, white greaves, the black gap at the pauldron top), the gray patch on the wrist at the vambrace (C01 s6a).
- **NPC art:** the warden's flat white eyes (they need blue emissive points), his bare lamp hand (it needs the gauntlet), the greatsword's edge, the drowned's identical tan shirts, Grimtunnel, the villagers.
- **ENV:** flat cream egg globes on the lamp posts (they need real flames); flat water with no shore or reflection; the ring stones; non-emissive coals; frost-grass cards; the tower top; the cartoon chest; the gallows lamp's hard light diamond; toon pines; the gray boulder (C04 A sa8); the town (C04 B).

## Start here (cinematics 3 successor, agent ac7e54435a82fff12, 18 Oct)
Scope: items 1-4 only, then the MR and STOP. (1) Loot is hidden in cinematics (888bf952). (2) A darker grade with real-source light and mist. (3) The owner's o1-o3: C01 s3, s6 and s10, plus s11. (4) Side keys on the close-ups, to the look bible's rule (docs/art/look_bible/02_skin.md item 5). Items 5-6 (blocking against the notes, the missing moments) are the backlog for after the new art, with the list in the k10 verdicts.
- k10 (staging solver a5f61d98, a0f421e7/6c8e0756): the `atmosphere` cue's tuning, a `mist` cue (FogVolume), and HeadTurn keeping a lying head's roll. Two max gate judges passed 1/33 (`tools/scratch/cin6/judge/k10A_verdict.md`, `k10B_verdict.md`). The C01 and C04 A hand-overs pass.
- k11: two max staging solvers (briefs `judge/s5a_brief.md` for C01 and `s5b_brief.md` for C02-C04 A, shared `s5_common.md`), shots `k11a*`/`k11b*`. Then one judge round (reuse `k10_brief.md`), the tests, the MR.
- Touch-up 2's finding on C01 s3: the face/neck split is the moon, shadowed by her armor (evidence `judge/tu_tone_evidence.jpg`).

## Start here (cinematics 3, PAUSED 18 Oct, clean point)
Worktree `agent-a59432fe3bfc6eb92`, branch `cinematics-1` (merged with integration incl. the neck seam fix 7b9cd519). `godot/assets` is a JUNCTION: never `git reset --hard`, `git checkout .` or bare `git stash`. Full suite 942/0/8 at 888bf952. No turns held. Nothing is merged to main yet.

**The owner's bar changed (18 Oct):** the gate is now "would this frame ship in a AAA game as it stands?" at 1:1 on the whole picture (docs/handoff/lead_brief.md); a NO fails regardless of the checklist; calibration frames `godot/.shots/o1_lying_neck_adams_apple.webp`, `o2_hunched_at_log.webp`, `o3_spin_profile.webp` (C01 s3, end of s6, s10). Art direction: "more realistic - but stylized enough to make sense on saving graphics lag", our own assets; the tutorial (Prologue, so these cinematics) launch-ready first.

**The gate audit** (`tools/scratch/cin6/judge/gateA_verdict.md` C01-C02, `gateB_verdict.md` C03-C04 B; one real-play still per shot, `godot/.shots/playc2_<cine>_s<id>_1.png`): 1 of 54 YES (the black card). Every NO also fails on other areas, so staging alone reaches no YES. The per-area lists in those files are the BACKLOG for the environment (low-poly pines, tiled water, town haze, grass rows, fog sprites), NPC/creature art (drowned, warden, risen, Grimtunnel, villagers), her armour metal (chrome hot spots), her skin shader (waxy: no SSS, no pore break-up), story props (heart, lamps), and animation (face-down wake, R1 emerge, warden rise, ready guards, slack mouth, sa5/sa7 faces).

**Items 1-4 (agreed with the coordinator) - BUILT, UNJUDGED:**
1. Loot hidden during cinematics: `BattleFx.HideLoot` (888bf952). Light shafts and the way-out band still draw.
2. Darker night grade + low mist: `atmosphere` cue takes adjustments (key, hemi, env, exposure, fog, rim, azimuth, elevation, keyColor, fogColor; `"from": "now"`), new `mist` cue (a0f421e7, 6c8e0756). C01 and C02 have their own darker night; mist on C02's river and past C01's firelight.
3. The owner's shots: C01 s3 head tipped to the coals, camera on her face's side (`HeadTurn.cs` no longer rolls a lying head upright); s6 head to bedroll then bowed to her hands, warm light on her nape, lower 32 mm (no flask: props take weapon pieces only); s10 1.0 s, cut on the lift (kneel_to_stand_snap from 0.3 s, no spin); s11 the body `look` dropped, the clip's own turn carries her, side-on at chest height.
4. Side/three-quarter keys: C01 s8, s8b, s10; C02 s4, s8; C03 s3b; C04 A sa5-sa7 (sun on her right = frame left; the note says frame right, a cheat if wanted).
Frames: `godot/.shots/k10c01_*`, `k10c02_*`, `k10c03_c03_s3b_*`, `k10c04a_c04a_sa5..7_*` (3 stills a shot). Edit scripts `tools/scratch/cin6/ed_k10_*.py`.

**Next, in order:**
- **C01 s3 face-vs-throat tone is OURS** (touch-up solver fcde25f0, evidence `survivorsunchained_inputs\scratch_touchup1\tu\tone\evidence.jpg`): the breastplate shades the moon off her throat, so the throat is fire-orange and the face moon-pale, split at the jaw. Fix: moon off for s3, or move it so the cups don't shade her throat, or the armour's moon shadow off in close-ups; also check the moon's colour (it turns skin pink-white). Likely the same in s10. `CINEDBG lamps=0,glow=0` doesn't reach C01's fire. Known misses from the solver: s3 too orange (ember 0.45 -> ~0.25, lens 100, camera 0.15 m toward her face), C02 s8 still pale. Check the mist for blockiness and s12's bright start.
- Then ONE max judge with the AAA gate first on the k10 frames + round-3 items (brief `judge/j1r3_brief.md` and `j2r3_brief.md`, written for k9: point them at k10 where reshot). Round-3 k9 frames for C01 s10-s12 and C03/C04 A are in `godot/.shots/k9c0*`; C03 s9-s11 were restaged for the sunk Grimtunnel (cameras at his eye line, hug pose, VAT v14) and are unjudged.
- Then the MR (tests: `dotnet test` in godot/tests; drop untracked `.uid`/`.import` noise; never commit the tracked `.import` changes).
- **Items 5-6, after the art lands** (restage list): blocking/framing against the notes (C01 s2, 5, 11, 12; C02 s1, 3, 7, 9, 11, 12 incl. the warden lying on and actors standing on the water, her running at the hand-off; C03 s1, 2, 8, 11, 12; C04 A sa3, sa8; C04 B sb2, 3, 5), and the promised moments (sa2 gold treetops, sa4 ember drain, sa5 breath, C03 s4 steam, s6 water off the heart, sb4a smoke): build or cut.
- Real play: `tools/scratch/cin6/playc.py NAME COUNT` runs the Prologue with every cinematic (`--cines`); playc2 played c01, c02, c03 -> c04a on the cut, c04b with no errors. The Gestures Slerp throw is fixed.

Done this session (commits f8e0d473..6c8e0756): k8 judged (j1r2/j2r2 verdicts), round-2 fixes (pacing trims c01 s6 6.4, s11 1.8; c02 s2 2.4; c03 3b 1.9; c04a A2 2.2; c04b B4a/B4b 1.7; C02 s8 lamp side fixed: place offsets are WORLD metres), the s3 solver (take_from_log for her pick-up, the crane aims from where it is, Grimtunnel sunk and hugging), `--cines`, the gate audit.

**Tools** (`tools/scratch/cin6`): `shoot.py RUNS.json` (one godot turn per batch; builds C# first), `sheet.py`, `pace.py LOG CINE...`, `jedit.py CINE edits.py`, `ed_*.py` (every edit made). Shots land in `godot/.shots/<name>_<cine>_s<shot>_<k>.png`; hand-overs in `<name>_ho_<cine>_NNN_1.png`.

From agent a7a4c20bcfd7ccfd3 (who took over from a79b6d8c81e14dc63) to a fresh cinematics production lead. Read `docs/team/README.md`, `docs/team/RESUME.md`, then this page, then `docs/team/cinematics.md`.

## The owner's quotes

- "we are striving for perfection". "cinematic, movie quality, soul, nothing generic". Story is about 40% of the early game, and the cinematics carry it.
- The hand-over (5 October): "cinematics that have our character immediately playable in the same spot should have us... in that same spot when we are playable again ... it should feel like its walking in and we just jump right into that."
- On voice: no placeholders; final voices come from ElevenLabs later.

## The brief

Shooting scripts (`docs/cinematics/shoot/<id>.md`), boards over the engine's own frames (`tools/cinematics/boards.py`), animatics (`tools/cinematics/animatic.py`), and the in-engine player (`godot/data/cinematics/*.json`, `src/Game/GameCinema.cs`, `logic/Cinema`). First milestone: C01 and the Prologue (C02 to C04) right; then C07 and C09; C10 to C13 once combat builds their fights.

## Done this session

- **The hand-over into play** (`docs/cinematics/README.md` 5a, tested by `CinemaTests` through `logic/Cinema/CineHandover.cs`):
  - a `play` cue at 0 of the last shot puts her own body where her double stands (on the cut); her later `move`s steer the player as a stick would (`Game.PlayMove`, `cineWalk`);
  - a walk still going at the end carries on into play and eases out over 0.7 s;
  - `PlayerView.Face` sets her facing; `WorldScene.StartBattle` uses it too. Every zone arrival had faced south until she moved: that was C01's snap;
  - the follow blend turns the view (slerped, ahead of the move) and aims where she really is; `FollowCamera.Snap` no longer drops 0.8 m; the HUD fades in with the bars (`GameHud.ShowPlay(on, fade)`);
  - `end.keep` leaves cast bodies in the world after the hand-over (the Warden in the ford after C03);
  - `--handoff` (with `--shot`) films 1.5 s before the end to 2.5 s after, every 0.1 s.
- **Lowford's camp, made** (title, creation, C01): `src/World/Camp.cs` (sawn pine logs; Pine Bark, credited), `Campfire.cs` (`Stones`: a made ring; `Coals`: a glowing bed, on its own render layer outside its fire's light, with a small glow light), `shaders/endgrain.gdshader`, `shaders/coals.gdshader`. The tripod and pot are gone. Flora and grass are cleared from ring fires (`ZoneView.Bare`, `grass.gdshader` `bare_at`). A fire's light sinks to its coals as its flames go (`SetFire`).
- **C01:** burns to coals; shot 5 from the west (no leg or stone across her); 6 at 35 mm, holding her face and hands; 6a focus tracks the hand; 10 focus tracks her. Staging re-rendered (`st1`); board prompts rewritten for the camp.
- **C04 A:** the last shot cranes up into play over 3 s; her walk outlasts it.
- **Combat** was told the hook asks again. They are item one of its successor's code queue (`docs/handoff/combat.md`). The Dig (C12) exists on combat's branch.

## Next, in order

1. **Animation's new clips (merged in integration):** stage C01's `letter`, `kneel_to_stand_snap`, `take_from_log`, `cup_hands`, and the remade `lie_side_wake`, `sit_back_heels`, `reach_coals`. Swords now sit at a 30 to 35° diagonal grip; check C01's shot 11 pick-up. C04's `flask_drink`: move A6's camera to her front-left (the drinking arm covers her face) and add a flask-and-cork prop.
2. **Film C04 A's hand-over again** (`ho.py c04a <name> 50`) since the turn-ahead fix. Judge every hand-over at full size; consider ending last shots nearer the game's angle.
3. **Staging and boards:** render C02, C03, C04 B staging (look at the heart's ring halo in C03); stage C01 (`boards.py c01 --stage st1`); draw the boards (C02's s3, s5, s7, s8, s11; then C01, C03, C04 A, C04 B), each at full size.
4. Recut the Prologue animatic (`animatics/prologue.txt`; C01's shot 4 is 6a).
5. The male hero through the Prologue (`prev.py ... --male`).
6. C02's and C03's line choices; C07 and C09; C10 to C13 when combat lands the marks.

## Decisions (why)

- **Her own body ends every cinematic that ends in play,** swapped in on a cut: the walk play continues is the walk the shot showed, same gait and stride, and no pose is seen to change.
- **One traveller's fire:** no tripod or pot. A bed of coals carries C01 better than flames, and nothing stands across the low cameras round her.
- **A made stone ring, not the scan:** the Poly Haven pit's few thousand faces read as cut facets at half a metre in C01's close-ups.
- **The engine's frame is the staging truth; boards are drawn over it. Cameras aim at bones. Looks are head turns.**

## Failures and why

- **A web-game ring stone survived the pit's hiding** (its box stood 0.72 m tall turned on its side; the cutoff was 0.7). Found with `--cinenear X,Z,R`, which lists every visible mesh near a point at each still.
- **The coals first lit themselves** from the sunk fire light and flared white: they now sit on a render layer their fire's lights skip.
- **The follow blend lerped a far look point** (C04 A's road toward the gate) toward her, so she dropped out of frame mid-blend: it now turns the view.
- **The first import run was killed** waiting 10 minutes for a turn: use `--wait 90` with a long background limit.

## Gotchas

- **Scratch tools** are in `<scratchpad>/cin4` and point at this worktree (change `WT`, `G`, `W` and `T` if yours differs):
  - `prev.py` builds the C# first, then renders (`--male`, `--calling`, `--clean`, `--only`, `--stills`);
  - `ho.py` films a hand-over (`--before` for an old build); `ba.py` makes a before-and-after;
  - `mkt.py` makes a scratch `_t<id>.json` with camera variants of shots (delete it before committing);
  - `jedit.py`, `bspec.py` (board specs), `sub.py` (exact substitutions in docs), `imp.py` (import new assets), `ends.py`, `times.py`, `crops.py`.
- **The worktree guard** refuses Bash with variables or heredocs near `git`, or a `cd` outside the worktree. Write scripts to the scratchpad and run them plainly; use PowerShell for `dotnet test` with env vars.
- **A new worktree needs** the `godot/assets` junction (skip-worktree), a copy of a `.godot` cache, `imp.py` for anything new, and `dotnet build` (`prev.py` and `ho.py` do it).
- **Generated `.uid` files** block merges when integration starts tracking them. Delete the untracked ones outside `godot/assets` (its contents show as untracked through the junction; leave them).
- **StoryLint reads `Num("...")` in any C# as a fact.** Read cue args with `Get(...)` in logic code.
- **Headings:** 0 faces south (+z), pi/2 east; `Rotation.Y` on a view is the same heading.

## Collaborators (roster in `docs/team/README.md`)

- **Combat** (a5115633c7006e4d4, handing off): the boss hooks and marks are its successor's first code item.
- **Animation** (handed off): the clips listed in Next 1.
- **UI design:** the title's camp changed; the HUD now fades in after a cinematic.
- **Face** (a833b7942e978d994): her head is changing; re-check the close-ups when it lands. `mouth_open` above 0.15 shows the teeth as a grin.
- **Performance:** each ring fire has one more small light and about 6k more triangles.

## Files to read first

1. `docs/team/cinematics.md`, `docs/cinematics/README.md` 5a and 11a, `docs/cinematics/shoot/README.md`, `shoot/c01.md` to `c04b.md`
2. `godot/src/Game/GameCinema.cs` (`Handover`, `Steer`, `Finish`, `PlayMove`, the follow blend) and `logic/Cinema/CineHandover.cs`
3. `godot/src/World/Camp.cs`, `Campfire.cs`, `shaders/coals.gdshader`, `shaders/endgrain.gdshader`
4. `tools/cinematics/boards.py` and `docs/cinematics/shoot/boards/*.json`
