# The Warden's four skills: what fires, and the hooks for VFX

For the skills VFX lead (Combat VFX 7 first). Written by Classes 16, 1 November 2026, from classes-15 (MR1).

**Where things live.** Events are in `godot/logic/Sim/Events.cs` (`Ev.*`) and are emitted from `godot/logic/Sim/WardenSkills.cs`. The view is `godot/src/Fx/BattleFx.cs` (the event switch, about lines 1236-1335) and `BattleFx.Skills.cs`. Art keys come from the skill's `"art"` in `godot/data/content/skills.json`, plus the suffixes below. Today most of them fall through to the generic Beam, Explosion and Nova looks.

**Schools:** Sunder and Groundbreaker are physical; Rebuke and Watch Bell are holy. **Sizes** are given at rank 1, and area grows 4% a rank. Timings come from `skills.json` and `wicks.json`.

## 1. Sunder

A passive two-hander cleave: cooldown 1.6 s, reach 3 m, arc 220°. The `wide_swing` lamp widens it to 300°, and `still_reach` makes it longer while she stands still.
- **Every swing:** `Ev.Slash` with Art `slash_heavy`. `Swing()` in BattleFx.Skills.cs (about line 264) already has a heavy look for it.
- **Every 4th swing is heavy** (every 2nd with the Splitting Stroke Turn). A heavy swing also fires `Ev.Beam` with Art `slash_heavy_line` (WardenSkills.cs about line 32): a ground split 7 m straight ahead, 1.2 m wide, lasting 0.4 s.
  - Wanted: a crack or split line, dust, and a clear heavy read.
  - The `burning_edge` lamp adds a holy sear on the line. The event's School stays physical, so a tint is optional.

## 2. Groundbreaker

Cooldown 5 s. She drives the blade into the ground, a crack runs to the densest pack within 10 m (14 m with `fault_line`), and the ground heaves where the crack ends. She plays her heavy attack pose (done).
- **Crack:** `Ev.Beam` with Art `slash_quake_crack`, 1.2 m wide, 0.35 s (about line 89). The `twin` lamp gives two cracks, splayed either side.
- **Heave:** `Ev.Explosion` with Art `slash_quake_heave`, radius 2.5 m (grown by area), Power from 0 to 2 (about line 136). It stuns for 0.6 s. The `upheaval` lamp throws lesser things up.
- **Aftershock Turn:** `Ev.Strike` with Art `slash_quake` and Delay 0.8 s at the same spot, then a heave at 35% (about line 323). `Fall()` and `Landing()` already treat `slash_quake` as a ground mark.

## 3. Rebuke

Reactive: it has no timer.
- **When it fires:** on every blow that reaches her, blocked or not, at most once every 0.5 s.
- **What it does:** holy light strikes the one who struck her and the 5 nearest it within 5 m, and throws them back (knockback 0.6). The same champion is struck at most once every 5 s.
- **Carried:** it also raises her block chance, 8% at rank 1 and 1% more a rank.

The events:
- **Strike:** `Ev.Nova`, centered on the striker, Radius 5, Duration 0.25, Rings 1, Art `nova_holy` (about line 200).
- **The block itself:** the existing hit event's `Blocked` flag (Events.cs lines 35 and 54).
- **Shield of Morning Turn:** each strike leaves her a small barrier for each creature struck (see hook b).

**Readability (keep this).** In a press it fires up to twice a second, so the look is a shield flash at her plus a lash or burst on what it strikes. Not a big ring every 0.5 s.

## 4. Watch Bell

Cooldown 6 s. It tolls only when something is within reach: 8 m, or 10 m with the `loud` lamp. A toll does three things:
- it draws everything that isn't a boss to about 1.2 m from her, as a slide;
- it strikes everything in reach (12 damage);
- it gives her a barrier of 1% of max health for each thing drawn (at most 5 count), up to 15% held.

The events and variants:
- **Toll:** `Ev.Nova`, Radius 8-10, Duration 0.35, Rings 2, Art `nova_holy` (about line 255).
  - Wanted: a bell-toll ring (a sound wave, bronze or holy), the inward draw read clearly (the enemies' slide is already in the sim), and the barrier gain on her.
- **Stone Bell Turn:** each toll lays 2 stones, and each champion drawn lays 1 more.
- **`oath_and_bell` lamp:** a stagger rings an extra toll.
- **Pulse Turn on the bell:** 3 follow-up tolls at 85% size.

## Hooks

- **a) Own art keys.** Rebuke and Watch Bell both use `nova_holy`, so they share Dawnpulse's look. They get their own keys, `rebuke` and `watch_bell`. The sim never reads art, so balance doesn't move. *Classes does this in MR2; a line here will say when it lands.*
- **b) Barrier gain.** Only `Ev.ShieldHit` (absorbed, broke) exists today, and no event fires when she gains a barrier. `Ev.Barrier {X, Z, Amount, Source}` will be emitted where `WardenSkills.Toll` and `RebukeStrike` add to `Player.Shield`. *Classes does this in MR2; a line here will say when it lands.*
- **c) Generic Turns.** Split, Wide, Linger, Pulse, the On-kill echo and the fire, holy and frost schools are parameters on the same events (count, size, school), per CLASS_IDENTITY_AND_TALENTS §6.2 risk 1. No new art per Turn.
