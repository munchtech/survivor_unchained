# Grim Dawn: what the classes lead took

Summary notes for `docs/design/CLASSES.md`. The owner: "oh study grim dawn too, its got some great stuff".

## How it works

- **Two masteries per character**, chosen from ten (the tenth, the Berserker, came with *Fangs of Asterkarn*, 23 July 2026): 45 named class pairs (Soldier + Occultist is the Witchblade). Each pair's name and fantasy emerge from the mix.
- **The mastery bar:** points put into the bar itself give health and attributes and open the mastery's skills by tier. So every mastery has a "spine" you invest in, and skills hang off it.
- **Skill modifiers:** a base skill (Fire Strike) has modifiers bought with points (Explosive Strike, Static Strike) that change what it does; modifiers can lead to other modifiers.
- **Transmuters:** a skill modifier that changes the skill's whole mode (Blitz becomes a stationary ward; Cadence's damage converts), one of which can be active.
- **Devotion constellations:** a second, shared star map (about 85 constellations) bought with points earned from shrines. Constellations need affinities (colours) from others first, so the map is a puzzle. Five of them give a **celestial power** you bind to a skill: "on attack, 15% chance: summon a wolf". Procs from devotion and items make builds auto-fire much of their damage.
- **Items:** set items and Legendaries that add +ranks to named skills and grant item skills (granted procs). Respec at the Spirit Guide: costs iron, scaling with level, refunds points; mastery bar points cannot be refunded.

## What makes it "click and have fun"

- A **single fantasy per mastery** (Soldier, Arcanist, Nightblade) with a clean bar; pick two and you are a Witchblade.
- **Procs are fun to watch:** binding a celestial power and seeing a giant spectral wolf appear on its own feels like loot.

## What makes it "plan for hours"

- **The pair is the build:** 45 combinations, each with its own good skill pairs.
- **Devotion pathing** (affinity requirements) is a self-contained puzzle with known good answers per build.
- **"Bind this proc to that skill"** creates synergies between systems (an auto-attack replacer with a proc on it).
- **Conversion through items** (a Legendary that turns a skill's damage to chaos) rebuilds a build around one drop.

## Failure modes

- **Wall of numbers**: skill tooltips list ten values; the effect on play is hard to see.
- **Devotion is front-loaded tedium** (crossroads, affinity juggling) for a new player.
- **Mastery bar points can't be respecced**: a beginner's regret.
- **Two masteries hide each class's identity**: many builds are "the pair", and the single mastery's flavour fades.

## What we take

1. **The hybrid is named and rewarded:** each calling's two types join at a **bridge** whose lamps pay for carrying both, and a union per calling (the Witchblade feeling, inside one calling).
2. **Procs are our genre's language.** Grim Dawn's celestial powers are what our auto-firing game already is. Our calling arts (Shield Bash, War Cry, Smoke Bomb) become **reflexes**: lamps that fire an art when a condition is met (on a block, on a perfect dash, below a third of health).
3. **Transmuters** are our Blue Lamps' best form: one skill changes mode ("your Judgement Disc no longer flies: it orbits you as a shield").
4. **A spine to invest in:** each road's depth thresholds (lamps lit on the road open its deep lamps) are the mastery bar.
5. Avoid: unrefundable points and the number wall.
