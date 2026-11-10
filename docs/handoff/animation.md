# Handoff: animation

For the next animation lead (`su-lead-high`). Read `docs/team/README.md` ("Working lean", "Safety"), `RESUME.md`, `OWNER_NOTES.md` ("Animation: joints and motion to perfection"), then this page and `docs/team/animation.md`. Written by ae2a9884e3e51609c (branch `worktree-agent-ae2a9884e3e51609c`), handed off at about 320k on 7 October. **Read by section: grep, then `sed -n` the lines. Whole-file reads were this lead's largest context cost.** Earlier leads' ids are retired.

**Standing bar (the owner, 26 Oct): "effortlessly badass".** Every judge brief on her motion (armed walks especially) asks it as the whole-frame question: does she move effortlessly badass, or stiff, careful or strained?

## 000000000000000000000000000000000. MR READY (Animation 62, 3 Nov, closeout wave 2): crowd deaths + Long Cut entry SHIP (max r2); the warden town elbow CLOSED AS KNOWN (OLD ships)
**The app can now:**
- **Lay the crowd's dead as a fight, not a starburst.** 2 in 5 crumple any way; the rest fall within +-75 deg of the blow (the knockback, else away from her); every fall ends with a seeded +-30 deg twist; no two radial neighbours lie within 1.8 m (CrowdView DeathToward/Twist/SpokeNear). Each rig's fall heading is read from its bake (Vat.Laid, VatAsset.FallOff).
- **Rest corpses on the slope** (RestTilt, tilt clamp 40 deg for the Verge's 36) **and dissolve them in place** with a staggered start (DissolveOf). They used to slide 1.1 m into the floor.
- **Never draw a held pose sliding.** Shoved bodies walk by their drawn speed, a knockback plays "hit", and strikes plant their feet (up to 0.45 m).
- **Measure all of it** with `--crowd-census`: fall-vs-away bins, spread around radial, the within-20 share, radial runs, corpse ground error, held-sliding walkers. Day Verge, 250 risen: spread 23 -> 74 deg, within 20 of radial 53% -> 5%, largest radial run 59 -> 3, ground error 0.006 m, sliding walkers 11 -> ~0.04.
- **Blend her Flare press from the pose drawn at the press** (PlayerView FullHerFrom + FlareXfade 0.1 s): a whole-body clip in play is held via TimeSeek+Blend2, an upper-layer swing is held under the fade, her facing turns onto the line over the blend, and no frames are held. The greatsword shows once her hand settles (GripSettle, press + 0.1 + 2/60 s). World wrist jump at the press 0.735 -> 0.256 m; grip restore 0/0/0. `--grip-probe` logs wrists, elbows, pelvis, stance and the tip per frame; `--flare-xfade S` is a dev switch.

**Judges (max, 2 rounds, one sheet).** r1: elbow THUMB FAIL medium; crowd FAIL medium (the day "sunflower"); entry PASS-WITH-NOTES. r2 (final): crowd SHIP; entry SHIP (a 0.15 s blend is not worth it); elbow: OLD ships. Sheets: coordinator scratchpad anim62\judge\, backed up to survivorsunchained_inputs\scratch_anim62\.

**Elbow: CLOSED AS KNOWN.** Owner route A is done; route D (a new source arm) is in pass 1. Never re-run Body 20's (A) spec.
- WARDEN_TOWN_ARM's default stays "side" (byte-identical).
- Tried and kept behind the switch: "thumb" (r1: a stomach-ache hand across her belly, worse bare) and "wrist" (r2: the inner wrist on the pommel; at -80 a dead-level forearm shelf with the hand dangling; worse at -45, +45 and +80).
- Why: the sheathed sword fills her left hip, so the crest is taken by the hilt; and the pommel's top is only 0.22 m below her shoulder, so any wrist or hand on it keeps the forearm level.
- A later pass needs the hilt hung 12-15 cm lower (a weapon-mount change), then "wrist"'s elbow by her side with OLD's hand curled over the pommel cap, the forearm 30-45 deg down, and the hand never dangling.

**Closed as known, or routed:**
- The risen have one death clip, so the dead repeat one silhouette (a later crowd pass: 2-3 end poses, or a mirrored death on half of them).
- Past 160 dead, CorpseMax's RemoveAt(0) pops the oldest corpse without a dissolve.
- The shield leaving as embers at the press (VFX).
- **For VFX (main to route):** FlareFx.LongCutArt.cs:50 bakes a 4096x512 strip on the press frame, so real play hitches about 1.2 s at the press (frames of 617 and 608 ms).
- For UI: ~60 "Barrow Dust" labels on a mass kill; the "THE MAP" tip pausing the game in shots.
- Run note: `--fixed-fps 60` must come before `--`; after it, it is silently ignored.

**Cost:** ~1.2M against the 0.5M estimate. Solvers: crowd/entry 202k + 152k, elbow 180k + 147k; worker 83k; judges 157k + 143k; lead ~140k; API $0. Tests 1453/0/10.

## 00000000000000000000000000000000. MR READY (Animation 61, 2 Nov): the Long Cut clip ON after its fix round (max r2 PASS-WITH-NOTES)
**Fix round (owner funded "Yes, fund it"; cap 0.38M, ~0.37M spent: solver 145k, judge 119k, lead ~105k).** tools/anim/clips/flare_long_cut.py: held kneel f25-57 chest back 16 (pelvis-neck line 10 behind vertical), clavicles back 8, head world bow 33-36 -> 14-16, hands at sternum height, blade 14.7 off vertical (tip 5 cm nearer her), left elbow +4 cm out; two breaths (shoulders +1.1 cm) and the head lifts 16 -> 3 f48-57; coil f3-6 hips -8.5 cm and 14 cm back, stance +14 cm, torso ~8 back. Entry kept as round 1 (ENTRY 0: the solver's f1 swing key gave a 177-deg one-frame forearm turn). Must-holds unchanged or better (right blade 1.2-3.2, left <= 1.5 mm, kneel 0 mm, motion right arm into breast 5 mm was 13, armscheck worst 78 -> same entry). Measuring: tools/scratch/anim61_meas.py; logs survivorsunchained_inputs\scratch_anim61\.
**Shots** survivorsunchained_inputs\anim61\lc\ (lcday/lcnight beats, sheet_lcs*/sheet_lcr* strips; script scratch_anim61\shoot.sh): grip restore 0 mm / 0 deg / 0 mismatches in 4 runs. Night shots predate Rendering 4's crowd light.
**Judge (max, the one allowed): PASS-WITH-NOTES**, gate YES on every frame day+night, "effortlessly badass" YES; the o2 hunch and the night "C" gone; recovery and the greatsword -> sword+shield swap clean. lamps.json the_long_cut "clip" back ON; FlareClipDataTests asserts it.
**Later list (judge's notes, 1:1 only):** (1) the hold's breath is ~0.5 px at the play camera: one readable beat (a landing settle, hips -3-4 cm and back over f17-25, or a 2-3 cm chest rise); (2) the f0 entry pop: pressed mid-swing, the greatsword shows ~1 frame in the last swing's pose (a 3-4 frame blend into the coil, or form the blade once the hand is at the coil pose); (3) night: the seam's warm light should win on her underside (shares the known pale night b6 fill, VFX/Lighting).


Older blocks: history/animation.md (grep by keyword, never read whole).
