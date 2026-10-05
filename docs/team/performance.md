# Performance

Status page for the performance lead (agent a0eb8c612c94d4aa5, branch `worktree-agent-a0eb8c612c94d4aa5`; took over from a56abaf3a104be675 on 2026-10-05). The handoff is `docs/handoff/performance.md`; the method and older numbers are in `docs/PERF_AUDIT.md`.

## Current state (2026-10-05)

- **Release build: proved and accepted by the legal lead.** The listing is `docs/legal/records/RELEASE_PACK_LISTING.txt`; `tools/godot/pack_listing.py` re-lists and checks it before an upload.
- **Loads (perf-loads-wip, verified and landed):**
  - **The photoscans (art/world/*.glb) now have mipmaps and BC7/BC5** (`tools_scenes/import_world.gd`). Arena art agreed after before/after pictures. At the game camera (23 and 31 m) the difference is about 1/255, invisible.
    - The arena's VRAM drops 2,226 to 1,998 MB.
    - The arena's flora lap drops 1.5-2.2 s to 0.87-1.02 s, from three interleaved runs each.
  - **Effects' meshes and the blood splat are made once a session.** A second entry's "rest of the stage" drops 0.5-0.84 s to 0.15-0.18 s.
  - **Older VAT bakes are swept** before a new one is written: 903 MB of v7-v11 down to the v13 set.
  - **`--travel ZONE@S[,ZONE@S...]`** chains entries, to measure warm and repeat builds.
- **Measure the C# as players run it.** The editor's game DLL is a Debug build (`/optimize-`); a release export is optimised. Kept builds for A/B runs: `dotnet build -p:Optimize=true --no-incremental` (MSBuild doesn't notice the property alone). C#-heavy costs (bakes, sim, crowd) read high in Debug.
- **Paired measurement on a shared GPU:** `--perf-flip X` takes X out every other second, and `tools/perf/flip.py` reads both halves of the same run.

## Measured (2560x1440; "dense" is tier 3 at 27.5 min, ~340 foes)

| what | cost | notes |
|---|---|---|
| Medium / Low vs High | -1.0 / -1.8 ms GPU | |
| FSR quality / balanced / performance | -1.4 / -1.8 / -2.0 ms GPU | doubles the flicker round her, so it stays opt-in |
| her, by calling (town / dense) | warden 0.60/0.68, reaver 0.84/1.06 ms GPU | outfits 375k-708k triangles, kept |
| grass (barrow / hollow) | 0.72 / 0.4 ms GPU | |
| arena first build (Debug C#) | 3.6-6.8 s | her 1.2-2.3 s, flora 0.9 s (was 1.5-2.2), the rest of the stage 0.6-1.1 s, fresh bakes 2.0-2.6 s |
| Waystation, entered second (warm) | 1.9-2.8 s | her 0.27-0.43 s; its people 0.54-1.6 s; its textures 0.4-0.8 s |
| first-launch bakes (Debug C#) | wolf 1.2-1.6 s, boar 0.74-0.94 s | 74% of it is skinning frames (C# math), 2% posing |

## Key decisions

- **Paired flips for GPU costs** while the GPU is shared. Draw counts are exact; plain A/B GPU numbers swing by 2x.
- **No Godot threaded loader.** It crashed on quit in 4.5.1; we decode textures on .NET threads ourselves.
- **Her detail is never traded by a tier.** No LODs on her, all her fur shells, her textures lossless (the owner's rule).
- **Medium stays without MSAA (closed, 2026-10-05).** The owner took the main session's recommendation. MSAA 2x steadies her edges at 23 m (5 flickering pixels against 8), but it costs 0.4-0.9 ms, half of what Medium saves.
- **Invisible changes only**, unless the owner or the owning lead agrees.

## Next

1. First-launch VAT bakes: measure them optimised; skin the frames on worker threads (byte-identical); pre-read the cached kinds before they're needed mid-fight.
2. Her first build (1.2-2.3 s, nearly all resource loading: heroine.glb is 73 MB imported). Her warm build is already 0.3-0.4 s.
3. The dense fight's 22-39 ms main-thread spikes (profile under way).
4. Hollow by Night (`--night hollow`), and loot's drop beams and light pillars once they land.

## Notes for other areas

- **Arena art:** the photoscans' mipmaps and BC7/BC5 have landed, as agreed. Re-shoot the arenas after your next merge and tell me if any scan blocks up or changes colour.
- **Skills:** BattleFx's pickup and weapon meshes and Gore's splat are made once a session now (kept by item and size in `BattleFx.Kept`), not again at every place entered.
- **Creatures:** the new boar's normal map goes in as a compile-time variant (`VAT_NORMAL`). Every other kind's pipeline stays as it is.
- **Legal:** re-list the pack before every upload: `python tools/godot/pack_listing.py Windows`.
