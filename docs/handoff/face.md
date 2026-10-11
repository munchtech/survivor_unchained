# Handoff: the heroine's face, hair and creation's Look (v12; neck judge n2)

From agent afb7deb41dbb5d904 (took over from a6e8e6d0f539943bb, cut off 7 October). Read `docs/team/README.md` ("Working lean", "Safety"), `RESUME.md`, `OWNER_NOTES.md` (the face's order and bar), this page, then `docs/team/face.md`. Read by section (grep, then line ranges). Hand off at about 300k.

## Start here (11 Oct, morning; face successor 5 handing off at about 260k; branch `worktree-agent-a2d632df7c7f21ec0` @ b3ede887)
Brief (coordinator): own the Look's portrait rig while rendering is paused (fill, bounce, key higher and frontal with shadow, then per-face hue and chroma trims), judged as a whole (skin vs portraits, jaw shade, catchlights, the presets' spread, armour clipping); the orange particle; then the nape crack; then the neck-length sheet for the owner; then the queue below. Helpers must SendMessage you their results.
Scratch G = `...\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad18` (shots in godot/.shots r1-r5b). Scripts are copied to `tools/scratch/face17`: `look.ps1` (a batch in one godot turn, each shot killed after 240 s and retried; preset `raw` for play shots), `meas.py TAG [faces]` (cheek, jaw and neck Oklab beside the portraits, plus the armour's clipped share), `trims.py TAG` (gains to the portraits), `sheet3.py TAG OUT` (judge sheets), `jawcrop.py`, `eyecrop.py`, `catch.py`, `ruler.py` and `notch.py` (neck proportion). Run them with the facefit venv.
- **Done:**
  - Nape crack (0cface69): `heroine_seam.py weld_weights` gives the head's shared points the graft's skin weights (two had Head 0.027 vs 0.40). Runs on already-seamed glbs too (marker seam_weights). heroine.glb is welded. The -3 cm profile fleck is gone (r3/r4 nk-3_p). Animation a4e62fc358dc5214a and outfits af07affeb22637bb5 are told. A nod check is still to do.
  - Rig (b3ede887; written into performance.md's "Paused here"): fill 1/0.98/0.96, bounce 0.045, key side 0.55 and up 1.25, energy 1.3, size 0.3, sheen 0.3. Embers and smoke kept out in front of her (`Campfire.ClearNear`). Catchlight a soft window at 12 o'clock (`catch_window`, size 2.8).
  - Diagnosis (d1): the jaw shade is lit mostly by the fill and the key's soft shadow. A smaller key (0.3) took own's jaw L from .50 to .44 (= portrait). Vixen and Fey stay .48-.53 (portraits .37-.38) whatever the rig: that's their paint or shape, not the light. Highborn went to .40 (portrait .50).
- **In progress, UNJUDGED: skin trims.** HerFaceTone was refitted twice (r1, r3): cheeks within +1 to +7% chroma and +0 to +3 deg hue of the portraits. HerBodyTone takes the neck to the portraits' neck/cheek chroma ratio (0.56-0.80). At full strength (k=1) the lit neck matches, but the shade under the jaw goes grey-violet on own and Highborn (C .015, h 30): the owner's old complaint, so not shipped. Default `BodyK` 0.5 (`--body-k`); the face keeps the rest, so the cheek is unchanged. Crops: G\jaw2.jpg (k1, k0.5, k0.5 with a whiter key, k0 with a whiter key, portrait). k0.5 still reads a little cool under the jaw.
  - **Next:**
    1. Decide k (0.3-0.5), or lift the shade's chroma another way. `--shade-tint` (shade_tint by down-facing normal) also hit the lower cheek (+20% chroma): not a fix as it stands.
    2. Rerun `heroine_ears.py` from `f17\heads_orig`: its `tones()` must multiply in body^(1-k) to match `FaceTone()`.
    3. Shoot `face17/r5.ps1` (all ten, t40 ears, untrimmed A/B, bust and full frames, neck 0/-1.5/-2/-3 at the Look and in play). Then sheet3.py and ONE fresh max judge on the whole (checklist: the coordinator's list above plus j2's acceptance numbers in face16).
- **Neck length (for the owner, after the judge):** sheets are not made yet. Ruler (Guler.jpg, notch.py): portraits' notch dips sit at 0.44-0.47 and 0.64-0.68 of pupil-to-chin below the chin; ours (strongest dip) 0.89 today, 0.80 at -1.5, 0.73 at -3. That puts -1.5 still about 20% long, so a -2 cm column is added (r5.ps1). There's no in-play profile: no heading switch in play; the conversation camera only. No helmet or gorget model exists: say so on the sheet.
- **Armour:** the polished pauldron still clips at the key's highlight (about 5.5% of the lower frame; not from sky reflections, `--look-refl off` didn't change it). Outfits' metal roughness, or a lower key sheen.
- **Queue after:** Sunborn's and Saffron's ears (re-laid; check them at 40), f6's lids, brows and lashes (a dense, dark upper lash line), the red hair tuft through the plunge in chain_haul (crops in the coordinator's scratchpad `o2\h1\`).
- Gotchas: about 1 shot in 7 hung this session (look.ps1 kills and retries them). Don't `dotnet build` while a batch runs, or the later shots load the new DLL.

## Earlier start-here (11 Oct, early morning, successor 4)
In this page's history (6fc6b368): judges j1 and j2, the nape crack's cause, the rig ask.

## Earlier start-here (11 Oct, night)
In this page's history (4aa76ffe): judge n2, the throats, the seam ease, Sunborn's tone, the neck solver's c3f549ec.

## Earlier start-here (11 Oct, later)
Judge n1's start-here is in this page's history (5794c4e3); its items 1-3 are done above.

## Earlier start-here (11 Oct, agent a411e6c81f22f5c18 handing off)
Scratch F = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\181eef02-779f-45de-b419-31a949a4d27e\scratchpad\f13`. Integration and rendering 38cb3391 are merged (hair "two", the Look TAA+MSAA without DOF); 775 green at cf9e2888.
**Latest judge: `F\judge_f6\verdict.md`: neck FAIL, lids PASS WITH FIXES.** Its sheets and numbers are beside it.
- **Done:**
  - Seam at SPLIT fixed at the root (5a2f5121). The head keys' normals are held to the neck's by `tools/assets/heroine_seam.py`, run after every heroine.glb export, including heroine_outfits.py's (outfits told). The features' blue is eased out above SPLIT. The jaw-cut pads. No step at SPLIT at 1:1 (judge).
  - Per-face resting lids within ±0.011 of target (judge: no nudges).
  - `--skin-set "part:k=v;..."` dev switch.
  - `heroine_unpainted.blend` images relinked and packed (face6 backup; the graft from shipped head_tex). Local, ignored; `.prepack.blend` beside it.
  - `under_jaw` per texel (3afe6ffb); own and Highborn recut over the old cut.
  - **`People.HeadPaintFile` now loads her own paint from head_tex/heroine_head.jpg.** Before, own's paint was heroine.glb's embedded older copy, so no jaw cut on own ever showed. That is why the judge saw own unchanged. Built, not yet shot.
- **Note:** `F\seamstep.py`'s edge at x 980-1020 is the jaw line, not SPLIT. Use the solver's `F\solve1\step.py` for the seam.
- **Next, in order:**
  1. Reshoot own and Highborn (`-import`) and confirm own's cut now shows. Add a debug frame with the cut mask as colour (`F\jaw\<face>\jaw_cut.png`).
  2. Highborn's blue-violet bruise (obvious) and the grey zones on all ten: the cut must cover from the ear lobe to mid-jaw and down to the end of the grey zone, with the ramp ending on the neck and the neck's own colour (hue 17-18°, sat ~0.24). Redo all ten via `F\jaw1.ps1 -inplace -faces ...` (the blend runs now).
  3. Dark speckle under the jaw on all ten ("stubble"): fade ~50% from the jaw line to SPLIT; keep the cheek freckles.
  4. Sunborn's terracotta neck, chest and lids: tone (sat 0.37 → 0.28-0.35, hue up; SSS for dark skin).
  5. Saffron's (then Moonlit's) crease under the chin: relax the keys there, or give the graft `face_*` keys eased over 4-5 cm.
  6. **Outfits' report: a ragged pale-to-warm paint edge across her upper breasts** in every chest close-up (`...91211d34...\scratchpad\o2\judge2\` s1/s2). Probably the graft's lower edge (CUT, heroine_head.py). Ours. Tell outfits lead ace45ae43386569ed the commit when fixed.
  7. The judge's other tells: a glossy lilac band on her shoulders (body rough/spec against the face's); Moonlit's pink-red temple arc (brow tail to eye corner; a hook on Saffron and Hard-won); lower lids asymmetric R/L; brows lower and flatter than the portraits.
  8. The iris swatches after rendering's Night-grade fix (the coordinator forwards the commit): `F\gains2.py`, then the lashes (target (45,30,24)).
  9. The next judge: `F\neckrows.py` sheets plus a 70-90° profile neck tile per face and Highborn turned 40°; "Context budget: NNk" in the brief. Then the GPU re-lay of the ten paints.

