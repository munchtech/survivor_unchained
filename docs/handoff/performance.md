# Handoff: performance lead

For a fresh successor. Read `docs/team/README.md` first, then this, then
`docs/team/performance.md` (status) and `docs/PERF_AUDIT.md` (the harness and older numbers).
Written by agent a7145e18b3eb78294 at its context limit, 2026-10-04.

## The owner's words

- "look for any optimizations we may be missing to improve performance - do not sacrifice quality at this time but we can consider it".
- The team bar: "AAA standard", "never settle", "Never claim what you haven't seen". British spelling.
- **New rule for the heroine (4 Oct, via the coordinator):** at every in-game zoom except the farthest, her breasts and buttocks stay high detail and her face must read. "If a tier must trade, it trades the world, not her."
- **Lamps (owner's decision):** the town's lamps and fires cast shadows only at dusk and by night. Done.
- **Downloads:** the owner said yes in their own chat; the coordinator installed the export templates.

## The brief

Continue the list in order:
1. Ribbons' `Buffer.Flush`. Done.
2. The stopped sweeps. Partly re-run; the GPU was never quiet.
3. The prop square size. Done: 24 m.
4. The landmark merge. Measured: worthless, and removed.
5. Load times. Prefetch built; it crashes on quit, so it's parked.
6. The quality tiers and FSR. Started.
7. The heroine's merged outfits (in at 87ad2f1). Not yet measured.

Added on the way:
- the heroine's detail check (the owner's rule);
- the legal lead's release-build blockers (debug switches, export filter, proving it with a pack listing).

Working rules:
- Commit and push your own branch at milestones; the main session merges. No PRs.
- Run `dotnet test` in `godot/tests` before every commit.
- **The GPU is shared:** only CPU-side numbers count while others render. **Right now the owner is using the GPU: no Godot, ComfyUI or Blender until the coordinator says so.**

## Done (all merged into the integration branch at 9978f337 unless marked WIP)

