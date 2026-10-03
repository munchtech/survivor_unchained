# Cinematics: index and production brief

The game's cinematic scripts, written to be built in Godot in real time with
the game's own characters, sets and light. This page is the brief for
whoever builds them: what to build first, the visual language every script
shares, the conventions the scripts are written in, and what the game does
not have yet. Each script is `docs/cinematics/<id>.md`. The story under them
is `docs/STORY_BIBLE.md`; voices are `docs/VOICES.md`; Act 1's facts and
routes are `docs/WRITING_PASS.md`.

## 1. Index

(Filled in below as the scripts land; see section 7.)

## 2. What a cinematic is for, here

Every cinematic in this game earns its place by doing at least one of three
things, and the scripts say which:

- **moving a relationship or a truth forward** (Brannoc learns where his
  daughter is; Vonnra hears herself named);
- **paying off something planted** (the Warden's lamp-iron is new; the
  survivor's breath does not smoke at night);
- **planting what a later act pays** (the prints in the frost come up from
  the river and none go down to it).

They are short. The longest in Act 1 is the fortune, and only because the
player wrote most of it. Nobody explains anything. The survivor never makes
a speech; she barely speaks at all. The camera notices what the narrator does
not say.

## 3. The heroine

The survivor is the player's: any face (the 25 sliders), any hair (long,
ponytail, braid, bob, pixie, in any colour), any skin, any of four callings
in its outfit, any background. A male survivor exists too and plays every
script unchanged, with the pronoun and hair notes each script gives.

- **Faces we can move.** Her head has these expression shapes, each 0 to 1:
  `blink_l`, `blink_r`, `eyes_wide`, `squint`, `brows_up`, `brows_sad`,
  `brows_angry`, `smile`, `mouth_open`, `pucker`, `snarl`, `frown`,
  `nose_wrinkle` (`tools/assets/heroine_head.py` EXPRESSIONS, applied by
  `People.HerFace`). Her eyes are driven by `HerFaceLife.Look` (where she
  looks, in iris radii; +x her left, +y down) and `Wander`; her blinks run on
  their own unless a shot holds them. Scripts give performance as these
  shapes with values and timings, and gaze as targets.
- **Hair moves.** Long, ponytail and braid swing on chains
  (`HairSway.cs`); bob and pixie move as springs. Scripts that want hair to
  carry a beat say so (a toss of the head, wet hair hanging).
- **Calling beats.** Where a calling changes a beat, the script gives four
  inserts: warden, reaver, arcanist, stalker. The weapon in hand is the one
  she chose (Oathblade or Judgement Disc; Cleaver or Axe Gyre; Seeking Motes,
  Cinderfall or Rimeshard; Volley or Knifestorm); inserts say how each
  variant reads.
- **Her voice.** She has none in the cinematics: breath, effort, a held
  breath let go. Her lines are the player's choices, read silently. This
  keeps every face and every survivor hers.
- **NPC faces.** The townsfolk have no face shapes and no jaw (Quaternius
  bases). Until they do, scripts frame them for it: no extreme close-ups on
  an NPC who speaks, speech carried by the head, the hands and the light. See
  section 6.

## 4. Visual language

**Aspect and bars.** Cinematics play at 2.39:1: black bars ease in over 0.6 s
as one begins, out over 0.8 s as it hands back to play. The HUD, plates and
hints hide with the bars in and return with them out. Subtitles sit in the
lower bar.

**Lenses.** Scripts give lenses as full-frame 35 mm focal lengths. Build them
as a horizontal field of view (`Camera3D.KeepAspect = Width`, `Fov` =
horizontal), which the bars do not change:

| Lens | 14 | 18 | 24 | 28 | 35 | 40 | 50 | 65 | 85 | 100 | 135 | 200 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Horizontal FOV (°) | 104.3 | 90.0 | 73.7 | 65.5 | 54.4 | 48.5 | 39.6 | 30.9 | 23.9 | 20.4 | 15.2 | 10.3 |

**Camera rules.**
- Wide lenses (24 to 35) for places and danger, long lenses (85 to 135) for
  faces and for what is far and wrong. 50 is the default for two people.
