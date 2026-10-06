# Handoff: the heroine's face, hair and creation's Look

From agent a2f7b0f1283f6144a (took over from a6007bf07fd45ab0d at v8e).
Read `docs/team/README.md`, `docs/team/RESUME.md`, then this page, then `docs/team/face.md`.

## The owner's words
- "all of the pre made faces are kinda ugly"; "for premade faces generate beautiful ones with our local ai hookup".
- "the customizations don't do enough to change".
- The face must read at every in-game zoom except the farthest.
- "face is doing a great job, keep up the work". "the face lead can keep improving till we run out of credits". The bar: "we are striving for perfection".

## The brief
- Keep improving her, and every preset face, at the Look close-up and at play zoom, in order of what most improves her. Each time a version is good enough to ship, tell the main session. It refits the outfits on this worktree's `tools/comfy/out/heroes/heroine_built.blend`, then merges. Any change to her head or body geometry, or to her normals, needs that refit. Paint and shader changes alone don't.
- After a refit, rerun creation's portraits yourself on your branch (`heroine_paint.py brows`, then `creation_portraits.py --sex female`, then the Look shots), commit them and tell the main session.
- The Look's light (`GameFront.PortraitLight`) ships as it is. Judge skin under `--rig-white` too, but ask the main session before changing the light.
- Rules:
  - Krea 2, TRELLIS 2 and MoGe-2 only.
  - Don't edit `heroine_outfits.py`.
  - Never commit `heroine.glb` or the outfits.
  - Take turns with `tools/turn.py` (`gpu`, `blender`, `godot`).
  - Batch shots and look once.
  - British spelling.
  - Run `dotnet test` before every commit.
  - At each milestone, commit, push and update the status page.

## Done
- **v9** (5094608d, merged): her lips meet again, because v7's `portrait-heroine.target` is back.
- **Portraits** (3a60d682, merged): `creation_portraits.py` and `Portraits.cs` put each face on as `CreateLook.Choose` does: its `faceShape` key and painting, its skin and its eyes. Before that, all ten portraits were her own face.
- **v9b, half done** (code committed; the main session has not refitted it). Her lips' white slivers at a turn are gone: `heroine_skin.gdshader` occludes her sheen by her AO (`SPECULAR *= smoothstep(0.45, 0.95, ao)`). They were the rim light on her lips' inner linings, not teeth; `teeth_probe2.py` sees no tooth from ±30 degrees yaw or ±20 pitch, any face. `heroine_head.py` joins her body's split normals along her middle (797 corners).