## Paused before (10 Oct, agent a2d632df7c7f21ec0); its notes:
Scratch F = `S\f13` (scripts, logs, `jaw\`, `heads\`). Nothing below has been judged.
- **Applied (code, WIP 19a239bd; built art in the next commit):** eyes per the round-2 values (iris 0.117 or per face, pupil after tint with soft edge, `pupil_dark` 0.020 (0.010 rendered ~0.01 under AgX), per-face `cover` resting lids, catchlight colour/dim, whites gradient, lid shadow, wet line; new shader uniforms `catch_colour`, `catch_dim`, `ring_light`, `white_grad`, `low_lift`; `FaceShape.Iris/.Cover`); swatches recalibrated by per-channel gains (`F\gains.py`; the render puts a magenta cast on dark irises, green suppressed even under the white rig: Sloe is olive in data to read right; root cause open). Lashes repainted (`heroine_lashes.py`, darker root/tip) and lit: card shaders' `skin_lit` (1 for lashes; facing camera plus up x0.5) on the blend and coverage paths only (the plain "hash" path is still unlit: rendering's). Brows: `brow_zone` v2 (own lower/upper edges, cubic fit, forehead eased over 2 ew, `FACE_BROW_OVER`), `tint_to` on skin-like texels, `front_hair` mask; Doe and Sunborn re-laid flat into `F\heads\doe3.jpg`/`sun3.jpg` (not relayed onto the shipped heads). Hair: baby hairs lighter, flat, fewer astray; cap darkening only at fade 0.85-1; all styles rebuilt.
- **Owner's neck note, cause found and fixed (unjudged):** the grey-violet, stepped-edged patch under the jaw on every face was the face lay's paint on her neck: the portraits' necks in their jaws' shadow, laid on her. The lay's cut below the chin used the lowest forward-facing point down her middle as her chin, which was her neck's, so the front and sides of her neck kept the paint. A/Bs ruled out shadows (new dev switch `--key-shadow off|SIZE`), SSS, grain, AO, hair and the graft. Fix: `heroine_face.py` `under_jaw` (below the jaw line from `marks_drawn.json` on the front drawing, plus the jaw's down-turned underside; eased) now in the lay's cover, and `FACE_JAW_ONLY=1` mode + `tools/assets/heroine_jaw_cut.py` applied it to all ten shipped heads in place (and to doe3/sun3 as `F\heads\doe3j.jpg`/`sun3j.jpg`): the cut zone takes a smooth colour field over her head's points, held to the paint above and to her body's texture along SPLIT (her MakeHuman base was greyer/mauve and had lighter lobes along SPLIT). Face paints' alpha written as cut. `F\jaw1.ps1 -inplace -faces ...` reruns it (from the committed heads, so run it on originals only).
- **Shots:** `godot/.shots/f4_*` (the full set, fixed heads, heads 3j for Doe/Sunborn). Neck sheet `F\neck_f4.jpg`: the patch is gone on all ten. Still visible: a faint light step along the head-to-body seam (Vixen, Wildling, Hard-won most), a short stepped edge at the jaw's side under the ear (own, Highborn), a dark crease under the chin on Moonlit and Saffron (check whether geometry or paint), Sunborn's neck redder/darker than the field. A wall worth a solver if one pass doesn't clear it.
- **Left of the fix pass:** measure f4 (`F\em.py f4 ...`: pupil light 0.055-0.095, lash darkness/colour, ring colours vs targets) and adjust once; the fresh su-lead-max judge with the round-2 targets plus "each face's neck at 1:1 beside its portrait: no blotches, no violet, no band"; iterate; `dotnet test`; then report ready to merge. GPU re-lay of the ten paints still pending (the lay now carries the neck cut and the brow/tint fixes).

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

HANDOFF READY: docs/handoff/face.md on worktree-agent-a2d632df7c7f21ec0@b3ede887 (+ this page)