| commit | what | numbers (2560x1440, optimised C#) |
|---|---|---|
| cacfb96 | `Ribbons.cs`: each Buffer is one surface made once at Capacity; vertex, attribute and index regions written in place, laid out as the engine stores them (checked at start, with the old remake path as fallback); zeroed index tail; hidden when empty | dense fight: effects' garbage 53-79 KB/frame to under 2; fx main-thread time down 0.25-0.5 ms; screenshots identical in look |
| 943c56f | `Gore.cs`: decals told their size and colour only on change; settled gibs not re-placed until they sink (merged with the experience lead's settle: Still only after Settle reaches 1). `Sparks.cs` `Uploads` keeps its MultiMesh and RID, and sets the shown count only on change | fx 0.73-0.75 to 0.55-0.57 ms at 20 min |
| ce5784d | `GameHud.cs`: status and boon chips rebuilt only when the set changes, countdowns set in place. `Ornate.cs` `Globe.Changed()` redraws only on change. The UI lead agreed | HUD 0.17-0.51 to 0.05-0.08 ms/frame; its 2-3 ms spike every fifth frame gone |
| 581be7b | `Dressing.PropCell` 32 m to 24 m. `Landmarks.Merge` deleted | Waystation shadow draws 6,067-6,093 to 5,286-5,323, picture draws 341-350 to 324-326. 16 m and 48 m were worse. A/A/B shots: B differs no more than A from A. The merge saved 25 draws in the Verge and none in town, and cost 0.2-3.3 s of loading |
| 2b298e7 | Lamp shadows only at dusk and night: `ZoneView.SetDusk`, `CastsShadow`, `Shadows()`. Game tells the view of dusk at zone entry and on rest. The `hub_dusk` scenario added | town by day: shadow draws 5,350 to 1,890, renderer CPU 9-12 to 7 ms, GPU 5.7 to 3.9 ms. Dusk and night unchanged. Looked at day, dusk and night at full resolution |
| 29b5ae5b | The heroine sharp at every zoom (details below) | MSAA 4x costs 0.3-0.5 ms GPU over 2x |
| 8a770667 | Release builds: `Args.Dev` (`OS.IsDebugBuild()`) gates every developer switch in `Shots.cs`'s Args. All three presets exclude unused bodies, packs, tools and the placeholder voices. `tests/ExportTests.cs` guards the excludes | not yet proved by an export (see Next) |

**The heroine's rendering (29b5ae5b):**
- **Mipmaps.** Her textures had none: heroine.glb embeds its images, and Godot gives embedded images none, while most external ones were imported without. Every one is now lossless with mipmaps and `detect_3d/compress_to=0`.
- **The import script.** `heroine.glb.import` runs `tools_scenes/import_mipmaps.gd` to give its embedded images mipmaps.
- **Hair LODs off** (`generate_lods=false`).
- **MSAA 4x, as the project means.** High had MSAA 2x; the project's `msaa_3d=2` is 4x in Godot's count.
- **FXAA off** in `project.godot`: with TAA and MSAA it only blurred everything again.
- **Skin scattering kept at Low.**
- The face lead recorded these import settings in `docs/handoff/face.md`.

**Zooms (the game's camera range):**
- 12.5 m in conversation;
- about 23 m in town, 22 m at arena start, up to 31 m late in the arena;
- 33-34 m for the boss and after winning: the farthest.

## WIP branches (not for merging until checked)

### `perf-prefetch-wip@55c10527`: a place's scenes loaded on the worker threads first

Files: `godot/src/World/Prefetch.cs`, `People.Files(spec)`, `Dressing.Files(z)`, calls in `Game.Stage`, and `Game._ExitTree` calling `Prefetch.Release()`.

**Why.** The Waystation took 10.7-15.5 s to build; `GD.Load` was 9.8 s of it. The kits' textures are UASTC KTX2 (Zstandard), and each is decoded on the CPU as it loads, one file at a time on the main thread. The 131 scenes load in 2.3 s in parallel, against about 15 s serial.

**What it does.** `Prefetch.Zone` requests, with `ResourceLoader.LoadThreadedRequest(path, "", true)`:
- the flora and props files;
- `landmarks.glb`;
- every weapon;
- the heroine's files;
- in places with people, the whole townsfolk wardrobe (from `Lore.OutfitFor` over sex, kind, hood and pauldron, `Lore.HairStyles`, the beard and the named NPCs' specs).

It then collects everything before the build and keeps it, so people's parts are no longer loaded twice.

**Result.**
- Waystation built in 5.1 / 3.4 s (from 15.5 / 10.7); first frame at 9.9 / 8.3 s after launch (from 23.5 / 15.2).
- The Verge and the arena are 1-2 s faster.
- Screenshots show the same people, clothes and look.

**The crash.**
- At quit, about 1 run in 10: `0xC0000005` in `godotsharp_internal_refcounted_disposed` from `DisposablesTracker.OnGodotShuttingDown`.
- Counts: 2 in 10 at first, then 2 in 20 after collecting everything before building. The base build: 0 in 10.
- The latest commit (55c10527, **not yet run**) disposes the kept resources in `Game._ExitTree`, while the engine is whole. The theory: C# held PackedScenes until the engine was half torn down.

**Test.** `scratchpad/perf2/crashloop.ps1 -Build <dll dir> -Tag x -N 20`. It runs the Waystation shot 20 times and prints exit codes. The pass is 0 in 20.
- If it still crashes, run a GDScript-only hold: `load_threaded_request` and `get` on the scenes, kept in a GDScript array, then quit, 20 times.
  - If that crashes too, the threaded loader is at fault: load in parallel another way, e.g. `GD.Load` on .NET thread-pool threads.
  - If not, hold the results in a GDScript-side array rather than C#.

### `perf-tiers-wip@96067341`: Low keeps her in a sun cascade as fine as High's

- **Before:** Low used two cascades split at 7 m on a 2048 atlas, so at every play zoom she sat in a 7-70 m cascade, her shadows about four times coarser than at High.
- **Now:** a new `Tier.SunSplit` field. Low: split 0.5 (35 m), atlas 4096. High and Medium: 0.1 (Godot's default).
- **Not yet seen or measured.** Look at her at Low at 12.5, 23 and 31 m against High, and measure the GPU cost against Low as it was.

## Next, in order (when the coordinator says the GPU is free)

1. **Prefetch crash test** (above). If it's clean, merge `perf-prefetch-wip` into your branch, run the load A/B again (`run.py hub verge dense --repeat 2 --builds base=...,pre=... -- --perf-warm 3 --perf-for 2`), and commit.
2. **Release export proof** for the legal lead (aab20546fe06daa89).
   - The templates are installed at `%APPDATA%\Godot\export_templates\4.5.1.stable.mono` (28 files, SHA-512 checked by the coordinator).
   - Run `godot --headless --path godot --export-pack Windows out.zip` (a zip, so it can be listed).
   - Check that none of the excluded paths are in it (`tools_scenes`, `anime_female`, `her_Hair_*`, `woman.glb`, `woman_mask.png`, `hero.glb`, `assets/characters|props|anim/humanoid|ground/*.ktx2|people/*.bake.webp|env/polyhaven`, `art/vo`). Check that the data JSON and `art/**.json` the code reads with FileAccess do ship: `include_filter` has `data/*.json, data/*.bin, data/*.png`, but **`art/fx/sprites.json`, `art/ground/ground.json`, `art/people/outfit_materials.json`, `art/sound/sounds.json` and `art/fx/fb/*.json` may need adding to `include_filter`.**
   - Then do a full release export (`--export-release Windows`), run it, and confirm `--body hero` and `--quick` do nothing, and that the game starts and plays.
   - Send the listing to the legal lead.
   - Not yet answered: whether `art/vo/*` stays out (asked of the main session; the owner wants no placeholder voices, and subtitles still show).
3. **Tiers.** Look at `perf-tiers-wip`.
   - Medium turns MSAA off, leaving her edges to TAA. Shoot her at Medium against High at 23 m; if her rims crawl, give Medium MSAA 2x.
   - Measure each tier and FSR step with `sweep.py dense quality low,medium,high` and `sweep.py dense scale quality,balanced,performance` on a quiet GPU, and look at each at full resolution.
   - FSR can't spare her (one viewport); it stays the player's opt-in, with native as the default.
4. **Arena grass.** The arena art lead reports about 2.8M triangles. The predecessor's dense sweep, on a quiet GPU, took grass out: primitives 8.83M to 5.66M, GPU 5.72 to 4.44 ms. So grass costs about 1.3 ms of GPU and is the biggest single GPU item in the densest fight.
   - Ideas that keep the look: fewer blades out of view (the meadow is 40 m round her and the camera sees about 38x22 m at 23 m); a visibility range or a density fade with distance from her; blades culled beyond the screen; no shadows (check what they cast now).
   - Agree any visible change with the arena art lead.
5. **Her outfits** (merged at 87ad2f1: warden 5 meshes, arcanist 6, ranger 8, reaver 8). Measure `sweep.py dense off her` and town. Earlier (before the merge) she was about 105 picture draws and 244 shadow draws, and about 0.35 ms of GPU.
6. **First-launch freezes:** the VAT bakes (`user://vat`, 307 MB) and item photos, made in the first fight. Ship them pre-made or warm them at the title.
7. Remaining hot spots in the dense fight's CPU profile:
   - `Sparks.Step`: MultimeshSetBuffer copies;
   - `BattleFx.Pickups`: a Basis built per pickup per frame;
   - `GameHud.Frame`'s weapon slots: `GetChildren` each call.
   All small.

## Decisions (and why)

- **Measure at 2560x1440 windowed, vsync off, with an optimised C# build** (`dotnet build -p:Optimize=true --no-incremental -o <scratch dir>`). Interleave the builds (`run.py --builds`, `sweep.py --repeat`): CPU contention from other sessions moves renderer CPU by up to 2x from run to run.
- **Look before claiming.** `--fixed-fps 60` screenshots (`scratchpad/perf2/shot.py`, `abshots.py`) at the same moment. Take A twice to get the noise floor: moths, flames, walkers and the night watch's torch vary run to run, while the town by day without `--auto` is almost still.
- **Draw counts are exact** whatever the GPU is doing; use them to choose when the GPU is busy.
- **Invisible changes only at default settings**, or the owner's decision. Visible or unverified work goes on a WIP branch.
- **The heroine's assets keep their import settings** (lossless, mipmaps, no 3D detection, no LODs).

## Failures and why

- **The GPU was never quiet.** Use draw counts and CPU numbers; label anything else.
- **Prefetch crashes on quit.** Not yet understood; see above.
- **A cached `.godot` copied from another worktree hides import changes.** Godot judged `outfit_thread_diff.jpg` up to date and kept its old import. Delete that file's `.godot/imported/<name>-*` and re-import.
- **The sandbox refuses many shell forms:** `cd` elsewhere, variables in commands, xargs into git, complex heredocs. Write scripts with the Write tool and run them by absolute path; use the Edit tool for code.
- **dotnet-trace on the console exe times out.** Trace the GUI exe (`Godot_v4.5.1-stable_mono_win64.exe`, with `--log-file`). Keep the game alive past `--duration`, or the stacks come out unresolved.

## Gotchas

- `godot/assets` must be a junction to `public/assets`, with `git update-index --skip-worktree godot/assets`.
- Untracked `.import` files for `public/assets` gltfs are generated. Copy them from another worktree or let the import make them.
- Never commit stray `.import` rewrites, which are line endings only. Restore them with `git checkout -- "*.import"` before merging.
- `--perf-off` works only with `--perf` (its `Each` runs in Perf). For screenshots with something off, add `--perf x --perf-warm 1000`.
- `Args` now reads nothing in a release build. Everything here uses the editor binary, which is a debug build, so it's unaffected.
- `MultimeshSetBuffer` needs `InstanceCount × stride` floats; `Uploads` resizes by powers of two.
- Godot's colour vertex attribute is RGBA8 truncated, not rounded (Ribbons' `Pack` matches it).
- The arena isn't deterministic run to run even with `--fixed-fps`; the town by day without `--auto` nearly is.

## Collaborators

| who | what |
|---|---|
| Coordinator / main session | merges; relays the owner; says when the GPU is free |
| Legal lead (aab20546fe06daa89) | wants the pack listing; status `docs/team/legal.md`; spec in `docs/legal/LEGAL_BRIEF.md` issue 3 and `ASSET_PROVENANCE.md` BU-02 |
| Skills (a63cd93fc73d5ed79) | Ribbons' Buffer rewritten (Capacity still 9,000 verts); `Blades.cs` to measure |
| Face (successor to abfa9bb430ec2391e) | keeps her import settings (`docs/handoff/face.md`) |
| UI design (successor to ac76f400913a109cd) | HUD chips and globe changed (agreed) |
| Arena art | grass cost |
| Experience (a33f58e68e89e3ccf) | Gore's settle merged with my Still |

## Files to read first

- `docs/team/performance.md`
- `godot/src/Perf.cs`
- `tools/perf/run.py`
- `tools/perf/sweep.py` (`--repeat`, `flag`)
- `godot/src/Game/Graphics.cs`
- `godot/src/World/ZoneView.cs` (lamp shadows)
- `godot/src/World/Dressing.cs`
- `godot/src/Fx/Ribbons.cs`
- `godot/src/Fx/Sparks.cs` (`Uploads`)
- `godot/export_presets.cfg`
- `godot/tests/ExportTests.cs`
- on `perf-prefetch-wip`: `godot/src/World/Prefetch.cs`
- the scratch scripts (`C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf2`):
  - `shot.py`, `abshots.py`: screenshots and A/B;
  - `her_shots.py`: her at each zoom;
  - `crashloop.ps1`;
  - `prof.py`: dotnet-trace speedscope summaries;
  - `tex_imports.py`, `her_imports.py`.
