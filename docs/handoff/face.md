# Handoff: the heroine's face, hair and creation's Look (v12, round 2 judged; the fix pass next)

From agent afb7deb41dbb5d904 (took over from a6e8e6d0f539943bb, cut off 7 October). Read `docs/team/README.md` ("Working lean", "Safety"), `RESUME.md`, `OWNER_NOTES.md` (the face's order and bar), this page, then `docs/team/face.md`. Read by section (grep, then line ranges). Hand off at about 300k.

## The owner's words
- "we are striving for perfection". The bar: at the Look close-up beside each face's reference, no "this is a render" tell; grain at least 0.9 of the photo's; tones and irises within a few per cent; no seams, bands or blobs; it holds at play distance.
- Order: the face, then the paints and sliders, then hair over many rounds ("way more than 2-3").

## Branch: `worktree-agent-afb7deb41dbb5d904` (pushed; 775 tests green)
Based on `claude/vigilant-galileo-l6jqyx` @ 45a0bde4, with the predecessor's WIP merged (its commit wrongly turned `godot/assets` into real files; the merge keeps the symlink). Commits: f0665929 (eyes, atlas, lashes script, brow pin), 6e19fd2c (hair round 2). Not merged to integration: the eye values below must change first.
- `heroine_eye.gdshader`: new uniforms (defaults = the old look, so the hero is unchanged): `iris_contrast`, `ring_to` (amber drawn in), `pupil_dark`, `white_tint`, `corner_pink`, `lid_shadow`/`lid_y`/`lid_fade` (upper-lid shadow held to the eyeball), `low_wet`/`low_y` (lower-lid wet line), `catch_soft`.
- `People.HerEyes(e, face)`: all her eye uniforms in one place, per face from looks.json faces (`Lore.FaceShape.Pupil`, `.Whites`, `.Lid`); called from `HerPart` and the look re-apply loop. `--eye-set k=v,...` overrides last.
- looks.json faces: lid/pupil/whites on own, Highborn, Doe, Sunborn; Sloe desaturated (#221f17 / #2c281e).
- `heroine_hair.py`: atlas strands redrawn not clipped, ragged soft roots, straight (un-premultiplied) shade, wider shade spread; baby hairs from the lock columns. Atlas, scalp and all five styles rebuilt. `heroine_hair.gdshaderinc`: card tone narrowed (depth 0.75-1, AO 0.75-1, lock tint 0.04, roots by 1-depth), cap hairline shade 1.0 and ragged. `heroine_skin.gdshader`: rim only against light from behind (shared with the hero: tell his lead).
- `heroine_lashes.py`: 300 upper lashes in clumps, root band; output not shipped (trial `f12\lashes_e.png`).
- `heroine_face.py` `brow_zone`: the move smoothed per brow (quadratic in u, linear in v), lower edge at `FACE_BROW_LOW` (0.65) of the fraction, zone over the temple. `FACE_BROW_SMOOTH=0` for the old way.

## Verdicts (scratch S = C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\181eef02-779f-45de-b419-31a949a4d27e\scratchpad)
- Round 1 (brows and eyes): in this page's history (Doe 1.0, Sunborn 0.6; eyes as below, partly reversed).
- Hair round 1: atlas SHIP with blended drawing (`--hair-draw blend`).
- **Eyes round 2: `S\judge_ey2\verdict.md`** (scripts `fit2.py`, `pupil.py`, `lash2.py` there). MediaPipe mismeasures renders: trust its edge fits, not round 1's iris and lid numbers.
- **Brows round 2: `S\judge_br2\verdict.md`** (scripts `zonefit.py`, `kinks.py` there). Rule for all ten: fraction 1.0, lower share 0.65, after these `brow_zone` fixes: (a) each landmark's share by where it sits between the brow's own lower edge (46-53-52-65-55) and upper edge (70-63-105-66-107) at that point along it, not by height across the whole brow (tails droop 0.15-0.2 ew); (b) move the forehead landmarks just above too, easing to zero about 1 ew over the brow top (69/104 squeezed 1.8-3.6x: the dip); (c) a cubic along the brow, brow and neighbours fitted apart. Doe: setting ships, paint after (a) and the tint fix. Sunborn: 0.8 split until (a)+(b), then 1.0. Doe's brows still heavy (contrast 0.68 vs 0.56). The temple smear/tail blue-grey is the lay's per-channel `tint_to` turning the photo's hair edge and sheen lavender: mask hair and backdrop out of the front lay (feathered), colour shift on skin-like pixels only, sheen out first; the tint's fit set is unstable (0.8 and 1.0 lays got different gains). Re-shoot Doe and Sunborn (front, t40, white) before the GPU re-lay.
- **Hair round 2: `S\judge_hr2\verdict.md`.** SHIP WITH a baby-hair fix: keep the card tone, atlas spread and rim change (all measure better, no new speckle). The new baby hairs read as dark grey strokes crossing in X's (a new tell): recolour and recomb them (`heroine_hair.py` hairline_hairs, about lines 650-665: 2-7 mm, spread 0.2 rad, 8% astray, lighter copper, no root/AO darkening) or switch them off before the owner sees anything. Then, worst first: the hairline dark band (the cap's x0.5 at `heroine_hair.gdshaderinc` ~line 100: fade 0.85-1.0; root, depth and AO at 1.0 near the hairline; one A/B shot); shine (about 0.5 using `fibre`, not `fibre * fibre`, ~line 149); the turned-40 curtain edge; a bob rebuild; temples. Her hair renders 18% darker and redder than her portrait. Rendering's: the strap cut at the right ear, DOF at the crown, shadow facets on her neck, card order.

## The fix pass: exact values from the eyes round-2 judge (set in `People.HerEyes` / looks.json)
- iris_r 0.117 (per face if possible: Sunborn 0.108, Moonlit 0.109, Saffron 0.114, Wildling 0.121).
- pupil_dark 0.010, applied after `tint` in the shader (or 0.019 for her painted iris). pupil: own 0.22, Highborn 0.23, Doe 0.25, Sunborn 0.225, Vixen 0.225, Moonlit 0.255, Saffron 0.255, Wildling 0.215, Hard-won 0.23, Fey 0.29.
- Resting lids (with iris_r 0.117): own 0.03, Doe 0.035, Highborn 0.06, Sunborn 0.08; Vixen, Saffron, Wildling, Hard-won -0.05; Moonlit, Fey -0.07 to -0.08 (or the `eyes_open` slider). Lower lid over 0.05 of the iris after that: a sculpt fix for the refit.
- whites: own 1.25, Highborn 0.9, Doe 0.8, Sunborn 0.65, Vixen 0.8, Moonlit 0.85, Saffron 0.85, Wildling 0.75, Hard-won 0.8, Fey 1.0. Add the portraits' gradient (white 1.15-1.3x brighter half a radius below centre, 0.6x at +0.2 R).
- lid shadow: place it at the visible margin (-0.42 to -0.52 R on the defaults), not -0.85. Wet line: at 0.95 once the lower lid is down, plus a 10-15% albedo lift over 0.05 R.
- catchlight: catch_at (-0.15, -0.33), catchlight 0.9; in the shader `ALBEDO *= 1.0 - 0.8 * glint`, emission (0.9, 0.95, 1.08).
- Lashes REDO: the cards are unlit (paint (26,19,15) renders about 0). Light them like lid skin (normals to camera/up, or wrap) or lift the paint to about (60,42,32); target (45,30,24) at the Look; alpha capped 0.85; fan the outer lashes (alpha <= 0.6) instead of the winged wedge. Then write `head_tex/heroine_lashes.png` (the script's default output) and retire `heroine_eyes.lashes()`.

## Next, in order
1. The fix pass above, with brows and hair round 2's fixes; one eye/brow/hair batch; a fresh judge.
2. Then the handoff's older list: one sculpt (upper lips 13-37% thin, maybe the brow ridge after a raking-light check of Doe at 1.0), one GPU re-lay of the ten paints (`f12\pin_test2.ps1 -detail 0.3`, gpu + blender turns, ComfyUI headless), one build, one refit (tell main); neck grain; the book by day; jaw-edge spots; then paints and sliders, then hair rounds.

## Scripts (in `S\f12`; repointed copies of the predecessor's face11)
- `look_ab.ps1 -tag T -runs "NAME|PRESET|ARGS"` (takes the godot turn; `-import` after art changes), `shot.ps1` (1920x1080), `blend_one.ps1 BLEND SCRIPT TAG ARGS` (blender turn).
- Sheets: `rows.py` (face crops 1:1 + portrait), `eyes.py` (eyes at 2x; env HALF_W/X_OFF/TOP/BOT/UP for one eye at 4x). Batches: `eyes2.ps1` (all ten faces), `brows2.ps1` (lay, relay, shoot), `hair2.ps1`; measures `atlas_prof.py`, `lash_ink.py`, `alpha_rgb.py`.
- Old worktree (read-only art): `.claude\worktrees\agent-a6e8e6d0f539943bb\godot\.shots\` br_*, ey_* (round-1 frames, the "old" baselines). Raw heads and `heroine_unpainted.blend` copied into this worktree's `tools/comfy/out/heroes` (from agent-abe65bc929823a791's).

## Gotchas
- The worktree guard refuses computed paths, variables, heredocs and compound commands in Bash: write scripts and call them with literal paths.
- Godot's import rewrites hundreds of `.import` sidecars and adds `.uid`s: never commit them (stage files by name). `godot/assets` is a junction with `--skip-worktree`.
- A fresh worktree needs main's `godot/.godot` (robocopy), `f12\sidecars.py`, and a first `-import` (about 8 minutes).

HANDOFF READY: docs/handoff/face.md on worktree-agent-afb7deb41dbb5d904
