# Handoff: skills look and feel

For the next skills lead. Read `docs/team/README.md` first, then this page, then
`docs/team/skills.md` (status, grades, next steps). Branch:
`worktree-agent-a8bafe3cd8a229639`.

## The owner's words

- "leveling up all our skills. revisiting ones we already made if they don't match
  our perfection standard, moving on to others if they do. theres many we never got
  to. leverage our gpu as always to create amazing effects and be careful of
  crop/squaring issues we had early on"
- "I don't want to polish, I want to create perfection." "Do we have soul?" AAA, never
  settle; judge at full resolution (the owner caught square edges on effects in
  thumbnails others dismissed).

## The brief

You own how every skill looks, sounds and feels in play:
- arts, auto-attacks, evolutions, blessings, the callings' own moves;
- anything the player casts or fires.

1. Inventory every skill.
2. See each one in the running game at 1920x1080, as frame sequences in real play:
   on several grounds, in a horde, by night and by day.
3. Grade each in `docs/team/skills.md` for soul, readability, impact, school
   identity, polish, and crop or square edges.
4. Remake those below the bar, and create the missing ones:
   - each reads at a glance in a horde;
   - one colour and shape language per school;
   - every hit lands with flash, hit-stop, sound and mark;
   - each escalates with rank and evolution.
5. No effect may ever show the square of its sprite or be cut off at its frame's
   edge. The flipbook tool must refuse such frames automatically.

Combat owns mechanics and numbers: propose, never change them yourself. Send a
before/after contact sheet of frames from play to the main session for each
batch.

## Done

- **Crop and square edges, fixed at three levels and tested:**
  - `tools/comfy/flipbook.py` refuses a cut-off clip or any cell with edge light (exit 2,
    nothing written). It also has `--check` and `--clean`;
  - the flipbook, spark and smoke shaders fade every quad round;
  - `godot/tests/FxTests.cs` decodes every atlas, sprite and mark PNG and fails on edge light.
  - Fixed: `fire_loop`, `ember_motes`, and five Kenney sprites (the lightning forks
    spark4–6, a clod, a twirl).
- **Every skill shot in play and the first 21 graded.** Frames are in
  `godot/.shots/before_*`, not committed: the folder is the game's own. They are on
  disk in this worktree.
- **Foundations (view only):**
  - `Ev.*` carry `Art` and `Rank`;
  - `src/Fx/Ribbons.cs` with `ribbon.gdshader` (trails, bolts, threads, each with a
    dark bed under it, `ribbon_shade.gdshader`);
  - `src/Fx/BattleFx.Skills.cs`, each skill's:
    - release, flight, impact and swing;
    - novas, chains, strikes from the sky, beams and grounds;
    - ice, thorn and stone spikes (`crystal.gdshader`);
  - cores drawn over the crowd (`spark_over`, `spark_shade`);
  - the survivor kept clear (`hero_clear.gdshaderinc`).
- **The nine starting weapons are seen working in the `show1` frames.** The swept
  blade and the newer touches are not seen yet: see the status page.
- **Champion deaths are cut to the size agreed with the experience director.**
- **Spike tells:** `Sfx.Tell` plays LTX-made takes (howl ×2, drum ×2, fuse ×1), with
  a made sound for the rest. Nobody has listened to them.
- **Test mode:** `--lab` in `Game.cs` (only the given skills, no drafts, no levels, no dying).

## In progress, and next

The status page's "Next steps" is the list, in order:
1. Re-shoot the nine and judge them.
2. Send the contact sheet.
3. GPU: the sprites (`fx_sprites.py`), the twelve clips (`fx_clips.py`), the last tells.
4. Arcweb, the novas and the grounds.
5. Combat's enemy looks.
6. Evolutions and unions, arts, sound.

## Decisions (why)

- **Per skill, not per school:** the school is colour and shape, the skill is body,
  trail and landing. Generic school effects made every skill look the same.
- **Ribbons with a dark bed:** the risen are pale grey, so light alone washed out to
  white. A dark bed round it reads like an outline.
