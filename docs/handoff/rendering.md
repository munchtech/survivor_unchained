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

## Rendering 3 (history, 1 Nov): NPC town light CLOSED as the better state; MR READY
- **Worktree** `.claude/worktrees/rend-2`, branch `rend-2` (integration merged at 54282c1b1). Round 4 (final, main's cap 4): xhigh FAIL near, but B better than integration on all 12 NPC night frames (none same or worse), so closed per main's rule. Gate YES: Rav, Sella (round 3 faults fixed), Keegan, Holloway, Rook, Wenna (nothing broke). Gate NO: Harlan (LIGHT, near: the camel coat is lit evenly from shoulder to sleeve, no head-to-body falloff), Chid (ASSET, near: near-white tunic paint, routed clamp ~0.65-0.70 sRGB).
- **Later list (light, not gate-failing alone):** (1) Harlan falloff: lower-frame cloth about 1 stop under the same cloth at the shoulder, face unchanged; if the 22 deg cone can't (spot too far), move the people's key 30-40 deg off the camera axis so the coat gets a shadow side. (2) The teal wash reads mint on pale cloth in shade (Chid's hood lining, Harlan's shirt edge): pull `--close-rim-colour-folk` toward grey-teal ~0.62,0.78,0.80. Re-check Chid after the NPC area's tunic clamp.
- **Tests:** `dotnet test godot/tests/Tests.csproj` 1337/0/10 (the .sln runs nothing). **Perf** (night close-up, her, `--close-folk off` A vs on B, ABAB 25 s): GPU 4.37 -> 4.46 ms (+0.09), render CPU +0.5 ms, shadow draws +25; frame ms noisy (machine shared). The A runs (`--close-folk off`, a debug switch) segfault at quit after Godot's "indexing did not unpair geometries from light"; the default (B) and all 26 shots exit clean.
- Round 4 frames and sheets were sent to the Recycle Bin (re-shootable: the gate list is the chest lines in `survivorsunchained_inputs/scratch_rend2/r0b.txt`, with `shoot.sh` and `body.py` there); briefs and verdicts j3/j4 are backed up there too.


## Rendering 2 (history, 1 Nov): town light on NPCs. Night/day faces CURED; one judge left (cap 3 USED: ask main for a raise), perf, MR
- **Worktree** `.claude/worktrees/rend-2`, branch `rend-2` @7a356e9a1 (integration merged at 1cb7afd04; `godot\assets` junction to its OWN `public\assets`, assume-unchanged). Scratch: coordinator pad `b9e8a09f...\scratchpad\rend2\` (backup of scripts/lists `survivorsunchained_inputs\scratch_rend2\`): `shoot.sh LIST OUTDIR TAG` (absolute paths; `IMPORT=1` after a merge), `face.py DIR` (NPC chest-frame face box: lit/shade Oklab L C hue), `body.py FILES` (neck/chest/low/face boxes), lists r0b (all 12 NPCs chest day+night, talk, her), r1-r7; frames r0 (integration baseline) .. r7; judge sheets j1-j3.
- **Gate frame:** `--npc def.NAME:swap:chest --close 1 --idle-after 1 --zone waystation --time day|night` (the NPC in her place, the close rig lights it). The dialogue panel's portrait is a separate rig (fine); the talk camera (12.5 m) shows faces too small to judge.
- **Cause (measured):** night lavender = her close rig's cool fill (0.72/0.82/1) and moon rim on people's layer 2 over the NPCs' red-rich paint (not the town presets). Day navy sockets = play's day grade (WaystationDay slate shade 1.6) on dark low-chroma skin.
- **Fix (GameCloseUp.cs, cleared by main; all behind switches):**
  - By night, while she is on her own layers (OwnLayer), the rig's key, fill, moon rim and body rim reach people through twins on layer 2 (`FolkTwins`/`Twin`): amber fill 1/0.86/0.62, key x0.7 drawn halfway to 1/0.92/0.75 with sheen 0.12, rim x0.45 teal 0.55/0.85/0.85, a teal wash x0.15 of the fill, no body rim; the key and fill aimed at the head in a 22-degree cone, soft falloff 0.45. Switches `--close-folk off`, `--close-folk-key/-rim/-cool/-key-spec/-fill-cone/-fill-edge`, `--close-fill-colour-folk`, `--close-rim-colour-folk`, `--close-key-colour-folk`. Her own lights unchanged: her night close-up vs integration mean 0.16/255, 0.3% px >8 (flicker).
  - `CloseGradeDay` 0 to 1 (the close view by day takes its own paint grade), keeping play's highlight tint by day (`Atmosphere.SetViewHighlights(k, keepTint)`, `--close-day-hi-tint off`). `--air-tune` now takes NightTown and `pshskin`.
- **Judged:** her close-up A/B (max): PASS, B better (deep skin's indigo shade gone, irises green, leather brown); the flat grey sky it caused is fixed (j2: sky right). NPCs xhigh: j1 FAIL near (rose patches), j2 FAIL near (faces PASS all 12; steel mauve, pale cloth glowing), j3 FAIL near (Keegan, Holloway, Rook, Wenna YES; below the 11-degree cone's hard edge the old lilac returned on Rav's neck, Sella's chest, Harlan's coat, Chid's tunic rose). After j3, numbers only (r7, cone 22 / edge 0.45 / teal 0.55,0.85,0.85): no skin or pale cloth in hue 260-350 (Rav neck 344->50, chest 283->32; Harlan coat 324->49; Rook apron 303->30); Harlan's coat L 31 under his face's 65.
- **NEXT:** (1) ask main for `Round cap raised for npc town light to 4`; shoot all 12 night chest frames at the defaults (list `r0b.txt` cn_ lines) and run one xhigh judge (whole-frame gate first, the j3 brief + r7 numbers). (2) `dotnet test` (my background run wrote nothing: rerun), perf ABAB at the night close-up (`--close-folk off` vs on: 4 extra unshadowed spots at night close view only), MR.
- **Known / routed:** Chid's near-white tunic stays the brightest thing in his frame under every cone tried (asset: clamp the tunic's paint to ~0.65-0.70 sRGB, NPC area). Vonnra by day: ashy eye area = her paint (j2). Wenna's red cheek blotch, Sella's far-jaw crease, Harlan's coat/vest cut: assets. Brannoc's chest frame shows his back (his idle's swing: NPC/animation framing). Real-game note: with the warm light now aimed at the framed head, NPCs merely beside her at the close view get the town's light only (unmeasured; town-lit faces at the play camera are too small to read).
- **Cost:** lead ~280k; judges 91k + 109k (max) + 99k + 73k; ~11 short Godot shoots.

## Now (Rendering 1, 28 Oct): fixed list DONE (3 rounds, final max judge: merge YES, no regressions); MR READY
- **Worktree** `.claude/worktrees/rend-1`, branch `rend-1` (from integration 7b94438d; `godot\assets` is a junction to its OWN `public\assets`, assume-unchanged; the unstaged `.import` edits are reimport noise, not ours). Scratch (the coordinator's pad): `...\scratchpad\rend1\`: shoot.sh (list format `NAME|WxH|ENV|ARGS|SECONDS|COUNT|EVERY`, `EXTRA=` for switches), r0.txt (the 30-frame worst-case set: Low Ford night play, camp, lantern, a night fight, the close-up at camp fair and deep, the town by night, day and dawn at play and close-up, the Look by night, day and deep), measure.py, sheet.py, `r2d\face3.py` and `e\e_face.py` (face box: face:bg, key:fill, cheek L/C/hue; reads `--camlog`), `work_c\poolc.py` (pool areas), briefs and verdicts j0-j3, frames r0-r3. Backed up to `survivorsunchained_inputs\scratch_rend1\`.
- **What changed:**
  - **LowFordNight (Atmospheres.cs, d351ad4e):** moon 1.7, exposure 1.3, fill #34507e at 1.6, env 0.6, the shade blue (not violet), ember 3.5.
  - **Camp:** lantern 0.42, range 3.2 (props_own.json `lamps.glow-1-0`, 480df369); the fire light 80/18 (zone.json lights[0]).
  - **The town:** NightTown ember 3 plus a lift; WaystationDay PaintShadowK 1.6 (cool slate shade).
  - **Her ember, split (PlayerView.cs, 105cdcaa):** a ground-only 2500K pool, plus a `FolkLight` 4.5 m up for her and the people near her; her gear on the people layer while it's on. Flare burst gain capped at 2.2. Near a lamp (3 m) the folk light halves and the pool is cut.
  - **Close-up rig (GameCloseUp.cs, 745d3847, 64f35775, f806d91e, 2bacf782, 71c9d88e):**
    - The key comes from the nearest fire or lamp (or the moon), 3000K, held within 100 deg of where she faces, 65-75 deg off the camera at Low Ford and 50-60 in town.
    - A cool fill at 0.25 plus extra on dark skin.
    - A warm ground spot lights the world around her (not in town).
    - Her shield and sword are on her gear layer at the night close view, with their metal halved.
    - Town lamps are 1 stop down at the night close view (a camera multiplier; the town's data is untouched).
    - Her folk light is off and her pool at 0.25 in the town's night close view.
  - **Skin guard (Atmosphere.cs GradeLut, ae09adb5):** up to 25% chroma off strong red-orange skin, close view and Look only.
  - **The Look by night (GameFront.cs, 6167d17f; People.HerSkinGain, 05450777):** a fire-side key, a cool fill, and deep skin +0.5 stop on the skin only.
  - All the knobs are `--close-*`, `--look-night-*`, `--ember-*` and `--skin-guard-*` switches.
- **Closed:**
  - Not visible at 1:1: night crushing her and the dead; the AgX lantern blowout (no own tonemap needed); the BattleFx discs.
  - Passed: Low Ford's dark wash, the camp lantern, her ember at the play camera, deep skin at the close-up, the town's day shade, the Look by night, tcloseN, tdawn_01, tnight_01.
- **Closed as known (round cap, j3):**
  1. **tnight_02, the town night close-up at the stall:** flat front light, pale and waxy. It's a dialogue spot: RESTAGE first in the next rendering pass, keying her from the stall-lamp side with tcloseN_00's rule.
  2. **The night close-up in near-profile (lfclose_00):** flat pale cream. The three-quarter view (lfclose_01) is modeled. Suspect the extra dark-skin fill. Restage any staged shot at this angle.
  3. **The deep preset's copper hair reads paler than on fair skin:** the crown pixels match, so pick the same strands first; if they match, it's Face/hair (a per-skin swatch).
  4. **Deep shoulders and chest redder than the face at the Look:** body vs face albedo (Face/body).
  5. **The wood road's side thirds near-black (Environment's judge):** the fill and env barely move them (+1-2 luma at hemi 2.8, env 1.0); only the moon or exposure would, which would undo the passed darkness.
  - Marks: the town by day close-up face is a little flat and the haze milky; shaded wood reads navy by day; a hot yellow sheen on the forehead at lfclose_01.
- **Routed:** the cobble patches are Environment's mud decals (unchanged with SSAO and key shadow off); the forehead seam at the hairline is Face/hair; the moon glints were fixed by Environment (#d8e0ea).
- **Owner sheet (half size, judge-passed frames):** `survivorsunchained_inputs\rend1\rendering_before_after.jpg` (the night close-up, Low Ford at night, the camp, the town at night at play and close-up).
- **Cost:** judges 150k + 157k + 158k + 149k; solvers A 157k, B 201k, C 156k, D 182k, E 200k; lead ~250k. About 1.8M in all.
