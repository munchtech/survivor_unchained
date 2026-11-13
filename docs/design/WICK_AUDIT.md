# Warden wick audit

Design report for the classes lead, November 11, 2026. Audited integration **9a991da71**. The lamp inventories and the rules determining these marks are unchanged from the initial ede4bf910 snapshot. Documentation only: no game code, data, art, UI layout, or story text changes. Idea names below are design handles, not proposed player-facing copy.

**Pick first: Third Blow (SU1), offered on the first road level-up.** Its heavy-count rule already exists, the tutorial names that moment, and the live lamp instead gives +10% damage. Connect that mechanic before making the player wait for a Turn. The first ten minutes is a future acceptance gate, not a measured delivery claim.

## Scope and classification

Sources: [ARPG_FUN, section 4 items 9 and 11](ARPG_FUN.md), [ONE_BUILD, sections 4-5](ONE_BUILD.md), [skill_lamps.json](../../godot/data/content/skill_lamps.json), and [wicks.json](../../godot/data/content/wicks.json). Content/Wicks.cs loads the latter; Rpg/WickBook.cs expands three strands into twelve lamp positions per skill. Shared templates are expanded per skill: Oathblade's wide.1 and Sunder's wide.1 are separate choices. A live row's key is **(skill, lamp ID)**; a catalog row's key is its full **id**. Similar IDs across sources are different records, sometimes with different effects.

- **NUMBER:** only damage, an already-granted healing/barrier amount, cooldown/cost, existing-status chance, duration, speed, reach, radius, or another size changes. Conditional stat bonuses still count. A larger circle or farther straight rush is the same shape.
- **BEHAVIOR:** changes shape, attack/branch/heavy count, target selection, trigger, element, or adds a status/resource grant not previously present. A full reset or new re-press window changes when she can act; subtracting seconds from a wait is NUMBER. A numerical price attached to a new mechanic stays BEHAVIOR.
- Compare against the base skill **and required parents**. The Answer only retimes answers its parents already supply. Let Blood trades damage between an existing cut and bleed. Third Blow changes which firing produces the heavy line.
- The mark classifies the definition, not player availability. A BEHAVIOR record awaiting wiring is not delivered behavior. Baseline conflicts are called out separately.

There are **219 inventory rows**: 84 live positions, 132 catalog lamps, and 3 shared Unions. The eleven catalog skill headers are covered in the count table. Library templates, keywords, rank growth, and shared surplus cards (Hotter, Banked, A draught) are not separate Warden wick lamps. The unused library frost strand is not assigned to a Warden wick. Board-wide lamps_v2.json is outside this skill-wick audit.

## Counts and availability

| Skill | Live NUMBER | Live BEHAVIOR | Catalog NUMBER | Catalog BEHAVIOR | Live strands; suggested first |
|---|---:|---:|---:|---:|---|
| Oathblade | 9 | 3 | 4 | 8 | wide, linger, holy; first wide |
| Judgment Disc | 8 | 4 | 1 | 11 | chain, split, fire; first chain |
| Dawnpulse | 8 | 4 | 2 | 10 | pulse, linger, fire; first pulse |
| Sunder | 9 | 3 | 0 | 12 | wide, holy, sunder.stroke; first sunder.stroke |
| Groundbreaker | 10 | 2 | 1 | 11 | wide, linger, groundbreaker.aftershock; first groundbreaker.aftershock |
| Rebuke | 8 | 4 | 1 | 11 | fire, onkill, rebuke.morning; first rebuke.morning |
| Watch Bell | 10 | 2 | 2 | 10 | wide, pulse, watch_bell.stone; first watch_bell.stone |
| Shield Charge | 0 | 0 | 3 | 9 | No live wick |
| Heroic Leap | 0 | 0 | 4 | 8 | No live wick |
| Butcher's Cleaver | 0 | 0 | 3 | 9 | No live wick |
| Iron Vow | 0 | 0 | 4 | 8 | No live wick |

| Source | Entries | NUMBER | BEHAVIOR |
|---|---:|---:|---:|
| Live wicks, expanded | 84 | 62 | 22 |
| Catalog skill lamps | 132 | 25 | 107 |
| Catalog shared Unions | 3 | 0 | 3 |
| Total, keeping sources distinct | 219 | 87 | 132 |

**73.8% of live positions are NUMBER**, including all four live Wide Turns: area, cadence and damage do not create a new shape. The catalog brings that share down to **18.9%** of its skill lamps, but does not remove it. A kind label is not proof of a behavioral change.

**No BEHAVIOR option in the live wick planner:** Shield Charge, Heroic Leap, Butcher's Cleaver, and Iron Vow have no wicks.json entry at all. They have skill/rule primitives, not selectable live wick positions. **Among the seven live wicks, none lacks a BEHAVIOR option somewhere in its tree. Among all eleven catalog wicks, none lacks one either.** The early gap is shared: every suggested live strand starts with NUMBER, and all three lead-ins are NUMBER. Each suggested route waits for its fourth lamp, the Turn, before changing behavior; all seven suggested Turns are behavioral.

### What “today” means

The catalog's about field and ONE_BUILD's “does not read it yet” are now too broad. Wicks.Rows reads catalog **names and card measurements**, not the full effect graph. Wicks.Load, WickBook.Path/DayPath, Battle.Relight, and Turns.Build still source selectable effects from wicks.json. LevelCardModel deliberately shows the live text. Catalog engine labels describe reusable primitives, not proof those lamps are offered.

P7 implemented the four newer skills' rules in WardenWicks.cs / PressedWarden.cs. WickRulesTests.Light manually installs their rule effects or evolutions. That establishes rule paths, not a catalog loader. Inventory B labels **Spec** for definitions/primitives not loaded as these lamps, and **Hook** for P7 paths that exist but have no live wick entry.

Keep these mismatches in the build brief:

