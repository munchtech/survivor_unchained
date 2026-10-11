# Classes (phase 1: systems)

**State (11 October, end of session 2 of about 3):** the Battle runs the classes design: the Kin rides the dash as its form, the calling arts fire as reflexes, and the Flare fills, casts (Q / right-click), clutches and burns missiles. The harness knows types, lamps and Flares. The Flare's timing and boss share are tuned and mostly in band. Next: wire the remaining ~100 phase-1 lamp rules (warden in progress), re-measure, fix what's out of band, then a judge. Handoff: `docs/handoff/classes.md`.

**Key decisions**
- The art in hand is the dash form; the Kin's facets come only from lamps, while a learned form keeps ArtBook's (no double source).
- A reflex borrows the art's wait while it runs, so the arts' own wait tricks (Rebound, Quickening, Quarry) work unchanged.
- The Flare's own damage never refills it, and boss fill counts only other sources (it can't feed itself).
- The fill table was tuned by the harness (CLASSES §3.2): champions and kills are capped per second, because this horde has about 40 champions a minute.
- Flare damage follows the game's ember scaling (+8% a level), so it keeps pace with a night's build (boss share 14-23%).
- Small lamps' rules sleep by night (only the road's lean), per §2.10. Rules stack across lamps and scope to their skill or tags.

**Measured (482124f0, rules mostly unwired: baseline only)**
- Flare: first 1.3-2.5 min; gap 63-116 s (casters 104-116 s, above band); 1.7-3.8 per boss; 14-23% of boss damage.
- Types vs median: out of band at verge T4 ×1.96, roadknife T3 ×1.42, butcher T3 ×0.66, bulwark T2 ×0.68.
- Full board vs empty: 0.63-1.24 (prices are in, gains not yet).

**Notes for other areas**
- Story: `Ev.Flare` with `Clutch`, `Battle.FlareClutches`, `Ev.Rise` and `Ev.PlayerDeath` are the countable hooks for the toll. Lamp, Flare and great-blessing names are drafts for your voice check.
- Phase 2 (experience, VFX): `Ev.Flare` Press/Blow/End, `Battle.FlareFreeze` (0.22 s at 8%), and `Battle.FlareFreezeScale` for the setting.
- Combat: the types' spread mostly follows each road's three signature skills in the draft; their own balance is yours.
- UI (phase 3): `Battle.Reflexes` (`Cd`, `Full`), `FormReady`, `FlareMeter`/`FlareCharges` feed the HUD. Today's readout is plain debug (`ArtNote`).
