# Handoff: the heroine's face, hair and creation's Look (v12, continued)

From agent aed215ba3ca60cc29 (took over from a43570e07edbe40b2 at v11). Read `docs/team/README.md`, `RESUME.md`, `OWNER_NOTES.md` (the face's order and bar), this page, then `docs/team/face.md`. **Read code by section, not whole files** (the sections are named under "Files").

## The owner's words
- "we are striving for perfection". The bar: at the Look close-up beside each face's reference, no "this is a render" tell; grain at least 0.9 of the photo's; tones and irises within a few per cent; no seams, bands or blobs; it holds at play distance.
- Order: the face, then the paints and sliders (freckles as a Look control), then hair over many rounds.
- 6 October: "we want smooth skin aside from pores / freckles", "the breasts must look magnificent". Done (below).

## Done this session (4b568967, merged)
- The speckle over her breasts: the face-grain tile (93f66173) now only goes up her neck (the freckle maps' blue), with its outliers eased; no freckles on the front of her chest. Sheet: `docs/team/face_sheets/v12_breast_speckle.jpg`.
- Her skin's scattering is 0.1 (was 0.38): Godot's SSS smeared her paint at the Look. Grain 0.74 / 0.92 / 0.99 of her portrait's.
- Mipmaps on code-loaded textures. Dev switches: `--zoom`, `--lids`, `--tonemap`, `--grade off`.

## Next, worst first
1. **Brows too near the eyes on every face** (in eye widths, `headpose.py`: portraits 0.77 to 0.91, game 0.52 to 0.63), and too pale. The warp squashed each portrait's eye region onto the clay's narrower eyes, and the laying's match squeezed the contrast. `tools/assets/heroine_face.py` (committed with this page) has the fix:
   - `FACE_BROW_PIN`: the brows pinned to the portrait's place over each eye. Written but **not yet run**.
   - `tint_to`: a linear tint (`FACE_MATCH=add` for the old match).
   - `front_features`: the front's features laid from it alone. Tint and features measured on Doe's flat preview: brow mass 0.44 to 0.53 (portrait 0.60).
   - The plan, no refit:
     - Copy `survivorsunchained_inputs\face7\paint_<id>` and `paintL` (hers) to scratch.
     - Run with `FACE_REF`, `FACE_SHAPE=<dir>\shape.json`, `FACE_REUSE=1`, `FACE_DETAIL_GAIN 1.7`, `FACE_DETAIL_MM 2.0` on `heroine_unpainted.blend`. That's a GPU turn (Krea re-details the re-warped front). Picks: highborn_23, vixen_23, doe_37, sunborn_23, moonlit_37, saffron_23, wildling_37, hardwon_11, fey_37, and hers her_23. Then tune the gain with `FACE_LAY_ONLY=1` (Blender only), since scatter is 0.1 now. `lay_probe.ps1` with an `_old` folder reproduced Doe's paint in use bit for bit.
   - Lay the paints on the head textures **without a rebuild**. Write `heroine_face_relay.py`:
     - new raw = RAW + alpha x (new - old face paint). RAW is `tools/comfy/out/heroes/heroine_head_raw[_id].jpg`, in a43570e07edbe40b2's worktree. Check that alpha is unchanged and the edge colour moves under 1%.
     - Then `heroine_face_fixes.fix(head, path, raw=, key='face_<id>')` in Blender on `heroine_built.blend` (hers: key None).
     - Her own paint comes from heroine.glb's embedded copy, byte-identical to `head_tex/heroine_head.jpg` today. Make `People.HeadPaintFile` return that file for her own face.
   - Her brow-dye mask (`art/people/paint/brows.png`) must move with her brows, or the copper lands under them. Then rerun `heroine_grain.py`.
2. **The eyes stare, and read as a render** (no refit):
   - A resting lid per face, via `looks.json` faces plus HerFaceLife's rest under blinks. Try values with `--lids`: Highborn about 0.18 (0.15 hid 0.16 of the iris; portrait 0.19), hers about 0.06, Sunborn about 0.12, Doe 0.
   - Irises: radius 0.12 to about 0.13, hers only (the hero shares the shader). Their paint is too saturated, with a hard limbal ring; the pupil reads large; the catchlight is small.
   - Lashes: MakeHuman's dense black winged lashes, scissored at 0.35, make a hard band. That's the biggest tell. Needs a new, finer dark-brown paint and a softer edge. The paint also has a faded rectangle across one upper strip.
3. **Upper lips 13 to 37% thin in the sculpt** (`fair.py` on the clays against the portraits; Sunborn 0.038 vs 0.060, Fey 0.034 vs 0.047, hers 0.033 vs 0.047). The `lips_upper` slider only pouts. This needs a per-face sculpt, then that face's paint re-laid, then **one refit**: gather every head change first and tell main when `heroine_built.blend` is new.
4. **Neck grain:** half her portrait's neck's (neck/face 0.34 / 0.29 / 0.28 against 0.46 / 0.45 / 0.39). The tile is outlier-free now: raise `HerGrain` and check at 1:1.
5. The old list: the book by day is flat; the spots at her jaw's edge (her right). The chest flake is closed: neither this session's bust shots nor the outfits lead's show it. Then the paints and sliders pass, then hair (with the rendering lead's AA).
6. Unconfirmed, from the outfits lead: her nipple bumps sit 8 to 9 mm above her painted areolas' centres (paint and sculpt out of register). Agree with them who takes it, then check at 1:1.

## Decisions and failures (why)
- **Scatter:** 0.2 smears as much as 0.38.
- **Brows:** the `brows_height` slider is no use (gap 0.52 to 0.60 at 1.0, looks surprised). Mipmaps, 4K and linear downscaling didn't change them either. The causes are the scatter, the laying and the warp.
- **AgX** (the world's tone curve) pales her lips and lifts darks unshaded; under the white rig the lips are near. Secondary, and rendering's domain.

## Gotchas
- The worktree guard refuses compound shell commands and computed paths: write scripts. PowerShell drops `''` arguments.
- Build before every batch. `dotnet test` compiles only `logic/`, so it's safe during shots. 1440p shots come out 2526x1421.
- `regions.py`: the first picture sets the scale. MediaPipe's irises are rough on renders, and its brows on clay are guesses.
- A camp ember can drift in front of her at the Look.
- The legal motion check appends code at the end of her skin shader's `fragment()` (the outfits lead's 4934a39e): keep its last statements free to append after.
- ComfyUI isn't running. Start it headless (untried this session) from `%LOCALAPPDATA%\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI`, using its `.venv\Scripts\python.exe main.py --listen 127.0.0.1 --port 8188 --extra-model-paths-config "%APPDATA%\Comfy Desktop\instance-model-paths\inst-1790761498447.yaml"`, under a gpu turn. POST /free after.

## Scripts and collaborators
- Scripts: `tools/scratch/face9` (this session's: `fair.py`, `headpose.py`, `irisw.py`, `speck.py`, `regions.py`, `lay_probe.ps1`, `preview_front.py`, `clay_now.py`, `mouth_probe.py`, batches) and `tools/scratch/face8`. Copy both to your scratchpad and run `repoint9.py` (edit its paths first). Measures run with `%LOCALAPPDATA%\facefit\.venv\Scripts\python.exe`.
- Collaborators: main (reviews, merges, refits); rendering a20bdef993e00f26b (the AA, the TAA's share of the finest grain); outfits afb34c385770877d3 (told about the skin).

## Files (read these sections)
- `People.cs`: Skin, HerScatter, HerGrain, HeadPaintFile, HerPaint.
- `heroine_skin.gdshader`: fragment.
- `heroine_face.py`: from_reference, front_features, tint_to, the laying.
- `heroine_face_fixes.fix`.
- `heroine_freckles.py`: the graft section.
- `HerFaceLife.cs`: _Process.
- `looks.json`: faces.

HANDOFF READY: docs/handoff/face.md on worktree-agent-aed215ba3ca60cc29@HEAD
