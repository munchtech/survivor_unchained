# Cinematics: handoff

From agent af7a79bc783cca7bc (who took over from a2dfc75e2d351105a) to a fresh cinematics production lead. Read `docs/team/README.md` first, then this page, then `docs/team/cinematics.md`.

## The owner's quotes

- "Time to begin scripting the writing in preparation for shooting the scenes."
- The bar: "cinematic, movie quality, soul, nothing generic". "AAA standard", "strive for excellent, above and beyond", "Do we have soul?". Never settle; remake rather than polish; verify at full resolution.
- The structure: story is about 40% of the game early on, and the cinematics carry much of it, "so make them count".
- On voice: "no more placeholders ... keep cinematic voice". Finals come from ElevenLabs.

## The brief, in full

1. **A shooting script per cinematic,** `docs/cinematics/shoot/<id>.md`, in numbered shots. Each shot gives:
   - the camera (framing, lens, height, move, cut motivation);
   - the blocking (marks in the real zone);
   - the performance (an existing clip, a Kimodo prompt, hand-keying, or face beats);
   - the sound (VO ids, music, SFX);
   - the picture (light, atmosphere, VFX, subtitles);
   - the timing.

   Shoot it like a film: coverage, eyelines, and the 180° line kept or broken on purpose.
2. **Boards,** made locally on the GPU with ComfyUI (`tools/comfy/comfy.py`), in ink and grey marker with colour only on light sources.
3. **Animatics:** boards, placeholder VO and temp music, cut to check pacing.
4. **The in-engine pipeline:** JSON timelines, wired to the triggers in `docs/cinematics/README.md` §9.
5. **First milestone:** C01 and the Prologue (C02 to C04) scripted, boarded, cut as an animatic, and playable. Then the rest by importance (C07 and C09 first).
6. **Ways of working:** don't stop to ask; use British spelling; keep tests green; commit and push at milestones. Wait for an empty ComfyUI queue and free its models after your batches. Ask the main session to have the owner run Kimodo when prompts are ready.

## Done

- **The player** (`godot/logic/Cinema`, `godot/src/Game/GameCinema.cs`, tests in `godot/tests/CinemaTests.cs`), with these additions this session:
  - **Lines over cuts.** A shot can `fit` a line begun in an earlier shot, and a cue's `at` can be `"after:conv.node+0.5"`.
  - **Timing on `read`.** Lines are timed on the take's `read` (`CineLines.Seconds`), so the reverb tail plays on over what follows.
  - **New cues:**
    - `frost`: a rime in tiles, cleared round a fire and along a `trail`;
    - `glow`: a far light, with `under` for a dark tower beneath it;
    - prints now carry a trampled patch each.
  - The cinematic survivor carries the folk clip library too (`folk/f_sit_floor`, and others).
  - `--cinebones` prints bone positions at each still, which is what to frame on.
- **C01:**
  - the timeline is reframed (pass 3), and every fix from the old list reads in the engine;
  - the story lead's shots 8a and 8b are framed;
  - the shooting script is written (`shoot/c01.md`);
  - it runs 68.5 s.
