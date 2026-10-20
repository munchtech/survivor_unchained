# Brief S2: a kit-sheet painter, the well, one stall, one folk palette (style r2, E3 jobs 2-4)

Context budget: 200k. You're a code solver at medium effort for art-style lead 3, who is waiting on you in the foreground: **your final message is your report** (under 30 lines; no SendMessage needed).

**Worktree:** `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\art-style`, branch `art-style`. It has its own `godot/assets` junction (into its own `public/assets`), so never `git stash`, `git reset --hard` or `git checkout .` there, and never write into `public/assets` (it's shared art: your outputs go to a new override folder). `git add` named files only: never the ~1,146 line-ending-only `.import` files or the stray `.uid` files. Commit as you go, with messages ending `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Godot runs need a turn: `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "art-style: kit paint" --wait 1800`, given back straight after (frames.py does this for shots). Never kill processes by name.

**Sharing the worktree:** the lead's light sweep is shooting in this worktree, and each of its calls runs `dotnet build`. So **until the file `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\746784c6-95b9-4ef2-95bf-f24b9874f4bb\scratchpad\art_style\lead3\sweep_e1.log` contains `SWEEP DONE`, don't edit any `.cs` or `.gdshader` file, and don't build, import or shoot.** Do the Python tool and the painted sheets first (check every 60 s once you're ready to build; go ahead after 60 min anyway).

## The goal
We're proving a signature look in engine: painterly realism. Forms stay real, but surfaces read as painted: simplified texture detail, value shapes over micro-detail, crevices darker and top edges lighter (painted in), warm and varied colour. No outlines, no cel look. The bar is the painted target `C:\Users\munch\Desktop\survivorsunchained_inputs\art_style\r2\target_town.png` (a Krea preview, never shipped). Look at it once at full size, and once at 1:1 crops of the well (about x 260-560, y 250-560) and of the blue-white stall at the lower right (about x 1220-1620, y 760-1080). Today's engine frame at the same camera is `C:\Users\munch\Desktop\survivorsunchained_inputs\art_style\r1\A_town.png`. **Build with our own shippable tools only** (numpy/OpenCV/Blender, our code), never Krea or any AI image model: the proof must show the real pipeline. Everything sits behind a flag, default off.

## What the target shows
- **The well:** a rough stone ring with light painted tops and dark gaps, warm terracotta round tiles on the roof (the kit's own `RoundTiles`, if the well's roof uses it; check), and warm painted wood. Today it reads toy-clean: a grey, even ring and a flat plank roof.
- **The stall:** sun-faded painted canvas stripes with soft folds and a darker valance shadow, plus warm painted wood.
- **The folk:** warm, varied clothes (ochre, madder red, moss, indigo, undyed linen), never grey.

## The jobs, in order
1. **The sheet painter, a reusable tool** (`tools/assets/paint_tex.py`, a CLI with `--help`): it turns a kit BaseColor plus its normal map into a painted albedo.
   - Edge-preserving simplification at texel scale (flat patches that follow the forms).
   - Cavity and AO from the normal map baked in: darker crevices, lighter top edges.
   - A palette shift toward the target (warm, with dull midtones gaining the most).
   - A gentle stroke texture along the dominant direction (the wood's grain, a stone's long axis), low contrast. A screen-space brush filter adds a stroke hand on top, so keep this one subtle.
   - Run it on the sheets the well uses: `public/assets/env/village/T_UnevenBrick_BaseColor`, `T_RockTrim_BaseColor`, `T_WoodTrim_BaseColor`, `T_RoundTiles_BaseColor` (KTX2 2048; check which sheets `public/assets/env/custom/Well.gltf` really uses; it's built by `tools/models/well.py`). Write the results to an override folder in the repo, git-ignored if large (say `godot/art/kit_paint/`), in a format Godot loads, at today's sizes.
   - Add a Godot flag `--kit-paint DIR`: `KitMaterials.Get` in `godot/src/World/Landmarks.cs` swaps a material's albedo when DIR holds a file with that texture's name. Those sheets are shared with the village houses, so the houses change too. That's fine for the proof, but say so.
2. **One stall:** the stalls come from `godot/data/zones/waystation/landmarks.glb` (made web-side in `src/world/zones/waystation.ts` ~327-370; the awnings are 64x8 px stripe PNGs with flat-colour posts). Under `--kit-paint`, give the blue-white stall in the square (lower right in town frame 00) a painted canvas texture (stripes with soft folds, a darker valance shadow, sun-faded) and painted wood. Find it by mesh or material name, and make the texture with your tool or a small generator in the same file.
3. **One folk palette:** the folk's looks are `godot/data/content/folk.json` (`looks`: `model`, `tint`, `under`), read by `godot/logic/World/Lore.cs` (`NpcDef.Tint`). Find where the tint reaches the material. Under `--kit-paint DIR`, a `DIR/folk.json` overrides the look of one villager seen in town frame 00 to a warm palette (ochre or madder with undyed linen). If two are visible, do both.

## Acceptance (give the numbers)
- `dotnet build godot/SurvivorUnchained.csproj -v q -nologo` is clean (no new warnings). `dotnet test godot/tests/Tests.csproj` passes (pass/fail/skip).
- **Flag off:** a town frame matches one shot before your change, at `fps=30`. Report the max and mean abs diff against the run-to-run noise (shoot it twice).
- **Shots,** from the worktree root:
  `python tools/scratch/art_style/frames.py k1 t,b town "try.town=vib=0.8,hi=0.6,shadow=#34406a,shadowk=0.7" "x=--setts-paint --brush --kit-paint godot/art/kit_paint" fps=30`
  (use the DIR form your flag takes). The frames land in `godot/.shots/k1_town_{t,b}_0N.png`.
- **For the lead:** one 1:1 review sheet, JPEG q90, `godot/.shots/k1_review.jpg`. Two columns, t on the left and b on the right. Its rows: the well (x 560-1040, y 200-560 in frame 00; adjust to where it is), the blue-white stall, and each villager you changed (a 240x240 box round them). Look at it at half size yourself at most (`python tools/half.py <file>`). The lead judges the look, so tune by numbers and a look or two, then stop.
- **Report** the texture sizes and counts, and any runtime cost (same sizes means none).
- Commit, then report: the files, the flag, the tool's CLI, the numbers, the sheet path and the commit ids.
