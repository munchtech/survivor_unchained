# Handoff: performance lead

For a fresh successor. Read `docs/team/README.md` first, then this, then
`docs/team/performance.md` (status) and, for the harness and older numbers,
`docs/PERF_AUDIT.md`. Written by agent a56abaf3a104be675 at its context limit,
2026-10-05. (The predecessor before me was a7145e18b3eb78294.)

## The owner's words

- "look for any optimizations we may be missing to improve performance - do not sacrifice quality at this time but we can consider it".
- "we are striving for perfection". Improved is not enough: ask whether it is the best version of this in any game, and root designs in how the best games solve it.
- **The heroine:** at every in-game zoom except the farthest, her breasts and buttocks stay high detail and her face must read. "If a tier must trade, it trades the world, not her."
- **Lamps:** the town's lamps cast shadows only at dusk and by night (done earlier).
- The team bar: "AAA standard", "never settle", "Never claim what you haven't seen". British spelling.

## The brief (from the main session, 2026-10-04)

1. Release export and pack listing for the legal lead. **Done and accepted.**
2. The prefetch crash on quit; merge once fixed. **Fixed by a redesign and merged.**
3. The quality tiers (Low's shadow split, Medium's MSAA) and FSR, each looked at in full. **Done.** Medium's MSAA is with the owner.
4. The arena grass cost. **Measured.** Arena art keeps the look.
5. Measure her merged outfits. **Done.**

Working rules:
- Commit and push your own branch at milestones; the main session merges. No PRs.
- `dotnet test` in `godot/tests` before every commit.
- **Heavy work takes turns.** Run `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "performance: <job>"` before any Godot run; exit 1 means busy, so do light work. Give it back the moment you are done, and profile only while you hold a turn. A headless `--import` or `-s` script is a Godot job too.
- The GPU is shared: say which numbers it may affect, and prefer `--perf-flip`.

## Done (on `worktree-agent-a56abaf3a104be675`)

| commit | what | numbers |
|---|---|---|
| 10ab91a8 | `docs/legal/records/RELEASE_PACK_LISTING.txt` | 1,683 paths, 1.37 GB; nothing excluded ships; the release build ignores the switches and plays |
| 45cab502 | Prefetch rewritten: the kit's KTX2 textures transcoded on .NET threads (`Image.LoadKtxFromBuffer`) and put in the cache with `TakeOverPath`, let go after the build frame. Also `--perf-flip`, `tools/perf/flip.py` and `tools/godot/pack_listing.py` | quit crash 0 in 20 (the old prefetch: 3 in 11); Waystation build 10.4 to 7.0 s |
| 78776e81 | Low tier: 2 cascades split at 35 m on 4096 (perf-tiers-wip merged); `--perf-flip furshadow` | Low saves 1.8 ms against High (the old Low saved 2.3); her shadows and those near her as at High |
| 07cfa567 | status page | |
| f16890ab | Prefetch reads the scenes' dependencies on worker threads, once a session (`GetDependencies` was 0.7 s of a first entry) | Waystation 6.8-9.2 to 4.3-5.8 s; quit crashes 0 in 10 |

## Measured (2560x1440, paired flips unless marked)

- **Dense fight** (tier 3, 27.5 min, about 340 foes; High is 5.1-5.5 ms GPU):
  - Medium -1.0 ms; Low -1.8 ms.
  - FSR quality/balanced/performance: -1.4/-1.8/-2.0 ms.
  - MSAA 2x at Medium: +0.4 ms on a quiet GPU, 0.9 ms on a busy one.
  - SMAA at Medium: 0.07 ms but more shimmer, so rejected.
- **Her**, town / dense:
  - warden 0.60 / 0.68 ms;
  - reaver 0.84 / 1.06 ms (21 fur shells; 2.5M primitives);
  - arcanist 0.50 ms; stalker 0.61 ms.
  - Her fur's shadows: 0.15-0.25 ms.
  - Outfit triangles: warden 708k, ranger 651k, arcanist 436k, reaver 375k. Body 92k, long hair 173k.
