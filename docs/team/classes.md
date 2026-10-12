# Classes (paused after phase 1)

**State (11 October, end of session 5):** paused by the owner. Phase 1 (systems) is merged. `classes/phase1b` carries the Echo fix (its wait is a quarter by night, as its echo is) and Moonfire as an arcane hit instead of a Burn (it seeded Pyre Burst chains); judged PASS WITH FIXES, fixes done, 818 tests green. Next, when resumed: phase 2 (the beat and four Flares), starting with Banked Flame in the pilot and the Road's Toll on bosses. Handoff: `docs/handoff/classes.md`.

**Key decisions**
- The art in hand is the dash form; the Kin's facets come only from lamps.
- A reflex borrows the art's wait while it runs.
- The Flare's own damage never refills it; boss fill counts health lost, a gate's Break only up to a tenth of its health.
- By night sizes are quartered, counts +1 at most, a rule's defining number in full; prices stay in full except three that follow their gift (the Echo, the Crowded Sky, the Butcher's Count) (CLASSES §2.10).
- A lamp's effect never seeds another calling's chains by accident: Moonfire is arcane, not a Burn.
- On-calling is measured as a fitted home term (calling + road + home x road).

**Measured** (48 seeds; CLASSES §7 "Phase 1, measured")
- Types at T3/T4 all in band except moonweaver T4 1.38 (passed untrimmed: its empty board's 1.14; a 2% trim is below what 96 seeds resolve). Butcher 0.80/0.82.
- Full vs empty in band; on-calling home term 0.85-1.22; Flare first 54-123 s, gap 52-81 s, 3 per boss, 15-23% of boss damage.

**Open questions (for the owner, via the main session)**
- The Bulwark's rebuke is under 1% of its night damage (a judge asked 8-15%).
- Home adds little today (median x1.03) until phase 5's signature skills.
- Act 1's story bosses' health raised x1.10 to x1.15 (11 October, the owner's call), so they last as long as before the Flare (CLASSES §7 Open (5)).

**Notes for other areas**
- Story: `Ev.Flare` with `Clutch`, `Battle.FlareClutches`, `Ev.Rise`, `Ev.PlayerDeath` are the toll's hooks. Lamp, Flare and blessing names are drafts.
- Phase 2 (experience, VFX): `Ev.Flare` Press/Blow/End, `Battle.FlareFreeze`, `FlareFreezeScale`. Moonfire is now a violet arcane flash on the new mark bearer (credit "moonfire").
- UI (phase 3): `Battle.Reflexes`, `FormReady`, `FlareMeter`/`FlareCharges`, `Battle.Stones` feed the HUD.
