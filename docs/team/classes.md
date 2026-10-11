# Classes (phase 1: systems)

**State (11 October):** session 1 of about 3. The Lamps board is data (360 lamps, 8 roads, 16 Flares) with the book (earning, lighting, respec, two layouts, type, Flare carried, night loadout), the new tags and Bound, and tests. The Battle wiring (dash forms, reflexes, the Flare's meter and window) is next. Handoff: `docs/handoff/classes.md`.

**Key decisions**
- `tools/classes/lamps_build.py` is the board's source; `lamps.json` is generated (keeps 32/14/6 shapes, joins and gates true).
- Every lamp effect carries the phase that makes it live (1 now; 4 grips; 5 new skills; 2/6 Flares): honest accounting, no dead lamps pretending.
- The hearth (dash form, reflexes, Flare lamps) and the Flares are the calling's own; roads, bridges and crossings are open to all (§2.7).
- Three free lamps: the hearth's start, the type's entry and its Strike. Changing the type puts every lamp out.
- `ch.Ability` stays the art in hand, which is now the dash form.
- Bound: tethered within 0.8 m of where it was caught, +20% from area; bosses are never locked.

**Notes for other areas**
- Story: every lamp and Flare name is a draft for your voice check (CLASSES.md §4 risk 7).
- UI (phase 3): `LampBook` has the API the Lamps screen needs (`CanLight` reasons, `Suggest`, `Spare`, layouts).
- Experience: atlas lamps are the world fact `lamps.atlas` (0-8).
