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
- **The Prologue animatic is cut:** `docs/cinematics/shoot/animatics/prologue.mp4` (C01, C02, C03, C04 A and B, with cards for the play between). Its cut list is `prologue.txt`. It was made by `tools/cinematics/animatic.py`: boards on CineSchedule's clock, with the placeholder VO, subtitles, temp SFX (Sfx.Cine's recipes), temp music beds and ambience.
- **Boards: C01 to C04 are made** (54 frames, `shoot/boards/<id>/`, from `shoot/boards/<id>.json` through `tools/cinematics/boards.py`), in ink and grey marker with colour only in the light. Weak frames still to remake:
  - C01 s10 (she sits rather than whips round) and s11 (she is drawn twice);
  - C02 s3 (drawn as two panels) and the Warden's scale in s7 and s12 (he should be nearly three times her height);
  - C03 s6 (the heart is held in hands; it should rise alone), s11 (Grimtunnel crawls; he should dive) and s13 (she is drawn twice).
- **C02 to C04 timelines are drafts** (`c02.json`, `c03.json`, `c04a.json`, `c04b.json`, each with a `draft` note). They are cut from the written scripts for the animatic. Their cameras are unsurveyed, and they are not yet wired into the zones.
- **Narration:** Vonnra is not the narrator (story). The call up the road is subtitled "A voice up the road", never named (`far_voice` is not among C01's `narrators`).

## Next

1. Watch the animatic and judge its pacing. Remake the weak boards (listed above), then recut.
2. Survey the C02 to C04 sets in the engine (`_survey.json`; the tests skip it), set the draft timelines' cameras on what is really there, and write `shoot/c02.md` to `c04.md` from them.
3. Wire C02 to C04 into the game:
   - C02 replaces `RunIntro`. It needs a `boss` cast kind on `WardenView`, the zone's view hidden while it plays, and the `warden_up` event to spawn him at (3, -33.2).
   - C03 replaces `RunVictory`'s staging.
   - C04 A replaces `Douse`'s caption, with the `douse` event.
   - C04 B plays on the first Waystation arrival.

## Key decisions

- **Cues are timed from their own shot, and a shot fits its line.** A retime is one line, and a new take recuts itself.
- **Shots are cut to the voice lead's target windows, not to the placeholders.** A take that runs long lengthens its shot.
- **The survivor is a double built from her loadout.**
- **A camera on a person is set where the person is as the shot begins** (`track` follows them).
- **Board language:** monochrome ink, with colour only for the three story lights.
- **The opening is not played on `--quick`** (only with `--cine c01`).

## Blockers

- **Motion:** none of the C01 to C04 clips exist. All the prompts are in `tools/anim/kimodo_gen.py` (f802ed3), and they wait on the owner's Kimodo run, which the main session was asked for.

- **Set dressing and systems:** wetness, the weed, breath smoke, ember VFX, the bedroll, the background items, and frost that cracks.

## Notes for others

- **Voice (a501b387a90d78b4e):** the windows are agreed; C01's lamp and call windows are 8.0 to 9.0 s and 3.0 to 3.6 s.
- **UI:** `CinemaBars` is ready for your styling.
- **Combat:** C10 to C14 need boss spawn and death hooks that call `Game.Cinematic(id, done)`.
