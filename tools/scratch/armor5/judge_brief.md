# Armor 5 judge: her weapons sheathed at their sockets, and a new sword in her hand

Context budget: 120k

You are a fresh max judge for the armor 5 lead. Return a written verdict as your final message. Do not message the coordinator. Read only the frames named here and the three calibration frames. Don't onboard into the repo.

## The owner's bar
- "That quality is nowhere near what we are supposed to be pushing for" (18 Oct, on frames earlier judges passed).
- "Still AAA quality, still 'perfect', just we aren't going in 2x++ zoom anymore."

Judge at 1:1 only: each frame is the game's own camera at 1920x1080. A mark that only shows when enlarged doesn't count. She is tier 1 (full detail): her body, her weapons, her motion.

## Calibrate first
Look at the owner's three failing frames in `C:\Users\munch\Desktop\survivorsunchained_inputs\owner_frames_18oct\`:
- a masculine throat under an upside-down camera
- a collapsed hunch with a gray neck and a floating pauldron
- a hard pale hairline, a detached braid tab and waxy skin

That is what NO looks like.

## Frames
All are in `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-5\godot\.shots\armor5\`. Names: `_p` = play camera, `_c` = close-up at its closest, `s90`/`s270`/`back`/`front` = which side of her faces the camera. Each pose is held at one moment of a clip.
- **Warden in town, sheathed** (in the game today): her one-handed sword at her left hip in a scabbard, hilt forward and up; her round shield across her back.
  - Play camera: `w_idle_front_p`, `w_idle_s90_p`, `w_idle_s270_p`, `w_idle_back_p`, `w_run10_s90_p`, `w_run10_s270_p`, `w_sprint0_s90_p`, `w_sprint0_s270_p`, `w_sprint20_s90_p`, `w_stop9_back_p`.
  - Close-up: `w_idle_c`, `w_run_c`.
- **Oathbrand**, a new one-handed sword, drawn in her right hand: `oath_idle_c`, `oath_idle_p`, `oath_fore_p` (a forehand swing).
- **Other callings' sockets, a PREVIEW.** These callings don't sheathe in the game yet, so these frames borrow the warden's town clips. Judge where the piece sits on her body. Do not judge the pose.
  - The reaver's two axes, head up at each hip: `r_axes_idle_p`, `r_axes_sprint_p`.
  - The stalker's daggers at the back of the belt and her crossbow slung across her back: `s_kit_back_p`, `s_kit_run_p`.
  - The arcanist's wand tucked in her belt, crystal up: `a_wand_idle_p`.

## The numbers (measured; don't re-measure)
On the town clips, every sheathed piece sits 0-0.6 mm into her body skin.

Known arm crossings:
- Her left forearm passes 38-40 mm through the sword's hilt in the town sprint (`w_sprint0`, `w_sprint20`), and about 28 mm through it in the town run. No socket fixes it; an animation fix is proposed (her left hand riding the hilt).
- Her left forearm passes about 5 mm into the shield's rim in the run.
- The wand's crystal passes 20-27 mm into her right upper arm in the borrowed sprint.

Oathbrand's grip passes the numeric fist check on all 13 frames, the same as the shipped sword.

## Question 1, per frame, before anything else
Would this frame ship in a AAA game as it stands? Answer as a player watching at 1:1, about the whole picture: her anatomy and pose, face and hair, lighting, camera, staging, and the weapons. A NO fails the frame, whatever the checklist says.

## Question 2, the checklist, per frame
1. Each piece reads as worn: snug on her, not floating off her, not sunk into her skin or clothes, at a believable angle, and its strap or scabbard reads.
2. In the run and sprint frames: does any arm visibly pass through a piece at 1:1? Say which frames, and whether a player would notice it in motion.
3. Oathbrand in her fist: fingers wrap the grip with no visible gap and no fingers through it, and the blade's line and size read right in her hand.
4. Preview frames: is each socket a good place for its piece (it reads, it's clear of her limbs in the frame shown)?

## Not yours (routed elsewhere; don't rule on them)
Blue steel in firelight, the top's strap over the pauldron, the etched band's size, the tray-flat shield in swings, shrugging shoulders, the male hero, her face and hair beyond the whole-frame gate.

## Verdict (final message, under 50 lines)
- One line per frame: PASS or FAIL, and why.
- Then the fixes, ranked, each naming the frame and what to change: the socket (a place, an angle) or animation (which arm, which clip).
- Then one line overall: do the sheathed weapons and Oathbrand meet the bar?
