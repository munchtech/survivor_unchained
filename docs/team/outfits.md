# Heroine body and outfits: status

Lead: su-lead-max (first lead, 6 October 2026; wound down for usage). Handoff: `docs/handoff/outfits.md`. Branches: `worktree-agent-afb34c385770877d3` (finished work, merge it), `outfits-lead-wip` (heroine_outfits.py in progress: build and check before merging).

## Now
- The legal motion check works again: it measured nothing from face v10 until now, and it missed her right areola on the v11 body. True baselines are in the handoff.
- Every strip exposure happens in motion (at rest all are covered, 4.4 to 7.5 mm to bare skin). The causes are found; fixes are written but not yet built.
- The Warden's "nipple-tip pokes" were MSAA artefacts on steel, now fixed in the outfit shader.

## Key decisions
- Coverage fixes tighten, never enlarge. Exception: where the check's 2.4 cm strip is wider than the garment (the Arcanist's 1.9 cm V, the 2.2 cm back strings), the garment widens to just cover it.
- Gussets and strings tuck her skin and follow it, as stretched cloth does, instead of moving as rigid straps.
- The check runs against this lead's own worktree build and import, never the main checkout's.
- MSAA silhouette samples are repaired in the outfit shader (no-length or backward normals, clamped attributes). The look elsewhere is unchanged (checked by a frame diff).

## Next
1. Apply the ribbon calls, build, read the `COVER`/`UNBOUND` logs, check all four outfits, and iterate to zero.
2. The Warden's left pauldron: unbound rim (the jagged sparkle line), crumple at the armpit, brushing too regular.
3. Tailoring list, then distance appeal. (The chest flake is closed: not seen on v11 or v12.)

## Blockers
- None (wound down for usage).

## Notes for other areas
- Rendering lead (a20bdef993e00f26b): TAA throws an out-of-gamut pixel at a gold edge against the background (Warden vault, chest view, frame 10, near (591, 323)); the MSAA ones are fixed in the outfit shader.
- Animation lead (a9a80800a7dae2519): garments must keep the skin's weights under them; send per-outfit deviations after the helper bones.
- Face lead (aed215ba3ca60cc29): paint and sculpt may be a little out of register (nipple bumps 8 to 9 mm above the areola centres); to confirm by eye.
- Any lead: the worktree-import recipe and every check script are in `tools/scratch/outfits/` and the handoff.
