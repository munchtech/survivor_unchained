# Skill kinds: what each skill becomes (22 November 2026)

**Status: proposal, awaiting the owner's approval.** Paper only; no code changes until you approve it (P4 part 2).

Basis: your words of 21 Nov in `BUILD_DIRECTION.md` Round 9 and `GAME_PLAN.md` decision 15. Every skill below comes from the game's data (`godot/data/content/skills.json`: 34 skills and 10 Unions) and the bar code (`godot/logic/Rpg/SkillBook.cs`). Labels: **[O]** seen in our code or data this session, **[D]** checked in a public source this session, **[I]** inference or memory, not checked. This page covers the campaign only. The arena's drafts, which fire themselves and are not in the demo, are untouched.

| Skill | Today | New kind | Why |
|---|---|---|---|
| Sunder | key 1, held (her basic attack) | **pressed**, slice key 1 | Her main attack, held, the way ARPG main attacks work. |
| Heroic Leap | key 2 | **pressed**, slice key 2 | The genre's leap (Diablo's Barbarian [I]); her gap-closer. |
| Bladestorm | key 3, held | **pressed**, slice key 3 | The genre's whirlwind (Diablo's Barbarian [I]); it already spins while the key is held. |
| Iron Vow | auto slot 2 (braces by itself before a big blow) | **pressed**, slice key 4 (ruling 3) | Brace, take blows at half, return them in a ring: a defensive button. Timing the brace is the skill. |
| Shield Charge | key 4 | **pressed**, not in the slice's four | A line move like the Leap and the dash (`DEN_ROSTER.md`). It stays for later, and Falling Wall needs it. |
| Groundbreaker | auto slot 1 (fires itself near a crowd) | **node**: a Turn on Sunder's Wick | Your words: "every 3rd attack groundbreaks." Task 8 proposes it as the slice's one Turn. It replaces Splitting Stroke, which already makes every 2nd swing split the ground. [I] I read "attack" as Sunder, her basic attack. If you meant every skill's attacks, it goes on the Lamps board instead. |
| Rebuke | auto only (strikes back when she is struck) | **node** on the Lamps board | A rule on being struck, with nothing to press or aim. Retaliation is a passive in the genre (Diablo 4's Thorns [I]). Its riposte key goes. |
| Watch Bell | auto slot 3 (tolls by itself near a crowd) | **pressed** | It draws foes in to face her, so the moment should be her call, like a war cry (Diablo 4's Barbarian shouts [I]). Tolling by itself every 6 s would drag packs to her, the streaming that the den re-cut removes. |
| Hallowed Ground | auto only (near a crowd) | **aura** | While it is on, foes on the hallowed ground around her burn: a damage aura like Diablo 2's Holy Fire [I]. |
| Dawnpulse, Judgement Disc | both ways (pressed, or kindled near a crowd) | **pressed** | Already a cast and a throw on a press. The kindled form goes (Round 9). |
| Oathblade, Butcher's Cleaver, Iron Palms, Gale Chakram | key only | **pressed** (no change) | Already pressed only. |
| Axe Gyre | fires itself (no press record) | **pressed** | A press sets axes turning about her for a few seconds, the way Path of Exile's Blade Vortex adds blades [I]. Axes that circle her nonstop are the survivors-roguelike habit. |
| Thunderhead | fires itself (no press record) | **aura** | A cloud follows her and strikes what crowds her, the way Path of Exile's Herald of Thunder works [I]. |
| Gravecall | fires itself (no press record) | **pressed** | Raises the dead on a press, for a while, like Path of Exile's Summon Raging Spirit [I]. |
| Reaving Arc, Volley, Knifestorm, Firepot, Seeking Motes, Moonbrand, Cinderfall, Rimeshard, Hoarfrost, Arcweb, Umbral Bolt, Grave Tether, Verdant Lance, Blightfield, Thornbloom, Spirit Herd | fire themselves (no press record) | **pressed** | Thrown, shot or cast at the aim, as in other ARPGs. They fire themselves today only because nobody wrote their press records (`Content/Weapons.cs` 308-314) [O]. |
| Falling Wall, Butcher's Wheel, Hail of Steel, Dawn's Judgement, Frostfire Comet, Rotwood, The Barrow Host, Soul Lantern, Starfall (Unions) | two keys (all but Falling Wall and Dawn's Judgement fire themselves) | **pressed**, two keys | Both parts are pressed, so the Union is one pressed skill that takes both their keys (you, 8 Nov: "unions are 2 skills combined but still take up both skill slots"). |
| The Tempest (Union of Arcweb and Thunderhead) | two keys (fires itself) | **cut** for now | Thunderhead becomes an aura with no key, so this pair no longer joins two buttons. The idea can return with the Arcanist's kit. |
| Skills on items: "of Seeking Motes", "of the Gyre", "of Cinders", "of Dawn", "of Knives" | worn skills that fire themselves beside the auto slots, no cap | **an effect written on the item** | Round 9. Example: "every 5 s, three axes circle you." |

**One departure from the plan's wording.** Decision 15 says today's auto skills become tree nodes. On this page only Groundbreaker (your words) and Rebuke do. Iron Vow and Watch Bell are actions whose moment the player should choose, so they are pressed. Hallowed Ground is an aura.

**The bar after this page.** Four keys, all pressed; key 1 holds the basic attack; a Union takes two (the keys open at levels 1, 4, 5 and 9, as today). Auras have no key: they show as small icons beside the bar. A skill with the auto gem leaves its key, and the freed key takes another skill. Gone: the three auto slots and every kindled form. Not in the slice: auras, Unions, stances, and the auto gem unless task 8 picks it as one of the slice's three supports.

## Three rulings for you

**1. What an aura costs.**
- *Recommended:* no key. She switches an aura on in the skill screen, and it stays on, through a stance change too, until she switches it off. Each aura reserves part of a small separate pool that grows with level and gear and is never spent in a fight. This is Path of Exile 2's Spirit [D]: auras, buffs, permanent minions and meta gems reserve it; it starts at 0, the bosses and acts give 100, and body armor, amulets and scepters add more. Starting numbers, tuned in part 2: 30 per aura, with the pool enough for one at level 7, two at level 10 and a third with gear. That is about what the old auto slots held.
- *Why not her Resolve:* only the Warden has Resolve; the other callings' resources are still open (Round 7, item 6). And a reserved top costs her only when the bar would have filled past it, which is mostly Bladestorm's longest spins [I].
- *Alternative:* each aura reserves the top of her Resolve bar, the way Path of Exile 1's auras reserve mana [I]. Nothing new on screen, and the cost shows as a locked end of the bar. Against: it works for the Warden only, and she may seldom feel it [I].

**2. What the auto gem does and costs** (working name: Kindling).
- *What it does:* socketed in a pressed skill, the skill leaves its key and fires itself when its moment comes, a moment its data already names. Iron Vow braces when a big blow is about to land; Dawnpulse fires when a crowd is close. A skill with no moment named fires whenever it is ready and a foe is in reach. It still pays its Resolve each time. It cannot go on a held skill (Sunder, Bladestorm), on one that moves her (Heroic Leap, Shield Charge), or on a Union, since that would free two keys.
- *Recommended:* it reserves 30 from the same pool as an aura and takes one of the skill's sockets (a skill has one or two). That gives one rule for anything that works without a press. Path of Exile 2 does the same: its meta gems, such as Cast on Shock (60), reserve Spirit alongside the auras [D].
- *Alternative:* no pool. The skill hits 30% lighter and waits half again as long, and only one skill at a time may carry the gem. Against: always-on things would then follow two rules, and a cap of one is a hard wall where a pool would be a budget.

**3. The fourth pressed skill** (the slice's key 4).
- *Recommended:* **Iron Vow.** She plants her feet, takes blows at half for 2 s and returns them in a ring, so it is not a line move. The re-cut den gives one heavy foe a readable slam (`DEN_ROSTER.md`, approved), and bracing into that slam is an answer other than the dash. It is already built: her clip, its sounds and its effects [O]; it ran in auto slot 2. Genre melee kits keep a slot for a defensive cooldown, as the Barbarian does in Diablo 3 and 4 [I].
- *Alternative:* **Judgement Disc**, a thrown shield that ricochets five times through a pack, for 25 Resolve. It would be her only ranged hit, and holy color in an otherwise physical kit. Against: no throw clip of hers exists yet [O], so it adds animation work to the slice.
- Shield Charge leaves the slice's four either way.

## For the code, after your approval (part 2)

- **Bar:** `SkillBook.cs` (the bar, from line 69). `KeysAt` stays. `AutosAt`, `IsAuto`, `Both`, `SetAuto` and the auto halves of `TakeUp`, `Swap` and `Carried` go, along with `Weapons.AutoSlots` and the press record's `kindled` option. `taught_builds.json`: keys become Sunder, Heroic Leap, Bladestorm and ruling 3's pick (level 9); "autos" goes; Shield Charge joins "later". The hands-rule tests lose "three autos, all kindled" and "half the kit offered kindled".
- **The 27 skills with no press record** fire themselves even on a key today. None of them is offered in the campaign until it has a press record (none is in the demo).
- **One count, not three:** Sunder already keeps two, its heavy line every 4th swing (`skills.json`) and her Hand's heavy blow every 6th (`hands.json`) [O]. The Groundbreaker Turn should ride one of them, so one button never shows three rhythms.
- **Reuse:** the auto gem reads the moments in `Sim/Kindle.cs`. The item skills are the `Grants` affixes in `Rpg/Items.cs` 376-385.

Source [D]: maxroll.gg, "Spirit guide" (Path of Exile 2), https://maxroll.gg/poe2/resources/spirit-guide, read 22 Nov 2026.
