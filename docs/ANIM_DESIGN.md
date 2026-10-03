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
| Run | Grounded and hard: a heavier, slower cadence (21 frames a cycle), little bounce, square shoulders, shield across the body, the sword arm swinging short | Upright and light, chin up, steps on one line and the hips swaying, the staff still in one fist, the free hand open | Pitched forward 24°, hunched, short fast cadence (19), high knee drive, big arm pump with the axes | A glide: low knees, long strides, little bounce, head steady and forward |
| Idle break | Rolls her sword shoulder, checks the buckler's strap, settles her weight | Turns the staff in her fingers, glances at the sky, tucks her hair | Rolls her neck, spins the axe in her hand, a restless step | Scans left and right, a crouch to read the ground, rises |
| Signature | The shield never drops | The free hand always shapes something | Never still | Always watching |

## 4. The set

Status: **made** (in the library, wired), **planned**, or **fallback**
(the Universal Animation Library plays, through `HerPose`). The manifest is
the live list.

### 4.1 Locomotion
- `run_<calling>[_<weapon>]` ×7: warden (sword and buckler), reaver (axe),
  reaver_axes, arcanist (staff), arcanist_wand, stalker (crossbow),
  stalker_daggers. Keyed by stride (`gait.py`). 5.1 m/s on her skeleton.
- `sprint` (planned): a longer, harder stride for the sprint art and the
  dash's burst.
- `run_stop_l/r` (planned): the plant and settle (0.5 s), chosen by which
  foot is down; `run_start` (planned): the lean in and first push.
- Turns: procedural lean into the turn (`HerCarriage`), not clips.
- Aiming while running: the legs run where she goes, her back turns to
  where she strikes (`HerCarriage`), up to 100°; beyond that she turns.

### 4.2 Idles (the signature)
- `idle_<calling>` loops, from 100STYLE takes (real weight shifts and
  breathing) retargeted, with the arms re-solved to hold the calling's
  weapon its way: warden (Proud), arcanist (Neutral, cocked hip),
  reaver (Angry), stalker (Crouched).
- `idle_<calling>_break`: one-shots every 8–14 s of standing (planned).
- `catch_breath` after hard running (planned).

### 4.3 Combat
Swings are upper-body clips laid over the run, and full-body when she
stands. Each: cocked at frame 0, the cut through frames 1–4, a held end of
cut at 4–6, follow-through to ~12, recovery to ~20 (at 30 fps; the game
plays them at 1.6×).
- Sword (warden): `sword_a` forehand (right to left), `sword_b` backhand,
  `sword_heavy` (a full turn of the hips, wide sweep).
- Axe (reaver): `axe_a` diagonal down-cut, `axe_b` rising backhand,
  `axe_heavy` overhead into the ground, from the hips.
- Axes: `axes_a` right, `axes_b` left, `axes_heavy` both, crossing.
- Knives (stalker): `throw` flick, `daggers_heavy` double slash.
- Arcanist: `cast_bolt` (the staff thrust forward, the free hand pushing
  the spell), `cast_raise` (the staff lifted and struck down), and the
  free-hand `cast_gesture` that marks spells going off.
- Crossbow: `crossbow_shoot` (raise, sight, the kick of the shot).
- Arts: `warcry` (a roar, arms out), `throw` (grapple, disc).
- `dash`: a low lunge, body nearly horizontal, trailing arm and hair, into
  the run (0.2 s of travel, 0.25 s to settle).

### 4.4 Reactions and death
- `hit` (upper, from the front): big enough to read at 31 m; head snaps,
  shoulders twist away, a half step back in the full version.
- `hit_heavy` (planned): staggered, a knee nearly down.
- `death`: knees go, a twist, down onto her side; held.
- `get_up`: from where `death` leaves her, a push up to one knee, rise.

### 4.5 Story and town
- `sit_log` (the title): sitting on a low log by the fire, forearms on her
  knees, breathing, now and then looking into the fire.
- Creation flourishes, one per calling: `warden_show` (the shield up and
  the sword levelled over it), `arcanist_show` (staff raised, light called
  to the free hand), `reaver_show` (the axe spun and slammed on her
  shoulder), `stalker_show` (the crossbow raised and sighted).
- Talk, gestures, kneel, emotes (planned; folk are Quaternius bodies and
  keep the library for now).

## 5. In the game

- Her clips are one library, `godot/art/anim/heroine.res` ("her/…"),
  added beside the Universal Animation Library on her player and her
  AnimationTree. `heroine_clips.json` says each clip's speed, cycle and
  layer.
- `People.HerClip` maps the game's clip names to hers by her calling and
  what she holds, and falls back to the library's for anything not made.
- `HerPose` stands down (`Lower`, `Upper`) for whichever half of her plays
  her own clips.
- `PlayerView` (her): idle and run blended by speed, the run's playback
  matched to her ground speed; swings on the upper body; one-shots on the
  whole body; `HerCarriage` leans her into turns and turns her back toward
  a strike while her legs keep running.
