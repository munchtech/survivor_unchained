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
- **Boards for C01 to C04** (54 frames) are in `shoot/boards/<id>/s<shot>.jpg`, made by `tools/cinematics/boards.py` from `shoot/boards/<id>.json`. That file holds a fixed description per person, put in with `{name}`, and a seed per shot. The style is ink and grey marker, with colour only in the light. The weak frames still to remake are listed on the status page.
- **The Prologue animatic:** `docs/cinematics/shoot/animatics/prologue.mp4`, with its cut list in `prologue.txt`. It runs C01, C02, C03, C04 A and C04 B, with cards for the play between them.
- **C02 to C04 draft timelines** (`godot/data/cinematics/c02.json`, `c03.json`, `c04a.json`, `c04b.json`):
  - They are cut from the written scripts, so the animatic plays the game's own clock.
  - Each carries a `draft` note. Their cameras are not surveyed in the engine.
  - They are not wired into the zones yet, so nothing starts them.
  - C04's two parts share `cin_first_light`. The line-order test reads a conversation across its parts, in id order.

## Next, in order

1. **Judge the animatic.** Watch it at full size, judge the pacing against the windows, then remake the weak boards and recut. To remake one, edit its prompt and run `python tools/cinematics/boards.py <id> --only <shots> --sheet <out.jpg>`.
   - The model draws a person twice when that person's description is long and the shot is wide. Name one person only ("one woman only"), and say "a giant nearly three times her height" for the Warden.
   - Recut with:

     ```
     python tools/cinematics/animatic.py c01 "card:..." c02 "card:..." c03 "card:..." c04a "card:..." c04b --crf 28 --out docs/cinematics/shoot/animatics/prologue.mp4
     ```

     The exact cards are in `prologue.txt`.
2. **Survey C02 to C04 in the engine,** then set the drafts' cameras on what is really there, and write `shoot/c02.md` to `c04.md` from the final timelines.
   - Render with `python <scratchpad>/cine/prev.py <id> <name> <until> [--zone Z] [--cols 2 --width 760]`. It saves a contact sheet in the scratchpad.
   - Or by hand:
     1. In `godot/`, run `dotnet build -v q -nologo SurvivorUnchained.csproj`.
     2. Then run `Godot_v4.5.1-stable_mono_win64_console.exe --path . --resolution 1920x1080 -- --quick warden --sex female --zone lowford --cine <id> --shot <name> --until <s> --cinebones`.
   - C04 B is in the Waystation, so use `--zone waystation`.
3. **Put animation's first three C01 clips on the timeline** (on worktree-agent-a1e3002b800ee55ac@809c358: merge it once the main session has, or ask):
   - `her/lie_side_wake` (7 s): she lies on her right side, head toward -X, facing +Z, and comes up onto her right elbow, held. The face close-up is from +Z.
   - `her/sit_back_heels` (6 s): from that pose to kneeling on her heels, facing +Z, hands palm up before her lap.
   - `her/reach_coals` (4.2 s): from there, the right hand goes out low, palm down, and is held.

   With these she wakes on her side facing the fire and kneels, instead of sitting on the log. To re-block shots 2 to 8b round them:
   - set her `lie` heading so that +Z faces the fire;
   - re-survey with `--cinebones`;
   - tell animation's successor what the clips need.
   Animation's successor (a435f4dd0ac80df75) has also pushed three gestures, at worktree-agent-a435f4dd0ac80df75@d7b091e. Each plays over whatever she is doing, cued as `{"do": "anim", "clip": "her/nod"}`. On a gesture, `speed` scales it, and `from` and `blend` are ignored.
   - `her/nod` (1.0 s): for C03 3b.
   - `her/exhale` (1.5 s): it holds the settled shoulders until her next clip cue that isn't a gesture. Use it in C01 shot 8 at 1.2 s, under the face's `mouth_open` and `brows_sad`, and in C04 A5.
   - `her/shiver` (1.1 s): for C04 A5.
4. **Wire C02 to C04 into the zones:**
   - **C02** replaces `Prologue.RunIntro`.
     - Add a `boss` cast kind that builds a `WardenView` (`src/Actors/BossViews.cs`; its inner `PersonView` plays clips).
     - Hide the zone's own `wardenView` while it plays.
     - Its `warden_up` event (`ZoneRuntime.CineEvent`) spawns him at (3, -33.2).
   - **C03** replaces `RunVictory`'s staging. Keep its `G.Apply` effects in code at the hand-back, so a skip sets them too.
   - **C04 A** replaces `Douse`'s caption. Its `douse` event calls `Douse`.
   - **C04 B** plays on the first Waystation arrival.
## Decisions (why)

- **Cue timing and fit.** Cues are timed from their own shot, and a shot fits its line, so a new take recuts itself.
- **Cut to the windows.** Cut to the voice lead's target windows, not to the placeholders, because the owner's takes aim at those windows.
- **The survivor's double.** The survivor is a double built from her loadout, and her clips run on the cut's clock.
- **Cameras on a person** are set up where the person is at the shot's start; `track` follows them.
- **C01 blocking.** She sits on the log from shot 6 until `lie_side_wake` and `sit_back_heels` exist. The cut from 5 hides the change, and every face shot is framed to that eyeline.
- **C01's shot 2** is a top shot, not the stone ECU. The ECU camera sat inside the fire ring, and the top shot says more.
- **The frost** is laid as decals in 6 m tiles, each 1.4 m deep, so it whitens grass and earth and never the trees. The trail is cleared in it, so the prints read from far off as a line.
- **Vonnra is not the narrator** (the story lead). She has one unnamed call in C01, subtitled "A voice up the road" (`far_voice` is not a narrator): the narrator never speaks a person's words.

## Failures and why

- **Prints didn't show.** Dark decals on dark night grass are invisible. Fix: put the frost under them, and clear the trail through it.
- **The first frost decal (44 m, 8 m deep) whitened the trees.** Fix: tiles, each only knee-deep.
- **The `after:` parser cut at the wrong sign.** Ids contain no signs, so the offset starts at the first sign after the conversation's dot.
- **A wait clamped to the written length** before the shot was fitted. Waits are now unclamped while the schedule lays out the lines.
- **PowerShell `Set-Content -Encoding utf8` wrote a BOM into a C# file.** Write with `[IO.File]::WriteAllText`.

## Gotchas

- **Stage directions show in subtitles.** C02's W1 subtitle shows "(sung, under the water)", because the direction is part of the line's text. Ask the story lead to move it into the line's direction, or strip parentheses in `CinemaBars.Say`.

- **Never commit the `.import` and `.uid` files** that the import touches. About 1000 of them are dirty in this worktree. Add files by name.
- **The worktree's `godot/assets`** is a junction to `public/assets`, marked skip-worktree.
- **The untracked `godot/art/vo/<voice>/` folders** hold the voice branch's other placeholders (Rook, Brannoc and the rest). Never commit them: the owner said "no more placeholders ... keep cinematic voice". Only the cinematics' takes are in the repo.
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

HANDOFF READY: docs/handoff/cinematics.md on worktree-agent-af7a79bc783cca7bc (the commit after 8f9f38e)
