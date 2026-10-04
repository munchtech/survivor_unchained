# Handoff: the heroine's animation

For the session that carries on the character animation of Survivor
Unchained. Read this, then the files in §12. Written by the animation agent
(worktree `agent-a50313d92b0c7aba2`, branch
`worktree-agent-a50313d92b0c7aba2`) at the end of its run.

## 1. The owner's bar (quotes)

- The brief: AAA quality, **"not polish, perfection"**: motion that is
  **"weighty, characterful, readable at the game's camera"**, made for the
  heroine's body and her four callings (warden, arcanist, reaver,
  stalker/ranger).
- The test, relayed by the coordinator: **"do we have soul?"** The owner
  wants **"one game in a million, not one soulless game of many"**. For
  animation that means **"movement with personality, specific to her and to
  each calling: a signature idle, the way she draws a weapon or catches her
  breath, small human details. Stock-library motion fails, however clean.
  Hold every clip to that standard."**
- From the owner's standing memory: wants amazing, not improved; remake
  rather than skip; verify at full resolution; don't stop to ask.
- Feminine, attractive movement where it fits (hip sway, confidence)
  without losing power in combat. The game is 18+ (mature, not explicit).
- British spelling; comments are short prose that say why. Commit often;
  messages end `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## 2. The brief, in full (as given)

Own character animation. Godot 4.5.1 .NET/C# in `godot/`; repo
munchtech/survivor_unchained; commit on the worktree branch and push
(`git push -u origin HEAD`), no PR. The game uses Quaternius's Universal
Animation Library (`godot/assets/people/UAL1.glb`, `UAL2.glb`), made for
other bodies; the owner wants our own animations at AAA quality.

1. Research exhaustively (video mocap, text/audio-to-motion, libraries and
   their licences, retargeting, how Diablo IV / PoE2 / Last Epoch and
   survivors-likes build motion) into `docs/ANIM_RESEARCH.md`. Never ship
   what can't be shipped; licences in `public/assets/CREDITS.md`.
2. Design the set in `docs/ANIM_DESIGN.md` (locomotion, combat per calling
   and weapon, reactions, deaths, town and story, each calling's carriage,
   feminine movement), from what the code actually plays.
3. Build the pipeline in `tools/anim/` (source, solve or generate,
   retarget, clean up, export a Godot library, hook into the clip mapping)
   with a manifest of every clip, its source, licence and status.
4. Make the clips, judge them as an animation director from rendered frame
   sequences, wire them in with the UAL as fallback, check in the game.

Rules: keep `cd godot/tests && dotnet test` green; in `godot/src/Actors/`
change only animation mapping and playback (hair, face, skin, outfit code,
`tools/assets/` and `godot/shaders/` belong to another session); don't
rewrite story or UI; GPU shared, be considerate; no paid cloud; never print
or commit secrets. If `godot/assets` is a small text file: in PowerShell from
the worktree root `Remove-Item godot\assets; cmd /c mklink /J godot\assets
public\assets; git update-index --skip-worktree godot/assets`, then import
once (`--headless --path godot --import`).

### Later messages from the coordinator (in order)

1. Merge `origin/claude/vigilant-galileo-l6jqyx` and read
   `docs/feel/README.md` and `SUGGESTIONS.md` (a game-feel study) as input.
2. The "soul" test above.
3. (Twice) cut off by the usage limit: carry on, commit and push often.
4. New resources: **Mixamo** (the owner is signed in in the app's built-in
   browser; FBX, Without Skin, 30 fps, in place where the game handles
   root motion; priority: the clips still on the library (leap, vault, bull
   rush, chain haul) plus townsfolk and crowd motion, and anything Mixamo
   does better; retarget through the pipeline, never ship raw Mixamo files;
   record sources in the manifest and CREDITS; change nothing on the
   account). **SAM 3D Body** weights are in ComfyUI: set up video to motion
   end to end, test on a free stock clip (CC0 or Pexels/Pixabay), document
   how the owner feeds their phone video. **Kimodo**: when the owner's
   Llama 3 request is approved the token is at
   `%USERPROFILE%\.cache\huggingface\token`; set it up, else note it.
5. The owner signed into pexels.com in the built-in browser; Pexels clips
   may be downloaded for the SAM test (one person, full body, steady
   camera); note each clip's URL in the manifest.
6. Llama 3 access granted; set up Kimodo (Python 3.10-3.12 venv; never
   print the token) and use it to in-between keyed poses and to generate
   reactions and emotes where that beats keying.
7. Downloads: **the owner must click Save in the built-in browser for every
   download** (a deliberate safety gate; never script around it). Batch
   picks, send one line to the main session before each batch ("N
   downloads coming, about 2 minutes of clicking"), pick by preview and only
   fetch what will be used; prefer routes with no browser (curl from
   reputable sources, local generation). For Pexels, the owner can make a
   free API key (`PEXELS_API_KEY`) if wanted: ask the main session.
8. Hand off at the next checkpoint (this file).

## 3. Where things stand

Branch `worktree-agent-a50313d92b0c7aba2` (pushed), main branch merged in
twice; tests 435 green. Key commits, oldest first: 0f48f3d groundwork;
aa75dc7 runs and retargeting; 81073eb clips in the game; cabd0b4 axes,
daggers, dash, hit, death, casts; 3754c3a soul clips; b654e32 sprints and
stops; 9c60c05 hand cross-fade fix; 18629d8 blows from the hips; 205773d
review boards; 76a62fd SAM 3D Body and Kimodo pipelines; 0b52d8a Mixamo leap;
baacaa9 Mixamo downloads; fc10d39 library without test takes.

**In the game now** (`godot/art/anim/heroine.res`, 59 clips, all wired;
`tools/anim/manifest.json` is the list): runs ×7 and sprints ×7 (keyed by
stride, `gait.py`), stops ×8, idles ×4 (100STYLE, arms re-keyed), idle
breaks ×4, catch_breath, sit_log (title), flourishes ×4 (creation), sword
×3, axe ×3, two axes ×3, daggers ×3, throw, cast_bolt (staff), cast_flick
(wand), cast_raise, crossbow_shoot, warcry, dash, hit, death, get_up, and
**leap** (Mixamo, retimed to the Crashing Leap's 0.42 s). Boards:
`docs/anim/*.jpg`.

**How it plays**: `HerClips.cs` maps the game's clip names to hers by
calling (from her outfit) and weapon kind; `People.Clip(person, name)` is
the single call views make (UAL fallback). `PlayerView.cs` (her branch):
idle/run/sprint blend by speed with playback matched to ground speed;
swings on the upper body alternating like the arcs; Full one-shots;
her tree advanced manually on the fight clock (hit-stop holds her);
`Rest()` plays stops, idle breaks and the caught breath; `OnMuzzle`
(from `WorldScene`) plays the cast/shot/throw when a weapon looses;
`HerCarriage.cs` banks, tilts and turns her back to a blow. `PersonView`
(creation, portraits, title, reflections) plays hers too, with fidgets and
`Flourish()`. `HerPose` stands down (`Lower`/`Upper`) for her own clips.

## 4. In progress (exact state)

- **Mixamo, downloaded and converted to BVH, not yet retargeted** (all in
  `C:\Users\munch\Tools\mocap\mixamo\`, FBX and BVH side by side):
  `vault_jump_over` ("Jumping Over Into Combat"), `shield_run` ("Sword And
  Shield Run", for the bull rush), `greatsword_slide_attack` ("Great Sword
  Slide Attack", for the chain haul: she is hauled in blade first),
  `shield_death_forward` ("Sword And Shield Death", falling forward),
  `shield_impact_unblocked` ("Sword And Shield Impact"), and the townsfolk
  batch: `folk_weight_shift_idle`, `folk_talking` ("General
  Conversation"), `folk_clapping` (for the game's Cheer), `folk_pick_up`,
  `folk_sitting_chair` ("Sitting Looking Side To Side"),
  `folk_sitting_floor`, `folk_waving`, `folk_walk_feminine`. Not fetched:
  a male walk, an arms-crossed idle, any crowd/zombie motion.
- **Kimodo**: installed and working except the text encoder (see §8).
- **SAM 3D Body**: working end to end; one Pexels test clip done.

## 5. Next, in order

1. Retarget the four arts into `clips/generated.py` TABLE rows like
   `leap` (each art's timing: vault 0.32 s flight, bull rush 0.4 s at 9 m/s,
   chain haul: `Arts.cs`); choose spans by rendering the raw retarget with
   `LOOK=pelvis` first; `place="pin"`, `warp=` to fit the art; check with
   `review.py`, then in game (`--art <id> --cast T`).
2. Decide whether the Mixamo death/impact beat `death`/`hit` (keyed);
   render both side by side (`board.py`) at the `arena` view.
3. Townsfolk: build a second library on the UAL skeleton
   (`tools/anim/data/ual_skeleton.json` is already dumped; `Skeleton.load`
   takes a path; `Rig` and `retarget` work on any skeleton): e.g. a
   `build.py --skeleton ual` mode packing `godot/art/anim/folk.res`, then
   map folk names in `People.Clip`/`Resolve` for non-heroine bodies
   (Walk_Loop, Idle, Idle_B, Idle_Talking_Loop, Cheer, Interact, PickUp,
   Sit_Chair_Idle, Sit_Floor_Idle, Wave). Their pelvis rest is 0.917 m.
4. Kimodo generation once the token can be read (§8): `kimodo_gen.py`
   holds the prompts (leap, vault, bull rush, chain haul, heavy and
   directional hits, knockdown, talk, kneel, cheer, wave, shrug, bow); add
   rows to `generated.py` with `source="kimodo"`. Kimodo can also in-between
   keyed poses (full-body keyframe constraints: `--constraints`).
5. The owner's own video (SAM 3D Body): see `tools/anim/video_motion.py`'s
   docstring for how to film; add rows with `source="video"`.
6. Crowd motion is VAT-baked (`Vat.cs`); new clips there need `Vat.Version`
   bumped. Not started.
7. Polish noted in `docs/ANIM_DESIGN.md` §7.

## 6. Decisions and why

- **Clips are built on her skeleton as Godot sees it** (dumped by
  `godot/tools_scenes/anim_skeleton.gd` to `tools/anim/data/`), written as
  JSON per clip and packed by Godot (`anim_pack.gd`) into one
  AnimationLibrary. No Blender export round trip, so no axis surprises.
- **Keyed in code for combat and runs** (`keyed.py`, `gait.py`): ARPG
  attacks are hand-keyed in AAA; timing must match the game's arcs (damage,
  arc and swing start together; the arc's head crosses in 0.12 s; swings
  start cocked, cross by frame ~2.5 at 30 fps, held beat, follow-through;
  played at 1.6x). Feet and hips lead the hands (`STRIKE` lead).
- **The run is the hero clip** (she moves at 5.0-5.6 m/s nearly always):
  keyed by stride so planted feet move at exactly ground speed; playback
  matched to speed. Leans were raised after judging (13° to 32°).
- **Idles from 100STYLE (CC BY 4.0)**: real weight shift and breath; her
  back and head calibrated against the performer's own neutral standing
  (100STYLE's performer looks at the floor).
- **Licences**: rejected SMPL-based mocap (GVHMR, WHAM...), HumanML3D
  models, Bandai Namco and LAFAN1 (non-commercial), HY-Motion (VRAM,
  territory). Kimodo-SOMA-RP is commercial (NVIDIA Open Model License).
- **SAM 3D Body's rig rests along its bones' axes**, so its motion is
  retargeted from joint positions (`globals_from_positions`, profile
  `mhr`), not rotations, and grounded each frame (monocular height is
  unreliable).
- **Mixamo raw files stay out of the repo** (`C:\Users\munch\Tools\mocap\
  mixamo`), only retargeted clips ship.

## 7. Tried and failed

- Reading the HF token from this session (see §8).
- `kimodo` pip install without CMake: needs `cmake` (pip) and
  `CMAKE_GENERATOR="Visual Studio 17 2022"` (VS 2022 Build Tools present).
- Kimodo demo NPZs lack `local_rot_mats`: `kimodo_bvh.py` converts globals.
- ComfyUI `BuildPoseFile`'s dynamic combo must be flattened in API JSON:
  `"format": "bvh", "format.units": "cm"`.
- Grounding with smoothing ruined a jump (smeared flight into planted
  frames): use `ground="exact"` for game-flown jumps.
- First Pexels picks were cut off at the thigh; use full-body clips.

## 8. Gotchas

- **Hugging Face token**: `%USERPROFILE%\.cache\huggingface\token` exists
  but this session's sandbox denies reading it (even with the sandbox
  override). Kimodo's ungated parts are pre-downloaded; the Llama 3 base is
  not. Either the owner runs `python tools/anim/kimodo_gen.py` in their own
  terminal (it uses `C:\Users\munch\Tools\kimodo\.venv`, text encoder on the
  CPU), or a session that can read the token does. Then
  `python tools/anim/build.py` picks the BVHs up via `generated.py`.
- **Mixamo in the built-in browser** (`mcp__Claude_Browser__*`, tab "seed"):
  the owner is signed in. Each download needs the owner's Save click:
  batch, and `SendMessage` to `main` first. Flow per clip: navigate to
  `https://www.mixamo.com/#/?page=1&query=<q>&type=Motion`, list cards with
  JS (`.product-list .product` innerText), `find` the "Description: ..."
  item, click it, click the top Download button (stable `ref_88`), `find`
  "Download" for the dialog's button and click it. "Without Skin" and 30 fps
  persist. Files land in `C:\Users\munch\Downloads` named by the card title
  (duplicates overwrite: move each before the next with the same title).
  Then `blender -b --python tools/anim/fbx_bvh.py -- in.fbx out.bvh` (the
  BVH is at the scene's 24 fps; the loader resamples). Another agent may
  open tabs in the same pane: always pass `tabId: "seed"`.
- **Pexels**: direct `https://www.pexels.com/download/video/<id>/` with
  curl and a browser user agent works; 4K files, ~20-60 MB.
- **SAM 3D Body**: `python tools/anim/video_motion.py <video> <name>
  --start S --seconds N` (ffmpeg at `C:\Users\munch\vo-tools\ffmpeg\bin`);
  ComfyUI must be up at 127.0.0.1:8188; output joint names are
  `joint_NNN` (MHR); the mapping in `retarget._mhr_positions` was read off a
  take (eyes give facing): check it against a new rig version.
- **Godot**: the review tool (`godot/tools_scenes/anim_review.gd`, via
  `tools/anim/review.py` and `board.py`) renders in its own SubViewport, run
  with `--fixed-fps 30` (not headless). Views: front side left back three
  rthree top day arena; env `LOOK=pelvis` follows root motion, `OVER=`/
  `OVERAT=` lay a swing over a run, `DEBUG=bone` prints a bone's axes,
  `YAW=` turns her under the game cameras. Godot occasionally fails to make
  a Vulkan device when the GPU is busy: retry. Importing rewrites many
  `.import` files with LF line endings (noise: never stage them; stage
  files explicitly). `godot/assets` is a junction (skip-worktree).
- **Pose controls** (`keyed.py`): hand `arc` is about the shoulder in the
  chest's frame; `pos` is character space; keys may switch between them
  (cross-faded since 9c60c05). `blade` is the hand's +Z (thumb side, where
  a held shaft leaves the fist), `knuckles` its +Y. Leaving a turn out of a
  key means zero there; leaving a hand out means interpolated.
- **HerPose** must stand down for her clips (`Native`/`Lower`/`Upper`),
  or her pelvis is lifted twice and her arms pulled in.
- The heroine's outfit materials were reworked by another session after my
  boards: colours in old sheets differ; harmless.

## 9. Open questions

- Should Mixamo's mocap death and impact replace the keyed ones? (Render
  and judge.)
- Townsfolk: one library per sex or shared? (Folk have `look.Sex`.)
- A male townsfolk walk and an arms-crossed idle were not fetched.
- Crowd/zombie motion (VAT) is untouched.
- Would the owner provide a Pexels API key (`PEXELS_API_KEY`) or their own
  phone video for her idles (the brief's best route to "her" motion)?

## 10. Collaborators

- The coordinator / main session: address `main` with `SendMessage`.
- This agent: `agent-a50313d92b0c7aba2` (worktree and branch name).
- Another session owns hair, face, skin, outfits (`tools/assets/`,
  `godot/shaders/`, those parts of `godot/src/Actors/`).
- A cloud session wrote `docs/feel/` (game feel), merged into the main
  branch.

## 11. Commands

    python tools/anim/build.py [names]          # build clips (all, or matching) and pack heroine.res; manifest refreshed
    python tools/anim/review.py her/<clip> side three --frames 10 --step 2 --weapon sword+shield --outfit warden
    python tools/anim/board.py out.png her/a@weapon@outfit her/b ... --view arena
    python tools/anim/video_motion.py <video> <name> --start 2 --seconds 12
    python tools/anim/kimodo_gen.py [names]     # needs the HF token readable
    <blender> -b --python tools/anim/fbx_bvh.py -- in.fbx out.bvh
    cd godot/tests && dotnet test

## 12. Read first

1. `docs/ANIM_DESIGN.md` (what each clip is, §7 what is short of the bar)
2. `docs/ANIM_RESEARCH.md` (sources, licences)
3. `tools/anim/manifest.json` (every clip, source, status)
4. `godot/src/Actors/PlayerView.cs` (how she plays in the fight)
5. `godot/src/Actors/HerClips.cs` (name mapping)
6. `tools/anim/keyed.py` (the pose solver and key interpolation)
7. `tools/anim/gait.py` and `tools/anim/clips/run.py` (runs)
8. `tools/anim/retarget.py` (100STYLE, SOMA, Mixamo, MHR profiles)
9. `tools/anim/clips/generated.py` (the table for Mixamo, Kimodo, video)
10. `godot/tools_scenes/anim_review.gd` (the review renderer)
