# PoE2 movement reference from public footage

Status: PASS 2 DONE, STILL PARTIAL (21 Nov 2026). Task 2 of GAME_PLAN. Measured, not remembered. Nothing here says how PoE2 is built inside.
Owner, 21 Nov: "Path of Exile 2 is the specific movement benchmark. Treat matching its observable movement design and responsiveness as a serious target, not a loose inspiration." Footage: "Use public footage".
State file with every raw number: `survivorsunchained_inputs/scratch_devplan/task2_poe2_ref/STATE.md`.

## Bottom line

- Usable (two clips agree within 2 frames, about 0.035 s): shot 1 start, shot 2 stop, camera lock. Caveats in the table: coarse pixel steps, and the second clip does not show which input device was used.
- One dodge roll was found and measured in one clip (JMs9JutejRU, 0.5 era): single source, medium-low. It gives shot 8 only. Shots 9 and 10 were not found.
- Shots 3, 4, 5, 6, 7, 10, 12 have nothing readable in public footage I could open. Shot 9 has no clean case. See the final list.
- Method lesson: the Gobbo clip (mX8XgeX0VYk) duplicates about 1 frame in 3 during motion (read it in seconds). JMs9JutejRU duplicates about 1 in 20 (3 in 70 ticks, 3 in 75), so its ticks are close to real ticks. kafVcaU7S0w showed no duplicates in a 60-tick check.
- Most public gameplay is dark, commentary-free walkthrough with no key overlay, so you cannot tell WASD from click-to-move by looking. Only mX8XgeX0VYk shows keys.

## Method (so the next pass can repeat it)

- Built-in browser, quality forced to 1080p60, checked with the player's stats (`1920x1080@60`).
- A script seeks the video element to each 1/60 s tick (waiting for `seeked`, with a 6 s fallback for far seeks) and draws the frame to a canvas. Contact sheets (many frames, one screenshot) for looking; block matching (SAD, plus or minus 14 px at 480x270, a 100x100 block on the ground left of her) for scroll per tick. An exact-duplicate tick is reported as DUP.
- Because the camera is locked to her, ground scroll is her world speed in screen pixels, not meters. Unit: her on-screen height, about 0.08 to 0.10 of frame height (about 90 px at 1080), eyeballed.
- Far seeks in a long video are slow (0.5 to 1 s each). Run work as a background job and poll.

## Clips

| id | what | upload | 60 fps | WASD | class, weapon | patch | good for |
|---|---|---|---|---|---|---|---|
| mX8XgeX0VYk | Gobbo, walk-cancel demo, 1:26 | 14 Jan 2026 | stream yes; about 1 in 3 ticks duplicated in motion | yes: key overlay box shows A and D | Warrior, mace | unconfirmed (UI not read; likely 0.4.x) | the only clip with inputs on screen; shot 11; camera |
| JMs9JutejRU | "POE 2 - Master the Controls", voiced explainer with real gameplay, 41:42 | 13 Nov 2026 | stream yes; 3 in 70 and 3 in 75 ticks duplicated | by title and description (WASD, mouse aim); no key overlay, so not confirmed from the picture | armored melee, small figure, weapon not identified | 0.5 era (date only; no patch text read) | shots 1, 2, 8; camera. Chapters (s): dodge roll 1644, decel and facing 1046, attack and move rhythm 768, sprint 2127 |
| kafVcaU7S0w | CaptainCigar Warrior Act 1-4, no commentary, 11 h 59 min | 3 Apr 2026 | stream yes; no duplicates in 60 ticks at 110.0 s | not shown; unknown | pale melee-looking character | unconfirmed | opened, dark scenes, no key overlay, no roll seen; one 60-tick check only |
| jpPo8H9zEI8 | KG Evil-Ash walkthrough, titled 4K 60FPS Steam Free Weekend, 4 h 25 min | 1 Sep 2025 | stream yes (not frame-checked) | not shown; unknown | not identified | 0.3 era | opened for metadata and a 12-frame sheet only; not measured |
| mU7mLtj7nxU | official Mercenary walkthrough, 12:23 | older (about 2 yr) | not opened | not opened | Mercenary | old | not opened: dropped for budget after better clips appeared |
| 0sHeOGW9lt4 | MrLlamaSC WASD breakdown, 9:35 | 21 Mar 2024 | stream yes, not checked | by title | n/a | pre-launch | design facts only; rejected for numbers |
| jefJa9gL8Lo | DarkLight Count Geonor fight | 8 Dec 2024 | stream yes, not checked | unknown | caster-looking | 0.1 era | rejected for numbers |
| e_7EwDqhMWI | Massify Warrior 0.5 guide, 22:55 | 25 Jun 2026 | stream yes, not checked | unknown | Warrior | 0.5 (title) | effects bury her; rejected |
| ElSRiYUv7yQ | Path of WASD (third-party WASD tool) demo | 14 Jul 2025 | 30 fps only | tool, not stock | n/a | n/a | rejected: 30 fps and a mod |
| _2JMALgV2q0 | "How to change Dodge Roll Effect", 0:12 | 7 Nov 2026 | 30 fps only | n/a | n/a | n/a | rejected: 30 fps, a menu |
| SFd0mGsKFUU | "Why you can't dodge roll", 1:37 | 11 Sep 2026 | stream yes | n/a | n/a | n/a | rejected: settings talk with face cam, no movement play |

