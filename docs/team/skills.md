# Skills: how every skill looks, sounds and feels

Status page for the skills lead (branch `worktree-agent-a8bafe3cd8a229639`).

## Current state (2026-10-03, stopped at the owner's usage limit)

Tests green (472). Everything below is committed and pushed.

- **Inventory**:
  - 26 combat skills, 52 evolutions and 9 unions (`logic/Content/Weapons.cs`);
  - 16 arts (`Content/Abilities.cs`);
  - blessings and discoveries with visible rules (`Content/Boons.cs`, `Discoveries.cs`).
  - The nine starting weapons: Oathblade or Judgement Disc (warden), Cleaver or Axe
    Gyre (reaver), Seeking Motes, Cinderfall or Rimeshard (arcanist), Volley or
    Knifestorm (stalker).
- **Before, seen in play** (every skill at rank 4 in a horde of risen with eight
  champions, night; frames in `godot/.shots/before_*`, sheets in the scratchpad's
  `skills/before/`):
  - every skill was drawn by its school, not as itself;
  - projectiles were glowing dots with dotted trails, flown at chest height, so from
    the high camera the crowd hid them. Moonbrand, Umbral Bolt and Volley are
    invisible in a horde; Seeking Motes and Judgement Disc nearly so;
  - Dawnpulse and Hallowed Ground read as fire (orange glare discs); Blightfield is a
    flat neon-green disc with a hard rim; Hoarfrost and Rimeshard are white glare;
    Thunderhead's own strike marks look like hostile telegraphs; Verdant Lance and
    Arcweb are flat cylinders with square ends;
  - champions' deaths (big dust blasts) drown every skill's frames.
  - Thornbloom's run gave no frames: run it again.
- **Crop and squaring, fixed at three levels**:
  - `tools/comfy/flipbook.py` refuses (exit 2, nothing written) a clip that runs off
    its own frame, and any cell with light on its border, past 0.97 of its radius, or
    more than 1% of its light past 0.9. `--check` and `--clean` for atlases already made;
  - the flipbook, spark and smoke shaders fade every quad round, whatever it holds;
  - `tests/FxTests.cs` holds every atlas, sprite and ground mark to the rule (checked
    that it fails on the old `fire_loop`);
  - found and fixed: `fire_loop` (every frame at its edge), `ember_motes`, and five
    sprites that ran off their square (the pack's lightning forks, a clod, a twirl).
- **Batch 1, code written, not yet right on screen**:
  - blows carry their skill's art and rank (`Ev.*.Art`, `Rank`; the view only reads them);
  - `src/Fx/Ribbons.cs` and `shaders/ribbon.gdshader`: trails, bolts and threads as
    one mesh a frame, drawn over the crowd;
  - `src/Fx/BattleFx.Skills.cs`: each skill's flight, trail, release, swing and impact;
    novas (Hoarfrost, Dawnpulse, Reaving Arc), chains, strikes from the sky and beams;
  - projectile cores drawn over the crowd (`shaders/spark_over.gdshader`), flights lifted
    to head height.
  - **First look** (`godot/.shots/after1_*`, sheet `scratchpad/skills/ba_batch1_first.png`):
    the new swing (sparks, crack, dust) shows; **the ribbon trails do not show** on
    Volley or Seeking Motes. Debug that first (is the mesh drawn at all? camera,
    strength, width, the `Now`/`Feed` timing against `Ribbons.Step`).
- **Lab**: `--lab` (only the skills given, no drafts, no levels, no dying) with
  `--give`, `--horde`, `--shot --every --count`. Scripts in the scratchpad's
  `skills/`: `shot.py` (one run at 1920x1080, fixed 60 fps), `sweep.py TAG [ids]`
  (each skill alone, a sheet each), `sheet.py` (contact sheets).
- **New clips**: twelve prompts added to `tools/comfy/fx_clips.py` (frost_spikes,
  holy_ring, blood_scythe, moon_burst, ice_shatter, poison_cloud, bramble_burst,
  gold_flare, fireball_impact, dust_chop, shadow_wisps, leaf_burst). The batch was
  stopped at the first clip for the usage limit; none is made. ComfyUI is freed.

## Grades (before)

1 (poor) to 5 (at the bar), from the frames above. Crop/square: "risk" where a
square-edged texture or cylinder end could show.

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

The rest (Iron Palms, Grave Tether, Gravecall, Thornbloom, Spirit Herd and the
unions) have frames but are not graded yet.

## Key decisions

- **Per skill, not per school**: the school sets colour and shape language; the skill
  sets the body, trail and landing. A rank-8 skill is drawn about a third larger and
  brighter than at rank 1 (`Grow`); an evolution adds a layer of its own.
- **Ribbons over dotted sparks** for what flies: a line reads as speed and direction;
  dots read as litter, and cost more.
- **Drawn over the crowd**: from the game's high camera, bodies hide anything at chest height.
- **Pale effects need colour, not white**: the risen are pale grey, so white glare
  vanishes into them; frost is blue, holy is gold, never white-hot over a crowd.

## Next steps, in order

1. Find why the ribbon trails do not show; then rerun `sweep.py after1` for the nine
   starting weapons and judge each at full resolution against the before frames.
2. Make the twelve clips (`fx_clips.py <tools/comfy/out/clips> <names>`), cut each with
   `flipbook.py` (it refuses a cropped one: change its seed and make it again), and use
   them in `BattleFx.Skills.cs` (frost_spikes for Hoarfrost and Rimeshard, holy_ring for
   Dawnpulse, blood_scythe for Reaving Arc, and so on).
3. Before/after contact sheet of Batch 1 to the main session.
4. Batch 2: zones (Blightfield, Hallowed Ground, Thornbloom with real brambles), the
   herd (spirit beasts on the wolf's body with the ghost shader), summons, Grave
   Tether, Iron Palms; then evolutions and unions; then arts and the callings' own;
   then sound per skill (all synthesised today, by school).
5. Champions' death blasts (`BattleFx` Kill, elites) are too big: agree a size with
   the experience director.

## Notes for other areas

- **Combat** (`ac4ec5bbd2763a0df`): events now carry `Art` and `Rank`; nothing in the
  logic reads them. Its coming encounter work (the charge director, minibosses) will
  need telegraphs and effects from here: ask.
- **Experience director**: hit-stop is global (`WorldScene.Weigh`); a hit's flare and
  sparks scale with the share of life a blow takes. The champions' death blasts drown
  the skills.
- **Whoever owns pickups**: plain white balls lie on the ground in these frames
  (what the dead drop, not yet identified).
