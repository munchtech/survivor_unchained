# Judge brief: her town idles and town runs (animation 44, item 3, round 1 of 3)

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

## What's new
In a safe place (town), the reaver, arcanist and stalker now sheathe and play a town idle and a town run, as the Warden already did. Before this, they stood in their combat idles (Angry, Strutting, Crouched) in town.
- **The idles:** the same 100STYLE WiggleHips take as the Warden's (`idle_warden_town`, the owner's reference, shown as `idle_wt`), a different stretch for each calling. The arms are the Warden's, with the elbows softer.
- **Measures** (sway peak to peak / period; share of the loop clearly on one foot; elbows L/R):

  | Idle | Sway / period | One foot | Elbows L/R | Notes |
  |---|---|---|---|---|
  | warden (ref) | 15.8 cm / 2.68 s | 49% | 34-37 / 37-40 | |
  | reaver | 16.1 cm / 2.57 s | 46% | 23-27 / 28-29 | hands 46-52 mm from the hip-loop axes |
  | arcanist (wand on the belt) | 16.4 cm / 2.85 s | 49% | | right hand 82 mm from the wand |
  | stalker | 17.6 cm / 2.93 s | 55% | | hands >= 70 mm from the crossbow and daggers |

- **Shared numbers:** shoulders 1.5-2 cm above rest, as the Warden. Fingers relaxed, not fists. 0 mm into her body or outfit, foot slide under 2 mm, clean loop seams.
- **The town runs** use the Warden's judged town-run arms, with relaxed hands: run_reaver_town, run_arcanist_wand_town, run_stalker_town. 0 mm into her. Known: the wand run's right hand passes within 1 mm of the wand on her belt.
- **Weapons sheathed:** the axe on the hip loop, the gyre axes on both hips, the wand at the belt, the crossbow on the sling, the daggers at the belt back. The staff has no town idle this round, so the staff arcanist stays armed.

## Frames (1920x1080, the real game, day, facing 315)
All files are under `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-40\tools\scratch\anim40\`. Open these 15 images, and only these, once each:
- `sheets_idle1/`: these are 1:1 crops, never scaled.
  - idle_wt.png (the reference), idle_rv.png (reaver, one axe), idle_rvx.png (reaver, gyre axes), idle_arw.png (arcanist, wand), idle_stc.png (stalker, crossbow), idle_std.png (stalker, daggers). Each is the close-up at zoom 0.6, at 0, 25, 50 and 75 % of the loop, so you see the sway.
  - runs_m.png (reaver axe, reaver axes and arcanist town runs, two phases each), runs_m2.png (stalker crossbow and daggers town runs).
  - play_p.png: the play camera, cropped round her. The top row is the idles; the bottom row is the runs.
- `shots_idle1/`: full frames, the close-up at its closest zoom: wt_c.png, rv_c.png, rvx_c.png, arw_c.png, stc_c.png, std_c.png.

## Checklist (after the gate)
1. Relaxed, not anxious: weight on one hip, soft knee, shoulders down, elbows bent, hands loose, neck and head easy. Does each read as relaxed as the Warden's?
2. The sway reads as a natural weight shift across the four phases, not a mechanical rock, and the feet stay planted.
3. The hands are clear of the sheathed pieces and don't read as gripping air. The pieces sit believably: no axe that reads as held, nothing floating or through her.
4. No arm through her body, breast or outfit, and no broken wrist or pinched elbow.
5. The town runs: natural free-arm swing, hands relaxed, clear of the sheathed pieces, gait unchanged.
6. Variety: do the callings read as the same woman at ease without looking copy-pasted? (Same take, different stretch.)

## Return (under 50 lines)
1. Per sheet and frame: GATE yes/no (one line), then PASS/FAIL with tagged marks.
2. For each failure, a concrete fix a solver can make in one pass: the clip, the phase, which joint, which way and roughly how much. Or RESTAGE, with what it should be.

Ask for any measurement you need. Don't open crops.