## The 12 shots

Rule: usable only when two clips agree within 2 frames (about 0.035 s). Times are clip seconds. Scroll numbers are pixels at 480 wide (multiply by 4 for 1920 wide).

| # | shot | reading | clip, time | status, confidence and why |
|---|---|---|---|---|
| 1 | Start: rest to full run | Full scroll within 1 to 3 ticks (about 0.02 to 0.05 s) of the first moving tick; no ramp visible. JMs9: 1,0 / 0,0 / 1,1 / 2,1 / 1,1 / 1,1 / 2,1 px per tick from 1888.0. mX8: 1,0,3,3,2 px from 00:17.60. | JMs9JutejRU 00:31:28.0 (1888.0 s); mX8XgeX0VYk 00:17.60 | USABLE, medium-low: two clips agree within 2 ticks. Caveats: steps are 1 px at 480 wide; mX8 was an attack-cancel not a true rest; JMs9's input device is not shown. |
| 2 | Stop: full run to rest | Scroll goes from run speed to zero in 2 to 3 ticks, no slide after. JMs9: 1,0 / 1,1 / 1,0 / 1,1 / 0,0 / 0,0 (about 3 ticks) at 1887.97. mX8: 3,1,0 (2 ticks) at 00:15.99. | JMs9JutejRU 00:31:28.0; mX8XgeX0VYk 00:15.99 | USABLE, medium-low: agree within 1 tick. Same caveats as shot 1. This is camera plus body together. |
| 3 | Reversal | Not found. | none | unreadable |
| 4 | Quarter turn | Not found. | none | unreadable |
| 5 | Strafe | No speed ratio read. mX8 key overlay shows A and D held while swinging, fits strafing. | mX8XgeX0VYk | unreadable for speed |
| 6 | Backpedal | Not found. | none | unreadable |
| 7 | Circle around a fixed aim point | Not found. | none | unreadable |
| 8 | Dodge roll from rest | Direction: along the screen direction of travel (toward lower-left to upper-right on screen; which key was held is not shown). Onset: scroll steps from zero straight to about 5.6 px per tick at the first moving tick (no ramp). Speed per tick (px at 480): 4,4,7,4,8,4,4,8,dup,7,7,3,7,3,3,6,2,3,2,2,3,1,1, then about 1.4 (run speed). Curled roll pose seen 1716.00 to 1716.15, upright by 1716.30. Length: about 0.45 s (about 27 ticks) from onset to run speed. Distance: about 93 px across by about 65 down at 480 wide, path about 113 px at 480 wide, about 450 px at 1920 wide, about 4.7 of her heights. Peak about 8 px per tick at 480 wide, about 5 to 6 times the run speed seen at 1888 s. | JMs9JutejRU onset 1715.75 s (00:28:35.75) | SINGLE SOURCE, low-medium: one clip; identified as a roll by pose and by being in the dodge-roll chapter, not by an input; distance in her heights uses an eyeballed height; the first ticks may include a duplicate. |
| 9 | Roll at full run, and out | Not clean. At 1860.7 s in JMs9 scroll rises from about 1.4 to 3 to 6 px per tick for about 20 ticks and settles back to about 1.4, but the narration there is about tapping against holding the dodge key (sprint), and the pose was not seen. | JMs9JutejRU 1860.7 s | unreadable: roll not identified |
| 10 | Roll across or against the aim | Not found. | none | unreadable: the cursor is not visible in the clips, so follow-the-cursor against follow-the-keys cannot be told |
| 11 | Attack while moving | In the Gobbo clip she swings repeatedly with A or D held and the camera keeps her at the same screen spot. Ground scroll is zero while swinging (ticks 25 to 45 and 150 to 172 from 00:14.70) and resumes when the swing ends. Read: the swing is planted, and movement returns at the animation cancel. | mX8XgeX0VYk, 00:15.12 to 00:15.45 and 00:17.60 | SINGLE SOURCE, low: one clip; only some skills shown |
| 12 | Heavy hit while moving | Not found. | none | unreadable |