- **Grass:**
  - barrow 0.72 ms (2.8M prims); hollow about 0.4 ms (0.8M).
  - Collapsing off-view tussocks in the vertex shader saved 0.03 ms, so it was reverted. The cost is the on-screen blades under MSAA.
- **Shimmer round her at 23 m** (`her_flicker.py`, pixels changing over 6 levels across 8 frames): High 2, Medium 8, Medium + MSAA 2x 5, Medium + SMAA 100. FSR doubles the mean frame-to-frame change.
- **Loads** (zone build, ms; CPU contention moves these a lot):
  - Waystation: 10.4-10.8 s (base) to 7.0 s (KTX prefetch), then 4.3-5.8 s with parallel dependency reads (uncommitted).
  - Arena: 6.5 s to 4.5-5.2 s.

## In progress: branch `perf-loads-wip@65259ada` (built and tests pass, not yet run in the game)

Merge it into your branch, take a Godot turn, verify each item, then commit or drop it.

1. (Done and committed: the parallel dependency reads, f16890ab.)
2. **`Gore.SplatTextures` and `BattleFx` Pickup/Weapon meshes made once a session.** These were 0.23 s and 0.47 s at every place entered.
   - Built, not yet run.
   - To verify: `--travel waystation@6` from an arena quick start, comparing `scratchpad/perf3/dll_travelbase` with `dll_travel`. Then look at a fight (blood, pickups, thrown axes) for sameness.
