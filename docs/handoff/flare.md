# Handoff: the Flares (look, sound and feel)

Read `docs/team/README.md`, `RESUME.md` (top block), `OWNER_NOTES.md` (13 October), then this page, then
`docs/design/FLARE_LOOK.md` §0-§2 and §4 (grammar, sound, the slice: Burns Twice, beat sheet, "done", judge checklist).
Branch `flare-1`. Worktree `.claude/worktrees/agent-af0782e2e3f51bc1f`. Coordinator: 59a43b82. Numbers are classes'
(now classes-10, ad0c69063d34fa8de); her clip is animation's (aaf7f8cdd03812ebd: deep lunge, staff planted at f20).

## The owner's words
"super epic flare animations. like beyond anything we've done yet"; "an 'oh shit' button ... a 'clear the whole room'
button"; "pushing a flare should always do something visible"; "flares should be unique"; "sounds that feel awesome".

## State (successor 3 stopped here; 883 tests green)
- **Built, seen and measured (t10).** Frost: ground as dark wet glass with bright fern lines (`flare_spine`, a big and a
  quieter fine layer), dark glassy body glaze, frost_plate mipmaps, small cold Shatter dust. Shards: the mesh was wound
  CCW (Godot fronts are CW), so they drew inside out: the white "paper flakes" of t1-t8; fixed in `FlareShards.ShardMesh`,
  no direct specular, a drawn glint. Steam (`FlareBits.P.Swirl/Seed/Wind`): gusts, eddies, a shared wind lean, darker
  warmer bellies (flare_bits `v_h`). BOOM: a shock front in the marks texture's texel 31 (`flare_boom` in
  flare_world.gdshaderinc), ground and bodies; a dark smoke column; shorter last fireball. The eye's dip
  (`FlareFx.Dip` to `Atmosphere.FlareDip`): exposure x0.62 from inside the last hitstop, back over a second.
- **§1.6 holds (L12, arena night, 250 packed):** peak 1.88x, 4 frames over 1.5x (budget 4: no headroom), 0.52% over the
  knee, 1.5 swings/s. Any brighter BOOM needs the dip deeper or the flash smaller.
- **Sound (`Audio/Sfx.Flare.cs`, Bus.Flare in Synth over the world -12 / music -9 dB duck), unheard by the owner:**
  catch, confirm, inhale + 0.15 s gap, frost, ember fall/land, the last BOOM in four layers + the valley echo at night,
  debris. `--wav`: peak -2.0 dBFS, no clipping; BOOM -13.7 dB RMS(50 ms) vs confirm -18.8. Owner must listen.
- **The red needle** was the hoard stone's beam (BattleFx `HoardLight`), real game UI. `--clean` now hides it, loot
  lights and ground names; the judge also gets one real-game frame per row (coordinator's rule).
- **Classes' events (classes-10, not yet in integration):** Ev.Flare Blow part "aim" (0.2 s before each ember; the Blow
  may bend up to ~5.5 m if the target died: steer to the Blow's TX/TZ in the last frames) and part "shove" (each
  survivor, TX/TZ rest point, Radius metres, 0 for a boss). BurnsBlow ignores unknown parts. Wire both after it merges.

## Judge 1 (aa37114707572563c, t10): NOT ready for the owner. Passes 3, 13, 18 (weak). Fails 7, 9, 10, 11, 14, 21.
Its fixes, in order (start here):
1. **Keep the pack visible and kill it on screen.** Glaze each body as the front reaches it (not all by b5); a glazed
   body one step brighter than the ground glass (ice-blue fresnel rim, a few % glinting, cyan at thin edges); glaze heads
   and hoods (warm "beads/petals" remain); every death shatters into shards with a small scorch. b6 = a field of
   glittering statues; c1w = that field bursting outward. (Check `flare_glazed`/`flare_body`, CrowdView's held/shattered.)
2. **Rebuild the BOOM and the ring.** Last ember near her (<= 3 m) so it is centred at both cameras; earlier impacts
   down to embers first; a different shape (an upward column + flash), emphasis by size/shape, not brightness; the ring
   0.5-1 m wide, white-yellow core under the knee to orange to red, sparse outward-leaning tongues, darker char behind,
   reaching the reach edge in 0.6-0.8 s easing out; no black flecks (soot/bodies?); bodies it crosses burst.
3. Embers: hot head, orange-to-red taper, sparks; smoke ribbons that curl and break in 0.5 s (now straight parallel
   bands at c1). Impacts: flash, 3-6 turned jets, translucent faceted shards lit warm/cool, a steam puff, a wet char ring.
4. Return: steam never the brightest thing (Verge night puffs are lavender cotton balls), mostly transparent by day;
   melt glints from her outward; the web sinks over 2-3 s.
5. Day: the glaze cold teal-blue with glints, not slate; no sepia veil at c3; cap day steam opacity.
Also: a still white triangle at Verge top centre b6..c1w (a stuck shard?). Thaw at sd c2 reads from the BOOM outward.
These are taste-heavy: give fixes 1+2 to ONE fresh su-lead-max solver (Context budget: 220k, build first, foreground),
then re-judge b6, c1_last5, c1w, c2 at both cameras and re-measure §1.6.

## Tools (scratch, backed up in `survivorsunchained_inputs/scratch_59a43b82/flare/`)
`batch8.sh TAG` (clean 3 rows + real 3 rows with `--wav` on Verge night + 60 fps arena and Verge), `batch9.sh` (lighter),
`batch.sh`, `shot.sh`; `sheet.py OUT TILE_W COLS png...` (TILE_W is per tile!); `meas.py TAG` (beat means vs ready),
`lum60.py NAME` (§1.6 from 60 fps frames), `wavmeas.py FILE from to`. Beats now include `c1w_wave` (+0.3 s after the
BOOM). Delete `godot/.shots/L*_NNN.png` after measuring (270 frames each).

## Gotchas
- NEVER `python -` (with or without a heredoc): it hangs (twice this session). Write the script to a file.
- Wait on a background job by its exact output file, never `ls -t` (it picked another agent's transcript).
- `--import` churn under `godot/art/**/*.import` stays uncommitted; give the godot turn back by its exact name.
- The Flare clock runs at 0.1 during hitstop: time anything "real-frames" off it accordingly (the dip did).
