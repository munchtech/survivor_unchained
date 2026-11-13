# Build direction: skills, tree, gear (the owner's interview, 13 November 2026)

Six rounds of questions against PoE2, Last Epoch, Diablo 3/4 and Grim Dawn. **Where this page differs from `ARPG.md` §3 (six keys, 9 Nov), this page wins.** Design only: nothing here is built yet.

## Decided

**The model:** Last Epoch. Each skill's own tree (the Wicks) transforms it, beside a passive board. Power is split: the tree and wicks set the plan, gear adds twists. Respec stays free at any lamp-post.

**Keys (replaces six keys):**
- **4 keys per weapon set,** and the basic attack takes one of them (Diablo-style, so it maps to a pad's four face buttons).
- **Two weapon sets; the swap changes the whole bar.** Set A is a calling weapon; set B may be off-calling. Weapons gate skills (sword skills need a sword).
- **What the swap is for:** situations, chaining buffs, movement, single target to AoE, and other creative uses. Every swap is also a strike, with an internal cooldown so it can't be spammed.
- **3 auto-only slots,** hers and always on through a swap: auras, summons and kindled triggers, opening by level. Auto skills granted by items stack on top of the three.
- **Dash, Flare and swap stay outside the 4.**
- **Pacing is per skill:** some skills build or spend a resource, others run on cooldowns. Not everything is builder/spender; some callings use mana.

**Supports:** items that slot into a skill to make fun combinations. Start with 1-2 sockets a skill, opening with rank; maybe more later.

**Unions:** hand-made, a few per calling at first, growing with updates. The owner's aim is "every reasonable pair", with a limiter (for example the two parts must differ in type, physical + ice, fire + lightning) so it never becomes a billion pairs. Linking takes rare items. A Union takes both keys and must never feel weaker than the two buttons apart: stronger if anything, but never mandatory, just a different build idea.

**Gear:**
- **Crafting** is a mix: safe deterministic steps (today's heat system) plus a rare gamble for a shot at a perfect piece.
- **Great uniques** rewrite a skill, enable a whole build, or grant an auto skill.
- **Sets** stay small (2-3 pieces) with minor perks, never the build.
- **Transmog:** a wardrobe filled by collecting looks, plus dyes.
- **Players:** single-player now, with systems kept ready for co-op.

**Progression:**
- **Levels:** PoE-style, but the cap is 75 (each level slower than the last).
- **Subclass:** the calling's road is a story choice, its own passives and maybe a skill, a moment with weight.
- **Death:** free in the campaign, with the story's toll counting each rise. The endgame is harder: limited lives, a lost map, and experience lost at high levels. A Hardcore mode is optional.

**Scope now:** Act 1 and the demo ship a fully fleshed-out Warden as the melee bruiser. Other archetypes come later.

## What changes in the code (from the 13 Nov summary)
- **Slots:** `SkillBook.SlotsAt` (2-6 keys) and the hands rule (`taught_builds.json`, HandsRuleTests) become 4 keys per set plus 3 auto slots; `Battle` gains weapon sets, a swap, and a swap strike with a cooldown.
- **Weapons:** they carry skill gates. The Warden's taught build is re-cut for 4 + 4 + 3.
- **New systems:** supports (sockets per skill by rank), the wardrobe, subclass, and a level cap of 75 (today 30; the board gives a point a level).
- **Unions:** the current pairs (`skills.json`, 10) stay hand-made; add the rare-item price and the lamp-post join (M7, not built).
- **Resolve** stays for the Warden but no longer paces every skill.

## Pushback on record
- **Complexity:** 8 carried skills (4 buttons per set), 3 auto slots, item auto skills, supports, Unions and a subclass make a PoE2-depth system. It works only if each layer opens at a different time: weapon swap, supports, Unions and subclass each need an unlock point across Act 1 and Act 2. The owner's 9 Nov worry ("6 is too many" with cast abilities) is answered by 4 keys, not by the layers.
- **Unions:** "every reasonable pair" hand-made is a large content cost. Start with a few per calling; a shape-by-element scheme (author leap + frost once) is the fallback if the list has to grow fast.

## Round 7 (the owner, 13 November)
- **Buttons:** 4. Dash, the Flare and the swap are not counted as skill buttons. Across both weapon sets she carries 8 skills, but only 4 are on the buttons at once. Every layer unlocks slowly over time.
1. **Gear slots:** every slot carries stats, and some slots are removed (which ones: the owner's pick, proposal below).
2. **An exciting drop:** one that grants a skill she might not get any other way, with the adrenaline of the drop and the dopamine of its sounds and visuals.
3. **Supports** drop as gems, with bad-luck protection: once she has a gem, that gem drops less often, so the others come.
4. **Item auto skills:** no limit on how many stack.
5. **Subclass:** chosen early, and it can be changed.
6. **Mana:** the Sorcerer for sure (the Arcanist's line); others undecided.
7. **The swap strike:** one per weapon set.
8. **The basic attack:** each weapon set starts with a basic skill that can be built in depth like any other (its own wick and supports), and it can be swapped for another skill.

## Round 8 (the owner, 13 November): overrides the weapon-set and slot lines above
- **The second weapon set is a stance, not a second skill bar.** She keeps the same 4 skills. Each set gives a cost/benefit stance: defensive, faster, buffs (battle stance versus defensive stance). The swap strike still comes from the weapon set. She carries 4 skills, not 8.
- **Open:** if her skills need a weapon type, does the stance weapon have to meet the same gate, or does the stance set skip gates (a shield-and-mace stance under greatsword skills)?
- **Slots:** belt, legs, cloak and bracers are removed, and the relic is cut. Body armor covers the whole body except the head, like a matching set. The cloak may come back later as something she customizes, never as a drop. Left: weapon, offhand, head, body, shoulders, hands, feet, amulet, two rings (10).
- **Slots (settled):** shoulders and hands go too, and boots stay. That leaves **8: weapon, offhand, head, body, boots, amulet, two rings.**
- **Weapon gates in a stance (the owner: "I want fun different combos to exist"). The coordinator's default, until the owner overrides:** a stance never turns her skills off. The stance weapon flavors the same skills instead. Under a shield stance her blows block and stun; under twin blades they come faster and bleed; under a mace they stagger. The fun is skills times stances: 4 skills and a few stance weapons give many combos, with no dead keys. A build's real choice is which stance it leans on, and what the stance costs (slower, less damage, less defense).
