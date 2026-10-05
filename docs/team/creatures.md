# Creatures and models: status

The creatures and models lead (branch `claude/creatures-boar`). The brief: replace every model that isn't ours with our own, in the order of `docs/art/MODELS_TO_MAKE.md`, starting with the boar (a launch blocker: its file is "personal use only").

## State (5 October)

- **The boar: in progress.** Pipeline set up; waiting on the GPU turn for the first pictures.
  - `tools/creatures/concept.py`: concept pictures from Z-Image-Turbo (Apache-2.0, no revenue cap), each with its record (prompt, seed, model hash, date).
  - `tools/creatures/sculpt.py`: a picture through TRELLIS 2 (MIT) locally, with its record.
  - `tools/comfy/graphs/zimage_t2i.json`: the Z-Image graph.

## Key decisions

- **Pictures from Z-Image-Turbo, not Krea 2.** Legal 5(g) ranks a cap-free local model above Krea; a Krea-made boar would only join the list of things to replace. Krea stays the fallback if Z-Image can't get the look.
- **A new four-legged rig, not the old boar's skeleton.** The old skeleton's clips are part of the personal-use asset. The new rig is meant to be shared with the wolf later. Agreed with animation (a7dd95d00c4a6a017): I key a first pass, they review and own the clips.
- **Budget (agreed with performance, a0eb8c612c94d4aa5):** about 7k VAT vertices (inside the 8000), a 2K albedo, a 2K normal map read through a compile-time `VAT_NORMAL` shader variant (only boar surfaces pay), the bristles on their own cut surface and texture. Textures ship as separate VRAM-compressed files, not embedded uncompressed.
- **Charge as its own role** (a gallop), played while lunging; the trot stays `move`.

## Next

1. Concept pictures (Z-Image) → pick → TRELLIS 2 sculpts → pick.
2. Blender: orient, symmetrise, retopology, UVs, bake, our own paint layer, tusks and bristle cards, rig, weights, first-pass clips.
3. Swap into Godot under the same name; judge in a horde at the game camera and close up (Old Tusk at 1.9x).
4. Paperwork: `docs/legal/records/BOAR_RECORD.md`, ASSET_PROVENANCE (CR-02 retired), CREDITS.

## Notes for other areas

- **Animation:** rig conventions agreed (+Z forward, hooves at y 0, bones along +Y, mirrored rolls, in-place clips with speeds in m/s, Snout and leaf bones).
- **Performance:** perf-flip numbers against today's boar with `--horde 60:boar` when it lands.
