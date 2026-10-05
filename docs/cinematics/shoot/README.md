# Shooting the cinematics

The written scripts (`docs/cinematics/<id>.md`) say what happens and why. The
shooting scripts here say how it is filmed, shot by shot, in the game's own
places, and each one has a timeline the game plays. The chain:

1. **Shooting script** `shoot/<id>.md`: per shot, the camera, the blocking on
   marks in the zone, the performance mapped to motion, the sound with its VO
   ids, the picture, and the timing. It also holds the coverage plan, the
   line of action, the cutting rhythm, and every change from the written
   script (with the reason).
2. **Boards** `shoot/boards/<id>/s<shot>.jpg`: a frame per shot, made locally
   with the GPU from `shoot/boards/<id>.json` (`tools/cinematics/boards.py`).
   Every frame uses the same board language: ink and grey marker, with colour
   only in the light. Warm orange is fire, pale blue is the Wardens' ember,
   and red is the ember in the survivor. A board is for staging and mood. The
   survivor in it is a stand-in, since in the game she is the player's own.
3. **Animatic** `shoot/animatics/<id>.mp4`: the boards cut to the timeline's
   own clock, with the placeholder VO, the subtitles, the temp sound and the
   temp music (`tools/cinematics/animatic.py`). It is cut from the same file
   the game plays, so the pacing judged in the animatic is the pacing the
   game gets.
4. **Timeline** `godot/data/cinematics/<id>.json`: the data the game plays
   (`logic/Cinema`, `src/Cinema`). It covers the shots, the cameras, the cast
   and its marks, and the cues.

## The timeline format

```jsonc
{
  "id": "c01", "title": "The Drowned Fire", "conversation": "cin_drowned_fire", "zone": "lowford",
  "script": "docs/cinematics/shoot/c01.md",
  "bars": { "in": 0.5, "out": 0.8 },      // letterbox ease in/out, seconds (in 0: there on the first frame)
  "skip": { "from": 1.5, "hold": 0.8 },    // hold interact/pause 0.8 s; from 1.5 s in (from 0 once seen)
  "world": { "rate": 0, "zoneHeld": true }, // Battle.WorldRate under it; the zone's director waits
  "marks": { "fire": [-10.5, 90.5], "end": [-7.5, 87.5, 3.1416] },  // [x,z] [x,z,heading] [x,h,z,heading]
  "cast": { "her": { "kind": "survivor", "mark": "lie" }, "r1": { "kind": "enemy", "def": "risen" } },
  "shots": [
    { "id": "3", "type": "CU", "dur": 4.0,
      "cam": { "pos": [-9.9, 0.25, 90.8], "at": { "actor": "her", "bone": "head" }, "lens": 85,
               "focus": { "actor": "her", "bone": "head" }, "fstop": 2,
               "move": { "push": 0.1, "start": 0, "end": "end", "ease": "linear" } },
      "fit": ["cin_x.line"],                // the shot holds to the end of this line (+ tail 0.6 s)
      "cues": [ { "at": 2.0, "do": "lids", "value": null, "over": 0.15 } ] }
  ],
  "end": { "her": "end", "camera": "follow" }
}
```

- **Times.** A cue's `at` is seconds from its shot's start, or `"end-0.8"`
  from its end, or `"after:conversation.node+0.5"`: that long after a line
  already said ends. A shot that `fit`s a line lasts at least until that
  line's take ends, plus its `tail`; the line may have begun in an earlier
  shot, so a line can run on over a cut (C01 8a to 8b). A longer take
  therefore makes a longer shot, and everything after it moves with it. The
  take's length is its `read` in `godot/data/vo/index.json` (the voice
  without the room's tail, which plays on over what follows; `sec` for a
  take made before `read` was measured). Shots are written to the voice
  lead's target windows; a take that runs long lengthens its shot. A line
  with no take is timed at a reading pace.
- **Places.** `[x, h, z]` is h above the ground. `{"abs": [x,y,z]}` is an
  exact point (use it over water). `{"mark": m, "off": [dx,dh,dz]}` and
  `{"mark": m, "y": Y}` are taken from a mark. `{"actor": a, "bone": "head"}`
  is on someone, where they are now. Headings are as `NpcActor` turns: 0
  faces south (+z), pi/2 east, pi north.
