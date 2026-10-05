# Cinematics: index and production brief

The game's cinematic scripts, written to be built in Godot in real time with
the game's own characters, sets and light. This page is the brief for
whoever builds them: what to build first, the visual language every script
shares, the conventions the scripts are written in, and what the game does
not have yet. Each script is `docs/cinematics/<id>.md`. The story under them
is `docs/STORY_BIBLE.md`; voices are `docs/VOICES.md`; Act 1's facts and
routes are `docs/WRITING_PASS.md`.

## 1. Index

The full table is section 7. In short: fourteen Act 1 scripts, ready to build
(C01 to C14); the Act 2 and Act 3 cinematics and the endings outlined
(`act2_outline.md`, `act3_outline.md`). Build in priority order: 1 (the opening
and the act's turns), then 2 (the choices), then 3 (the optional night fights).

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

### The soul test

The owner's question of every scene is "do we have soul?": is this one game in a
million, or one of many? Every script here has been read against it, and every
new one must be. **If a shot, a line or a beat could be lifted into another
dark-fantasy game and work unchanged, it is not finished.**

What makes a scene this game's and no other's:
- **This valley's debt to the dead.** Everyone here keeps the lights on with a
  debt to the dead they cannot pay, and the light is the dead. A scene earns its
  place when it touches that: who is being burned, who is being kept, who is
  counting.
- **This valley's things.** Lamps held up to faces; ember blue in a new black
  iron; oil burning warm; breath that does and does not show; prints in frost;
  a hammer as the town's clock; boots; a toll-token with three roads; a square
  coin; a ledger in violet ink; weed in red hair. If a scene could swap its
  objects for any other game's, its objects are wrong.
- **This valley's words.** "Lie down." "Is it morning?" "Not yet." "Them
  first." "You know the place." "Nobody's!" The Order's call, the hymn, the
  handbook. People speak in their trades and their histories, never in the
  genre's voice.
- **One point of view.** The narrator's: present tense, plain nouns, one image
  at a time, never what it means. The camera holds a beat longer than is safe,
  looks at hands, and stays with the person who has to live with it.
- **Costs paid on screen, by people we know.** Not "the town suffers": Brannoc
  kneels; Rook steps back and back; Harlan's hand stays on Jory's shoulder.

What fails it, and is cut on sight:
- a villain who explains, or laughs at nothing;
- a hooded watcher who sees the deed and leaves (we cut two);
- prophecy, destiny, the chosen one; "it has begun";
- red eyes meaning evil, rain meaning grief, a tear in close-up meaning sad;
- a dying speech that sums up a life;
- a reveal that is only a fact, rather than something the player did, seen
  again;
- a line any character could say;
- an image that is only beautiful.

Ask it of every shot, in every review, alongside `docs/editorial/REALNESS_AND_EXTREMES.md`'s
four questions about the people in it.

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
  game's own camera is high), for the first establishing shot of a place (C04's
  crane into the Waystation), for the valley from the toll tower, and for one
  shot a scene that must show how small she is (C03's groan).
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
- **ford-lamp blue** (`#8ac8ff`, steady, cold): ember burning in a Warden's
  iron, and only there (Brannoc's new irons on the Low Ford road; the Wardens;
  the chain). In an open lamp ember burns gold, small and very steady: Rook's
  Order lamp, Vonnra's lamp on the tower, the town's lamps. Oil, when anyone has
  it, burns yellower and smokier than either (Brannoc's lantern in C14). Sella's
  blue room is indigo glass over a warm flame, never `#8ac8ff`;
- **ember red** (`#ff5a1e` to `#ff9a48`, pulsing): the ember, the scars, the
  survivor burning at night.

**Motifs.** Recurring images the scripts plant and pay. Keep them exact:
- *No breath at night.* On cold nights everyone's breath smokes. The
  survivor's never does while the ember burns; at dawn, when it goes out, her
  first breath smokes (C04). This needs a breath-smoke effect on people in
  the cold, and its absence on her, every night of the game.
- *Prints.* Hers in the frost come up from the river and none go down
  (C01); at dawn new ones come up out of the river and go on (C04). Jessop's at
  the sealed door go in and none come out (Act 1 find; C13 glimpses him; Act 3
  pays).
- *Lamps held up to faces.* The keeper's habit: the Ford-Warden lifts his lamp
  to the survivor's face to see who she is (C02); Grimtunnel swings his
  head-lamp into it to smell her (C03); Vonnra lifts hers only if the survivor
  tells her she lit the lamps (C09), and it is the first time she has looked at
  the survivor's face at all. Three in Act 1; do not add a fourth. What a keeper
  looks for, holding a lamp to a face at night, is breath. In the lamp's light,
  the survivor's does not show (C02 shot 8; C09 shot 14a, beside Vonnra's, which
  does). Nobody ever says so: it is the reason for the gesture, and the player
  who notices has the whole motif.
- *A lamp that never touches the water,* until it does (C02, C03); *a lamp
  burning in daylight*: Vonnra's in the tower window, kept lit past dawn for
  one arrival (C04), and Rook's at Nell's grave (C08).
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
(`cin_raid_on_the_roost.last#1`). That is the scripts' short form. The voice
system (`tools/vo`, `VoiceLines`) files the same line as
`dlg.<conversation>.<node>.<index>` (`dlg.cin_raid_on_the_roost.last.1`); a
caption written in a zone's code is filed by the hash of its words. A variant whose text is empty is no line:
nothing plays and no subtitle shows. (Use one where a beat is spoken for some
survivors and silent for the rest; none of the Act 1 scripts needs one now.) Lines a cinematic stages from an existing
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

**Love scenes are not cinematics.** There are no NPC faces to hold, and
two-person animation is the dearest thing on this list. Each love scene's
cut-away is narrated, as written in `docs/romance/`, and the screen holds one
object, still, for its length: Sella's bolt going home; Maeca's boots side by
side outside the hides; Keegan's armour laid out in order on a chapel bench;
two cups on Rav's table, one full; Ysolde's spectacles folded on the twelfth
drawing. An insert at 85 to 100, the room's own light, no music but the room.

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
   while the ember burns (C01, C04, and every night after); a breath that a
   lamp's flame leans from (C09).
9. **Ground decals**: wet footprints (C01), frost on grass, blood.
10. **Sets**: the prologue's Low Ford road at night, reused for a story fight,
    its irons lit along it and the ambush's wagon and ditch (C14); a roof on the
    toll tower to stand on (C09), with a backdrop of
    the valley whose lights follow the world's facts; Brannoc's anvil and the
    rack with two lamp-irons by the smithy (C07, and all of Act 1); the Roost's
    people (women, the old, children, cooking fires) and an old red standard
    with Ashford's arms (C06); Nell's iron marker by Ashe's grave in the Quiet
    Garden, and the empty hook over the Last Lamp's door (C08); a den's mouth at
    the edge of the Pack's arena (C10). Props with writing: the ledger page,
    twenty-seven lines in a small violet hand, twenty-six ruled through (C09);
    the marker's plate, NELL punched with a nail (C08).
11. **Music cues**: the mood system driven from a timeline (a mood, an
    intensity ramp, a swell, a hit, a cut to silence), and a handful of
    composed motifs named in the scripts (the Warden's song, which is the
    Order's evening call; the lamp motif; the burial hymn "Lie Down", sung by
    Chid and a crowd, C08).

11a. **Boss hooks on a story fight** (built by combat in `StoryNight`, 4
    October): the fight plays `<id>_arrival` as the boss comes in, and
    `<id>_end` or `<id>_spared` as it ends, where `CanCinematic` finds a
    timeline (`StoryFight.Cinematic` names the id: `c10` for the Hollow). The
    ids: `c10_arrival`, `c10_end`, `c10_spared`; `c11_arrival`, `c11_end`,
    `c11_spared` (and `c11_again`, his laugh on a rise); `c12_arrival`,
    `c12_end`; `c13_door` (before the fight), `c13_arrival`, `c13_end`.
    - The end is decided in play (the spent boss, the prompts), and the
      cinematic starts from it: `_end` on the death, `_spared` at the choice.
      A spared part owns the boss's getting up and going; the fight releases
      him when it hands back.
    - The fight passes the marks `boss` (where he stands or lies, and his
      heading) and `her`, and the place's named points the part needs
      (`den_mouth` for C10), so the cameras are offsets that hold wherever the
      fight ends (as C03's are).
12. **Allies in a fight**: an NPC who fights beside her in an arena, holds a
    place (the edge of a light) and does not chase (Brannoc, C14; Act 2's war at
    the gate needs many).
13. **Story fights on the merciful routes**: C14 is the first, on the truth
    route; the Act 1 story fights are otherwise all on the violent routes.

**Should have**
14. Ember VFX: the ember draining out of the survivor at dawn (down her body
    into the ground); embers kindling in her at night; the heart's cold
    light reaching for her (C03).
15. A Warden of real presence: a face for the giant (or a helm with eyes of
    blue light) that can be held in close-up; his lamp on its own bone so it
    can be lifted to a face.
16. Water: the ford's surface reacting (wakes, the drowned turning in an
    eddy).
17. Hand IK for holding hands, taking a coin, reading a palm, closing a dead
    man's eyes, lifting a cord over a head.

**Production notes**
- Render VO with Qwen3-TTS at 48 kHz, one file per id, named by id.
- Keep every cinematic's timeline as data next to its script, so the writer
  can retime without code.
- Redcowl is two different models today (an NPC with a crossbow; the
  "enforcer" with a greataxe when he fights). The scripts treat him as one
  man: a big man, bearded, a red hood, the greataxe across his back. Make the
  NPC match.

## 7. Index of scripts

### Act 1 (scripts)

| Id | Title | Where | Kind | Priority | Length | File |
|---|---|---|---|---|---|---|
| C01 | The Drowned Fire | Prologue, the camp | The opening | 1 | 48 s | `c01_drowned_fire.md` |
| C02 | None Cross After Dark | Prologue, the ford | Boss arrival (the Ford-Warden) | 1 | 44 s | `c02_none_cross.md` |
| C03 | The Heart Goes Down | Prologue, the ford | Boss death; Grimtunnel | 1 | 45 s | `c03_heart_goes_down.md` |
| C04 | First Light | The north bank; the Waystation | The ember goes out; chapter one opens | 1 | 40 s + 26 s | `c04_first_light.md` |
| C05 | The Kneeling | The Verge, Wolf Hollow | Choice, with endings | 2 | 55 to 75 s + choices | `c05_kneeling.md` |
| C06 | Forty-One Mouths | The Verge, the Roost | A reveal; into Redcowl's talk | 2 | 33 s, then the talk | `c06_forty_one_mouths.md` |
| C07 | The Hammer Stops | The Waystation, the smithy | Choice, with endings | 1 | 45 to 80 s + choices | `c07_hammer_stops.md` |
| C08 | The Iron Marker | The Waystation, the Quiet Garden | Conditional payoff (Nell's burial) | 2 | 72 s | `c08_iron_marker.md` |
| C09 | The Fortune | The toll tower's roof | Act 1 closes; choice | 1 | 2 min to 2 min 17 s | `c09_fortune.md` |
| C10 | The Hollow by Night | Arena | Boss arrival and death (Greymuzzle) | 3 | 9 s + 16 s | `c10_hollow_by_night.md` |
| C11 | Raid on the Roost | Arena | Boss arrival, and death or the spared ending (Redcowl; her choice) | 3 | 10 s + 17 s or 20 s | `c11_raid_on_the_roost.md` |
| C12 | The Dig Boils Over | Arena | Boss arrival and retreat (Grimtunnel) | 3 | 9 s + 11 s | `c12_dig_boils_over.md` |
| C13 | Behind the Sealed Door | The Verge's door; arena | The door; boss arrival and kneel (the Barrow Lord) | 3 | 12.5 s + 8 s + 16 s | `c13_behind_the_door.md` |
| C14 | The Road Back | The smithy; the Low Ford road | Choice; the truth route's night (Wat; Brannoc carries Nell home) | 2 | 18 s + choice, 30 s, 10 s, 48 s | `c14_road_back.md` |

### Act 2 (outlines, `act2_outline.md`)

C20 The Ground Opens (Act 2 opens) · C21 Chapter Four (Keegan) · C22 The Letter
(Holloway) · C23 Barefoot (the boots) · C24 What He Carried (Harlan) · C25 The
Numbers (Pell) · C26 The Bandits Are the Army · C27 The Hooded Buyer (Brannoc)
· C28 The Kiln Ford (the second Unchained) · C29 Silverstair · C30 What You Are
(the turn) · C31 The War at the Gate (the climax) · C32 Come Down With Me (Act 2
closes).

### Act 3 and the endings (outlines, `act3_outline.md`)

C40 The Stair · C41 Vonnra's Truth · C42 Chid's Truth · C43 The Names (the bottom
of the stair; the reveal: ember is the dead) · C44 The Inner Door · C50 Re-forge
the Chain (five variants) · C51 Break the Chain · C52 Take the Light · C53 The
Epilogue.

## 8. Storyboard frames

Six frames in `boards/`, made on this machine with the local Krea 2 model, at
2.39:1. They are references for mood, light and framing only. The survivor in
them is a stand-in: in the game she is the player's face, hair and calling, so
build to the script, not to her. Nor are their costumes, props or architecture
canon (the script and the zone are).

| Frame | Script, shot | What it is for |
|---|---|---|
| `c01_s08_no_breath.jpg` | C01, shot 8 | The waking close-up: frost, wet hair, night, and no breath in the cold. |
| `c02_s07_lamp_to_face.jpg` | C02, shot 7 | The Warden bending to lift the lamp to her face; the drowned standing in the pool; the blue posts. |
| `c03_s08_heart.jpg` | C03, shot 8 | The heart's cold light reaching toward her hand over the water. |
| `c04_a5_first_breath.jpg` | C04, shot A5 | Dawn through the trees, and her first breath smoking. |
| `c07_s04_hammer_raised.jpg` | C07, shot 4 | Brannoc at the anvil, the hammer coming up for a stroke that will not come; the two lamp-irons by the door; the forge's light against the daylit lane. |
| `c09_s01_tower_roof.jpg` | C09, shot 1 | The roof, the lamp on the table, the town below and the dark valley. (Made before C09 was restaged: in the script Vonnra sits with her back to the town, facing the Verge.) |

## 9. Triggers, exactly

Where each cinematic starts, what is live in the game now, and what the
cinematic player replaces. "Live now" means its lines and effects are already
in play as plain captions, barks or a conversation, so the story is whole before
any cinematic exists; when the cinematic is built it takes the place of exactly
those calls. File references are `godot/logic/Play/Zones/`.

| Id | Conversation | Starts | Live now | The production agent wires |
|---|---|---|---|---|
| C01 | `cin_drowned_fire` | `Prologue.cs`, the night's first moment (stage `Wake`, where `Begin` sets the night and the objective "Survive the night"), straight after creation | Its three narrated lines as captions, in order | The cinematic in place of the three `G.Say` calls; the world held (`WorldRate` 0) with the risen mid-rise until its last shot |
| C02 | `cin_none_cross` | `Prologue.cs`, `Go(Stage.Intro)` (the approach to the ford); `RunIntro` | "Something lies in the ford..." as a caption; the evening call, "Lie down." and "NONE CROSS AFTER DARK." as the Warden's barks | The cinematic in place of `RunIntro`'s showcase and barks; the boss bar after its last shot |
| C03 | `cin_heart_goes_down` | `Prologue.cs`, `OnWardenDown`, then `RunVictory` | "Is it morning?" as the Warden's bark; the heart's caption; Grimtunnel's three barks ("Ooh, still lit!...", "...You smell like downstairs.", "...ever so grateful.") | The cinematic in place of `RunVictory`'s showcase and barks. The heart going down the hole stays in `Prologue.cs`; the cinematic only shows it |
| C04 | `cin_first_light` | Part A: `Prologue.cs`, `Douse` (the ember goes out at dawn). Part B: the first arrival at the Waystation's south gate after `prologue.done` | Part A's caption (the ember "back into the ground"; the mother's face); the guard's bark "Dawn arrivals..." | A in place of `Douse`'s caption; B on the first entry to the Waystation |
| C05 | `greymuzzle` | `Verge.cs`, interactable `greymuzzle` (Approach, while he is neutral): `G.Talk("greymuzzle")` | The conversation, as text | The cinematic staging the same conversation's choices (it is wordless) |
| C06 | `cin_forty_one_mouths` | `Verge.cs`, `Approach`, the Roost's branch when `KerchiefsFriendly()`, the first time (zone key `verge.roost_kitchen`) | The camp in a caption, the woman at the cages, and "Them first." | The cinematic in place of those three captions, ending on `G.Talk("redcowl")` |
| C07 | `brannoc` (`nell`) | Brannoc's conversation, entry `nell`: met, day 2 or later, by day, not yet asked (npc flag `asked_nell`); he asks as she walks up to the smithy | The conversation, as text | The cinematic staging the same nodes and choices |
| C08 | `cin_iron_marker` | `Waystation.cs`, interactable `burial` in the Quiet Garden: `nell.burying` (true the burial morning only, rule `nell.burial`), by day, once (zone key `waystation.burial`). After C14 it starts from the square | A caption of the garden, then the hymn as Chid's conversation | The cinematic in place of the caption and `G.Talk` |
| C09 | `vonnra` (`fortune` to `f_door`) | `Waystation.cs`, Vonnra's conversation, the choice "Tell me my fortune." (after dark, `chapter.ready`); the stinger after the `fortune` action | The conversation, as text, including the interruption at `f_below` | The cinematic staging the fortune's nodes; the stinger before `Chapter.Summary` |
| C10 | none (wordless) | Story night `hollow_by_night` (`StoryNight`, `Play/Story/Hollow.cs`): `c10_arrival` as he walks out; spent, he lies down and, where the let-go is open, she chooses; `c10_end` on his death, `c10_spared` on "Let him go" | The title card ("Who Kept the Cold Off") from `ArenaSpec.BossTitle`; the lie-down and the walk to the den as barks | The three parts on the boss hooks (section 6, 11a) |
| C11 | `cin_raid_on_the_roost` | Story fight `roost_raid`: `c11_arrival` (`bairns`); at his knee, her choice: "Finish it" plays `c11_end` (`last`), "Spare him" `c11_spared` (`spared`, `flit`) | The outcome: the fight's `OnWin` sets `redcowl.last_words` exactly as `last` does, so Rav's "the leg held" is reachable; `OnSpare` sets `redcowl` = `spared` | The parts on the boss hooks |
| C12 | `cin_dig_boils_over` | Story fight `dig_boils`: spawn (`pump`) and death, played as a retreat (`quiet`) | Nothing yet (title "Ever So Grateful") | The two parts on the boss hooks |
| C13 | `cin_behind_the_door` | The door (`c13_door`): `Verge.cs`, interactable `night:vault`, before `G.EnterArena`. Then story fight `vault_opened`: `c13_arrival` (`nondum`) up the stair, and `c13_end` when she has laid him down and he will not stay down: the hand at the gate (`redi`) | Nothing yet; the door's Latin is already in `vaultdoor` | The door before the arena; the two parts on the boss hooks |
| C14 | `cin_road_back` | Dusk: a new node `brannoc.road` (the choice). Night: a new story fight `road_back` on the Low Ford road; spawn (`wat`'s title) and the dawn win | The night's outcome as told: the morning report (`nell.burial`) tells his going alone | The node, the facts (`nell.road`, `nell.brought_home`), the story fight with Brannoc as an ally, the report's variant; then the cinematic's four parts |

Nothing else starts a cinematic. The explorer (`docs/cloud/story-explorer.md`)
plays every `cin_*` conversation that something starts, so as each trigger
above is wired, its lines leave the explorer's unreached list.
