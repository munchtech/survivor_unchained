# Classes (phase 2 in progress)

**State (12 October, end of session 6):** branch `classes-6`. Steps 1-3 of phase 2's opening (Banked Flame in the pilot, the rebuke, the Road's Toll's measure) are built, measured at 48 seeds and judged PASS WITH FIXES; the data and text fixes are done, two checks are open before merge. Phase 2's logic (the four staged Flares) is built and tested but not yet measured or judged. Handoff: `docs/handoff/classes.md`.

**Key decisions**
- The pilot banks Banked Flame (one charge kept for a boss or the edge): the lamp is a sidegrade banked, a trap unbanked; Light my way should never light it (owner asked).
- The Bulwark's rebuke: every blow that reaches her lays a stone, six stones, 8 m (owner: "a little more"); 3.6-7.9% of a night by tier. More, if wanted, from five stones, not reach.
- The Flare's boss share is counted on health taken (a gate's Break capped at a tenth), beside the damage share: damage poured into a boss's gate inflated the denominator.
- By night sizes are quartered, counts +1 at most, a rule's defining number in full; three prices follow their gift (CLASSES §2.10).
- A staged Flare's timings and numbers are data (lamps.json "beat" and "args"), its moments are events; the view stages it without touching the logic.

**Measured** (48 seeds; CLASSES §2.8, §7)
- Types T1-T4 (full): all in band except the moonweaver (T2 1.36, T4 1.38: known, phase 7). Butcher lowest (0.76-0.86).
- Flare share of boss health taken: 16-31% by type and tier; T1 median 26.9% (over 25%) reopened.

**Open questions (for the owner, via the main session)**
- Should Light my way light Banked Flame? Recommendation: never.

**Notes for other areas**
- **Experience (camera, time) and skills VFX (grade, look, sound):** every Flare emits `Ev.Flare` (Sim/Events.cs): Ready, Press (t = 0: freeze `Battle.FlareFreeze` 0.22 s at 8%, scaled by `FlareFreezeScale`; grade, push 12%, pitch 4°), Release (the key pose ends: time returns over 0.08 s, camera eases back 0.6 s), Blow (Part: toll, blast, frost, ember, cut, execute, pulse, blow; Last; TX/TZ where it landed; Target enemy id; Hitstop frames), Kill (a boss fell to it, or while a Stand held: the last blow's 0.6 s at 20% and 15° orbit, TX/TZ the boss), End. Timings per Flare are `FlareDef.Beat` (key, first, step/last, frost, hitstop, hitstopLast, hitstopExecute). Bell's camera pushes per toll (2%, 4%, 8%) and Burns Twice's lift (8°, 15% out) are in CLASSES §3.6, not data: add them to Beat if you want them there. Butcher's Hour: 1 frame of hitstop on each of her hits while `Battle.HourHolds`, 4 on an "execute" Blow.
- **Animation:** each staged Strike's blows land at `Beat` times from the press: Bell 0.3/0.55/0.8 (a fourth at 1.05 with Fourth Toll); Burns Twice frost at 0.3, embers 0.55-1.05; Road's Toll key 0.24, cuts every 0.08 s to 1.12 (18 cuts in the same span with Toll Doubled). Butcher's Hour: key 0.3 s (the roar), controls back at once. The clips should hit these times, or tell classes the times to change (data only).
- **Story:** `Ev.Flare` with `Clutch`, `Battle.FlareClutches`, `Ev.Rise`, `Ev.PlayerDeath` are the toll's hooks, unchanged. Lamp, Flare and blessing names are drafts ("Readier Wall" is new).
- **UI (phase 3):** `Battle.Stones` (now six to a rebuke) needs pips on the shield or by the meter, or the wall's rhythm is invisible. `Battle.Reflexes`, `FormReady`, `FlareMeter`/`FlareCharges` feed the HUD.
