# Handoff: the heroine's face, hair and creation's Look (v12, continued)

From agent abe65bc929823a791 (took over from aed215ba3ca60cc29). Read `docs/team/README.md`, `RESUME.md`, `OWNER_NOTES.md` (the face's order and bar), this page, then `docs/team/face.md`. **Never Read a whole file** (whole-file reads were my largest context cost): `grep -n`, then `sed -n 'A,Bp'` (or Read with offset and limit) on the lines you need; the sections are named under "Files". Hand off at about 300k.

## The owner's words
- "we are striving for perfection". The bar: at the Look close-up beside each face's reference, no "this is a render" tell; grain at least 0.9 of the photo's; tones and irises within a few per cent; no seams, bands or blobs; it holds at play distance.
- Order: the face, then the paints and sliders (freckles as a Look control), then hair over many rounds. 6 October: "we want smooth skin aside from pores / freckles" (done, v12).

## Done (ca7efb10, pushed; nothing in it changes what ships)
- `heroine_face.py` `from_reference`: the predecessor's `FACE_BROW_PIN` crashed every run (the warp's landmarks shadowed `src`, the reference picture); fixed. Pinned alone, the brows folded the warp: MediaPipe's guessed forehead points just above them held while they moved, a band stretched 12 to 25 times, and Sunborn's brows came out as streaks. New `brow_zone()` pins the brows **with** the landmarks round them (lid crease to just over the brow, in each eye's frame: Doe 13, Sunborn 22). `FACE_BROW_PIN` is a fraction (0 as before, 1 the portrait's place). Stretch 0.55 to 1.24 at 1.0, 0.74 to 1.02 at 0.6 (`face10/warp_diag2.py`). `free()` copes with no ComfyUI, so `FACE_DETAIL=0` runs need Blender only.
- `heroine_face_relay.py`: a face's new paint laid on its head texture without a build (raw + alpha x (new - old)), then `heroine_face_fixes.fix` in Blender. Doe and Sunborn: alpha unchanged, the soft edge moves 0.7%.
- `heroine_lashes.py` (not shipped): lashes painted hair by hair on her four lash cards (grids read from HeroineLashes, 13x5 upper and 12x5 lower; roots by arc length; 128 upper at 4-10 mm, 42 lower at 2-6 mm; tapered, dark brown to lighter tips). Trial `lashes_d.png` in my scratch. The shipped paint is MakeHuman's, near black, with a faded rectangle on one upper strip (`heroine_eyes.lashes()` cuts rows at 54%). The cards' outer wing runs to 15 mm, so the new paint stops short of it.
- Game: looks.json faces "lid" (`Lore.FaceShape.Lid`; none set, so 0) feeds `HerFaceLife.Rest`, set in `People.HerFaceKey`. Lids run from rest to shut; `--open-eyes` holds them at rest. Dev switches: `--rest-lid X`, `--head-paint PATH`, `--lashes PATH` (`People.TryFile`: any picture, mipmapped). The lashes' AlbedoColor is white, since their colour belongs in the paint (the shipped paint is black either way: 9/255 at most).

## In progress: the brows (decide the pin)
- Test lays (no Krea) in my scratch `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\0b33992d-1e38-4eb8-80a1-d5c23b1a44e6\scratchpad\face10`: `pz_<face>_<frac>` (doe and sunborn, at 1.0 and 0.6), and relayed heads `heads/<face>_<frac>.jpg` (no fixes). Flat sheet `c_pt_doe_11.jpg`: Doe's new brows are dark and full like her portrait's (the old ones are thin, grey and on her lid). **Not yet seen in the game.**
- The question is the brow ridge. On the clays MediaPipe has the brows (and the rim's shadow) 0.47-0.55 eye widths over the corners; the portraits have them at 0.72-0.85. A full pin lifts them 38 px (Doe) to 60 px (Sunborn), 6 to 10 mm. If at 1.0 they sit above the bone when lit and turned, take 0.6 to 0.75, or raise the brow ridge in the sculpt with the lips (the same refit).
- `tint_to`'s gains are large (linear: Doe 1.3/1.8/2.3, Sunborn 2.3/3.7/5.3), but it keeps each feature's depth. After any re-lay, refit `People.HerFaceTone` (fitted to the old paints).

## Next, in order
1. **Brows A/B:** `face10/look_ab.ps1` (takes the godot turn; runs "NAME|PRESET|ARGS"). For example `doe_old|doe|`, `doe_10|doe|--head-paint <scratch>\heads\doe_1.0.jpg` and the 0.6 head, each also with `--turn 40` and `--rig-white`. Then look at 1:1 beside the portraits (`face10/pair.py`) and decide the fraction.
2. **The rendering lead's hair results** (7 October; it's handing off too). Branch worktree-agent-a7afb4d33cdd5efba @ 293ed039 (a switch only). Sheets: `docs/team/perf_sheets/c1_look_pony_x2.png` and `c1_look_long_turned.png`; frames in its worktree's `godot/.shots/c1_*`.
   - Blended cards: no speckle, a clean hair-to-cheek edge, full soft lashes, no card-order errors at +-40. "two" is dropped.
   - Still short: blended hair shimmers under FSR 2 (theirs: the reactive mask), side hair is soft on dark ground, and (ours) lock blocks and pale temples.
   - Look at both sheets and answer its successor.
