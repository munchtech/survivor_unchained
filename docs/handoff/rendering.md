# Handoff: rendering (global light, exposure, tonemap, grade, her light vs the scene's)

## START HERE (Rendering 5, 3 Nov): the night crowd under her lamp, the r2 judge's numbers APPLIED and measured; MR READY
- **Worktree** `.claude/worktrees/render-5`, branch `render-5`. Numbers only: no judge, no taste call; the owner sees it in play. Arena nights only (day and story zones unchanged by construction: every new term is behind `crowd_night.w`/`CrowdFill`).
- **The app can now** print the five r2 numbers off frames: `python tools/render/crowd_lamp_measure.py shoot TAG` (hold a godot turn; 14 shots at her 4th swing, ~25 min, `godot/.shots/render5/TAG/`) then `... measure BEFORE AFTER [..]`; `--help` explains each number. Debug masks: `--crowd-dbg-mode 3..7` (3 near/mid/far/flat/dead, 4-5 distance bands, 6 paint classes, 7 the lamp factor as grey, `--crowd-dbg-s` its scale); `--crowd-omni on|off` (her real light on the crowd layer).
- **What changed (vat.gdshaderinc, Atmosphere.cs, PlayerView.cs):** her lamp on the crowd is `1/(1+0.5 d^2)` past 2 m, gone at 7 m (`--crowd-k/-full/-zero`), the real omni light skips the crowd by night (see below), `--crowd-ember` 0.35 -> 0.43 to land the energy; the flat and dead lose only the lamp (not the moon or the fill); the dead get their own floor after their darkening (`--crowd-dead 0.03`); hair and fur cards are not lifted; a warm rim toward her (`--crowd-rim 0.13`); cool top 0.2 -> 0.1 (`--crowd-top`); the crowd within 1.5 m takes 17% of the lamp (`--crowd-near-r/-near-k`). **A/B:** `--crowd-curve old --crowd-omni on` is Rendering 4's shipped look (`--crowd-fill off` still kills it all).
- **The numbers** (before -> after, same night 250 `mid` frame, 1:1; table in `survivorsunchained_inputs/scratch_render5/r5_final.txt`):

| | target | before | after |
|---|---|---|---|
| lamp factor at 2 / 3.5 / 6 / 7 m | 1 / .5 / .1 / 0 | 1.0 / .98 / .54 / .35 | 1.0 / .475 / .114 / 0 |
| lamp energy on the crowd | 0.65 (-35%) | 1 | 0.61 |
| standing bodies in the pool / lit floor | 0.7-0.9 | 1.02 | 0.89 |
| flat / dead over their ground | >= 0.6-0.8 | 0.55 / 0.30 | 1.01 / 0.75 |
| skin / cloth under the lamp | >= 3 | 4.4 | 4.3 |
| hair not lifted (hair over cloth, moonlit) | down | 7.05 | 4.18 (the lift is gone; few risen wear hair cards, none near her in this frame) |
| warm rim added over the bodies in reach | ~0.15 | 0 | 0.143 |
| moonlit bodies / moonlit floor | <= 0.8 | 0.64 | 0.63 |
| cool top's addition | -50% | 1 | 0.59 (the constant is exactly halved; the rest is the lifted dead and un-cut flat) |
| bodies within 1.5 m / her own L | 0.75 | 1.06 | 0.73 |

  All five are met within the measure's noise. Not shown by the measure: the dead now read a touch bluish-grey and the flat bodies are no longer sunk (both follow from the numbers; the owner's eye decides if the dead floor `--crowd-dead` wants a warmer tint).
