# Animation design: the heroine

What she plays, why, and how each clip should feel. The research behind it
is `docs/ANIM_RESEARCH.md`; the tools are `tools/anim/`; what is made and
from where is `tools/anim/manifest.json`.

The test for every clip is the owner's: **does she have soul?** Stock
motion fails however clean it is. Every clip is hers (her proportions, her
weight, her calling's attitude), carries a human detail or two, and reads
from the arena's camera at 31 m.

## 1. What the game plays on her

From the code (`PlayerView.cs`, `PersonView.cs`, `GameFront.cs`,
`Portrait.cs`, `Reflections.cs`, `Loadout.cs`):

| Where | When | Clip today (UAL) | Layer |
|---|---|---|---|
| The fight | Standing | the calling's idle (`Idle_Loop` for her) | full |
| | Moving (5.0–5.6 m/s, 0.2 s to reach it) | blend of `Walk`, `Jog_Fwd`, `Sprint` by speed | full |
| | A melee weapon swings (on its cooldown) | `Sword_Regular_A/B/C`, `Sword_Attack` (wide arcs), `Sword_Heavy_Combo`, `OverhandThrow` | upper body over the run |
| | A caster's spells go (every 1.6 s while slow) | `Spell_Simple_Shoot` | upper |
| | Arts: blink, mirror, echo | `Spell_Simple_Shoot` ×1.8 | upper |
| | Arts: grapple | `OverhandThrow` | upper |
| | Arts: warcry, sprint, cinder trail, wraith walk | `Punch_Cross` | upper |
| | Arts: bull rush / chain haul | `Shield_Dash` / `Sword_Dash` | full |
| | Arts: leap / vault | `NinjaJump_Start` / `Jump_Start` | full |
| | Dash (5.5 m in 0.2 s) | `Roll` ×1.9 | full |
| | Struck (>25% of the hurt timer) | `Hit_Chest` ×1.6 | upper |
| | Falls | `Death01`, held | full |
| | Second chance (prologue) | `LayToIdle` ×1.2 | full |
| Title | By the fire (a hooded stranger, her body) | `Sitting_Idle` | full |
| Creation | Standing, then a flourish when the calling changes | calling idle; `Spell_Simple_Enter` / `Sword_Regular_A` / `Sword_Block` / `Pistol_Shoot` | full |
| Portraits, mirror images | | the calling's idle, `Attack[0]` | full |

Her weapons by item (`Loadout.cs`): oathblade (sword + buckler) and
judgement disc (sword + buckler, throws) for the warden; cleaver (one axe)
and gyre axes (two) for the reaver; wand, ember staff, rime rod for the
arcanist; hunting bow (a crossbow, held pistol-fashion) and the knife belt
(two daggers) for the stalker.

## 2. Principles

1. **Hers, not borrowed.** Built on her skeleton at her proportions; no
   correction layer needed (`HerPose` stands down for her own clips).
2. **The run is the hero clip.** She is running nearly always: one cycle
   per calling and weapon, at the game's speed (5.3 m/s in the world), feet
   planted dead still on the ground, played faster or slower with her
   speed so they stay planted.
3. **Strike first, weight after.** The game deals damage, draws the arc and
   plays the swing in the same frame. A swing starts already cocked (the
   anticipation is the 0.05 s blend in), the blade crosses inside the arc's
   0.12 s, holds a beat at the end of the cut (where hit-stop lands) and the
   weight is sold in a long follow-through and recovery, which the next
   swing may cut short. Alternate swings alternate sides, as the arcs do.
4. **Read from above.** Big lateral sweeps; arms and weapons away from the
   body; a clear lean into speed, starts, stops and turns; silhouettes that
   say the calling at a glance.
5. **Soul is in the small things.** A signature idle per calling with
   breaks (a fidget, a check of the gear, a breath); weight shifts; the head
   leading turns; breath after effort; hands that are never claws.
6. **Feminine and powerful at once.** Hip sway, a line of steps, chin up,
   a confident carriage; in combat no loss of power: the hips drive the
   blows.

## 3. The four carriages

| | Warden | Arcanist | Reaver | Stalker |
|---|---|---|---|---|
| Attitude | The wall: heavy plate, unhurried, certain | Poise: a scholar of dangerous things | Feral: hungry, restless, all forward | The predator: patient, low, silent |
| Stance | Square, feet wide, weight even, shield up | Upright, feet on a line, one hip cocked, staff planted | Low, wide, weight forward on the balls of the feet, shoulders hunched | Crouched a little, weight back, head level and turning |
| Run | Grounded and hard: a heavier, slower cadence (21 frames a cycle), little bounce, square shoulders, shield across the body, the sword arm swinging short | Upright and light, chin up, steps on one line and the hips swaying, the staff still in one fist, the free hand open | Pitched forward 32°, hunched, short fast cadence (19), high knee drive, big arm pump with the axes | A glide: low knees, long strides, little bounce, head steady and forward |
| Idle | Heavyset's square, tensed standing; buckler across her, sword low | Strutting's chin-up ease; staff upright, a hand on her hip | Angry's restless tension; the axe on her shoulder | Crouched and ready; the crossbow low across her |
| Idle break | Rolls her sword shoulder, looks her buckler over | Turns the staff in her fingers, glances at the sky, tucks her hair | Rolls her neck, spins the axe in her wrist, shakes out her hand | Scans left and right, a crouch to read the ground, rises |
| Signature | The shield never drops | The free hand always shapes something | Never still | Always watching |

## 4. The set

Everything below is **made** and wired into the game unless marked
**planned**; anything without a clip of hers plays from the Universal
Animation Library through `HerPose` as before (the leap and vault, the
bull rush and chain haul). `tools/anim/manifest.json` is the live list,
with each clip's source, licence and length.

### 4.1 Locomotion
- `run_<calling>[_<weapon>]` ×7: warden (sword and buckler), reaver (axe),
  reaver_axes, arcanist (staff), arcanist_wand, stalker (crossbow),
  stalker_daggers. Keyed by stride (`tools/anim/gait.py`): planted feet
  travel at exactly ground speed, so with playback matched to her speed
  they stay put. 5.1 m/s on her skeleton, 5.3 in the world. The leans
  (13° arcanist to 32° reaver) were raised after judging the side views:
  at the game's camera a run needs more pitch than life to read as one.
- `sprint_<calling>[_<weapon>]` ×7: each run pushed (longer and lower, more
  lean, harder arms), in step with its run so the two blend by speed.
- `stop_<calling>_l/r` ×8: out of the run onto whichever foot was coming
  down, carried over it, braking back, a rebound, settled.
- Turns and starts: procedural (`HerCarriage`): she banks into turns by
  turn rate times speed, tips forward into a start and back out of a stop.
- Aiming while running: the legs run where she goes, her back turns to
  where she strikes (`HerCarriage.Aim`, shared down the spine), up to 110°;
  beyond that, or standing, she turns whole.
- `run_start` (planned): a first push off the back foot.

### 4.2 Idles (the signature)
- `idle_<calling>` loops: a 100STYLE take for the body (real weight shifts
  and breath; CC BY 4.0), retargeted, the arms re-keyed to hold the
  calling's weapon its way. Warden: Heavyset, the buckler across her, the
  sword low. Arcanist: Strutting, the staff upright, the free hand on her
  hip. Reaver: Angry, the axe on her shoulder. Stalker: Crouched, the
  crossbow low across her.
- `idle_<calling>_break`: every 10–16 s of standing where nothing is near:
  the warden lays the blade on her shoulder, rolls it and looks her buckler
  over; the arcanist tucks a strand behind her ear and looks up at the sky,
  turning the staff in her fingers; the reaver rolls her neck, spins the
  axe twice in her wrist and shakes out her hand; the stalker looks each
  way and crouches to touch the ground. Laid over her captured standing,
  so her weight keeps moving. Any of them gives way the moment she moves.
- `catch_breath`: stopping after more than six seconds of running, nothing
  near: hands on her knees, three hard breaths, up, the hair pushed back.

### 4.3 Combat
Swings are upper-body clips laid over the run (full-body when she stands).
Each starts cocked (the blend in is the anticipation), crosses within the
arc's first 0.12 s, holds the end of the cut a beat (where hit-stop lands),
then follows through and recovers; played at 1.6×.
- Sword (warden): `sword_back` (her left to her right: the game's first
  arc), `sword_fore` (back the other way), `sword_heavy` (a full turn from
  the hips, low and wide). The buckler stays up before her through all of
  them.
- Axe (reaver): `axe_back`, `axe_fore` (hacks that fall as they cross, the
  back thrown behind them, the free fist flung back), `axe_heavy` (from
  over the shoulder down and through).
- Axes: `axes_left`, `axes_right` (each hand in turn, the other winding up
  for its go), `axes_heavy` (both crossing out from the middle).
- Daggers: `daggers_back`, `daggers_fore` (quick rips), `daggers_heavy`
  (a crossing cut); `throw` when a knife is loosed.
- Arcanist: `cast_bolt` (the staff's spell pushed from the open hand with
  the shoulder behind it), `cast_flick` (the wand whipped out at the foe),
  `cast_raise` (the great working: the staff swept up and struck down).
  Played when a spell is actually loosed (`Ev.Muzzle`), not on a timer.
- Crossbow: `crossbow_shoot` (up to the eye, the kick, lowered), on each
  bolt loosed.
- Arts: `warcry` (gathered in, thrown open, a roar held), `throw` (the
  chain, the disc).
- `dash`: a low streak, the arms swept back, the back leg long, landing on
  the front foot into the run (0.2 s of travel, 0.27 s to settle).

### 4.4 Reactions and death
- `hit` (upper body): the head snaps, the chest twists and caves, the
  shoulders come up, the hands jerk; she gathers herself.
- `death`: rocked back, the knees go, she drops to them, sways, and falls
  forward onto her face with an arm out; held.
- `get_up`: from there: a push up on her hands, a knee under her, up, a
  roll of the shoulders.
- `hit_heavy` and directional reactions (planned).

### 4.5 Story and town
- `sit_log` (the title's stranger): forward on the log, forearms on her
  knees, two slow breaths, a look off down the road over her shoulder and
  back, her hands rubbed warm; eight seconds, looping.
- Creation flourishes: `warden_show` (steps in behind the buckler and
  levels the blade over its rim), `arcanist_show` (strikes the staff down,
  her free hand opens to the light, chin up), `reaver_show` (wheels the
  axe overhead and slams it back onto her shoulder), `stalker_show`
  (sights the crossbow across the dark, left, then right).
- Talk, gestures, kneel, emotes (planned; folk are Quaternius bodies and
  keep the library for now).

## 5. In the game

- Her clips are one library, `godot/art/anim/heroine.res` ("her/..."),
  added beside the Universal Animation Library on her AnimationPlayer and
  her player's AnimationTree; `heroine_clips.json` beside it holds each
  clip's speed, cycle and layer.
- `HerClips` maps the game's clip names to hers by her calling (from her
  outfit) and what she holds, and falls back to the library's for anything
  not made; `People.Clip(person, name)` is the one call the views make.
- `HerPose` stands down (`Lower`, `Upper`) for whichever half of her plays
  her own clips, eased over the blend.
- `PlayerView` (her): idle, run and sprint blended by speed, the playback
  matched to her ground speed; swings on the upper body, alternating as
  the arcs do; one-shots on the whole body; her clips advanced on the
  fight's clock, so hit-stop and slow motion hold her too; stops, breaks
  and the caught breath when she stands; `HerCarriage` for banking, tilt
  and the turn of her back toward a blow.
- `PersonView` (her elsewhere: creation, portraits, reflections, the
  title): her clips through `People.Clip`, her calling's break now and
  then while she stands, `Flourish` for creation.

## 6. Judging

Every clip was rendered as contact sheets (`tools/anim/review.py`,
`board.py`: her in her outfit, with stand-ins for her weapons, over a
checked floor) from the side, the front, three-quarters and the game's
own camera at its true size, frame by frame, and checked in the running
game. What the sheets showed and what changed is in the commit history;
what is still short of the bar is in §7. The latest boards are in
`docs/anim/`: `runs.jpg` (the four carriages and a sprint, from the
side), `idles.jpg`, `swings.jpg`, `actions.jpg` (dash, flinch, fall and
rise, war cry, throw, crossbow, casts) and `soul.jpg` (the seat by the
fire, the flourishes, the breaks, the caught breath, a stop).

## 7. Still short of the bar

- The swings and casts are keyed poses with sound arcs and timing, but
  little overlapping motion of their own (her hair and soft-tissue springs
  supply some); an animator polishing the in-betweens, or Kimodo
  in-betweening the keyed poses once its gate is open, would lift them.
- The idles' bodies are one performer's (100STYLE's): real weight, but a
  man's way of standing; the arms and the calling's hold make them hers,
  and her own performance captured on video (SAM 3D Body) would be better.
- The walk is never seen for more than a few frames, so it has no clip:
  the run blends from standing.
- The leap, the vault, the bull rush and the chain haul still play the
  library's clips.
- Folk and the crowd keep the library.
