# The ARPG direction (the owner, 8 November 2026)

**Read this before `ONE_BUILD.md`, `CLASS_IDENTITY_AND_TALENTS.md` and `DEMO_PLAN.md`: where they describe nights as the game, this page overrides them.** The design lead turns it into `docs/design/ARPG.md` (the loop, the systems kept, reworked and dropped, the migration list, the cost); the owner picks on that proposal first.

## The owner's words (8 November, the week's restart)

- "I've decided to completely move away from survivors like as a main part of the game. It will just be a fun arena mode we can do with daily challenges or something. But the game is now an ARPG, Diablo style game."
- Sieges once an act or so (`SIEGES.md`): "we don't need to build on that yet, just keep it in mind in design decisions."
- "We need to finish the body pipeline and quick makes in Marionette for new NPCs and build armor sets."
- "The tutorial needs to be revamped around being an ARPG only."
- "We need to solidify our art style as visually stunning cel shading painterly with vibrant colors."
- "We need to dial in on getting spells and effects and just having the game be fun."
- "Our charge thing needs some work. We def need a heroic leap and a cyclone/bladestorm thing."
- "Unions maybe are 2 skills combined but still take up both skill slots since 6 is a lot and that would get too complicated if it allowed for more total skills; however the union of 2 things would make bladestorm or something."

## What it means (the coordinator's reading; the design lead checks each line)

1. **The main loop is Diablo's:** zones, packs, elites, bosses, loot, towns, a story in acts (the seven chains stand), builds that grow through levels, skills and gear. The 12-minute night with the ember's cards is no longer the spine. The Wayfinder's table, the tiers and the endless are the **arena mode**: survivors fun with daily challenges, a side door, not the game.
2. **One combat, one build stands** (4 Nov): one character, one build, the same fight everywhere. What changes is where the talent offer happens: the ember's three cards were the night's try-before-you-buy; in an ARPG the Lamps and Wicks are lit at lamp-posts (or on level) and the "card" moment, if kept, belongs to the arena mode. The design lead decides and says why.
3. **Six skill slots, and Unions take two.** A Union is two carried skills combined into one skill that occupies both slots (the whirlwind plus the heavy swing makes Bladestorm). It never adds a seventh skill. This replaces ONE_BUILD's "a Union is one shared lamp and both keep firing".
4. **Movement and big skills are the fun:** the charge reworked (find what the owner means by "our charge thing": the dash charges, a charge skill, or a charge-up, and report before changing it), a **Heroic Leap** (jump to a point, land with a slam) and a **Cyclone / Bladestorm** (a spinning sustained AoE she moves through). Spells and effects get the budget: every press visible, the feel judged in motion at the play camera.
5. **The tutorial teaches the ARPG:** move, hit, a skill, a pack, loot, the first elite, a lamp-post, the first boss; nothing about nights, waves or the dawn card. The storybook lore intro before C01 stands (18 Oct).
6. **The art style is locked in words:** visually stunning, cel-shaded, painterly, vibrant colors (the Marvel Rivals kind, G1 picked 4 Nov). L1 continues to GATE G2 with "vibrant" as the check the last wave failed (a mauve day cast, a brown night pool).
7. **The character pipeline is unchanged and first:** P1 to RIGHT and the owner's A|B pick, then the P2 chain (gear on the base, hair, her paint), P3 quick NPC makes through Marionette, armor sets built as data on the slot shells (smart-armor-parts, player-gear-scope). Sieges want many soldiers and undead on screen: NPCs on the shared base with LODs, squads as data.
8. **Sieges inform, not schedule.** Systems built now that a siege will reuse: the director as assault groups with objectives and routes (P6's director already has waves and a surround director; keep it data), destructible positions, squad AI and a command radial, environmental weapons (the burning oil is a telegraph-kit effect; the ballista a mounted skill), three LODs of battle, a morale number, a dawn timer. Build none of it yet; do not build anything that makes it harder.

## Owner calls the design lead puts in its proposal (not asked now)

- Where the lamp/card offer lives in an ARPG (lamp-posts only, on level-up, or the ember's card kept as the arena mode's rule).
- Zone shape: handcrafted acts with set zones (Diablo 2 and 4) versus procedural layouts (Diablo 3 rifts, PoE maps) for the endgame maps.
- Loot cadence per `LOOT_DESIGN.md` under an ARPG's hour, not a night's twelve minutes.
- Death: an Ember Walker returns (the siege page) versus a night lost; what a death costs in the campaign.
- Difficulty: tiers per act (the arena's tiers) or world tiers.

## What is cut from the briefs on sight

- Any task framed around "the night" as the main game (the 12-minute night, the idler gate as the game's gate, the dawn card as the talent screen).
- The roguelite frame (already dropped 4 Nov).
