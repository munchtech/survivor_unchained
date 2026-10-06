# Performance

Status page for the performance lead. The last lead was agent a0eb8c612c94d4aa5 on branch `worktree-agent-a0eb8c612c94d4aa5`. **Handed off at its context limit (2026-10-06): a successor starts from `docs/handoff/performance.md`.** The method and older numbers are in `docs/PERF_AUDIT.md`.

## Current state (2026-10-06)

- **Top priority (the owner):**
  1. Her blur in motion: "we are blurry when moving in active action gameplay".
  2. The see-through-trees dither is "pedestrian in its pixelation".

  Not started; the brief and leads are in the handoff.
- **Landed this round** (optimised C#, 2560x1440):
  - **The photoscans' mipmaps and BC7/BC5** (`tools_scenes/import_world.gd`, agreed by arena art).
    - Invisible at the game camera.
    - Arena VRAM drops 2,226 to 1,998 MB; its flora lap drops 1.5-2.2 s to 0.9-1.0 s.
  - **Effects' meshes and the blood splat made once a session:** a second entry's stage drops 0.5-0.84 s to 0.15-0.18 s.
  - **Old VAT bakes swept** (903 MB). **`--travel A@S,B@S`** chains entries.
  - **VAT bakes skinned on worker threads,** byte-identical across seven kinds: the arena's wolf and boar together drop 1.8-1.9 s to 0.44-0.49 s on a first launch.
  - **The Risen's first bakes** drop 5.1-5.4 s to 2.7-2.8 s: their kit textures are decoded first (`Prefetch.Scenes`).
  - **Her body held for the session:** her re-entry build drops 0.3-0.5 s to 0.
  - **Garbage in the dense fight** drops 30 to 17 KB a frame, with GCs 7-8 down to 5 in 40 s:
    - the synth's buffers are kept;
    - per-frame StringNames are made once;
    - the painted UI frames are read at start, so the first draft no longer holds 13-80 ms.
- **Medium stays without MSAA (closed).** The owner took the main session's recommendation.

## Measured (dense = tier 3 at 27.5 min, about 340 foes)

| what | cost | notes |
|---|---|---|
| Medium / Low vs High | -1.0 / -1.8 ms GPU | |
| her (warden, dense) | 0.71 ms GPU, 0.96M primitives | `--perf-flip her`; kept, by the owner's rule |
| loot's ground labels | 0.03-0.13 ms main, no GPU | `--perf-flip labels` |
| Hollow by Night | pieces 1.15 ms GPU (1.48M primitives); fires and lamp shadows are within noise | 625 shadow casters, 40k instances |
| her first build | body 0.5, materials 0.2-0.27, clips 0.15, outfit 0.5-0.7, hair 0.25-0.33 s | first entry only now |
| arena first entry, cached bakes | 3.6-5.0 s | |

## Key decisions

- **Paired flips (`--perf-flip`) for GPU costs:** the GPU is shared. Kept C# builds for A/B: `dotnet build -p:Optimize=true --no-incremental -o <dir>`.
- **No Godot threaded loader.** It crashed on quit; we decode on .NET threads ourselves. The quit check is 0 in 10.
- **Her detail is never traded,** and her textures stay lossless.
- **Invisible changes only,** unless the owner or the owning lead agrees.
- **Dropped:**
  - the GC's larger young generation (`DOTNET_GCgen0size`): inconclusive, one 172 ms pause;
  - holding the kit's people's scenes: no gain on a first entry.

## Next

1. **Her blur, then the see-through cut-out** (handoff, "Top priority").
2. **A queued draft rebuilds its whole panel at every pick** (15-20 ms each; the autopilot shows it as 10-70 ms). Reuse the panel (UI design owns it).
3. **First bakes still left:**
   - `skeleton_rogue` (`GenerateLods` on the kit meshes, 0.4-1.1 s);
   - bake at the title, or ship the bakes.
4. Loot's beams: measure them once the loot lead's successor lands their final look.

## Notes for other areas

- **Arena art (paused):**
  - The photoscans' mipmaps have landed; re-shoot after merging and run `--import` once.
  - Hollow by Night's pieces cost 1.15 ms of GPU (1.48M primitives): give them a visibility range or LODs when you're back.
  - The see-through-trees effect (`shaders/kit.gdshader`, `hero_clear.gdshaderinc`) is being remade by performance as a soft, round, feathered cut-out with no dither. The trees' look is yours, so it will be shown to you first.
- **UI design:** the draft panel is rebuilt whole at every queued pick (`GameMenus.Present`), 15-20 ms a time.
- **Creatures:** the boar's normal map goes in as a compile-time `VAT_NORMAL` variant. Send `--perf-flip` numbers.
- **Skills:** BattleFx's pickup and weapon meshes and Gore's splat are made once a session (`BattleFx.Kept`).
- **Legal:** re-list the pack before every upload: `python tools/godot/pack_listing.py Windows`.
