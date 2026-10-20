# Judge brief: her attack poses (animation 43, item 2, round 2 of 3)

Context budget: 160k. Read-only: your final message is the verdict. Don't write any files.

## The bar
The owner: "still AAA quality. still 'perfect', just we aren't going in 2x++ zoom anymore." A judge rules at the cameras the player has: the play and town camera, the close-up camera at its closest zoom, and character creation's Look camera for the face, day and night, at full size and critically. It must look perfect there. Judge at 1:1 only. A mark that only shows enlarged is closed. These are her MAIN ATTACKS, seen all the time, so judge them at full detail.

**Whole-frame gate first (the owner, 18 Oct: "that quality is nowhere near what we are supposed to be pushing for").** For each frame, before any checklist, ask: *would this frame ship in a AAA game as it stands?* Answer as a player at 1:1, about the whole picture: anatomy and pose, face and hair, light, camera, staging. A NO fails the frame. Calibrate first on the owner's three failing frames in `C:\Users\munch\Desktop\survivorsunchained_inputs\owner_frames_18oct\`:
- o1: a masculine throat under an upside-down camera.
- o2: a collapsed head-down hunch, a gray neck, a floating pauldron.
- o3: a hard pale hairline, a detached braid tab, waxy skin, a jarring spin.

Tag what isn't animation's `[not-anim: area]` (outfit, hair, light, camera). It still counts against the gate, but name it exactly.

The owner on motion: "bad, unnatural movements with respect to wrists - follow through motion joint to joint, some elbow pinching or arms going through body or breast, some sliding."

## What round 1 failed, and what changed since
Round 1 judged 23 frames and passed 10.
- **Held standing frames.** Round 1: the idle's feet-together legs carried no weight under a swing. Now axe_fore, axe_heavy, axe_back, axes_left/right/heavy and cast_flick are STANCE swings:
  - While she stands, they play on her whole body: feet 1.31x shoulder width, left foot ahead, knees bent, hips into the blow.
  - While she runs, they play on her upper body over the run's legs. The `_run_` frames show this, the most common case in play.
- **The f7 finishes.** Round 1: the axe head sat on her left boot top, and fore and heavy looked alike.
  - The finish now goes forward and across: the fist is level with her left thigh, and the head is 48-55 cm clear of her leg.
  - Her right upper arm no longer passes through her breast (measured 72 -> 38 mm, back to the old contact).
  - Heavy now has knees at 34-38 deg (fore 13-20), more hinge and a lower head.
  - **heavy7_m and heavy7_run_m are KNOWN OPEN:** the axe head reads end-on, behind the haft. Don't spend the gate on them. Say in two lines what would make that finish read (grip roll, haft angle, camera side).
- **axe_fore f0.** Round 1: it read as raising a torch. It is now cocked.
- **cast_flick.** Round 1: the free hand clutched under her breast at f0, and the wand arm was locked straight. Now the free hand starts low, and the wand elbow is soft.
- **chain_strike.** Round 1: it read as setting the axe down, and it was one-handed. It is now TWO-HANDED (the owner: "if it was meant to be two-handed, then two handed").
  - It is a centred chop: the left fist is on the haft (0-2 mm) f3-f9, the head is planted f3-f11, and the axe's flat faces the camera.
  - Watch the reaver outfit around her left wrist and thigh: a measure says the wrist passes over the loincloth flap.
  - The front loincloth panel sticks out in the crouch. That is already routed to outfits: tag it `[not-anim: outfit]`.
- Not in this round: the runs' free hand (unchanged since round 1, being fixed next).

## Mid-swing frames
The swings play at 1.6x, so a mid-swing frame (axe_fore f3, axe_heavy f4, axes f3) is on screen for about 20 ms. Judge those for a broken or ugly pose, not for staging. The wind-up (f0) and the finish (f7 onward) hold longer and must read as a strong hack. f3 and f4 are also shot from a second facing (`_f45`).

## Frames (1920x1080, the real game, day, the waystation)
Folder: `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-40\tools\scratch\anim40\shots_atk4\`. Open ONLY these 23 PNGs:
- fore0_m, fore3_m, fore7_m
- heavy0_m, heavy4_m, heavy7_m
- axesl3_m, axesr3_m, axesr7_m
- chain0_m, chain3_m, chain6_m, chain9_m, chain3_p
- flick0_m, flick1_m, flick4_c, flick8_m
- fore3_f45_m, heavy4_f45_m
- fore0_run_m, fore7_run_m, heavy7_run_m, flick4_run_c

Suffixes:
- `_m`: the close-up at middle zoom 0.6 (the closest zoom crops her hands off in swings).
- `_c`: the close-up at its closest zoom.
- `_p`: the play camera.
- `_run_`: the swing over her run's legs.

The list with each frame's clip and time is `..\shots_atk4.txt` (NAME|calling|weapon|CLIP@seconds|time|zoom|facing|sex). It runs at 30 fps, so @0.1 = f3.

## Checklist (after the gate)
1. Pose: strong, athletic, intentional. The stance carries her weight. No hunch, no collapsed head.
2. The weapon reads as an axe or a wand, held, with its line right for the moment (cocked, cutting, finished). It isn't limp or dragging, and isn't through her or her legs at 1:1.
3. The free hand is purposeful (balance, guard). It is never at her groin, behind her back or clutching her shoulder, and there are no T-pose arms. In chain_strike, both hands read on the haft.
4. Wrists and elbows: no broken, wrung or pinched joint, and no arm through her breast or trunk.
5. Heavy vs fore: from the frames that show it, does the heavy blow read heavier (deeper, lower, longer)?
6. The wand never goes through the hat.

## Return (under 60 lines)
1. Per frame: GATE yes/no (one line), then PASS/FAIL with tagged marks.
2. Then FIXES for animation, most important first. Make each one concrete: the clip, the frame, which hand, which way, and roughly how much.

Ask for any measurement you need. Don't write scripts or open crops.
