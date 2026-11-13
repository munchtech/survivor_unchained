# The unlock ladder: when each layer opens

Coordinator #9, 13 November 2026. The one page every build-direction lane implements against. `docs/design/BUILD_DIRECTION.md` decides *what* the layers are; this page decides *when* each one arrives, and nothing else may invent its own level numbers.

**Why it exists.** BUILD_DIRECTION's own pushback: 4 keys, 3 auto slots, item auto skills, stances, supports, Unions and a subclass are PoE2-depth, and they work only if each layer opens at a different time. The owner (round 7): "Every layer unlocks slowly over time." So one new thing lands every one or two levels through Act 1, and no two land together.

## The ladder

| Level | What opens | Act | Owner |
|---|---|---|---|
| 1 | **Key 1: the basic attack** (the Warden's `sunder`, held). A real skill: its own wick, its own sockets, buildable in depth, swappable for another skill later. | 1 | bd-keys |
| 1 | **Auto slot 1** (the Warden's `groundbreaker`, kindled). | 1 | bd-keys |
| 4 | **Key 2** (`heroic_leap`, pressed). | 1 | bd-keys |
| 5 | **Key 3** (`shield_charge`, pressed). | 1 | bd-keys |
| 6 | **The subclass: her road.** A story beat with weight, its own passives and maybe a skill; changeable afterwards at a lamp-post. Early on purpose (Last Epoch's model, which is ours). | 1 | bd-ranks |
| 7 | **Auto slot 2** (`iron_vow`, kindled). | 1 | bd-keys |
| 8 | **The stance: the second weapon set, and its swap strike.** A story beat: she takes up a second weapon. Same 4 skills; the stance weapon flavors them and never turns one off. One swap strike per set, on an internal cooldown. | 1 | bd-keys |
| 9 | **Key 4** (the calling's fourth press skill; `dawnpulse` is the Warden's offer). | 1 | bd-keys |
| 10 | **Auto slot 3** (`watch_bell`, kindled). Item auto skills stack on top of the three, uncapped, from whenever such an item drops. | 1 | bd-keys |
| 12 | **Supports.** Gems start dropping (with bad-luck protection). A skill's socket 1 opens at **skill rank 3**, socket 2 at **skill rank 6**, so a favored skill sockets before a fresh one. | 2 | bd-sockets |
| 15 | **Unions.** Joined at a lamp-post, priced in rare items, both halves evolved, the pair differing in type. Takes both keys and is never weaker than the two apart. | 2 | bd-sockets |

Past 15 there is no new layer: a lamp a level to the cap of **75** (each level slower than the last), gear twists, and the deeper reaches of the wicks. The layers above are the whole ladder.

## Rules that go with it

- **Gear slots:** all **8** (weapon, offhand, head, body, boots, amulet, two rings) are hers from the start. No slot is a progression gate; what drops into them is.
- **Dash, the Flare and the swap** are never counted among the 4 keys and never occupy one.
- **Free respec** stays at any lamp-post: the keys, the wicks, the board, and the road.
- **Act 1 and the demo show the whole Act 1 half of the ladder** (levels 1-12). A layer that cannot be reached in Act 1 is Act 2's, and no lane may move one into Act 1 to show it off.
- **A level that teaches a layer teaches nothing else.** If a lane needs to move a number, it changes it here first, in one commit, and tells the coordinator; it never carries a local copy.
- The Warden is the only calling built to this ladder now. The other callings fill the same columns later; mana (the Sorcerer, on the Arcanist's line) is not built here.
