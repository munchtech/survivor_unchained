# Cinematics: status

Agent af7a79bc783cca7bc (succeeded a2dfc75e2d351105a on 4 October), branch `worktree-agent-af7a79bc783cca7bc`. The brief: shooting scripts, boards and animatics for C01 to C14, and the in-engine cinematic player. Pipeline and timeline format: `docs/cinematics/shoot/README.md`. Handoff: `docs/handoff/cinematics.md`.

## State (4 October)

- **C01 is reframed (previs pass 3) and its shooting script is written** (`shoot/c01.md`).
  - Every shot from the handoff's fix list now reads in the engine:
    - 2 is now a top shot of her by the embers, and 4 a hand insert from above;
    - 6 to 8b are framed to her eyeline seated on the log (`her/sit_log`), until Kimodo's lying-to-sitting clips land;
    - 10 turns to R1 and stands; 11 is wide enough for all of her.
  - The story lead's call up the road is framed as 8a and 8b:
    - 8a is an ELS from the road at z 5 north to the ford's three blue lamps, with one gold lamp high over the gate;
    - the narration runs over the cut into 8b's CU, and the call comes there.
  - It runs 68.5 s with today's placeholders.
- **Frost and the trail read.** New cues:
  - `frost`: a rime in knee-deep tiles, cleared round the fire and along her `trail`;
  - `glow`: a far light, with a dark tower under it;
  - each print has a trampled patch.
- **Player:**
  - a line can run over a cut (a shot fits a line begun earlier);
  - a cue can wait for a line (`"after:conv.node+0.5"`);
  - lines are timed on the take's `read`, with the room's tail playing on.
  - The cinematic survivor also has the folk clips.
  - `--cinebones` prints bone places at each still, for framing on them.
- **`tools/cinematics/animatic.py` is written** (with `--plan`). It lays boards (or slates) on CineSchedule's clock, with VO, subtitles, temp SFX (Sfx.Cine's recipes), music beds and ambience, then encodes through ffmpeg. It has not yet been run end to end.
- **Narration:** Vonnra is not the narrator (story). C01's `narrators` holds `["narrator", "far_voice"]` (the coordinator, 535bb60), so the call up the road reads unnamed, in italics.

## Next

1. Write `shoot/c02.md` to `c04.md`. Survey each set in the engine first with `_survey.json`, which the tests skip.
2. Write `tools/cinematics/boards.py` and make the C01 to C04 boards (Krea 2 turbo, style B prefix in the handoff, 1536×640, fixed seed per shot), judged on contact sheets.
3. Cut `shoot/animatics/prologue.mp4` (C01, a card, C02, a card, C03, C04).
4. Build the C02 to C04 timelines and wire them in (C02 in place of `RunIntro`, C03 of `RunVictory`'s staging, C04 A of `Douse`, C04 B on the first Waystation arrival). C02 and C03 need the Warden under the cinematic's control (a `boss` cast kind on `WardenView`).

## Key decisions

- **Cues are timed from their own shot, and a shot fits its line.** A retime is one line, and a new take recuts itself.
- **Shots are cut to the voice lead's target windows, not to the placeholders.** A take that runs long lengthens its shot.
- **The survivor is a double built from her loadout.**
- **A camera on a person is set where the person is as the shot begins** (`track` follows them).
- **Board language:** monochrome ink, with colour only for the three story lights.
- **The opening is not played on `--quick`** (only with `--cine c01`).

## Blockers

- **Motion:** none of the C01 to C04 clips exist. All the prompts are in `tools/anim/kimodo_gen.py` (f802ed3), and they wait on the owner's Kimodo run, which the main session was asked for.
- **Voice:** C02 to C04's cinematic placeholder takes were left out of the integration branch, so in the game those lines are timed at reading pace. The takes are still on the voice branch at 7fc0013.
- **Set dressing and systems:** wetness, the weed, breath smoke, ember VFX, the bedroll, the background items, and frost that cracks.

## Notes for others

- **Voice (a501b387a90d78b4e):** the windows are agreed; C01's lamp and call windows are 8.0 to 9.0 s and 3.0 to 3.6 s.
- **UI:** `CinemaBars` is ready for your styling.
- **Combat:** C10 to C14 need boss spawn and death hooks that call `Game.Cinematic(id, done)`.
