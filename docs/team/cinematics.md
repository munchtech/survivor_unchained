# Cinematics: status

Agent a2dfc75e2d351105a (handed off: `docs/handoff/cinematics.md`), branch `worktree-agent-a2dfc75e2d351105a`. The brief: shooting scripts, boards and animatics for C01 to C14, and the in-engine cinematic player. Pipeline and timeline format: `docs/cinematics/shoot/README.md`.

**2026-10-04:**
- **Previs:** pass 2 is judged. Shots 3, 4, 7, 9 and 12 read; 2, 5, 6, 8, 10 and 11 need reframing (the handoff lists each fix).
- **Narration:** it is swappable. The timeline's `narrators` list and the dialogue speaker decide it, so Vonnra could voice the opening with no code change.
- **Motion list:** sent to animation.

## State (2026-10-03)

- **Cinematic player: built and working in the game.**
  - Logic, tested (`logic/Cinema`, `tests/CinemaTests.cs`, 7 tests; all 477 green):
    - the timeline format;
    - the schedule, where a shot fits its line's take, so a longer take retimes the cut;
    - a cue clock that fires every cue once, in order, whatever the frame rate;
    - the camera as a function of time: lens to horizontal FOV, moves, spline crane, push, focus, and the blend into the follow camera;
    - skip to the end, keeping what lasts.
  - The game (`src/Game/GameCinema.cs`):
    - the world is held and the controls and HUD captured;
    - the survivor is played by a double built from her loadout, with clips on the timeline's clock, face shapes, gaze, held lids, held items and props;
    - enemies are spawned into the fight;
    - lights, fire size and atmosphere follow the timeline;
    - temp cinematic SFX (`Sfx.Cine`), a music mood override, VO with subtitles in the lower bar, letterbox (`src/Ui/CinemaBars.cs`), wet bootprint decals;
    - hold-to-skip with a ring, seen-once memory in Settings;
    - the hand-back into the follow camera.
  - Debug flags:
    - `--cine ID` plays a cinematic at once;
    - `--shot NAME --until S` saves each shot's still into `godot/.shots/NAME_<id>_s<shot>_1.png`, which is the previs boards;
    - `--nocine` turns them off.
- **C01 is wired** (`Prologue.Begin`): it plays once a journey on a real new journey, not on `--quick` unless `--cine c01`. The captions remain the fallback. It runs end to end at 53.9 s with the voice's placeholders, and hands back to `Stage.Wake` with the four risen spawned.
- **C01 framing is mid-iteration.** Pass 2 of the previs was rendered (`c01_prev2.jpg` in the scratchpad) but not yet judged. In pass 1:
  - shots 10, 11 and 12 read;
  - shots 2, 3, 5, 6, 7, 8 and 9 were re-aimed (camera offsets on her head bone; shot 9 raised out of the grass).
- **Not yet written:** the shooting script docs (`shoot/c01.md` to `c04.md`), the boards, and the animatic tool (`tools/cinematics/animatic.py`, to cut boards to the timeline with VO and temp sound through `C:\Users\munch\vo-tools\ffmpeg\bin\ffmpeg.exe`).
- **Boards:** style test done. Ink and grey marker, with colour only in the light (style B, `tools/comfy` Krea 2 turbo, 1536×640, prompt expansion off). The board tool is still to write.

## Next

1. Judge the pass 2 previs, fix the framing, then write `shoot/c01.md` from the final timeline. It covers the coverage plan, the 180° line (south of her and the fire; shot 12's crane crosses it on purpose), the rhythm, and per-shot camera, blocking, performance, sound, picture and timing.
2. The boards tool plus C01 to C04 boards, then `animatic.py`, then the Prologue animatic.
3. C02 to C04 timelines and wiring:
   - C02 replaces `RunIntro`, with the Warden spawned at his end mark through an `event` cue;
   - C03 replaces `RunVictory`'s staging;
   - C04 A replaces `Douse`'s caption, and B is the first Waystation arrival.
4. Switch the fit to the voice's `read` field (`VoTake.Read`, on a501b387a90d78b4e's branch) once it is merged.

## Key decisions

- **Cues are timed from their own shot** (or from its end), and a shot can `fit` its line. Retiming is then a one-line change, and a new take moves the cut by itself.
- **The survivor in a cinematic is a double from her loadout**, and the game's figure is hidden. Her clips run on the timeline's clock (`PersonView.Cue`/`Advance`), so the performance keeps to the cut.
- **Cameras on a person are set up where the person is as the shot begins.** `"track": true` follows them instead.
- **The opening plays once a journey** (fact `prologue.woke`): a continue never replays it.
- **Board language:** monochrome ink, with colour only for the three story lights. It is consistent and quick, and it keeps the frames about staging.

## Blockers and gaps (C01, existing motion)

- **Motion:**
  - lying on the side to sitting (the existing lying poses are prone);
  - the hand to the coals;
  - the letter;
  - kneeling. Kimodo prompts are to go to animation (a1e3002b800ee55ac).
- **Set dressing:**
  - the bedroll with its folded blanket;
  - the flat stone;
  - the background items;
  - frost on the grass.
- **Systems:**
  - wetness on hair, skin and cloth;
  - breath smoke (none on her);
  - ember VFX.

## Notes for others

- **Voice (a501b387a90d78b4e):** the timing windows are agreed. `prints` is the one to shorten (9.1 s now).
- **UI:** `CinemaBars` is functional and ready for your styling: the subtitle font and size, and the skip ring.
- **Combat:** C10 to C14 need boss spawn and death hooks that can start a cinematic (`Game.Cinematic(id, done)`).