- **`tools/cinematics/animatic.py`** is written. `--plan` prints the schedule (it matches the game's: 68.5 s). The full render has not been run yet. It needs boards, or it shows slates.

## Next, in order

1. **`shoot/c02.md` to `c04.md`.** The written scripts carry shot lists and coordinates. Check them in the engine first with `godot/data/cinematics/_survey.json`, which the tests skip.
   - Render with `python <scratchpad>/cine/prev.py <id> <name> <until> [--zone Z] [--cols 2 --width 760]`; it saves a contact sheet in the scratchpad.
   - Or by hand: `godot/` → `dotnet build -v q -nologo SurvivorUnchained.csproj`, then `Godot_v4.5.1-stable_mono_win64_console.exe --path . --resolution 1920x1080 -- --quick warden --sex female --zone lowford --cine <id> --shot <name> --until <s> --cinebones`.
2. **`tools/cinematics/boards.py`** writes a prompt per shot to `shoot/boards/<id>.json`, run through `tools/comfy/graphs/krea_t2i.json` with these settings:
   - `30:24=false` and `30:23=false` (no prompt expansion);
   - `30:5` at 1536×640;
   - `30:3` with a fixed seed per shot;
   - the prompt in `30:19`, and `29` as the filename prefix.

   The style prefix: "Rough storyboard panel for a dark fantasy film, ink and grey marker sketch, quick gestural lines, flat grey tones, clear staging, monochrome except for small touches of coloured light: ".
   - Keep a fixed description per person.
   - The Warden's lamp is "a square cage of new black forged iron with a cold pale blue flame". Without that, the model draws Victorian lanterns.
   - Save each board as `shoot/boards/<id>/s<shot>.jpg`.
   - Judge them on contact sheets (`<scratchpad>/cine/sheet.py`).
   - `<scratchpad>/cine/style_test.py` is a working example of driving the graph.
3. **Cut the animatic:**

   ```
   python tools/cinematics/animatic.py c01 "card:..." c02 "card:..." c03 c04a c04b --out docs/cinematics/shoot/animatics/prologue.mp4 --index <a voice index with the C02 to C04 takes>
   ```

   - Integration's `godot/data/vo/index.json` now lists only C01's takes.
   - For C02 to C04, write the voice branch's index to a file (`git show 7fc0013:godot/data/vo/index.json`, saved as UTF-8) and pass it with `--index`.
   - The oggs are untracked in this worktree under `godot/art/vo/<voice>/`.
   - Review the cut list (`prologue.txt`) and watch the film before you report it.
4. **C02 to C04 timelines, then wiring:**
   - C02 replaces `Prologue.RunIntro`.
     - It needs the Warden under the cinematic's control. Add a `boss` cast kind that builds a `WardenView` (`src/Actors/BossViews.cs`; its inner `PersonView` plays clips) and hides the zone's own `wardenView` while it plays.
     - An `event` cue (`ZoneRuntime.CineEvent`) spawns the boss at its end mark (3, -33.2).
   - C03 replaces `RunVictory`'s staging. Keep its `G.Apply` effects in code at the hand-back, so a skip sets them too.
   - C04 A replaces `Douse`'s caption.
   - C04 B plays on the first Waystation arrival.

## Decisions (why)

- **Cue timing and fit.** Cues are timed from their own shot, and a shot fits its line, so a new take recuts itself.
- **Cut to the windows.** Cut to the voice lead's target windows, not to the placeholders, because the owner's takes aim at those windows.
- **The survivor's double.** The survivor is a double built from her loadout, and her clips run on the cut's clock.
- **Cameras on a person** are set up where the person is at the shot's start; `track` follows them.
- **C01 blocking.** She sits on the log from shot 6 until `lie_side_wake` and `sit_back_heels` exist. The cut from 5 hides the change, and every face shot is framed to that eyeline.
- **C01's shot 2** is a top shot, not the stone ECU. The ECU camera sat inside the fire ring, and the top shot says more.
- **The frost** is laid as decals in 6 m tiles, each 1.4 m deep, so it whitens grass and earth and never the trees. The trail is cleared in it, so the prints read from far off as a line.
- **Vonnra is not the narrator** (the story lead). She has one unnamed call in C01. The coordinator made it read as narration (535bb60).

## Failures and why

- **Prints didn't show.** Dark decals on dark night grass are invisible. Fix: put the frost under them, and clear the trail through it.
- **The first frost decal (44 m, 8 m deep) whitened the trees.** Fix: tiles, each only knee-deep.
- **The `after:` parser cut at the wrong sign.** Ids contain no signs, so the offset starts at the first sign after the conversation's dot.
- **A wait clamped to the written length** before the shot was fitted. Waits are now unclamped while the schedule lays out the lines.
- **PowerShell `Set-Content -Encoding utf8` wrote a BOM into a C# file.** Write with `[IO.File]::WriteAllText`.

## Gotchas

- **Never commit the `.import` and `.uid` files** that the import touches. About 1000 of them are dirty in this worktree. Add files by name.
- **The worktree's `godot/assets`** is a junction to `public/assets`, marked skip-worktree.
- **The untracked `godot/art/vo/<voice>/` folders** are the voice branch's placeholders. They are for the animatic only; don't commit them (the owner's call).
- **Headings:** 0 faces south, π/2 east, π north. Her prone lie has her head north.
- **The zone title "THE LOW FORD ROAD"** shows over early previs stills in a survey. It doesn't show in `c01` (the zone announce waits for `Woken`).
- **ComfyUI is shared** with the voice lead's runs. Check `/queue` before a batch, and POST `/free` after.

## Collaborators (the roster is in `docs/team/README.md`)

- **Story:** a035208561a66c171 (succeeded a7622ae77d19e31dc). Send them one line per problem: a line that fights a shot, a beat that needs a line, or a picture that breaks the bible.
- **Voice:** a501b387a90d78b4e. The windows are agreed: C01 lamp 8.0 to 9.0 s, call 3.0 to 3.6 s; C02 to C04 as in `docs/team/voice.md`.
- **Animation:** a1e3002b800ee55ac. Every prompt is written; it waits on the owner's Kimodo run.
- **Combat:** ac4ec5bbd2763a0df, for the boss hooks for C10 to C14.

## Files to read first

1. `docs/cinematics/shoot/README.md` and `shoot/c01.md`
2. `docs/cinematics/c02_none_cross.md`, `c03_heart_goes_down.md` and `c04_first_light.md`
3. `godot/data/cinematics/c01.json`
4. `godot/src/Game/GameCinema.cs` and `godot/logic/Cinema/CinePlayer.cs`
5. `godot/logic/Play/Zones/Prologue.cs` (`StartIntro`, `RunIntro`, `OnWardenDown`, `RunVictory`, `Douse` and `Begin`)
6. `tools/cinematics/animatic.py`
