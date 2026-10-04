# Cinematics: handoff

From agent a2dfc75e2d351105a (context full) to a fresh cinematics production lead. Read `docs/team/README.md` first, then this, then `docs/team/cinematics.md`.

## The owner's quotes

- "Time to begin scripting the writing in preparation for shooting the scenes."
- The bar: "cinematic, movie quality, soul, nothing generic". "AAA standard", "strive for excellent, above and beyond", "Do we have soul?". Never settle; remake rather than polish; verify at full resolution.

## The brief (in full)

1. **A shooting script per cinematic**, `docs/cinematics/shoot/<id>.md`, in numbered shots, each with:
   - **Camera:** framing, lens/FOV, height, the move and its timing, and the cut's motivation.
   - **Blocking:** marks in the actual zone geometry.
   - **Performance:** mapped to an existing clip, a Kimodo prompt, hand-keyed motion, or face beats.
   - **Sound:** VO ids and timing (the voice agent's ids), music, SFX and ambience.
   - **The picture:** light, atmosphere, VFX and subtitles.
   - **Timing:** duration, transitions, the skip point and the hand-back to play.

   Shoot it like a film: coverage, eyelines, and the 180° line kept or broken on purpose, with a rhythm to the cutting.
2. **Boards**, made locally on the GPU (ComfyUI at 127.0.0.1:8188 via `tools/comfy/comfy.py`), rough but clear and consistent per character. Then **animatics**: boards, plus placeholder VO, plus temp music, to check pacing before anything is built.
3. **The in-engine pipeline**:
   - a JSON timeline that drives cameras, actors, voice and subtitles, music, SFX, lights, VFX and game events;
   - letterbox, skip with a clean resume, determinism and tests;
   - wired to the triggers in `docs/cinematics/README.md` §9.
4. **First milestone:**
   - C01 and the Prologue (C02 to C04) scripted, boarded and cut as an animatic;
   - C01 playable in the game with placeholder voices and existing motion.

   Then the rest by importance (priority 1: C07 and C09).
5. **Ways of working:**
   - Coordinate by short written briefs.
   - Don't stop to ask; record decisions.
   - Use British spelling.
   - Commit and push at milestones, with tests green.
   - Wait for an empty ComfyUI queue and free its models after your batches.
6. **Latest from the coordinator:** the owner asked whether Vonnra, the hidden villain, should be the narrator who calls the survivor to town. The story lead decides, and it may change C01's voice, so build the narrator's voice to be swappable. That is done: see the decisions.

## Done

- **The player** (merged into the integration branch at 212e5bf). Its format is in `docs/cinematics/shoot/README.md`.
  - Logic in `godot/logic/Cinema`:
    - `CineFile` (the model);
    - `CinePlayer.cs`: the schedule (shots fit their line's take), the camera evaluation and the cue clock;
    - `CinePlaces` (marks, ground, actors and bones);
    - `CineLines` (lines from `dialogue.json`, VO ids, reading times).
  - Tests in `godot/tests/CinemaTests.cs`.
  - The game side, in `godot/src/Game/GameCinema.cs` (a partial of `Game`):
    - **cast:** a survivor double from her loadout, with clips on the timeline's clock (`PersonView.Cue` and `Advance`), face shapes (`People.HerFace`), gaze and held lids (`HerFaceLife.Lids` and `Snap`), held items and props, NPCs and spawned enemies;
    - **picture:** lights, fire size and atmosphere (`ZoneView.SetLevel` and `SetFire`), and wet bootprint decals;
    - **sound:** temp SFX recipes (`Sfx.Cine`), a music mood override (`SoundBridge.CineMood`), and VO plus subtitles in the bars (`src/Ui/CinemaBars.cs`);
    - **control:** hold-to-skip with a ring, seen-once memory (`Settings.SeenCinematics`), and the hand-back into the follow camera (`FollowCamera.PoseFor`).
  - Other wiring:
    - `IZoneHost.Cinematic(id, done)`, which returns false in the tests, so the zones keep their caption fallbacks;
    - `ZoneRuntime.CineEvent` for zone hooks;
    - the zone's director is held while a cinematic plays (`world.zoneHeld`).
- **C01** (`godot/data/cinematics/c01.json`) is wired in `Prologue.Begin`.
  - It plays once a journey (fact `prologue.woke`) on a real new journey. On `--quick` it plays only with `--cine c01`.
  - It runs 53.9 s with the placeholder VO and hands back to `Stage.Wake` with the four risen spawned.
- **Swappable narration:**
  - The timeline's `narrators` list (default `["narrator"]`) decides which speakers read as narration (italic, unnamed).
  - The voice is the dialogue node's speaker. A recast is a change to the speaker in `dialogue.json` and to this list; the timing follows the new take through `fit`.
  - A test holds C01's lines to its narrators.
- **Motion list and Kimodo prompts** for C01 to C04 were sent to animation (a1e3002b800ee55ac).
- **Timing windows** for all 14 Prologue lines were agreed with voice (a501b387a90d78b4e). They are written into the lines' direction and packets as targets.
- **Board style** was chosen by test. The prefix is in "Next" below.

## C01 previs: pass 2 judged (the next work)

Render with: `godot/` → `dotnet build -v q -nologo SurvivorUnchained.csproj`, then

```
C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe --path . --resolution 1920x1080 -- --quick warden --sex female --zone lowford --cine c01 --shot prev --until 58
```

This saves `godot/.shots/prev_c01_s<shot>_1.png`.

- **Good:**
  - s3, the face CU: eyes open, cheek to the ground, ember-lit;
  - s4, through the embers;
  - s7, the OTS to the north;
  - s9, the camp from the south-east;
  - s12, the crane.
- **Fix:**
  - **s2 (ECU on the stone):** black; the camera is inside geometry.
  - **s5 (insert):** the camera is inside her arm.
  - **s6:** the face is cut at the top. Pull back and up; `Crouch_Idle_Loop` is a forward crouch.
  - **s8:** the camera is too low and close, so the eyes sit at the top edge.
  - **s10:** she looks screen-right, away from R1. `her/get_up` seems to turn her (root rotation?). Put the `look` after the stand, and test the clip's facing.
  - **s11:** the camera is too low and close (head cut). Frame the pickup wider.
  - **s7:** the bootprint decals don't show. Check the `Decal` size and projection, `AlbedoMix`, the texture's alpha, and grass cover.

The camp as built:
- The fire is at (-10.5, 90.5), with a tripod and cauldron.
- The log runs north to south at x ≈ -8.4, z 89.2 to 92.6, and is a crude box (art debt).
- She lies prone at `lie` (-9.1, 91.05), heading π, head north, between the fire and the log.
- The bedroll is south-west of the fire (about (-11.6, 94.8), unverified).

## Next, in order

1. Fix the C01 framing above. Then write `shoot/c01.md` from the final timeline, covering:
   - coverage;
   - the line of action: the camera stays south of her and the fire, and shot 12's crane crosses the line on purpose;
   - the rhythm: long holds in 2 to 8, then 5.0, 2.5, 3.5, 3.5;
   - per shot: camera, blocking, performance, sound, picture and timing;
   - the changes from the written script, with reasons: shot 6 is shot from her left (the fire side) to keep the line, shot 7 is 7.5 s to hold the line, and she lies prone until `lie_side_wake` exists.
2. Write `shoot/c02.md` to `c04.md`. The written scripts already carry shot lists and coordinates; check each in the engine first with a survey timeline. Use a `_survey.json`, which the tests skip because of the leading underscore.
3. **Boards.** Write `tools/cinematics/boards.py`: a prompt per shot in `shoot/boards/<id>.json`, run through `tools/comfy/graphs/krea_t2i.json` with `30:24=false`, `30:23=false`, `30:5` at 1536×640 and a fixed seed per shot.
   - **Style prefix:** "Rough storyboard panel for a dark fantasy film, ink and grey marker sketch, quick gestural lines, flat grey tones, clear staging, monochrome except for small touches of coloured light: ".
   - Keep fixed character descriptions per person. The Warden's lamp is "a square cage of new black forged iron with a cold pale blue flame"; without this the model draws Victorian lanterns.
   - Judge the frames on contact sheets.
4. **Animatic.** Write `tools/cinematics/animatic.py`:
   - resolve each timeline exactly as `CineSchedule` does (shots plus fit, using the take lengths from `godot/data/vo/index.json`);
   - lay the boards, the VO oggs at their cue times and the subtitles;
   - add temp sound and music (numpy recipes like `Sfx.Cine`, plus `godot/art/sound` beds);
   - encode to `shoot/animatics/prologue.mp4` with `C:\Users\munch\vo-tools\ffmpeg\bin\ffmpeg.exe`.
5. **C02 to C04 timelines and wiring:**
   - C02 replaces `Prologue.RunIntro`, with the Warden spawned at his end mark by an `event` cue;
   - C03 replaces `RunVictory`'s staging;
   - C04 A replaces `Douse`'s caption, and C04 B is the first Waystation arrival.
6. Fit lines on the voice's `read` field (`VoTake.Read`) instead of `Sec` once voice's branch lands. The Warden's reverb tail is about 1.4 s.

## Decisions (why)

- **Cues are timed from their own shot, and a shot fits its line.** A retime is then a one-line change, and a new take recuts itself.
- **The survivor is a double built from her loadout,** and the game's figure is hidden (`PlayerView.Hidden`). Her performance runs on the cut's clock.
- **A camera on a person is set where the person is as the shot begins.** `"track": true` follows them instead.
- **In a cue, `at` is time and `where` is a place.** A camera's `at` is still its look target.
- **Board language:** monochrome ink, with colour only for the three story lights (fire, ford-lamp blue, ember red).
- **The opening is not played on `--quick`,** so tool runs see the game at once.

## Failures and why

- **Pass 1 framed most shots wrongly.** Bone offsets were written for a woman on her side facing west, but the only lying clip is prone, with her head north. Survey in the engine before writing numbers.
- **"at" was used for both a time and a place,** and the parser threw. Places are now `where`.
- **The constructor threw inside `Prologue.Begin`.** `Game.Cinematic` now catches it and returns false.

## Gotchas

- **The worktree sandbox refuses commands it cannot verify:**
  - shell variables used as commands;
  - `cd` chains into other worktrees;
  - inline Python heredocs with quotes.

  Write scripts to the scratchpad (`.../scratchpad/cine/`: `sheet.py` makes contact sheets, and `edit_c01.py FILE PATCH.json` patches shots and reformats) and run them plainly.
- **A fresh worktree:**
  - `godot/assets` is a 16-byte file. Replace it with a junction to `public/assets`, then run `git update-index --skip-worktree godot/assets`.
  - Robocopy the main checkout's `godot/.godot` (1.6 GB) into it, then run `--import` (about 20 minutes).
  - Never commit the `.import` and `.uid` files the import touches.
- **Cinematic camera:** `Camera.Near` is 0.04 during a cinematic (for ECUs), and it uses `KeepAspect` Width with the horizontal FOV.
- **Headings:** 0 faces south, π/2 east, π north. Verified in the engine.
- **The survivor's clips:** UAL clips play on her by name. Hers are `her/<name>`. `LayToIdle`, `Death01`, `her/death` and `her/get_up` all lie prone.
- **Timeline layout:** `tools/cinematics/timeline_fmt.py` writes the house layout, one cue to a line.

## Collaborators (roster: `docs/team/README.md`)

- **Story:** a7622ae77d19e31dc owns the text, including the Vonnra-narrator decision.
- **Voice:** a501b387a90d78b4e owns the ids, placeholders and windows.
- **Animation:** a1e3002b800ee55ac has the motion list.
- **Combat:** ac4ec5bbd2763a0df owns the boss hooks for C10 to C14 (`Game.Cinematic`).
- **UI:** a5629aff0f215ea4a styles `CinemaBars`.
- **Experience director:** a33f58e68e89e3ccf owns the pacing.

## Files to read first

1. `docs/cinematics/README.md` (§4 visual language, §5 conventions, §9 triggers)
2. `docs/cinematics/c01_drowned_fire.md` to `c04_first_light.md`
3. `docs/cinematics/shoot/README.md`
4. `godot/data/cinematics/c01.json`
5. `godot/src/Game/GameCinema.cs`
6. `godot/logic/Cinema/CinePlayer.cs`

HANDOFF READY: docs/handoff/cinematics.md on worktree-agent-a2dfc75e2d351105a (commit below)
