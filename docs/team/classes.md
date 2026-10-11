# Classes (phase 1: systems)

**State (12 October, end of session 3):** the Battle runs the classes design: the Kin rides the dash, the calling arts fire as reflexes, the Flare fills, casts, clutches and burns missiles, and **all 133 phase-1 lamp rules are wired** (one file per quarter, `*Lamps.cs`). The harness measures types, lamps, Flares and on-calling (`--offcalling`, `classes_summary.py`). A max judge passed it with fixes; the fixes are in. Next: a 12-seed re-sweep, the judge's remaining measurements, a short re-judge. Handoff: `docs/handoff/classes.md`.

**Key decisions**
- The art in hand is the dash form; the Kin's facets come only from lamps (no double source).
- A reflex borrows the art's wait while it runs, so the arts' own wait tricks work unchanged.
- The Flare's own damage never refills it; boss fill counts health lost, and a gate's Break only up to a tenth of its health (uncapped, poison on a gated boss filled 30 Flares a fight).
- By night sizes are quartered, prices kept in full, counts +1 at most, and a rule's defining number (a chance, reach or count it can't fire without) stays in full (CLASSES §2.10).
- On-calling is measured as a fitted home term (calling + road + home x road), because raw on/off mostly measures each calling's base strength.
- The Bulwark's rebuke: max health x10, growing 8% a level like the Flare ("the wall answers as hard as it is thick"); every block, the draft's Warding too, lays a stone; stones fall after 6 s of calm unless Mortar holds them.

**Measured** (12 seeds; details in the handoff §4)
- Types within x1.35 at tiers 1-4 except T2 chainbound 0.72 and T4 moonweaver 1.42; arcanists 1.5 at level 30 (night skills' balance).
- Full vs empty 0.86-1.20. On-calling home term 0.87-1.20 (never over x1.25).
- Flare: first 72-126 s, gap 66-81 s, 2.5-3.1 per boss, 15-19% of boss damage.

**Open questions (for the owner, via the main session)**
- The rebuke is under 1% of a Bulwark's night damage; a judge asked 8-15%. Getting there needs more rebukes or a wider one (phase 5's "Wider Rebuke"), not a bigger number.
- Home adds little today (median x1.03): only one of each road's three signature skills exists until phase 5.

**Notes for other areas**
- Story: `Ev.Flare` with `Clutch`, `Battle.FlareClutches`, `Ev.Rise`, `Ev.PlayerDeath` are the toll's countable hooks. Lamp, Flare and blessing names are drafts.
- Phase 2 (experience, VFX): `Ev.Flare` Press/Blow/End, `Battle.FlareFreeze`, `FlareFreezeScale`; Strike powers were raised (Burns Twice 1160, Branding 2100, Road's Toll 700, Drag Them Under 1590).
- Combat: the types' spread on an empty board (arcanists high, reavers low) is the night skills'; `Probe.Lamped` and `LAMPS_OFF` help.
- UI (phase 3): `Battle.Reflexes`, `FormReady`, `FlareMeter`/`FlareCharges`, `Battle.Stones` feed the HUD.
