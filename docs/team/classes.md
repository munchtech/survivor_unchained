# Classes (phase 2 done; phase-6 plan judged, waiting on the owner)

**State (13 October, session 13):** branch `classes-10` (from integration 3935476c). The Flare is the owner's BOOM button: specialized (Clear, Save, Single, Context), and every press is seen. This session: Burns Twice's aimed embers and its last-ember shove (asked for by the Flare lead); the Road's Toll with nothing near; the phase-6 plan's role column (judge 7: PASS WITH FIXES, applied). Being traced: the "drift" (see Open). Handoff: `docs/handoff/classes.md`.

**Key decisions**
- Flare roles follow FLARE_LOOK (six Clears, four Saves, two Singles, four Contexts), confirmed in CLASSES §7's phase-6 plan. Judge 6's first table differed on eight Flares; the look's reading matches what each does in play.
- Every staged Flare's Blow events carry a ground point and radius even with nothing in reach. A Stand shows at its key.
- Balance never blunts a Flare. The night is tuned so a player who never times it well stays in band. Past the 35% arena share, the cut is a modifier's number or `bossMul`, never look, reach or room clear.
- Burns Twice: each ember is aimed 0.2 s before it lands (beat "aim"). An ember already falling counts the ice round its aim as broken; without that, a press killed about 15% fewer (diagnosed with a synthetic crowd). The last ember throws back what stands in reach (args "shove" 3 m, "shoveStun" 0.5, "shoveStagger" 0.15 on a boss).
- The Road's Toll with nothing near cuts twelve points on a zigzag along her aim (args "emptyFan", "emptyRadius").
- A boss takes half a rebuke. The pilot banks Banked Flame. A staged Flare's boss measure is calibrated on Act 1's story bosses (earlier sessions; still in force).

**Open**
- **The drift is a baseline question, not (yet) a regression.** `base11` (the "pre-Flare" target since 12 Oct) is not the pre-Flare code. The real pre-Flare game (9cbc654c, health 103/130/100/109) runs boss fights of 233 s with 0.125 falls a night. base11 runs 204 s with 0.030, and today never-pressing runs 225 s with 0.089. So today's never-press game is shorter and safer than the true pre-Flare game. The bisect (`S/bis`, p0-p5) shows where 11 October's fights moved. Don't tune anything to base11 until it's resolved.
- Burns' shove and aim: arena and Act 1 re-measure on fresh seeds (`S/w`). The first measure (`S/s`, before the aim fix) showed Flare kills -15% from the aim (now fixed) and Act 1 bosses 7.7% shorter for the arcanist (`S/v` C tests whether that's the boss stagger).

**Notes for other areas**
- **Flare lead and skills VFX:** Burns Twice's "aim" (one per ember, Target id or 0, Last on the 12th; the ember Blow follows 0.2 s later on its target's current spot, or bends to the nearest pack within 3 m of the aim if its target fell). "shove" (one per survivor after the last ember: TX/TZ where it rests, Radius how far, 0 for a boss). The Toll's empty cuts. Butcher's Hour has no blow: stage its press roar and frenzy until End. One Arrow's plain form is a 30 m clear today ("line" is phase 6). FLARE_LOOK L546 (Through and Through, Empty) needs the no-dash ring of cuts (judge 7).
- **Experience and animation:** `Ev.Flare` phases and `Beat` timings as before (Sim/Events.cs, lamps.json "beat"). Burns' embers still land 0.55-1.05 s from the press.
- **Story:** names unchanged. The four replaced modifiers' names (Thaw-Burst, The Eye, Free Hands, Through the Heart) still go to the story lead.
- **UI:** `Battle.Stones` pips; teach players that a Flare shortens the boss phase it lands in.
