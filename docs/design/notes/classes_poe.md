# Path of Exile 1 and 2: what the classes lead took

Summary notes for `docs/design/CLASSES.md`. The survey of skills-as-gems is in `docs/SKILLS_RESEARCH.md` (PoE section); this goes deeper on the tree, the ascendancies and supports.

## How it works

- **One shared passive tree** (PoE 1: about 1,300 nodes; PoE 2: about 1,500). Each class starts at a different place on it. The tree's regions are the attribute colours (Strength, Dexterity, Intelligence), and the classes sit at or between them. Anyone can walk anywhere; distance is the cost.
- **Node grammar:** small nodes (+10% of a thing), notables (named, a few small effects together), **keystones** (one rule with a real cost: Chaos Inoculation sets life to 1 and makes you immune to chaos; Resolute Technique means you always hit and never crit). Jewel sockets let items add or change nodes (Thread of Hope lights nodes far away; timeless jewels rewrite a region).
- **Ascendancy** (8 points, from labyrinth or trial fights): about six signature notables, the class's fantasy in rules (Juggernaut cannot be slowed; Deadeye's projectiles chain). PoE 2 has three per class and adds more over time.
- **Skill gems and supports:** the skill is the item; supports change it (more projectiles, added fire, area). PoE 2 drops gems uncut (a currency of choice) and puts supports on the skill gem itself; 0.3 added Lineage Supports (unique supports with build-defining rules), 0.4 added about 35 more.
- **Weapon sets (PoE 2):** two loadouts swapped in play; passives can be assigned to one set only, so a build can carry a "boss set" and a "clear set".

## What makes it "click and have fun"

- Very little, honestly: PoE's fun starts once a guide is followed. The clicking pleasure is the skill gem: socket Fireball, it works.
- PoE 2 does better: the class's starting area is labelled, and the ascendancy is a short, legible menu of six.

## What makes it "plan for hours"

- **Pathing efficiency**: reaching a distant keystone while picking up life on the way is a puzzle with a real answer.
- **Keystones with costs** create build identities nobody designed (CI, Eldritch Battery, Ghost Reaver).
- **Items that rewrite the tree** (jewels, uniques that grant keystones) make the tree and the loot one game.
- **Conversion chains** (physical to fire to chaos) and "hit vs ailment" scaling make the same skill play two ways.

## Failure modes

- **Opacity.** Mechanics stack in ways the tooltip never shows; real builds need external calculators (Path of Building). New players make unrecoverable trees.
- **Regret orbs.** Respec is costly, so experimentation is punished.
- **Travel tax.** Much of the tree is +10 attributes on the way to something; nodes nobody wants but everyone takes.
- **"Anyone can do anything" means every class plays the same build at the top** unless the ascendancy is strong. PoE 2 answered with ascendancies that change how skills behave.

## What we take

1. A **shared board** where each calling starts at home, and distance is the price of going elsewhere: the owner's "anyone can do anything ... certain things are easier or better" exactly.
2. **Keystones with a real cost** (our Blue Lamps), few and named.
3. **Items that light far nodes** (a Legendary that lights one Blue Lamp anywhere).
4. **Keep the board small** (about 340 lamps, not 1,500), every lamp's text one line, and say what it feeds. **Respec free**, by day.
5. Supports become our **skill lamps** (three small changes per skill) and the night's evolutions, not a socket economy.
