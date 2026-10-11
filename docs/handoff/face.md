# Handoff: the heroine's face, hair and creation's Look

Read `docs/team/README.md` ("Working lean", "Safety"), `RESUME.md`, `OWNER_NOTES.md` (the face's order and bar; "Neck length"), this page, then `docs/team/face.md`. Read by section (grep, then line ranges). Hand off at about 300k.

## Start here (11 Oct, late morning; face successor 7 handing off at about 255k; branch `worktree-agent-a2d632df7c7f21ec0`)
Brief (coordinator): fix the lit neck, then the jaw shade and the warm jaw-edge line, to j5's numbers; reshoot ears at 40; fix and re-judge the neck sheet; then lashes, catchlights, Vixen's and Fey's jaws. Nothing to the owner (pronouns they/them) without a judge's pass. Helpers must SendMessage you or run in the foreground (j6 ran in the foreground, ~157k).
Scratch G = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18`. Scripts in `tools/scratch/face17` (copies of the .ps1 batches in G): `look.ps1` (one godot turn, runs "NAME|PRESET|ARGS"), `r7.ps1` (the judge batch, 51 shots, ~25 min), `meas.py TAG [faces]`, `trims.py TAG` + `apply_trims.py FILE`, **new:** `liftfit.py TAG LIFT_B` (body lift per face from TAG_a_/TAG_b_ shots), `softfit.py T1 TH LO HI` (env KEEPL=1 keep jaw L, CUR=1 T1 shot at People.cs's HerSoftTone; TH at `--soft-tone 0.5,0.5,0.5`), `neckpair.py OUT names` (necks at one eye-chin scale), `edgecrop.py OUT names` (jaw edge 2x), `neckprof.py`, `jawcrop.py`, `sheet3.py TAG OUT`, `neck_sheet.py TAG OUT` (env NOTCH_Y=545 for r7). Python with mediapipe: `%LOCALAPPDATA%\facefit\.venv\Scripts\python.exe`.
- **Merged integration** (4fe35e6b): hair .bin files kept ours (flipped; round 2 passed j5). 792 tests green.
- **79e3844f, WIP UNJUDGED -> judge j6 (verdict `G\j6\verdict.md`, sheets in `G\j6`):**
  - Lit neck: skin shader `body_lift` (People `HerBodyLift`, 1.0 Sunborn to 1.39 own) multiplies the non-soft lamps' diffuse on her body and her head below 3 cm over the seam (`1 - ao.g`), faded by facing (`lift_from/lift_to` -0.15..0.15 on world normal y). Fitted at `--neck-cm -3` (the spot falls on the same anatomy as the portraits'; at today's length it sits mid-neck). j6: sound at -3 (all within .02), today .03-.08 short; fade too strict.
  - Jaw shade: `soft_tone` (People `HerSoftTone`, linear RGB per face) tints the soft lamps' light outside the face mask (`1 - features.b`). Jaw chroma now within 10% on 8/10. j6 PASS WITH FIXES.
  - Trims refitted twice (k7, k14) for neck chroma.
  - Dev switches: `--body-lift X`, `--soft-tone R,G,B`, `--key-cone A`, `--look-ambient X`, `--edge-up U`, `--facing DEG` (play start heading; 0 faces the play camera).
  - Measured and ruled out: the key's cone and distance falloff (`SpotAttenuation` is distance; `--key-cone 35` no change), the sky's ambient (no effect at the Look), key shadow size and height (don't move Vixen's/Fey's jaw: their jaw spot is key-lit, a shape item). The warm jaw-edge line is the fire's edge lamp (orange, +0.35 m behind) grazing the jaw silhouette.
- **Next, in order (j6's fixes; numbers in the verdict):**
  1. Ears FAIL: Sunborn's ear beige against her brown cheek, Saffron's lighter. Carry each face's tone into the ear (paint or tone over the ear's UVs). Accept at t40 on all ten: lit helix L within .04 of the lit cheek, C within 15%, hue within 6 deg.
  2. Lift: gate it to the key only (rim and edge lamps take it now: e.g. multiply by `1 - behind`, or pass the key's identity); widen the fade to about `smoothstep(-0.45, 0.15)`; refit on a band (0.3-0.8 pupil-chin mean within .02 of the portrait's ratio, each 0.1 step within .03 except the notch, 0.0-0.2 no lighter) at both lengths on matched anatomy (today's spot 3 cm lower). Send Sunborn's profile and a 0.02-step chin profile with lift on/off (no jump over .01).
  3. Ship `--edge-up 1.3` as the default (GameFront `edgeUp`), after the whole Look frame and bust show the fire rim still on hair and shoulders, and own/Highborn/Moonlit's jaw edge at 2x has no lilac line (edge pixel within .02 L and 10 deg of 3 px either side). Then re-measure Sunborn's jaw at eu13; if still over +10% chroma, check her under-jaw paint.
  4. Far side of the neck on fair faces still reads cool grey-lilac (the owner's spot): measure 0.3 pupil-chin below the far jaw line vs the portrait's neck-side shade; hue within 5 deg, C within 15%.
  5. Vixen/Moonlit/Fey soft tones: refit at a soft-lit spot (or the fair faces' median), then check their shaded body (under the bust, inner arm) isn't yellow. Highborn's jaw .09 too dark joins the jaw-shape item (measure square-on).
  6. Play: one sunlit and one torch-lit close-up of own and Sunborn; neck/cheek within .03 of the Look's ratio.
  7. Neck sheet (`G\j6\neck_sheet.jpg`): rescale the portrait column on measured pupil-to-chin (or fix the caption); a tick at each column's own notch; play caption: her head is bowed, so the four look alike from the front too; maybe steps today/-1/-2/-3; send only once the lift holds at both lengths. Then a judge, then the main session.
  8. New tells: her lower face reads short (lip-to-chin about 2/3 of the portraits'): a level square-on render of own beside her portrait, accept within 5%; a thin light vertical line down the far side of the neck in every rim crop (UV seam or normal crease); collarbones and notch barely read at the Look; Fey's frame has the fire's bokeh disc on her jaw; Sunborn's chest glossier than her face; meas.py's clip% (armor's blown share, lower centre) is 5.74 everywhere.
  9. Hair (animation's judge 20, `G\..\an11\judge20\verdict.md`): braid stands off her back face down in death f37-43 (gravity must win; add upper-back and shoulder colliders), braid and ponytail rigid in death f19-25 (softer tip half), ponytail tip over the pauldron, long-hair wisp 7 cm above her back, long lock into the raised bracer in throw f3 (forearm capsule). I told animation (a521f0caab2e91579) not to re-shoot until the fix lands.
  10. Then lashes, catchlights, lids (values below), Vixen's and Fey's jaws.
- Gotchas (new): People.cs is BOM + CRLF (edit with the Edit tool or Python bytes; anchor replacements so 12-space indents don't match 24-space ones). Godot sometimes loses the device on a shot (look.ps1 retries only hangs): check every PNG exists before measuring. `--soft-tone` and `--body-lift` override every face. Keep the built art uncommitted as before (none new this round).

## Earlier start-heres
In this page's history: successor 6 (70568821: j5, the tuft, BodyK 1), successor 5 (214249ec: rig, nape weld, trims at 0.5), successor 4 (6fc6b368), n1/n2 (4aa76ffe, 5794c4e3), f6 (a411e6c81f22f5c18's, in 6fc6b368).

## The owner's words
- "we are striving for perfection". The bar: at the Look close-up beside each face's reference, no "this is a render" tell; grain at least 0.9 of the photo's; tones and irises within a few per cent; no seams, bands or blobs; it holds at play distance.
- Order: the face, then the paints and sliders, then hair over many rounds ("way more than 2-3").


## Eyes round-2 judge's values (most applied in 19a239bd and after: check `People.HerEyes`/looks.json before redoing; lashes and catchlight still open)
- iris_r 0.117 (per face if possible: Sunborn 0.108, Moonlit 0.109, Saffron 0.114, Wildling 0.121).
- pupil_dark 0.010, applied after `tint` in the shader (or 0.019 for her painted iris). pupil: own 0.22, Highborn 0.23, Doe 0.25, Sunborn 0.225, Vixen 0.225, Moonlit 0.255, Saffron 0.255, Wildling 0.215, Hard-won 0.23, Fey 0.29.
- Resting lids (with iris_r 0.117): own 0.03, Doe 0.035, Highborn 0.06, Sunborn 0.08; Vixen, Saffron, Wildling, Hard-won -0.05; Moonlit, Fey -0.07 to -0.08 (or the `eyes_open` slider). Lower lid over 0.05 of the iris after that: a sculpt fix for the refit.
- whites: own 1.25, Highborn 0.9, Doe 0.8, Sunborn 0.65, Vixen 0.8, Moonlit 0.85, Saffron 0.85, Wildling 0.75, Hard-won 0.8, Fey 1.0. Add the portraits' gradient (white 1.15-1.3x brighter half a radius below centre, 0.6x at +0.2 R).
- lid shadow: place it at the visible margin (-0.42 to -0.52 R on the defaults), not -0.85. Wet line: at 0.95 once the lower lid is down, plus a 10-15% albedo lift over 0.05 R.
- catchlight: catch_at (-0.15, -0.33), catchlight 0.9; in the shader `ALBEDO *= 1.0 - 0.8 * glint`, emission (0.9, 0.95, 1.08).
- Lashes REDO: the cards are unlit (paint (26,19,15) renders about 0). Light them like lid skin (normals to camera/up, or wrap) or lift the paint to about (60,42,32); target (45,30,24) at the Look; alpha capped 0.85; fan the outer lashes (alpha <= 0.6) instead of the winged wedge. Then write `head_tex/heroine_lashes.png` (the script's default output) and retire `heroine_eyes.lashes()`.


## Gotchas
- The worktree guard refuses computed paths, variables, heredocs and compound commands in Bash: write scripts and call them with literal paths.
- Godot's import rewrites hundreds of `.import` sidecars and adds `.uid`s: never commit them (stage files by name). `godot/assets` is a junction with `--skip-worktree`.
- A fresh worktree needs main's `godot/.godot` (robocopy), `f12\sidecars.py`, and a first `-import` (about 8 minutes).