- The camera stays at eye height, or below it for anything that should feel
  bigger than the survivor. It goes above her only to hand back to play (the
  game's own camera is high) and for the valley from the toll tower.
- Moves are slow and motivated: pushes on a realisation, drifts with a walk,
  one crane a scene at most. Handheld is reserved for the night fights' boss
  arrivals (a light shake, 0.3 to 0.6 of the game's camera shake). No
  whip-pans except where a script names one.
- Depth of field on every close-up (`CameraAttributesPractical`, far blur on,
  focus on the eyes or the named object).
- Cut on action or on a look; hold a beat longer than feels safe when the
  beat is silence.
- Shot types: ECU, CU, MCU, MS, MLS, LS, ELS, OTS (over the shoulder), POV,
  INSERT (an object), 2S (two-shot).

**Light and grade.** The game's atmospheres (`Atmospheres.cs`: Night, Dawn,
Dusk, NightTown) are the base. Over them, cinematics add a grade: shadows
pushed toward blue-green at night, highlights kept warm wherever there is
fire, a little more contrast than play, and a soft vignette. Three lights
carry the story's meaning and should always read as themselves:
- **firelight** (warm, low, flickering): people, the living, the town;
- **ford-lamp blue** (`#8ac8ff`, steady, cold): the Wardens, the chain, the
  Morrow's light as the Watch kept it;
- **ember red** (`#ff5a1e` to `#ff9a48`, pulsing): the ember, the scars, the
  survivor burning at night.

**Motifs.** Recurring images the scripts plant and pay. Keep them exact:
- *No breath at night.* On cold nights everyone's breath smokes. The
  survivor's never does while the ember burns; at dawn, when it goes out, her
  first breath smokes (C04). This needs a breath-smoke effect on people in
  the cold, and its absence on her, every night of the game.
- *Prints.* Hers in the frost come up from the river and none go down
  (C01). Jessop's at the sealed door go in and none come out (Act 1 find,
  Act 3 payoff).
- *Lamps held up to faces.* A watchman's habit: the Ford-Warden holds his
  lamp up to the survivor's face before he speaks (C02); Vonnra lifts hers
  the same way at the fortune (C09).
- *The hammer.* Brannoc's hammer is the town's clock. When it stops, the
  town hears it stop.

## 5. Conventions in the scripts

**Places.** Zone coordinates in metres, as in `godot/data/zones/<zone>/zone.json`
`places`. North is -z, east is +x. A heading of 0 faces south (+z), pi/2 east,
pi north, -pi/2 west (as `NpcActor` turns). Heights are above the ground at
that point (`HeightAt`).

**Timing.** Each shot gives a duration in seconds; the total is the sum. Lines
are timed from the shot they start in. `[beat]` is about half a second of
nothing; `[hold]` is a second or more, as long as the shot.

