**Animation 39 verdict: not a pass overall.** One animation fix (`xb_break_27`) and one non-animation fix that covers two frames (the arcanist hat's brim underside in `staff_idle_c` and `staff_show_c`). Everything else passes the whole-frame gate and the checklist.

How I viewed them: the image pipeline would have shrunk a whole 2008-px sheet, so I split each sheet into its two halves and looked at each half once at native 1:1. I opened the two whole frames once each, as context only. I sent the temporary halves to the Recycle Bin and wrote nothing else. For future sheets, keeping each image under about 1.15 megapixels (one 1000x1080 crop per image) would let a judge open it whole at 1:1.

**Close camera**
- `sword_idle_c`: GATE YES; PASS (1,2,6). The grip is vertical, the pommel sits on the fist, and the arm is clear of the hip.
- `viking_idle_c`: GATE YES; PASS (1,2,6). Same pose, with the viking pommel seated.
- `dag_idle_c`: GATE YES; PASS (1,2,6). Both daggers point down in closed fists, forearms in front of the hips. Her eyes read shut (see the notes).
- `staff_idle_c`: GATE NO `[not-anim: hat]`; PASS (1,2,5,6). The fist wraps the grip and the hand on the hip rests on the hip.
- `staff_show_c`: GATE NO `[not-anim: hat]`; PASS (1,2,5,6). The right elbow stays near her body, so no chicken wing. The chin-up reads proud, not strained.
- `wand_run_c180`: GATE YES; PASS (2,5,6). Arms are mid-swing, both at her sides, fists relaxed.
- `xb_idle_c0`: GATE YES; PASS (1,2,4,6). Low ready. Her head is as high as in the warden idle, so she isn't squatting.
- `xb_idle_c24`: GATE YES; PASS (1,2,4,6).
- `xb_show_12`: GATE YES; PASS (1,2,6). The crossbow is presented upright, muzzle down. The right elbow is high (optional note below).
- `xb_show_30`: GATE YES; PASS (1,2,6). The right forearm crosses in front of the upper breast with a clean edge, and the left fingers are under the stock.
- `xb_show_60`: GATE YES; PASS (1,2,3,6). Reads as a shooter sighting: right elbow up, left elbow tucked under the fore-stock, head down to the stock.
- `xb_show_80`: GATE YES; PASS (1,2,6).

**Play camera**
- `sword_fore_p90`: GATE YES; PASS (1,6). The blade is clear of her head.
- `dag_idle_p90`: GATE YES; PASS (1,4,6).
- `staff_idle_p90`: GATE YES; PASS (5,6). The staff is upright beside her, but at 120 px I can't confirm its foot is on the ground.
- `staff_flare_p90`: GATE YES; PASS (5,6). A low lunging slam; the hat hides most of her, which is the design.
- `wand_run_p180_0`: GATE YES; PASS (5,6).
- `wand_run_p180_17`: GATE YES; PASS (5,6).
- `wand_sprint_p180_10`: GATE YES; PASS (5,6).
- `wand_sprint_p180_33`: GATE YES; PASS (5,6).
- `xb_run_p180`: GATE YES; PASS (1,6). The crossbow is carried level at the right hip, at low ready.
- `xb_run_p90`: GATE YES; PASS (1,6). The forward lean reads as a run, not a crouch.
- `xb_sprint_p180`: GATE YES; PASS (1,6).
- `xb_idle_p90`: GATE YES; PASS (1,4,6). Upright with soft knees.
- `xb_idle_p0`: GATE YES; PASS (1,4,6).
- `xb_idle_town`: GATE YES; PASS (6).
- `chain_43`: GATE YES; PASS (5,6).
- `chain_48`: GATE YES; PASS (5,6).
- `chain_53`: GATE YES; PASS (5,6).
- `chain_48f`: GATE YES; PASS (5,6). The shield arm is out to the side, clear of her body.
- `xb_break_19`: GATE YES; PASS (4).
- `xb_break_21`: GATE YES; PASS (4). On the way down.
- `xb_break_27`: GATE NO; FAIL (4).
- `xb_break_34`: GATE YES; PASS (4).
- `xb_break_36`: GATE YES; PASS (4).
- `xb_stop_03`: GATE YES; PASS (1,6).
- `xb_shoot_00`: GATE YES; PASS (1,3,6).
- `xb_shoot_00f`: GATE YES; PASS (1,3,6).
- `xb_shoot_02`: GATE YES; PASS (1,3,6).
- `xb_shoot_08`: GATE YES; PASS (1,3,6).
- `xb_shoot_08f`: GATE YES; PASS (1,3,6).
- `xb_shoot_13`: GATE YES; PASS (1,3,6).
- `xb_shoot_18`: GATE YES; PASS (1,6).
- `whole_xb_shoot_08`: GATE YES.
- `whole_xb_show_30`: GATE YES.

**The failures**

1. **`xb_break_27`** (animation, the most visible fault). At the bottom of the idle break she drops into a full squat. Her hips go back behind her heels, her back rounds, her torso folds close to flat, and her head ends up about level with her hips. From the high camera that is a butt-out squat in a thong-cut outfit: the silhouette the owner called "crouching like they have to go to the bathroom," plus the head-down hunch from his o2 frame. The break plays every time she stands still with the crossbow, so players will see it a lot. I judged this from one 120-px frame, but the silhouette is clear.
   - **Fix:** replace the heel-sit with a one-knee kneel. Put the right knee on the ground and plant the left foot ahead with the shin near vertical. Keep the pelvis under the shoulders and the spine within 15–20° of upright (it reads near flat now). Lift the head 20–30° so she looks out, scanning. Rest the crossbow on its stirrup ahead of her, or across the left thigh, with the right fist on the grip. Let the left hand come off the stock to rest on the left knee, which gives the hand-off a reason.
   - **Fallback if the heel-sit stays:** chest up to within 30° of upright, hips forward 8–10 cm under the shoulders, head up about 20°, forearms on the thighs. Hold the bottom for at least 1 s so it reads as a rest, not a squat repetition.
   - Re-shoot 2.4–3.0 s at the play camera from the side and the front, plus one close frame. The left hand leaving and returning to the stock can't be judged at 120 px.

2. **`staff_show_c` and `staff_idle_c`** `[not-anim: hat material/lighting]`. The brim's underside renders flat black with no detail, while her face right under it is fully lit. In the show pose it becomes a large black disc behind her face; in the idle it's a black band. It reads as a cut-out, not shade.
   - **Route** to the outfit or rendering lead: give the underside the felt color with correctly facing normals, and let light bounced off the ground reach it. The underside should read dark navy with visible weave. The clip itself needs nothing; the show's head tilt is fine.

**Minor notes (not failures)**
- **`dag_idle_c`:** her eyes read shut. If the capture caught a blink, fine. If the idle holds a low gaze, lift the head or eyes about 10° so the close camera meets her eyes.
- **`xb_show_12`:** the right elbow sits above the fist (upper arm out about 60°) while that hand holds the upright stock at breast height, which reads a little posed. Optional: lower the right elbow about 20° over f8–f18.
- **`staff_idle_p90`:** measuring the staff tip's height above the ground in `idle_arcanist` would close the planted question (it should be within 1–2 cm).
- **`flare_burns_twice`:** the known one-frame left-hand spins don't show in the frame where the staff strikes the ground or at the play camera. They would flick at the close camera; low priority.
- **Coverage gaps:** the town run and the close-camera wand sprint named in the brief aren't on the sheets (`xb_idle_town` is).
- **Calibration against o1–o3:** none of the close frames shows an Adam's apple, gray neck, hard hairline, floating pauldron or detached braid.

**Fixes, ordered by how visible they are:**
1. `xb_break_27`: restage the sit (animation).
2. `staff_show_c` and `staff_idle_c`: the brim underside (`[not-anim: hat]`); one fix closes both.

Nothing else blocks. The crossbow aim, in both the shoot and the show, reads two-handed and capable at both cameras. At 1:1 I saw no arm through her body or breasts, no broken wrists, and no weapon through geometry.