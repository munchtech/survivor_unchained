# UI design (character creation first): status

Agent a69858664f1d3dd29, branch `worktree-agent-a69858664f1d3dd29` (integration branch merged in at 8da202d).
Predecessor's handoff: `docs/handoff/ui_design.md`.

## How the owner reaches character customisation
**New Journey; the Look is step II**, straight after the calling (Calling, Look, Arms, Origin, Name).
- Step I has a card under the callings with her portrait, "II · Her look". Its Next button says "Next: her hair, face and paint".
- The Look's parts are Hair, Face, Shape, Paint and Body (tabs, or `,` and `.`, or LT and RT).
- To turn her, drag; the wheel or a double click brings her face near.
- **Old builds:** the title's foot says when the code was built. If any `.cs` file is newer than the build, an ember line says to open the project in Godot and press Play. (Run from the project manager, Godot starts the last build without making a new one.)

## Current state (pushed; 565 tests green)
- **Cameos are her portraits**, rendered from the game by `tools/assets/creation_portraits.py` (`tools_scenes/Portraits.cs`) into `art/ui/create/female/`. Cuts are rendered grey with a mask, and the cameo dyes them the chosen colour.
  Rerun it after any head, hair, face or paint rebuild: `python tools/assets/creation_portraits.py [hair|face|paint|look]`.
- **Face paints were retuned as seen on her** (`tools/assets/heroine_paint.py`):
  - kohl is bold, with a wing;
  - woad is a brow band plus cheek stripes;
  - ochre and blood are opaque;
  - ash is pale;
  - gilt runs along the cheekbones.
  Colours lean against AgX, which turns blue violet and deep red rust.
- **Brows are dyed her hair's colour:** a pass in `heroine_paint.gdshader` finds each painted hair under the `paint/brows.png` mask. Dark colours look right. Fair ones read a little flat and cool on the shadow side.
- **Face and Shape are split.** Shape has the column to itself, with its group tabs four to a row. A face to start from may set `skin` and `eyes`.
- **The male hero's fields are agreed and built:**
  - `HeroLook.Beards`;
  - `BeardStyle` on CharacterData, CreationChoice and PersonSpec;
  - a Beard row in his Hair part;
  - `HeroKit(sex) = Lore.Hero(sex)`, so `heroes.male` in looks.json turns his Look on.
- The plaque rule no longer runs through titles. Self's standing lines have stat icons.

## Next (in order)
Handed off at the context limit: `docs/handoff/ui_design.md` is the successor's brief.
1. Launch blocker: a Credits and Licences screen (from the title and pause menu, built from
   `public/assets/CREDITS.md`) and a `licences/` folder in the export; wording checked with legal.
2. Place the UI art lead's pieces as they land (header, backdrop layers, column divider, card_light,
   hero plate, section rule).
3. The experience director's map result and atlas screens.
4. Rerun paints and portraits after the face lead's new head; the male hero's portraits when his body lands.
5. The crafting lead's pack bugs (doll T-pose on Refresh, PlayerView rebuilt on every G.Gear).
## Waiting on others
- **Face lead (ade92e8285938438f):** new head, faces and 47 sliders in 8 groups. After the main session writes `heroine.glb`, I rerun `heroine_paint.py` then `creation_portraits.py`. `LoadoutTests` expects 25 sliders, and the face lead updates that.
- **Male hero (ab82cbe99e2937ddd):** will write `heroes.male` and his builder. I then render `creation_portraits.py --sex male` (Portraits.cs builds her only today).

## Key decisions
- Look is step II: the calling dresses her, then she is shaped. A woman or a man is chosen on step I.
- Portraits are rendered from the game, not painted by hand, so they stay true when her head changes. The painted pass goes over them.
- Paint is laid thick where it is meant to be solid. A thin coat over skin changes its hue in the tone mapping.

## Notes for other areas
- Main session: the title warns about stale builds, so the owner can see when to rebuild.
- UI art: register the paint-over of `art/ui/create/female/*.png` once the faces settle. Paint the cut images in grey and leave their `_mask` as is.
- Scratchpad: `scratchpad/uid3/` (`shot.ps1`, `por.ps1`, `paints.ps1`, `grid.py`, `c1.py`, `edlib.py`).
