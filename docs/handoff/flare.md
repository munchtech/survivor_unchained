# Handoff: the Flares (look, sound and feel)

Read `docs/team/README.md`, `RESUME.md` (top block), `OWNER_NOTES.md` (13 October), then this page, then
`docs/design/FLARE_LOOK.md` §0, §1.6, §4.1, §4.4. Branch `flare-1`, worktree `.claude/worktrees/agent-af0782e2e3f51bc1f`.
Numbers are classes' (paused; send anything for classes through the coordinator). Her clip is animation's.

## The owner's words
"super epic flare animations. like beyond anything we've done yet"; "an 'oh shit' button ... a 'clear the whole room'
button"; "pushing a flare should always do something visible"; "flares should be unique"; "sounds that feel awesome".

## Paused here (successor 6, 13 October); next:
- **Judge 4: NOT READY** (verdict `scratch_1be2d2a9/flare/f6/j4/verdict_j4.txt` in survivorsunchained_inputs, sheets
  beside it). Freeze, hold, frost glaze, ember streaks and onset sync are good. BOOM FAIL (birth f114-f122 a flat cream
  cotton ball lighting nothing; then a black soot collar ~10 m that reads as a hole). Ring WEAK (thin, no mass; red edge
  turns statues mauve; the circle through the fireball reads as a decal). Shards FAIL (opaque matte grey card; landed stay
  pale; by day spilled salt). Return FAIL (no arena steam; melt edge = white static; cracks a vector overlay). Day WEAK
  (black soot blob). Empty WEAK. §1.6 FAIL (swings 2.5/s both nights; empty peak 1.84x; floors 0.52-0.68x; knee 0.6%).
- **Built this session (all on flare-1, unjudged beyond judge 4):** the Return's light (char ~0.7x its ground from
  `fl_alb0`; crust cracks `fl_seam` glowing to 2 s, dark by 4 s, web.X/Y timeline in Burns.cs; meltwater glints at the
  receding edge); shards as faceted plates (`FlareShards.cs` new mesh, land flat, melt 0.5-1.5 s; `flare_shard.gdshader`);
  ring tongues in 0.6 m slots riding the line (`FlareBits.P.Show` draws a bit along a way other than its velocity), a
  red edge, coals 1 m cells, `CrackHold` now -2..-3 frames; ring through the fireball's base (`flare_fb`); day steam
  warm-white, warm char rim, no ring scars; impact steam 4 thin puffs, ember trails thinner; BOOM light 11, rim 10;
  sim soot thins 0.35-0.8 s and fades 0.9-1.4 s; tips held from the press to +3 s (`GameHud.FlareDim`); `FLARE_NOWEB=1`.
- **The atlas in the game is b5cx** (solver 4: `tools/fxsim/birth.py` regrades bake b5's f1-f9 in its cache into
  `.shots/b5c/cache`, ~20 s; take `burns_boom5c`; then `rr.sh b5c NAME --take burns_boom5c`, ~2 min; mix with b5g's
  f10-48 as b5cx was). Solver 3's b5 bake (15 m box, res 240) and b5g render are the base. `pow_keys` (mine) did nothing:
  the flame field is saturated.

## Next, in order (judge 4's fixes; full numbers in verdict_j4.txt)
1. Birth atlas f1-f9 hot to cool: white-yellow core >0.92 on ~20% of the ball for 3 frames shrinking by f120; body
   yellow-orange 0.6-0.75; rims orange-red; creases 0.25; two finer billow sizes so f9 meets f10; edge rolling out.
   (birth.py is the lever: a fresh max solver with these numbers.)
2. A warm fireball light (#FFB060, ~3 m up, f114-f130) so the glass statues near it catch fire; ground within 4 m <=1.4x.
3. Lit soot, not black: night 0.10-0.20 lit amber from below, day grey-brown; opacity <=0.7; footprint <=1.3x the ball;
   thinned by +0.6 s (pack/tone or the `smoke` keys in `FlareFx.Boom.cs` BoomTick). Floors and swings follow from it.
4. Shards as see-through cyan glass (needs a transparent pass: `flare_shard.gdshader` is opaque today), one 2-frame facet
   flash each, landed dark within 0.15 s with a wet mark; 1-2 chunks of 40-60 cm per statue.
5. Cracks: tapering 1-5 px with a hot core and red halo, kinked, each going dark at its own time (`fl_seam` in
   flare_world.gdshaderinc).
6. Melt edge a wet dark band with a thin bright line (replace the glint band); low amber-lit steam at arena night.
7. Ring mass (40-60 cm burning band, taller tongues with a hot core, a haze skirt ahead, the outer edge amber not red);
   8. the ring born from the fireball's lower billows instead of the circle through it; 9. ember scars stretched along
   each ember's path, varied, broken into arcs.
10. Judge 5 wants first: counted swings (frame, direction, size) for both nights; a Verge-night floor against an empty
    Verge night; shard pixels >0.5 at f140/f160/+1 s; frames from press to first change; hitstop frames and the audio
    transient's frame; true 100% crops of f116, f119 and a day f116. Then captures for the owner (`f5/cap.sh`).

## Tools
Old scratch (still on disk): `59a43b82.../scratchpad/flare/` (`lq.sh TAG`, `batch8.sh TAG`, `jsheet.sh TAG`, `sheet.py`,
`lum60.py`, `meas.py TAG`, `shot.sh`). Lead 6 (`1be2d2a9.../scratchpad/f6/`, backed up in survivorsunchained_inputs/scratch_1be2d2a9/flare/f6/): `lq.sh TAG an sn sd` = clean rows (to +6 s) + 60 fps runs + `lum.py` (peak, knee, swings, Return floor; EXTRA="--horde 0" for an empty field); `reach.py` in-reach vs outside; `js.sh TAG LATE` judge sheets; `grid.py`, `crop.py`, `ed.py`. Lead 5: `1be2d2a9.../scratchpad/f5/` (`q.sh TAG an` = import + clean row + a BOOM
sequence at 20 fps from 7.75 s; `lqs.sh TAG` = Verge night lq; `cap.sh`; `onset.py WAV t0 t1`; `bisect.sh`).
Backed up in `survivorsunchained_inputs/scratch_1be2d2a9/flare/` (with `f6_boom.jpg`).
Build C#: `dotnet build godot/SurvivorUnchained.csproj -v q`. Tests: `dotnet test godot/tests/Tests.csproj` (887 green).

## Gotchas
- **NEVER `git stash`, `git reset --hard` or `git checkout .` here** (godot/assets junction; see README DANGER).
- NEVER `python -` (it hangs, even with a heredoc). Write a .py file.
- Mantaflow: setting any domain property after `cache_directory` deletes the bake (it is set last now).
- pack.py once handed PIL float64 planes as "F" and wrote noise into every resized cell: keep the float32 cast.
- The Flare clock runs at 0.1 during hitstop; the column/particles and the sim quad run on real time.
- Solvers run out at about 200-220k after one round. Give them one problem and a working pipeline.