- **Omni cull, flipped on measured need (coordinator's rule):** with her real light still on the crowd, bodies within 1.5 m read 0.91x her luma (target 0.75; the real light alone adds a third of the lamp there and nothing past 3 m), so the default is now off the crowd by night when the crowd's own light is on. `--crowd-omni on` restores it. Perf delta of the whole change: below.
- **Perf** (Release, 1080p high, night 250, A = `--crowd-curve old --crowd-omni on`, B = new; 7 runs each, `survivorsunchained_inputs/render5/perf`): medians p50 3.93 / 3.90 ms, p99 6.93 / 7.29 ms, GPU 3.346 / 3.357 ms, GPU p99 3.884 / 3.883 ms, CPU main 0.778 / 0.786 ms. GPU is flat to 0.01 ms; the frame-time p99 gap and every outlier (B4 7.6 ms p50) track machine CPU at 95-100% from other processes (runs at 40-60% CPU show p99 4.5-6.7 for both arms). **Rendering 4's "+0.1/+0.3 CPU, p99 +1.2/+2.9" was noise, not real.** Four pairs gave misleading means; use medians and note machine CPU in `driver.log`.
- **Tests** 1453 / 0 failed / 10 skipped (full `godot/tests/Tests.csproj`).
- **Not done / for later:** hair is unmeasured near her (this horde wears no hair cards in reach); the measure's mask references (`REF` in the script) are tonemap outputs: re-measure them if the grade changes. Cost about 0.25M (lead; one Haiku runner 53k).

## Rendering 4 (history, 2 Nov): night crowd "starburst" CLOSED as known, switch ON (net gain); MR READY
- **Worktree** `.claude/worktrees/render-4`, branch `render-4` (integration merged at 9dd4b0611; own junction, assume-unchanged).
- **Cause (measured, not a shadow):** in play no positional light shadows (only the moon key) and the crowd casts none (CastShadow Off). The "spokes" are the risen bodies themselves (VatCrowd, cloth paint ~0.015), pointing at her (lunge/slam lean, the dead fall straight away), crushed by the grade: about half the body pixels were pure black on her lit floor. The proof chain: moon shadow off, SSAO off, blobs off, corpses hidden, all lights hidden, FX hidden, SMAA all keep the spokes; hiding the crowd removes them.
- **Fix (arena nights only, `CrowdFill` in ArenaPlaces.For; day and story zones skip it):**
  - The crowd shader gets its own night light (vat.gdshaderinc, globals crowd_ember/lamp/fill/top/amb/night, set in PlayerView and Atmosphere):
    - her lamp, directional (wrap 0.3), full within 3 m, gone by 10 m;
    - the paint lifted toward luminance 0.04 with its hue kept, in ALBEDO, so the moon's shadowed light sinks figures in the canopy shade;
    - a small dirt-hued fill, and a cool top only on heads and shoulders;
    - flat, up-facing surfaces cut.
  - Pool blobs are 25% wider, 20% darker, offset 0.25 m away from her.
  - The crowd also wears `PlayerView.CrowdLayer` (1<<16), and her ember pool lights it.
  - Switches: `--crowd-fill off` (A/B), `--crowd-lift/-ember/-ember-h/-reach/-moon/-wrap/-top/-dirt/-back/-amb/-flat/-dbg`, `--ember-crowd off`. Debug: `--shadowdbg`, `--dbg-hide crowd,fx,ssao,herlights,alllights,decals`, `--dbg-key-noshadow`, `--dbg-no-corpses`, `--crowd-shadows off`.
- **Judged (max):**
  - r1 FAIL medium: grey plaster crowd, a pale burst of flat bodies.
  - r2 (final, main's cap) FAIL medium, near end. Q2 net gain over the black starburst: YES, so it ships ON.
  - Day identical, her unchanged.
- **Numbers (night 250 mid):** body vs ground L 0.44 to 0.86; pure-black body pixels 43-53% to 17-26% (mostly in the canopy shade).
- **Perf** (Release ABAB, night 250, `--crowd-fill off` vs on, 8-10.5 s; `survivorsunchained_inputs\render4\perf`): GPU -0.01/+0.04 ms, CPU +0.10/+0.31 ms, p99 +1.2/+2.9 ms (two pairs; a shader-only change, so CPU and p99 are likely noise or first use, unproven). **Tests** 1402/0/10.
- **Later list (r2 judge): APPLIED in Rendering 5 (above):**
  1. The lamp on the crowd tighter: full within 2 m, half by 3.5 m, 10% at 6 m, 0 at 7 m, squared falloff, -35%. Target: bodies 0.7-0.9x the lit floor.
  2. The dead and flat bodies never darker than 0.6-0.8x their ground (a black ring of dead returns in B3/B4); cut only the lamp on them, not the moon.
  3. Material separation: hair not lifted; skin at least 3x cloth under the lamp; a warm rim on the side facing her (about 0.15).
  4. The cool top fill -50% (moonlit bodies at most 0.8x the moonlit floor).
  5. The crowd within 1.5 m about 25% under her.
- **Routed (main logged them):** death and lunge fall directions, and corpses sinking (combat/animation); frozen walkers; ember glows on the crowd; the Deep Shaw grade crushing the canopy shade (~20% of the frame pure black). Her own rim or light, so she reads over the ring (rendering later).
- **Scratch:** coordinator pad `45b9ec4e...\scratchpad\render4\` (shoot.sh, bodyground.py, solver/m.py, solver2/m2.py, judge1/judge2 frames); backed up to `survivorsunchained_inputs\scratch_render4\`.
- **Cost:** about 0.76M, over the 0.6M cap. Lead ~0.28M, solvers 0.11M + 0.15M, max judges 0.09M + 0.11M, runner 0.03M.


Older blocks: history/rendering.md (grep by keyword, never read whole).
