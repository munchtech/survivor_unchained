# Last Epoch: what the classes lead took

Summary notes for `docs/design/CLASSES.md`. The survey of its skill levelling is in `docs/SKILLS_RESEARCH.md`.

## How it works

- **Five base classes, three masteries each** (15). Pick the mastery at about level 20. Each mastery has its own passive tree of about 25 nodes, beside the base class tree; points spent in the chosen mastery unlock deeper tiers (a node needs N points in that tree). You may put points in the other two masteries' trees, but fewer of them and never their mastery skills. (Since 2025 the mastery can be changed.)
- **Every skill has its own tree** (about 20 nodes). A skill gains experience when used, to level 20; each level is a point in its tree. Five specialisation slots match the action bar. Nodes rewrite the skill: Fireball becomes three homing fireballs, or a slow giant orb, or converts to cold.
- **Respec:** passive points are refunded one at a time for a little gold, and a skill's tree costs levels to respec. Cheap enough to try things.
- **Item-level hooks:** uniques and set items name a specific skill node ("+3 to Fireball"); experimental affixes; Legendary Potential lets a unique carry rare affixes.

## What makes it "click and have fun"

- **Per-skill trees read as "make this skill do the thing I want".** A new player who loves one skill can follow its tree and feel it change. Visible, direct cause and effect.
- Masteries name a fantasy in one word (Forge Guard, Spellblade, Beastmaster) with a portrait and three signature skills.

## What makes it "plan for hours"

- **Skill-tree nodes that point at other skills** (a Warpath node that fires Smite when you spin; Rive applying the Void Cleave's echo). Combining two skills' trees is where the builds are.
- **Mastery thresholds**: going deep in your mastery is strong, dipping into the others is a real cost decision.
- **Conversion nodes** change a skill's element and so which passives it wants.

## Failure modes

- **Many trees to read**: five skills times 20 nodes plus 3 trees; some nodes are flat "+12% damage" filler.
- **Skill levelling before planning:** a new skill starts low (mitigated by the minimum skill level).
- **Mastery as a lock** for the first years: a wrong choice at 20 was permanent, and it was hated (changed in 2025).

## What we take

1. **A calling's two types are its masteries:** two roads with depth thresholds (a road's deep lamps need lamps lit on that road), and the other road still open, at a cost. **Never a lock.**
2. **Skill lamps:** a few lamps per signature skill that rewrite it (LE's per-skill tree, compressed to three lamps per skill on the road, so there is one board to read, not twelve).
3. **Nodes that point at another skill** are our notables' main job ("when Rebuke strikes, Sunder's next blow is heavy").
4. **Cheap respec** and items that name a lamp.
5. Avoid filler: no lamp that only says "+n% damage".
