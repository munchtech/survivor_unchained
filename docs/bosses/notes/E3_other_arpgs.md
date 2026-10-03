> Research notes for `docs/bosses/`, kept as written. Where the **Verification** section at the end corrects a claim, the correction stands; `RESEARCH.md` uses the corrected version.

# E3 — Boss fights in other ARPGs (Grim Dawn, Lost Ark, Titan Quest, Torchlight, Souls lessons)

Strand: Grim Dawn, Lost Ark, Titan Quest, Torchlight I/II/III/Infinite, and Souls lessons that transfer to an isometric camera. Every factual claim carries a URL; "(secondary)" marks claims seen only in a search summary. Reddit, grimtools.com and wikiwiki.jp were blocked from this environment, so player opinion comes from Steam discussions and the Crate forums.

## Summary of lessons

1. **Make damage into verbs.** Lost Ark's stagger bar, blue-glow counter window and breakable weak points ask for a *kind* of damage at a *time*, so build choice becomes role choice. A visible stagger bar filled by fast auto-weapons (with an Elden-Ring-style regen delay) is the most transferable system in this strand.
2. **Replace invisible attrition with one readable big hit.** Grim Dawn's 2023 "Sunder" reform removed resist-shred from ordinary monster attacks, added one slow, dodgeable, non-stacking "take X % more damage" hit per boss, slowed those animations and stopped late tracking. Advice to players shifted from "stack 180 % resist" to "dodge the wing flap".
3. **One-shots are tolerated only when rare, named, telegraphed and positional** (Valtan's second axe, Kakul's hammer rows, Hades' raised-hand Shadow Star). Coincidence deaths in a crowd, on-death explosions and no-warning effects are the most resented mechanics in horde modes (Grim Dawn Crucible, Torchlight III).
4. **Key phases to visible HP milestones and change the body or the arena.** Lost Ark's "x160" bar counter with mechanics at fixed bar counts; Valtan destroying arena rings under a red decal; Hades' arm transforming at 50 %; TL2's Alchemist moving to a harsher arena each phase with a breather between.
5. **Let the boss interact with the horde, not just add to it.** Ordrak eats his adds to heal; Mordrox resummons only when few are left; Ormenos' falling ceiling kills his own sprites; Callagadra's immortal tornadoes are the real threat. Interactive add mechanics suit a survivors game better than "more chaff".
6. **Handle absurd builds with stopwatches, not immortality.** Grim Dawn's superbosses became time trials (25 s four-player Mogdrogen; AFK-kill challenges); TL3 had to raise boss HP 120 % after sub-30-second kills. Always play each phase opener even if damage overshoots, and offer player-chosen escalation (TL:I invitations, Tartarus' leave-the-orb gamble).
7. **Staggered arrivals beat simultaneous bosses.** Grim Dawn players argued that all-bosses-at-once "just amounts to some raw build check"; Crate made bosses wait until approached.
8. **Ritual and payoff are cheap and memorable:** summon-by-sacrifice (Ravager's form chosen by which NPC you sacrifice), click-to-burst loot orbs (Typhon), take-or-double reward orbs (Tartarus), per-boss signature trophies (TL2 "Eye of" gems), and a beat between death and drop (TL3 fix).
9. **Colour alone is not a telegraph.** Lost Ark's Tytalos was criticised because his wipe colour was shared with routine attacks and lacked a raid-wide sound; pair every lethal cue with a unique sound and silhouette.
10. **Tartarus (Titan Quest) is the closest existing analogue to an ember arena**: timed waves (7 min) of level-matched enemies under stacking curses, a boss every fifth battle, and a take-the-loot-or-escalate orb.


---

## Titan Quest (2006, Immortal Throne 2007, Anniversary Edition and later DLC)

Source wiki: Titan Quest Fandom (wikitext pulled through the MediaWiki API, `titanquest.fandom.com/api.php`). Pages: Boss, Typhon ~ Bane of the Gods, Typhon ~ Undead Titan, Hades ~ God of the Dead, Megalesios / Aktaios / Ormenos / Omega Telkine, Cerberus, Tartarus (arena and boss).

### Generic boss rules (the "boss contract")

The wiki's Boss page lists the global rules every TQ boss obeys ([Boss](https://titanquest.fandom.com/wiki/Boss)):

| Rule | Value |
|---|---|
| Resistance to % health reduction | 85–95 % by difficulty |
| Resistance to energy damage | 70–90 % |
| Resistance to energy/life leech | 80 % |
| Crowd control (slow, disruption, fear, conversion, confusion, sleep, immobilise, petrify, freeze, stun) | immune ("1000 % resistance") |
| Taunt resistance | only 50 % |
| Dodge | 10–30 % by difficulty |
| Vulnerable to | Fumble, Dispel |

The arena convention is also stated there: bosses "often reside on the other side of large, ornate doors, which frequently lock once the Hero enters the room", and they usually guard a Majestic Chest — the highest-value container in the game ([Boss](https://titanquest.fandom.com/wiki/Boss)). That gives TQ a very clear ritual: ornate door → seal → fight → essence orb or chest.

**Lesson:** a flat, published immunity contract (no CC, almost no %-HP damage) is how an ARPG stops the build's strongest *control* tools from trivialising a boss without having to hand-tune each one. The cost: control-centric builds feel useless at exactly the most important moment, which Survivor Unchained should avoid by converting CC into something (see synthesis).

### The Telkine (act-end sorcerers)

| Boss | Act | Signature mechanics (wiki) |
|---|---|---|
| Megalesios | I | Erects a barrier you cannot pass, animates **four guardian statues** while he destroys the Celestial Conduit; ranged vs close-range attack sets switch on distance; **mind-controls player pets** for 10–12 s; summons two Limos that leech life and **feed it to him** ([Megalesios](https://titanquest.fandom.com/wiki/Megalesios_~_Telkine)) |
| Aktaios | II | **Light of Ra**: sunlight rays that "always hit the same spots, making them easy to avoid" — ~400 dmg/tick on Normal with 60 % fire res, ~5,000/tick on Legendary at 0 %; **Mirage**: two lower-HP copies that only throw fireballs; Sandstorm (physical + skill disruption); summons two Tomb Guardians ([Aktaios](https://titanquest.fandom.com/wiki/Aktaios_~_Telkine)) |
| Ormenos | III | Stationary artillery; **drops the cavern ceiling**, then uses Telekinesis to throw the fallen rocks; summons 4 Magma Sprites which "can be killed by the rocks falling from the ceiling that Ormenos himself summons" ([Ormenos](https://titanquest.fandom.com/wiki/Ormenos_~_Telkine)) |
| Omega Telkine | Atlantis | Second form of Lyktos; stomp (stun/disrupt/slow), Chaotic Resonance (% health damage), summons ghost clones faster than Lyktos; wiki advice: "Attack the main body, not the clones… they are quickly respawned anyway" ([Omega Telkine](https://titanquest.fandom.com/wiki/Omega_Telkine)) |

Design notes:
- **Fixed-position hazards are a teaching tool.** Light of Ra is deadly on paper (5,000/tick) but readable because the rays always land in the same places; the wiki says simply "stay away from the centre of the chamber" ([Aktaios](https://titanquest.fandom.com/wiki/Aktaios_~_Telkine)).
- **The boss's hazards hurt its own adds** (Ormenos' falling ceiling kills his sprites). That is exactly the kind of interaction a horde game can lean on: a boss slam that also clears the horde opens breathing room and rewards baiting.
- **Healer adds create a priority puzzle** (Limos feeding Megalesios; "kill them instantly to prevent them filling up the Telkine's life").
- **Pet theft** is an early "your build can be turned against you" mechanic — temporary, with a leash: pets return if you move far enough away ([Megalesios](https://titanquest.fandom.com/wiki/Megalesios_~_Telkine)).
- The wiki notes Megalesios was "originally supposed to summon a ghost of himself upon dying. Maybe it was supposed to be a second phase" — evidence that TQ's early bosses were single-phase by budget, not intent.

### Typhon, Bane of the Gods (end of the original game)

- Arena: summit of Mount Olympus. In the original release, **four god statues** (Apollo, Demeter, Hades, Zeus) around the arena each granted Typhon a power set: Demeter gave a poison attack and a "gripping hand" paralyse; Hades gave a health drain that **fully healed him each use** and summoned abyssal liches; Zeus a lightning attack; Apollo a meteor shower ([Typhon](https://titanquest.fandom.com/wiki/Typhon_~_Bane_of_the_Gods)). In Immortal Throne "the statues are no longer active and instead Typhon now simply has all their previously granted abilities right from the beginning", and the drain became a slow regeneration rather than a full heal ([Typhon](https://titanquest.fandom.com/wiki/Typhon_~_Bane_of_the_Gods)).
- Abilities: Demeter's Poison Bolt (always followed by an Energy Drain), Energy Leech, Fire Breath, Life Leech, Meteor Shower, **Thorns** (reflects melee as bleed for a short window), Zeus Lightning.
- Help in the arena: shrines hidden under the temple roofs at the arena edge ("battle marker and/or a shrine of mastery") — the wiki calls them "your key to victory" ([Typhon](https://titanquest.fandom.com/wiki/Typhon_~_Bane_of_the_Gods)). So the arena itself carries both the threat (statues) and the comeback tool (shrines).
- Victory: a **"Typhon's Essence" orb appears and "explode[s] into a bunch of loot when you click on it"**, then Zeus delivers a speech and a portal appears ([Typhon](https://titanquest.fandom.com/wiki/Typhon_~_Bane_of_the_Gods)). The click-to-burst orb is a deliberate, player-triggered loot moment.
- Undead Typhon returns in Immortal Throne, erupting "from the ground as a huge skeleton when you enter the room"; his **Bone Spire** is a line attack doing physical + pierce + % current life, telegraphed by Typhon raising his hands; **Bone Trap Grenade** immobilises so he can combo into the Spire ([Typhon ~ Undead Titan](https://titanquest.fandom.com/wiki/Typhon_~_Undead_Titan)). The wiki: "You absolutely need to avoid the Bone Spire as it will kill you."

### Hades, God of the Dead (Immortal Throne final boss): three forms

| Phase | Trigger | Resist shift | Key attacks |
|---|---|---|---|
| 1 | start | phys 0/5/7 %, elements 25 %, vitality 20 % | **Shadow Star**: orb thrown at a hero *outside melee range*, splits into 8 bolts; "it certainly will one shot most characters" — 3,000 damage on Normal even with 80 % vitality res. Long, distinct wind-up: Hades raises his right hand |
| 2 | **½ life — his right arm transforms** | elements 35 %, vitality 30 % | Shadow Balls (6 orbs that bounce off walls), **Death Vortex** that follows the hero for 12 s |
| 3 | phase 2 "defeated" → turns into a **ghost** | 70 % *absorption* of physical/pierce/poison/bleed, **–20 % fire/cold/lightning**, immune to life leech | Shadow Stars ×5 thrown at random, Expanding Ring (stun), Uber Shadow Bolt ("likely to one shot everything"), Spirit Wave (% health reduction + decay) |

All from [Hades ~ God of the Dead](https://titanquest.fandom.com/wiki/Hades_~_God_of_the_Dead).

What transfers:
- **The visible body change is the phase announcement** (arm transforms at 50 %; ghost form after "death"). No UI is needed.
- **Resistance profile flips by phase** — physical builds that were fine in phase 1 hit 70 % absorption in phase 3, while elemental builds suddenly find –20 %. This is a mild "test a different axis" move; it punishes mono-builds. In a draft-your-weapons game it would be read as unfair unless signposted (e.g. the ghost visibly shrugging off blades).
- **Ranged-punishing one-shot**: Shadow Star specifically targets heroes *outside* melee range — a mechanic that counter-programmes kiting, the dominant ARPG habit.
- Hades' drop: 10 % chance of The Overlord on Normal (unlocks the Secret Passage easter egg) ([Hades ~ God of the Dead](https://titanquest.fandom.com/wiki/Hades_~_God_of_the_Dead)).

### Cerberus: a floor-crack safe-spot puzzle

- **Poison Cracks**: green fire erupts from cracks in the floor for 4.8 s; "possible to avoid this attack by simply standing between the crevices (zooming out helps identifying safe spots)"; Cerberus **raises his head** first. Damage: up to 1,360 / 2,376 / 3,192 poison per second (Normal/Epic/Legendary) at 0 % res ([Cerberus](https://titanquest.fandom.com/wiki/Cerberus_~_Warden_of_Hades)).
- Combined with Poison Puddle (a lobbed ball that leaves a large pool) this produces a positional puzzle: the safe ground shrinks.
- The arena geometry *is* the telegraph — cracks are painted into the floor permanently, so the player can pre-plan.
- Note the wiki's comment: "% less damage from Beasts" does not reduce the cracks or puddles — environment damage is classed separately, so a defensive build cannot erase the mechanic.

### Tartarus: TQ's wave-arena boss (closest analogue to an ember arena)

From the Tartarus arena and boss pages ([Tartarus location](https://titanquest.fandom.com/wiki/Tartarus), [Tartarus ~ Lord of the Abyss](https://titanquest.fandom.com/wiki/Tartarus_~_Lord_of_the_Abyss)):

- Each battle is a wave of random enemies from all acts, **all at the player's exact level**, that must be killed within a **time limit (starting from 7 minutes)**.
- Each battle applies a curse: enemy buffs (bigger/smaller, spawn ghosts/traps/insects on death, explosive missiles, leech…) and player maluses (reduced resistances, slower spells, weaker companions).
- **Every 5th battle is Tartarus himself**, under the same modifiers, in a large circular arena with adds. He is always at the player's level, so "grinding to catch up is useless".
- Telegraphed kit: Sea of Fire (shield slam → fire domes at random spots), Ice Meteors (roar → falling shards that *leave spiky ice behind*; meteors near the wall are intercepted by it), Lightning Wave (frontal sheet, used more if you stay away), **Teleport** (stomps, vanishes in a red circle, appears *on top of the player* in a matching circle), Draining pillar (only dangerous close), **Blood Pool** (raises arms, kneels → homing expanding pool), Summon Golem.
- **Press-your-luck reward**: defeat leaves an essence orb, "Gift of Tartarus". Loot it, or leave it untouched to make the next 5 battles harder — leaving it **doubles the chance of a Unique drop each time** ([Tartarus ~ Lord of the Abyss](https://titanquest.fandom.com/wiki/Tartarus_~_Lord_of_the_Abyss)). A 2019 patch "Added some random enemies to Tartarus boss arena" ([Titan Quest Update 2.8, Steam](https://store.steampowered.com/news/app/475150/view/3364670677176283921)).

**Direct relevance:** a level-matched boss at the end of a timed wave sequence, under stacking modifiers, with a "take it now or double down" reward, is almost exactly Survivor Unchained's 30:00 boss + endless-after-win structure.

---

## Torchlight I, II, III and Infinite

Wiki: Torchlight Fandom (`torchlight.fandom.com`, wikitext via API); Torchlight III Steam patch notes; TLIDB (tlidb.com) for Infinite data.

### Torchlight (2009)

- **Ordrak** (final boss, floor 35, "The Lair"): summons Dragonkin and Enslaved throughout; "a few moments after summoning creatures, Ordrak will kill all the creatures he summons, absorbing their lifeforce and restoring his own health" ([Ordrak](https://torchlight.fandom.com/wiki/Ordrak)). Armour and all resistances listed at 140 %; 100 % knock-back resistance. **This is the single most relevant horde-interaction mechanic in this strand**: adds are a timed heal for the boss, so the player must kill adds before the "harvest". In a survivors game the equivalent is a boss that periodically devours the horde around it — which the player's clear speed directly counters.
- **The Sisters** (Lady Marishka et al.), floor 6: a trio of spectral bosses; Marishka summons zombies and casts fire, 5 health stolen on hit ([Lady Marishka](https://torchlight.fandom.com/wiki/Lady_Marishka)).

### Torchlight II (2012)

| Boss | Mechanic worth stealing | Source |
|---|---|---|
| **General Grell** (Act I) | Slow, lumbering; **cannon arm pointed at you = cannonball, ~0.5 s to sidestep; cannon pointed at the ceiling = falling rocks around Grell, ~1 s to leave the radius**. The wiki says the adds spawning "along the sides of the arena" are "more troublesome than Grell himself" | [General Grell](https://torchlight.fandom.com/wiki/General_Grell) |
| **Mordrox** (Act I) | Emerges from a huge pit (the wiki calls it a "Grand Entrance"); summons skeletons and pyromancers, vomits Blightslugs. **"Mordox only summons more skeletons once there are only a few left, so players can try to prevent the next summon phase by leaving a few minions alive"** | [Mordrox](https://torchlight.fandom.com/wiki/Mordrox) |
| **Wraith Lord** | Conjures a different spectral weapon per attack (axe/mace swing, spear thrust at range, hammer slam creating fissures) — weapon shape *is* the telegraph; raises 3 random skeletons; teleports away after being hit several times | [Wraith Lord](https://torchlight.fandom.com/wiki/Wraith_Lord) |
| **Bloatfang** (Act III) | Rush, vomit, leap smash, boulder toss, **consumes corpses**; hidden path to a Claptrap easter egg behind the boss chest | [Bloatfang](https://torchlight.fandom.com/wiki/Bloatfang) |
| **The Alchemist** (Act IV) | 3 phases, "each phase will have a brief intermission, allowing players to regain health, cooldowns"; **each phase moves to a different fighting ground**: small plain area → small area with fire-grate traps → large area with traps and 2 dwarf statues | [The Dark Alchemist](https://torchlight.fandom.com/wiki/The_Dark_Alchemist) |
| **Netherlord** (final) | Phase 1 shadow form ("fairly easy"); phase 2 "significantly larger… His health greatly increases". On death: drops items, **boss chest**, portal to surface, unlocks Mapworks and New Game Plus | [Netherlord](https://torchlight.fandom.com/wiki/Netherlord) |

Standard TL2 boss resist block (e.g. Wraith Lord, Grell, Bloatfang): 85 % slow resistance, 100 % charm, 92 % stun, 100 % interrupt, 100 % knock-back (95 % Bloatfang), 88 % immobilise, 100 % flee/silence, 75 % teleport, 90 % pull, 90 % blind ([Wraith Lord](https://torchlight.fandom.com/wiki/Wraith_Lord); [General Grell](https://torchlight.fandom.com/wiki/General_Grell)). Note these are *high but not total* (e.g. 92 % stun) — CC still occasionally lands, which keeps CC builds feeling alive, unlike TQ's flat immunity.

Loot: each named TL2 boss has a 15 % chance to drop a unique socketable "Eye of [Boss]" (Eye of Mordrox, Eye of Grell, Eye of the Wraith Lord, Eye of Bloatfang) ([Mordrox](https://torchlight.fandom.com/wiki/Mordrox), [General Grell](https://torchlight.fandom.com/wiki/General_Grell)). A per-boss signature trophy is a cheap, memorable reward pattern.

### Torchlight III (2020): what the patch notes say went wrong

Torchlight III's Early Access patch notes are an unusually frank record of boss tuning against player builds:

- **Bosses dying too fast**: "Boss Health increased to a baseline of 70 (up from 32), +120% from prior. This is mostly as a reaction to Tyler's recent non-act boss videos which shows those like Kronch dying in sub-30 seconds on multiple characters and builds, and on Hard mode. A big swing is warranted." Named non-act bosses went 70 → 100; Brall and Sadista 100 → 140; Ordrak stayed at 200 ([TL3 EA patch, 13 June 2020](https://store.steampowered.com/news/app/1030210/view/3309530667984015598)).
- **Phase thresholds**: "Brall's phase changes now happen a little earlier, with her final phase beginning at 50% HP"; Brall's illusions now spawn at *Brall's current health percentage* rather than full; her Nether Well Arrow cooldown 10 s → 5 s and its hazards last 20 s instead of 10 s (same source).
- **Difficulty as a damage multiplier on bosses**: player damage vs bosses was set to 80 % / 60 % / 35 % on Hard / Painful / Ridiculous ([State of the Game Week 10](https://store.steampowered.com/news/app/1030210/view/3670950880878954376)); later "Reduced the amount of damage that bosses take from players on Ridiculous from 70% to 50% and on Painful from 80% to 60% to make bosses feel like more of a proper challenge" ([Mainline Patch 11 Aug 2020 pt 4](https://store.steampowered.com/news/app/1030210/view/3667572003477325221)).
- **Adds by HP threshold**: "Set all the mapworks minibosses to trigger monster spawns as adds on spawn and at 50% health" (same 11 Aug note).
- **Removed boss kill celebrations for Sadista, Brall, and Odrak** (same note) — the source does not say why.
- **Arena tooling**: "Pulled out the camera further in the Brall boss battle"; "Shuffled around some hub boss encounters so that larger bosses have more space to maneuver"; "Removed two coils near Shriekbeak spawn so that players are not immediately killed" ([11 Aug pt 3](https://store.steampowered.com/news/app/1030210/view/3667572003477324882); [13 June](https://store.steampowered.com/news/app/1030210/view/3309530667984015598)). Shriekbeak's phases are driven by coils at the arena edge that "send a beam to Shriekbeak when he switches to a new phase", and the coils' visual state did not always match their gameplay state until fixed ([6 Oct 2020 pt 2](https://store.steampowered.com/news/app/1030210/view/3807188575867855901)).
- **Telegraph honesty**: "Hazard radius for Rising Strike slightly reduced (intentionally smaller than visual suggests)"; Netherim Herald's "longer, well-telegraphed teleport slam" deals 200 % damage while its fast claw deals 75 % — damage explicitly scaled to telegraph length (6 Oct 2020 pt 2, same URL).
- **One-shots**: "Players are reporting hazards in some areas are producing one-hit kills… without warning. We are reviewing and adjusting" ([Week 10](https://store.steampowered.com/news/app/1030210/view/3670950880878954376)); in the endgame dungeon "You should now be able to make it to the end on Ridiculous without normal monsters one-shotting you. Champions and bosses, on the other hand? No guarantees." ([6 Oct pt 2](https://store.steampowered.com/news/app/1030210/view/3807188575867855901)).
- Loot timing: "Items fall and announcements are no longer made too quickly after killing monsters, especially bosses" ([30 June 2020 pt 2](https://store.steampowered.com/news/app/1030210/view/3444639924512703424)) — i.e. the drop needs a beat after the death.
- Relic skills disabled "while in the 'lobby' leading up to the boss arenas" ([11 Aug pt 4](https://store.steampowered.com/news/app/1030210/view/3667572003477325221)) — a pre-boss lobby is a standard TL3 pattern.

**Lessons:** (1) "damage dealt to bosses" multipliers by difficulty are the cheapest lever and were TL3's main one; (2) HP-threshold adds, threshold phase changes and illusions that inherit current HP; (3) make hazard hitboxes *smaller* than the visual; (4) give the long telegraph the big number; (5) let loot land a beat after the death.

(Torchlight: Infinite section below.)

---

## Grim Dawn (2016, Crucible DLC 2016, Ashes of Malmouth 2017, Forgotten Gods 2019, Fangs of Asterkarn 2026)

Sources: Grim Dawn Fandom wiki (via API), Crate Entertainment forums (Discourse JSON), Crate patch notes, Steam news. The Fandom pages for the superbosses are stubs; most mechanical detail comes from the forums and Crate's own patch notes. The grimtools.com monster database and the Japanese wiki (wikiwiki.jp/gdcrate) were Cloudflare-blocked, so HP numbers below are from players quoting them.

### The three "Celestial" superbosses

All three are optional, summoned on purpose, and sit far above the campaign's difficulty: they are the build check of the game.

| Boss | How it starts | What it does | Numbers found |
|---|---|---|---|
| **Avatar of Mogdrogen** (Asterkarn Valley) | Complete the Rhowari Legacy quest, then **talk to him and launch the fight** | Summons three beasts (Briarthorn Terror, Frosthide Chilltusk, Boneback); Lightning Shield, Lightning Storm, Lightning Bolt Volley, Lightning Strike | Appears at **minimum level 71 even on Normal**; 85 % all resistances; 500 % freeze/knockdown/petrify/sleep/stun/trap resistance ([Avatar of Mogdrogen](https://grimdawn.fandom.com/wiki/Avatar_of_Mogdrogen)). ~18 million HP on Ultimate single-player, ~28 million with the 4-player HP bonus (player-reported, 2017) ([Crate forum](https://forums.crateentertainment.com/t/1-0-0-9-worlds-fastest-ultimate-avatar-of-mogdrogen-kill-4-players-fevered-rage-25-seconds/38463)) |
| **The Ravager** (Barrowholm) | You choose which NPC to **sacrifice** in the quest Cast Off the Flesh; that choice sets his form (Flesh, Minds or Souls). Fight begins through dialogue | Common kit: stacking "frenzy swipes" that raise his crit/speed and apply resist reduction per stack; Howl (AoE, 10 % life damage, resist reduction, regen reduction); Necrotic Orb (15 % life damage); **Enrage at 50 % health** — damage absorption, damage increase, total speed increase ([Ravager summary, 2017](https://forums.crateentertainment.com/t/spoiler-ravager-summary/41986)). Minds: summons totems that **nullify you for 5 s** and "can summon a lot of them over time, so you have to think about where you stand"; Souls: pools with 100 % fumble and 70 % damage reduction on you. All forms: a normal swipe and a sundering swipe, "usually used after 4-5 regular swipes", and "two sundering homing projectiles if you get too far away" ([forum, 2024](https://forums.crateentertainment.com/t/looking-for-pointers-to-superbosses/137339)) | Always drops Ravager's Gaze (Dreadgaze on Ultimate), whose look and resist bonus depends on the form killed; respawns each session so it can be farmed ([The Ravager (BOSS)](https://grimdawn.fandom.com/wiki/The_Ravager_(BOSS))) |
| **Callagadra, Scion of the Sands** (Korvan Sands, Forgotten Gods) | Place a rare **Celestial Essence** on a sacrificial altar ([wiki](https://grimdawn.fandom.com/wiki/Callagadra,_Scion_of_the_Sands); [Celestial Essence](https://grimdawn.fandom.com/wiki/Celestial_Essence)) | Mostly physical/pierce plus bleed. "She summons immortal 'minions', in the form of tornadoes and shifting sands, those are frankly more dangerous overall, if they stack up on you"; –14 % physical resist from tornadoes; 470 DA debuff; fumble/impaired aim up to 50 %; "Her Sunder is on the 'wing flap' and can be dodged really easily… you also have to watch your debuff bar, fighting her when you are standing in the shifting (glittering) sands is usually not a good idea" ([forum, 2024](https://forums.crateentertainment.com/t/looking-for-pointers-to-superbosses/137339)) | Level 86 Normal / 112 Elite (wiki). A player reported "her tornado basically oneshots me… 11-12k health"; another pointed to a **cast-on-spawn self buff of +500 health/s, +3000 % health regeneration and +50 % total speed** listed on grimtools ([Callagadra fight mechanics, 2019](https://forums.crateentertainment.com/t/callagadra-fight-mechanics/85810)) |

Player view of these fights:
- **They are build checks first and mechanics checks second.** A 2022 player: "I was staring at the 'scythe' status and my health bar the whole time, AFKed more than I was fighting… the second phase was crazy especially with the life drain… Now I'm absolutely clueless about how to fight callagadra. Potions don't help when you are getting two shot" ([Endgame is unintuitive](https://forums.crateentertainment.com/t/endgame-is-unintuitive/113414)). Replies are about gear numbers ("you need something like 180'ish pierce/bleed resist"), not dodging.
- An early Ravager thread: "Im not sure theres much avoidance involved. Face tank is the only way. Or bug him out using screen full of pets" ([Ravager summary](https://forums.crateentertainment.com/t/spoiler-ravager-summary/41986)).
- After the 1.2 Sunder change (below) the advice shifted toward reading a single wind-up: "avoid their sunder… When Calla swings her wings, that's her sunder… usually when u learn their movements it becomes way easier to beat" ([forum, 2025](https://forums.crateentertainment.com/t/some-one-help-for-my-build-to-defeat-callagadra-on-ultimate/148147)); "you must dodge the Sunder. If you do and still just die in one hit, you're probably heavily lacking in Health or DA" ([Help with Ravager, 2026](https://forums.crateentertainment.com/t/help-with-ravager-superboss/151711)).
- The ceiling of player power: a 4-player party killed Ultimate Mogdrogen (with the Fevered Rage buff) in **~25 seconds**; "Funny to see his HP bar vanishing in seconds" ([forum](https://forums.crateentertainment.com/t/1-0-0-9-worlds-fastest-ultimate-avatar-of-mogdrogen-kill-4-players-fevered-rage-25-seconds/38463)). Solo build threads advertise kill times in the 1–2 minute range for all three (e.g. "Ravager of Flesh 1m 08s, Callagadra 1m 19s, Mogdrogen 1min 25s" in a 2024 build title, [forum](https://forums.crateentertainment.com/t/1-2-1-6-sledgehammer-edition-2h-warborn-cadence-warlord-ravager-of-flesh-1m-08s-callagadra-1m-19s-mogdrogen-1min-25s-no-mi-no-doping-sr-35-all-3-superboss-killer/136163)); there is even a community challenge for the fastest **AFK** Callagadra kill ([forum](https://forums.crateentertainment.com/t/build-challenge-fastest-afk-callagadra-kill/147835)). The superbosses have become a benchmark/time-trial — a role the 30:00 ember boss could also play in endless mode.
- Bosses that are only HP and stats invite cheese: one Mogdrogen-era exploit was dragging bosses into town to let guards tank, which Crate fixed ([Callagadra fight mechanics](https://forums.crateentertainment.com/t/callagadra-fight-mechanics/85810)); Ravager could be "bugged out" with pets until a 2019 fix ("It's an exploit not a function… should no longer be possible come next patch", [Ravager made easy](https://forums.crateentertainment.com/t/ravager-made-easy-tactics-vids/51349)).

### Crate's 1.2.0.0 boss reform (Nov 2023): the "Sunder" mechanic

Crate's patch notes for v1.2.0.0 are the clearest developer statement in this strand of how to make ARPG bosses read better ([Grim Dawn v1.2.0.0 notes](https://forums.crateentertainment.com/t/grim-dawn-version-v1-2-0-0-v1-2-0-1-v1-2-0-2-v1-2-0-3-hotfixes/132117)):

- "A new Monster mechanic has been added: **Sundered**. Many bosses can now Sunder your defenses, causing you to take X% additional damage for Y seconds. Multiple instances of Sundered do not stack, only the strongest effect is active."
- "Many Monster special attacks, particularly those that apply Sunder, have had their **animation speeds reduced**."
- "Many Monster special attacks, particularly melee and breath attacks, now **stop tracking the player's movement past a certain point**, making it easier to evade those attacks."
- "Monsters with charge abilities are now slower when charging and have a finite pursue range."
- "**Monster abilities no longer apply % Resist Reduction and flat Resist Reduction.** Unique monster debuffs that reduced resists continue to do so."
- "Stun, Freeze, and Petrify effects have been removed from most standard (non-hero/boss) monster abilities" — CC on the player is reserved for bosses and heroes.
- "Reflected debuff effects (ex. Sunder…) are now applied at up to 30% intensity."
- "The most dangerous hero archetypes now have more prominent visuals to distinguish their presence."
- Bosses: low-level boss health increased; "All Bosses now have a 100% chance to drop their (non-legendary) Monster Infrequents."

In design terms Crate converted invisible, always-on attrition (resist shred on every hit) into **one readable, dodgeable, slow wind-up that marks you as vulnerable**, and stopped late tracking so the dodge is honest. That is the central lesson of this strand for a top-down horde game.

### The Crucible: wave arena with bosses

From the wiki ([The Crucible](https://grimdawn.fandom.com/wiki/The_Crucible)) and patch notes:

- Three difficulties (Aspirant, Challenger, Gladiator) of 150 waves (170 with Ashes of Malmouth; Fangs of Asterkarn adds 30 more, i.e. up to 200, [Steam](https://store.steampowered.com/news/app/219990/view/1839041357026796)). Ten selectable arenas with "different layouts and defensive positions".
- **Every 10 waves** the player chooses to cash out into the Treasure Chamber or push on. Death ends the run.
- **Tributes** (currency every 10 waves) buy **Celestial Blessings** (12 Tributes each, 25-minute buffs, lost on death): e.g. Blessing of Ulo (33 % CC resist, 25 % all-damage resist), Empyrion's Guidance (+80 % health), Might of Amatok (all damage +26 %, +75 OA). This is effectively the Crucible's "great blessing" — the closest analogue to Survivor Unchained's start and 15:00 blessings.
- **Defences**: placeable beacons (Deathchill, Inferno, Stormcaller) and banners (Stonewall: health/DA/regen; Vanguard: damage/OA/frenzy), each upgradeable twice.
- **Mutators** start at wave 31 and re-roll every 10 waves: 1 at 31, 2 at 61, 3 at 91, 4 at 111, 5 at 131. In 1.2.0.0, "All mutators no longer have negative effects… Positive player mutators are now always rolled for the 2nd and 5th mutators" ([1.2.0.0 notes](https://forums.crateentertainment.com/t/grim-dawn-version-v1-2-0-0-v1-2-0-1-v1-2-0-2-v1-2-0-3-hotfixes/132117)).
- **Bonus timer**: resets each wave; clearing before it expires adds +1 to the score multiplier (max 10) but shortens the next timer. "**Defeating a Hero, Boss or Nemesis monster will add several seconds to the current bonus timer**" ([The Crucible](https://grimdawn.fandom.com/wiki/The_Crucible)). Bosses are thus both a threat and a time refund.
- 1.2.0.0 Crucible tuning: "Reduced the number of non-boss monsters spawned"; "Monster % Heal effects are now reduced"; "Spawn areas no longer grant a movement speed buff to monsters"; nullification re-enabled at reduced duration except "Loxmere Nightmage's nullification remains disabled as it is an **instant effect that cannot be dodged**" (same source). Boss health increases explicitly do not apply to the Crucible.
- When wave 170 is beaten the doors open and Lokarr says "You've chosen to end your suffering. Understandable…" before the treasure room (secondary: [forum](https://forums.crateentertainment.com/t/1-3-0-7-crucible-automatically-stops-after-beating-170/158742)).

Player complaints about bosses inside a horde (Crucible waves 181–200, Oct 2026 PTR thread, [forum](https://forums.crateentertainment.com/t/reducing-oneshots-in-crucible181-200-would-be-nice/160644)):
- "When it's a **big telegraph ability that's meant for you to avoid it, that's fine**. But more often than not it's a combination of random or just over the top factors that are hard or impossible to avoid."
- On a boss's explosion when it dies: "Considering our mission is to kill stuff I don't think getting punished for killing stuff, especially this severely, is a good inclusion"; "the blast hits like screen-distance and sometimes even though a wall."
- "The time between first projectiles hit me and unavoidable wave that leads to death is 1.3 sec."
- "Purple Tempest Spawn's dispell rock that comes with no warning every 8 seconds."
- Counterpoint from a veteran: "Anasteria spawn is deterministic and can be played around, that's a definition of skill issue. Ixall and Sriek sadly aren't." — players accept danger they can predict.
- "If Crucible [is] to remain this dangerous rewards should be adequate."

### Shattered Realm and multi-boss rooms

The Shattered Realm alternates three combat shards with a boss room that often contains several bosses at once. A 2019 player poll on making all bosses in a room aggro at once ([forum](https://forums.crateentertainment.com/t/make-enemies-in-sr-boss-stages-aggro-all-at-once/50544)) captured the trade-off well:
- Against: "it just amounts to some raw build check. You have enough defenses to not insta-die, or you don't, and it over-emphasize building defensively"; "You tank or you die just simple things."
- A proposed middle ground: "make them spawn in three waves with 10-15 seconds intervals. That way, offensive builds can take on waves one by one… and defensive builds can… take the full spawn on."
- Crate then shipped in 1.1.9.0: "Bosses now do not engage until you get closer" and "It is now possible to avoid pulling all bosses in a Shattered Guardian's Domain without resorting to camera exploits" ([v1.1.9.0 notes](https://forums.crateentertainment.com/t/grim-dawn-version-1-1-9-0/106945)).

**Lesson for a horde boss:** staggering elite/boss arrivals lets glass-cannon builds win by killing fast and tanky builds win by surviving, instead of the fight collapsing into a single defence check.

### Grim Dawn takeaways
1. Optional superbosses work as a long-term benchmark, but when their danger is invisible stat attrition, players experience them as gear checks and AFK them.
2. A single named, slow, dodgeable "big hit" (Sunder) with a visible vulnerability debuff fixed much of that.
3. Bosses that summon *immortal* hazard-adds (Callagadra's tornadoes and sands) are more dangerous than the boss itself — fine if the adds are visually distinct (glittering sand) and readable.
4. In a horde, the deadly moments are coincidences (death explosion + projectile + wave). Avoid on-death blasts that punish killing; keep instant undodgeable effects out of horde modes, as Crate did with Loxmere.
5. Kill-the-boss-to-buy-time (Crucible bonus timer) is a neat interaction between boss and clock.

---

## Lost Ark (Smilegate RPG; West 2022, Amazon Games)

Lost Ark is the most important reference in this strand: it is an isometric ARPG whose whole endgame is boss fights, and it built an explicit, shared vocabulary of boss interactions that players learn once and reuse. Sources: the official Guardian Raid guide, Maxroll and Fextralife guides, Steam discussions (fetched directly), and Mein-MMO's report of a developer livestream. Reddit was not reachable from this environment.

### The shared vocabulary (applies to every boss)

| System | What the player sees | What it does | Source |
|---|---|---|---|
| **Segmented HP bar** | The boss bar shows a bar count, e.g. "x160", ticking down | Long fights read as a countdown; every mechanic is keyed to a bar count (see Valtan) | [Maxroll Valtan G2](https://maxroll.gg/lost-ark/legion-raids/valtan-phase-2) |
| **Stagger meter** | "the purple bar below the HP of the boss" | "Once the purple Stagger bar hits 0, the boss is incapacitated for a few seconds"; on Guardians "each stagger phase grants a stackable debuff to the Guardian that permanently increases the damage they take" | [Maxroll general raid guide](https://maxroll.gg/lost-ark/resources/general-raid-guide) |
| **Stagger check** | Boss channels; often a shield must be broken first | A short window to deal enough stagger, or the channel resolves (often a wipe). "Destroy the shield with your normal skills first", then "use your skills with high Stagger Damage to interrupt the boss" | [Maxroll Valtan G2](https://maxroll.gg/lost-ark/legion-raids/valtan-phase-2) |
| **Counter attack** | "Some bosses glow blue for a brief moment before they use a charge attack pattern" | A skill tagged "Counter: Yes" landed in the window interrupts the attack and staggers the boss; "you must stand in front of the boss" | [Maxroll general](https://maxroll.gg/lost-ark/resources/general-raid-guide); [Mein-MMO](https://mein-mmo.de/en/lost-ark-how-to-counter-attacks-from-bosses,787486) |
| **Destruction / weak point** | Breakable armour and parts | "Weak Points helps to destroy armor or cut parts of the boss"; Destruction Bombs carry the Weak Point affix | [Maxroll general](https://maxroll.gg/lost-ark/resources/general-raid-guide) |
| **Battle items** | Four slots: bombs, grenades, potions, utility | "Players will be unable to use normal items within a Raid instance and are instead limited to using Battle Items… one type of item from the Bombs, Grenades, Potions and Utility categories" | [Fextralife](https://lostark.wiki.fextralife.com/Guardian+Raids) |
| **Telegraph colours** | Blue = counterable; red areas = dodge; yellow areas = displacement (secondary) | Blue marking on the body or ground signals a counter, distinct from red AoE zones | [Mein-MMO](https://mein-mmo.de/en/lost-ark-how-to-counter-attacks-from-bosses,787486); yellow = displacement only seen in a search summary (secondary) |

The design point: **stagger, counter and destruction turn the player's damage into verbs.** Instead of "deal X damage", the boss asks "deal *this kind* of damage *now*". Builds are tagged with which verbs they bring (stagger value, counter, weak-point level), so build variety maps onto role variety. In a survivors game the equivalent is tagging drafted weapons with properties like *stagger* or *break* and letting the boss expose a bar that only those properties fill.

### Guardian raids (4-player hunt bosses)

- **20-minute time limit**: "Failing to slay a Guardian within the time limit will result in a wipe and failed attempt" ([Fextralife](https://lostark.wiki.fextralife.com/Guardian+Raids); [official guide](https://playlostark.com/en-us/game/guide/guardian-raid-guide)).
- **Shared revives**: "By default, each party is limited to 3 respawns per run. These respawns are shared between all party members" ([Fextralife](https://lostark.wiki.fextralife.com/Guardian+Raids)); Maxroll notes this was later made unlimited ("as of March 11, 2026 is unlimited", [Maxroll general](https://maxroll.gg/lost-ark/resources/general-raid-guide)).
- **Scaling**: "the Guardian Raid's Health and Destruction/Stagger requirements scale depending on how many participants are in instance when you enter" ([official guide](https://playlostark.com/en-us/game/guide/guardian-raid-guide)).
- **Fleeing**: "Guardians appear randomly in their designated habitat and may move to new locations. Flare battle items can help you find them" (official); "Certain Guardians have escape mechanics designed to make players waste time" (Fextralife).
- **Enrage**: Guardians that "glow orange" are in an enraged state that raises attack power and adds effects (secondary — search summary of PCGamesN).

Player opinion on Guardians (Steam, Feb 2022):
- On **Tytalos**: "the red color he's supposed to get for a wipe is applied to most abilities so its hard to tell which 'sucking sand is bad' moment… imagine if someone had any sort of color blindness? Wheres the OBVIOUS RAID WIDE SOUND EFFECT TO GIVE PEOPLE A WARNING?" Another player: "He literally has one 'gathering energy from all around while crouched' move and he uses it exclusively 2-4 attacks after earthquake stomp. It's trivial to avoid" ([Steam thread](https://steamcommunity.com/app/1599340/discussions/0/3185737486654198230/)). The lesson: a wipe telegraph that shares its colour with ordinary attacks fails; the defender's point is that a *fixed sequence position* (2–4 attacks after the stomp) is itself a telegraph.
- On shared revives: "im so tired of some random guy dying 3 times over the span of 2 minutes and wasting everyones time… why revives dont count towards individuals themselves, i will never understand" ([Steam](https://steamcommunity.com/app/1599340/discussions/0/3185737486662933738/)).

### Legion raids: Valtan as the worked example

**Valtan Gate 1** (Dark Mountain Predator) — mechanics by HP bar ([Maxroll G1](https://maxroll.gg/lost-ark/legion-raids/valtan-phase-1)):

| Bar | Event |
|---|---|
| x40 | Blue Wolf "Invader" joins; a Golden Orb buff marks a player; the two wolves must be separated and split between groups |
| x30 | **Orb phase**: "Orbs will spawn around the boss with a stagger bar"; players collect orbs in alternating colour order, then stagger the boss |
| x25 | Red Wolf Invader joins (bleed stacks; at 3 stacks a line slash) |
| x15 | Orb phase again |

Telegraphs listed include blue bombs (freeze, projectile spray, expanding circles), a purple Fear that targets the furthest player and must be staggered, a slash combo that leaves lines on the ground, and red/purple tornado variants.

**Valtan Gate 2** (the Legion Commander) ([Maxroll G2](https://maxroll.gg/lost-ark/legion-raids/valtan-phase-2)):

| Bar | Mechanic | Failure |
|---|---|---|
| x160 | **Armour break**: bait Valtan into charging 4 towers; each destroyed tower drops 2 blue orbs; break 2 armour layers with Corrosive and Destruction bombs | Harder fight |
| x130 | **Wipe pattern**: "2 axe strikes towards the ground. The 2nd strike can one shot players"; survive with the orbs from the towers (or a Sidereal skill), then stagger | Deaths/wipe — the earlier tower phase *is* the counter |
| x110 | **Pillar hug**: four pillars; a "huge yellow zone and a small cone-shaped red zone" that "locks on to a random player and follows his movements" | High damage |
| x85 | **Stage break**: Valtan leaps; a "red telegraph indicated the part which will be destroyed" — the outer left or right ring of the arena falls away; then pillars and a roar that "deals high damage to everyone who is not standing behind a pillar" | Fall = death |
| x65 | **Counter**: stomp → delayed explosion under each player → charge/grab; "use your skills with Counter Attack affix on the 3rd second" | He charges "multiple times in a row and grab[s] everyone in his path to follow up with a 1 shot skill" |
| x35 | Stage break again: the remaining outer ring is destroyed | — |
| x17–15 | **Ghost transition**: "Almost any hit can push you off the arena and kill you immediately"; group on the left side | Fall = death |
| ghost | Ghost phase: 4 armour stacks (6 on Hard) removed only by countering Ghost Clone attacks | Clone's Cross attack pushes players off |

Other telegraphs on the list: "faint flowing line" for a portal charge path, "cracks on ground" warning of a pull follow-up, "lightning effect on axe" for an enhanced strike. A three-strike counter sequence assigns one player per strike; a failed last one "can even wipe the entire raid".

What Valtan demonstrates for a top-down camera:
1. **Mechanics keyed to visible HP milestones** let players anticipate; experienced players call phases by bar count.
2. **The arena is destroyed in stages** (x85, x35) with a red decal showing exactly what will fall; the remaining space shrinks and ledges make knock-back lethal. That is "arena change as phase marker" done cleanly.
3. **Earlier mechanics produce the tools for later ones** (towers → orbs → survive the axe). The fight has internal causality, which is what players remember.
4. **Every verb appears**: stagger (orb phase), counter (x65, ghost), destruction (armour layers), positioning (pillars), items (bombs).

### Difficulty arc and player reaction

- Smilegate's developers said at the November 2022 anniversary livestream that **Brelshaza** (6 gates) drew harsh criticism in Korea and Russia as too hard, that **Akkan was "intentionally designed to be significantly less punishing"**, "emphasizes individual player skill over excessive team coordination" and "forgives more mistakes" — while the next raid (Thaemine) would still be very hard ([Mein-MMO](https://mein-mmo.de/lost-ark-legion-raid-hart/)).
- Kakul-Saydon's final phase is a literal board game: a **5×5 grid**; "every 30-40 seconds, a bomb appears above a player's head", falls on their square after ~5 s and flips tiles in a "+" pattern; the party must complete a row ("Bingo") to break Saydon's channel, which deals "x13 HP bars of damage" each time. A hammer pattern shows "red indicators on which row/column they will hit. They one shot" ([Maxroll Kakul-Saydon G3](https://maxroll.gg/lost-ark/legion-raids/kakul-saydon-gate-3)). This is the purest "safe-spot puzzle" in ARPGs.
- Steam players, against wipes: "Having the entire raid insta-wipe because of the mis-click or mistake of one person is asinine… because person A didn't touch an orb or stand in a circle" ([Steam](https://steamcommunity.com/app/1599340/discussions/0/3185738755289030160/)); "too many 1 shot mechanics… the one shot mechanics need to be removed. or at the very least rare special attacks only should 1 shot" ([Steam](https://steamcommunity.com/app/1599340/discussions/0/3185738120275014076/)); "i have no energy left to keep learning how to fight stuff… i don't care about doing homework" ([Steam, 2023](https://steamcommunity.com/app/1599340/discussions/0/3806156352190272903/)).
- For: "Abyss Dungeons are incredible and well designed… a superb experience" (same 2022 thread as above); "Mechanics aren't hard… All you need is to move like it's a clock and absorb orbs, stand between pillar and the boss and stagger mechanics." A 2024 player proposal: "Easy Mode = no Raid Wipes but independent wipe mechanics; Normal Mode = maybe 1 Raid Wipe; Hard Mode = as intended… i think Valtan was where Difficulty was good, not too hard not too easy" ([Steam, 2024](https://steamcommunity.com/app/1599340/discussions/0/4635985982183733641/)).

**Lost Ark takeaways for a solo survivors boss:** keep the verbs (stagger bar, counter window, breakable parts) and the HP-milestone phases; keep arena destruction with exact decals; drop group-wipe logic entirely (there is no group) and make "one-shots" rare, named, and taught. The "individual wipe mechanic" idea (fail = you die, not the run) maps onto a run-based game as "fail = large chunk of HP or a lost blessing", not instant death.

### Torchlight: Infinite (XD, 2022–): seasonal bosses

Data here is thinner: TLIDB (a fan database built from beta data) and the official Steam announcements.

- **Seasonal pinnacle bosses with player-chosen difficulty.** Season 2 (Blacksail): kill the stage boss → a "Void Sea Seal" appears → collect Void Sea Invitations → challenge the Lord of the Void Sea. "The difficulty level of the Lord of the Void Sea differs according to the number of Void Sea Invitations the Hunter places in the Void Sea Seal" ([Steam, Jan 2023](https://store.steampowered.com/news/app/1974050/view/5035620840526482422)). The developers later called him "the most difficult challenge of the game" ([Dev Blog #27](https://store.steampowered.com/news/app/1974050/view/5059268543374702007)). Season 1 (Dark Surge) used the same ladder: infected map bosses → a Familiar → Dark Surge Edicts → "the season boss of two varying difficulties" ([TLIDB Dark Surge](https://tlidb.com/en/Dark_Surge_Season)). Clockwork Ballet added the Silverwing Danseuse ([Steam](https://store.steampowered.com/news/app/1974050/view/5842939267324371194)).
- **Roaming bosses inside the horde.** The Hunter's Odyssey pre-season put "2 Star of Calamity bosses" in every map "that are constantly eyeing the Hunters… extremely powerful", with modifiers that can double their number or make them "replicate once", and a chance to drop the exclusive items of the seasonal bosses ([Steam](https://store.steampowered.com/news/app/1974050/view/5229301621578037278); [event](https://store.steampowered.com/news/app/1974050/view/5229301621578037271)). This is the nearest ARPG analogue to a survivors-style elite that hunts you through the swarm.
- **Timers.** The 2026 Afterlight season adds a tower where you "climb ever-higher floors against a tense three-minute timer, defeat floor bosses" ([Steam](https://store.steampowered.com/news/app/1974050/view/1838407329258272)). A new player describing the campaign's Ordrak: "First health bar/fight I do no problem. Didn't notice the timer until it was super low and next thing I know I get one shot… now every time I try to revive and enter his chamber again it immediately kills me" ([Steam, 2024](https://steamcommunity.com/app/1974050/discussions/0/4634860616374302186/)) — a hard enrage that a first-timer did not notice is a failure of signposting, not of difficulty.
- TLIDB lists the S1 boss Ordrak with flags "Immune to Knockback, Stun, Freeze", "Unlimited activation range", "**Hide Life Bar**", "Attack and Cast Speed cannot be reduced to below the base value" and "Movement Speed cannot be reduced to below the base value" ([TLIDB Ordrak](https://tlidb.com/en/Ordrak)) — i.e. slows are allowed but floored at base speed, a softer version of a CC immunity.
- Racing as endgame: competition servers rank players by time to kill the Realm Lords / the Traveler ([Steam](https://store.steampowered.com/news/app/1974050/view/5519792046244021463)).

---

## Elden Ring and Souls: lessons that survive the move to a top-down camera

Only the transferable parts. Source: Elden Ring wiki.gg (API) and a Steam discussion.

### Stance (posture) as a hidden stagger bar
- Every enemy has hidden poise: "15 to 65 for normal enemies and 80 to 120 for bosses"; poise damage is independent of damage dealt and heavier attacks do more. Poise regenerates at 13/s after a delay of base poise ÷ 13 seconds (≈9.2 s for a 120-poise boss). At zero the enemy is "stance broken… stunned for a significant amount of time" and exposes a critical-hit riposte, which resets poise ([Poise, wiki.gg](https://eldenring.wiki.gg/wiki/Poise)).
- Outliers are authored, not formula: Radahn has 200 poise (15.4 s regen delay); Night's Cavalry takes only 20 % poise damage; Ancient Dragons take 20 % except 80 % on headshots (same source). **Weak points are expressed as poise multipliers.**
- Transfer: Lost Ark shows the bar; Elden Ring hides it. For a horde game where the player cannot watch a boss closely, show it (Lost Ark style) — and make the regen delay explicit so sustained pressure from auto-weapons, not one big hit, is what breaks the boss. That rewards fast-firing builds with a payoff moment that slow, high-damage builds get anyway.

### Delayed attacks and input-reading
- A Dec 2022 Steam thread ("Elden Ring bosses have flawed battle design…") complains of "delayed unnatural attacks that are designed to make you panic roll into them (ex. Margit charging his cane for what feels like more than 5 seconds)" and "the absence of openings and attack windows (Morgott, Beast Clergyman, Maliketh, Godfrey…)"; another poster: the bosses "don't account for the player's abilities/speed, which is why the input reading feels even more egregious". Defenders reply that the telegraphs are fine and Elden Ring "punishes you, rightfully" for roll-spamming ([Steam](https://steamcommunity.com/app/1245620/discussions/0/3729575504108842499/)).
- Transfer: from isometric distance the player reads silhouettes and decals, not fine animation. A *delayed* hit only works top-down if the delay itself is visible (a filling decal or a charge meter), otherwise it reads as randomness. Delays are good for breaking rhythm against autopilot movement in a survivors game — but only if the "release" frame is unambiguous.

### Signature one-shot-adjacent moves with an always-available answer
- Malenia's **Waterfowl Dance**: "Leaps into the air and hovers for a period, before performing… four bursts of slashes, homing in on the player with each burst… very difficult to dodge at close proximity, but it is possible to roll through the attacks or run away" ([Malenia, wiki.gg](https://eldenring.wiki.gg/wiki/Malenia,_Blade_of_Miquella)).
- **Scarlet Aeonia** opens phase 2 every time and "can be avoided from any range by sprinting sideways until the flower blooms"; phase 2 starts at 80 % of her health (same source).
- Malenia heals on hit; "she staggers easily, and her attacks can be cancelled by attacking during her wind-up animations. Frostbite and Blood Loss are especially good for staggering her" — the boss has a designed weakness for specific build properties.
- Transfer: a named signature move, scripted at a fixed moment (phase start), with a universal positional answer (move sideways / get out of the circle), is learnable even from a top-down camera. It becomes the "story" players tell about the boss.

### Arena gimmicks and allies
- **Starscourge Radahn**: a huge open battlefield with NPC summon signs placed around it — "Six can be summoned at a time… each NPC has multiple summon signs" — and a phase 2 at <50 % HP where he vanishes into the sky and returns as a meteor: "After several seconds, he hurtles back down from above, causing a devastating explosion upon impact" ([Starscourge Radahn, wiki.gg](https://eldenring.wiki.gg/wiki/Starscourge_Radahn)). Phase 1 includes arrow volleys that rain "in a line which homes in on the player" and a roar that "pulls the player and any summoned allies towards him".
- Transfer: Radahn is the closest Souls fight to a horde setting — a big arena, many bodies on the field, a boss that targets allies too, and a sky-drop that only works because the arena is large enough to run from it. The meteor reads top-down as a growing shadow decal.

---

## What makes boss mechanics work from a top-down camera

Synthesis across Titan Quest, Torchlight, Grim Dawn, Lost Ark, Torchlight: Infinite and the Souls notes above, with the companion strands (Diablo, PoE/LE, survivors games) in mind.

### 1. Ground decals and colour language
- **One colour, one meaning, everywhere.** Lost Ark's blue = counterable is learnt once and reused for every boss ([Maxroll](https://maxroll.gg/lost-ark/resources/general-raid-guide)). The Tytalos complaint shows the failure mode: when the "wipe" colour also appears on routine attacks, players cannot pick out the one that matters, and colour-blind players are excluded ([Steam](https://steamcommunity.com/app/1599340/discussions/0/3185737486654198230/)). Pair every lethal telegraph with a unique *sound* as well as a colour.
- **Telegraphs should be honest or generous, never stingy.** Torchlight III deliberately made a hazard radius "intentionally smaller than visual suggests" ([TL3 patch](https://store.steampowered.com/news/app/1030210/view/3807188575867855901)); Grim Dawn made attacks "stop tracking the player's movement past a certain point" ([GD 1.2.0.0](https://forums.crateentertainment.com/t/grim-dawn-version-v1-2-0-0-v1-2-0-1-v1-2-0-2-v1-2-0-3-hotfixes/132117)).
- **Scale damage with telegraph length.** TL3's Netherim Herald: fast claw 75 %, "longer, well-telegraphed teleport slam" 200 % (TL3 patch above). Grim Dawn slowed the animations of its Sunder attacks. Big number ⇒ long, unmistakable wind-up.
- In a horde game, boss decals must sit on a render layer above both the swarm and the player's own effects, and the player's auto-weapon VFX should dim inside a boss decal or during a lethal wind-up (cf. the survivors strands).

### 2. Arena geometry and staged arena change
- Fixed hazards are teachable: Aktaios's sunbeams always land in the same spots; Cerberus's poison cracks are painted on the floor permanently, so "standing between the crevices" is a plan you can make in advance ([Aktaios](https://titanquest.fandom.com/wiki/Aktaios_~_Telkine); [Cerberus](https://titanquest.fandom.com/wiki/Cerberus_~_Warden_of_Hades)).
- Arena destruction as phase marker: Valtan destroys one outer ring at x85 bars and the other at x35, with a red decal on the part that will fall ([Maxroll](https://maxroll.gg/lost-ark/legion-raids/valtan-phase-2)). TL2's Alchemist moves to a new, more trapped arena each phase, with a breather between ([The Dark Alchemist](https://torchlight.fandom.com/wiki/The_Dark_Alchemist)).
- The arena can hold both threat and remedy: Typhon's god statues power him while shrines at the edge help you ([Typhon](https://titanquest.fandom.com/wiki/Typhon_~_Bane_of_the_Gods)); Valtan's towers give the orbs that let you survive his axe.
- Camera and space are part of the fight: TL3 "Pulled out the camera further in the Brall boss battle" and moved bosses so "larger bosses have more space to maneuver" ([TL3 patches](https://store.steampowered.com/news/app/1030210/view/3667572003477324882)). Cerberus' wiki tip is "zooming out helps identifying safe spots". For a 30:00 boss in an open arena, a slight zoom-out on boss arrival is cheap and effective.

### 3. Safe-spot puzzles
- Ranges from trivial to elaborate: Cerberus cracks (stand between lines), Valtan pillar-hug (stand behind a pillar against the roar), Kakul-Saydon bingo (5×5 grid; complete a row to break the channel; hammers with red row/column indicators one-shot) ([Maxroll Kakul G3](https://maxroll.gg/lost-ark/legion-raids/kakul-saydon-gate-3)).
- In a horde game, the "safe spot" can be made *by the player*: a boss slam that clears enemies (Ormenos' falling rocks kill his own sprites), or a pillar the horde cannot path through.

### 4. Phase transitions
- **Visible body change** is the best announcement: Hades' arm transforms at 50 %, he becomes a ghost after "death" ([Hades](https://titanquest.fandom.com/wiki/Hades_~_God_of_the_Dead)); TL2's Netherlord goes from shadow form to "significantly larger" ([Netherlord](https://torchlight.fandom.com/wiki/Netherlord)).
- **Thresholds keyed to HP**, ideally HP shown as segments (Lost Ark's "x160" bar count). TL3 moved Brall's last phase to 50 % and made her illusions spawn at *her current HP %* instead of full ([TL3 EA patch](https://store.steampowered.com/news/app/1030210/view/3309530667984015598)).
- **Open each phase with a signature move**: Malenia's phase 2 always opens with Scarlet Aeonia ([wiki.gg](https://eldenring.wiki.gg/wiki/Malenia,_Blade_of_Miquella)); Valtan's x130 axe. A fixed opener is a free lesson.
- **Resistance or rule flips per phase** (Hades' ghost takes 70 % less physical but –20 % elemental) test a different axis; signpost them visually.
- **Breathers**: the Alchemist's intermissions "allowing players to regain health, cooldowns"; TL2/TQ bosses do not chain phases without a beat.

### 5. Minion mechanics: how the boss uses the horde
| Pattern | Example | Counter-play |
|---|---|---|
| Boss consumes adds to heal | Ordrak kills his summons and absorbs their life ([Ordrak](https://torchlight.fandom.com/wiki/Ordrak)); Bloatfang consumes corpses | Kill adds before the harvest; clear speed matters |
| Healer adds | Megalesios' Limos leech life to him | Priority targeting |
| Summon on low count | Mordrox only resummons "once there are only a few left" — players leave a few alive ([Mordrox](https://torchlight.fandom.com/wiki/Mordrox)) | Manipulate the trigger |
| Adds at HP thresholds | TL3 minibosses "trigger monster spawns as adds on spawn and at 50% health" ([TL3](https://store.steampowered.com/news/app/1030210/view/3667572003477325221)) | Burst through thresholds |
| Immortal hazard adds | Callagadra's tornadoes and glittering sands ([forum](https://forums.crateentertainment.com/t/looking-for-pointers-to-superbosses/137339)) | Positioning, not killing |
| Clones/illusions | Aktaios' Mirage, Omega Telkine ghosts, Brall's illusions | Track the real one; illusions share HP % |
| Adds from the arena edge | General Grell: side spawns are "more troublesome than Grell himself" ([Grell](https://torchlight.fandom.com/wiki/General_Grell)) | — |
| Boss hazards hurt adds | Ormenos' ceiling kills his own sprites | Bait the boss's AoE into the crowd |
| Pet/minion theft | Megalesios converts player pets for 10–12 s | Leash by distance |

For Survivor Unchained the horde already exists, so the strongest options are the *interactive* ones: the boss eats the horde to heal (so clearing denies it), the boss's slams carve paths through the horde, adds carry a resource the player needs (Valtan's orbs, TQ shrines), and the boss calls named elites at HP thresholds rather than adding more chaff.

### 6. Damage checks versus mechanic checks
- **Pure stat checks get AFKed or cheesed.** Grim Dawn's superbosses were for years discussed as gear thresholds ("you need something like 180'ish pierce/bleed resist"), and the community now races AFK kills ([forum](https://forums.crateentertainment.com/t/endgame-is-unintuitive/113414); [AFK challenge](https://forums.crateentertainment.com/t/build-challenge-fastest-afk-callagadra-kill/147835)). Crate's fix was a mechanic check: the dodgeable Sunder.
- **Pure mechanic checks with group wipes alienate**; Smilegate itself pulled back after Brelshaza ([Mein-MMO](https://mein-mmo.de/lost-ark-legion-raid-hart/)).
- **The good middle**: Lost Ark's stagger check is a damage check of a *specific kind* in a *specific window*; Valtan's x130 axe is a mechanic check whose answer comes from an earlier damage task (break towers). TQ's Tartarus is a level-matched DPS race under modifiers with a clear time limit.
- **Hard enrage**: Lost Ark Guardians fail at 20 minutes ([Fextralife](https://lostark.wiki.fextralife.com/Guardian+Raids)); TQ's Tartarus waves start at 7 minutes; TL:I Ordrak's timer killed a player who never noticed it ([Steam](https://steamcommunity.com/app/1974050/discussions/0/4634860616374302186/)). If there is an enrage, make the timer loud.

### 7. Handling weak-to-absurd builds
- **Global immunity contracts**: TQ bosses are immune to CC and 85–95 % resistant to %-HP damage ([Boss](https://titanquest.fandom.com/wiki/Boss)); TL2 uses high-but-not-total CC resists (92 % stun, 85 % slow); TL:I floors slows at base speed ([TLIDB](https://tlidb.com/en/Ordrak)). The softer the contract, the more CC builds still matter.
- **Boss damage-taken multipliers by difficulty**: TL3 set player damage vs bosses to 80/60/35 % on Hard/Painful/Ridiculous, then tuned to 60/50 ([Week 10](https://store.steampowered.com/news/app/1030210/view/3670950880878954376); [11 Aug](https://store.steampowered.com/news/app/1030210/view/3667572003477325221)).
- **HP buffs when bosses melt**: TL3 raised boss baseline health 32 → 70 after videos showed bosses "dying in sub-30 seconds on multiple characters and builds" ([TL3 EA patch](https://store.steampowered.com/news/app/1030210/view/3309530667984015598)).
- **Phases that resolve even if you skip their HP**: Valtan-style mechanics keyed to HP bars mean a very strong build simply sees mechanics in quicker succession; TL3 illusions inherit current HP %. Design rule: a phase transition should *always play* (its opener move) even if the damage overshoots the threshold, so strong builds still see the content.
- **Player-chosen difficulty for the pinnacle**: TL:I's invitation count ([Steam](https://store.steampowered.com/news/app/1974050/view/5035620840526482422)); Grim Dawn's Ultimate/Veteran tiers; TQ's Tartarus orb that you can leave untouched to make the next five waves harder for doubled unique chance ([Tartarus](https://titanquest.fandom.com/wiki/Tartarus_~_Lord_of_the_Abyss)). This maps neatly onto "endless play after the win".
- **Time-trial ceiling**: Grim Dawn kill-time culture (25 s four-player Mogdrogen; 1–2 min solo) shows that absurdly strong builds want a stopwatch, not an immortal boss.
- **Staggered arrivals** (GD forum proposal: bosses in "three waves with 10-15 seconds intervals") let offence-heavy builds win by speed and defence-heavy builds win by endurance ([forum](https://forums.crateentertainment.com/t/make-enemies-in-sr-boss-stages-aggro-all-at-once/50544)).

### 8. One-shots and how they are telegraphed
- Players accept one-shots that are **rare, named, telegraphed and positional** (Valtan's x130 axe, Kakul's hammers with red row indicators, Hades' Shadow Star with a long raised-hand wind-up, Undead Typhon's Bone Spire with raised hands). They reject one-shots that are **coincidences**: Crucible deaths in "1.3 sec" from overlapping effects, an on-death blast that "hits like screen-distance", a dispel "with no warning every 8 seconds" ([Crucible thread](https://forums.crateentertainment.com/t/reducing-oneshots-in-crucible181-200-would-be-nice/160644)); TL3's "hazards… producing one-hit kills… without warning" ([TL3](https://store.steampowered.com/news/app/1030210/view/3670950880878954376)). Lost Ark players' compromise: "rare special attacks only should 1 shot" ([Steam](https://steamcommunity.com/app/1599340/discussions/0/3185738120275014076/)).
- In a horde, do not let the boss's lethal attack coincide with uncontrolled swarm damage: either pause/clear the swarm during the wind-up, or make the lethal move a *sundering* debuff (GD style) rather than raw damage.
- Remove instant undodgeable effects from horde modes entirely (Crate kept Loxmere's instant nullify disabled in the Crucible for that reason).
- Do not punish killing: on-death explosions in a crowd were the most resented Crucible mechanic.

### 9. Entrance rituals
- Summon-by-choice gives ownership: Grim Dawn's Celestial Essence on an altar, the Ravager form picked by **which NPC you sacrifice**, Mogdrogen started by talking to him ([wiki](https://grimdawn.fandom.com/wiki/The_Ravager_(BOSS))). TL:I's invitations placed in a seal.
- Physical arrival: Mordrox "emerging from a huge pit"; Undead Typhon "erupts from the ground as a huge skeleton when you enter the room"; TQ's ornate doors that lock behind you.
- Lobbies: TL3 has pre-boss lobbies (relic skills disabled in them) and intro cinematics (Sadista) ([TL3](https://store.steampowered.com/news/app/1030210/view/3667572003477325221)).
- For the 30:00 ember boss: the clock itself is the ritual; add a 2–3 s arrival beat (horde recoils/dies, ground decal of the landing, unique sting) and lock the camera zoom.

### 10. Loot and the victory moment
- **Click-to-burst loot orbs**: TQ's Typhon's Essence explodes into loot when clicked; Tartarus' Gift orb can be taken or left to double the next prize ([Typhon](https://titanquest.fandom.com/wiki/Typhon_~_Bane_of_the_Gods); [Tartarus](https://titanquest.fandom.com/wiki/Tartarus_~_Lord_of_the_Abyss)). The pause lets the player savour the kill and, in Tartarus' case, decide whether to keep going — exactly the choice an endless-after-win mode needs.
- **Boss chests and trophies**: TL2 boss chests and per-boss 15 % "Eye of [Boss]" uniques; Ravager's guaranteed Gaze that changes look with the form you chose; Grim Dawn 1.2 made bosses always drop their Monster Infrequent.
- **Give the drop a beat**: TL3 fixed loot and announcements that came "too quickly after killing monsters, especially bosses" ([TL3](https://store.steampowered.com/news/app/1030210/view/3444639924512703424)).
- **Celebration is a design choice**: TL3 removed boss kill celebrations for three bosses (reason not stated) — evidence that a celebration which interrupts flow can be worse than none.
- **Narrative payoff**: Zeus' speech and portal after Typhon; TL2's Netherlord death unlocks Mapworks and New Game Plus; Lokarr's line when the Crucible ends.

### 11. Stagger bars: the one system worth stealing outright
Lost Ark's purple stagger bar under the HP bar, emptied by a build property, rewarding a few seconds of free damage and (on Guardians) a permanent stacking damage-taken debuff ([Maxroll](https://maxroll.gg/lost-ark/resources/general-raid-guide)), combined with Elden Ring's poise regen delay (≈ base ÷ 13 s), gives a survivors game a way to make *how* a build deals damage matter against a boss, to create spectacle moments (boss collapses mid-horde), and to give weak builds a catch-up lever (a stagger-focused draft) without raising their raw DPS.

---

## Gaps and caveats

- No HP figures found for Callagadra, the Ravager forms, Typhon, Hades or the Lost Ark bosses (Lost Ark shows bar counts, not raw HP). Mogdrogen's ~18 M / ~28 M HP is a 2017 player figure.
- grimtools.com (monster database) and wikiwiki.jp were Cloudflare-blocked; Callagadra's regen buff numbers are as quoted by a forum player from grimtools.
- Reddit was unreachable; Lost Ark and Elden Ring opinion comes from Steam discussions only. No Smilegate primary-source interview was retrieved; the developer statement is via Mein-MMO's livestream report.
- Lost Ark telegraph colour meanings beyond blue = counter (e.g. yellow = displacement, orange = Guardian enrage) are secondary.
- Torchlight: Infinite seasonal boss mechanics (Lord of the Void Sea, Silverwing Danseuse, Tidemaster) were not found in detail; TLIDB stat blocks are from beta data.
- Why Torchlight III removed three boss kill celebrations is not stated in the patch notes.
- Titan Quest Telkine and Torchlight 1 HP numbers not found.

---

## Verification

Adversarial check (2026-10-03). Each cited source was re-opened: Crate forum and Maxroll pages via fetch; Fandom pages via the MediaWiki API; Torchlight III and Grim Dawn Steam posts via the Steam news API (full text).

| # | Claim | Verdict | Notes / correction |
|---|---|---|---|
| 1 | GD 1.2.0.0 Sundered (non-stacking X% for Y s), Sunder animations slowed, attacks stop tracking past a point, monster abilities no longer apply %/flat resist reduction | Confirmed | All four quotes are verbatim in the notes ([source](https://forums.crateentertainment.com/t/grim-dawn-version-v1-2-0-0-v1-2-0-1-v1-2-0-2-v1-2-0-3-hotfixes/132117)). Unique monster resist debuffs still apply. |
| 2 | Crucible: Hero/Boss/Nemesis kills add several seconds to the bonus timer; mutators start at wave 31 and rise to 5 by wave 131; Blessings cost 12 Tributes and last 25 min | Partly right | The wiki supports all of it ([wiki](https://grimdawn.fandom.com/wiki/The_Crucible)). But the 1.2.0.0 notes say "Waves 150-170 now have 6 mutators as a positive player mutator is now always rolled for the 5th mutator", so the post-1.2 maximum is 6, not 5 ([1.2.0.0](https://forums.crateentertainment.com/t/grim-dawn-version-v1-2-0-0-v1-2-0-1-v1-2-0-2-v1-2-0-3-hotfixes/132117)). |
| 3 | Ultimate Mogdrogen has ~18 M HP solo and ~28 M with 4 players; a 4-player party killed him in ~25 s | Confirmed (player-reported, v1.0.0.9 / 2017) | The post also gives combined DPS of about 1.12 M/s, which fits 28 M in 25 s ([forum](https://forums.crateentertainment.com/t/1-0-0-9-worlds-fastest-ultimate-avatar-of-mogdrogen-kill-4-players-fevered-rage-25-seconds/38463)). Later boss-health patches may have changed the numbers. |
| 4 | Valtan G2 at x160 (armour/towers), x130 (two axes, 2nd can one-shot), x85 and x35 (outer rings, red telegraph), x65 (counter on the 3rd second) | Confirmed | ([Maxroll](https://maxroll.gg/lost-ark/legion-raids/valtan-phase-2)) |
| 5 | Purple stagger bar; boss incapacitated a few seconds at 0; Guardian stagger adds a stacking permanent damage-taken debuff; blue glow before counterable charge | Confirmed | ([Maxroll](https://maxroll.gg/lost-ark/resources/general-raid-guide)) |
| 6 | Guardian raids: 20-min limit (fail = wipe), 3 shared respawns by default | Outdated (respawn half) | The 20-minute limit is confirmed. Maxroll now says the resurrection limit "as of March 11, 2026 is unlimited" ([Maxroll](https://maxroll.gg/lost-ark/resources/general-raid-guide)). The Fextralife "3 respawns" is the old rule; the notes already flag this in the Guardian section. |
| 7 | Kakul-Saydon Bingo: 5x5 grid, a bomb every 30-40 s, lands after ~5 s, + pattern, a completed row breaks the channel for x13 bars | Confirmed | "After 5 seconds, the bomb icon … disappears. A bomb will fall shortly after"; the channel comes every 3rd bomb ([Maxroll](https://maxroll.gg/lost-ark/legion-raids/kakul-saydon-gate-3)). |
| 8 | TL3 boss baseline HP 32 to 70 (+120%) after sub-30 s kill videos; Brall's final phase at 50%; illusions now spawn at Brall's current HP % | Partly right | The HP and phase lines are verbatim. The illusion line is a **bug fix**, not a design change: "Fixed an issue where Brall's illusions sometimes would spawn at full health instead of Brall's health percentage" ([13 June 2020](https://store.steampowered.com/news/app/1030210/view/3309530667984015598)). Inheriting current HP % was always the intended behaviour. |
| 9 | TL3 bosses take less damage on Ridiculous (70% to 50%) and Painful (80% to 60%); mapworks minibosses spawn adds on spawn and at 50%; kill celebrations removed for Sadista, Brall, Odrak | Confirmed | All verbatim ([11 Aug 2020 pt 4](https://store.steampowered.com/news/app/1030210/view/3667572003477325221)). The same note also first cut Ridiculous boss damage from 75% to 70%. |
| 10 | TQ bosses immune to CC, 85-95% resistant to % health reduction, only 50% taunt resistance | Confirmed | ([wiki](https://titanquest.fandom.com/wiki/Boss)) |
| 11 | Hades: arm transforms at 1/2 life; ghost form has 70% physical absorption and -20% fire/cold/lightning; Shadow Star deals 3,000 on Normal at 80% vitality res | Confirmed | ([wiki](https://titanquest.fandom.com/wiki/Hades_~_God_of_the_Dead)). Minor: in phase 3 each Shadow Star splits into 5 bolts, not 8. |
| 12 | Tartarus: timed battles from 7 min, level-matched, curses, boss every 5th battle; leaving the orb makes the next 5 harder and doubles Unique chance | Confirmed | The 7-min and level-matched details come from the [Tartarus location page](https://titanquest.fandom.com/wiki/Tartarus), the orb detail from the [boss page](https://titanquest.fandom.com/wiki/Tartarus_~_Lord_of_the_Abyss). |
| 13 | TL1 Ordrak kills his summons and absorbs their lifeforce to heal | Confirmed | Wording is "a few moments after summoning" rather than "periodically" ([wiki](https://torchlight.fandom.com/wiki/Ordrak)). |
| 14 | Elden Ring boss poise 80-120 (Radahn 200); regen 13/s after a delay of base/13 s; at zero, stance break and critical | Confirmed (per source) | ([wiki.gg](https://eldenring.wiki.gg/wiki/Poise)) |

Other claims spot-checked:
- GD 1.2.0.0 Crucible lines (fewer non-boss spawns, reduced % heals, no spawn-area speed buff, Loxmere nullify kept disabled, boss-HP buff not applied to the Crucible, "All mutators no longer have negative effects") are **confirmed** verbatim.
- Fangs of Asterkarn "thirty additional waves" for the Crucible is **confirmed** ([Steam](https://store.steampowered.com/news/app/219990/view/1839041357026796)).
- TL3 Week 10 player damage vs bosses of 80/60/35% on Hard/Painful/Ridiculous is **confirmed** ([Steam](https://store.steampowered.com/news/app/1030210/view/3670950880878954376)).
- TL3 named-boss HP exceptions are **confirmed** (non-act 70 to 100; Brall/Sadista 100 to 140; Ordrak stays 200).
