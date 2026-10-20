# Brief S1: painted setts behind a flag (style r2, E3 job 1)

Context budget: 200k. You're a code solver at medium effort for art-style lead 3, who is waiting on you in the foreground: **your final message is your report** (under 30 lines; no SendMessage needed).

**Worktree:** `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\art-style`, branch `art-style`. It has its own `godot/assets` junction, so never `git stash`, `git reset --hard` or `git checkout .` there. `git add` named files only: never the ~1,146 line-ending-only `.import` files or the stray `.uid` files. Commit as you go, with messages ending `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Godot runs need a turn: `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "art-style: setts" --wait 1800`, given back straight after (frames.py does this for shots). Blender, if you need it: `take blender`. Never kill processes by name.

**Sharing the worktree:** the brush-filter coder is finishing a round in this same worktree (Brush*.cs, frames.py). Don't touch those files. Do your Python and texture work first. **Before your first `dotnet build`, Godot import or shot, wait until `godot/.shots/s3_review.jpg` exists** (check every 60 s, at most 60 min, then go ahead anyway): until then it is building and shooting.

## The goal
We're proving a signature look in engine: painterly realism. Forms stay real, but surfaces read as painted. The bar is the painted target `C:\Users\munch\Desktop\survivorsunchained_inputs\art_style\r2\target_town.png` (a Krea preview, never shipped). Look at it once at full size, and once at a 1:1 crop of the square around the well (x 400-1360, y 150-690). Today's engine frame at the same camera is `C:\Users\munch\Desktop\survivorsunchained_inputs\art_style\r1\A_town.png`. **Build with our own shippable tools only** (numpy/OpenCV/Blender, our code), never Krea or any AI image model. Everything sits behind a flag, default off.

## What the target's setts show (the lead's reading at 1:1)
- **Stones of varied size and shape:** a few big flat flags, mostly mid stones, small fill stones. Today's layout is an even grid of near-equal cobbles with dark joint lines, which reads as procedural.
- **Each stone is one flat painted tone,** warm grey-ochre in the sun, varied stone to stone. It's slightly lighter on its top and its sun-side rim (a painted light edge; the sun comes from azimuth 330 at elevation 28, so work out which side that is in the tile), and slightly darker at its foot. Fewer micro-details: no grain noise, value shapes over texture.
- **Joints filled with opaque, matte, ochre-brown packed mud, not dark lines,** uneven in width. The mud sits flush over the stones' buried edges. Moss green at the edges and near the well.
- **A lighter, polished wear lane** down the street, carried in the albedo.
- **The mud patches round the well and the posts:** today they read as bright yellow-ochre stains at 1:1. In the painted mode, make them a darker, browner, matte earth with moss at their edges.
- **Brushwork in the albedo:** only a gentle per-stone tonal variation along each stone's long axis (strokes about 1.5-2 cm wide in the world, a contrast of about +/-4%). The screen-space brush filter (`--brush`) adds the stroke hand on top, so don't double it.
- **Value:** keep the stones' mean albedo near today's, but warmer. The lead tunes the sunlight afterwards (E1) to bring the sunlit stones up to the target's brightness, so the albedo shouldn't carry the light.

## The job
1. In `tools/assets/env_ground.py`, add a painted mode. Give it a new layout with varied stone sizes, as a variant set in `setts_layout`/`setts_sources` (keep today's untouched), and a painted albedo in `bake_setts` (or a `bake_setts_paint`). The sources go to their own folder (say `tools/assets/setts_src_paint/`) so they can be re-baked. Write the maps to alternate files: `godot/art/ground/setts_paint_albedo.jpg`, `setts_paint_normal.jpg` and `setts_paint_arh.jpg`, at the same sizes and layering as today's (today's stay byte-identical). The normal and height should follow the new layout: stones domed, joints filled and flatter.
2. Add the Godot flag `--setts-paint` to `godot/src/World/Ground.cs` (~line 82, where `setts_albedo.jpg` is chosen) so it loads those files. Under the same flag, make the mud opaque and matte where `godot/shaders/terrain.gdshader` lays it (`setts_mud` and friends; there are already per-uniform flags, `--setts-mud`, `--setts-mud-tone`, `--setts-mud-sat`, `--setts-mud-spec`; set defaults for the painted mode in code under the flag, and don't change today's defaults).
3. Reimport after the texture change: `"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe" --headless --path godot --import` (with the godot turn).

## Acceptance (give the numbers)
- `dotnet build godot/SurvivorUnchained.csproj -v q -nologo` is clean (no new warnings). `dotnet test godot/tests/Tests.csproj` passes (pass/fail/skip).
- **Flag off:** a town frame matches one shot before your change, at `fps=30`. Report the max and mean abs diff, and the scene's own run-to-run noise (shoot the old build twice).
- **Shots,** from the worktree root (one godot turn each, frames.py takes it):
  `python tools/scratch/art_style/frames.py p1 t,b town "try.town=vib=0.8,hi=0.6,shadow=#34406a,shadowk=0.7" "x=--setts-paint" fps=30`
  then round `p2` with variant `b` only and `"x=--setts-paint --brush"`.
  The frames land in `godot/.shots/p1_town_{t,b}_0N.png`.
- **For the lead:** one 1:1 review sheet, JPEG q90, `godot/.shots/p1_review.jpg`. Its rows, each cropped at x 400-1360, y 150-690: `p1_town_t_00` (today), `p1_town_b_00` (painted setts), `p2_town_b_00` (painted setts + brush). Look at it at half size yourself at most (`python tools/half.py <file>`). The lead judges the look, so tune by numbers and a look or two, then stop.
- **Report** the texture sizes and counts, and that nothing changes at runtime cost (same sizes).
- Commit, then report: the files, the flag, what each map does differently, the numbers, the sheet path and the commit ids.
