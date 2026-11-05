# Motion bible: her, casual badassery and effortless sexiness

A1 Stage A (motion director, 5 Nov 2026). Every clip of hers on the new rig (P1's 124-bone skeleton) is authored, built and checked against these rules. The boards are in `survivorsunchained_inputs\motion_a1\boards\`, one per section (named in brackets). The clip-by-clip plan and the pipeline are in `MOTION_PLAN.md`.

**The owner's words.** "casual badassery and sexyness"; "good time to make more casual badassery and effortless sexyness"; "upgrading by redoing if needed and not just trying to patch whats already there". The standing bar (26 Oct) is "effortlessly badass". On idles (19-20 Oct): "I adore the idle sway back and forth you made the warden do in town"; "non movement is ok - just not if its a weirdly rigid pose - its anxious"; each calling has its own idle. From 26 Oct: "nobody stands like that". From 18 Oct: sex appeal drives, "tho not at the cost of looking bad".

**Derivation key** (PIPELINE.md rule 4). Each rule says what it comes from:
- **(a)** the game's need, with a number taken from the game;
- **(b)** a named reference;
- **(c)** inherited, with the file, lead or date named.

Numbers are at 60 fps. "f" means a frame.

## 0. The one rule

**She never works harder than the moment needs.** The badassery is economy: little motion, all of it decisive, then stillness. The sexiness is ease: her weight is committed, her joints are soft and her hips lead. Tension reads as fear (the owner's "anxious"), and effort reads as weakness. Every judge asks one whole-frame question: "does she move effortlessly badass, or stiff, careful or strained?" (c: the owner, 26 Oct).

## 1. Scale: what each camera can see

| Camera | Her size | 1 px is | What reads there |
|---|---|---|---|
| Play (arena, roads) | 40-60 px tall | 2.8-4.3 cm (3.4 at 50 px) | the silhouette, the weapon, rhythm, and the negative space between her arms and body |
| Town (close zoom) | 300-500 px | 0.3-0.6 cm | weight, sway, hips, hands, the glance |
| Close-up / Look | head and torso fill the frame | under 0.2 cm | breath, fingers, eyes; the face stays still and the body talks |

- **R1.1 A beat that must read at play moves the silhouette at least 2 px:** 7 cm at a hand, the weapon tip or the head, or 5 deg on the whole body line. (a) Her height (1.70 m) at the play camera's 40-60 px. The Long Cut judge saw a 0.5 px breath as no beat at all (c: Animation 61).
- **R1.2 The weapon carries 2-3x the body's motion in every action**, because at play it is the part that reads (a: the same arithmetic; b: League of Legends and Hades build their top-down attacks on the weapon's arc).
- **R1.3 At play, an attack's anticipation silhouette differs from the ready silhouette by at least 4 px** (the weapon moves 15 cm or more), and the contact pose is the longest line in the motion. (b) Fighting-game readability: Street Fighter 6's startup poses are made to be read at a glance.

## 2. Rest: the line of action and the S-curve [boards I1-I4]

- **R2.1 Contrapposto, always at rest:**
  - At least 75% of her weight is on one leg.
  - That hip sits 4-7 cm out past the ankle line, and the pelvis tilts 5-9 deg with the free side down.
  - The shoulders counter-tilt 2-5 deg the other way, so the flank on the standing side is compressed and the free side is long.
  - The free knee is bent 10-20 deg, and the free foot is 5-15 cm forward and turned out 15-30 deg.
  - The eyes stay level: head roll is within 5 deg, or 5-10 deg as a deliberate attitude.

  Derivation: (b) Polykleitos' Doryphoros (the chiasmus of hips against shoulders) and Praxiteles' Aphrodite of Knidos (the S-curve); (c) the owner's G1 key-art pick (weight on the right, hip out, chin up) and his 19 Oct clarification "weight on one hip, soft knee, dropped shoulders, bent elbows".
- **R2.2 The line of action.** Every key pose has one C or S curve from the planted foot through the pelvis to the head, at least 8 deg off straight at rest and at least 15 deg in action keys. Measured as the bend at the pelvis of the ankle-pelvis-head polyline in the camera plane. (b) Preston Blair's and Walt Stanchfield's line of action (Drawn to Life).
- **R2.3 The arms break the silhouette.** At rest at least one arm leaves a gap of 5 cm or more from the torso (1.5 px at play): a hand on the hip, a thumb in the belt, a forearm on a prop. Arms hanging straight against her sides are forbidden at rest. (a) R1.1. (c) the owner's 26 Oct "nobody stands like that" (arms out, fists clenched, square stance).

## 3. Tension fails, ease passes [all boards]

R3.1 These are the ranges at rest, in idles, walks and the fight-ready pose:

| Joint | Ease (passes) | Tension (fails) |
|---|---|---|
| Clavicles | at rest or 0-4 deg down | raised (a shrug) |
| Scapulae | 3-6 deg back (the chest open) | protracted (a hunch) |
| Elbows | 10-35 deg bent | locked straight, or a 90 deg "chicken wing" |
| Wrists | within 15 deg of neutral, unless gripping | cocked (the posed salute) |
| Fingers | a relaxed curl that increases from index to pinky (about 20/30/40/50 deg at the knuckle) | a fist without a grip, or splayed |
| Standing knee | 3-8 deg | 0 deg (locked) |
| Spine | lumbar 5-10 deg past neutral extension, the pelvis slightly forward | ramrod straight, or slumped |

Derivation: (c) the owner, 19 Oct: "stillness passes, tension fails (raised shoulders, locked arms, a ramrod spine, weight even on both feet, clenched fists)"; (b) the relaxed-hand curl of anatomy references (the hand's resting cascade).

## 4. Weight: where it sits and when it shifts [I1-I4]

- **R4.1 The centre of mass reaches the standing foot before the other foot lifts.** No float, no step taken from a centred weight. (b) Biomechanics: the COM shift precedes the step (anticipatory postural adjustment).
- **R4.2 Every idle shifts her weight, and the pelvis travels at least 7 cm side to side at some point in its loop (2 px at play).** Measured on today's clips (c: inventory worker, `docs/design/motion/measures.json`):
  - The Warden's town sway, the one the owner loves: 15.8 cm of pelvis travel, 7 deg of roll, 12 deg of yaw, the head 6.7 cm, one cycle per 2.67 s.
  - Every other idle: under 2 cm (under 0.6 px). That is why they read as frozen.

  So the band runs from 7 cm up to the Warden's 16 cm, and §11 sets each calling's place in it.
- **R4.3 A shift eases in and out over 0.8-1.6 s, then settles with one overshoot of 1-2 cm past the target and back over 0.3-0.5 s.** (b) The Illusion of Life's slow-in/slow-out and follow-through; (c) the Warden sway's period.

## 5. Breath and life [I1-I4]

- **R5.1 Breath:**
  - At rest, 3.6-4.5 s per breath (13-16 a minute). After a fight (catch_breath), 2.0-2.5 s, easing back to rest over 10-20 s.
  - The chest rises 0.6-1.2 cm and the shoulders 0.3-0.6 cm.

  The breath reads only at the close-up and in town; at play the sway carries her life (R1.1). (b) Adult resting breathing runs 12-20 a minute.
- **R5.2 Loop length and breaks:**
  - An idle loop holds whole numbers of sway cycles and breaths (the Warden's 5.33 s holds two 2.67 s sways). Other callings loop at 6-8 s.
  - Each calling has 2-3 idle breaks of its own (a stretch, a look, a prop beat), drawn at random every 10-20 s and never twice in a row.
  - Fight idles break only after 6 s without input.

  (b) League of Legends' idle-break practice; (c) the owner's natural-idles notes (19-20 Oct).
- **R5.3 Stillness is allowed; rigidity is not.** A held moment of up to 2 s passes if the pose itself is easy (§3). (c) The owner: "non movement is ok".

## 6. Overlap, settle and overshoot [all boards]

- **R6.1 The chain delays at every start and stop:**
  - From the hips: spine +2 f, chest +3 f, neck and head +4-6 f.
  - Down the arm: upper arm +3 f, forearm +5 f, hand +6-8 f.

  The overshoot is 10-20% of the move, one bounce, and it is gone by the second cycle. (b) The Illusion of Life (follow-through and overlapping action); (c) the owner, 6 Oct: "follow through motion joint to joint".
- **R6.2 Secondary motion is runtime springs on the new bones**, with parameters per kit. A clip never keys these:

| Part (P1 bones) | Frequency | Damping ratio | Lag | Amplitude cap |
|---|---|---|---|---|
| Breasts (breast, breast_tip), cloth top | 2.5-3.5 Hz | 0.30-0.45 | 3-5 f behind the chest | 2.5 cm vertical in the run |
| Breasts under plate or rigid cups | 4-6 Hz | 0.5-0.6 | 2-3 f | 1 cm |
| Glutes | 4-6 Hz | 0.5 | 2-3 f | 1 cm at heel strike |
| Braid (its own chain) | 0.6-0.9 Hz | 0.15-0.25 | follows the head | settles in 2 swings (1.5-2.5 s); never passes through her (capsules on her back, hips and shoulders) |
| Skirts and pteruges | 1.5-2.5 Hz | 0.4-0.6 | 2-4 f behind the hips | never past mid-thigh in the run |

  Derivation: (b) the Portsmouth breast-biomechanics studies (Scurr et al., 2010-2011): the breast moves in phase with the step, lags the trunk, and a supportive top cuts its travel by more than half; (c) the owner, 18 Oct: "sex appeal ... tho not at the cost of looking bad", so the motion is plausible and slightly emphasized, never cartoon physics.
- **R6.3 The weapon is rigid in the hand. Its follow-through lives in the arm:** the wrist drags 2-3 f behind the forearm on the way in, then snaps through contact. (b) Richard Williams, The Animator's Survival Kit (drag and successive breaking of joints).

## 7. Locomotion [R1, R2]

- **R7.1 The town walk (her own walk):**
  - 1.2 m/s at 104-110 steps a minute (a step of about 0.68 m).
  - The hips lead: pelvic list +-5-7 deg, pelvic yaw +-6-8 deg, the thorax counter-rotating +-4-6 deg.
  - Lateral pelvis sway is +-3.5-5 cm, with the feet placed within +-4 cm of the line of travel.
  - Arms swing +-15-20 deg at the shoulder (more back than forward) with the elbow at 15-30 deg, lagging the pelvis yaw by 2-4 f.
  - The head bobs at most 2.5 cm.

  Derivation: (a) the game's walk band (1.12-1.23 m/s, `Stride.Weights` 0.15-0.7 m/s blend); (b) Williams' walks on 12s (brisk) to 16s (stroll), with ours at about 13-14 frames a step at 24 fps; gait norms (Perry and Burnfield, Gait Analysis: pelvic rotation +-4-5 deg in a plain walk), raised for a feminine walk (Johnson and Tassinary, 2005: femininity is read from hip sway, masculinity from shoulder swagger).
- **R7.2 The run is authored at each calling's own game speed**, so playback scale stays within +-10%. Today one 5.1 m/s cycle is stretched 0.55-1.5x.

  | Calling | Speed | Steps a minute |
  |---|---|---|
  | Warden | 5.0 m/s | 168 |
  | Reaver | 5.1 m/s | 172 |
  | Arcanist | 5.3 m/s | 174 |
  | Stalker | 5.6 m/s | 180 |

  - Pelvic yaw +-8-12 deg, thorax counter +-10-14 deg, forward lean 5-8 deg.
  - Elbows at 80-100 deg, swinging +-35-50 deg; on the weapon side the swing is damped 50-70% and the weapon is carried quiet, low and back.
  - Pelvis vertical travel is 5-6 cm and the head's at most 5 cm. The head glides.

  Derivation: (a) archetypes.json move speeds and the `Stride.Period` clamp; (b) running norms at 5 m/s (cadence 170-180 a minute, vertical oscillation 6-10 cm, with efficient runners at the low end); 2B (NieR:Automata) and Aloy (Horizon Forbidden West) for the level head and the hips-first glide.
- **R7.3 The sprint (the Sprint art adds 70%: 8.5-9.5 m/s):** 200-215 steps a minute, a 12-18 deg lean, elbows at 90 deg with a full pump, the braid streaming back. (a) `Abilities` +70%.
- **R7.4 The stops (left and right foot):** 0.5-0.8 s; the last step is planted, then the weight rocks forward 3-5 cm and back, then the calling's idle. (c) The stop_* clips, rebuilt.
- **R7.5 The dash moves her on the press frame. Nothing comes before the travel:**
  - Travel 12 f (5.5 m in 0.2 s, 27.5 m/s). The first 2 f are the lean-in smear, the body at 35-45 deg low and long.
  - Landing at f12, with a 6-10 f recovery that overlaps the run blend.
  - The braid whips forward on the landing.

  Derivation: (a) `Abilities.Dash` 5.5 m / 0.2 s / 0.3 s i-frames; (b) Hades' dash (no wind-up, all read in the smear and the landing).

## 8. Economy in action: the attack [A1-A4]

- **R8.1 Structure.** Each attack runs anticipation, acceleration, contact, hold, follow-through, recovery, in that order:
  - The press is answered on frame 1 by the anticipation (the coil). Never by a frozen frame.
  - The contact holds 2-4 f: the click of the hit.
  - Recovery returns to the RELAXED fight-ready pose (§3), never to a guard.
  - The cancel window opens after the hold, so a faster attack speed cuts the recovery and never the contact.

  Derivation: (b) Street Fighter 6 frame data (startup / active / recovery); (a) the game plays swings at 1.6x (heavies 1.5x) on the upper layer, alternates back and fore, and cools down from 1.05 s (oathblade), 1.45 s (cleaver) and 1.6 s (sunder) to a 0.08 s floor, so the action part must stay readable at 2.5x.
- **R8.2 Frames by weapon class, authored at 1.0x:**

| Class (calling) | Anticipation | Contact | Hold | Follow + recovery | Total | Cancel from | Rhythm |
|---|---|---|---|---|---|---|---|
| Sword and shield (Warden) | 9 f | f13 | 3 f | 9 + 12 f | 36 f | f19 | committed: the shield moves first, the hips drive |
| Sword heavy (Warden) | 18 f (the shield punch) | f24 | 4 f | 12 + 14 f | 54 f | f31 | the weight thrown through |
| Axes (Reaver) | 8, then 6, then 5 f | f11, f9, f8 | 2 f | the spin carries into the next blow | 34, 30, 26 f | the hold's end | accelerating: each recovery is the next anticipation |
| Axe heavy (Reaver) | 20 f overhead | f26 | 4 f | 14 + 16 f | 60 f | f33 | the body crunches down |
| Staff cast (Arcanist) | 10 f (gather) | f12 (release) | 6-8 f STILL | 10 + 10 f | 40 f | f20 | the hand leads; only the arm moves; the hold is the read |
| Wand flick (Arcanist) | 6 f | f7 | 5 f | 8 + 10 f | 30 f | f14 | a flick from the wrist |
| Daggers (Stalker) | 3-4 f (a hip drop) | f5-6 | 2 f | 4 + 8-10 f, then STILL | 24 f | f9 | stillness, explosion, stillness |
| Crossbow (Stalker) | 6 f (brace) | f8, with a 3 f recoil | 6 f | 16 f (re-span, settle) | 36 f | f14 | a breath held, then a release |

  Derivation:
  - (b) Fighting-game norms: lights start in 4-6 f, heavies in 10-16 f.
  - (b) The economy of John Wick (2014, Chad Stahelski: no wasted motion), Atomic Blonde (2017, the stairwell: weight and real impact), Sifu (2022: snap strikes, then stillness), and Doctor Strange (2016: spell hands from finger tutting, the body still).
  - (c) Today's contacts land at 4-6 f (0.067-0.1 s, tools/anim): too early to show a coil.
- **R8.3 Between blows nothing extra:** no flourish, no victory pose, the head still. The head stays within 10 cm of its ready position except for a designed snap. (b) Furiosa (Mad Max: Fury Road) and Black Widow (MCU): lethal and calm.
- **R8.4 The grip tightens only at contact.** In ready and recovery the fingers sit at the ease of §3, shown at the wrist. (c) The owner, 17 Oct: fingers barely show, so the wrist carries it.

## 9. Hit, death, get-up [H1, H2]

- **R9.1 The hit** (upper layer, so the legs keep their gait):
  - An impact snap over 2 f: the chest and head displaced 8-12 cm away from the blow (3 px at play).
  - A 2 f hold, then recovery over 18-24 f with one overshoot back toward the threat.
  - 0.4-0.5 s in all. The arms keep their hold.

  (c) Today's flinch ("the chest caves, the head snaps back, the legs keep running"); (b) The Last of Us Part II's directional hits.
- **R9.2 Death** (1.2-1.6 s, held at the end):
  - The knees buckle (f0-12), the hips drop (f12-24), ground contact (f24-36) with a 3-5 cm bounce, then still.
  - She ends composed (an arm out, the braid across the ground), never a broken ragdoll.

  (b) The Last of Us Part II: weight and gravity, no float.
- **R9.3 The get-up** (1.2-1.6 s): the head comes up first, then onto a knee and the weapon hand, a push off the planted foot, and she is standing, rolling her shoulders, in the calling's ready pose. Defiance, not effort. (b) Sifu's and Elden Ring's quick rises.

## 10. The Flare press [F1]

**R10.1 Every press is visible, and the press is the BOOM.**
- Gather 8 f: the fist to the chest, the knees dip, the head drops.
- Impact on f9-10 with a 3 f smear.
- The money frame: a still hold of 20-30 f (0.35-0.5 s) inside the blast, her eyes up through it.
- Rise 24 f into ready. About 1.0-1.2 s in all.
- Each Flare has its own clip on this frame.
- The blend in from any pose is 0.1 s, never a held frame (c: Animation 62's FlareXfade).

Derivation: (c) `flare-is-a-boom-button` (screen clears, every press visible); (b) Marvel Rivals ultimates (one committed pose the whole screen reads), and the superhero-landing trope (Iron Man, 2008).

## 11. Each calling's own body [I1-I4, A1-A4]

| Calling | The read | Town idle (weapons sheathed) | Sway: pelvis travel, cycle | Fight-ready | Run carriage | Attack rhythm |
|---|---|---|---|---|---|---|
| **Warden**, hold the line | the wall at ease: grounded, heavy settles | hand on the hip, the other on the pommel, the sword hilt hung 12-15 cm lower than today (c: Animation 62's elbow finding), the shield on her back | **12-16 cm, 2.67 s: KEEP the owner's sway**, rebuilt on the new rig | the shield relaxed at chest height, the sword low by the hip | the shield low in front, the sword trailing | committed, rotation-driven, the shield first |
| **Reaver**, take it out of them | the restless predator: forward, asymmetric, a smirk | the hip cocked, a hand on the axe head, the neck crack, the axe spun and rested on the shoulder | 10-14 cm, uneven (a 2-beat shift, then a hold, 1.6-2.2 s) | the axes hanging from loose wrists, swinging as pendulums (1.2-1.5 s) | a 10-12 deg lean, the axes low and back | accelerating; the spins carry |
| **Arcanist**, keeps ledgers | composed, upright, precise hands | leaning into the planted staff, the hip into the shaft, ankles crossed, an ember rolled in the fingers. The staff's foot reaches the ground (a prop length in the spec; c: Animation 58's staff note) | 7-10 cm, one sway a breath (4 s) | the staff upright, the free palm up near the hip | the staff diagonal across the body | gesture-led; the hold is the read |
| **Stalker**, never there when it lands | light, watchful, UPRIGHT | weight on the back leg, the front foot on its ball, a dagger rolled across the knuckles, a thumb in the crossbow strap; the head scans 30-60 deg every 3-5 s while the body stays still. Knees 10-15 deg and the pelvis 2-3 cm down at most (c: the owner's "crouching like they have to go to the bathroom") | 6-9 cm, quick micro-shifts (1.2-1.8 s) | the daggers in reverse grip, close and still | the lightest: 180 steps a minute, 4-5 cm of bob, arms tight | stillness, explosion, stillness |

References for the town idles:
- Warden: the G1 key art; Wonder Woman (2017), the shield-bearer at ease.
- Reaver: Lagertha (Vikings), the cocky axe; Harley Quinn's bat-on-the-shoulder rest (Birds of Prey, 2020).
- Arcanist: Yennefer (The Witcher 3), stillness and precise hands; Ada Wong (Resident Evil 4, 2023), the poised hip lean.
- Stalker: Aloy (Horizon Forbidden West), the upright scan; Black Widow (MCU), watchful ease.

## 12. Effortless sexiness without vulgarity

1. The S-curve at rest (R2.1).
2. The hips lead the walk (R7.1).
3. The arch: the chest open and the shoulders back (R3.1), never a hunch.
4. The long free leg: knee soft, foot turned out.
5. Unhurried transitions in town (0.8-1.6 s).
6. The glance: the head turns 20-40 deg toward the camera at idle breaks, a half-smile at the close-up.
7. The hands rest on her own body: hip, thigh, belt, braid. It reads relaxed and sensual.
8. Secondary motion is plausible and slightly emphasized (R6.2).
9. Never pin-up posing in play, no thrusts, no mugging at the camera. The close-up walk-away and the "stare at the butt" town zoom (c: the owner, 17 Oct) get their read from the walk's hip rules and the glute springs, not from extra motion.

Derivation: (c) the owner's "sex appeal ... tho not at the cost of looking bad"; (b) 2B and Ada Wong (confident ease, no mugging).

## 13. Close-up and cinematics

- **R13.1 At the close-up the face stays still:** blinks, eye darts and a held half-smile only (c: `cutscene-face-minimal`, 28 Oct). The body carries the beat: breath, a weight shift, fingers, a glance with the eyes leading the head by 4-8 f and the head leading the chest by 4-8 f.
- **R13.2 Cinematic walk-ups and walk-aways use her town walk (R7.1) at 0.9-1.0x.** The beats are carried by a stop (R7.4), a turn led by the eyes and head, and a settle into contrapposto (R2.1).

## 14. What the check measures (each rule becomes a number in the P4 check)

| Check | Rule | Measure | Pass |
|---|---|---|---|
| Foot lock | R4.1 | a planted foot's slide | 0.5 cm or less |
| Contacts | R2.3 | hand-to-hip, pommel, staff: the gap | 1 cm or less while held |
| Self-intersection | §6 | arm into torso or breast; a weapon into her | 3 mm or less; weapon 0 mm |
| Idle life | R4.2 | pelvis lateral travel per loop | within the calling's band in §11 |
| Rest S-curve | R2.1-R2.2 | pelvis tilt, hip offset, line-of-action bend | in band |
| Tension | R3.1 | clavicle lift, elbow, wrist, knee at rest | in band |
| Head stillness | R8.3 | head travel over pelvis travel | 0.5 or less in idles and runs |
| Cadence | R7.1-R7.3 | steps a minute at the game speed | in band; playback scale 0.9-1.1 |
| Overlap | R6.1 | delay down the chain at the clip's stops | in band |
| Attack frames | R8.2 | contact frame, hold length, cancel frame | as the table |
| Play-read | R1.1, R1.3 | silhouette change in px at the play camera, anticipation to contact | 4 px or more |

The motion judge then rules on what the numbers can't: the whole-frame question at the play camera and at the close-up, 1:1.

## Boards

`survivorsunchained_inputs\motion_a1\boards\` holds 13 key-pose sheets, ChatGPT in the owner's account. Each sheet's PROVENANCE line is in `raw\PROVENANCE.txt`.
- I1-I4: the four town idles.
- R1-R2: the run and the dash.
- A1-A4: the four attack rhythms.
- H1-H2: hit, death and get-up.
- F1: the Flare press.

Each board's caption names its references and what is taken from each. The boards show intent (poses and rhythm), not final art. The outfits are indicative.
