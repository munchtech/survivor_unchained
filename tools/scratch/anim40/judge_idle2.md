# Judge brief: her town idles and town runs (animation 44, item 3, round 2 of 3)

Context budget: 180k. This is read-only: your final message is the verdict. Don't write files or run scripts.

## The bar
The owner: "still AAA quality. still 'perfect', just we aren't going in 2x++ zoom anymore."
- A judge rules at the cameras the player has: the play and town camera, the close-up camera at its closest zoom, and character creation's Look camera for the face, day and night, at full size and critically. It must look perfect there.
- Judge at 1:1 only. A mark that only shows enlarged is closed.
- These are her idles, seen all the time, so judge them at full detail.

**Whole-frame gate first** (the owner, 18 Oct: "that quality is nowhere near what we are supposed to be pushing for").
- For each sheet and frame, before any checklist, ask: *would this ship in a AAA game as it stands?* Answer as a player at 1:1, about the whole picture: anatomy and pose, face and hair, light, camera, staging. A NO fails it.
- Calibrate first on the owner's three failing frames in `C:\Users\munch\Desktop\survivorsunchained_inputs\owner_frames_18oct\`.
- Tag what isn't animation's `[not-anim: area]`. Known and routed, so don't re-flag: no contact shadow at the 0.6 zoom [light]; her face paler than her chest at the close-up [skin].

**The owner on idles (19 Oct):** "I adore the idle sway back and forth you made the warden do in town its great. I love natural looks. a lot of the looks are rigid even when safe." Then: "non movement is ok - just not if its a weirdly rigid pose - its anxious."
- The bar is relaxed, not busy. Stillness is fine, but tension fails.
- Tension: raised shoulders, arms locked or held off the body, a ramrod spine, weight even on both feet with a level pelvis, clenched fists, the head held rigidly forward.
- Relaxed: weight on one hip with the other knee soft, dropped shoulders, arms hanging with bent elbows, an easy spine and neck.

## Round 1 and what changed
Round 1's verdict is `judge_idle1_verdict.md` in this folder: read it first. The stalker, the Warden reference and every body, sway and head passed. The reaver and arcanist failed on where the sheathed pieces sit.
- **Reaver (fix 1):** the hip loop moved behind her right hip at about 5 o'clock.
  - The head is at the belt, the haft runs down the back of her thigh, and the blade faces back.
  - Gyre's left axe is a true mirror, its blade back too.
  - Nearest hand, wrist or fingers to the axe head or haft top:
    - idle: 54 mm before, now 196 / 221 mm (right / left);
    - run: 160 before, now 386;
    - sprint: 159 before, now 399.
  - 0 mm into her; 3.4 mm into the outfit at worst.
- **Arcanist (fix 2):**
  - The wand is now tip down behind her right hip at about 5 o'clock, its grip at the leotard's hip line, the crystal down and back about 30 deg. The run's right hand is 336 mm from it (was 100, with the forearm 34 mm into it).
  - The idle moved to another stretch of the take, so her right wrist no longer rises: it rides her hip like the Warden's (101 cm up at 25/75 %, the Warden's 103).
  - Known: this stretch overlaps the reaver's by about 3 s (offset 2.2 s). Rule whether that reads as copy-paste; only one calling is ever on screen.
- Unchanged: the bodies, the arms (other than the arcanist's take stretch) and the town runs' swing.

## Frames (1920x1080, the real game, day, facing 315)
All files are under `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-40\tools\scratch\anim40\`. Open these 9 images, and only these, once each:
- `sheets_idle2/` (1:1 crops, never scaled):
  - idle_rv.png, idle_rvx.png, idle_arw.png: the close-up at 0.6, at 0/25/50/75 % of the loop;
  - runs_m.png: the reaver axe, reaver axes and arcanist town runs, two phases each;
  - play_p.png: the play camera cropped round her (rv, rvx, arw idles; rrv, rrvx, rarw runs).
- `shots_idle2/`: full frames, the close-up at its closest zoom: rv_c.png, rvx_c.png, arw_c.png.
- For reference only if needed (passed in r1): `sheets_idle1/idle_wt.png`.

## Checklist (after the gate)
1. The sheathed pieces read as worn, not held: no axe head or haft top at either hand, nothing beside her breast, nothing floating or through her. A piece that reads as stowed on her back or hip is right.
2. Relaxed, not anxious, as round 1 (weight on one hip, shoulders down, elbows bent, hands loose); the arcanist's right arm hangs as easily as the Warden's in all four phases.
3. The town runs: the free swing is clear of the pieces and the gait is unchanged.
4. No arm through her body, breast or outfit, and no broken wrist.

## Return (under 40 lines)
1. Per image: GATE yes/no (one line), then PASS/FAIL with tagged marks.
2. This is round 2 of a cap of 3. For each failure, either a concrete one-pass fix (the clip or socket, which way, roughly how much) or KNOWN (it passes the gate and the mark is small enough to close).

Don't open crops.
