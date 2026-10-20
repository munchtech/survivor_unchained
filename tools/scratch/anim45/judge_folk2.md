# Judge brief: armed townsfolk's town idles (animation 45, round 2)

You are a fresh judge for Survivor Unchained, an 18+ dark-fantasy action RPG. Return a written verdict (no files beyond it). Context budget: 120k. Look at each frame once, at full size; do not write measuring scripts or crop.

## The finish line (the owner)
A judge rules at the cameras the player has: the play and town camera, the close-up camera at its closest zoom, and character creation's Look camera for the face, day and night, at full size and critically. It must look perfect there. Marks that only show enlarged are closed, not logged.

## First, the whole-frame gate (for every frame, before the checklist)
*Would this frame ship in a AAA game as it stands?* Answer as a player watching at 1:1, about the whole picture: anatomy and pose, staging, how the weapon is carried. A NO fails the frame. Calibrate on the owner's three failing frames (18 Oct: "that quality is nowhere near what we are supposed to be pushing for"): C:\Users\munch\Desktop\survivorsunchained_inputs\owner_frames_18oct\ (o1 masculine throat under an upside-down camera; o2 a collapsed head-down hunch, gray neck, floating pauldron; o3 hard pale hairline, detached braid tab, waxy skin).
Tier: these are townsfolk, TIER 2: "good on a budget". A tier-2 asset passes if it looks good in the shot and runs well, not if it matches the heroine. **Scope: you rule the POSE AND MOTION (how they stand and carry the weapon).** These are the kit's old bodies and outfits (white hood on the Watchman, the kit's flat cloth), which the Marionette NPC pipeline replaces; list any look mark under "Routed (not animation)" and don't fail the pose on it.

## The owner's words on idles (19 Oct)
"I adore the idle sway back and forth you made the warden do in town its great. I love natural looks. a lot of the looks are rigid even when safe." Then: "non movement is ok - just not if its a weirdly rigid pose - its anxious". The bar is relaxed, not busy: stillness passes, tension fails (raised shoulders, locked arms, a ramrod spine, weight even on both feet, clenched fists, a weapon up as if fighting). Weight on one hip, soft knee, dropped shoulders, bent elbows.

## The frames (tools/scratch/anim45/, worktree C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-40)
The close-up camera at its closest, the NPC stood in her place facing the camera, day, the town square; _c0/_c1/_c2 are three phases of the weight-shift loop. Round 1 PASSED the Watchman (sword hanging easy in the right fist, left arm free: shots_folk2/watch_c0.png is your reference for a passing carry) and the unarmed folk.
- Keegan (a probationary knight, a woman): round 1 FAILED her zweihander shoulder rest (gate NO: "reads as holding a sword up"). Restaged: she now carries a one-handed sword at ease, on the Watchman's passing stand. Frames: shots_folk4/keegan_c0.png, keegan_c1.png, keegan_c2.png. Numbers: sword lowest point 301-376 mm off the ground, 34-36 mm clear of her, 0 mm into her; elbows 27-44 deg.
- Wenna (the herbalist, short staff hanging in the right hand): round 1 FAILED minor (gate YES): arms ~10 cm out from her narrow corset waist; the free hand's fingers straight and spread; the staff head along the forearm guard. Round 2 changed only the free hand's fingers (curled more toward the little finger); the arm width and staff tilt are limited by the wrist and the staff's mount. Frames: shots_folk3/wenna_c0.png, wenna_c1.png, wenna_c2.png (round 1 for comparison: shots_folk2/wenna_c0.png).

## Checklist (per frame)
1. Whole-frame gate: YES/NO with one line.
2. Relaxed, not anxious (shoulders, elbows, spine, weight); the carry reads as a natural way to hold that weapon at rest in a safe town.
3. Arms hang naturally (not held out like an A-pose); hands natural.
4. Wenna: is what remains a mark a player would notice at this camera, or a nicety?

## Return
A table: frame, gate YES/NO, PASS/FAIL, one-line reason. Then Keegan PASS/FAIL and Wenna PASS/FAIL, each FAIL with the fix in concrete pose terms. Under 40 lines.
