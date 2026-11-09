# The Nights We Hold: siege gameplay (the owner's design, 8 November 2026)

**Status: DESIGN ONLY, not built.** The owner wrote this with ChatGPT and pasted it on 8 November with: "I will paste an idea I want for sieges that will happen once an act or something that sound very fun - but we don't need to build on that yet, just keep it in mind in design decisions." Every lead reads it for what it implies about the systems they build now (`docs/design/ARPG_DIRECTION.md` lists those implications). Nothing here is scheduled.

**Where it sits in the game:** a siege is the climax of an act (roughly one per act). The player is their normal ARPG character with their usual weapons, skills, gear and build; there is no separate strategy interface or combat system.

## 1. The fundamental mechanic

A siege is a large-scale ARPG battle across several interconnected city districts. The objective is to keep the city from falling until dawn.

The player gains three additional battlefield systems, and can use any mix of them or largely ignore them and rely on their own combat:

- **Troop commands:** rally and direct groups of soldiers.
- **Fortifications:** build, repair and activate defenses.
- **Battlefield objectives:** respond to breaches, eliminate commanders, rescue defenders, protect critical locations.

The siege must be beatable through several different approaches.

## 2. The battlefield: five interconnected districts

| District | Strategic role | If it falls |
|---|---|---|
| North Gate | primary defensive position | undead enter the northern streets |
| East Gate | secondary approach | enemies flank the market |
| Market Square | central crossroads | undead gain access to the inner districts |
| Chapel District | sanctuary and support | healing and civilian support are disrupted |
| The Keep | final defensive position | losing the keep ends the siege |

Each district has several defensible positions, environmental weapons and routes to its neighbors. The player moves freely between districts during the siege.

Districts do not have health bars. They have physical defensive positions enemies attack and destroy: gates, barricades, towers, rally points, occupied buildings. A district falls when its key positions are overrun and its defenders can no longer hold it; the enemy then advances through it into adjacent districts.

Districts can be retaken. A player might deliberately abandon the North Gate, let enemies into a prepared kill zone, then counterattack to reclaim the gatehouse. The city is an evolving battlefield, not a static arena.

## 3. The preparation phase

Before the siege the player receives a limited number of **Preparation Points** (workers, materials, time). Prototype: 10 points.

| Preparation | Cost | Effect |
|---|---|---|
| Reinforce a gate | 3 | the gate withstands significantly more damage |
| Build a barricade | 2 | blocks or redirects enemies |
| Position a ballista | 3 | heavy damage against lines of enemies and siege monsters |
| Prepare burning oil | 2 | an area-denial trap |
| Recruit militia | 2 | a squad of basic defenders |
| Deploy veteran guards | 3 | a stronger squad with better survivability |
| Establish a rally point | 1 | soldiers regroup and recover morale there |

Defenses go at predetermined, strategically meaningful locations (no freeform construction), so the city is designed around satisfying chokepoints. The player cannot afford everything: heavy fortification means fewer soldiers, a large army means fewer defenses, and a personal-combat player can invest in neither. Preparation takes two to four minutes, with the option to launch at once.

## 4. Troop commands

Troops are squads of six to twelve with a captain, a role and a morale value. Squad types: **shield guards** (hold chokepoints, protect others), **archers** (walls and elevated positions), **pikemen** (counter large monsters and charges), **Ember Watch veterans** (elite, limited ember abilities).

Commands through a quick radial menu, under a second to issue, with a target or location marked directly in the world. No individual soldier selection; squads attack, defend and follow basic rules on their own.

| Command | Effect |
|---|---|
| Rally | nearby soldiers move to the player and gain temporary morale |
| Hold | the squad defends its current position |
| Charge | the squad attacks a targeted enemy or location |
| Focus | ranged units prioritize a marked enemy |
| Retreat | the squad falls back to its rally point |

Example: an undead brute approaches the gate; the player targets it and activates Focus; nearby archers concentrate fire while the player engages it in melee.

**Morale is the main tactical resource.** Soldiers lose it when surrounded, when their captain dies, or when nearby allies are overwhelmed. Low morale means retreat or weaker fighting. The player's presence, kills and Rally restore it, so fighting alongside your troops is valuable.

## 5. Fortifications and siege weapons

Interactive, powerful, easy to understand; each with a clear tactical purpose. Not a tower-defense game: tools that complement normal combat.

- **Barricades:** at designated street entrances; redirect movement into chokepoints; undead attack them when there is no other route; the player can repair one mid-fight, exposed while doing it.
- **Ballistae:** mounted, operated automatically by soldiers or manually by the player; a heavy bolt penetrates lines and devastates siege monsters; manual aim can hit weak points.
- **Burning oil:** prepared above gates or along streets; activated at a mechanism or by striking an ignition point with an ember attack; a temporary area of intense damage.
- **Crushing gates:** heavy portcullises or collapsible structures, triggered at the right moment to crush groups or split an attacking army.
- **Ember beacons:** attract nearby undead; let the player pull monsters toward fortified positions or away from weak districts.