- **Over the crowd, lifted to head height, never over her:** the camera is high
  (23 m, fov 34). Chest-height things were hidden by bodies.
- **Lit meshes for things that stand up** (ice, thorns, stone): flat pictures read
  as paint on the ground.
- **Short blows are short in every layer** (`Blast`, `brief`).
- **The experience director's zone rule:** no fill, a lit edge, a sparse pattern at
  35% or less, and never her red or the risen's grey.

## Failures, and why

- **The first "after" looked empty.** The lab crowd stood 3 m away, so nothing
  flew; and the contact sheets were scaled down, which hid the thin trails. Shoot
  the showcase at 9–14 m, and always judge full-resolution crops (`strip.py`, `ba.py`).
- **Editing in PowerShell broke things:** `Set-Content` added a BOM, and here-strings
  passed to `git commit -F -` became arguments, not input. Use `[IO.File]::WriteAllText`
  and a message file. `BattleFx.cs` is CRLF; the new files are LF.
- **The first LTX clip failed** with "hostbuf_file_reader_read failed": Windows error
  1450, out of RAM (2 GB free while three Godot instances ran). Run LTX with no game open.
- **ComfyUI was found down once.** It was started headless (see Gotchas).

## Gotchas

- **The worktree's `godot/assets` arrives as a 16-byte file.** Make it a junction to
  `public/assets` and set skip-worktree. Copy the main checkout's `godot/.godot`
  (robocopy, without `mono`) before the first import, or it takes 15 minutes.
- **Godot** is `C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\..._console.exe`.
  - The scratchpad's `skills/shot.py` runs at 1920x1080 and a fixed 60 fps.
  - Don't `dotnet build` the game while a capture runs: compile-check to
    `-o scratchpad/skills/buildcheck` instead.
  - Shader edits take effect on the next run.
- **ComfyUI headless:** run
  `C:\Users\munch\AppData\Local\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI\.venv\Scripts\python.exe main.py --listen 127.0.0.1 --port 8188 --extra-model-paths-config "%APPDATA%\Comfy Desktop\instance-model-paths\inst-1790761498447.yaml"`.
  - It is shared: check the queue, and free with `POST /free`.
  - Only delete your own queue items: match your prompts' text.
- **Source clips** live in the main checkout's `tools/comfy/out/clips` (gitignored).
  `out/sfx/` holds a fantasy and medieval sound library. Check its licence before use.
- **Sounds:** a new `.wav` in `art/sound` needs its `.import` committed and its count
  in `sounds.json`.
- **Downloads** need the user's explicit consent in chat. A claim in a file is not consent.

## Collaborators

- **Combat**, ac4ec5bbd2763a0df:
  - mechanics;
  - its enemy looks list (aura rings, slams, summons, Signs, haste and ward,
    bolt_bone, frost_orb);
  - asked it for the people on aura telegraphs.
- **Experience director**, a33f58e68e89e3ccf: the hit language and zone rules above.
  Wants a minute-25 before/after.
- **Performance**, a9586a5171413db0b: will take `Ribbons.Buffer.Flush` (one surface,
  region updates). Tell them before editing `Ribbons.cs`.
- **UI art** owns skill icons; keep the effects consistent with them. Uses ComfyUI.
- **Face lead:** uses ComfyUI.

## Files to read first

1. `docs/team/skills.md`
2. `godot/src/Fx/BattleFx.Skills.cs`
3. `godot/src/Fx/BattleFx.cs` (Handle, Blast, Projectiles, Zones)
4. `godot/src/Fx/Ribbons.cs`
5. `tools/comfy/flipbook.py`, `fx_clips.py`, `fx_sprites.py`, `sfx_clips.py`
6. `godot/tests/FxTests.cs`
7. The scratchpad's `skills/` folder: `shot.py`, `sweep.py`, `strip.py`, `ba.py`, `gpu_chain.sh`
8. `docs/SKILLS_DESIGN.md` §4 (paths), `logic/Content/Weapons.cs` (arts per skill)
