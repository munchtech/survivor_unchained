# Classes (phase 2 done; phase-6 plan with the owner; Act 1 baseline named)

**State (13 October, session 15):** branch `classes-11`. Wave 6a built: the Branding (measured: Act 1 -22.4% against the baseline, -1.7% against its plain form, arena share 21-24%), the Long Cut, One Arrow, Drag Them Under and the Butcher's Bill (built and tested, not yet measured). The four new modifiers' texts are in; The Eye and Through the Heart have logic, Thaw-Burst and Free Hands wait for 6b. Handoff: `docs/handoff/classes.md`.

**Key decisions**
- Flare roles follow FLARE_LOOK (six Clears, four Saves, two Singles, four Contexts), confirmed in CLASSES §7's phase-6 plan. Judge 6's first table differed on eight Flares; the look's reading matches what each does in play.
- Every staged Flare's Blow events carry a ground point and radius even with nothing in reach. A Stand shows at its key.
- Balance never blunts a Flare. The night is tuned so a player who never times it well stays in band. Past the 35% arena share, the cut is a modifier's number or `bossMul`, never look, reach or room clear.
- Burns Twice: each ember is aimed 0.2 s before it lands (beat "aim"). An ember already falling counts the ice round its aim as broken; without that, a press killed about 15% fewer (diagnosed with a synthetic crowd). The last ember throws back what stands in reach (args "shove" 3 m, "shoveStun" 0.5, "shoveStagger" 0.15 on a boss).
- The Road's Toll with nothing near cuts twelve points on a zigzag along her aim (args "emptyFan", "emptyRadius").
- A boss takes half a rebuke. The pilot banks Banked Flame. A staged Flare's boss measure is calibrated on Act 1's story bosses (earlier sessions; still in force).

**Open**
- **Act 1 baseline "pre-Flare 11 Oct" (adopted 13 October; CLASSES §7 Acceptance):** 9cbc654c at health 103/130/100/109, never pressing, seeds 1-32: 233 s, 0.125 falls a night. Today against it on matched seeds: never pressing -0.1% (0.093), careless -7.5%, good use -17.7% (0.034), bankers -24%. In band; no re-tune. base11 is retired: it was the Flare's first build pressed with the 3 s press stun (matched fight for fight). The "drift" was base11 plus a seed-set mismatch (1-32 against 1-96).
- Burns' shove and aim, re-measured against the true parent 3935476c (batch W, fresh arena seeds): Flare kills a press +12-16% at every tier, Act 1 -1.4% (inside 2%; without the boss stagger -2.6%, so it stays at 0.15), arena deaths and damage taken within noise. Merge requested at 30899ed3.

**Notes for other areas**
- **Flare lead and skills VFX:** Burns Twice's "aim" (one per ember, Target id or 0, Last on the 12th; the ember Blow follows 0.2 s later on its target's current spot, or bends to the nearest pack within 3 m of the aim if its target fell). "shove" (one per survivor after the last ember: TX/TZ where it rests, Radius how far, 0 for a boss). The Toll's empty cuts. Butcher's Hour has no blow: stage its press roar and frenzy until End. One Arrow's plain form is a 30 m clear today ("line" is phase 6). FLARE_LOOK L546 (Through and Through, Empty) needs the no-dash ring of cuts (judge 7).
- **Experience and animation:** `Ev.Flare` phases and `Beat` timings as before (Sim/Events.cs, lamps.json "beat"). Burns' embers still land 0.55-1.05 s from the press.
- **Story:** names unchanged. The four replaced modifiers' names (Thaw-Burst, The Eye, Free Hands, Through the Heart) still go to the story lead.
- **UI:** `Battle.Stones` pips; teach players that a Flare shortens the boss phase it lands in.
