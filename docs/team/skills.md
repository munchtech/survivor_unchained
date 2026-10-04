# Skills: how every skill looks, sounds and feels

Status page for the skills lead (branch `worktree-agent-a8bafe3cd8a229639`).

## Current state (2026-10-04, stopped at the owner's usage limit)

Tests are green (520). Everything below is committed and pushed. ComfyUI is freed.

- **Inventory**:
  - 26 combat skills, 52 evolutions and 9 unions (`logic/Content/Weapons.cs`);
  - 16 arts;
  - blessings and discoveries.
  - The nine starting weapons: Oathblade, Judgement Disc, Cleaver, Axe Gyre,
    Seeking Motes, Cinderfall, Rimeshard, Volley, Knifestorm.
- **Before**: every skill drawn by its school; projectiles hidden in the crowd; the
  grades are below. Frames: `godot/.shots/before_*`, rank 4, a horde of 70 risen
  and 8 champions at 3 m, night.
- **Crop and squaring** (done, tested):
  - flipbook.py refuses a cut-off clip or a cell with edge light;
  - the shaders fade every quad round;
  - `FxTests` holds every atlas, sprite and mark to the rule.
- **Batch 1, the nine starting weapons: working on screen, not yet sent.**
  - Seen in the showcase frames (`godot/.shots/show1_*`: 40 risen at 9–14 m, every
    0.05 s; strips made by the scratchpad's `skills/strip.py`):
    - Volley: a fan of arrow streaks;
    - Knifestorm: a ring of knife streaks;
    - Axe Gyre: four axes with curved white wakes;
    - Judgement Disc: gold hoops with gold wakes that curve as they home;
    - Cinderfall: a burning coal with a flame trail, and its blast;
    - Rimeshard: ice lances with frost trails;
    - Seeking Motes: violet trails.
  - Not seen yet, built since `show1`:
    - the swept blade (Oathblade and Cleaver were still the painted fan in
      `show1`, a flat beige half-disc);
    - each skill's mark on the body;
    - ice, stone and thorn spikes (`Erupt`, `shaders/crystal.gdshader`);
    - the twinkling mote core;
    - the toned-down Hoarfrost (white-out mist cut) and Dawnpulse (sigil smaller);
    - the dark beds' effect in the crush scenario.
- **Grounds** (Blightfield, Hallowed Ground, Thornbloom, Pyre): drawn to the
  experience director's rule (no fill, lit edge, pattern ≤ 35%). Not yet seen: the
  `show1` frames don't show the zone in the crop. Look at a full frame.
- **Agreed with the experience director**:
  - champion death blast about 3 m, flash ≤ 0.15 s, dust ≤ 0.6 s (done);
  - zones as above;
  - the survivor kept clear: what is drawn over the crowd drops to a third of its
    strength over her (`shaders/hero_clear.gdshaderinc`).
- **Spike tells** (combat): `Ev.Sound` ids `tell_*` play recorded takes (`Sfx.Tell`).
  - Made with LTX's audio (`tools/comfy/sfx_clips.py`): tell_howl ×2, tell_drum ×2,
    tell_fuse ×1.
  - tell_whistle is not made yet; it plays a made sound until then.
  - Nobody has listened to any take: the owner should.
- **GPU jobs not done**:
  - the skills' sprites (`tools/comfy/fx_sprites.py make`, Krea);
  - the twelve clips (`fx_clips.py`).
  - The first clip try failed with Windows error 1450 (out of RAM: 2 GB free while
    Godot ran). Run them with no game open.
  - The chain script is the scratchpad's `skills/gpu_chain.sh`.
- **Ribbons.cs is the performance lead's** (a9586a5171413db0b) until they say they
  have pushed region updates for `Buffer.Flush`. Don't edit it before then.

## Grades (before)

1 (poor) to 5 (at the bar), from frames in play.

| Skill | Soul | Reads in a horde | Impact | School | Polish | Crop/square |
|---|---|---|---|---|---|---|
| Oathblade | 2 | 3 | 2 | 2 | 2 | ok |
| Cleaver | 1 | 2 | 2 | 1 | 2 | ok |
| Axe Gyre | 2 | 2 | 1 | 2 | 2 | ok |
| Volley | 1 | 1 | 1 | 1 | 1 | ok |
| Knifestorm | 1 | 1 | 1 | 1 | 1 | ok |
| Judgement Disc | 1 | 1 | 2 | 2 | 1 | ok |
| Seeking Motes | 1 | 1 | 1 | 2 | 1 | ok |
| Moonbrand | 1 | 1 | 1 | 1 | 1 | ok |
| Umbral Bolt | 1 | 1 | 1 | 1 | 1 | ok |
| Cinderfall | 2 | 3 | 3 | 3 | 2 | ok |
| Firepot | 2 | 3 | 3 | 3 | 2 | ok |
| Rimeshard | 1 | 2 | 2 | 2 | 1 | ok |
| Hoarfrost | 1 | 3 | 2 | 2 | 1 | ok |
| Gale Chakram | 1 | 2 | 1 | 1 | 1 | ok |
| Arcweb | 1 | 1 | 1 | 2 | 1 | risk (cylinder ends) |
| Thunderhead | 2 | 3 | 3 | 3 | 2 | ok |
| Verdant Lance | 1 | 2 | 1 | 2 | 1 | risk (cylinder ends) |
| Dawnpulse | 1 | 3 | 2 | 1 | 1 | ok |
| Reaving Arc | 1 | 1 | 1 | 1 | 1 | ok |
| Blightfield | 1 | 3 | 1 | 2 | 1 | ok |
| Hallowed Ground | 1 | 3 | 1 | 1 | 1 | ok |

## Key decisions

- **Per skill, not per school**: the school sets colour and shape; the skill sets its
  body, trail and landing. Rank grows it (`Grow`); an evolution adds a layer.
- **Ribbons with a dark bed under them**: the risen are bone-grey, and light over them
  washes to white; dark round a light is what makes it seen.
- **Drawn over the crowd, at head height, never over her**: from the high camera,
  bodies hide anything at chest height, and the survivor must stay readable.
- **Real shapes where a flat picture fails**: ice, thorns and stone stand up as lit meshes.
- **Pale effects need colour, not white**: frost is blue, holy is gold.

## Next steps, in order

1. Build and run `sweep.py show2 <the nine>` (showcase, `--horde 40 --dist 9 --spread 5
   --every 0.05 --count 32 --start 2.0`). Then run `sweep.py a4 <the nine>` with the
   default crowd, like for like with `before`. Judge every one at full resolution
   (`strip.py`, `ba.py`).
2. Make the before/after contact sheet (`ba.py`) and send it to the main session.
   Send the experience director the minute-25 view (`--minute 25 --auto` with a late
   build).
3. GPU, with no game open: the sprites (pick, then `fx_sprites.py cut NAME=PATH`),
   the twelve clips, tell_whistle and a second tell_fuse take. Then use them:
   - sun_disc for the Judgement Disc;
   - frost_spikes and ice_shatter for frost;
   - holy_ring and gold_flare for holy;
   - blood_scythe for Reaving Arc;
   - poison_cloud and bramble_burst for the grounds.
4. Arcweb: a thicker, bluer bolt. Verdant Lance and the other novas and grounds, seen and judged.
5. Combat's enemy looks (its message of 2026-10-04):
   - aura rings in the people's colour (asked for the people on the event);
   - slams with a dust ring and stone;
   - summon circles;
   - the Sign marks;
   - the haste and ward glints;
   - the bolt_bone and frost_orb arts.
6. Then evolutions and unions, the arts and the callings' own, and sound per skill.
   A Sonniss-style library is on disk in `tools/comfy/out/sfx/` (arrows, axe impacts):
   check its licence first.

## Notes for other areas

- **Combat** (ac4ec5bbd2763a0df): events carry `Art` and `Rank` for the view. The
  tells are in. Its enemy looks are queued above.
- **Experience director** (a33f58e68e89e3ccf): an enemy hit flashes its whole body
  white, which blooms into a blob over the pale risen. A tint or rim would read better.
- **Performance** (a9586a5171413db0b): owns `Ribbons.Buffer.Flush` for now. My added
  batches (shades; ice, thorn and stone spikes with shadows, at most 900) are in its harness.
- **Pickups**: plain white balls lie on the ground in every frame (not identified).
  Loot beams are cylinders with flat-cut tops.
