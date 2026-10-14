# Handoff: the Flares (look, sound and feel)

Read `docs/team/README.md`, `RESUME.md` (top block), `OWNER_NOTES.md` (13 October), then this page, then
`docs/design/FLARE_LOOK.md` §0, §1.6, §4.1, §4.4. Branch `flare-1`, worktree `.claude/worktrees/agent-af0782e2e3f51bc1f`.
Numbers are classes' (paused; send anything for classes through the coordinator). Her clip is animation's.

## The owner's words
"super epic flare animations. like beyond anything we've done yet"; "an 'oh shit' button ... a 'clear the whole room'
button"; "pushing a flare should always do something visible"; "flares should be unique"; "sounds that feel awesome".

## Paused here (successor 5, 13 October); next:
- **Salmon fixed (6b747aad):** arena_ground's `uniform vec3 ember` won over flare_ground's local `ember`. Locals in
  flare_world.gdshaderinc take an `fl_` prefix when in doubt (it is included by arena_ground, terrain, vat, grass, kit...).
- **The BOOM is now a simulated burst** (tools/fxsim): `boom_sim.py` (Blender 4.5 Mantaflow, TAKES presets, `--set`,
  `--render-only`), `run.sh NAME args` (takes the blender turn, bake ~15-20 min, render ~3), `pack.py atlas|preview|frames`
  (EXR, tone-mapped hue-kept; needs `pip install OpenEXR`), `calib.py` (Mantaflow is ~30x slow at this scale: time scale 4).
  Atlas `godot/art/fx/flare/burns_boom.png/.json` (7x7 x 384, 48 frames, 24 fps). The game plays it on one camera-facing
  quad (`flare_fb.gdshader`, `FlareFx.Boom.cs`: SimSize 16, SimLook 4.5, SimRate 1.4, SimFirst 6, fire_tint, faded by
  +0.8 s); when the atlas is there the mesh pillar, cap, jets and Column particles are off (fallback only).
- **Judge 3 (f6, sheets `scratchpad f5/f6_boom.jpg`, `59a43b82 scratchpad flare/f6_judge.jpg`): NOT ready.**
  BOOM WEAK (was FAIL: real fireball, scale "whoa", but lit orange smoke, salmon, see-through, no soot, no tongues;
  starfish birth with grey squares), ring WEAK (best thing: no tongues, no red edge, coals in a polka grid), shards FAIL
  (dark glass invisible on char; orange "straw" carpet), frost PASS, Return FAIL (dead black frame 0.56-0.60x; cotton-ball
  steam; no melt glints), day WEAK, §1.6 FAIL narrowly (Verge night 2.5 swings/s), bar FAIL.
- **Done after judge 3 (0c47329a):** steam a third, thin, warm roots, none within 2 m of her; thrown shards' hot rims
  ~0.3 s; web under char halved and sunk by 2 s; pre-BOOM dip 0.9; BOOM light 15; sim fade by +0.8 s. Measured f7:
  arena peak 1.79x, 4 frames over, 1.5 swings/s; Verge night 1.61x, 3 over, 1.0/s. BUT the Return's floor fell to
  0.29x arena / 0.37x Verge night: the steam had been lighting it. Its own light (judge fix 4) is the next build.
- **Solver 2 (sim shading) was running at handoff:** dark opaque soot, blackbody flame, a round birth with no starfish
  so SimFirst can go to 0, no tail speckle. See "Solver 2" below for its result.

## Next, in order (judge 3's fixes; full text in its verdict, summarised)
1. Integrate solver 2's take (SimSize/SimLook/SimFirst, drop fire_tint if it says so), shoot, look once.
2. BOOM birth: white-hot core ~1-1.5 m at once, full size in 4-6 frames; spend 1-1.5% of pixels over the knee for 3
   frames; whole-frame peak <= 1.6x (now 1.79x); draw the ring's first 0.1 s over the fireball's base.
3. The Return's light: web amber 0-2 s then dark by 4 s; meltwater glints (sharp, twinkling, ~1/m², at the frost's
   receding edge); char >= 70% of the ground around; arena-night floor >= 0.70x through +3 s from these lights.
4. Shards: 3-6 faceted plates per statue, 15-40 cm, cold blue-grey glass body with a flickering glint; landed ones melt
   to water glints over 1-1.5 s. Find what the remaining "sticks" are (hide the web for one +0.6 s frame).
5. Ring: flame tongues 0.5-1.2 m tall every ~0.6 m, leaning out; a red edge 2-3 px outside the line; coals jittered
   ±0.5 m, sized 0.5-2x, a third out early; statues within 1 m crack 2-3 frames before the line.
6. Day Return: char a clear disc 25-35% darker than the ground with a warm rim; steam warm-white; no grid of stumps.
7. Hold tips (e.g. "THE MAP") from the press to +3 s.
8. Then judge 4 with: frames 112-122 one by one (arena night, 60 fps), a 400x400 crop of 4 frames at the ring's front,
   +3 s and +6 s frames (an, sd), in-reach vs outside luminance at +1/+3 s, a boss run (`--boss`), and the sound.
9. Then captures for the owner: `scratchpad f5/cap.sh TAG ZONE TIME COUNT` (60 fps frames + `--wav`, muxed by
   `tools/fxsim/cap.py`; tape starts at game 0, sync measured: BOOM onset 7.850 s audio vs frame 7.85-7.88 s).

## Tools
Old scratch (still on disk): `59a43b82.../scratchpad/flare/` (`lq.sh TAG`, `batch8.sh TAG`, `jsheet.sh TAG`, `sheet.py`,
`lum60.py`, `meas.py TAG`, `shot.sh`). Mine: `1be2d2a9.../scratchpad/f5/` (`q.sh TAG an` = import + clean row + a BOOM
sequence at 20 fps from 7.75 s; `lqs.sh TAG` = Verge night lq; `cap.sh`; `onset.py WAV t0 t1`; `bisect.sh`).
Back them up to `survivorsunchained_inputs/scratch_1be2d2a9/flare/` before the scratch is cleared.
Build C#: `dotnet build godot/SurvivorUnchained.csproj -v q`. Tests: `dotnet test godot/tests/Tests.csproj` (887 green).

## Gotchas
- **NEVER `git stash`, `git reset --hard` or `git checkout .` here** (godot/assets junction; see README DANGER).
- NEVER `python -` (it hangs, even with a heredoc). Write a .py file.
- Mantaflow: setting any domain property after `cache_directory` deletes the bake (it is set last now).
- pack.py once handed PIL float64 planes as "F" and wrote noise into every resized cell: keep the float32 cast.
- The Flare clock runs at 0.1 during hitstop; the column/particles and the sim quad run on real time.
- Solvers run out at about 200-220k after one round. Give them one problem and a working pipeline.
