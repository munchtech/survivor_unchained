# Handoff: the Flares (look, sound and feel)

Read `docs/team/README.md`, `RESUME.md` (top block), `OWNER_NOTES.md` (13 October), then this page, then
`docs/design/FLARE_LOOK.md` §0-§2 and §4 (the grammar, sound, and the slice: Burns Twice, its beat sheet,
"done" and the judge's checklist). Branch `flare-1` (from integration cc8bf6c1). Worktree
`.claude/worktrees/agent-af0782e2e3f51bc1f`, set up: `godot/assets` is a junction to its own `public/assets`
(assume-unchanged), with `.godot` and the `.import` files copied and imported.

## The owner's words
"I'm simply anxious to begin building super epic flare animations. like beyond anything we've done yet with effects
and just awesomeness"; "its supposed to be epic. an 'oh shit' button. a planned 'BOOM' button. a 'clear the whole
room' button"; "pushing a flare should always do something visible"; "take a look at sound research too. sounds
that feel awesome, feel good. intangibles"; "flares should be unique ... our existing effects aren't perfect yet".
So: no spell's flames, ice, sparks, sprites (Kenney's pack included) or sounds. Engine tools are fine. It must be the
best effect in the game by a distance.

## Brief (from the coordinator)
- Build the grammar once (FLARE_LOOK §4.2), then Burns Twice on it, to §4.3's "done".
- Then a fresh `su-lead-max` judge (FOREGROUND, `Context budget: 150k`) with §4.4's checklist, sheets and numbers.
- Then 60 fps captures for the owner, through the coordinator.
- The numbers are classes' (a63a34b9e5a45d1bf, classes-9): propose, don't change.
- The clip comes from animation (aaf7f8cdd03812ebd), built at 30 fps with the brief's timings. The contact frames: butt down at 0.67 s (f40 at 60), the sweep at 1.42 s, the run blend from 1.52 s. They'll message when it passes judge. Placeholder until then: `cast_raise`, then `cast_bolt`.
- Staff head: node `arm:mage_staff` (under `mount:hand_r`), holder-local (0.04, 0.87, 0.01); the butt is at Y -0.79.
- Textures: ComfyUI only on a gpu turn, logged in `docs/legal/ASSET_PROVENANCE.md`. Sound: ours (Synth.cs, or offline synthesis) or CC0, logged.
- Short reports to the coordinator at milestones. Commit as you go; `dotnet test` green before each push.

## Done (committed, built, NOT yet run or seen)
- **Her clock** `Battle.FlareLead(dt)` + getters `FlareKey`, `FlareReleased` (Flare.cs end).
  - Agreed with classes, with four guards: no blows; stops at the key; no world stamps; its own method.
  - Test: `Her_clock_lead_...` in `FlareStagedTests`.
  - How it's used: while the view freezes the world at 8%, it calls `b.FlareLead(dt*LeadRate - fightDt)`. LeadRate = key / (0.22 + the calling's hold), so Release lands at 0.52 s real for the arcanist and every later beat keeps lamps.json's spacing.
- **`Ev.Hit.ByFlare`, `Ev.Kill.ByFlare`** (Events.cs; set in Battle.cs from `credit == "flare"`). View only.
- **Camera** (`FollowCamera`):
  - `FlarePush` (share of the distance; negative pulls out);
  - `FlarePitch` (radians; negative lifts toward the sky);
  - `Jolt(axis, trauma)`, a damped 13 Hz swing along the blow.
- **World shaders** read globals from `shaders/flare_world.gdshaderinc`: `flare_at`, `_look`, `_web`, `_frost`, `_hue`, plus the samplers `flare_plate`, `flare_noise`, `flare_marks`. They're registered in `project.godot` [shader_globals].
  - Wired at the end of fragment() in arena_ground and terrain (`flare_ground`), kit (`flare_prop`), grass, arena_grass and arena_leaves (`flare_blade`), and vat.gdshaderinc (`flare_body`).
  - The crowd's spell rime gives way to the glaze (`fz` in vat.gdshaderinc).
  - The include holds: the drain and repaint (cold for Burns); the web (cellular hairlines, lit outward, running inward, fading at the reach, with heat cooling hue → dull red → dark); the frost (growth map `flare_arrive`, `flare_cover`, two multiplied plate layers, honest edge, melt from the edge, the crystallising front band); the impacts (melt, wet, char splash, cooling heart); the body glaze; frost on grass tips and on props.
  - **Never compiled by Godot yet.** Watch the log for: hints on `global uniform sampler2D`; `TIME` and `dFdx` inside functions; reading ALBEDO, NORMAL and the like after writing them in the wired blocks. Fix any of those first.
- **Textures** (ours, procedural): `tools/fx/flare_plates.py` makes `godot/art/fx/flare/frost_plate.png` (R feathered 60° dendrites, G tips, B cloud) and `flare_noise.png` (fbm R/G/B, cellular edges A), plus `flare_marks0.png` (black placeholder).
  - Seen at 512: R reads as real feathered frost. G's tip dots are too dense and big: thin them (draw tips at about 30% chance and 1 px).
  - Log both in ASSET_PROVENANCE (not done).
  - Compare a ComfyUI frost plate on a gpu turn later.