## 6. The siege director

Not identical waves at fixed intervals: the director manages **assault groups**, each with an objective, a composition and a route, introduced by siege phase.

- Group A, North Gate: 80 basic undead, 12 armored, 2 siege brutes; objective: destroy the North Gate.
- Group B, East Wall: 40 fast undead, 8 climbers, 1 Grave-Caller; objective: a foothold behind the defenders.
- Group C, Chapel: 25 undead, 1 elite hunter; objective: eliminate the chapel defenders.

It may adjust pressure when the player dominates or struggles, but it never secretly negates good preparation: a well-designed defense genuinely makes the battle easier. Its purpose is interesting situations, not punishing success.

## 7. The player's battlefield role

The player is the most powerful individual combatant; their job is the problems soldiers cannot solve. A siege brute at the North Gate can be: killed personally; pinned by pikemen under archer focus; lured into a ballista lane; or let through into a fortified chokepoint. All four work.

**The core principle: every major threat has multiple solutions, and the player's ARPG build decides which feel best.**

## 8. The battle timeline (prototype: about 20 minutes)

1. **The Approach (3 min):** scouts and small groups; intercept, activate defenses, reposition; the first assault begins.
2. **The Assault (6 min):** several gates under attack; move between threats or trust defenses and troops; siege monsters appear.
3. **The Breach (6 min):** a major enemy champion; extreme pressure on one or more positions; the battle spills into the streets; abandon, reinforce or retake districts.
4. **The Final Stand (5 min):** peak pressure; the defenders rally; hold until the dawn timer expires. At dawn the assault collapses.

Timing and counts tuned in playtesting; a later story siege can run longer with more mechanics.

## 9. Heroic Momentum

Built by impactful actions: elite kills, saving soldiers, defending a gate, destroying a siege monster, retaking a district, powerful combinations. A full meter unlocks a major battlefield ability by specialization:

- **Champion, Ember Ascendant:** a short window of extraordinary offense against formations.
- **Commander, For the Living!:** nearby squads recover morale, gain bonuses and counterattack together.
- **Warden, Rain of Fire:** the prepared defensive weapons fire a coordinated barrage on a chosen area.

Spectacular, earned by participation, memorable turning points.

## 10. Victory, defeat, consequences

- **Major victory:** most districts intact; substantial rewards, recognition, possibly unique gear.
- **Costly victory:** the city survives but districts fell; siege rewards, and the damaged city changes future quests, services and rebuilding.
- **Defeat:** the keep falls before dawn; the player, an Ember Walker, returns; the story continues in a devastated city with objectives of survival, recovery and reclaiming ground. A lost siege never erases hours of progress.

## 11. Builds in a siege

The siege uses the existing ARPG progression; no siege character. Sword-and-shield holds chokepoints and counters big threats; dual daggers hunt commanders and answer distant threats fast; the heavy axe tears formations and siege monsters; the staff gives area attacks and control; the crossbow picks priority targets from walls and rooftops. **No build ever needs troop or fortification investment to be viable;** those systems are alternative ways to win, never mandatory upgrades.

## 12. The spectacle: three layers of simulation

1. **Immediate combat:** fully interactive enemies near the player, the normal ARPG combat.
2. **Distant battlefield:** simplified formations of soldiers and undead along walls, streets and far positions.
3. **Background spectacle:** large animated armies, flaming projectiles, collapsing structures, distant explosions, scripted events.

As the player approaches a distant fight, its enemies become fully interactive. Thousands of combatants in appearance, never thousands simulated. Immediate combat stays readable, responsive and satisfying.

## A concrete example: the North Gate

Prepared with one ballista, two shield squads and a burning-oil trap. Eighty undead approach; archers fire on their own. The player jumps from the battlements into the front of the horde. A siege brute appears behind them; the player marks it for focus and keeps fighting through the crowd. The brute reaches the gate; the player falls back, lights the oil, and dozens burn. The brute survives. The player mounts the ballista and staggers it with a bolt to the chest. A Grave-Caller beyond the walls starts raising the fallen. The player chooses: finish the brute, or leave the defenders to hold and hunt the Grave-Caller. They hunt. The brute breaks the gate. On return, the shield squads are retreating into the market. The player rallies them, activates Ember Ascendant, charges the breach. The brute falls; the defenders retake the gatehouse. The eastern bell rings. The siege continues.

## The central design principle

The Nights We Hold never feel like a separate tower-defense minigame. They are the biggest ARPG battles in the game. The player is always fighting, moving, killing with the character they have spent hours building. Troops support. Fortifications create opportunities. Objectives give direction. The director builds pressure. The city responds to what the player does.

You have spent the game becoming a legendary warrior. Now an entire city depends on what you can do. Hold until dawn.
