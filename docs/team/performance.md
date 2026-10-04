# Performance

Status page for the performance lead (agent a7145e18b3eb78294, branch `worktree-agent-a7145e18b3eb78294`).
Method and older numbers: `docs/PERF_AUDIT.md`; the predecessor's handoff: `docs/handoff/performance.md`.
**Paused at the owner's request (2026-10-04); the next step is at the bottom.**

## Done this round (all pushed; 566 tests pass)

| commit | what | measured (2560x1440, optimised C#, CPU side unless said) |
|---|---|---|
| cacfb96 | Ribbons: one surface each, written in place | dense fight: effects' garbage 53-79 to under 2 KB/frame, fx 0.25-0.5 ms less |
| 943c56f | Gore and effect batches tell the engine only what changed | fx 0.73-0.75 to 0.55-0.57 ms at 20 min |
| ce5784d | HUD chips rebuilt only on change; globe redrawn on change | HUD 0.17-0.51 to 0.05-0.08 ms/frame, spikes gone |
| 581be7b | Props in 24 m squares; landmark merge removed | Waystation shadow draws 6,070 to 5,300; the merge saved nothing and cost 0.2-3.3 s of load |
| 2b298e7 | Lamp shadows only at dusk and night (owner's call) | town by day: shadow draws 5,350 to 1,890, renderer CPU 9-12 to 7 ms, GPU 5.7 to 3.9 ms |
| 29b5ae5b | Heroine detail at every zoom: mipmaps on all her textures, hair LODs off, MSAA 4x again, FXAA off, skin SSS kept at low | MSAA 4x costs 0.3-0.5 ms GPU over 2x; crops at 12.5/23/31 m crisper and steadier |
| 8a770667 | Release builds ignore developer switches; unused bodies, packs, tools and placeholder voices excluded; ExportTests guards it | not yet proved by an export (templates) |

## Key decisions

- Measure at 2560x1440, vsync off, optimised C# (`-p:Optimize=true --no-incremental`), own user folder (`godot/override.cfg`), builds interleaved. The GPU is shared: trust CPU-side numbers unless it was quiet.
- Visual checks with `--fixed-fps 60` screenshots at the same moment, A against A to get the noise floor (moths, flames and walkers vary run to run).
- The heroine (owner's rule): no tier trades her detail. Her textures are lossless with mipmaps and `detect_3d/compress_to=0`; `heroine.glb` gets its embedded images' mipmaps from `tools_scenes/import_mipmaps.gd`; her hair has no LODs.

## In progress

- **Prefetch** (`perf-prefetch-wip@25479894`, NOT for merging). Loads a place's scenes on the worker threads first. The Waystation goes from 10.7-15.5 s to 3.4-5.1 s. But the game crashes on quit about 1 run in 10 (DisposablesTracker disposing a freed RefCounted). Loading everything before the build did not fix it (2 in 20). Scripts: `scratchpad/perf2/crashloop.ps1`. The base build crashed 0 in 10.
- **Export proof** waits on the export templates (the coordinator is asking the owner). The legal lead (aab20546fe06daa89) wants the zipped pack listing.

## Next (in order)

1. **Prefetch crash.** Run the GDScript-only hold (`load_threaded_request` and get on the 131 scenes, held in a GDScript array, then quit) 20 times.
   - If it crashes, the loader is at fault: load in parallel from C# without `load_threaded_*` (`GD.Load` on .NET thread-pool threads).
   - If not, hold the fetched resources in GDScript instead of a C# dictionary.
   - Pass: 0 in 20.
2. **Export.** Once the templates are in, `--export-pack Windows out.zip`. List it, check none of the excluded paths appear and that `art/**.json` ships, then send the listing to the legal lead. Run the release build to confirm `--body hero` does nothing.
3. **Tiers.**
   - Low's sun split: two cascades put her in a 7-70 m cascade; set split 1 to about 0.5.
   - Medium's MSAA: off leaves her edges to TAA; measure 2x.
   - Then measure each tier and FSR at full resolution.
4. Heroine outfits (merged at 87ad2f1): measure `--perf-off her` against ref.
5. Load times beyond prefetch: first-launch VAT bakes and item photos.

## Notes for other areas

- **Main session:** confirm `art/vo/*` stays out of release builds (placeholder voices; the subtitles stand). FSR can't spare the heroine (one viewport), so it stays opt-in with native as the default.
- **Face lead (successor):** keep her `.import` settings as they are (`docs/handoff/face.md` records them).
- **UI:** HUD chips and globe changed in `GameHud.cs`/`Ornate.cs` (UI lead agreed): order and look unchanged.
- **Skills (a63cd93fc73d5ed79):** Ribbons Buffer rewritten; Capacity is still 9,000 verts per buffer.