**Lines and VO ids.** Every spoken or narrated line lives in
`godot/data/content/dialogue.json`. Lines written for a cinematic are in a
conversation of their own named after it (`cin_drowned_fire`), one node per
line, chained with `next`; the node's `speaker` says who (`narrator`, a
person's id, `ford_warden`, `grimtunnel`). A line's VO id is
`<conversation>.<node>`; where a node has text variants (by calling, by
facts), each variant's id adds `#<index>` in the order written
(`cin_fortune_ledger.close#1`). Lines a cinematic stages from an existing
conversation (Greymuzzle, Brannoc, Vonnra's fortune) keep their own ids
(`brannoc.nell_ditch`). A cinematic's chain ends on a node whose only choice is
`(Continue.)`: the player of cinematics does not show it; it is there so the
conversation can also be walked as an ordinary one (`--open talk:cin_...`), to
hear and check the lines before the cinematic exists. Each cinematic
conversation has a `speakers` entry in `npcs.json` (its title) so the content
tests know it.

**Effects.** Where a cinematic changes the world (a fact set, a journal line),
the change is on its conversation's nodes, so it happens whether the
cinematic plays or is skipped.

**Performance.** Lines carry a note: the feeling under it, the beat, where the
speaker looks. For the heroine, the notes give face shapes and gaze. For NPCs,
the notes give body and head (no faces yet).

**Sound.** Music is composed live (`src/Audio/Music.cs`: moods Silence, Title,
Explore, Town, Night, Combat, Boss, Mystery). Scripts give cues as a mood, a
tempo, an intensity over time, instruments and the swells; and every sound
by what makes it. Silence is a cue.

**Subtitles.** On by default in cinematics. Speaker's name for people, none
for the narrator (italics). Up to two lines at a time, 42 characters a line;
long lines break at the script's `/`.

**Skipping.** Every cinematic can be skipped after its first 1.5 s by holding
interact or pause for 0.8 s (a ring fills). Skipping lands on the end state:
the effects applied, the survivor where the cinematic leaves her, the game's
camera. A cinematic seen once can be skipped from its first frame.

## 6. What the game needs that it does not have yet

The tech each script needs is listed in that script; this is the whole list,
in the order to build it.

**Must have (Act 1 cannot be built without it)**
1. **A cinematic player**: reads a timeline (shots, cameras, cast marks and
   moves, clips, face keys, line cues, sound and VFX cues, effects) and plays
   it in the running zone with the world paused or slowed (`Battle.WorldRate`)
   and controls captured (`Capture`). Hold-to-skip; seen-once memory.
2. **A cinematic camera**: animated position, look-at and roll; field of view
   per shot; depth of field; cuts and blends; crane and dolly by spline;
   handheld noise; blend into and out of the game's follow camera. Today
   `Showcase` only drifts a fixed-FOV camera to a mark.
3. **Letterbox** and a subtitle line in the bar (the `Say` line restyled).
4. **Voice**: VO playback by line id, from files rendered with the local
   Qwen3-TTS (cast per `VOICES.md`), with subtitles timed to the audio.
5. **Clips we lack**: lying and waking on the ground (on the side, to
   sitting); sitting on the ground (the game maps it to a crouch); kneeling on
   one knee and staying; kneeling with a hand held out, palm up; laying a
   weapon down; lifting a shield off the ground; wrenching an axe out of wood;
   a hand to the throat; carrying a small body; digging; a slow head-turn to
   look at someone; a seated reading of a palm (two people, hands); a
   standing embrace; a fall to the knees and a fall forward (the Warden's,
   Greymuzzle's). Each script names its own.
6. **NPC faces**: at least blink and a jaw (or a mouth-open shape) on named
   people, driven by their VO's loudness; better, the heroine's head on the
   people who carry scenes (Vonnra, Brannoc, Rook, Harlan, Redcowl, Maeca,
   Chid). Until then, the scripts' framing avoids NPC close-ups while they
   speak.
7. **Wetness** on hair, skin and cloth (darker, glossier, clumped hair), set by
   a value that dries over time (C01).
8. **Breath-smoke** on people in the cold at night, absent on the survivor
   while the ember burns (C01, C04, and every night after).
9. **Ground decals**: wet footprints (C01), frost on grass, blood.
10. **Sets**: a roof on the toll tower to stand on (C09); Brannoc's anvil and
    the rack with two lamp-irons by the smithy (C07, and all of Act 1); the
    Roost's people (women, the old, children, cooking fires) and an old red
    standard with Ashford's arms (C06); Nell's iron marker by Ashe's grave in
    the Quiet Garden (C08).
11. **Music cues**: the mood system driven from a timeline (a mood, an
    intensity ramp, a swell, a hit, a cut to silence), and a handful of
    composed motifs named in the scripts (the Warden's song, the lamp motif,
    Chid's hymn).

**Should have**
12. Ember VFX: the ember draining out of the survivor at dawn (down her body
    into the ground); embers kindling in her at night; the heart's cold
    light reaching for her (C03).
13. A Warden of real presence: a face for the giant (or a helm with eyes of
    blue light) that can be held in close-up; his lamp on its own bone so it
    can be lifted to a face.
14. Water: the ford's surface reacting (wakes, the drowned turning in an
    eddy).
15. Hand IK for holding hands, taking a coin, reading a palm.

**Production notes**
- Render VO with Qwen3-TTS at 48 kHz, one file per id, named by id.
- Keep every cinematic's timeline as data next to its script, so the writer
  can retime without code.
- Redcowl is two different models today (an NPC with a crossbow; the
  "enforcer" with a greataxe when he fights). The scripts treat him as one
  man: a big man, bearded, a red hood, the greataxe across his back. Make the
  NPC match.

## 7. Index of scripts

| Id | Title | Act | Kind | Priority | Length | File |
|---|---|---|---|---|---|---|
| (filled as written) | | | | | | |
