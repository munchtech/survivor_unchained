# Judge brief: armed townsfolk's town idles (animation 45, round 3 (the last))

You are a fresh judge for Survivor Unchained, an 18+ dark-fantasy action RPG. Return a written verdict (no files beyond it). Context budget: 120k. Look at each frame once, at full size; do not write measuring scripts or crop.

## The finish line (the owner)
A judge rules at the cameras the player has: the play and town camera, the close-up camera at its closest zoom, and character creation's Look camera for the face, day and night, at full size and critically. It must look perfect there. Marks that only show enlarged are closed, not logged.

## First, the whole-frame gate (for every frame, before the checklist)
*Would this frame ship in a AAA game as it stands?* Answer as a player watching at 1:1, about the whole picture: anatomy and pose, staging, how the weapon is carried. A NO fails the frame. Calibrate on the owner's three failing frames (18 Oct: "that quality is nowhere near what we are supposed to be pushing for"): C:\Users\munch\Desktop\survivorsunchained_inputs\owner_frames_18oct\ (o1 masculine throat under an upside-down camera; o2 a collapsed head-down hunch, gray neck, floating pauldron; o3 hard pale hairline, detached braid tab, waxy skin).
Tier: these are townsfolk, TIER 2: "good on a budget". A tier-2 asset passes if it looks good in the shot and runs well, not if it matches the heroine. **Scope: you rule the POSE AND MOTION (how they stand and carry the weapon).** These are the kit's old bodies and outfits (white hood on the Watchman, the kit's flat cloth), which the Marionette NPC pipeline replaces; list any look mark under "Routed (not animation)" and don't fail the pose on it.

## The owner's words on idles (19 Oct)
"I adore the idle sway back and forth you made the warden do in town its great. I love natural looks. a lot of the looks are rigid even when safe." Then: "non movement is ok - just not if its a weirdly rigid pose - its anxious". The bar is relaxed, not busy: stillness passes, tension fails (raised shoulders, locked arms, a ramrod spine, weight even on both feet, clenched fists, a weapon up as if fighting). Weight on one hip, soft knee, dropped shoulders, bent elbows.

## The frames (tools/scratch/anim45/, worktree C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-40)
The close-up camera at its closest, the NPC stood in her place facing the camera, day, the town square; _c0/_c1/_c2 are three phases of the weight-shift loop. Already PASSED: the Watchman and Keegan (one-handed sword hanging easy: shots_folk4/keegan_c0.png is a passing reference) and the unarmed folk (shots_folk2/folk_c0.png: arms resting against the body).
- Wenna (the herbalist, short staff hanging in the right hand). Round 2 FAILED minor (gate YES): both arms in a stiff A-frame off her narrow corset; the free hand's index and middle straight and apart. Round 3: her free left arm and its fingers are now the capture's own (the same arm and hand the passing unarmed folk have), unlayered; the staff arm is unchanged (its wrist and the staff's mount keep it out: the staff is 42-47 mm clear of her thigh, 0 mm in; foot 405-468 mm off the ground). Left elbow 21-23 deg.
- Frames: shots_folk5/wenna_c0.png, wenna_c1.png, wenna_c2.png; round 2 for comparison: shots_folk3/wenna_c1.png.

## Checklist (per frame)
1. Whole-frame gate: YES/NO with one line.
2. Relaxed, not anxious; the A-frame broken? The free hand natural?
3. Is any remaining mark one a player would notice at this camera, or a nicety? This is the last round: say whether it ships as it stands.

## Return
A table: frame, gate YES/NO, PASS/FAIL, one-line reason. Then Wenna PASS/FAIL; if FAIL, whether it is a nicety to close as known or a mark that needs a restage (and which). Under 25 lines.
