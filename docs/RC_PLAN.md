# Toward a release candidate

The bar is not a polish pass: it is a game many times better in every
respect, one that stands beside the best of its kind. This list is kept in
priority order and ticked as work lands. Every visual change is checked in
the running game (RTX 5080, real time); `dotnet test` passes before every
commit.

## What we have to work with
- The game runs in real time on the owner's PC; `--give`, `--horde`,
  `--dist`, `--spread`, `--cam` and `--auto idle` make an effects lab: the
  survivor standing in a pack at arm's length, a burst of frames.
- A local ComfyUI with Krea 2 (stills, the darkbrush LoRA), LTX 2.5
  (video: fire, smoke, blasts and magic shot on black and cut into
  flipbooks), TRELLIS 2 and Pixal3D (image to 3D), BiRefNet (cut-outs),
  MoGe (depth and normals) and Qwen3-TTS (voices).
- Sketchfab (CC-BY, credited) through `tools/assets/sketchfab.mjs`, and the
  CC0 libraries (Poly Haven, Kenney, Quaternius).

## 1. Combat that feels like a blow landing (the brief's first priority)
- [x] Struck creatures flash white-hot, then flare at the rim.
- [x] Thrown axes and daggers are the weapons, not boxes of light.
- [ ] A new effects library: flipbook fire, smoke, blasts, lightning and
      magic generated with LTX and cut into atlases; soft particles,
      distortion, ground decals (scorch, cracks, frost, blood), light that
      flickers with them. Every school (fire, frost, storm, holy, shadow,
      nature, physical, blood) with its own look in core, halo and trail.
- [ ] Scale and restraint: no effect may fill the screen with a flat disc
      (level-up, Crashing Leap, novas): a fast bright flash, then shape.
- [ ] The swing: a crescent with a white-hot edge, sparks off armour,
      a short hitstop and camera kick weighted by the blow.
- [ ] Spirit Herd as spectral elk charging through the pack (Realistic
      Animated Elk, WildMesh_3D, CC-BY: needs the Sketchfab token).
- [ ] Sound: layered impacts (transient, body, tail) per weapon and per
      what is struck; spell casts and their landings.

## 2. A world worth looking at
- [x] Moonlit nights; a warmer day.
- [ ] The ground: from the high camera it reads as flat mud and lilac
      stone. Rich terrain shading: macro variation, wet and dry, paths
      worn in, scorch and bone; stone that reads as stone.
- [ ] Foliage and roofs between the camera and the survivor fade.
- [ ] The campfire: real flame (flipbook), embers, smoke, flicker.
- [ ] The Waystation: camera height and framing; the sign colliding with
      the zone title.
- [ ] A living world: birds, moths round lamps, mist in hollows, wind in
      the grass and trees, townsfolk at work.

## 3. Story, choices and their outcomes
- [ ] A full audit of the writing, the choices and the structure (under
      way), then the rewrite it calls for.
- [ ] Voice acting for the main characters (Qwen3-TTS), cast per person.

## 4. People
- [ ] The woman survivor checked in a real window (title, creation, the
      staff, a fight) and made a striking, fuller figure in the game's art.
- [ ] The reaver's bare head reads as a white ball under the rim light.

## 5. Day and night as a loop
- [ ] Play the day story and the night arenas end to end; tune what
      draws a player from one to the other.

## Housekeeping
- [x] `Items` published its table before it was whole; four tests failed at
      random on a fast machine.
- [x] The presets' test checks the light's direction, not the web game's
      numbers.
