# Skills: how every skill looks, sounds and feels

Status page for the skills lead (a63cd93fc73d5ed79, branch `worktree-agent-a63cd93fc73d5ed79`).

## Current state (2026-10-04)

Tests green (539). Pushed: 5d33acc, 135cd7c. Before/after sheets sent to the main session
(`scratchpad/vfx/ba_nine_*.png`, `ba_a7_*.png`).

- **Batch 1 (the nine starting weapons, Hoarfrost, Dawnpulse): remade, seen at full resolution** in
  a packed crowd (rank 4, 70 risen and 8 champions at 3 m) and in the 9–14 m showcase.
  - Blades: a crescent shader (`shaders/blade.gdshader`, `src/Fx/Blades.cs`, one MultiMesh). A
    white edge leads, a streaked smear follows and tatters away, with its own dark bed. It replaces
    the ribbon sweep, whose joins and flat ends showed as squares.
  - Motes weave with a short tail and spark dust (their long tails had read as beams). The disc is
    gold with spin arcs and a painted sawblade face. Ice is cut crystal (`crystal.gdshader`, facets).
    Rimeshard flies as a six-sided lance, arrows are real arrows, and Cinderfall has a painted coal.
  - Crowd restraint (the cream blobs): kill bursts budgeted at six a frame, steel kills throw grit,
    flashes share their light, champions falling together are told by the first, and no filmed
    burst per mote, shard or disc hit.
- **Grounds**: fills premultiplied (the pyre "square" is gone); burning ground is fire in cracks;
  Hallowed's edge is thinner and its runes are at 0.18; hostile fills are hatched (front edge plus
  about 30% hatch). Seen at rank 8 for Hallowed, Sanctified and Pyre.
- **GPU**: ten Krea sprites cut into `art/fx/sprites.png` (sun_disc, dawn_sigil, frost_star,
  rune_ring, umbral, ward_disc, crescent, ember_coal, wisp, blood_drop). The LTX chain (tell_whistle,
  a second tell_fuse, the twelve clips) is running from `scratchpad/vfx/gpu_ltx.sh`, waiting for
  11 GB of free RAM before each job.
- **Trail heads** come to a point (Ribbons.DrawTrail; the performance lead agreed).

## Grades (now)

1 (poor) to 5 (at the bar), from frames in play. "Before" is in the git history of this page.

| Skill | Soul | Reads in a horde | Impact | School | Polish | Crop/square |
|---|---|---|---|---|---|---|
| Oathblade | 4 | 4 | 4 | 4 | 4 | ok |
| Cleaver | 4 | 4 | 4 | 4 | 4 | ok |
| Axe Gyre | 3 | 4 | 3 | 3 | 3 | ok |
| Judgement Disc | 3 | 3 | 3 | 4 | 3 | ok (face reads as a sun: dimmed, unseen) |
| Seeking Motes | 3 | 3 | 2 | 4 | 3 | ok (magenta haze in a crowd: dimmed, unseen) |
| Cinderfall | 3 | 4 | 4 | 4 | 3 | ok |
| Rimeshard | 3 | 4 | 3 | 4 | 3 | ok |
| Volley | 3 | 4 | 3 | 3 | 3 | ok |
| Knifestorm | 3 | 4 | 3 | 3 | 3 | ok |
| Hoarfrost | 3 | 3 | 3 | 4 | 3 | ok |
| Dawnpulse | 3 | 3 | 4 | 4 | 3 | ok |

## Key decisions

- **Hues below the tone curve's knee.** AgX turns any coloured light over about 2 to white or
  cream, so bodies and smears sit near 1; only the thin edge or core is white.
- **Dark beds**, in the same pass where possible (premultiplied: alpha darkens, colour adds).
- **A crowd is told by its first few deaths and blasts.** Many effects at once must not sum to a wash.
- **Per skill, not per school**; real shapes where a flat picture fails (ice, arrows); painted
  sprites for bodies, luminance-keyed and edge-checked.

## Next steps, in order

1. When the LTX chain is done: cut the twelve clips (`flipbook.py`) and listen to the tell takes. Use
   frost_spikes/ice_shatter for frost, holy_ring/gold_flare for holy, blood_scythe for Reaving Arc,
   and poison_cloud/bramble_burst for the grounds.
2. See the dimmed disc face and motes in a crowd. Use dawn_sigil as a ground mark for Dawnpulse.
3. Arcweb (a thicker, bluer bolt), Verdant Lance, Thunderhead, the other novas and grounds,
   Umbral Bolt and Moonbrand (new painted bodies, unseen).
4. Combat's enemy looks: aura rings, slams, summon circles, Sign marks, haste and ward glints,
   bolt_bone and frost_orb.
5. Evolutions and unions, the arts and the callings' own, and sound per skill.

## Notes for other areas

- **Experience director** (ad1f5623590e09883): your items 1–3 are in. I've asked you about the frozen
  and burning tints in `vat.gdshaderinc` (they turn the risen white and cream in crowds).
- **Performance** (a7145e18b3eb78294): Blades is one MultiMesh, at most 48 instances. Ribbons only
  gained the head cap.
- **Main session**: running `--headless --import` in a worktree rewrites many `.import` files (VRAM
  formats). Commit only your own; never restore them mid-session or the next import redoes them all.
