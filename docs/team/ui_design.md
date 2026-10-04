# UI design (and the UI merge): status

Agent ac76f400913a109cd (successor to a5629aff0f215ea4a, whose handoff is `docs/handoff/ui_design.md`),
branch `worktree-agent-ac76f400913a109cd` (includes the integration branch at 780e256 and 51350b1).

## Current state: the heroine's character creation (stopped mid-way at the owner's usage limit)
Built and pushed (472 tests green), **not yet seen right on screen**:
- **Saved and worn**: `CharacterData`/`CreationChoice` keep `Face` (slider -> value, only those moved),
  `Eyes`, `Paint`; `PersonSpec` carries `Face`, `Eyes`, `EyeRing`, `Paint`; `Loadouts.Of` gives her
  her hairstyle at last (`Loadouts.HerHair`: hers, or an old save's cut mapped to the nearest).
- **Data** (`data/content/looks.json`): `herHairs` (5 cuts with words), `eyes` (9, iris + ring
  colour, in-world names), `paints` (8 with sheen/metal), `faces` (7 presets), `sliders` (25, grouped
  Eyes/Nose/Mouth/Jaw, end words, tasteful `min`/`max` judged from renders), 5 more hair colours.
- **View** (`src/Actors/People.cs`): `LookOf(spec)`, `HerRestyle` (hair cut/colour, skin, eyes, face,
  paint changed on her where she stands), `HerEyes`/`EyesOf` (read after her corrective layer via
  `SkeletonUpdated`), `HerPaint` (a next pass, `shaders/heroine_paint.gdshader`), `EyeColour`.
- **Eye shader**: iris recolour (`recolour`, `iris_colour`, `ring_colour`): fibres kept, verified on
  all 9 colours in renders.
- **Creation** (`Ui/Front.cs`, new `Ui/CreateLook.cs`): five steps (Calling, Arms, Origin, **Look**,
  Name); Look has parts Body/Hair/Face/Paint (him: Body/Hair) on LT/RT; cameos for cuts, faces and
  paints (`art/ui/create/*.png`, glyph until painted; cuts dyed live by a mask), beads for colours
  (eyes drawn as her own iris, `shaders/ui_iris.gdshader`), `Groove` sliders; drag/wheel/double
  click and the right stick (`Controls.Look`) turn her and frame her (`GameFront.UpdateCreate`:
  full, head and shoulders, face; longer lens, DOF behind her). Defaults to the heroine. Name step
  reads back each step. The figure slider is gone (no effect on her body).
- Tools: `tools_scenes/face_sheet.gd` + `FaceSheet.cs` (her looks side by side via the real code).

## Next (in order)
1. **Shoot the Look step** (`--new --keys TabNext,TabNext,TabNext[,SubNext...]`; the first shots
   only reached step II: the key tour needs longer `--seconds` or a `--step` arg) and fix what shows.
2. **Face paint art**: write `tools/assets/heroine_paint.py` (head UV <- cylindrical face sheet
   reprojection from heroine.glb; brush-stroke designs) -> `art/people/paint/<id>.png`; plus a
   **brow dye** layer (her brows are painted copper in the head texture, wrong with other hair colours).
3. **Cameo portraits**: render via FaceSheet (hair cuts in grey + `_mask`, faces, paints), paint them
   over, register in `tools/comfy/ui_assets.json` and UI_ART_BRIEF for the UI art lead.
4. Pad focus audit of the Look step; UI_DESIGN 7.2 rewritten.
5. Then the handoff's list: announcements, item card, journal deeds/codex, HUD dash and draught.

## Key decisions
- Creation opens on the heroine (the docs call the survivor "the heroine"; a man remains a choice).
- Slider ends are capped where the shape keys break (renders): e.g. cheeks +0.25, eyes_height +0.25.
- Face paint is a separate pass over her skin, so the skin shader (main session's) is untouched.

## Notes for other areas
- Main session: long/ponytail show a pale strip at her left temple; brows don't follow hair colour.
- UI art (a72467cac33063d3a): cameo portraits and a swatch setting will be registered (step 3).
- Scratchpad: mine is `scratchpad/uid2/` (`shot.ps1`, `fs.ps1` face sheets, `crop*.py`).