## Next (worst first)
1. **The throat band** (the portraits' dark vertical line down her throat and chest under their side key; the main session wants it gone before the portraits are merged again). Known:
   - It comes with the key alone (`LIGHTS=1,0,0`), with the key's shadow off too, and is gone without the key.
   - The NormalBuffer shows a step there.
   - Joining her middle's split normals did not move it; nor did rounding her throat's normals across her middle (tried in `heroine_head.py`, reverted).
   - Her throat's front is her head mesh down to her lower neck, then her body (`side_light.py` colours them).
   - A clay render under a side light shows her upper chest's normals broken into faceted shards. These are the "pale patches on her upper chest" in the Look. Tell the main session, whose body it is.
   - Next to try: the band in Blender under the portrait's exact light and camera (`side_light.py`, camera from her front at yaw -14); her head mesh's own neck normals (`normals_split_custom_set_from_vertices(hn)`); Godot's SSS (skin mode) at a terminator.
   - Then rebuild (`build_v9.ps1 -rest`; the worktree's built blend still holds the reverted rounding), send the blend for one refit, and rerun the portraits on your branch (`portraits.ps1`) once it's refitted.
2. **v10, skin grain.** The code is in `heroine_face.py`, committed with v9b.
   - The fix: each view is split into broad colour, blended as before, and fine detail finer than `FACE_DETAIL_MM`, taken from the view that sees it most squarely (weights^6). `match` now cuts only the broad band's contrast. `FACE_DETAIL_GAIN` scales the detail.
   - Her trial `quick_her.ps1 -gain 1.7 -mm 2.0` (shot q2) reaches about 0.87 of the portrait's grain at the mid scales (`fair_grain.py`).
   - Run `lay_all.ps1 -gain 1.7 -mm 2.0`; it needs no GPU, because `FACE_LAY_ONLY` re-lays from the paintings in each `paint_<id>` folder. Then `build_v9.ps1 -rest`, `shots_v8.ps1 -tag v10 -nocal` and `shots_white.ps1 -tag v10`.
3. **Preset tones.** Run `tone_fit.py v10` with the facefit python on the white-rig shots. It prints the factor each skin needs and new looks.json swatch colours: un-eased for Rose, Warm and Brown, and her own tone (`People.SkinTone`) for Fair.
   - Under the white rig, Sunborn needs (0.88, 0.73, 0.59) in linear light; she is lighter and greyer than her portrait.
   - Her own Fair is about 12% redder in R/G than her portrait, even under white light.
   - Swatches change for every face that shares them, and the beads show them.
4. **Hair, broad strokes.** The atlas's strands are under a texel wide, while a card is 256 texels across 1.2 to 4 cm. At the close-up about 3.3 texels fall to a pixel, so each card averages flat. The plan, in `heroine_hair.py draw_atlas`:
   - Group each column's strands into wisps 1 to 3 mm wide, with a shared sway, a shade and an id per wisp, and thinner gaps between wisps.
   - Run the hair with the `atlas` argument to redraw it.
   - Also measure her default "as it grew" red (the shader's `colour` 0.56, 0.17, 0.07) against her_23's copper. It reads blood-red beside the portrait.
5. **Eyes.**
   - The key's catchlight is a white blob as big as her pupil (cornea `wet_rough` 0.035, a big spot light); the portrait's is small and crisp. Try `--eyeparam wet_rough=...`.
   - Sloe and peat are a little dark.
6. **Brows** read faint and grey beside her_23's copper brows. They are painted from the reference, and `heroine_paint.py brows` dyes them.
7. A pale wedge under her jaw at a turn. Behind her neck, the Tail reads as a dark shape in front view; it is the tail, not a fault.

## Measuring (scripts in the scratchpad's `face6/`; inputs in `face4/`; run the measures with `%LOCALAPPDATA%\facefit\.venv\Scripts\python.exe`)
- `fair_grain.py`: grain with every face scaled to 380 px tall. `skin_sample.py`'s grain is relative to picture height, so a 1536 portrait shows grain a 1080p face can't.
  - Portrait: 0.021 / 0.033 / 0.051 at s0.8 / s1.6 / s3.2.
  - v9: 0.011 / 0.022 / 0.037.
  - q2: 0.014 / 0.029 / 0.047.
- `same_size.py`: faces side by side at one size.
- `skin_ratio.py TAG`: each preset's skin against hers, beside the same ratio for the portraits.
- `tone_fit.py TAG`: the new tones.
- `teeth_probe2.py`: the whole mouth, every face, many views.
- `seam_probe.py`: the normals along her middle.
- `clay_views.py`: clay renders. `uv_front.py`: a texture seen unlit from the front.
- `build_v9.ps1 -unpainted|-paint|-rest`, `quick_her.ps1` (her paint re-laid, head, shots), `lay_all.ps1`, `shots_v8.ps1`, `shots_white.ps1`, `portraits.ps1` (import, portraits, Look shots).
- Shot flags: `--skinparam`, `--rig-white`, `--no-taa`, `--mipbias`, plus the older `--open-eyes`, `--unshaded`, `--debugdraw`, `--eyeparam`, `--rig`.

## Findings that save time
- Her paint, not the renderer, held half the grain. Mip bias (global or her paint's own) changed nothing. TAA removes the finest pixel-scale grain (about 0.6x at s0.8); that is the renderer's limit.
- Under the white rig she is hardly pink. The pink in the Look is the warm key and the fire's edge light.
- The portraits' dark band was there with the key alone and with its shadow off, and gone without the key. The NormalBuffer showed it: normals, not light or paint.

## Gotchas
- **ComfyUI may be down.** `heroine_face.py` then fails at Krea's detail and copies the old paint. Start it headless:
  - Python: `C:\Users\munch\AppData\Local\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI\.venv\Scripts\python.exe main.py --listen 127.0.0.1 --port 8188 --extra-model-paths-config "%APPDATA%\Comfy Desktop\instance-model-paths\inst-1790761498447.yaml"`.
  - Run it with `Start-Process` from that folder.
- **`turn.py` queues you behind yourself.** Taking a turn under a name you already hold waits behind your own hold. Give it back before a script takes it again.
- **The `godot/assets` junction.** It must point at this worktree's `public/assets`. Set `git update-index --skip-worktree godot/assets`.
- **Copied `.import` files.** Copying `godot/.godot` from another worktree saves a long import, but about 1000 `.import` files then show as modified. Never commit them, but do commit the `.import` of a new file.
- **Building with C# changes.** `dotnet build godot/SurvivorUnchained.csproj` after editing C#, before shots.
- **The worktree guard.** It refuses git run through cd into another worktree, and complex heredocs. Write a small script file instead.

## Collaborators
- The main session (coordinator) reviews, refits on the built blend and merges. Message it, not UI design, which is paused.
- The male hero (paused) shares the eye shader.

## Files to read first
- `docs/team/face.md`
- `tools/assets/heroine_face.py` (the laying)
- `tools/assets/heroine_head.py` (`matched_base`, normals)
- `godot/shaders/heroine_skin.gdshader`
- `tools/assets/heroine_hair.py` (`draw_atlas`)
- `face6/build_v9.ps1`, `face6/lay_all.ps1`

HANDOFF READY: docs/handoff/face.md on worktree-agent-a2f7b0f1283f6144a@HEAD
