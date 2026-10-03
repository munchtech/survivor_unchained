# Game feel: research, audit and suggestions

What makes ARPGs and survivors-likes feel so good to play, what Survivor
Unchained does about it today, and what to build next. Written for the
main development session, to read and decide from. Nothing in the game was
changed; everything here is notes, and one measuring tool.

## The files, in the order to read them

1. **`README.md`** (this file): the map, and the top ten.
2. **`SUGGESTIONS.md`**: 22 concrete, prioritised changes. For each: the
   feeling it targets, what to build, numbers to start from, where in the
   code, the cost, and how to tell in play whether it works. Ends with
   what not to do and the targets to measure against. **Start here if you
   only read one file.**
3. **`AUDIT.md`**: how the game feels today, read from the code, sense by
   sense: what is strong, what is missing, what is off. Its §9 has the
   measured numbers from the headless arena (hits to kill, event rates,
   draft cadence) that several suggestions rest on.
4. **`RESEARCH.md`**: the findings, organised by what produces the
   feeling: impact, power growth, reward and anticipation, flow and
   escalation, sound, sight, touch and the ineffable. Opens with the ten
   findings that matter most. Sources and numbers throughout, labelled as
   sourced or estimated.
5. **`notes/`**: the six full research strands (about 30,000 words),
   with every quote and claim's URL: impact and juice; survivors-likes;
   ARPG loot and power; psychology; sound and touch; the ineffable (a
   corpus of 34,543 Steam reviews).
6. **`probe/`**: the measuring program behind AUDIT §9: the repo's arena
   bot (`godot/tests/ArenaPlay.cs`) counting, minute by minute, blows per
   kill, one-blow kills, hits, kills and pickups per second, projectiles
   and drafts. It compiles `godot/logic` read-only and is not part of the
   game. From the repo root, with the .NET 8 SDK:

       dotnet run --project docs/feel/probe -c Release -- 36

## What the research says, in four lines

- **Weight comes from reaction, time and sound, not brightness.** Hit-stop,
  sound in sync with the blow, and the camera are what separate "crunchy"
  from "soft and powerless"; more effects alone make "rainbows but no
  weight".
- **The reward is in the wait.** Dopamine follows surprise and suspense;
  the genre's best moments are staged reveals (the chest, the drop sound,
  the bar about to fill). Ration them, and scale ceremony to value.
- **The survivors fantasy is an inversion**: start fleeing the horde, end
  wading into it while it evaporates. Players praise a *state* ("brain
  off", "the hum") as much as the hands.
- **In a horde the unit is the kill and the crowd, not the hit**: feedback
  must be tiered and budgeted, and the crowd heard as one rising texture.

## What the audit found, in four lines

- Strong foundations: trauma shake, gated hit-stop, white-hot hit flash, a
  superb perfect dodge, a pickup vacuum with a notice-hop, layered
  procedural sound with voice gating.
- **Measured: ordinary creatures get *harder* to kill as the run goes on**
  (~1.5 blows at minute 5, ~4 at minute 30; one-blow kills fall from up to
  three quarters to one in twenty). The power fantasy is inverted.
- The big moments land flat: chests open instantly into text, evolutions
  and the boss's death weigh about as much as an elite's.
- No ladders (the XP chime climbs microtonally and faintly; kills never
  swell), no ducking or particle priority for big moments, no rumble, no
  dash buffer, a 12 Hz HUD.

## The top ten suggestions

By return for the work. The full specifications are in `SUGGESTIONS.md`.

1. **S-01: Make ordinary creatures easier to kill as the run goes on**
   (Tweak). Divide ordinary arena creatures' health by `1 + 0.12 ×
   minute`; keep elites, heralds and the boss on the steep curve. Tried
   headless: it turns the hits-to-kill slope the right way without making
   the arena safe. Pair with S-12's spawner so the field stays full.
2. **S-02: A musical XP crescendo** (Small). D minor pentatonic ladder from
   D6, one step per stone, merged not dropped, louder; the lodestone gets a
   jackpot sound of its own instead of the dash's.
3. **S-03: Big moments duck the small ones** (Small). An SFX-bus duck of
   −8 dB for levels, evolutions, chests and bosses; a hurt low-pass; crits
   never silenced by the hit gate.
4. **S-04: A level-up that sounds like a gain** (Tweak). Keep the minor
   figure, land on a held Picardy third.
5. **S-05: A 120 ms dash buffer** (Tweak). A dash pressed a moment early
   happens instead of vanishing.
6. **S-06: Bars that flow** (Small). Ember and health bars at frame rate,
   a glow from 85% full, a kill counter that pops.
7. **S-07: A particle budget with priority** (Small). Trails capped at 60%
   of the pool; level-ups, crits and deaths of note may always spawn.
8. **S-08: The kill, not the hit** (Small). Merged kill sounds with a crowd
   layer, and a multi-kill swell at 15/40/80/150 kills in 1.5 s.
9. **S-09: The chest as a sequence** (Medium). Pause, shake, reel, a
   jingle per tier, 1/3/5 items at 50/10/3%; skippable; ceremony scaled to
   contents.
10. **S-10: The evolution as a ceremony, mid-run** (Medium). Slow motion,
    a name card, the evolved weapon's first volley as a showcase; offered
    in arenas from the tenth minute.

Next after these: the boss as the run's peak and end (S-11), an arena that
swells and breathes (S-12), and damage numbers that merge and cap (S-13).

## Confidence

- The code reading is direct, with file and line references; anything
  that depends on seeing or hearing the game in motion is marked
  **inferred**, since this session had no GPU or speakers.
- The measured numbers come from a bot that drafts blindly; a player
  choosing for synergy will do better, but the trends held for all four
  callings.
- Research numbers are labelled sourced or estimated. Some primary pages
  could not be fetched; those claims are marked as coming from search
  summaries, and a few are marked unverified.
