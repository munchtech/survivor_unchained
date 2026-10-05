# Performance

Status page for the performance lead (agent a56abaf3a104be675, branch `worktree-agent-a56abaf3a104be675`).
**Handed off (context past 500k): a successor starts from `docs/handoff/performance.md`.** The method and older numbers are in `docs/PERF_AUDIT.md`.

## Current state (2026-10-05)

- **Release build: proved and accepted by the legal lead.**
  - The listing is `docs/legal/records/RELEASE_PACK_LISTING.txt`.
  - Nothing excluded ships. Every dependency and every file read with FileAccess ships.
  - The release build ignores the developer switches (`--body hero`, `--quick`, `--shot`, `--perf`) and plays.
  - `tools/godot/pack_listing.py` re-lists and checks the pack before an upload, as the checklist now asks.
- **Load times: the quit crash is fixed.**
  - The old prefetch fetched whole scenes through Godot's threaded loader and crashed on quit, 3 runs in 11.
  - Now only the kit's KTX2 textures are transcoded, on .NET threads, and handed to the resource cache.
  - Quit crashes: 0 in 20, the same as the base build.
  - Waystation build: 10.4-10.8 s down to about 7 s; with the dependency reads in parallel (f16890ab), 4.3-5.8 s.
  - Arena build: 6.5 s down to 4.5-5.2 s.
  - The prefetch WIP branch is merged and replaced.
- **Low tier:** her shadows now match High's (merged from perf-tiers-wip). It costs 0.5 ms more than the old Low, and Low still saves 1.8 ms against High.
- **WIP, not for merging until verified:** `perf-loads-wip@65259ada`.
  - Effects' meshes and blood splat made once a session (0.7 s at each place entered).
  - `--travel ZONE@S`.
  - Older VAT bakes swept (1.9 GB on this machine).
  - Mipmaps and BC7/BC5 for the photoscans. Their textures have no mipmaps (probed); not yet seen in pictures. Agree this with arena art.
- **Paired measurement on a shared GPU.** `--perf-flip X` takes X out every other second, and `tools/perf/flip.py` reads both halves of the same run.

## Measured (2560x1440, paired flips; "dense" is tier 3 at 27.5 min, ~340 foes)

| what | GPU cost | notes |
|---|---|---|
| Medium vs High | -1.0 ms | |
| Low vs High | -1.8 ms | the old Low: -2.3 ms |
| FSR quality / balanced / performance vs native | -1.4 / -1.8 / -2.0 ms | her frame-to-frame flicker doubles (0.29 to 0.55-0.64), so FSR stays opt-in |
| MSAA 2x at Medium | +0.4 ms (quiet GPU) to +0.9 ms (busy) | her edges nearly as steady as High's: 5 flickering pixels against High's 2 and plain Medium's 8 |
| SMAA at Medium (with TAA) | +0.07 ms | worse: 100 flickering pixels. SMAA on jittered frames fights TAA. Rejected |
| her, by calling (town / dense) | warden 0.60/0.68, reaver 0.84/1.06, arcanist 0.50, stalker 0.61 ms | reaver: 21 fur shells, 2.5M primitives |
| her fur's shadows (reaver) | 0.15-0.25 ms | 42 shadow draws |
| grass (barrow, 2.8M prims / hollow, 0.8M) | 0.72 / 0.4 ms | off-view tussocks cost nothing (an early-out saved 0.03 ms, so it was removed) |

## Key decisions

- **Measure with paired flips while the GPU is shared.** Draw counts are exact. Plain A/B GPU numbers swing by 2x.
- **Load by decoding textures ourselves, not with Godot's threaded loader.** The threaded loader crashed on quit in 4.5.1, and identical textures come from the same transcoder.
- **Her detail is never traded by a tier.** Her outfits are 375k-708k triangles with no LODs. That is kept: the owner's rule.
- **Heavy work takes turns** (`tools/turn.py take godot`), and profiling happens only while holding one.

## Next

1. **Medium's edges: the owner's call** (asked of the main session). Without MSAA, her hair rims and sword shimmer a little at 23 m (8 pixels against High's 2). MSAA 2x fixes most of it (5) but costs 0.4-0.9 ms, about half of what Medium saves. It is unchanged until decided.
2. Verify and land `perf-loads-wip` (how: `docs/handoff/performance.md`, In progress).
3. Load: her build ("the survivor stood up", 2.0-2.5 s; re-profile after the main session's TuckSkin), and the arena's flora (1.4-1.7 s: the photoscans).
4. First-launch VAT bakes: 2.0 s fresh against 0.1 s cached at the arena's start, and more mid-fight.
5. Hitches in the dense fight: a 22-39 ms main-thread spike now and then (one with a gen-1 GC), outside the timed parts.
6. Arena art's Hollow by Night story place: six deadfalls with lights, and gate lights.

## Notes for other areas

- **Legal:** re-list the pack before every upload with `python tools/godot/pack_listing.py Windows`.
- **Arena art:** grass costs 0.72 ms in the barrow; your call on the blade count. The photoscans' textures (art/world) have no mipmaps: probed as RGB8 1K, none. Read from 20-50 pixels away, they should alias, though I haven't yet seen it in pictures. A fix waits on `perf-loads-wip` for your word.
- **Skills:** BattleFx's pickup and weapon meshes and Gore's splat are made once a session on `perf-loads-wip` (0.7 s at each place entered).
- **Main session / heroine outfits:** her outfits are heavy (warden 708k triangles, ranger 651k). She costs 0.5-1.1 ms of GPU. Nothing is traded, as the rule says.