Steady walk speed (a side reading, not one of the 12), unit her heights per second: mX8 about 436 px per s at 1920 wide (about 3.7 heights per s at 0.11 frame height). JMs9 about 336 px per s at 1920 wide (about 3.5 heights per s at 0.09). They differ because the camera zoom, character and any speed modifiers are different. Not a usable number; the order of magnitude is 3 to 4 heights per second. Low confidence.

## Our targets where footage gave no reading (inferences, 22 November)

None of these is a PoE2 measurement. Each is derived from the readings above (start 1 to 3 ticks, stop 2 to 3 ticks with no slide, camera locked to her) or from the owner's decision 3, and is marked so. A real reading replaces it when one exists.

| # | shot | our target | derived from | kind |
|---|---|---|---|---|
| 3 | Reversal | Full speed the new way within 6 ticks of the key change; under 0.1 m past the turn point; she stays mid-frame | stop (2 to 3) plus start (1 to 3) | inference |
| 4 | Quarter turn | Full speed on the new heading within 3 to 6 ticks; under 0.1 m of overshoot along the old heading; the camera never keeps the old way | start and stop readings; the locked camera | inference |
| 5, 6 | Strafe, backpedal | Same start and stop ticks as shot 1; facing holds the aim. Speed against forward: unknown, ours stays 1.00x | shot 1 and 2 readings | inference; the speed is unknown |
| 7 | Circle the aim | Constant speed; facing tracks the aim with no flip; she stays mid-frame | the locked camera | inference |
| 9 | Roll at a run, and out | The roll of shot 8; out of it at run speed with no dip, along the held keys | shot 8 (single clip) | inference on a single clip |
| 10 | Roll across or against the aim | The roll goes where the keys or the stick are held; nothing held, to the cursor; on a stick, her facing. After it, under 0.1 m off the keys' line and never under run speed | the owner's decision 3 (21 November), not footage | decision |
| 12 | Heavy hit while moving | 0 m of travel while her pose is held; at full speed again within 3 ticks of the hold's end | criterion D1; shot 1 | inference |

Where ours stands against these and against the usable readings (harness takes at a fixed 60 per second, old against `--move-new`): `tools/motion/move_matrix.py` runs the takes and writes the tables; the numbers of 22 November are in the lane's state file (`survivorsunchained_inputs/scratch_move/STATE.md`).

## Camera

- Locked to her: usable (two clips). In mX8XgeX0VYk she stays at about 0.49 of frame width and 0.39 of frame height through walking and swinging. In JMs9JutejRU she is at about the middle of the frame (about 0.5 across, 0.4 to 0.45 down) at rest, during the run and during the roll. No lead or trail on start, stop or the roll burst was visible: the scroll starts and stops with her, within a tick at the pixel step I could resolve.
- Pitch: high three-quarter view, about 55 to 60 degrees down, by eye from both clips. Low confidence.
- Her height: about 0.08 to 0.11 of frame height (the figure is small), with the interface bar at the bottom taking about 0.09. Eyeballed.
- In JMs9 the dodge burst moves the camera with her, and the picture jumps across a third of the frame in about 10 ticks. No camera lag on the roll was resolved.
- 0.5 build guide (e_7EwDqhMWI, 00:56 to 01:01): the view is closer and more cluttered; her share of frame height was not readable under the effects.

## What footage could not show

- Input delay: no clip shows inputs on the same clock as the picture. The key box in mX8XgeX0VYk is drawn by the recorder and its timing against the picture was not tested. No delay claimed.
- Which input device made the movement in JMs9JutejRU and kafVcaU7S0w (WASD or click-to-move): not visible.
- Exact speeds in game units, turn rate, buffer and cancel rules, whether the roll can be cancelled or buffered, and any invulnerability: not visible; not claimed.
- Whether the roll follows the cursor or the keys: the cursor is not shown.
- Frame counts from mX8XgeX0VYk are shaky (duplicate ticks), and YouTube may add or drop frames on encode in any clip. Steps in my scroll numbers are 1 px at 480 wide, which is coarse next to a 1 to 2 frame claim.
- Patch of every clip: no interface patch number was read.
- Camera behaviour in a fast reversal: not reached.

## Needs the owner's own recording

Public footage did not give these after both passes. Record on open ground, 1080p60 or better, with a key overlay and the mouse cursor visible, no attack running unless stated:

- 3 Reversal (full run, then the opposite direction)
- 4 Quarter turn (full run, then 90 degrees)
- 5 Strafe speed against forward run (aim held on a fixed point)
- 6 Backpedal speed against forward run
- 7 Circle around a fixed aim point
- 9 Roll at full run and out again (roll length, time to run speed, any pause)
- 10 Roll across or against the aim (follows keys or cursor)
- 12 Heavy hit while moving (freeze frames, slide)
- Also, to firm up: 8 (a second roll from rest), 11 (a second clip of attack while moving), and the input-to-motion delay for all of them.