3. **Lashes:** shoot `--lashes <scratch>\lashes_d.png`, on the blended path too. Then `blender -b heroine_built.blend --python tools/assets/heroine_lashes.py` writes the real one; retire `heroine_eyes.lashes()`.
4. **Resting lids and irises:**
   - Try `--rest-lid` per face. The predecessor's tries with `--lids`: Highborn about 0.18 (0.15 hid 0.16 of the iris; portrait 0.19), hers about 0.06, Sunborn about 0.12, Doe 0. Set looks.json "lid".
   - Irises, hers only (the hero shares the shader), in `heroine_eye.gdshader` and `People.HerPart`: radius 0.12 to about 0.13, a less saturated and contrasty paint, a softer limbal ring (0.62), a smaller pupil (0.28), a larger catchlight.
5. **One sculpt, one GPU re-lay, one build, one refit:**
   - Upper lips are 13 to 37% thin in the sculpt (`face9/fair.py`: Sunborn 0.038 vs 0.060, Fey 0.034 vs 0.047, hers 0.033 vs 0.047; `lips_upper` only pouts). Sculpt per face (`face_shapes.SCULPTS`, into each `face_<id>` key), maybe the brow ridge too.
   - heroine_head.py with `HEAD_UNPAINTED=1` (art to a scratch folder) for a new `heroine_unpainted.blend`.
   - The ten faces with Krea: `face10/pin_test2.ps1 -detail 0.3`. It takes only the blender turn, so take gpu too and start ComfyUI.
   - The full build; tell main for the refit. The brow-dye mask (`art/people/paint/brows.png`) must move with her brows; rerun `heroine_grain.py`. Consider q95 4:4:4 head JPEGs (now q92 4:2:0; freckles are partly colour).
6. **Neck grain:** half her portrait's (neck/face 0.34/0.29/0.28 against 0.46/0.45/0.39); raise `People.HerGrain` and check at 1:1.
7. **The old list:** the book by day is flat; spots at her jaw's edge (her right); unconfirmed from outfits, her nipple bumps sit 8-9 mm above her painted areolas' centres (agree who takes it).
8. Then the paints and sliders, then hair. I promised rendering to sort cards per layer by distance from her scalp in `heroine_hair.py`.

## Decisions and failures (why)
- Scatter stays 0.1 (0.2 smears as 0.38 does). The `brows_height` slider is no use (she looks surprised). AgX pales her lips (rendering's to fix).
- Her own face's paint stays heroine.glb's. `HeadPaintFile` returning `head_tex/heroine_head.jpg` (byte-identical today, and relayable without a glb) isn't yet seen in a shot, so I reverted it.

## Gotchas
- The worktree guard refuses compound shell commands and computed paths: write scripts. PowerShell drops `''` arguments. Build before every batch. `dotnet test` compiles only `logic/` (safe during shots). 1440p shots come out 2526x1421.
- `regions.py`: the first picture sets the scale. MediaPipe's irises are rough on renders, and its brows on clay are guesses. A camp ember can drift in front of her at the Look.
- The legal motion check appends code at the end of her skin shader's `fragment()`: keep its last statements free.
- ComfyUI isn't running. Under a gpu turn, start it headless from `%LOCALAPPDATA%\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI` with `.venv\Scripts\python.exe main.py --listen 127.0.0.1 --port 8188 --extra-model-paths-config "%APPDATA%\Comfy Desktop\instance-model-paths\inst-1790761498447.yaml"`. POST /free after.
- A fresh worktree needs:
  - `godot/assets` as a junction to its own `public/assets` (`git update-index --skip-worktree godot/assets`, the placeholder to the Recycle Bin);
  - main's `godot/.godot`;
  - the missing sidecars (`face10/sidecars.py`). Never commit sidecars.
- `face10/preview_lit.py`'s lights are lowered but not re-shot.

## Scripts, files, collaborators
- Scripts: `tools/scratch/face10` (mine; `repoint10.py` copies face8's and face9's into a scratch folder, repointed), `face9`, `face8`. Measures run with `%LOCALAPPDATA%\facefit\.venv\Scripts\python.exe`.
- Files (by section):
  - `heroine_face.py`: from_reference, brow_zone, front_features, tint_to.
  - `heroine_face_relay.py`; `heroine_lashes.py` paint; `heroine_face_fixes.fix`.
  - `People.cs`: Skin, HerPart, HerFaceKey, HerHeadPaint, HeadPaint, TryFile, HerScatter, HerGrain, HerFaceTone.
  - `HerFaceLife.cs` _Process; `heroine_eye.gdshader`; `looks.json` faces.
- Collaborators: main (merges, refits); outfits a1f120018d8749c97; animation ae2a9884e3e51609c.
- Rendering a7afb4d33cdd5efba, handing off. Its hair path is `--hair-draw hash|blend`. On blend, a lash's cover is its paint's alpha as painted, and alpha 0.99+ goes into the depth prepass.

HANDOFF READY: docs/handoff/face.md on worktree-agent-abe65bc929823a791@HEAD (code ca7efb10)
