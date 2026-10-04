> Research notes for `docs/bosses/`, kept as written. Where the **Verification** section at the end corrects a claim, the correction stands; `RESEARCH.md` uses the corrected version.

# B1 - Boss fights in Brotato, 20 Minutes Till Dawn and HoloCure

Strand B1 of the boss-fight research for Survivor Unchained. Every factual claim carries a URL. "(secondary)" marks a claim seen only in a search-result summary, not on the page itself. Where two pages on the same wiki disagree, both figures are given.

## Lessons (summary)

| | Brotato | 20 Minutes Till Dawn | HoloCure |
|---|---|---|---|
| Boss timing | Wave 20 only (90 s wave); elites waves 11-18 | 5:00 and 15:00; elites 3:00, 11:20, 16:00; **no 20:00 boss** | Mini-boss every 2 min; bosses 10:00 and 20:00 |
| Win condition | Kill all bosses **or survive the 90 s** | Survive to 20:00 | Kill the 20:00 boss(es); no time-out |
| Phases | Mutations at **HP% or time, whichever first** | Single pattern | Low-HP enrage with coloured aura (late bosses) |
| Horde during boss | Continues; some elites spawn adds | Continues (dev later planned to stop it) | **Cleared**, replaced by themed escort army |
| Arena | Fixed arena | **Electric barrier for 60 s** on open maps | Open; spawn-zone damage circle |
| Over-strong builds | %-HP effects cut 10x vs bosses | Endless multipliers made additive; summon cap | Bosses immune to instant KO / knockback |
| Endless | Both bosses every 10th wave; exponential factor | +5x base HP per 10 min; boss attack speed +0.25 | Kill screen after 30:00, YAGOO mini-boss waves |

