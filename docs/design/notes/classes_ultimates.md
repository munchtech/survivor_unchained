# Ultimates and limit breaks: what the classes lead took

Summary notes for `docs/design/CLASSES.md` §3. None of the ARPGs studied has a charged ultimate as their core; the best ones are in other genres.

| Game | How it charges | What it does | Why it works, and what goes wrong |
|---|---|---|---|
| **Final Fantasy VII** (Limit Break) | damage taken | a big, staged move; levels unlock new ones | **Taking damage fills it**, so it arrives when you're in trouble: the original "dopamine life-saver". Wrong: charge too slow, saved and never used. |
| **Hades** (the Call, God gauge) | damage dealt and taken | a god's power, with a brief invulnerability; boons change it | **Invulnerable while it plays**, so it's a panic button, and boons customise it (our tree modifiers). Wrong: a few Calls dominate. |
| **Hades II** (Omega moves, Hex) | magick spent / per kill | a hex (charged ultimate) chosen from the patron | One chosen hex per run with path upgrades: the "choose your ultimate, then shape it" model. |
| **Devil May Cry** (Devil Trigger) | style and hits | a timed transformation: faster, stronger, mends | **A state, not a strike**: seconds of being a god. The look (the change of silhouette) sells it. |
| **Overwatch** (ultimate charge) | damage, healing | one decisive ability per fight | **One per fight, felt by everybody.** Charge shown as a percent: it becomes a plan ("I'll have it for the boss"). Wrong: hoarding, and ultimates countering ultimates. |
| **Diablo III** (Archon, Wrath of the Berserker) | cooldown | timed transformation | The most remembered class moments of D3; a cooldown means no dopamine from earning it. |
| **Diablo IV** (Ultimate skills) | cooldown | Death Trap, Cataclysm, Army of the Dead | Big looks, but on a timer they're rotation, not a limit break. |
| **Bayonetta** (Witch Time) | perfect dodge | the world slows | **Reward a close call** with power: our perfect dash already does this. |
| **Vampire Survivors** (limit break; screen-clear pickups) | level-ups, pickups | a screen-clearing flash | Clearing the screen is the genre's strongest single dopamine hit. |

## What makes an ultimate "AWESOME" (common to the best)

1. **The key pose:** a held frame (0.2-0.4 s) where the world dims and the hero strikes a silhouette. Every limit break has one.
2. **Hitstop on the impact:** a few frames of freeze sell weight more than particles do.
3. **A change of the world:** colour drains, time slows, sound drops out and returns. The screen says "this is different".
4. **Sound first:** an inhale (a sub-bass drop, the music ducked), then the release.
5. **Invulnerability while it plays**, so the player's reward is never punished.
6. **Earned, not timed:** a meter filled by danger and success, shown as it fills.

## What goes wrong

- **Hoarding** (saved for a boss that never needs it): solved by charging from damage taken and close calls, so it's full when you're in trouble, and by a full meter that "glows" so it begs to be used.
- **Spam** in a horde game (kills fill it too fast): kills give little and are capped per second; danger gives a lot.
- **Visual noise** hiding enemy telegraphs: enemy danger marks always draw over an ultimate's light.
- **Losing control** for too long: our cap is 0.6 s without control.

## What we take

- Charge from **danger (taken, close calls) more than from success (dealt, kills)**; a one-time surge when health drops low.
- **Two shapes per calling type**: a **Strike** (instant, one decisive moment) and a **Stand** (a timed state, DMC and Archon).
- **Invulnerable while it plays**, a universal **key pose and hitstop grammar**, then each ultimate's own look.
- **Customised by the tree** (Hades' boons on the Call), three modifier lamps per ultimate.
