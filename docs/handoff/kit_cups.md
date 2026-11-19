# kit-cups (coordinator #15 lane, 18-19 Nov 2026)

## STATE (top block: keep current)
- Lead: kit-cups lead (this session). Worktree `.claude/worktrees/agent-af6695054c56ec8ef`, branch `kit-cups` from integration 553742efd. godot/assets = junction to this worktree's public/assets (assume-unchanged).
- Brief: the coordinator's kit-cups message (18 Nov). Goal: the kit bodice cups on B read round, full, smooth; one highlight per dome; trims follow the dome, no notch/fold/lump; fix in tools/armor/kit_build.py (recipe), not outputs. Judges <=2 (su-lead-max, Item: kit-cups, always-seen, 150k), 3 rounds max. Merge-ready evening 19 Nov; one-line status to coord by midday 19 Nov.
- Owner frames: `survivorsunchained_inputs/scratch_coord15/owner_frames/owner_cups_18nov.png`, `owner_cup_dent_ingame_18nov.png`.
- Old shoot scripts (lead 8, same scratchpad): `<scratchpad>/l8/j5.txt` (judge set), `l8/shoot_hud_keep.sh`, `l8/imp.sh` (they point at the demo-armor worktree: copy and repoint).
- State (18 Nov night): CAUSE FOUND offline. kit_build.dome() is body A's design (16 Nov, e351f651d): an ellipsoid least-squares fit (A's apex, drop 12 mm, axes 33.5/53/51.6 mm) smooth-maxed with her offset, eased back to her offset over u .62-1. On B (worn push-up) the ellipsoid hangs ~28 mm BELOW her lower pole (to y~1.305, under the band) then the ease pinches back to her skin: an S-bend on the lower spokes (psi 135-225) = a sagging pouch with a crease across each cup (the "fold"/"misshapen" look); upper half follows her skin (lumps where skin > ellipsoid). Also build()'s push-to-clear_min moves 124 cup verts up to 5.8 mm along her normal (possible notch at the rim; to map).
- Fix in progress: a B-only dome (cup.dome.by_body.p1 "mode") = her worn skin offset + a fullness lift (full at apex, 0 at rim), per-spoke convex hull to the rim point (no S-bend, edge stays on her), psi smoothing + re-hull. A untouched (byte-identical).
- Offline tools (scratchpad `kc/`): grab.py <out.npz> [json override] (GRAB_DOME=v1:v2 hooks a scratch dome), rend.py <npz> <png> [shade|toon|curv] (ONLY=cup_l), prof.py, meshprof.py; base.npz/base_shade.png = shipped shape. A kit_bodice build on B: 5.5 min cold, 2 s cached.
- Done: branch + junction; shipped bodice rebuilds byte-identical here.
- Next: v2 dome offline -> port to kit_build (knobs by_body p1) -> pytest -> ship chain (piece_ship --body p1, cover, gear_fit build --body godot/art/people/body_p1) -> import -> shoot before/after (static bind + idle) -> judge 1.
- Agents: none yet.
- Shell note: the sandbox refuses heredocs/compound bash here: write files with Write, run simple commands.
