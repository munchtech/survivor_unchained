# Performance

Status page for the performance lead (branch `worktree-agent-a7145e18b3eb78294`).
**Handed off (context past 500k): a successor starts from `docs/handoff/performance.md`.**
Method and older numbers: `docs/PERF_AUDIT.md`. Merged with the integration branch at 9978f337; 597 tests pass.

## Current state (2026-10-04)

- **Done and merged:**
  - Ribbons rewritten (garbage 53-79 to under 2 KB/frame);
  - Gore and the effect batches send only changes;
  - the HUD chips and globe redraw only on change (0.17-0.51 to 0.05-0.08 ms);
  - props in 24 m squares (13% fewer shadow draws);
  - the landmark merge removed (it saved nothing);
  - lamp shadows only at dusk and night (town by day: shadow draws 5,350 to 1,890, GPU 5.7 to 3.9 ms);
  - the heroine sharp at every zoom (mipmaps on all her textures, hair LODs off, MSAA 4x as the project meant, FXAA off);
  - release builds ignore developer switches and exclude unused bodies, packs, tools and the placeholder voices (guarded by `ExportTests`).
- **WIP, not for merging:**
  - `perf-prefetch-wip@55c10527` cuts the Waystation load from 10.7-15.5 s to 3.4-5.1 s, but crashed on quit about 1 run in 10. A fix (let go of the fetched scenes in `Game._ExitTree`) is built but not yet run.
  - `perf-tiers-wip@96067341` gives Low a 35 m first sun cascade at 4096, so her shadows match High's. Not yet seen.
- **Waiting on the GPU** (the owner is using it): the prefetch crash test, the release export proof, the tier looks.

## Key decisions

- Measure at 2560x1440, vsync off, with optimised C#, builds interleaved. Draw counts are exact; trust CPU numbers while the GPU is shared.
- Check every change in screenshots against an A/A noise floor. Visible or unverified work goes on a WIP branch.
- The heroine's detail is never traded by a tier: her textures are lossless with mipmaps and no 3D detection, with no LODs.

## Next

See `docs/handoff/performance.md`, "Next":
1. the prefetch crash test;
2. the release export listing for the legal lead (check `art/**.json` ships);
3. the tiers;
4. arena grass (about 1.3 ms GPU, 2.8-3.2M triangles);
5. her merged outfits;
6. first-launch bakes.

## Notes for other areas

- **Main session:** confirm `art/vo/*` stays out of release builds.
- **Legal (aab20546fe06daa89):** the pack listing comes once the GPU is free.
- **Face:** keep her `.import` settings.
- **UI:** the HUD chips and globe changed (agreed).
- **Skills:** Ribbons' Capacity is still 9,000 verts per buffer.
- **Arena art:** grass is the biggest GPU item in the densest fight; any visible trim is yours to agree.