- **Camera.** `lens` is full-frame mm, used as horizontal FOV (50 mm =
  39.6°). `focus` is metres or a place, and `fstop` sets how shallow the
  focus is. `handheld` runs 0 to 1. `move` covers `pos`, `at`, `push`,
  `path` (a crane by spline), `lens`, `roll` and `focus`, with `start` and
  `end` and an `ease` (`linear`, `in`, `out`, `inout`, `slow`). With
  `"follow": true` it ends in the game's own camera on the end mark. A
  `"black": true` shot is sound over black. `"hold": true` keeps the camera
  that was there.
- **Cues** (`do`):
  - Voice: `line` (`id`: a VO id; it plays the take and puts the subtitle
    in the lower bar).
  - Places in cues are `where` (a cue's `at` is always its time).
  - Sound: `music` (`mood`, `intensity`, `over`; `"mood": "silence"` cuts it
    dead), `sfx` (`name`, optional `where`, `gain`, `pan`).
  - People: `place`, `anim` (`clip`, `from`, `speed`, `loop`, `hold`,
    `blend`), `move` (`to`, `dur`, `clip`), `look` (`where`), `hold` (a hand's
    piece, null, or `@own`), `prop` (`@weapon` set down `where`).
  - The survivor's face: `face` (`keys` of her expression shapes, `over`),
    `gaze` (`look` [x,y], `wander`), `lids` (`value`, or null to let her
    blink again), `wet`.
  - Light and air: `light` (`light`, `intensity`, `color`, `over`), `lit`,
    `fire` (the campfire's size), `atmosphere`.
  - Effects and the world: `vfx`, `prints` (wet bootprints `from` `to`,
    each with a soft trampled patch so the trail reads through frost),
    `frost` (a thin rime about `where`, `size` across, cleared within
    `radius` of `clear`; laid in knee-deep tiles so it never touches the
    trees; it stays, as the prints do), `glow` (a light seen far off: a
    point and a halo of `color` and `size`; `clear` carries it through the
    mist; `under: [w, h]` sets it on a dark tower against the sky;
    `lantern: s` builds the keeper's lamp-iron about the flame at scale `s`,
    turned `turn` degrees; `out: true` puts the flame out, keeps the iron,
    and lets a thread of smoke go up for `smoke` seconds; for this
    cinematic only), `spawn` (an enemy into the fight, `style` rise),
    `world` (`rate`).
  - Frame: `bars`, `fade`, `title` (a title card), `hide`.
  - The game: `event` (a hook in the zone's code).

  A `when` (`calling`, `background`, `hair`, `sex`, `facts`) limits a shot or
  a cue to some survivors.
- **Skipping.** A skip goes straight to the end. The cues still to come that
  last (`place`, `spawn`, `world`, `light`, `lit`, `fire`, `atmosphere`,
  `event`, `hide`) still happen, in order. Nothing that is only seen or
  heard happens. The survivor stands on `end.her`. A cue's `"skip": "apply"`
  or `"drop"` overrides this.
- **Determinism.** The same file and takes give the same schedule. The clock
  fires every cue exactly once, in order, however the frames fall, and the
  camera is a function of time alone (`logic/Cinema`, tested in
  `tests/CinemaTests.cs`).

## The scripts

State on 2026-10-04 (see `docs/team/cinematics.md`):

| Id | Shooting script | Boards | Animatic | In the game |
|---|---|---|---|---|
| C01 The Drowned Fire | `c01.md`, written from its timeline | made (`boards/c01/`); s2, s8, s8b, s10, s11, s12 to remake | in `animatics/prologue.mp4` | `c01.json` plays on a new journey; previs pass 3, stand-in motion |
| C02 None Cross After Dark | `c02.md`, written from its timeline | made; most to remake (the Warden's scale and look) | in the Prologue cut (draft cameras) | plays at the ford in place of `RunIntro`; previs pass 1, surveyed |
| C03 The Heart Goes Down | `c03.md`, written from its timeline | made; most to remake | in the Prologue cut (draft cameras) | plays where the Warden falls; previs pass 1, surveyed |
| C04 First Light | `c04a.md`, `c04b.md`, written from their timelines | made; A1, A4 to A8, B3, B4, B4b, B5 to remake | in the Prologue cut (draft cameras) | A on the north bank, B on the first arrival; previs pass 1, surveyed |