- Live Sunder sunder.stroke.1 is +10% damage; the catalog record with that full ID is Third Blow. A name read cannot replace its mechanic. HeavyEveryOf already supports sunder.third_blow.
- Heave currently passes Heavy = true on every heave hit. Full Weight claims every sixth becomes every heave. Its intended count change is BEHAVIOR, but the benefit already exists in this path. Resolve its identity before implementing a redundant lamp.
- FireCrack already chooses a dense pack when not explicitly aimed; campaign casts use the cursor's pack. Thickest Press must distinguish itself while preserving aim. Nearest-to-densest is not an honest description of today's migration.
- Toll already stops the radial pull short of her feet (1.2 m plus the foe's radius). Arm's Length only changes that stop distance, so it is NUMBER despite its shape label.
- Catalog Burning Edge promises 3 s; existing SearEdge uses 1 s. Catalog Shield of Morning promises fast barrier-held answers; its live Turn only grants 0.1% health per target, capped at 0.4% per strike. Catalog Stone Bell promises an enclosure; its live Turn only grants Stones. These are different effects.
- Cleaver pace lamps alter Resolve cost/drain in the campaign and interval outside it (RulePayMul / RuleCooldownMul). Light Grip remains NUMBER in both modes.

## Inventory A: live wick lamps

Values are the data's own values before rank, gear, and other modifiers. School chance lead-ins introduce a status and count as BEHAVIOR; their damage-against-status and duration successors do not. Projectile shape lead-ins use speed instead of area. A/B are **two alternative replacements**, fully defined with systems below; they are not a request to install both.

| Skill | Live lamp ID | Lamp | What it does today | Mark | Replacement A | Replacement B |
|---|---|---|---|---|---|---|
| Oathblade | `wide.1` | Lead-in | +10% damage | NUMBER | OB1 | OB4 |
| Oathblade | `wide.2` | Lead-in | +10% area (projectiles: +15% speed) | NUMBER | OB5 | OB10 |
| Oathblade | `wide.3` | Lead-in | 8% shorter cooldown | NUMBER | OB2 | OB6 |
| Oathblade | `wide.4` | Wide | Bigger and slower: 20% larger, 30% longer cooldown, 15% less damage. | NUMBER | OB3 | OB5 |
| Oathblade | `linger.1` | Lead-in | +10% damage | NUMBER | OB4 | OB9 |
| Oathblade | `linger.2` | Lead-in | +10% area (projectiles: +15% speed) | NUMBER | OB3 | OB10 |
| Oathblade | `linger.3` | Lead-in | 8% shorter cooldown | NUMBER | OB2 | OB8 |
| Oathblade | `linger.4` | Linger | It leaves 1.5 m of its own ground for 2 s, burning at 25% of its damage a second. | BEHAVIOR | - | - |
| Oathblade | `holy.1` | Lead-in | 15% chance to sear | BEHAVIOR | - | - |
| Oathblade | `holy.2` | Lead-in | +10% damage to seared enemies | NUMBER | OB7 | OB9 |
| Oathblade | `holy.3` | Lead-in | Sear lasts 15% longer | NUMBER | OB6 | OB8 |
| Oathblade | `holy.4` | Holy | It becomes holy: it sears (dazzled for a moment; holy strikes it harder), and strikes 10% harder. | BEHAVIOR | - | - |
| Judgment Disc | `chain.1` | Lead-in | +10% damage | NUMBER | JD1 | JD4 |
| Judgment Disc | `chain.2` | Lead-in | +15% projectile speed (takes speed instead of +10% area). | NUMBER | JD3 | JD5 |
| Judgment Disc | `chain.3` | Lead-in | 8% shorter cooldown | NUMBER | JD6 | JD7 |
| Judgment Disc | `chain.4` | Chain | It bounces twice more, at 85% damage. | BEHAVIOR | - | - |
| Judgment Disc | `split.1` | Lead-in | +10% damage | NUMBER | JD2 | JD4 |
| Judgment Disc | `split.2` | Lead-in | +15% projectile speed (takes speed instead of +10% area). | NUMBER | JD2 | JD3 |
| Judgment Disc | `split.3` | Lead-in | 8% shorter cooldown | NUMBER | JD1 | JD6 |
| Judgment Disc | `split.4` | Split | Three smaller: three times the projectiles, each 28% damage and 75% size. | BEHAVIOR | - | - |
| Judgment Disc | `fire.1` | Lead-in | 15% chance to burn | BEHAVIOR | - | - |
| Judgment Disc | `fire.2` | Lead-in | +10% damage to burning enemies | NUMBER | JD5 | JD8 |
| Judgment Disc | `fire.3` | Lead-in | Burn lasts 15% longer | NUMBER | JD7 | JD8 |
| Judgment Disc | `fire.4` | Fire | It becomes fire: it burns, and strikes 10% harder. | BEHAVIOR | - | - |
| Dawnpulse | `pulse.1` | Lead-in | +10% damage | NUMBER | DA1 | DA6 |
| Dawnpulse | `pulse.2` | Lead-in | +10% area (projectiles: +15% speed) | NUMBER | DA2 | DA3 |
| Dawnpulse | `pulse.3` | Lead-in | 8% shorter cooldown | NUMBER | DA7 | DA9 |
| Dawnpulse | `pulse.4` | Pulse | It goes off three times, 0.3 s apart, each at 70% damage and 85% size. | BEHAVIOR | - | - |
| Dawnpulse | `linger.1` | Lead-in | +10% damage | NUMBER | DA1 | DA8 |
| Dawnpulse | `linger.2` | Lead-in | +10% area (projectiles: +15% speed) | NUMBER | DA3 | DA5 |
| Dawnpulse | `linger.3` | Lead-in | 8% shorter cooldown | NUMBER | DA4 | DA9 |
| Dawnpulse | `linger.4` | Linger | It leaves 1.5 m of its own ground for 2 s, burning at 25% of its damage a second. | BEHAVIOR | - | - |
| Dawnpulse | `fire.1` | Lead-in | 15% chance to burn | BEHAVIOR | - | - |
| Dawnpulse | `fire.2` | Lead-in | +10% damage to burning enemies | NUMBER | DA5 | DA6 |
| Dawnpulse | `fire.3` | Lead-in | Burn lasts 15% longer | NUMBER | DA4 | DA8 |
| Dawnpulse | `fire.4` | Fire | It becomes fire: it burns, and strikes 10% harder. | BEHAVIOR | - | - |
| Sunder | `wide.1` | Lead-in | +10% damage | NUMBER | SU1 | SU4 |
| Sunder | `wide.2` | Lead-in | +10% area (projectiles: +15% speed) | NUMBER | SU2 | SU3 |
| Sunder | `wide.3` | Lead-in | 8% shorter cooldown | NUMBER | SU5 | SU8 |
| Sunder | `wide.4` | Wide | Bigger and slower: 20% larger, 30% longer cooldown, 15% less damage. | NUMBER | SU6 | SU7 |
| Sunder | `holy.1` | Lead-in | 15% chance to sear | BEHAVIOR | - | - |
| Sunder | `holy.2` | Lead-in | +10% damage to seared enemies | NUMBER | SU9 | SU10 |
| Sunder | `holy.3` | Lead-in | Sear lasts 15% longer | NUMBER | SU4 | SU5 |
| Sunder | `holy.4` | Holy | It becomes holy: it sears (dazzled for a moment; holy strikes it harder), and strikes 10% harder. | BEHAVIOR | - | - |
| Sunder | `sunder.stroke.1` | Lead-in | +10% damage | NUMBER | SU1 | SU5 |
| Sunder | `sunder.stroke.2` | Lead-in | +10% reach (and the heavy line's) | NUMBER | SU2 | SU6 |
| Sunder | `sunder.stroke.3` | Lead-in | 8% less time between swings | NUMBER | SU3 | SU8 |
| Sunder | `sunder.stroke.4` | Splitting Stroke | Every 2nd swing is heavy and splits the ground; swings 15% slower. | BEHAVIOR | - | - |
| Groundbreaker | `wide.1` | Lead-in | +10% damage | NUMBER | GR1 | GR2 |
| Groundbreaker | `wide.2` | Lead-in | +10% area (projectiles: +15% speed) | NUMBER | GR4 | GR6 |
| Groundbreaker | `wide.3` | Lead-in | 8% shorter cooldown | NUMBER | GR3 | GR9 |
| Groundbreaker | `wide.4` | Wide | Bigger and slower: 20% larger, 30% longer cooldown, 15% less damage. | NUMBER | GR5 | GR7 |
| Groundbreaker | `linger.1` | Lead-in | +10% damage | NUMBER | GR7 | GR8 |
| Groundbreaker | `linger.2` | Lead-in | +10% area (projectiles: +15% speed) | NUMBER | GR5 | GR10 |
| Groundbreaker | `linger.3` | Lead-in | 8% shorter cooldown | NUMBER | GR2 | GR3 |
| Groundbreaker | `linger.4` | Linger | It leaves 1.5 m of its own ground for 2 s, burning at 25% of its damage a second. | BEHAVIOR | - | - |
| Groundbreaker | `groundbreaker.aftershock.1` | Lead-in | +10% damage | NUMBER | GR1 | GR7 |
| Groundbreaker | `groundbreaker.aftershock.2` | Lead-in | +10% crack and heave size | NUMBER | GR4 | GR6 |
| Groundbreaker | `groundbreaker.aftershock.3` | Lead-in | 8% shorter cooldown | NUMBER | GR8 | GR9 |
| Groundbreaker | `groundbreaker.aftershock.4` | Aftershock | 0.8 s later the heave strikes the same spot again at 35%, stunning again. | BEHAVIOR | - | - |
| Rebuke | `fire.1` | Lead-in | 15% chance to burn | BEHAVIOR | - | - |
| Rebuke | `fire.2` | Lead-in | +10% damage to burning enemies | NUMBER | RE4 | RE8 |
| Rebuke | `fire.3` | Lead-in | Burn lasts 15% longer | NUMBER | RE3 | RE6 |
| Rebuke | `fire.4` | Fire | It becomes fire: it burns, and strikes 10% harder. | BEHAVIOR | - | - |
| Rebuke | `onkill.1` | Lead-in | +10% damage | NUMBER | RE1 | RE2 |
| Rebuke | `onkill.2` | Lead-in | +10% damage to champions | NUMBER | RE5 | RE6 |
| Rebuke | `onkill.3` | Lead-in | 8% shorter cooldown | NUMBER | RE3 | RE7 |
| Rebuke | `onkill.4` | On-kill | It fires again from what it kills, at 30% damage (once every 0.5 s at most). | BEHAVIOR | - | - |
| Rebuke | `rebuke.morning.1` | Lead-in | +10% damage | NUMBER | RE1 | RE2 |
| Rebuke | `rebuke.morning.2` | Lead-in | +10% strike size | NUMBER | RE4 | RE7 |
| Rebuke | `rebuke.morning.3` | Lead-in | +10% damage to champions | NUMBER | RE5 | RE6 |
| Rebuke | `rebuke.morning.4` | Shield of Morning | Each rebuke strike leaves you a barrier of 0.1% of health for each creature it strikes. | BEHAVIOR | - | - |
| Watch Bell | `wide.1` | Lead-in | +10% damage | NUMBER | WB1 | WB7 |
| Watch Bell | `wide.2` | Lead-in | +10% area (projectiles: +15% speed) | NUMBER | WB2 | WB6 |
| Watch Bell | `wide.3` | Lead-in | 8% shorter cooldown | NUMBER | WB7 | WB9 |
| Watch Bell | `wide.4` | Wide | Bigger and slower: 20% larger, 30% longer cooldown, 15% less damage. | NUMBER | WB2 | WB3 |
| Watch Bell | `pulse.1` | Lead-in | +10% damage | NUMBER | WB1 | WB4 |
| Watch Bell | `pulse.2` | Lead-in | +10% area (projectiles: +15% speed) | NUMBER | WB3 | WB8 |
| Watch Bell | `pulse.3` | Lead-in | 8% shorter cooldown | NUMBER | WB7 | WB9 |
| Watch Bell | `pulse.4` | Pulse | It goes off three times, 0.3 s apart, each at 70% damage and 85% size. | BEHAVIOR | - | - |
| Watch Bell | `watch_bell.stone.1` | Lead-in | +10% damage | NUMBER | WB4 | WB5 |
| Watch Bell | `watch_bell.stone.2` | Lead-in | +10% reach | NUMBER | WB2 | WB6 |
| Watch Bell | `watch_bell.stone.3` | Lead-in | 8% shorter time between tolls | NUMBER | WB8 | WB9 |
| Watch Bell | `watch_bell.stone.4` | Stone Bell | Each toll lays two stones, and each champion it draws lays one more. | BEHAVIOR | - | - |

## Inventory B: catalog skill lamps

Each row reports the record's current definition, not a claim that the planner offers it. **Spec/built**, **Spec/rule**, and **Spec/new** retain the engine category with that limitation. **Hook** means a P7 rule/evolution path exists, still without a live wick entry. Each NUMBER row explains its mark and maps to two complete alternatives.

| Catalog ID | Skill / lamp | Current definition and availability | Mark | Replacement A | Replacement B |
|---|---|---|---|---|---|
| `oathblade.oathkeeper.1` | Oathblade / Crescent | Spec/new. Every third swing throws a crescent of light 6 m ahead. | BEHAVIOR | - | - |
| `oathblade.oathkeeper.2` | Oathblade / Blessed Steel | Spec/built. Oathblade turns holy: its cuts and crescents sear what they strike for 1 s. | BEHAVIOR | - | - |
| `oathblade.oathkeeper.3` | Oathblade / Onward | Spec/new. A crescent that kills throws another on from where it fell, at 50%, once a swing. | BEHAVIOR | - | - |
| `oathblade.oathkeeper.4` | Oathblade / Oathkeeper | Spec/built. Every swing throws a 2 m crescent of holy light that runs on through the whole crowd. | BEHAVIOR | - | - |
| `oathblade.graveedge.1` | Oathblade / Notched | Spec/rule. Oathblade's cuts bleed for 35% of the blow over 3 s. | BEHAVIOR | - | - |
| `oathblade.graveedge.2` | Oathblade / Open Wound | Spec/new. A cut on a bleeding thing starts its bleed over, 50% deeper. NUMBER reason: The parent already bleeds, and ordinary bleed reapplication refreshes time. Its extra payoff is deeper damage. | NUMBER | OB7 | OB9 |
| `oathblade.graveedge.3` | Oathblade / Let Blood | Spec/new. Oathblade strikes 25% softer, but each cut bleeds for 80% of the blow. NUMBER reason: Trades direct damage for damage in the bleed already supplied by its parent. | NUMBER | OB3 | OB8 |
| `oathblade.graveedge.4` | Oathblade / Grave-Edge | Spec/built. The edge drinks: anything bleeding below a sixth (17%) of its life dies at the next cut. | BEHAVIOR | - | - |
| `oathblade.answer.1` | Oathblade / On Guard | Spec/rule. A block or a perfect dash swings Oathblade at once, at most every 0.5 s. | BEHAVIOR | - | - |
| `oathblade.answer.2` | Oathblade / Blow for Blow | Spec/new. A blow that reaches you swings Oathblade at once too, at most every 1 s. | BEHAVIOR | - | - |
| `oathblade.answer.3` | Oathblade / Slow to Draw | Spec/new. Oathblade's own swings come 25% slower, but each answer strikes 50% harder. NUMBER reason: Only retimes existing swings and increases existing answer damage. | NUMBER | OB1 | OB6 |
| `oathblade.answer.4` | Oathblade / The Answer | Spec/new. Oathblade answers every block, perfect dash and blow on you, as often as every 0.3 s; its own swings come half as often. NUMBER reason: Its parents already answer all three events; only their gaps and the ordinary timer change. | NUMBER | OB5 | OB10 |
| `judgement_disc.reckoning.1` | Judgment Disc / Found Wanting | Spec/new. Each thing the disc kills gives it one more ricochet, 5 more at most a throw. | BEHAVIOR | - | - |
| `judgement_disc.reckoning.2` | Judgment Disc / Kept Aloft | Spec/new. A ricochet off a champion keeps the disc flying 0.5 s longer. NUMBER reason: Only adds flight duration after a champion ricochet. | NUMBER | JD2 | JD5 |
| `judgement_disc.reckoning.3` | Judgment Disc / Weighed | Spec/new. Each ricochet seeks the strongest thing within 6 m, not the nearest. | BEHAVIOR | - | - |
| `judgement_disc.reckoning.4` | Judgment Disc / Reckoning | Spec/new. The disc ricochets for as long as it flies, each strike 8% heavier than the last. | BEHAVIOR | - | - |
| `judgement_disc.aegis.1` | Judgment Disc / First Ward | Spec/new. The disc's first strike each throw gives you a barrier of 2% of health. | BEHAVIOR | - | - |
| `judgement_disc.aegis.2` | Judgment Disc / Arrowbreaker | Spec/new. The disc flies 25% slower, but it breaks every missile it passes through. | BEHAVIOR | - | - |
| `judgement_disc.aegis.3` | Judgment Disc / Turned Aside | Spec/new. Each missile the disc breaks flies back at whoever loosed it, at 100% of the disc's strike. | BEHAVIOR | - | - |
| `judgement_disc.aegis.4` | Judgment Disc / Aegis Wheel | Spec/built. Two discs fly each throw, and every ricochet gives you a barrier of 1% of health, 20% held at most. | BEHAVIOR | - | - |
| `judgement_disc.threefold.1` | Judgment Disc / Last Word | Spec/new. The disc's last ricochet bursts into 3 shards that fly on 5 m, each at 40%. | BEHAVIOR | - | - |
| `judgement_disc.threefold.2` | Judgment Disc / Cloven | Spec/new. A heavy throw splits in two, each at 75% (a stalker: a throw within 1 s of a dash). | BEHAVIOR | - | - |
| `judgement_disc.threefold.3` | Judgment Disc / Splinters | Spec/new. The disc flies 25% slower, but its shards ricochet twice each. | BEHAVIOR | - | - |
| `judgement_disc.threefold.4` | Judgment Disc / Threefold | Spec/built. Three smaller discs fly each throw, each at 28% damage and 75% size. | BEHAVIOR | - | - |
| `dawnpulse.dawn.1` | Dawnpulse / Kind Light | Spec/new. A pulse that strikes 5 or more mends you 3% of health. | BEHAVIOR | - | - |
| `dawnpulse.dawn.2` | Dawnpulse / Sun in Their Eyes | Spec/new. Dawnpulse strikes 20% softer, but what it sears strikes you 15% weaker. NUMBER reason: Direct and incoming damage modifiers on existing sear; no new firing or status. | NUMBER | DA5 | DA8 |
| `dawnpulse.dawn.3` | Dawnpulse / Mantle | Spec/new. For 2 s after each pulse, whatever strikes you is seared. | BEHAVIOR | - | - |
| `dawnpulse.dawn.4` | Dawnpulse / Circle of Dawn | Spec/new. Dawnpulse answers blows, not its timer: it fires each time a blow reaches you, at most every 1 s, and mends you 1% of health for each thing it strikes, 8% at most. | BEHAVIOR | - | - |
| `dawnpulse.sunbreak.1` | Dawnpulse / Sunstruck | Spec/new. A pulse that strikes a champion leaves daylight 2 m round under it, burning 3 s at 30% a second. | BEHAVIOR | - | - |
| `dawnpulse.sunbreak.2` | Dawnpulse / Morning Road | Spec/new. Where you dash, daylight lies behind you for 2 s, burning at 30% of the pulse a second. | BEHAVIOR | - | - |
| `dawnpulse.sunbreak.3` | Dawnpulse / Burnt Offering | Spec/new. Dawnpulse comes 25% slower, but what dies in its daylight bursts 2 m round at 50% of the pulse. | BEHAVIOR | - | - |
| `dawnpulse.sunbreak.4` | Dawnpulse / Sunbreak | Spec/built. Each pulse leaves a ring of daylight 3.5 m round that burns 2.5 s, at 30% of the pulse a second. | BEHAVIOR | - | - |
| `dawnpulse.rhythm.1` | Dawnpulse / Dawn Rhythm | Spec/rule. A heavy blow fires Dawnpulse as well, at most every 1.5 s (an arcanist: a kill by another spell). | BEHAVIOR | - | - |
| `dawnpulse.rhythm.2` | Dawnpulse / Where the Blow Falls | Spec/new. A pulse fired by a heavy blow rises 3.75 m round where the blow landed, not about you (an arcanist: where the thing died). | BEHAVIOR | - | - |
| `dawnpulse.rhythm.3` | Dawnpulse / Keep Time | Spec/new. Dawnpulse's own timer runs 50% longer, but a heavy blow (an arcanist: a spell kill) may fire it every 0.8 s. NUMBER reason: Both the timer and the heavy-trigger gap already exist in its parents. | NUMBER | DA2 | DA7 |
| `dawnpulse.rhythm.4` | Dawnpulse / Dawn upon Dawn | Spec/built. Each pulse goes off three times, 0.3 s apart, each at 70% damage and 85% size. | BEHAVIOR | - | - |
| `sunder.stroke.1` | Sunder / Third Blow | Spec/rule. Every 3rd swing is heavy, not every 4th. | BEHAVIOR | - | - |
| `sunder.stroke.2` | Sunder / Harvest | Spec/new. A heavy blow that kills 3 or more makes the next swing heavy too. | BEHAVIOR | - | - |
| `sunder.stroke.3` | Sunder / Thrown Down | Spec/new. Sunder swings 10% slower, but what a heavy blow throws back knocks down what it lands on, stunned 0.5 s. | BEHAVIOR | - | - |
| `sunder.stroke.4` | Sunder / Splitting Stroke | Spec/built. Every second swing is heavy and splits the ground; Sunder swings 15% slower. | BEHAVIOR | - | - |
| `sunder.furrow.1` | Sunder / Wide Swing | Spec/new. Sunder sweeps 300°, not 220°, and what it strikes at your back is thrown round in front of you. | BEHAVIOR | - | - |
| `sunder.furrow.2` | Sunder / Back Furrow | Spec/new. The heavy line also runs 4 m behind you. | BEHAVIOR | - | - |
| `sunder.furrow.3` | Sunder / Plowshare | Spec/new. Sunder swings 10% slower, but its heavy line throws what it strikes aside, opening a lane 2 m wide. | BEHAVIOR | - | - |
| `sunder.furrow.4` | Sunder / Three Furrows | Spec/new. The heavy line splits in three, 25° apart, each running its full 7 m. | BEHAVIOR | - | - |
| `sunder.edge.1` | Sunder / Burning Edge | Spec/rule. Sunder's heavy line sears what it strikes for 3 s. | BEHAVIOR | - | - |
| `sunder.edge.2` | Sunder / Hot Iron | Spec/new. Sunder strikes 15% softer, but every swing sears, not only the heavy line. | BEHAVIOR | - | - |
| `sunder.edge.3` | Sunder / Tinder | Spec/new. A heavy blow on a seared thing sets it burning 3 s, at 25% of the blow a second. | BEHAVIOR | - | - |
| `sunder.edge.4` | Sunder / Watch-Fire | Spec/new. Sunder takes holy fire: it becomes holy, and everything it sears burns 3 s at 25% of the blow a second. | BEHAVIOR | - | - |
| `groundbreaker.heave.1` | Groundbreaker / Sinking Ground | Spec/new. Before the heave strikes, everything within 4 m slides 1.5 m toward its heart. | BEHAVIOR | - | - |
| `groundbreaker.heave.2` | Groundbreaker / Full Weight | Spec/new. Every heave is heavy, not every 6th. | BEHAVIOR | - | - |
| `groundbreaker.heave.3` | Groundbreaker / Driven Deep | Spec/new. Groundbreaker comes 1 s slower, but the heave's heart, 1 m round, strikes twice as hard. NUMBER reason: Cooldown and conditional central damage; still one heave in the same place. | NUMBER | GR3 | GR9 |
| `groundbreaker.heave.4` | Groundbreaker / Second Heave | Spec/built. 0.8 s later the heave strikes the same spot again at 35%, stunning again. | BEHAVIOR | - | - |
| `groundbreaker.cracks.1` | Groundbreaker / Twin Cracks | Spec/rule. Groundbreaker opens two cracks, 30° apart, each to its own pack. | BEHAVIOR | - | - |
| `groundbreaker.cracks.2` | Groundbreaker / Fault Line | Spec/new. The cracks run 14 m and stay open 2 s; what walks across one is slowed 40% for 1 s. | BEHAVIOR | - | - |
| `groundbreaker.cracks.3` | Groundbreaker / Thickest Press | Spec/new. The cracks seek the thickest packs within 14 m, not the nearest. | BEHAVIOR | - | - |
| `groundbreaker.cracks.4` | Groundbreaker / Crow's Foot | Spec/new. Each crack branches where it reaches its pack: a new crack runs on to the next pack within 8 m, 3 packs at most. | BEHAVIOR | - | - |
| `groundbreaker.upheaval.1` | Groundbreaker / Upheaval | Spec/rule. Lesser things the heave strikes are thrown up 0.8 s, and take 30% more while in the air. | BEHAVIOR | - | - |
| `groundbreaker.upheaval.2` | Groundbreaker / Down They Come | Spec/new. What falls from the air lands hard, striking 1.5 m round at 30% of the heave. | BEHAVIOR | - | - |
| `groundbreaker.upheaval.3` | Groundbreaker / Great and Small | Spec/new. Groundbreaker comes 20% slower, but champions are thrown up too, for 0.5 s. | BEHAVIOR | - | - |
| `groundbreaker.upheaval.4` | Groundbreaker / Riven Earth | Spec/new. The whole crack heaves: everything along it is thrown up 1 s, not only the pack at its end. | BEHAVIOR | - | - |
| `rebuke.morning.1` | Rebuke / Thronged | Spec/new. A rebuke that strikes 4 or more gives you a barrier of 2% of health, 20% held at most. | BEHAVIOR | - | - |
| `rebuke.morning.2` | Rebuke / Broken Ward | Spec/new. When your barrier breaks, Rebuke strikes everything within 5 m at once. | BEHAVIOR | - | - |
| `rebuke.morning.3` | Rebuke / Glare | Spec/new. While a barrier holds, Rebuke's light sears what it strikes for 3 s. | BEHAVIOR | - | - |
| `rebuke.morning.4` | Rebuke / Shield of Morning | Spec/new. While your barrier holds, Rebuke answers every blow on you, as often as every 0.2 s, and each rebuke gives a barrier of 1% of health for each thing it strikes, 4% at most, 20% held at most. | BEHAVIOR | - | - |
| `rebuke.strong.1` | Rebuke / Rebuke the Strong | Spec/new. A champion's blow on you is rebuked at once, even inside its wait; the same champion once every 5 s. | BEHAVIOR | - | - |
| `rebuke.strong.2` | Rebuke / Brought Low | Spec/new. A champion Rebuke strikes deals you 25% less for 3 s. NUMBER reason: Only reduces a struck champion's damage against her. | NUMBER | RE4 | RE6 |
| `rebuke.strong.3` | Rebuke / Dazed | Spec/new. Rebuke strikes 3 fewer of the nearest, but a champion it strikes is stunned 0.5 s. | BEHAVIOR | - | - |
| `rebuke.strong.4` | Rebuke / Humbled | Spec/new. A rebuke on a champion is a heavy blow, and its light breaks out 4 m round the champion. | BEHAVIOR | - | - |
| `rebuke.answering.1` | Rebuke / The Long Answer | Spec/new. Rebuke's light runs on through the one that struck you, 6 m behind it, striking all in the line. | BEHAVIOR | - | - |
| `rebuke.answering.2` | Rebuke / Tidings | Spec/new. Rebuke's light leaps on from the one that struck you: 3 leaps, each to the nearest thing within 4 m. | BEHAVIOR | - | - |
| `rebuke.answering.3` | Rebuke / Slow to Anger | Spec/new. Rebuke answers at most every 1 s, not every 0.5 s, but its light leaps 3 more times. | BEHAVIOR | - | - |
| `rebuke.answering.4` | Rebuke / Open Rebuke | Spec/new. Each rebuke breaks out in a ring of light 4 m round you, striking everything in it. | BEHAVIOR | - | - |
| `watch_bell.stone.1` | Watch Bell / Alarm | Spec/new. When the wall answers (at 6 Stones), the bell tolls at once and its timer starts over. | BEHAVIOR | - | - |
| `watch_bell.stone.2` | Watch Bell / Millstone | Spec/new. While you hold 3 or more Stones, what the bell draws lands stunned 0.5 s. | BEHAVIOR | - | - |
| `watch_bell.stone.3` | Watch Bell / Cairn | Spec/new. Each toll that draws 5 or more lays a Stone. | BEHAVIOR | - | - |
| `watch_bell.stone.4` | Watch Bell / Stone Bell | Spec/new. Each toll raises a ring of standing stones 5 m round you for 3 s: what the bell drew is shut in with you, and each thing that reaches the ring from outside is held there and lays a Stone, once a toll each. | BEHAVIOR | - | - |
| `watch_bell.loud.1` | Watch Bell / Loud Bell | Spec/new. The bell tolls twice, 1 s apart: the second draws from 11 m and gives no barrier. | BEHAVIOR | - | - |
| `watch_bell.loud.2` | Watch Bell / Arm's Length | Spec/new. What the bell draws stops 2 m from you, in a ring, not at your feet. NUMBER reason: Toll already pulls to a stop ring; this changes its stopping distance. | NUMBER | WB2 | WB3 |
| `watch_bell.loud.3` | Watch Bell / In Their Wake | Spec/new. Each champion the bell draws drags the 3 nearest lesser things with it. | BEHAVIOR | - | - |
| `watch_bell.loud.4` | Watch Bell / Muster | Spec/new. The bell draws everything within 10 m into a press 3 m before you, all facing you. | BEHAVIOR | - | - |
| `watch_bell.iron.1` | Watch Bell / Iron Bell | Spec/new. What the bell draws is slowed 30% for 3 s. | BEHAVIOR | - | - |
| `watch_bell.iron.2` | Watch Bell / Bell and Barrier | Spec/new. Each slowed thing that strikes you gives you a barrier of 0.5% of health, 15% held at most. | BEHAVIOR | - | - |
| `watch_bell.iron.3` | Watch Bell / Leaden | Spec/new. The bell tolls 1 s slower, but its slow lasts until the next toll. NUMBER reason: Only extends the existing slow and lengthens its timer. | NUMBER | WB8 | WB9 |
| `watch_bell.iron.4` | Watch Bell / Long Toll | Spec/new. For 3 s after each toll, whatever comes within 6 m is drawn in and slowed too. | BEHAVIOR | - | - |
| `shield_charge.ram.1` | Shield Charge / Hide Like Iron | Hook; not in live wick planner. The charge's barrier is 25% of health, not 15%. NUMBER reason: Only increases the barrier already granted at charge start. | NUMBER | SC1 | SC6 |
| `shield_charge.ram.2` | Shield Charge / Unbowed | Hook; not in live wick planner. Each thing the charge strikes adds a barrier of 2% of health, 20% held at most above the charge's own. | BEHAVIOR | - | - |
| `shield_charge.ram.3` | Shield Charge / Goring Rush | Hook; not in live wick planner. What the charge strikes bleeds for 80% of the blow over 4 s, and a champion that stops it takes 50% more. | BEHAVIOR | - | - |
| `shield_charge.ram.4` | Shield Charge / Driven Home | Hook; not in live wick planner. The charge ends in a slam: everything within 3 m is struck for 140% of its blow and stunned for 1 s. | BEHAVIOR | - | - |
| `shield_charge.drive.1` | Shield Charge / Headlong | Hook; not in live wick planner. The charge runs 12 m, not 8, in the same 0.3 s. NUMBER reason: Only increases distance/speed along the existing straight rush. | NUMBER | SC2 | SC4 |
| `shield_charge.drive.2` | Shield Charge / Swept Along | Hook; not in live wick planner. Lesser things the charge strikes ride your shield to its end, 8 at most, and are thrown down there, stunned 1 s. | BEHAVIOR | - | - |
| `shield_charge.drive.3` | Shield Charge / Breakthrough | Hook; not in live wick planner. The charge strikes 20% softer, but no champion stops it: one it meets is struck as if it had, stunned 1 s, and you run on. | BEHAVIOR | - | - |
| `shield_charge.drive.4` | Shield Charge / Landslide | Hook; not in live wick planner. At the charge's end, what rides your shield is hurled on along your line: a 3 m wide tumble of bodies that rolls 10 m, striking everything in it for 100% of the charge's blow. | BEHAVIOR | - | - |
| `shield_charge.guard.1` | Shield Charge / Shield Up | Hook; not in live wick planner. For 2 s after the charge, your shield blocks every blow from in front of you. | BEHAVIOR | - | - |
| `shield_charge.guard.2` | Shield Charge / Rebound | Hook; not in live wick planner. Each block takes 1 s off the charge's wait. NUMBER reason: A block subtracts wait time; it does not itself fire or add a charge. | NUMBER | SC5 | SC3 |
| `shield_charge.guard.3` | Shield Charge / Sprung | Hook; not in live wick planner. A perfect dash readies the charge at once, as often as every 3 s. | BEHAVIOR | - | - |
| `shield_charge.guard.4` | Shield Charge / Stampede | Hook; not in live wick planner. The charge holds 3 runs: press again within 2 s to charge on from where you stopped, each run striking 30% harder than the last; then it waits. | BEHAVIOR | - | - |
| `heroic_leap.quake.1` | Heroic Leap / Crater | Hook; not in live wick planner. The landing ring reaches 4.5 m, not 3.5 m, and what it knocks down is stunned 1.2 s, not 0.8 s. NUMBER reason: Only increases landing radius and existing stun duration. | NUMBER | HL1 | HL6 |
| `heroic_leap.quake.2` | Heroic Leap / Second Quake | Hook; not in live wick planner. 1 s after you land, the ring heaves again at 40% of the landing, stunning again. | BEHAVIOR | - | - |
| `heroic_leap.quake.3` | Heroic Leap / Ninepins | Hook; not in live wick planner. The leap waits 11 s, not 8, but what the landing throws flies 6 m and strikes what it lands on for 50% of the landing. | BEHAVIOR | - | - |
| `heroic_leap.quake.4` | Heroic Leap / Henge | Hook; not in live wick planner. Where you land, standing stones rise in a 6 m ring for 4 s: lesser things inside can't get out, and none outside get in. | BEHAVIOR | - | - |
| `heroic_leap.flight.1` | Heroic Leap / Far Spring | Hook; not in live wick planner. The leap reaches 13 m, not 9, in the same 0.62 s. NUMBER reason: Only increases range/speed of the same leap. | NUMBER | HL3 | HL5 |
| `heroic_leap.flight.2` | Heroic Leap / Into the Thick | Hook; not in live wick planner. Aim within 4 m of a pack and you land in its heart. | BEHAVIOR | - | - |
| `heroic_leap.flight.3` | Heroic Leap / Unshackled | Hook; not in live wick planner. Leaping breaks every slow and hold on you, and for 2 s after you land you run 30% faster. | BEHAVIOR | - | - |
| `heroic_leap.flight.4` | Heroic Leap / Iron Comet | Hook; not in live wick planner. Hold the key to hang aloft up to 1.5 s, untouchable, steering your landing with the cursor as far as 16 m. | BEHAVIOR | - | - |
| `heroic_leap.bound.1` | Heroic Leap / Spring-Heeled | Hook; not in live wick planner. A landing that kills 3 or more takes 4 s off the leap's wait. NUMBER reason: The kill condition only rebates cooldown; no extra landing or press window. | NUMBER | HL7 | HL4 |
| `heroic_leap.bound.2` | Heroic Leap / War Pace | Hook; not in live wick planner. For 3 s after you land, you swing and cast 25% faster. NUMBER reason: A landing grants only attack/cast speed. | NUMBER | HL8 | HL2 |
| `heroic_leap.bound.3` | Heroic Leap / Restless | Hook; not in live wick planner. The leap strikes 20% softer, but a landing that kills 5 or more readies it at once. | BEHAVIOR | - | - |
| `heroic_leap.bound.4` | Heroic Leap / Unending Bound | Hook; not in live wick planner. After a landing that kills, press again within 1.5 s to leap on at once, as far as 9 m, 4 leaps in a row at most. | BEHAVIOR | - | - |
| `cleaver.wound.1` | Butcher's Cleaver / Laid Open | Hook; not in live wick planner. Every chop bleeds, not 35% of them: 40% of the blow over 4 s. NUMBER reason: The base chop already bleeds; only its chance, damage and duration change. | NUMBER | CL1 | CL2 |
| `cleaver.wound.2` | Butcher's Cleaver / Spatter | Hook; not in live wick planner. A thing that dies bleeding sprays 3 m round, bleeding what it splashes for 30% of the chop over 3 s. | BEHAVIOR | - | - |
| `cleaver.wound.3` | Butcher's Cleaver / Bled Dry | Hook; not in live wick planner. Cleaver strikes 20% softer, but its bleeds deal all their damage in 1.5 s. NUMBER reason: Only direct damage and existing bleed duration change. | NUMBER | CL2 | CL5 |
| `cleaver.wound.4` | Butcher's Cleaver / Rupture | Hook; not in live wick planner. A chop on a bleeding thing tears it open: the rest of its bleed lands at once and splashes everything 2.5 m round for as much. | BEHAVIOR | - | - |
| `cleaver.weight.1` | Butcher's Cleaver / Overhand | Hook; not in live wick planner. Every 3rd chop is heavy. | BEHAVIOR | - | - |
| `cleaver.weight.2` | Butcher's Cleaver / Hewn Down | Hook; not in live wick planner. A heavy chop throws lesser things 3 m and knocks them down, stunned 0.6 s. | BEHAVIOR | - | - |
| `cleaver.weight.3` | Butcher's Cleaver / Giantsbane | Hook; not in live wick planner. Cleaver chops 15% slower, but every chop on a champion is heavy. | BEHAVIOR | - | - |
| `cleaver.weight.4` | Butcher's Cleaver / Bonesplitter | Hook; not in live wick planner. Each chop sends a shockwave 3.5 m ahead, 1.8 m round, at 80% of the chop, staggering what it strikes; a frozen thing under half its life shatters. | BEHAVIOR | - | - |
| `cleaver.sweep.1` | Butcher's Cleaver / Butcher's Hook | Hook; not in live wick planner. Cleaver reaches 3.5 m, not 2.5 m, and drags what it strikes 1 m toward you. | BEHAVIOR | - | - |
| `cleaver.sweep.2` | Butcher's Cleaver / Next Cut | Hook; not in live wick planner. A chop that strikes 6 or more readies the next at once. | BEHAVIOR | - | - |
| `cleaver.sweep.3` | Butcher's Cleaver / Light Grip | Hook; not in live wick planner. Cleaver strikes 15% softer, but chops 25% faster. NUMBER reason: Only damage and pace/cost change; campaign cadence translates into Resolve cost. | NUMBER | CL3 | CL4 |
| `cleaver.sweep.4` | Butcher's Cleaver / Cross-Cut | Hook; not in live wick planner. Every chop cuts twice: across your front, then back again 0.25 s later, each cut at 65% of the chop. | BEHAVIOR | - | - |
| `iron_vow.hoard.1` | Iron Vow / Kept Count | Hook; not in live wick planner. The vow stores 35% of each blow on you, not 20%. NUMBER reason: Only increases the share of a blow already stored. | NUMBER | IV1 | IV3 |
| `iron_vow.hoard.2` | Iron Vow / Nothing Wasted | Hook; not in live wick planner. Each block in the brace stores 100% of the blow it turned. | BEHAVIOR | - | - |
| `iron_vow.hoard.3` | Iron Vow / Old Grudge | Hook; not in live wick planner. Iron Vow waits 14 s, not 10, but bursts at 5 times what it stored, not 3. NUMBER reason: Only increases cooldown and the stored-damage multiplier. | NUMBER | IV2 | IV4 |
| `iron_vow.hoard.4` | Iron Vow / Full Measure | Hook; not in live wick planner. The burst becomes a shockwave: it runs 14 m toward the cursor, 3 m wide, throwing everything aside, at 2 times the ring's blow. | BEHAVIOR | - | - |
| `iron_vow.brace.1` | Iron Vow / Steadfast | Hook; not in live wick planner. The brace holds 3.5 s, not 2. NUMBER reason: Only increases the existing brace duration. | NUMBER | IV5 | IV7 |
| `iron_vow.brace.2` | Iron Vow / Anvil | Hook; not in live wick planner. In the brace, blows on you are cut by 70%, not halved. NUMBER reason: Only increases damage reduction in the existing brace. | NUMBER | IV6 | IV8 |
| `iron_vow.brace.3` | Iron Vow / Iron March | Hook; not in live wick planner. You walk at full speed in the brace, and lesser things you walk into are shoved 2 m aside. | BEHAVIOR | - | - |
| `iron_vow.brace.4` | Iron Vow / Unyielding | Hook; not in live wick planner. Hold the key to keep the brace up to 6 s, then let go: the burst reaches 5 m, and 1 m more for each second you held. | BEHAVIOR | - | - |
| `iron_vow.challenge.1` | Iron Vow / Vigil Flame | Hook; not in live wick planner. The burst sears what it strikes for 3 s. | BEHAVIOR | - | - |
| `iron_vow.challenge.2` | Iron Vow / Like for Like | Hook; not in live wick planner. Each blow on you in the brace strikes its striker back for 50% of the blow. | BEHAVIOR | - | - |
| `iron_vow.challenge.3` | Iron Vow / Penance | Hook; not in live wick planner. The burst strikes 25% softer, but mends you for a third of what it stored, 15% of health at most. | BEHAVIOR | - | - |
| `iron_vow.challenge.4` | Iron Vow / Come Then | Hook; not in live wick planner. As the brace begins, everything within 12 m drops what it was doing and rushes you, archers and casters too, and the burst reaches 7 m, not 5. | BEHAVIOR | - | - |

## Inventory C: shared catalog lamps (Unions)

Each shared record appears once, not once per parent skill. Existing union/evolution primitives do not implement shared-lamp progression by themselves. The later ARPG two-key rule supersedes ONE_BUILD's older “both keep firing” assumption; reconcile that before building these catalog Unions.

| Catalog ID | Skills / lamp | Current definition and availability | Mark |
|---|---|---|---|
| `union.dawns_judgement` | Dawnpulse + Judgment Disc / Dawn's Judgment | Spec/built. The disc carries the dawn: it sears for 3 s, and wherever it strikes it breaks into light 2.2 m round, at 35% of the strike. | BEHAVIOR |
| `union.broken_country` | Sunder + Groundbreaker / Broken Country | Spec/new. Sunder's heavy line ends in Groundbreaker's heave: the earth rises there at 40%, stunning 0.4 s. | BEHAVIOR |
| `union.curfew` | Rebuke + Watch Bell / Curfew | Spec/new. Each toll rebukes what it draws: Rebuke's light strikes everything the bell pulls in, at 100% of a rebuke, once a toll. | BEHAVIOR |

## Replacement catalog: behavior and code route

Each NUMBER row assigns exactly two alternatives. Repeated idea IDs are choices for different placements in the same skill's wick: select a placement once, rather than duplicate the mechanic across strands. “Existing” means a combat primitive/rule exists; **every placement still needs future data/loader work**. “New” identifies the adapter, gate, or target query to build. This report builds none of them.

| System key | Current source and useful surfaces |
|---|---|
| T | [Turns.cs](../../godot/logic/Sim/Turns.cs): school/status, projectiles, Pulses, Ground, Again, HeavyEvery, and nonrecursive OnKillEcho/FireFrom. Suitability and dark-Turn rules still apply. |
| F | [Weapons.cs](../../godot/logic/Sim/Weapons.cs): FireSlash/ConeHit, FireNova, FireBounce, CountOf and evolution projectile paths. |
| S | [WardenSkills.cs](../../godot/logic/Sim/WardenSkills.cs): HeavyEveryOf, HeavyLineWhole, FireCrack/CrackOne/Heave, Toll/TollNow and draw vectors. |
| R | [WardenSkills.cs](../../godot/logic/Sim/WardenSkills.cs): RebukeOnBlow/RebukeStrike, nearest targets, champion RebukedAt and barrier grants. |
| W | [WardenLamps.cs](../../godot/logic/Sim/WardenLamps.cs), [WardenWicks.cs](../../godot/logic/Sim/WardenWicks.cs), [Battle.cs](../../godot/logic/Sim/Battle.cs): OnBlocked, LampsOnBlowLanded, LampsOnPerfect, WallAnswer, Barrier and HurtPlayer. Barrier-break is a proposed transition hook, not an existing generic event. |
| P | [Battle.cs](../../godot/logic/Sim/Battle.cs), [Entities.cs](../../godot/logic/Sim/Entities.cs): ProjectileHit, Bounces, SplitOnHit, hit sets, Chakram/Returning and bounce target selection. |
| Z | [Battle.cs](../../godot/logic/Sim/Battle.cs), [Entities.cs](../../godot/logic/Sim/Entities.cs): ApplyStatus, bleed slots, sear/burn, SpawnZone and zone membership. |
| Q | [PressedWarden.cs](../../godot/logic/Sim/PressedWarden.cs), [WardenWicks.cs](../../godot/logic/Sim/WardenWicks.cs): leap landing, charge steps/riders, Shove, Henge, brace/store/release, RuleGoaded and delayed rules. |
| C | [WardenWicks.cs](../../godot/logic/Sim/WardenWicks.cs): RuleBeforeCut/RuleAfterCut, RuleOnDeath, rupture/spatter and delayed CrossCut. |
| X | [Procs.cs](../../godot/logic/Sim/Procs.cs): combat trigger dispatch and nova effects; event-to-skill adapters can still be needed. |

The placement choice must supply each dependency: crescent and ground proposals below create their needed projectile or zone; barrier-break proposals require a build that can hold a barrier. Heavy-pulse proposals need one heavy-to-pulse adapter, never two copies when Dawn Rhythm already supplies it.

Future tuning belongs in data. Preserve hit attribution, champion/boss protections, terrain collision and target validity. Bound secondary echoes and resource loops. Selectors must respect campaign aim and held/pressed/kindled forms while working in the arena. A trigger must never add automatic player movement. These are selection constraints, not changes to presentation.

| Idea | Behavior replacement | System | Work needed |
|---|---|---|---|
| **SU1: Third Blow** | The Watch counts her cuts: every third swing throws the heavy ground line. | S: heavy line and count | Existing HeavyEveryOf / third_blow; wire the first live lamp. |
| **SU2: Back Furrow** | The heavy cut opens a second furrow behind her through the drowned. | S: heavy line and count | New backward firing through HeavyLineWhole. |
| **SU3: Three Furrows** | The heavy line forks through the press in three directions. | S: heavy line and count | New bounded fan of existing segment hits. |
| **SU4: Watch-Fire Edge** | The heavy line brands the drowned it crosses with sear. | S: heavy line and count | Existing burning_edge / SearEdge rule. |
| **SU5: Harvest of the Drowned** | A heavy cut finishing a pack arms the next cut as heavy; the bonus cannot arm itself. | S: heavy line and count | New kill counter and one-use latch on the existing heavy count. |
| **SU6: Open the Road** | The heavy furrow shoves drowned aside, opening a lane toward her aim. | S: heavy line and count | New perpendicular knockback using segment hits and Full Measure shove directions. |
| **SU7: Gathering Cut** | The backswing hooks drowned behind her into the next cut in front. | S: heavy line and count | New rear-target query using ConeHit and collision-safe Shove. |
| **SU8: Watch's Answer** | A block arms one ground line on her next held cut. | S: heavy line and count | New consumed OnBlocked latch; respect the current chain cancel beat. |
| **SU9: Ember Seam** | The heavy line leaves searing ember patches along its furrow. | S: heavy line and count | New capped segment sampler using SpawnZone and status. |
| **SU10: Last Cinder** | The first seared drowned a heavy line kills throws one short line onward from its body. | S: heavy line and count | New line-origin adapter using FireFrom and the nonrecursive echo guard. |
| **OB1: Watch Crescent** | Every third Oathblade cut sends the Watch's crescent through the front rank. | F + W + Z: cuts, answers, status | New count gate around the existing oathkeeper projectile. |
| **OB2: Shield and Edge** | A block owes Oathblade one answering cut at its legal cancel beat. | F + W + Z: cuts, answers, status | Existing OnBlocked / shield_and_edge / AnswerDue. |
| **OB3: The Drowned's Wake** | The first drowned Oathblade kills sends a crescent onward from its body. | F + W + Z: cuts, answers, status | New bounded FireFrom crescent echo; echoes cannot echo. |
| **OB4: Notched Watch Steel** | Every cut opens a bleed instead of gaining more direct damage. | F + W + Z: cuts, answers, status | Existing skill.status / ApplyStatus; introduces bleed, not a larger existing bleed. |
| **OB5: Unbroken Line** | An answering cut throws a piercing crescent through the front rank. | F + W + Z: cuts, answers, status | New answer-only adapter to the oathkeeper projectile. |
| **OB6: Turn to the Blow** | A blow on her arms the next answer toward its striker. | F + W + Z: cuts, answers, status | New source capture from LampsOnBlowLanded; consumed aimed answer. |
| **OB7: Blood at the Lamp** | The first drowned Oathblade kills bursts a searing ring from its body. | F + W + Z: cuts, answers, status | New kill/nova adapter; one nonrecursive burst per cut. |
| **OB8: The Wound Answers** | Cuts open a bleed; the first blow from a bleeding victim owes an answer against it. | F + W + Z: cuts, answers, status | Existing status payload plus a new source-and-bleed answer predicate, gated per target. |
| **OB9: Grave Seal** | Cuts bleed, and a cut finishes a bleeding drowned below its execution threshold. | F + W + Z: cuts, answers, status | Existing graveedge execute primitive; preserve boss restrictions. |
| **OB10: Two Watches** | An answering cut throws two narrow crescents on either side of her aim. | F + W + Z: cuts, answers, status | New answer-only CountOf projectile fan; split its damage budget. |
| **JD1: Found Wanting** | A disc kill earns another ricochet before the throw ends. | P + T: disc flight and Turns | New kill-to-Bounces adapter, capped per throw. |
| **JD2: Last Word** | The final ricochet breaks into a fan of ember shards. | P + T: disc flight and Turns | New last-bounce gate over SplitOnHit; child shards cannot split. |
| **JD3: Watch's Return** | After its last victim, the disc returns through the drowned toward her. | P + T: disc flight and Turns | New bounce-to-return transition using Chakram / Returning. |
| **JD4: Ember Verdict** | The disc becomes fire and burns everything it strikes. | P + T: disc flight and Turns | Existing fire Turn school/status conversion. |
| **JD5: Name the Strong** | Ricochets seek the strongest drowned nearby instead of the nearest. | P + T: disc flight and Turns | New ordering in the existing bounce target query. |
| **JD6: Dash Verdict** | A perfect dash arms a second disc on the next throw. | P + T: disc flight and Turns | New consumed LampsOnPerfect-to-CountOf latch. |
| **JD7: First Ward** | Only the first strike of a throw lights a barrier around her lamp. | P + T: disc flight and Turns | New per-throw hit gate using Barrier, with a held cap. |
| **JD8: Chain the Marked** | The disc's first hit sears; ricochets prefer seared drowned, with ordinary-target fallback. | P + T: disc flight and Turns | Existing sear payload plus new status-aware bounce ordering; no new mark system. |
| **DA1: Dawn Rhythm** | A heavy blow kindles Dawnpulse in addition to its normal firing. | F + T + Z + W: pulses and ground | Existing combat-trigger/nova primitives; add a bounded heavy-to-pulse adapter. |
| **DA2: Where the Blow Falls** | Heavy blows fire a pulse at their victim; ordinary pulses still open around her. | F + T + Z + W: pulses and ground | New bounded heavy-to-pulse/origin adapter through FireFrom / FireNova; preserve timer pulses. |
| **DA3: Light on the Ford** | A pulse leaves daylight beneath the drowned it catches. | F + T + Z + W: pulses and ground | Existing sunbreak / GroundOnHit primitive; one patch per pulse. |
| **DA4: Morning Road** | A dash lays the pulse's daylight behind her. | F + T + Z + W: pulses and ground | New capped route sampler through dash hooks and SpawnZone. |
| **DA5: Ember at the Threshold** | Each pulse leaves fading daylight; the first drowned entering it is seared, once per creature. | F + T + Z + W: pulses and ground | Existing ground primitive plus a new entrant set on its status-bearing zone. |
| **DA6: Last Dawn** | A drowned killed by the pulse releases one pulse from its body. | F + T + Z + W: pulses and ground | Existing nonrecursive OnKillEcho / FireNova Turn. |
| **DA7: Dawn upon Dawn** | Each pulse returns in a short series instead of one ring. | F + T + Z + W: pulses and ground | Existing Pulses / PulseGap Turn; share one damage budget. |
| **DA8: Light Answers** | For a short window after a pulse, the next striker is seared. | F + T + Z + W: pulses and ground | New consumed retaliation window using the blow source and ApplyStatus. |
| **DA9: Broken Lamp** | A barrier breaking fires Dawnpulse once at her feet. | F + T + Z + W: pulses and ground | New shield-transition hook to FireNova; prevent barrier feedback. |
| **GR1: Twin Cracks** | Two cracks run toward the drowned instead of one. | S + Q + Z: cracks and heaves | Existing FireCrack / twin; retain campaign cursor aim. |
| **GR2: Second Heave** | The same ground heaves again after the first strike. | S + Q + Z: cracks and heaves | Existing ScheduleHeave / Again Aftershock Turn. |
| **GR3: Sinking Ford** | Drowned slide toward the heave's heart before it lands. | S + Q + Z: cracks and heaves | New wind-up phase using collision-safe Shove. |
| **GR4: Crow's Foot** | A crack reaching a pack branches toward the next, stopping after a bounded number of packs. | S + Q + Z: cracks and heaves | New visited-pack set and branch queue around CrackOne / DensestHostile. |
| **GR5: Cold Ford** | The open crack becomes slowing ground that catches those crossing it. | S + Q + Z: cracks and heaves | New segment-to-zone adapter using SpawnZone / slow. |
| **GR6: Backwash** | The heave opens another crack backward from its landing point. | S + Q + Z: cracks and heaves | New reversed origin and direction through CrackOne. |
| **GR7: Upheaval** | The heave throws lesser drowned into the air instead of only stunning them. | S + Q + Z: cracks and heaves | Existing Heave / upheaval / AirUntil; preserve boss immunity. |
| **GR8: Down They Come** | The heave throws one lesser drowned airborne; its landing splashes an impact into its neighbors. | S + Q + Z: cracks and heaves | New airborne-landing callback borrowing Ninepins; one splash per cast. |
| **GR9: Chain the Captain** | The crack chooses a champion in the aimed pack and heaves under it. | S + Q + Z: cracks and heaves | New target override over CastAt / pack center, with ordinary-pack fallback. |
| **GR10: Ember Fault** | The heave leaves its ground burning beneath the drowned it lifted. | S + Q + Z: cracks and heaves | Existing CrackOne / Ground Linger Turn. |
| **RE1: Last Rebuke** | A drowned killed by Rebuke answers once more from its body. | R + T + Z: reactive light | Existing nonrecursive OnKillEcho / FireReactive Turn. |
| **RE2: Shield of Morning** | Each struck drowned feeds a capped barrier back to her lamp. | R + T + Z: reactive light | Existing RebukeStrike / BarrierEach / BarrierMost; adds a grant, not a larger existing grant. |
| **RE3: Broken Ward** | A barrier breaking releases one Rebuke around her. | R + T + Z: reactive light | New shield-transition event and radius target set; keep champion gates. |
| **RE4: The Long Answer** | Rebuke runs through its striker into the drowned behind it. | R + T + Z: reactive light | New target set from the actual striker using segment hits. |
| **RE5: Tidings** | Rebuke leaps from its striker through a bounded chain of drowned. | R + T + Z: reactive light | New chain adapter using existing queries; retain RebukedAt. |
| **RE6: Still the Captain** | Rebuke interrupts a champion's attack once per champion gate. | R + T + Z: reactive light | New Stun / Interrupt hook; bosses use stagger, never a stun lock. |
| **RE7: Open Rebuke** | The answer catches every drowned in a ring around her instead of a nearest-target list. | R + T + Z: reactive light | New HostilesInRadius target-set replacement; retain champion protection. |
| **RE8: Ember Answer** | Rebuke takes fire and leaves its striker burning. | R + T + Z: reactive light | Existing fire Turn school/status conversion. |
| **WB1: Second Watch** | The bell sounds a second toll after the first. | S + W + Q: bell and wall | Existing Pulses / FireToll Turn, including reduced barrier share. |
| **WB2: Muster at the Gate** | The bell gathers drowned before her shield instead of all around her. | S + W + Q: bell and wall | New Toll destination vectors; bosses still resist the pull. |
| **WB3: The Watch Holds** | A toll closes a ring that holds lesser drowned on their own side of it. | S + W + Q: bell and wall | New bell adapter around the existing Henge membership rule. |
| **WB4: Drowned Toll** | The first drowned the bell kills rings one toll from its body. | S + W + Q: bell and wall | New suitability/origin adapter using Toll / FireFrom; nonrecursive echo guard. |
| **WB5: Iron Undertow** | The pull also lays a slow on drawn drowned. | S + W + Q: bell and wall | Existing Toll / iron rule; introduces slow instead of extending an existing slow. |
| **WB6: In Their Wake** | A drawn champion hauls nearby lesser drowned into the pull. | S + W + Q: bell and wall | New capped neighbor-inclusion pass; deduplicate Toll targets. |
| **WB7: Alarm** | When the wall spends its Stones, the bell rings once. | S + W + Q: bell and wall | New deferred WallAnswer-to-TollNow hook; prevent toll-to-wall recursion. |
| **WB8: Long Toll** | For a short window, each new drowned crossing the bell's reach is drawn once. | S + W + Q: bell and wall | New entrant set in TickRules; one draw per creature per window. |
| **WB9: Watch at Her Back** | A perfect dash leaves one deferred toll where she stood. | S + W + Q: bell and wall | New origin snapshot from LampsOnPerfect to Toll; no extra movement. |
| **SC1: Driven Home** | The charge ends with a slam into drowned around the shield. | Q + W + F + Z: charging shield | Existing ChargeStep / pile_driver endpoint slam. |
| **SC2: Swept Along** | The shield carries lesser drowned to the charge's end and drops them there. | Q + W + F + Z: charging shield | Existing RuleCarryRiders / ChargeStep; retain rider and boss caps. |
| **SC3: Landslide** | Carried drowned tumble onward through the next rank when the charge ends. | Q + W + F + Z: charging shield | Existing bounded rider/body-line rule in WardenWicks. |
| **SC4: Ember Road** | The charge leaves short patches of ember behind it. | Q + W + F + Z: charging shield | New capped TickRush trail sampler using SpawnZone. |
| **SC5: Watch's Front** | The first frontal block after the charge throws a cone of light at its striker. | Q + W + F + Z: charging shield | New consumed RuleShieldBlock / OnBlocked-to-ConeHit adapter; never starts another charge. |
| **SC6: Broken Shield** | The charge's own barrier breaking releases one searing ring. | Q + W + F + Z: charging shield | New barrier-ownership and break gate using nova; prevent recursive barrier rewards. |
| **HL1: Second Quake** | The landing ring heaves again after the first impact. | Q + S + F + Z: leap | Existing RuleLeapLanded / ScheduleHeave aftershock. |
| **HL2: Split the Ford** | The landing opens a forward fault line instead of a larger ring. | Q + S + F + Z: leap | New landing-to-segment adapter using HeavyLineWhole; retain aim. |
| **HL3: Into the Thick** | A leap aimed near a pack lands in its heart. | Q + S + F + Z: leap | Existing RuleLeapAim / pack center; retain wall/range checks. |
| **HL4: Two Banks** | Takeoff leaves one small impact ring behind; landing makes the other. | Q + S + F + Z: leap | New takeoff nova; divide the landing budget. |
| **HL5: Ember Footprints** | The leap leaves ember at takeoff and landing, catching pursuing drowned. | Q + S + F + Z: leap | New two-endpoint SpawnZone placement; no airborne trail required. |
| **HL6: Henge** | Standing stones contain lesser drowned around the landing. | Q + S + F + Z: leap | Existing RuleLeapLanded / henge boundary; no permanent terrain. |
| **HL7: Unending Bound** | A killing landing offers a short window for another deliberate leap press. | Q + S + F + Z: leap | Existing boundUntil / boundChain; never leap without input. |
| **HL8: The Landing Answers** | The next held swing after landing cuts twice through the drowned. | Q + S + F + Z: leap | New one-use landing latch, reusing delayed CrossCut. |
| **CL1: Spatter** | A bleeding drowned's death splashes bleed onto its neighbors. | C + F + S: Cleaver | Existing RuleOnDeath / ApplyStatus; bound secondary deaths. |
| **CL2: Rupture** | A chop tears the remaining bleed out at once and splashes it into the pack. | C + F + S: Cleaver | Existing RuleBeforeCut / bleed removal; spend the wound once. |
| **CL3: Cross-Cut** | A chop cuts back across her front after the first cut. | C + F + S: Cleaver | Existing crossCuts / CrossCut; preserve split damage. |
| **CL4: Butcher's Hook** | Each chop hooks drowned toward her next cut. | C + F + S: Cleaver | Existing RuleAfterCut / Shove; retain boss restrictions. |
| **CL5: Overhand** | Every third chop becomes heavy, opening the Watch's heavy-hit links. | C + F + S: Cleaver | Existing overhand / HeavyEveryOf; changes firing identity. |
| **IV1: Nothing Wasted** | The brace stores blows her shield blocks, not only those reaching her. | Q + W + F + Z: vow | Existing RuleOnBlocked / BraceRun.Stored new-source rule. |
| **IV2: Full Measure** | The stored blow releases as an aimed shockwave instead of a ring. | Q + W + F + Z: vow | Existing full_measure rule; retain cursor aim. |
| **IV3: Vigil Flame** | The released vow sears the drowned it strikes. | Q + W + F + Z: vow | Existing vigil_flame status rule. |
| **IV4: Like for Like** | A blow taken in the brace strikes its own striker back. | Q + W + F + Z: vow | Existing VowTake / striker; retain attribution and reflection gates. |
| **IV5: Come Then** | The brace calls drowned off their attacks and toward her shield. | Q + W + F + Z: vow | Existing RuleGoaded AI override; preserve boss restrictions. |
| **IV6: Iron March** | She carries the brace through lesser drowned, shoving them aside. | Q + W + F + Z: vow | Existing RuleMoveMul / TickRules contact-once shove. |
| **IV7: Narrow Gate** | An early release spends the vow in a cone toward the cursor instead of a ring. | Q + W + F + Z: vow | New early-release branch extracted from TickVow, then ConeHit; no second burst. |
| **IV8: The Ward Breaks** | Losing her barrier while braced releases the stored vow once. | Q + W + F + Z: vow | New shield-transition hook into an extracted TickVow release; never starts or extends a brace. |

## Ten strongest choices, ranked

Ranked for a readable change in play, Warden identity, useful decisions and a credible code route. The first is deliberately teachable before ten minutes; later picks require their skill and prerequisites, not a first-run availability promise.

| Rank | Pick | Why it earns this place | Placement / dependency |
|---|---|---|---|
| 1 | **SU1: Third Blow** | The held swing reaches the next rank of drowned sooner. It teaches a changed combat rule with code already present. | Replace live Sunder's first Stroke +10% damage lamp at the first road level-up (ARPG 5a); light the held point where she stands. No Turn or lamp-post prerequisite. Capture a fresh Low Ford start and require the first changed heavy count inside 10 minutes; this audit does not claim that gate has passed. |
| 2 | **SU6: Open the Road** | The heavy cut makes an escape lane through the drowned. Aim and positioning matter beyond throughput. | Replace Sunder's Wide Turn; segment hit plus directional shove. Move enemies, never the player. |
| 3 | **GR2: Second Heave** | A delayed second strike rewards planning around the chosen ground. The delayed impact and stun exist. | Bring Aftershock forward to a live NUMBER lead-in; give its old Turn a distinct endpoint rather than duplicate the mechanic. |
| 4 | **WB2: Muster at the Gate** | The Watch gathers drowned before the shield, setting up a deliberate cut or charge. | Replace a bell size lamp, especially Arm's Length; change Toll destination vectors, preserving boss pull immunity. |
| 5 | **CL2: Rupture** | A chop spends a wound and carries its payoff into the pack. This is a spend moment rather than faster cadence. | Replace Bled Dry or Laid Open; bleed removal and splash exist. A preceding choice must introduce or preserve bleed. |
| 6 | **RE4: The Long Answer** | A blow on the shield answers through its striker into drowned behind it. Position shapes the retaliation. | Replace a Rebuke size lamp or Brought Low; use the actual striker, segment hits and champion gates. |
| 7 | **IV2: Full Measure** | Stored punishment becomes an aimed road through the pack, changing the release decision. | Replace Old Grudge; the shockwave rule exists. Keep release inside current pressed/kindled rules. |
| 8 | **JD2: Last Word** | The final ricochet has a distinct end: a bounded fan of ember shards. It changes where to send a disc. | Replace Kept Aloft or a projectile-speed lead-in; add the last-bounce gate over split projectiles. |
| 9 | **DA2: Where the Blow Falls** | Dawn opens at the heavy blow's victim, changing a self-centered pulse into an aimed combination. | Replace Keep Time after Dawn Rhythm; carry impact coordinates through FireFrom and keep ordinary pulses. |
| 10 | **HL6: Henge** | A landing divides the pack into drowned inside and outside the Watch's stones, changing the next decision. | Replace Crater when the leap wick is wired; the boundary rule exists. Retain lesser-foe restrictions and both cast modes. |

Choose one early Sunder mechanic, one grouping mechanic and one payoff for that grouping. The alternatives remain a menu for the classes lead, not a request to add everything. No player-facing wording, visual treatment or balance values are approved by this report.

## Coverage and remaining decisions

Reproduce coverage by expanding each wicks.json skills[skill].strands to positions 1-4, resolving own before library strands and shared lead-ins. Compare that (skill, lamp ID) multiset with Inventory A. Compare every skill_lamps.json lamps[].id with Inventory B and every unions[].id with Inventory C. Require multiplicity one, and require two defined, distinct replacement IDs on each NUMBER row and neither on BEHAVIOR rows. Totals: **84 + 132 + 3 = 219 rows; 87 NUMBER with 174 replacement assignments; 132 BEHAVIOR.** Shared idea definitions prevent the same mechanic being mistaken for multiple independent recommendations.

This is a source audit. No Godot play run or visual judgment was performed. No proposed mechanic is claimed to be tested in play. The C# suite is the separate commit gate, reported in the handoff. The classes lead still selects placements, resolves baseline mismatches and progression wiring, and playtests the first-ten-minute gate.
