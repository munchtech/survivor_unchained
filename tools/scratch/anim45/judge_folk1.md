# Judge brief: armed townsfolk's town idles (animation 45, round 1)

You are a fresh judge for Survivor Unchained, an 18+ dark-fantasy action RPG. Return a written verdict (no files beyond it). Context budget: 120k. Look at each frame once, at full size; do not write measuring scripts or crop.

## The finish line (the owner)
A judge rules at the cameras the player has: the play and town camera, the close-up camera at its closest zoom, and character creation's Look camera for the face, day and night, at full size and critically. It must look perfect there. Marks that only show enlarged are closed, not logged.

## First, the whole-frame gate (for every frame, before the checklist)
*Would this frame ship in a AAA game as it stands?* Answer as a player watching at 1:1, about the whole picture: anatomy and pose, staging, how the weapon is carried. A NO fails the frame. Calibrate on the owner's three failing frames (18 Oct: "that quality is nowhere near what we are supposed to be pushing for"): C:\Users\munch\Desktop\survivorsunchained_inputs\owner_frames_18oct\ (o1 masculine throat under an upside-down camera; o2 a collapsed head-down hunch, gray neck, floating pauldron; o3 hard pale hairline, detached braid tab, waxy skin).
Tier: these are townsfolk, TIER 2: "good on a budget". A tier-2 asset passes if it looks good in the shot and runs well, not if it matches the heroine. **Scope: you rule the POSE AND MOTION (how they stand and carry the weapon).** These are the kit's old bodies and outfits (white hood on the Watchman, the kit's flat cloth), which the Marionette NPC pipeline replaces; list any look mark under "Routed (not animation)" and don't fail the pose on it.

## The owner's words on idles (19 Oct)
"I adore the idle sway back and forth you made the warden do in town its great. I love natural looks. a lot of the looks are rigid even when safe." Then: "non movement is ok - just not if its a weirdly rigid pose - its anxious". The bar is relaxed, not busy: stillness passes, tension fails (raised shoulders, locked arms, a ramrod spine, weight even on both feet, clenched fists, a weapon up as if fighting). Weight on one hip, soft knee, dropped shoulders, bent elbows.

## The frames (tools/scratch/anim45/, worktree C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-40)
The close-up camera at its closest (`--close 1`), the NPC stood in her place facing the camera, day, in the town square. `_c0/_c1/_c2` are three times across the loop (8, 13.5, 19 s of a 16.6 s weight-shift loop, so they sample different phases).
- BEFORE (shots_folk1/): watch_c0.png (the gate Watchman: the kit's shield block stance), keegan_c0.png (Keegan, a probationary knight: the kit's 2H combat guard), wenna_c0.png (Wenna the herbalist: the kit's stiff idle, short staff).
- AFTER (shots_folk2/):
  - watch_c0, watch_c1, watch_c2: the Watchman, sword only now (the shield dropped in town), the sword hanging easy in the right fist, the left arm free. watch_p.png: the play camera, the Watchman beside the heroine (she is not judged here).
  - keegan_c0, keegan_c1, keegan_c2: the zweihander (1.6 m) resting on the right shoulder, fist before the chest.
  - wenna_c0, wenna_c1, wenna_c2: the short staff hanging in the right hand.
  - folk_c0, folk_c1: an unarmed townsperson on the same weight-shift base (the feet slide was fixed under it).

## Numbers (measured, real town builds, 12-16 samples over the loop)
- Watchman (sword): blade's lowest point 327-400 mm off the ground, 35 mm clear of the body, 0 mm into it. Elbows right 40-46 deg, left 28-41 deg.
- Wenna (staff): foot 404-464 mm off the ground, 37 mm clear, 0 mm into her thigh. Elbows right 40-46, left 27-42.
- Keegan (shoulder rest): 0 mm into her, 11 mm clear; the blade 11-12 mm above the shoulder; head 80+ mm clear; right elbow 113 deg throughout (a fist before the chest with a blade on the shoulder needs it); left 27-42.
- Feet: under 1 cm travel over the loop (was 12 cm of slide before).
- The loops start at a different phase for each NPC, so a crowd doesn't sway in step.

## Checklist (per AFTER frame)
1. Whole-frame gate (above): YES/NO with one line.
2. Relaxed, not anxious: shoulders, elbows, spine, weight on one hip.
3. The carry reads as a natural way to hold that weapon at rest in a safe town (not a fight stance, not a mannequin holding a prop). Keegan especially: does the shoulder rest read as a rest, or as a sword held up stiffly?
4. Arms: hang naturally, not held out from the body like an A-pose; hands natural.
5. Better than BEFORE, clearly?

## Return
A table: frame, gate YES/NO, PASS/FAIL, one-line reason. Then per character (Watch, Keegan, Wenna, folk): PASS or FAIL, and for each FAIL the fix in concrete pose terms (which joint, which way, roughly how much: "hand 5 cm closer to the thigh", "blade laid back 30 deg"). Then "Routed (not animation)" in one or two lines. Keep the verdict under 60 lines.