1. **Phase triggers should be "HP threshold OR elapsed time, whichever comes first"** (Brotato). Weak builds still see every phase; strong builds skip ahead. It costs almost nothing to implement.
2. **Give the boss fight a fallback end so a weak build is never stuck.** Brotato's 90 s timer counts as a win. HoloCure has none, and players kite for minutes. For a 30:00 finale, a survive-the-clock fallback (perhaps with a lesser reward than a kill) avoids the dead end.
3. **Clear or replace the horde when the boss arrives.** HoloCure wipes the field and sends a themed escort. 20MTD's developer later concluded "Normal enemies will not spawn during boss fights anymore to prevent too much clutter". Readability complaints in all three games come from boss attacks hidden in trash and in the player's own effects.
4. **Use one consistent telegraph vocabulary across trash, elites, bosses and hazards** (HoloCure: red circle, !! + sound, red line, shadow, cone, screen darken, flaming aura). Telegraphed hazards must deal no damage until the telegraph completes (Brotato's Invoker bug), and hazards must be cleaned up when the boss dies (Brotato's Eel bug).
5. **Use a temporary arena wall to force a duel on an open map** (20MTD: 60 s electric barrier). It turns a kite-able boss into a fight without a scene change.
6. **Cap the effects that break bosses rather than making bosses immune.** Brotato cuts %-current-HP crit and burn from 10% to 1% vs bosses and elites. HoloCure makes bosses immune to instant KO. 20MTD changed stacking multipliers to additive in Endless. Anti-boss stats (Brotato's "% damage against bosses") give builds a legitimate way to specialise.
7. **Mid-run elites are where runs die; announce them.** Brotato players call wave 11-12 elites "run killers" harder than the final boss, and movement-gated elites read as unfair. Brotato shows upcoming elite waves in the shop; players asked for which elite it will be too.
8. **Escalate by recombination.** HoloCure's hard stages bring back the previous finale as a 10:00 event, then a much larger new finale. Multi-boss finales (trio, five) with a healer add kill-order decisions.
9. **Make the boss impossible to miss, and the win a clear beat.** One HoloCure player never found the 20:00 boss. Its victory is a hard black-out to a "stage cleared" card, and bosses drop a box with a special animation for rare contents. A boss-themed weapon unlock (Fubuzilla gives Fan Beam) makes the kill matter beyond the run.
10. **Endless after the win needs its own ramp.** HoloCure's post-30:00 "kill screen" uses mini-boss YAGOO waves and exponential stats; Brotato spawns both bosses every 10th wave with a quadratic-then-steeper factor; 20MTD raises boss attack speed every 10 minutes. All three state the aim is to end runs that would otherwise last hours.

---

## 1. Brotato (Blobfish, 2023)

### 1.1 Structure: where the bosses sit

- A run is 20 waves. Wave 1 lasts 20 s and each wave adds 5 s up to a 60 s cap; **wave 20, the boss wave, lasts 90 s** (https://brotato.wiki.spellsandguns.com/Waves).
- **Bosses appear only on wave 20.** One of the two base-game bosses (Predator or Invoker) is picked at random on Danger 0-4. On Danger 5 **both** spawn, "with 75% of their original health" (https://brotato.wiki.spellsandguns.com/Enemies; https://brotato.wiki.spellsandguns.com/Danger_Levels). The 25% cut for Danger 5 bosses arrived in Patch 0.5.11c ("Bosses on Danger V now have 25% less health") (https://brotato.wiki.spellsandguns.com/Patch_0.5.11c).
- **Win condition is "kill or outlast".** The boss pages say "the player will win the run when all bosses on the wave have been killed **or the wave that the boss is on ends due to time**" (https://brotato.wiki.spellsandguns.com/Predator; https://brotato.wiki.spellsandguns.com/Invoker). So the 90 s wave timer is a hard cap on fight length: a weak build can win by surviving; a strong build ends the wave early by killing. Running out the timer is a known community tactic (secondary: search summary of https://steamcommunity.com/app/1942280/discussions/0/3364775865383231843).
- In Endless the 90 s still applies but killing the boss does not end the wave (https://brotato.wiki.spellsandguns.com/Endless_Mode). Patch 1.1 made "Dying or ending a run after the final wave's bosses are dead now counts as a win in endless mode" (https://brotato.wiki.spellsandguns.com/Patch_1.1.*.*).

### 1.2 The wave-20 bosses

The "mutation" system is the core idea: **each phase change triggers at an HP threshold OR a timer, whichever comes first.** This guarantees that every player sees the later phases, even a weak build that can't push HP down, and that a strong build skips ahead by burst.

| Boss | HP | Speed | Damage | Mutation 0 | Mutation 1 | Mutation 2 |
|---|---|---|---|---|---|---|
| Predator | 29,900 (D0-4) / 31,395 (D5) per the boss infobox; 29,250 / D5 30,712 per the Enemies table | 300 | 29.5 (infobox); "Contact 30, Projectile 23; D5 41C, 32P" (Enemies table) | Chases and dashes; ring of projectiles orbiting the boss | **50% HP or 45 s left**: stops dashing, emits projectiles in every direction "every so often" | - |
| Invoker | as Predator | 200 (M0-M1), 500 (M2) | 19.5 (M0-M1), 73 (M2) per infobox | Every 2 s creates an area of projectiles around the player that "spawn after a second of priming" | **60% HP or after 30 s** (boss page) / 75% HP or 30 s (Enemies table): more projectiles over a much wider area | **40% HP or after 60 s**: speed +150% (200 to 500), runs around the arena, rings the player with projectiles |

Sources: https://brotato.wiki.spellsandguns.com/Predator, https://brotato.wiki.spellsandguns.com/Invoker, https://brotato.wiki.spellsandguns.com/Template:Boss_Data, https://brotato.wiki.spellsandguns.com/Enemies.

The Abyssal Terrors DLC adds two more wave-20 bosses for its Abyss zone, both on three-mutation schedules (https://brotato.wiki.spellsandguns.com/Enemies):

| DLC boss | HP | Speed | M0 | M1 | M2 |
|---|---|---|---|---|---|
| Dead Whale | 31,625 (D5 33,206) | 200 | Wanders; 3 waves of 6 projectiles at the player | 70% HP / 20 s: chases, charges, sprays mixed-speed projectiles in all directions | 40% HP / 45 s: charges more often, large projectile ring around itself |
| Eel | 31,625 (D5 33,206) | 150 | Chases, stream of projectiles | 70% HP / 25 s: wanders, spawns a projectile spiral centred on the player that closes in | 40% HP / 55 s: as M1 plus four orbiting projectile lines |

Notes on the numbers:
- **HP formula.** Patch 1.0.0.3 changed boss HP from "28,000 + 100 per wave" to "**15,000 + 750 per wave**" (https://brotato.wiki.spellsandguns.com/Patch_1.0.0.3). At wave 20 that is 30,000 before danger modifiers; the per-wave term is what makes Endless bosses (waves 30, 40...) tankier. The wiki's 29,250/29,900 figures are close but not consistent with each other; the patch-note formula is the primary source.
- **Danger HP.** Danger 3/4/5 add +12%/+26%/+40% enemy HP and damage (totals, not cumulative); Nightmare adds +60% HP/damage and +10% speed (https://brotato.wiki.spellsandguns.com/Danger_Levels). D5 bosses: 0.75 x 1.40 = 1.05x base HP each, but there are two of them.
- **Early damage tuning.** "Bosses deal less damage" (0.5.9); "Wizard boss now waits 2 seconds before starting to cast spells" (0.5.11c); "Improved the hitbox of the Wizard boss projectiles (shouldn't damage you when the ball is not fully out anymore)" (0.5.10) (https://brotato.wiki.spellsandguns.com/Patch_0.5.9, https://brotato.wiki.spellsandguns.com/Patch_0.5.11c, https://brotato.wiki.spellsandguns.com/Patch_0.5.10). "Wizard" appears to be the early-access name for Invoker (inference from the matching behaviour, not confirmed).
- **Telegraph integrity bug.** Patch 1.1: delayed "slash and pillar projectiles could deal damage during the initial frame that they were spawned. This resulted in Bosses like Invoker dealing instant unavoidable damage to the player. This is now fixed." Also: killing the Eel too fast left its orbiting projectiles "invisible and persisting after its death... randomly taking damage without being able to see the source" (https://brotato.wiki.spellsandguns.com/Patch_1.1.*.*). Both are lessons: a telegraphed hazard must be harmless until the telegraph completes, and a boss's hazards must be cleaned up on death.

### 1.3 Elites and elite/horde waves (the mid-run "mini-bosses")

- Danger 0-1: no special waves. Danger 2-3: one elite **or** horde wave at wave 11 or 12. Danger 4-5: three special waves at 11/12, 14/15 and 17/18; the third is **always** an elite. Each of the first two is 60% elite / 40% horde. **Upcoming special waves are shown in the shop**, and since 1.1 also in the pause menu (https://brotato.wiki.spellsandguns.com/Elite_and_Horde_Waves; https://brotato.wiki.spellsandguns.com/Patch_1.1.*.*).
- **An elite cannot repeat within a run** (https://brotato.wiki.spellsandguns.com/Elite_and_Horde_Waves).
- Elite HP is **1 + 750 per wave** (700 for Monk and Turtle), damage 1 + 1.5 per wave (https://brotato.wiki.spellsandguns.com/Template:Elite_Data). So a wave-11 elite has about 8,251 HP before modifiers and a wave-18 elite about 13,501. Elites on wave 11-12 spawn at **75% HP**: patch 0.6.1.6 changed the reduction from -15% to -25% (https://brotato.wiki.spellsandguns.com/Danger_Levels; https://brotato.wiki.spellsandguns.com/Patch_0.6.1.6).
- **Reward:** a Legendary loot crate with a guaranteed tier-4 item, which heals 100 HP on pickup instead of 3 (https://brotato.wiki.spellsandguns.com/Danger_Levels). Patch 0.8.0.3 gave bosses legendary crates too (https://brotato.wiki.spellsandguns.com/Patch_0.8.0.3).
- Horde waves: extra enemies, each dropping 35% fewer materials, net more income (https://brotato.wiki.spellsandguns.com/Elite_and_Horde_Waves).

Elite roster (all HP/time mutations; https://brotato.wiki.spellsandguns.com/Enemies and individual pages):

| Elite | Speed | M0 | M1 trigger and pattern | M2 |
|---|---|---|---|---|
| Rhino | 250 | Charges every 2 s, side-firing projectiles during the charge | 60% / 25 s: charges every 1.3 s, shorter, +2 projectiles at charge start | - |
| Butcher | 200 | 4 slashes every 1.25 s around the player, pointed at them | 60-70% / 25 s: 8 slashes per second in random pattern over a large area | 40% / 40 s: 3 slashes every 0.6-0.75 s, 33% less damage |
| Monk | 350 | Spawns 15 Slasher Eggs | 10 s: 5 projectiles per second at the player | 30 s: flees for 10 s spawning Tentacles, then back to M1 (loops) |
| Croc | 350 | Charges every second, 2 slashes around itself | 50-60% / 25-30 s: charges every second, ring of projectiles around the player | - |
| Colossus | 300 | Chases; 50 moving projectiles in a big random area every second | 60% / 25 s: random walk; ring of projectiles around player that moves every 0.5 s | - |
| Mantis | 250 | Chases; 6 slashes every 1.25 s around itself | 60% / 25 s: charges every 1.3 s with slashes | - |
| Mother | not found | Chases; 4 slashes per second at player | 60% / 25 s: flees; 2 slashes every 0.25 s in random pattern, each spawning a Fin Alien | - |
| (DLC) Spider Crab, Prisoner, Giant, Turtle, Megalodon, Jellyfish, Bat, Isopod, Impaled Worm | 200-350 | various | Mostly 60% / 25 s; Spider Crab 85% / 12 s; Prisoner 75% / 20 s | Giant 40% / 55 s; Prisoner 40% / 40 s; Spider Crab 50% / 35 s |

Three elites (Monk, Mother, Spider Crab) use the horde: they **spawn adds** (Slasher Eggs, Tentacles, Fin Aliens, crabs). Patch 1.0.0.3: "Enemies spawned by elites and bosses are now affected by modifiers to the number of enemies" (https://brotato.wiki.spellsandguns.com/Patch_1.0.0.3), so items that shrink or grow the horde also shape boss adds.

### 1.4 Telegraphs and readability

- Elite and boss hazards are mostly **delayed area projectiles**: the Invoker's areas "spawn after a second of priming" (https://brotato.wiki.spellsandguns.com/Invoker); slashes and pillars likewise deal damage after a delay, a rule enforced by the 1.1 fix above.
- Bosses got HP bars in 0.5.10, and an option to **hide** boss health bars was added in 0.6.0.7 (https://brotato.wiki.spellsandguns.com/Patch_0.5.10; https://brotato.wiki.spellsandguns.com/Patch_0.6.0.7).
- Patch 1.1 "Added schematics for every Elite attack in the Codex": an in-game diagram of each attack, so players can learn the patterns outside a run (https://brotato.wiki.spellsandguns.com/Patch_1.1.*.*).
- Spawn warnings: 0.5.11c fixed "some enemies would spawn too close to the player without enough warning time" (https://brotato.wiki.spellsandguns.com/Patch_0.5.11c), so spawn-telegraph time is treated as a fairness guarantee.
- "Bosses and charging enemies can more reliably push other enemies out of the way to avoid being stuck" (1.1) (https://brotato.wiki.spellsandguns.com/Patch_1.1.*.*): a boss must not get wedged in its own horde.

### 1.5 Coping with weak and absurd builds

- **Time-or-HP mutations** (above) mean a weak build still sees the full pattern on schedule, and the 90 s timer means it can still win.
- **Percentage-damage effects are cut 10x for bosses and elites.** Crits that deal "10% of an enemy's current health as bonus damage (1% for bosses and elites)"; burning that deals "10% of current enemy HP (1% for bosses and elites)" (https://brotato.wiki.spellsandguns.com/Patch_0.8.0.3; https://brotato.wiki.spellsandguns.com/Patch_1.1.0.0). This blocks the one class of effect that would trivialise a 30k-HP target.
- **Explicit anti-boss stats** are given to builds instead: "% damage against bosses" is a secondary stat; Silver Bullet gives +25% vs elites/bosses; Jack's boss bonus went +50% to +75%; the Mutation item went +75% to +125% (https://brotato.wiki.spellsandguns.com/Elite_and_Horde_Waves; https://brotato.wiki.spellsandguns.com/Patch_1.0.0.3; https://brotato.wiki.spellsandguns.com/Patch_1.1.0.0). An achievement/challenge asks you to "Kill a boss or an elite in less than 15 seconds" (https://brotato.wiki.spellsandguns.com/Patch_0.8.0.3), turning a phase-skip into a goal.
- Effects that "damage a random enemy" were fixed to hit bosses (0.6.0.7) (https://brotato.wiki.spellsandguns.com/Patch_0.6.0.7): bosses must not be immune to whole build archetypes by accident.
- **Endless**: every 10th wave (30, 40, 50...) spawns **both** bosses regardless of Danger; +1 elite per elite/boss wave per 10 waves past 20; elites and bosses no longer guarantee crates, and drop ordinary ones (https://brotato.wiki.spellsandguns.com/Endless_Mode). The Endless Factor = (n(n+1)/2)/100 x mult, where n = wave-20 and mult = 2.0 + 0.2 per wave past 35. Enemy damage scales by (1 + factor) and max HP by (1 + 2.25 x factor). Damage is +110% at wave 30 and +630% at wave 40 (https://brotato.wiki.spellsandguns.com/Endless_Mode). The page's stated aim: "This ensures that all runs come to an end."
- Accessibility sliders scale enemy damage and HP 25-200% and speed 25-150%; the result is shown next to Danger on the pause and victory screens (https://brotato.wiki.spellsandguns.com/Danger_Levels).

### 1.6 Player opinion

- **Elites are the real wall, not the final boss.** "Elites on wave 11-12 are run killers. Consistently a lot harder to get through than the wave 20 boss duo every single time" (Rushin); elites in wave 11 "are often a death sentence for a lot of characters. That's a poor game design choice" (Chatpelier); "I never died on the wave 20 bosses except the first 2 times I encountered them" (Chatpelier). Source: https://steamcommunity.com/app/1942280/discussions/0/4631483020295041397.
- **Movement-gated elites.** "The new elites, Croc and Colossus, are definitely over powered than other guys!"; "I think Mother and Colossus are the hardest elites currently, maybe Butcher aswell" (ThunfischGott); "If your move speed is under 15% you won't move fast enough to sidestep on D5. He'll constantly dash faster than you can move" (Swamp Trash); one player answered that "You can dodge fine with half that speed bonus if you anticipate/bait its movement"; another asked for "Tooltips regarding which elite is going to spawn" (https://steamcommunity.com/app/1942280/discussions/0/6363075944119837726). Players also say the Gladiator elite "just destroys ranged builds" (https://steamcommunity.com/app/1942280/discussions/0/4631483020295041397).
- A critical review calls elites "too spongey" with "annoying attack patterns" (secondary: search summary of https://opencritic.com/user296d44c574/review/15137/brotato).
- A reviewer's framing of the loop: "Whenever it feels too easy, the wave ends and things get harder" (https://adrianhon.substack.com/p/brotato).

**Takeaways for Survivor Unchained:** (a) HP-or-time phase triggers are cheap and robust; (b) a survive-the-clock fallback win removes the "my build can't kill it" dead end; (c) a mid-run elite that is a stat check on movement speed reads as unfair. Announce it in advance, as Brotato's shop does, and don't make one stat mandatory; (d) cap %-HP effects on bosses rather than making bosses immune to them.

---

## 2. 20 Minutes Till Dawn (flanne, 2022-23)

### 2.1 Structure: no final boss, the clock is the finale

- In Standard Mode "the player simply has to survive for 20 minutes"; Quickplay is the first 10 minutes of Standard (https://20-minutes-till-dawn.fandom.com/wiki/Endless_mode). **There is no boss at 20:00.** The run ends at dawn, and the last minutes are a horde peak, not a duel.
- **Bosses spawn at 5:00 and 15:00.** Mini-bosses ("elites") spawn at 3:00, 11:20 and 16:00 (18:00 in Temple). The spawn tables list `start=300` and `start=900` for bosses, and `start=180`, `680` and `960` (Temple `1080`) for elites (https://20-minutes-till-dawn.fandom.com/wiki/Forest; https://20-minutes-till-dawn.fandom.com/wiki/Temple; https://20-minutes-till-dawn.fandom.com/wiki/Pumpkin_Patch). A review confirms: "At the 5 and 15-minute mark of every run, a powerful boss will spawn" (https://www.keengamer.com/articles/reviews/pc-reviews/20-minutes-till-dawn-review-surviving-the-swarm/).
- **The pacing pattern is elite (3:00), boss (5:00), elite (11:20), boss (15:00), elite (16:00), then dawn (20:00).** The second boss arrives with 5 minutes left, so its reward is spent in the hardest stretch.

Full schedule, Standard Mode (spawn times in seconds, HP before Darkness):

| Map | 3:00 elite | 5:00 boss | 11:20 elite | 15:00 boss | 16:00 / 18:00 elite |
|---|---|---|---|---|---|
| Forest (infinite) | Elder 1,000 | Shub-Niggurath 2,500 | Spawner 10,000 | Shoggoth 35,000 | Winged Terror 18,000 (16:00) |
| Temple (enclosed square) | Elder 1,000 | Yog 10,000 | Spawner 10,000 | Hastur 30,000 | Winged Terror 18,000 (18:00) |
| Pumpkin Patch (horizontal corridor) | Elder 1,000 | Shub-Niggurath 2,500 | Spawner 10,000 | Reaper 35,000 | Winged Terror 18,000 (16:00) |

Sources: the three map pages above and https://20-minutes-till-dawn.fandom.com/wiki/Map. For scale, small enemies on the same Forest table run from 24 HP at 0:00 to 250-500 HP after 16:00 (https://20-minutes-till-dawn.fandom.com/wiki/Forest). The 15:00 boss therefore has 70 to 140 times a late trash mob's HP.

### 2.2 Boss behaviour and telegraphs

| Boss | Behaviour (wiki) | Telegraph / horde interaction |
|---|---|---|
| Shub-Niggurath (5:00) | Melee; dashes "after a short charge up. The direction of the dash is locked in when the charge up starts", so circling or side-stepping beats it | Wind-up with direction lock-in: the classic readable charge (https://20-minutes-till-dawn.fandom.com/wiki/Shub-Niggurath) |
| Yog (5:00 Temple) | Charges; "At the end of the charge, it spawns 9 Sploders" | Uses the horde: each charge seeds exploding adds (https://20-minutes-till-dawn.fandom.com/wiki/Yog) |
| Shoggoth (15:00 Forest) | Keeps medium range, then fires "5 laser beams from its red eyes" while rotating. "Before firing, there are red lines that indicate the zones of damage" | Red line telegraphs. Patch 0.6.3 "Increased how often Shoggoth (laser eye boss) attacks" (https://20-minutes-till-dawn.fandom.com/wiki/Shoggoth; https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6214419130144571935) |
| Hastur (15:00 Temple) | Follows; dashes to spawn "2 groups of 3 Sploders (which can be immediately shot to damage Hastur)"; spawns destructible tentacles around the map; "spawns doors underneath the character which deals damage if not immediately moved from" | Adds double as ammunition against the boss (shoot the Sploders near it). Ground "doors" are a stand-and-die decal. 1.0 cut tentacle spawn cooldown from 4 s to 3 s (https://20-minutes-till-dawn.fandom.com/wiki/Hastur_(boss); https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5129083846338804693) |
| Reaper (15:00 Pumpkin Patch) | Dashes, then stops "for a few seconds" to shoot 1-2 projectiles and spawn 2 Eyebats | Stop-and-shoot gives a punish window (https://20-minutes-till-dawn.fandom.com/wiki/Reaper) |
| Secret boss | 1.0 added a "SECRET BOSS" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5129083846338804693). Killing a Mysterious Tree (45,000 HP, more than any boss) makes the other trees uproot and chase; "The secret boss will also spawn at the very end of the run, with one for every Mysterious Tree killed" (https://20-minutes-till-dawn.fandom.com/wiki/Mysterious_Tree) | Opt-in: the player chooses to summon a harder finale and chooses how many. A good model for an optional post-30:00 challenge |

Elites (wiki "Mini-Bosses"): Elder is pure melee; Spawner keeps a short distance and "spawns 6 Spawnlings every few seconds"; Winged Terror simply chases (https://20-minutes-till-dawn.fandom.com/wiki/Elder; https://20-minutes-till-dawn.fandom.com/wiki/Spawner; https://20-minutes-till-dawn.fandom.com/wiki/Winged_Terror).

### 2.3 Arena change: the boss barrier

- "When bosses spawn, a rectangular electric barrier traps the player for 1 minute while slowly becoming smaller" (https://20-minutes-till-dawn.fandom.com/wiki/Boss). The newer wiki.gg mirror instead says it "traps the player for 1 minute note it does not get smaller" (https://20minutestilldawn.wiki.gg/wiki/Bosses). The two wikis conflict; a beta note "Fixed a bug where the boss arena would get progressively smaller each loop" (Endless) shows the size was at least once unintended (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/4474904295764599946).
- The Temple map is already enclosed, so "when Bosses appear, there is no electric barrier" (https://20-minutes-till-dawn.fandom.com/wiki/Temple).
- 0.6.2 "Fixed the northern boss wall not hitting players" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/4480532686360643595): the wall damages on contact.
- **Design reading:** on an infinite map, kiting can make a boss irrelevant. The barrier is a temporary arena that forces engagement for 60 s, then dissolves so the horde game resumes. This is a direct model for spawning a boss in an open ember arena.

### 2.4 Darkness and light (two different things)

1. **Literal darkness / vision.** "Vision is limited at the start of each round, with only the eyes of the monsters being visible as they approach the player in the dark, until they enter the player's field of vision" (https://en.wikipedia.org/wiki/20_Minutes_Till_Dawn). "Most of the screen is darkened except for a circle of light around the player character" (https://www.keengamer.com/articles/reviews/pc-reviews/20-minutes-till-dawn-review-surviving-the-swarm/). A Vision upgrade tree exists (listed in the 1.0 notes, https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5129083846338804693). Red eyes in the dark act as an early-warning telegraph for off-screen threats, which fits a night setting.
2. **Darkness as difficulty.** Darkness is "the primary difficulty modifier", with 16 cumulative levels (0-15). Boss-relevant steps: D4 bosses +50% HP; D6 bosses deal double damage; D14 bosses +150% HP in total; **D15 "Bosses attack 80% more often"**. Elites get +50% HP (D3), double damage (D5), +25% speed (D8) and +125% HP in total (D13). Small enemies get spawn rate, HP, speed and "double damage in the last 5 minutes" (D10). Non-combat steps: D9 "Reduce upgrade choices by 1" and D11 XP -15% (https://20-minutes-till-dawn.fandom.com/wiki/Darkness). Note the levers: HP, damage, then **attack frequency** last of all, the one that changes how the fight plays rather than how long it lasts.

### 2.5 Readability

- 0.6.2 "Small Visibility Update": "Increased the contrast between the floor tiles and the enemies"; "Fireball and Scarlett's Firewave now spawn further away from the player as to not block view of the player"; and "I've heard your complaints in this area" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/4480532686360643595).
- A **boss contour (outline) option** sits in settings next to screen shake (https://toucharcade.com/2022/11/14/20-minutes-till-dawn-yuki-character-unlock-update-boss-contour-option-ios-android-steam-iphone-ipad/).
- 1.0 fixed "auto-aim not targeting bosses" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5129083846338804693): in an auto-aim game the boss must be a valid, preferably prioritised, target.
- The planned "Blessings & Curses" overhaul (announced to beta in Oct 2024) says: "Each boss now has unique minions that spawn alongside them for more interesting fights. **Normal enemies will not spawn during boss fights anymore to prevent too much clutter**" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6212245217911959733). This is the developer's own conclusion: boss plus full horde was too cluttered. Whether this update reached the live branch was not found.
- A Rock, Paper, Shotgun piece jokes that "Killing the framerate is 20 Minutes Till Dawn's secret real win condition" (https://www.rockpapershotgun.com/killing-the-framerate-is-20-minutes-till-dawns-secret-real-win-condition): the power fantasy and its readability cost in one sentence.

### 2.6 Weak vs absurd builds; Endless

- **No phase gates or caps on the bosses were found.** They are single-pattern HP sponges with timed spawns. A strong build kills them before the 60 s barrier ends; a weak build survives the barrier minute and goes on with the boss still chasing (inference from the barrier's fixed duration; the behaviour of a surviving boss after the barrier is not documented).
- **Reward:** bosses drop a **Tome**, a pick-1-of-3 special upgrade, "many tomes also have some disadvantages" (https://20-minutes-till-dawn.fandom.com/wiki/Tome). Elites drop a chest with a character-specific upgrade and 36 XP (https://20-minutes-till-dawn.fandom.com/wiki/Elder). The Blessings & Curses plan replaces tomes with curses, "power with heavy penalties" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6212245217911959733).
- **Endless:** Darkness is fixed at 0; each upgrade can be taken at most 3 times. Every 10 minutes all enemies get new HP = old HP + 5 x base HP, new speed = old + 0.2 x base, and **new boss attack speed = old + 0.25** (https://20-minutes-till-dawn.fandom.com/wiki/Endless_mode). The developer: "certain builds let players scale their damage much faster than enemies could scale in HP, which made endless mode too easy and uninteresting". Fixes: enemy HP and spawn rate scale faster; summons capped at 5 attacks per second; several damage multipliers changed "from multiplicative to additive" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/4474904295760720435). Later: "rebalanced to prevent runs that last multiple hours" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/4606641560251791268). A hotfix fixed "Bosses to scale much faster than they were suppose to" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/4539082035575570771).
- At early access the developer conceded variety was thin: "Currently the same bosses appear every run, but I want to add enough bosses so that different random bosses can appear every run" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/4480532526713157631).

### 2.7 Player opinion

- Hastur in Temple drew both praise and complaint in one thread. Praise: the boss does "zoning" well, "stopping you from firing back, and feels like an actual boss fight" as opposed to a bullet sponge (Dr Six). Complaint: "Tentacles everywhere and I can't see what to dodge lol"; "the tentacles spawn almost without pause and the mobs just keep coming... your own attacks blinds you while the enemy outlines doesn't really put much of a difference" (Peler Parker). Source: https://steamcommunity.com/app/1966900/discussions/0/3811785047389393016. The same complaint, the player's own effects hiding the boss's, is what led to the outline option and the later no-trash-during-bosses plan.
- A reviewer notes "the first boss appears at identical locations in 2 of the 3 areas" (Shub-Niggurath), while "the second boss is unique to each location" (https://www.keengamer.com/articles/reviews/pc-reviews/20-minutes-till-dawn-review-surviving-the-swarm/).

**Takeaways for Survivor Unchained:** (a) a temporary arena wall turns an open-field boss into a duel without a separate scene; (b) eyes in the dark are a cheap, on-theme off-screen telegraph; (c) at the top difficulty, raise attack *frequency* rather than only HP; (d) suppress or replace ordinary trash during the boss with the boss's own themed minions; (e) an opt-in secret boss, summoned by the player's own action, is a good after-the-win challenge.

---

## 3. HoloCure: Save the Fans! (Kay Yu, free; Steam since 2023)

### 3.1 Structure and the boss clock

- "Mini-bosses spawn every 2 minutes, while main bosses spawn every 10 minutes" (https://holocure.wiki.gg/wiki/Enemy). In Stage Mode "The stage ends once the player defeats the stage's final boss, which appears after 20 minutes" (https://holocure.wiki.gg/wiki/Stage). **No timer ends the fight**: the stage is cleared only by the kill.
- Boss/mini-boss rules: "(usually doubled) size, vastly increased stats", "immune to all instant KO effects, and some are completely immune to knockback" (https://holocure.wiki.gg/wiki/Enemy). Many items explicitly exclude bosses. Chicken's Feather's revive defeats "all non-Boss targets"; Black Plague and Ookami Mio's skill have "a small chance to be instantly defeated" only on "non-boss targets" (secondary: wiki search snippets for https://holocure.wiki.gg/wiki/Item, https://holocure.wiki.gg/wiki/Black_Plague, https://holocure.wiki.gg/wiki/Ookami_Mio).
- **Spawn cap bypass**: when the enemy cap is reached, periodic spawns stop, "However, enemies spawned via time events (including bosses) will still be spawned" (https://holocure.wiki.gg/wiki/Enemy). The boss always arrives on schedule.
- **Mini-boss cadence, Stage 1** (HP): Mega Chumbud 600 (2:00), Tako Grande 1,800 (4:00), Mega Dark Chumbud 2,500 (6:00), Giant Dead Batter 3,500 (8:00), **Fubuzilla 8,000 (10:00)**, King Kronie 5,500 (13:00), two Q mini-bosses 7,500 each (15:00), Overgrown Sapling 11,000 (17:30), **Smol Ame 25,000 (20:00)** (https://holocure.wiki.gg/wiki/Stage_1_-_Grassy_Plains). Mini-bosses are fan-themed big versions of the current trash, each a step up.

### 3.2 Every stage boss

| Stage | 10:00 boss (HP) | 20:00 final boss (HP) | Final-boss arrival and mechanics |
|---|---|---|---|
| 1 Grassy Plains | Fubuzilla 8,000: walks at you firing "massive Fan Beams horizontally in the direction it faces, requiring the player to attack from above or below" | Smol Ame 25,000 | "all previous enemies will disappear and she will be followed by an army of Thicc Bubbas". Periodic Ground Pound: "The shadow on the ground indicates where she will land" |
| 2 Holo Office | Mikodanye 16,000: cone of fireballs; throws buckets that leave lingering lava pools | A-chan 45,000 | Enemies disappear; "A large red circle will indicate where she will initially spawn"; escorted by Loyal Soratomos. Flies around firing blue streams and red rings; "At regular intervals, she will stop moving and darken the screen to perform a larger attack" (turning rings or a clockwise sweep) |
| 3 Halloween Castle | Shubangelion 24,000: raises fist and slams for a large AoE, then rubble falls from the ceiling | Spiderchama 55,000 | Enemies disappear; "a large red zone that appears around the playable character; if they fail to exit the area before the boss spawns, they will take damage"; Hatchling army. Bullet Stream; Chama Crush (leap, land, falling boulders); Chama's Web, signalled by "an eerie laugh", with rotating streams avoidable by circling or staying out of range |
| 4 Gelora Bung Yagoo | Udin 32,000: projectile waves plus a charge "indicated by two flashing !! exclamation points" | **Area 15 trio**: Moontato 53,000, Risusaurus 57,000, UFOFI 55,000 | All three spawn together, share a basic move-and-burst pattern, then use personal attacks. Moontato: "!! indicator along with an audio cue" before a lunge to your last position. Risusaurus: fire "indicated by a cone-shaped warning". UFOFI: circular bullet rings. "All three bosses must be defeated in order to clear the stage" |
| 5 Fantasy Island | Nanora 50,000: tracking fireball stream, longer range than Mikodanye; boulder showers | Pekodam 100,000 | Flies around firing aimed bursts and rings; stops to run a **fixed cycle** of (a) a tracking gunfire sweep, more accurate the further away you are, and (b) "4 waves of several missiles that strike from above after a delay" |

Sources: https://holocure.wiki.gg/wiki/Fubuzilla, https://holocure.wiki.gg/wiki/Smol_Ame, https://holocure.wiki.gg/wiki/Mikodanye, https://holocure.wiki.gg/wiki/A-chan, https://holocure.wiki.gg/wiki/Shubangelion, https://holocure.wiki.gg/wiki/Spiderchama, https://holocure.wiki.gg/wiki/Udin, https://holocure.wiki.gg/wiki/Area_15_(Bosses), https://holocure.wiki.gg/wiki/Nanora, https://holocure.wiki.gg/wiki/Pekodam. The boss HPs match the stage tables (https://holocure.wiki.gg/wiki/Stage_2_-_Holo_Office, https://holocure.wiki.gg/wiki/Stage_3_-_Halloween_Castle, https://holocure.wiki.gg/wiki/Stage_4_-_Gelora_Bung_Yagoo, https://holocure.wiki.gg/wiki/Stage_5_-_Fantasy_Island).

A guide describes A-chan arriving "generating a shock wave with an oversized warning sign", with a cycle of "move, fire red bullets, move, rapidly shoot blue bullets, move (repeat)". It advises: "A-chan's red bullet shooting mode has a cooldown so concentrate all your firepower on her when you see the opportunity" (https://samurai-gamers.com/holocure/stage-2-holo-office-walkthrough-and-guide/). This is a readable vulnerability window.

### 3.3 Hard stages: last stage's finale becomes this stage's midpoint

| Hard stage | 10:00 (HP) | 20:00 final (HP) | Final-boss notes |
|---|---|---|---|
| 1H Grassy Plains (Night) | Fubuzilla 15,000 **and** Smol Ame 12,000 together; Fubuzilla's beams "are instead aimed at the player" | Halloween Bae 72,000 | Red-circle spawn, enemies disappear, Baerat army. Danmaku streams; backflip "indicated by a large red circle" with spiral, **dodging all attacks during the backflip**. "When her HP is brought low enough, she will enrage and gain a flaming aura", with speed up, double bullets, and special Baerats that launch themselves at the player |
| 2H Holo Office (Evening) | Mikodanye 15,000 + A-chan 15,000 | Harusaki Nodoka 90,000 | Red-circle spawn, HoloStaff army; danmaku plus aimed Fan Beams; screen-darkening big attacks; low-HP enrage with "flaming green aura", more speed and bullets. The wiki notes "The spiraling ring of fastballs just before the boss is likely a reference to the final attack of Sans in Undertale": a scripted pre-boss set-piece |
| 3H Halloween Castle (Myth) | Shubangelion 35,000 + Spiderchama 35,000 | **Halloween Myth, five bosses**: Dino Gura 78,000 (charge), Dr Oopsie 80,000 (acid pools), Nurse Calli 83,000 (short range), Pumpkin Ame 75,000 (ground pound + rockfall), Vampire Kiara 82,000 (danmaku + **healing pulses** like Otaku Healers) | "all five bosses will spawn together, along with a swarm of their related fans". Combined 398,000 HP, "by far the highest of any enemy or boss" |
| 4H Gelora Bung Yagoo (Night) | Udin 60,000 + Moontato 45,000 + UFOFI 50,000 + Risusaurus 50,000 (four bosses) | Goriela 180,000 | Flies around firing at all times; stops for a tracking banana stream, exploding boulders, a delayed charge, or a dense barrage. **Below 50%** enrages with "a flaming golden aura, dealing much more damage", 3 banana streams and denser barrages. Stage hazard: lightning bolts every 20-30 s (estimated) with circular warnings and "only about a single second to avoid" |

Sources: https://holocure.wiki.gg/wiki/Stage_1_(Hard)_-_Grassy_Plains_(Night), https://holocure.wiki.gg/wiki/Halloween_Bae, https://holocure.wiki.gg/wiki/Stage_2_(Hard)_-_Holo_Office_(Evening), https://holocure.wiki.gg/wiki/Harusaki_Nodoka, https://holocure.wiki.gg/wiki/Stage_3_(Hard)_-_Halloween_Castle_(Myth), https://holocure.wiki.gg/wiki/Halloween_Myth, https://holocure.wiki.gg/wiki/Stage_4_(Hard)_-_Gelora_Bung_Yagoo_(Night), https://holocure.wiki.gg/wiki/Goriela.

Patterns worth copying:
- **Escalation by recombination.** The normal stage's two bosses return together as the hard stage's 10:00 event at different HP: 1H Fubuzilla gets more (15,000 vs 8,000), Smol Ame less (12,000 vs 25,000). Then a new, much bigger finale. Players meet familiar threats in a new mix before the unknown one.
- **Multi-boss finales** (Area 15 trio, Myth five) need every boss dead. They reward focus-fire and drop each boss's EXP and Holozon Box as it falls, which "means players could pick up the EXP and Holozon Boxes of the ones they manage to defeat first" (https://holocure.wiki.gg/wiki/Area_15_(Bosses)). A healer in the group (Vampire Kiara) creates a kill-order puzzle.
- **Enrage at low HP** with a coloured flaming aura (Bae, Nodoka, Goriela at <50%) is a clear visual phase change.

### 3.4 Telegraph vocabulary (shared across the game)

HoloCure uses one small, consistent set of warning symbols for bosses, mini-bosses, trash and stage hazards alike:

| Signal | Meaning | Source |
|---|---|---|
| **Red circle on the ground** | Something lands or explodes here: bomber fuse radius, Airdrop spawn, boss spawn point, Bae's backflip | https://holocure.wiki.gg/wiki/Enemy; https://holocure.wiki.gg/wiki/Halloween_Bae |
| **Large red zone around the player before a boss arrives** | Leave now or take damage (Spiderchama) | https://holocure.wiki.gg/wiki/Spiderchama |
| **Red "!!" over an enemy + audio cue** | Charge to your last known position (Chargers, Udin, Moontato) | https://holocure.wiki.gg/wiki/Enemy; https://holocure.wiki.gg/wiki/Area_15_(Bosses) |
| **Red line across the screen** | Fastball (enemy-as-projectile) path | https://holocure.wiki.gg/wiki/Enemy |
| **Edge alert indicator** | Stampede direction; Horde Rush | https://holocure.wiki.gg/wiki/Enemy |
| **Shadow on the ground** | Landing spot of a leap (Smol Ame) | https://holocure.wiki.gg/wiki/Smol_Ame |
| **Cone-shaped warning** | Breath attack arc (Risusaurus) | https://holocure.wiki.gg/wiki/Area_15_(Bosses) |
| **Screen darkens** | A big set-piece attack is coming (A-chan, Nodoka) | https://holocure.wiki.gg/wiki/A-chan |
| **Coloured flaming aura** | Boss has enraged | https://holocure.wiki.gg/wiki/Goriela |
| **Voice/laugh cue** | Spiderchama's web attack | https://holocure.wiki.gg/wiki/Spiderchama |
| **Full-width warning band** | Stage 5 pirate cannonball | https://holocure.wiki.gg/wiki/Stage_5_-_Fantasy_Island |

The wiki even flags an inconsistency as odd: "the Kronie Wall event at 16:15 is the only Wall-based event to use alert indicators" (https://holocure.wiki.gg/wiki/Stage_1_-_Grassy_Plains). The community reads the vocabulary as a rule set.

### 3.5 Readability in the crowd

- **The screen is cleared for the finale.** Every final boss arrival makes "all previous enemies... disappear", replaced by a themed escort army (Thicc Bubbas, Soratomos, Hatchlings, Baerats, HoloStaff) (https://holocure.wiki.gg/wiki/Smol_Ame; https://holocure.wiki.gg/wiki/A-chan; https://holocure.wiki.gg/wiki/Spiderchama). This is the same fix 20MTD later planned.
- Hitboxes: 0.4 Patch 1, "Bosses now have a shorter hitbox compared to their sprite height" (https://holocure.wiki.gg/wiki/Update_0.4_Patch_1): a big sprite must not mean unfair contact damage.
- Effect clutter: Update 0.7 merged stacked on-death bomb explosions on a boss: "Before: 10 bombs attached to boss, it creates 10 explosions at once when defeated. Now: ... 1 explosion that is equivalent to 10x damage" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1783238125235194).
- **The boss as weapon unlock.** Beating a boss unlocks a weapon modelled on its attack: Fubuzilla gives Fan Beam, a scaled-down version of its own laser ("The mid-game boss Fubuzilla shoots Fan Beams from its mouth, though they are far larger and more powerful than the player's") (https://holocure.wiki.gg/wiki/Fan_Beam). Smol Ame gives Gorilla's Paw, A-chan CEO's Tears, Spiderchama EN's Curse, Area 15 Sausage, Pekodam Owl Dagger (https://holocure.wiki.gg/wiki/Smol_Ame; https://holocure.wiki.gg/wiki/A-chan; https://holocure.wiki.gg/wiki/Spiderchama; https://holocure.wiki.gg/wiki/Area_15_(Bosses); https://holocure.wiki.gg/wiki/Pekodam).

### 3.6 Weak vs absurd builds; difficulty knobs; Endless

- **No time-out.** A weak build must still kill the 20:00 boss. Players say difficulty "depends heavily on item choices rather than strict level requirements"; one reports clearing Stage 1 "around level 40" (secondary paraphrase of https://steamcommunity.com/app/2420510/discussions/0/3810661398182497854). A player can also kite: the Stage 1 Hard final boss "lets you keep running away for a slower indirect kill" (xBleacheDxSungasMx, https://steamcommunity.com/app/2420510/discussions/0/3810661765908472148).
- **Strong builds**: another player's advice for a no-hit achievement was "use your special and kill the boss before they fire any projectiles" (AnonTwo, same thread). HoloCure accepts burst-skips. Its only guards are the exclusions above (no instant KO, often no knockback) and the very high HP of late bosses.
- **Halu, the opt-in difficulty item.** It raises spawn rate and makes fans stronger. In practice each level adds +2 spawn rate and buffs ATK, HP and SPD by 10/15/20/25/30%, applied to future spawns and undamaged enemies on screen. It pays HoloCoins per kill (up to 1 per kill at level 5); the in-game text at level 5 reads "Don't do it." (https://holocure.wiki.gg/wiki/Halu). Boss HPs on the wiki are quoted "without Halu", so Halu also inflates bosses (https://holocure.wiki.gg/wiki/Goriela).
- **Endless and the 30:00 kill screen.** Stats scale from two terms, a = max(0, minute-23) + 37 x hour and b = minutes past 30 + 60 x hours past 1: ATK = (base + 2a)^(1+b/25); HP = (base + 0.05 x base x a)^(1+b/50). The wiki splits a run into "Pre-Endgame (before 23:00)", "Endgame (23:00-30:00)" and "**Kill screen (after 30:00)**", where "Spawn pool are totally replaced with YAGOOs, enemy stats skyrocket every minute" (https://holocure.wiki.gg/wiki/Enemy). YAGOO (15,000 base HP, 30:00-40:00) and Angry YAGOO (10,000, 40:00+) count as mini-bosses for score (https://holocure.wiki.gg/wiki/Stage_1_-_Grassy_Plains; https://holocure.wiki.gg/wiki/Score). The endless "boss" is therefore a recurring mini-boss wave on an exponential curve, and the score formula weights each minute past 30 at 20,126 points (https://holocure.wiki.gg/wiki/Score).

### 3.7 Victory moment and reward

- Kill the final boss and "the game suddenly black out and there is a notice saying stage cleared" (RudiAn, https://steamcommunity.com/app/2420510/discussions/0/3810661398182497854): a hard cut to a result card, not a lingering field.
- Every boss drops a **Holozon Box**, a delivery package holding one product (a new weapon or item, or an upgrade) or three (9% chance), plus coins. There is a 5% chance of a **super box** "signified by a special animation". The player may accept or drop the contents (https://holocure.wiki.gg/wiki/Holozon_Box). The 10:00 boss's box is a mid-run power spike; the 20:00 box is mostly ceremonial.
- Stage clear pays floor((Halu coins + kills) x 0.25 + clearAmount), with clearAmount rising from 3,000 (Stage 1) to 50,000 (Stage 4 Hard) (https://holocure.wiki.gg/wiki/Stage).

### 3.8 Player opinion

Direct quotes were harder to obtain (Reddit and TV Tropes blocked scripted access). What was found:
- A new player played Stage 1 "for 40 minutes at level 35" without realising a boss ended the stage. They "had run too far away and forgotten about the boss, then died hitting a fence" (paraphrase of the OP, https://steamcommunity.com/app/2420510/discussions/0/3810661398182497854). **Lesson: a final boss must be impossible to miss.** Use an off-screen pointer, banner or music change.
- Achievement hunters treat the Stage 1 Hard finale as manageable by distance ("final boss lets you keep running away for a slower indirect kill") and burst ("use your special and kill the boss before they fire any projectiles") (https://steamcommunity.com/app/2420510/discussions/0/3810661765908472148).
- Popularity: HoloCure holds a "near-perfect Steam score", per a PCGamesN headline (secondary: Steam news feed title, https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=2420510).
- Specific love/hate threads for Goriela, Nodoka or Halloween Myth: not found.

**Takeaways for Survivor Unchained:** (a) clear the field and send a themed escort when the 30:00 boss arrives; (b) keep one global telegraph vocabulary (red circle = lands here, !! + sound = charge, line = projectile path, darkening = big attack, aura = enrage); (c) reuse earlier bosses as later mid-run events; (d) make the victory a hard cut with a clear "cleared" card, then offer the endless choice; (e) a post-30:00 kill screen with mini-boss waves and exponential stats is a proven endless design; (f) grant a weapon modelled on the boss's attack as a meta-unlock.

---

## Gaps and caveats

- Brotato wiki pages disagree on boss HP (29,900 vs 29,250) and on Invoker's M1 threshold (60% vs 75%). The patch-note formula (15,000 + 750 x wave) is the primary source. Boss VFX/audio on death and Brotato's exact spawn-telegraph duration: not found.
- 20MTD: whether the boss barrier shrinks is disputed between the two wikis; what a boss does after the barrier expires is undocumented; the secret boss's name and mechanics, and whether the Blessings & Curses boss rework reached the live game, were not found.
- HoloCure: no global "boss timer" or despawn rule for bosses was found (the only boss-timing rules are 2-min mini-bosses and 10/20-min bosses that bypass the spawn cap); the boss HP-bar presentation, music change on boss arrival and enrage HP thresholds for Bae and Nodoka ("low enough") were not found. Reddit, TV Tropes and itch.io devlogs blocked scripted access, so player-opinion quotes come from Steam forums only.

## Sources (main)

- Brotato wiki: https://brotato.wiki.spellsandguns.com/Enemies, /Predator, /Invoker, /Template:Boss_Data, /Template:Elite_Data, /Danger_Levels, /Waves, /Elite_and_Horde_Waves, /Endless_Mode, patch pages /Patch_0.5.9, /Patch_0.5.10, /Patch_0.5.11c, /Patch_0.6.0.7, /Patch_0.6.1.6, /Patch_0.8.0.3, /Patch_1.0.0.3, /Patch_1.1.0.0, /Patch_1.1.*.*
- Brotato Steam: https://steamcommunity.com/app/1942280/discussions/0/4631483020295041397, https://steamcommunity.com/app/1942280/discussions/0/6363075944119837726
- 20MTD wiki: https://20-minutes-till-dawn.fandom.com/wiki/Boss, /Forest, /Temple, /Pumpkin_Patch, /Shub-Niggurath, /Shoggoth, /Yog, /Reaper, /Hastur_(boss), /Mysterious_Tree, /Darkness, /Endless_mode, /Tome; https://20minutestilldawn.wiki.gg/wiki/Bosses
- 20MTD Steam news (flanne): 1.0 release, 0.6.2 visibility, 0.6.3, endless beta hotfixes, 0.7.7, Blessings & Curses (URLs inline)
- 20MTD press/forum: https://www.keengamer.com/articles/reviews/pc-reviews/20-minutes-till-dawn-review-surviving-the-swarm/, https://en.wikipedia.org/wiki/20_Minutes_Till_Dawn, https://toucharcade.com/2022/11/14/20-minutes-till-dawn-yuki-character-unlock-update-boss-contour-option-ios-android-steam-iphone-ipad/, https://steamcommunity.com/app/1966900/discussions/0/3811785047389393016
- HoloCure wiki: https://holocure.wiki.gg/wiki/Enemy, /Stage, every boss page, every stage page, /Halu, /Holozon_Box, /Score, /Fan_Beam, /Update_0.4_Patch_1
- HoloCure Steam: Update 0.7 notes (URL inline), https://steamcommunity.com/app/2420510/discussions/0/3810661398182497854, https://steamcommunity.com/app/2420510/discussions/0/3810661765908472148, https://samurai-gamers.com/holocure/stage-2-holo-office-walkthrough-and-guide/

## Verification

Adversarial re-check on 2026-10-03. I read the Brotato wiki pages as raw wikitext (`action=raw`), the 20MTD fandom pages through the MediaWiki API (the HTML is behind Cloudflare), the Steam thread and the news feed as raw JSON, and the HoloCure wiki.gg pages with WebFetch (scripted raw access is blocked).

| # | Claim | Verdict | Notes / correction |
|---|---|---|---|
| 1 | Brotato bosses only on wave 20; win on kill-all or wave timeout; wave 20 = 90 s | Confirmed | Predator/Invoker pages give the exact wording; Waves table shows wave 20 = 90s (https://brotato.wiki.spellsandguns.com/Predator, https://brotato.wiki.spellsandguns.com/Waves) |
| 2 | Invoker M1 60%/30 s, M2 40%/60 s, speed 200 to 500; Predator M1 50%/45 s left | Confirmed | Matches the page wording (https://brotato.wiki.spellsandguns.com/Invoker, https://brotato.wiki.spellsandguns.com/Predator) |
| 3 | Boss HP 28,000+100/wave to 15,000+750/wave in 1.0.0.3; D5 both spawn at -25% HP | Confirmed | Patch 1.0.0.3 line verbatim; Danger_Levels "(Bosses have -25% less HP)". See the HP reconciliation below |
| 4 | Crit/burn 10% current-HP effects do 1% to bosses/elites | Partly right | These are two specific items, not general crit/burn mechanics: **Giant Belt** (crit, in Patch 0.8.0.3) and **Greek Fire** (burn, in Patch 1.1.0.0, not 0.8.0.3) (https://brotato.wiki.spellsandguns.com/Patch_0.8.0.3, https://brotato.wiki.spellsandguns.com/Patch_1.1.0.0) |
| 5 | 1.1 fixed delayed slash/pillar projectiles damaging on the first frame (Invoker "instant unavoidable damage") | Confirmed | Verbatim, as is the Eel cleanup line (https://brotato.wiki.spellsandguns.com/Patch_1.1.*.*) |
| 6 | "Elites on wave 11-12 are run killers..." | Confirmed | Author Rushin, 6 Nov 2024. The full sentence continues "...even with retries for practicing." The thread's context is D5 Crash Site + Abyss (DLC) (https://steamcommunity.com/app/1942280/discussions/0/4631483020295041397) |
| 7 | 20MTD bosses start=300/900; Forest Shub 2,500, Shoggoth 35,000; elites 180/680/960; no 20:00 boss | Confirmed | Forest spawn table verbatim. In Endless, Shoggoth instead appears at start=600 (590 in the visual table) (https://20-minutes-till-dawn.fandom.com/wiki/Forest) |
| 8 | Electric barrier for 1 min; wikis disagree on shrinking | Confirmed | Fandom (Boss redirects to Enemies#Bosses): "while slowly becoming smaller"; wiki.gg: "note it does not get smaller" (https://20-minutes-till-dawn.fandom.com/wiki/Enemies, https://20minutestilldawn.wiki.gg/wiki/Bosses) |
| 9 | Darkness 15 "Bosses attack 80% more often"; D4 +50% / D14 +150% total boss HP; D6 double boss damage | Confirmed | Verbatim (https://20-minutes-till-dawn.fandom.com/wiki/Darkness) |
| 10 | flanne: "Each boss now has unique minions... Normal enemies will not spawn during boss fights anymore..." | Confirmed | Post "Blessings & Curses - Coming to Beta Branch Soon", 28 Oct 2024. It is a plan for the beta branch. The app news feed has no later post, so it is still unconfirmed whether this reached the live game (https://steamcommunity.com/ogg/1966900/announcements/detail/4538032056440979677) |
| 11 | HoloCure mini-bosses every 2 min, bosses every 10 min; immune to instant KO; time events bypass the cap | Confirmed | Verbatim (https://holocure.wiki.gg/wiki/Enemy) |
| 12 | Smol Ame 25,000 HP at 20:00; enemies disappear, Thicc Bubba army; shadow marks the Ground Pound | Confirmed | Verbatim (https://holocure.wiki.gg/wiki/Smol_Ame) |
| 13 | Goriela 180,000 HP, Stage 4 Hard, enrages below 50% with a flaming golden aura and much more damage | Confirmed | "Below 50% health, Goriela will enrage and gain a flaming golden aura, dealing much more damage" (https://holocure.wiki.gg/wiki/Goriela) |
| 14 | After 30:00 the spawn pool is all YAGOOs and stats "skyrocket every minute" ("kill screen") | Confirmed | Matches the Enemy page's phase list (https://holocure.wiki.gg/wiki/Enemy) |

Other claims spot-checked:
- **Brotato boss HP numbers (§1.2 notes; Gaps): partly right, and the explanation should be corrected.** The two wiki figures are not just "close but inconsistent". 29,250 = 15,000 + 750 x 19 (the current formula, with the wave term apparently zero-indexed). 29,900 = 28,000 + 100 x 19 (the **pre-1.0.0.3** formula). So the boss-page/infobox figure of 29,900 (D5 31,395) is outdated, and the Enemies-table figure of 29,250 (D5 30,712) is current. "At wave 20 that is 30,000" is probably off by one wave: the practical figure is 29,250. By the same logic a wave-11 elite may have 1 + 750 x 10 = 7,501 HP rather than 8,251 (inference, not confirmed) (https://brotato.wiki.spellsandguns.com/Patch_1.0.0.3, https://brotato.wiki.spellsandguns.com/Enemies, https://brotato.wiki.spellsandguns.com/Predator).
- Brotato wave durations (20 s, +5 s per wave, 60 s cap): confirmed (https://brotato.wiki.spellsandguns.com/Waves).
- Brotato Danger 3/4/5 at +12/26/40% as totals; elites at 75% HP up to wave 12; elite HP 1 + 750 per wave (700 for some): confirmed (https://brotato.wiki.spellsandguns.com/Danger_Levels, https://brotato.wiki.spellsandguns.com/Template:Elite_Data).
- 20MTD Endless (+5 x base HP per 10 min, +0.2 x base speed, boss attack speed +0.25; Darkness 0; upgrades capped at 3): confirmed. The fandom page "Endless_mode" now redirects to Modes#Endless Mode (https://20-minutes-till-dawn.fandom.com/wiki/Modes).
