# Heroine body and outfits: status

Lead: su-lead-max, from 6 October 2026 (until then the main session's own work). Handoff: `docs/handoff/outfits.md`. Branch: `worktree-agent-afb34c385770877d3`.

## Now
- The legal motion check was measuring nothing, and is fixed (see below). The first true baseline on the v11 body is in progress; the Reaver's is done:
  - areola: her right breast, 1 to 4 px from the 45° view in vault_back, chain_haul, bull_rush (down to 0.96 cm from the areola's centre). Cause: the band is laid on the convex hull of 2 cm slices of her chest, so it stands 5 to 20 mm off her upper breast and bridges the hollow towards each armpit; side cameras see in behind it.
  - strip: up to 59 px in chain_haul and chain_strike (a crease at her thigh's root carries skin out from under the G-string's front), 28 to 32 px in vault_back from below (beside the back string, 2.2 cm wide against the strip's 2.4 cm), 1 to 9 px lying on her back.

## The motion check, fixed (tools/legal/motioncheck/marks_section.py)
- Since face v10 (ba0797b4) her skin shader has its own light(); the check's codes were appended at the file's last brace, inside light(), where COLOR is unknown. The tinted shader failed to compile and every count read zero. The codes now go at the end of fragment(), and no lamp lights a coded pixel (her light() adds a sheen from a varying the codes never reset).
- On the v10/v11 body the "sharpest bump" took a lump low on her right breast for the nipple, 6 cm off, so her real right areola went uncoded; on her left it took a point 9 mm off the areola's middle, so a 2.2 cm disc round it missed pigment. Each areola is now found from her paint (skin painted darker than its breast's own), and distances run from its centre. The log prints both centres and warns unless they mirror each other (they agree within 0.2 cm now).
- Any count since 5 October 22:36 is void; re-run.

## Key decisions
- Coverage fixes tighten, never enlarge (the owner: "tighter, not bigger"; "not even a few pixels" extra).
- The check runs against this worktree's own build and import, never the main checkout's.
- Builds read a scratchpad copy of `heroine_built.blend` (md5 4ae7e07b…), so a refit lands only when merged here. A no-change build reproduces heroine.glb exactly; the outfits differ only by UV float noise and 30 trim triangles.

## Next (the handoff's "Open, worst first")
1. Coverage: the Reaver's band and strip; then the Warden and the Arcanist as the baseline shows them (running).
2. Tailoring: the Arcanist's boot cuffs as level bands; kinks at bindings (one seen: the Reaver band's binding folds into a Z where the cleavage bridge meets each breast); the Warden's cup slivers in motion.
3. Distance appeal at play zoom (with the rendering lead).
4. Confirm the pale flake on her upper chest (with the face lead).

## Blockers
- None.

## Notes for other areas
- Face lead (aed215ba3ca60cc29): a sculpt change goes to the main session for the refit; this lead builds on the refitted body once merged. To confirm by eye: the build finds her nipples' bumps 8 to 9 mm above the centres of her painted areolas (both sides), so paint and sculpt may be a little out of register.
- Animation lead (a9a80800a7dae2519): the garments take her skin's weights at build time, so any weight change needs an outfits rebuild before a motion check. Use the fixed check from this branch.
- Rendering lead (a20bdef993e00f26b): distance appeal and motion clarity.
- To give a worktree a working Godot import in about 30 s rather than a full re-import: copy main's `godot/.godot`, then main's `*.import` and `*.uid` sidecars (godot and public/assets), then make `godot/assets` a junction to the worktree's `public/assets` and `git update-index --skip-worktree godot/assets`. The sidecars then show as line-ending churn: never commit them.