3. **`--travel ZONE@S`** (Game.cs): goes on to ZONE S seconds in, to measure a warm second build. Built, not run.
4. **`Vat.Sweep`**: older-version VAT bakes deleted before a new bake is written. Each version is about 300 MB; the shared user folder held 1.9 GB over versions 7-13. Built, not run.
5. **Photoscans (art/world/*.glb): mipmaps and BC7/BC5 at import** (`tools_scenes/import_world.gd`; the 33 `.import` files point at it).
   - Their embedded textures are RGB8 1K **without mipmaps** (probed with `scratchpad/perf3/texprobe.gd`). That should alias at a distance, but it is not yet seen in pictures, and it takes 4x the VRAM of BC7. Arena flora took 1.4-1.7 s to load.
   - `scratchpad/perf3/batch6.ps1` does the A/B; it waited 40 minutes for a turn and was stopped, so it has not run.
     - It shoots A (before the reimport) with the crowd, effects and HUD out.
     - Then it runs `--import`, shoots B, and times the arena's flora lap before and after.
     - Run it from a worktree with perf-loads-wip merged, but take the A shots with the old `.import` files' imports still in `.godot`. The import only changes on `--import`, so A comes first.
   - **Agree it with arena art** (a26767f7f9955cb56) before committing: it is a visible change, meant as a fix.

## Next, in order

1. Verify and land `perf-loads-wip` (above), then push.
2. **Her build on load** ("the survivor stood up", about 2.0-2.5 s): heroine.glb, HerOutfit, HerHair, Arms.Make. The main session replaced HideSkin with TuckSkin (a shader parameter), so re-profile after merging. `scratchpad/perf3/loadprof.ps1` profiles a build with dotnet-trace (GUI exe, inside a turn); `prof.py --thread <main> --under Game.EnterZone`.
3. **First-launch VAT bakes:**
   - The arena's kinds took 2.0 s fresh against 0.1 s cached; later kinds bake mid-fight.
   - Ideas: skin the frames on worker threads (pose on the main thread, skin in parallel; bakes must stay byte-identical); warm the bakes at the title.
   - `--vat-fresh --vat-probe --log` show per-kind times.
4. **The dense fight's main-thread spikes** (22-39 ms, one with a gen-1 GC): outside the timed parts.
5. **Arena art's Hollow by Night story place:** six deadfalls with flame sets and lights, and gate lights with flame cards. Sweep it with the story nights.
6. **Medium's MSAA:** do as the owner decides (the main session asked).

## Decisions (and why)

- **Paired flips (`--perf-flip`) for GPU costs.** The GPU is shared and plain A/B runs swing 2x. Flips put both halves under the same load. Draw counts and primitives are exact.
- **No Godot threaded loader.** `ResourceLoader.LoadThreadedRequest` with whole scenes crashed on quit, about 1 run in 4-10, in `godotsharp_internal_refcounted_disposed` at shutdown. Decode the textures ourselves; nothing held past the build frame.
- **Her detail is never traded.** No LODs on her, no fewer fur shells, her textures lossless; her outfits' triangles stay.
- **FSR stays opt-in**, native the default: it doubles the shimmer round her.
- **Low keeps High's cascade near her** for +0.5 ms against the old Low.
- **Invisible changes only** without the owner's or the owning lead's word. Visible fixes (the photoscans' mipmaps) go to the owning lead first.

## Failures and why

- **The grass early-out:** off-view geometry was already cheap. Measure before building.
- **SMAA with TAA** shimmers more than nothing: it runs on jittered frames.
- **The predecessor's `_ExitTree` Release did not fix the prefetch crash** (3 in 11): the threaded loader itself is at fault.
- **PowerShell variables are case-insensitive.** `$s` in a loop overwrote `$S`, and `$t` overwrote `$T` (the turn tool), so a turn was not given back. Use long, distinct names in batch scripts.
- **The disk filled** (0 bytes free) when my 1.4 GB export landed on a nearly full drive. Keep one export at a time and delete it once tested; check `Get-PSDrive C` before big writes.

## Gotchas

- `godot/assets` must be a junction to the worktree's `public/assets`, with `git update-index --skip-worktree godot/assets`. Copy generated `.import` files for public/assets from another worktree (`scratchpad/perf3/copy_imports.py`), or let `--import` make them.
- Restore line-ending-only `.import` rewrites with `git checkout -- "*.import"` before merging. Untracked `.import` files that the merge adds must be deleted first. Never commit the `.uid` files Godot generates.
- `godot/override.cfg` (git-excluded) gives perf runs their own user folder (`SurvivorUnchainedPerf`).
- `run.py --wait 0`: otherwise it waits up to 10 minutes for a quiet GPU.
- The release build uses `config/use_custom_user_dir` from an `override.cfg` beside the exe; put `{"fullscreen":false}` in that folder's `settings.json` for a window. `scratchpad/perf3/relplay.ps1` drives it by posted keys (no focus taken) and captures with a topmost screen copy. PrintWindow gives black for Vulkan.
- `her_shots.py` / `her_crop.py` / `her_flicker.py` (scratchpad/perf3): her at 12.5/23/31 m, crops with difference maps, and a per-pixel shimmer map.
- `--perf x --perf-warm 1000 --perf-off crowd,fx,hud` with `--shot` takes still pictures without the crowd, effects and HUD.

## Collaborators

| who | what |
|---|---|
| Main session / coordinator | merges; relays the owner; holds Medium's MSAA question; replaced HideSkin with TuckSkin |
| Legal (aab20546fe06daa89) | accepted the listing; re-list before every upload (`tools/godot/pack_listing.py`) |
| Arena art (a26767f7f9955cb56) | keeps 26 grass blades; owns the photoscans' look (agree the mipmap fix); the Hollow by Night lights |
| Skills (a94ac6b67f1279213) | BattleFx/Gore are theirs: tell them about the once-a-session meshes and splat |
| Face (a6784044c82f101d9) | her import settings stay (lossless, mipmaps) |

## Files to read first

- `docs/team/performance.md`
- `godot/src/World/Prefetch.cs`
- `godot/src/Game/Game.cs` (`MeasureWith`: `--perf-flip`, `--perf-off`; `--travel`)
- `godot/src/Game/Graphics.cs`
- `tools/perf/run.py`, `tools/perf/flip.py`, `tools/godot/pack_listing.py`
- `godot/src/Actors/Vat.cs` (cache, bake)
- scratch scripts in `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf3`:
  - `batch*.ps1` (turn-wrapped batches);
  - `crashloop.ps1`;
  - `loadprof.ps1` and `prof.py`;
  - `gshot.py`;
  - `relrun.ps1` and `relplay.ps1`;
  - `packlist.py`, `depcheck.gd`.