- **`src/Fx/Flare/`**:
  - `FlareBits.cs` and `shaders/flare_bits.gdshader`: own particles. Kinds: Mote, Streak, Tongue, Puff, Thread, Soot. An additive batch, plus a lit, mixed "bed" batch made by string-replacing the render mode.
  - `FlareShards.cs` and `flare_shard.gdshader`: real lit ice-shard meshes that tumble, land and melt.
  - `FlareFx.cs`, the director. Handles Ready, Press, Release and Blow. Real-time `Tick(dt, b)`. Exposes `Frozen`, `LeadRate`, `Stop`, `WorldRate`, `HerRate` and `Quiet`. Runs the camera `Envelope()`, `Ready()` (staff-head breath, wick smoke), the press (staff flare, burnt missiles from `Watch(b)`), `SpendLight` (shadowed omni), the uniforms and the marks texture. `Kill(e)` and `DeathOf(id)` drive the crowd's held and shattered deaths. Hooks: `Cue`, `Rumble`, `HudDim`.
  - `FlareFx.Burns.cs`, Burns Twice:
    - the Draw's motes and threads homing into the staff head;
    - the head flame (amber, blue heart) and her smoking breath;
    - the frost front over 0.4 s, the cold repaint, and the web's return;
    - embers: one shared angle, a 0.14 s fall at 110 m/s, smoke trails, the first four lit (two shadowed). Called Down converges;
    - each landing: tongues, 16 shards, steam, sparks, soot, a char mark and the hitstop. The last is the BOOM;
    - the steam columns, and the shatters.

## Next, in order (exact)
1. **Wire it** (about 40 lines):
   - `BattleFx`: add `public readonly FlareFx Flare = new();` and AddChild it in `_Ready`. Set `Flare.Cam = Cam` and `Flare.HeightAt = heightAt`.
   - In `Handle`'s switch, first:
     - `case Ev.Flare fe: Flare.On(fe, b); break;`
     - `case Ev.Kill k when k.ByFlare && Flare.Active: Flare.Kill(k); break;` (no gore or Kenney bursts);
     - `case Ev.Hit h when h.ByFlare:` tally the number only for bosses and champions while `Flare.Quiet`. No Burst, no Gore.
   - `WorldScene.Update`:
     - if `Fx.Flare.Active`, `fightDt = dt * Fx.Flare.WorldRate` (the flare overrides the old hitstop);
     - after the step loop, if `Fx.Flare.Frozen`, call `b.FlareLead(Math.Max(0, dt*LeadRate - fightDt))`, then drain `b.Events` through Fx.Handle, Weigh and frameEvents, as the loop does;
     - call `Fx.Flare.Watch(b)` before the steps and `Fx.Flare.Tick(dt, b)` in Draw;
     - set `Fx.Flare.Her = HerDrawn` and `Fx.Flare.Staff = Player?.FindChild("arm:mage_staff", true, false) as Node3D` (cache it);
     - Player.Update gets `dt * HerRate` (not viewDt) while `Frozen || Stop > 0`.
   - `CrowdView`: `public static Func<int,int>? FlareDeath` (set to `Fx.Flare.DeathOf`). In the Dying case: `-1` returns (not drawn), `1` holds the body standing at its death's frame 0.
   - `Game`:
     - `Cue` → `Sfx.Flare(name, at, k)`;
     - `Rumble` → `Haptics.Add`;
     - `HudDim` → GameHud (dim to 35% except health, the Flare lamp and a boss bar);
     - `Motion` from Settings (1 / 0.5 / 0), `LessFlash` from Flashing.
   - Test args in `Game.Tour`: `--flare ID[+mod]` (set `b.Lamps`, `b.Flare`, and fill the meter; mods like `burns.black_ice`), `--flare-hp F` (the clutch), and `--cast T` (presses it already).
2. **Build, import, run.** `--quick arcanist --sex female --zone <arena> --horde 250 --cast 3 --shot NAME`. Get frames at the beats with `Shots.Want(tag, at)` from the director (ready, press+1f, Draw end, Hold, frost +0.1/+0.3, first impact, last, Return +1/+3 s). Better: Godot's `--write-movie out.avi --fixed-fps 60` for the 60 fps captures and strips (deterministic). Hand long batches to a `su-runner`.
3. **Sound** (§2.2, §2.3): `Audio/Sfx.Flare.cs`. Cues: catch, confirm, inhale (the riser from the reversed Spend, plus the gap at the last 0.1 s of the Hold), frost (thud, ice creak racing out, the wind dropping), ember_fall (the roar from the sky), ember_land (hiss and glass), ember_last (the four-layer BOOM, the valley echo), steam. Add the designed duck (world −12 dB, music −9 dB) and the crowd's bed. Offline numpy synthesis played through `Clip` is fine if logged as ours. Measure with `--wav`; the owner listens.
4. Luminance script (§1.6), frame time at the Spend (perf), then the max judge, then captures.

## Decisions
- **Globals, not masks**: only world shaders drain, so she, the Flare and the danger marks keep their colour for free.
- **Frost, web and scars live in the ground shader** (conformal, lit, no overdraw), not in decals.
- **Ember fall lag 0.14 s**: the logic picks the target at the blow, so the view lands it 0.14 s later. The killed are held standing until it lands. If that ever reads late, ask classes for an "aim" event 0.2 s ahead.
- **Own particles and shards**: the Sparks/Smoke batches use Kenney's sprites, which the owner's rule forbids for Flares.

## Gotchas
- The worktree guard refuses heredocs that write files and `cd X && ...` chains with odd constructs. Write scripts with the Write tool, or use Edit. **Never `python -`** (it opened a REPL that wrote 64 MB of errors).
- The first `--import` segfaults (139); the second is fine.
- Godot recompiles a `.gdshader` at its next launch.
