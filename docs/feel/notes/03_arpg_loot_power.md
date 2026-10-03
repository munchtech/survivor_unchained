# 03 — ARPG Reward, Loot and Power Growth

Research brief for a dark-fantasy ARPG / survivors hybrid. This covers Diablo II–IV, Path of Exile 1 and 2, Last Epoch, Grim Dawn, Torchlight II, Titan Quest, Lost Ark and Hades I/II. Each claim has a source URL, and numbers are in **bold**.

**About the sources.** Several primary pages (Maxroll, Icy Veins, PoE Wiki, Hades Fandom) blocked automated fetching. Where a claim comes from a search-engine summary of a page rather than the page itself, it is tagged *(via search summary)*. Claims from my general knowledge that I could not re-verify this session are tagged **[unverified]**.

---

## 1. Origins: the kill/reward slot machine (Diablo I/II)

### 1.1 The founders say it outright
- David Brevik: "We were basically making a slot machine where every time that you killed a monster, you were pulling that lever." He said the intent "wasn't really to pry money from your wallet. It was more that we liked the addictive feeling." — Kotaku, https://kotaku.com/why-video-game-loot-is-so-addictive-according-to-the-c-1846695147
- Internally the team called the core loop the **"Kill/Reward"** mechanic: every kill should leave you hopeful of a reward. — via mein-mmo, https://mein-mmo.de/en/page/2145/?term=kweis *(via search summary)*
- Unidentified items as a double reveal. Erich Schaefer: "If we could have added a third step, we would've." Brevik: "You get to unwrap it twice." — Kotaku, link above. **Design takeaway:** the drop is the first reveal and the identify or inspect step is the second.

### 1.2 Rarity colour language
- Brevik: "Blue, as we all know, is the international color for magic. That's why the mana ball is blue. So I think blue was the first one." Erich Schaefer: "Gold for the uniques was specifically because it looked more important. It looked cooler." — Kotaku, link above.
- The Diablo II ladder is white (normal) → blue (magic) → yellow (rare) → gold/tan (unique) → green (set), with orange for crafted. Grey means socketed or ethereal. **[unverified details; widely known]**
- Other games do not agree on the colours. Grim Dawn uses white → **yellow** (magic) → **green** (rare and Monster Infrequent) → **blue** (epic) → **purple** (legendary). — https://www.grimdawn.com/guide/items/the-hunt-for-loot. Titan Quest marks Monster Infrequents in bronze/light-yellow (magical) and **olive/light-green** (rare). — https://almarsguides.com/computer/games/titanquest/misc/gearlists/beginnermonsterinfrequents/ *(via search summary)*. Hades boons use white → blue → purple → red (Common/Rare/Epic/Heroic). — https://hades.wiki.fextralife.com/Boons
- **Takeaway:** only "orange/gold = special" and "blue = magic" are close to universal. Pick one ladder and use it everywhere: drops, UI frames, beams and minimap.

### 1.3 Sound as the first signal
- In Diablo I, rings were rare and hard to see on the ground. Erich Schaefer: "you'd hear it. So the sound became kinda emblematic of 'Something cool has dropped.'" — Kotaku, link above.
- Diablo II's gem-drop sound: Scott Petersen "purchas[ed] dozens of wine glasses and tapp[ed] various objects against them until finding the perfect note." His philosophy: "I was obsessed with getting the right sound for the right moment." Matt Uelmen sang "Kill the monster, kill the monster" to keep sounds tied to on-screen action. The loop: "click, click, kill, click, click, kill—loot." — Game Developer, https://www.gamedeveloper.com/audio/how-audio-design-enhances-diablo-2
- The "fwip-fwip-fwip" item-tumble sound in D2 is attributed to Uelmen or Petersen. Diablo III kept the D2 health-well sound so returning players would hear something familiar. — *(via search summary of* https://www.icy-veins.com/forums/topic/47324-why-diablo-2-still-holds-up-after-20-years-book-excerpt/ *)*
- **Takeaway:** each item category gets its own physical, non-UI sound: glass for gems, a metallic ping for rings and runes. Players learn these before they read anything.

### 1.4 Diablo II rune scarcity (the long tail)
- Hell Cows drop a **Ber about 1 in 730,000** and a **Zod about 1 in 2,560,000**. About **350–450** cows spawn per Cow Level run. Bosses are **10–20× more likely** to drop high runes than normal monsters. Examples: **Duriel drops a Ber about once every 42,945 kills**, and **Hephasto drops a Zod about once every 192,066 kills**. — Icy Veins rune guide, https://www.icy-veins.com/d2/rune-finding-guide *(via search summary; page 403'd)*
- Zod drops only in Hell Act 5 territory; Hell Baal (mlvl 99) can drop it. The Countess caps at Ist in Hell, and the Hellforge cannot give Zod. — https://diablo2.diablowiki.net/Rune_Hunting, https://rankedboost.com/diablo-2/bosses/baal/ *(via search summary)*
- Rune drop chance is **not** affected by Magic Find. — https://diablobytes.com/d2-resurrected/guides/rune-farming/
- A famous moment: a speedrunner found a Zod mid-run and sold it on stream. — https://www.techspot.com/community/topics/diablo-2-speedrunner-scores-legendary-zod-rune-trolls-audience-by-immediately-selling-it.284355/

### 1.5 Stone of Jordan, currency and duping
- Gold in D2 was "basically worthless," so the SoJ became the de facto currency, and top items were priced in SoJs. Duped SoJs then "flooded every server." After patch 1.10 made runewords central, high runes (HRs) replaced the SoJ as currency. Blizzard's fix was to make selling SoJs trigger the Diablo Clone world event. — https://diablo-archive.fandom.com/wiki/The_Stone_of_Jordan, https://diablobytes.com/d2-resurrected/guides/diablo-clone/ *(via search summary)*
- **Takeaway:** the item everyone hopes to see drop also becomes the unit of value. In a single-player survivors game this suggests a small set of "chase" items with fixed, legible worth.

### 1.6 The "one more Mephisto run"
- Mephisto has a waypoint close by, a strong loot table and can be cheesed, so "most characters farm him repeatedly." Players stacked Magic Find and movement speed to shorten each run. — https://www.wowhead.com/diablo-2/tw/guide/farming-mephisto, https://twinfinite.net/2021/02/5-things-we-cant-wait-to-do-over-over-again-in-diablo-2-resurrected/ *(via search summary)*
- The ingredients of the loop: **short run (roughly 1–2 minutes [unverified]) + guaranteed boss loot moment + a tiny chance at a jackpot + a quick restart.** This maps almost exactly onto a survivors run that is broken into short boss loops.

---

## 2. Diablo III: from Auction House to Loot 2.0

### 2.1 The Auction House hollowed out drops
- At GDC 2013, Jay Wilson said both auction houses "really hurt the game." Blizzard had assumed only a small share of players would use them and that prices would limit listings. Instead nearly every player used them, more than **50%** regularly, and about **3 million** monthly users traded. Item trading "damaged" the item-reward system. — https://www.engadget.com/2013-03-28-diablo-iiis-auction-house-really-hurt-the-game.html, https://www.pcgamer.com/au/diablo-3-auction-house-jay-wilson
- Mechanism: when the best upgrade is always for sale, a drop from a monster stops being exciting. Money becomes the motivation and killing Diablo does not. — same sources.

### 2.2 Loot 2.0 (Patch 2.0.1, February 2014)
- Shipped together with the removal of the Auction House. The aim was "quantity with quality": fewer, better and targeted drops. — https://diablo.fandom.com/wiki/Loot_2.0 *(via search summary)*, https://www.shacknews.com/article/83266/diablo-3-patch-201-deploys-with-loot-20
- **Smart Loot is an 85/15 split.** **85%** of drops roll for your class or main stat. The other **15%** are spread across the other classes, about **2.5% each**. This applies to legendaries, ancients and primals. — https://us.forums.blizzard.com/en/d3/t/when-are-items-actually-rolled/65494 *(via search summary)*
- **Legendary bad-luck protection:** "the longer you go without a legendary drop, your individual chance… increases," and the bonus resets when one drops. — https://diablo.fandom.com/wiki/Loot_2.0 *(via search summary)*. The exact per-minute increment was not public in the sources I could reach.
- **+100% legendary drop rate made permanent.** The May 2014 anniversary buff doubled legendary find. It "was overwhelmingly popular, warranting the decision to let the increase stick around." — https://www.engadget.com/2014-05-22-diablo-3-legendary-drop-rate-increase-now-permanent.html
- **Three-channel announcement for a legendary:** a loud *clang*, an **orange (or green for set) beam of light**, and a **star icon on the minimap**. The beam became iconic with 2.0.1. — https://di.diablowiki.net/Leg *(via search summary)*. A later patch **removed the beam from Greater Rift keys** because a non-legendary beam diluted the signal. — https://games.softpedia.com/blog/Next-Diablo-3-Patch-Removes-Legendary-Beam-from-Greater-Rift-Keys-458391.shtml
- Brevik later said randomness had gone too far with D3 Primals: "It feels like players have no influence on the loot." He contrasted this with targetable boss farming. — https://mein-mmo.de/en/diablo-3-urvater-kritisiert-items,137993

### 2.3 Paragon: infinite but small increments
- Paragon 2.0 (2014) removed the old **Paragon 100 cap** and made it **account-wide**. Each level gives **1 point** across **4 tabs** (Core/Offense/Defense/Utility), each field capped at **50**. Everything is full at **Paragon 800**, after which only main stat and Vitality keep growing. — https://diablowiki.net/Paragon, https://www.pcgamer.com/diablo-3-paragon-reaper-souls/ *(via search summary)*
- **Takeaway:** an always-on trickle of small permanent gains feeds "number go up" after the finite power curve is finished.

### 2.4 The Treasure Goblin
- Added late in D3 development. Its "high-pitched, maniacal giggle" makes you hunt for the source because the sound promises treasure. It runs and can portal away. — https://www.icy-veins.com/forums/topic/21374-developer-insights-behind-the-goblin-giggle *(via search summary)*, https://pcgamer.com/crushing-diablo-3s-treasure-goblins
- In a 2023 fan poll of D4 sounds, the goblin laugh was still among the most-mentioned. — https://mein-mmo.de/die-besten-sounds-in-diablo-4-laut-fans/

### 2.5 Number inflation
- D3 damage went from "a few dozen millions to a few billions." Players regularly hit for **trillions**, sometimes **quadrillions**. Patch **2.4.0** added number abbreviation ("31.5T") and a **new colour highlight for the largest hits**. Players reported that big numbers "lost their emotional appeal because they didn't stand out." Seasonal set items raised DPS by **2–5×** per build. — https://steamcommunity.com/app/219990/discussions/0/133260492057754221 *(via search summary)*
- Combat-feel references: Wyatt Cheng, GDC 2013, "Through the Grinder: Refining Diablo III's Game Systems" (iteration on health globes, controls, skills). — https://gamedeveloper.com/design/video-iterating-on-i-diablo-iii-i-s-game-systems. Julian Love (lead technical artist) on "further improvements to the way we recognize combat hits." — https://gamespy-archives.quaddicted.com/sites/www.planetdiablo.com/features/articles/jlove101309/index.html

---

## 3. Diablo IV: too many yellows, then Loot Reborn

### 3.1 Launch complaints (2023)
Players on the official forums (https://us.forums.blizzard.com/en/d4/t/i-hate-the-itemization/114952):
- "There is zero excitement about loot. Infact its almost the opposite."
- "I can't stand having to study each stat on each yellow I pick up to determine if it's an upgrade."
- "Essentially there is only one kind of item now, rares."
- "We don't need 250+ possible affixes. They could remove 80% of them and reduce loot by 80% and I'd be ecstatic."

Press and community analysis:
- **200+** item properties, and conditional affixes such as "up to 26% chance to reduce cooldowns when inflicting bleed on Elite enemies." Players spent their time "in town examining items… dismantling worthless drops." Quote: "Warum besteht dieses Spiel darauf, so langweilig zu sein???" ("Why does this game insist on being so boring???") — https://mein-mmo.de/en/why-does-the-game-insist-on-being-so-boring-items-frustrate-players-in-diablo-4,1087697/
- Beta "loot piñata" thread: "Legendaries doesnt feel like legendaries"; "I got too many golden items for a lvl 20… they should be hard to find." One poster asked for drop rates at **50%** of the beta level. A counter-view: "You need high droprate to have a chance to get gear appropriate for class and level and build." — https://eu.forums.blizzard.com/en/d4/t/loot-pi%C3%B1ata-save-us/900
- Joe Shely: "We don't want big numbers clogging up the screen." One player calculated that keeping numbers small at level 100 would need **99.999964%** monster damage reduction, and others argued that "feel matters more than the actual damage values." — https://us.forums.blizzard.com/en/d4/t/we-dont-want-big-numbers-clogging-up-the-screen-joe/16225

### 3.2 Season 4 "Loot Reborn" (May 2024)
Official notes (https://news.blizzard.com/en-us/article/24077223/4):
- "**Fewer items will drop overall**, but those items will be more likely to be valuable."
- **Legendaries go down to 3 affixes and rares to 2.** Simple flat stats replaced conditional ones, and complexity moved into crafting.
- **Greater Affixes** give **1.5×** normal values, are marked with an asterisk, appear only on Ancestral items, and an item can roll **1–4** of them. — also https://www.icy-veins.com/d4/news/diablo-4-season-4-loot-reborn-official-preview/ *(via search summary)*
- **Tempering** adds **2** chosen-category affixes (randomised within a recipe) from **6** manual categories: Weapons, Offensive, Defensive, Mobility, Utility, Resource. Durability or charges limit retries.
- **Masterworking** has **12 ranks**. Most ranks add about **+5%** to all affixes. Ranks **4, 8 and 12** add about **+25% to one random affix**, with a colour shift **blue → yellow → orange**. It **cannot fail** and can be reset. — https://primagames.com/gaming/all-masterworks-ranks-and-effects-in-diablo-4, https://www.wowhead.com/diablo-4/ko/news/masterworking-new-crafting-system-coming-with-diablo-4-season-4-338184 *(via search summary)*
- Stated goal: make it "easier to understand which items are upgrades" and let players spend more time fighting than sorting.

### 3.3 Uber/Mythic Uniques: beam, sound and pity
- The community estimated the Season 2 Echo of Duriel Uber drop at about **2%**. Blizzard temporarily **doubled** the rate. — https://www.icy-veins.com/d4/news/potential-drop-chance-of-uber-uniques-in-diablo-4-season-2/ *(via search summary)*, https://www.pcgamesn.com/diablo-4/update-drop-rates
- Season 5 renamed them **Mythic Uniques** and gave them a **unique drop sound, a purple beam and a revamped tooltip**. — https://diablo4.life/guide/mythic-uniques *(via search summary)*
- The fan poll ranked the **Mythic Unique drop sound #1** of all D4 sounds, ahead of the Butcher's "Fresh Meat!". Some players "have never heard the sound." — https://mein-mmo.de/die-besten-sounds-in-diablo-4-laut-fans/
- Adam Isgreen said Blizzard was exploring **bad-luck protection for Ubers**, which split players. For: "To waste peoples' time… with extremely rare drops is a complete insult." Against: "What purpose does the idea of a chase item serve if it's guaranteed after a certain point?" and "Let it actually be special." — https://us.forums.blizzard.com/en/d4/t/blizz-looking-at-bad-luck-protection-for-ubers-and-better-accessibility-for-boss-summoning-mats-in-future/144692
- **The pendulum keeps swinging.** In Season 7 (January 2025), players again felt "inundated," spent "more time sorting items than actually playing," and called the lack of a loot filter "unacceptable." — https://www.dexerto.com/diablo/diablo-4-legendary-loot-overload-2867981/, https://mein-mmo.de/en/diablo-4-loot-geraet-ausser-kontrolle-in-season-7,1220367

---

## 4. Path of Exile 1 and 2: filters, currency jackpots and slower combat

### 4.1 Loot filters as player-authored game feel
- NeverSink's filter has **500+ rules**. It tiers every unique, currency, divination card and fragment by live economy value, refreshing **currency every 4 hours and uniques daily**. Drop tiers run **white → red, with purple "if you're really lucky."** It sets custom font size, colour, **alert sound, beam colour and minimap icon** per tier. Items that need a manual check get a **blue minimap icon**. — https://gitee.com/agg/NeverSink-Filter, https://www.exitlag.com/blog/loot-filter-path-of-exile/ *(via search summary)*
- Sound tiering in practice: a lower sound is used for drops "about one-tenth as exciting as a Divine Orb." Players are advised to mute cheap items and keep loud alerts for Divines. Custom .mp3/.wav alerts are allowed. — https://maxroll.gg/poe/getting-started/lootfilter-advanced *(via search summary)*
- Player voice (official forum, https://www.pathofexile.com/forum/view-thread/3590371):
  - "For PoE1, a custom loot filter is mandatory… running without a filter at all is just madness."
  - "Being able to set my own sounds, colors and cues is a MASSSSSSSIIIVEEEEEEEEEEEEE positive."
  - "sometimes stuff that is valuable drops and you don't see it. I get paranoid that I might miss stuff."
  - "Filters… bridge the gap between loot catering to day 1 players needing white items and day 30 players only caring about certain things."
- **Takeaway:** what players want to hear changes with progression. Something exciting on day 1 is noise by day 30. A filter is a way to move the reward threshold up as the player grows.

### 4.2 Currency jackpots
- **Mirror of Kalandra** is estimated by the community at about **1 in 26,000,000** monster kills. Across the whole player base, one drops roughly every 3 days. — https://pathofexile.fandom.com/wiki/Mirror_of_Kalandra, https://cyberpost.co/how-rare-is-a-mirror-in-poe/ *(via search summary; community estimate)*
- The **Divine Orb** replaced the Exalted Orb as the high-end unit of value. Its drop sound is described as causing "euphoria." — https://www.pcgamesn.com/path-of-exile-2/return-of-the-ancients-divine-orbs, https://steamcommunity.com/app/2694490/discussions/0/565867707171371285 *(via search summary)*
- Jonathan Rogers (PoE2 0.5): "Divines, for whatever reason, are the thing that people use as their way of comparing loot." GGG raised Divine drop rates partly so that "nobody will be able to make the comparison any more" between leagues. The joke alternative was "What if we just remove Divines from the game?" — https://www.pcgamesn.com/path-of-exile-2/return-of-the-ancients-divine-orbs
- **Takeaway:** players pick one reference item and use it to judge whether a session was rewarding. Make sure your game has one deliberately, then tune its rate as a primary knob.

### 4.3 Ruthless: scarcity as reward
- "The quantity of items dropped has been massively reduced throughout all game content." Rings, amulets and belts are "much rarer" and not sold by vendors. GGG: "every item drop has the potential to be the breakthrough one you need… You might get to act four without equipping a pair of rings. But each ring you find represents a huge power boost." It is "not for everyone." — http://www.gamebanshee.com/9kpqx
- Built as a pet project by Chris Wilson and senior developers over about **18 months**. — https://www.poewiki.net/wiki/Ruthless *(via search summary)*

### 4.4 Chris Wilson's design thesis
- GDC 2019, "Designing 'Path of Exile' To Be Played Forever." Topics: seasonal leagues on predictable dates, content reuse, procedural generation, **"multiple overlapping axes of randomness for additional replayability,"** deep systems and community growth. — https://80.lv/articles/gdc-designing-path-of-exile/?amp=1
- Relevant here: stack many independent random layers (map, modifiers, league mechanic, item base, affixes, crafting result) so no two runs feel identical. That is the same principle as survivors level-up drafts combined with run modifiers.

### 4.5 PoE2: slower and more reactive combat
- Jonathan Rogers: "You can't be emitting 500 projectiles a second and covering the entire screen." "There's going to be less overall, just garbage on the ground and more of what you actually want to pick up." The dodge roll "does not make you move faster." The goal: "The most efficient way to play is also the most fun way to play." — https://maxroll.gg/poe/news/pax-west-path-of-exile-2-interview-with-jonathan-rogers
- PoE1 is "proactive" (kill before being killed) and PoE2 is "reactive." Rogers: "good combat involves some level of challenge." — https://sportskeeda.com/mmo/path-exile-2-more-difficult-than-first-game *(via search summary)*
- Reaction: patch **0.2.0** got the worst reception since Lake of Kalandra, largely because skill nerfs reduced endgame viability. GGG then made it a "major objective" to make all skills scale into endgame. — https://www.sportskeeda.com/mmo/path-exile-2-s-next-league-will-make-major-objective-make-skills-endgame-viable *(via search summary)*
- **Takeaway for survivors:** the genre is the "zoom/screen-clear" fantasy. PoE2 shows the cost of pulling it back. Players want screen-clearing as a *payoff* they reach, and deliberate combat in the early part of the run.

---

## 5. Last Epoch: crafting as anticipation and the built-in filter

- **Built-in loot filter** at launch, which reviewers and players widely praised. With a strict filter you see "way less items but those you see are basically an almost guaranteed upgrade." — https://diablo4.life/last-epoch/guides/forging *(via search summary)*
- **Forging Potential (FP)** works as a crafting budget per item. Each craft subtracts a random amount; one example is a T3 upgrade costing **1–18 FP**. Normal crafting caps at **Tier 5**, and **T6–T7 come only from drops**. **Critical Success** makes the craft free and upgrades another sub-T5 affix by one tier. **Glyph of Hope** gives a **25% chance** to spend no FP. — https://maxroll.gg/last-epoch/resources/beginner-crafting-guide
- **Legendary Potential (LP) and the Temporal Sanctum.** A Unique with **1–4 LP** combined with a **4-affix Exalted** item of the same type at the Eternity Cache becomes a Legendary. At **LP 4**, all affixes transfer; below that, a random subset transfers. — https://www.pcinvasion.com/?p=422704, https://icy-veins.com/last-epoch/advanced-crafting *(via search summary)*
- **Weaver's Will (WW)** is an alternative with values **5–28**. The item gains or upgrades one affix per WW point as it "levels." **28** is enough for four T7 affixes. — https://dotesports.com/last-epoch/news/last-epochs-weavers-will-uniques-explained *(via search summary)*
- **Why it works:** a single drop holds a *delayed* reveal. An LP 2 unique is worth a little now and potentially a lot after the Sanctum. That is Brevik's "unwrap it twice" turned into an actual system. The combination happens later, in a dedicated place, which turns it into a small ceremony.

---

## 6. Grim Dawn, Titan Quest, Torchlight II

- **Grim Dawn** aims for "reasonable" drop rates where loot "is still precious and the best items rare." Rarity tiers unlock by level: rares from about **level 8**, epics about **12**, sets about **20**, legendaries about **50**. Monster Infrequents (green) drop only from specific monster types and are "worth hunting for." Exploration and chests are presented as rewards in their own right. — https://www.grimdawn.com/guide/items/the-hunt-for-loot
- **Grim Dawn Devotion.** Points come from restoring shrines across the world and are spent on a **sky map of constellations**. Each star gives stats, completed constellations unlock **Celestial Powers** that proc from class skills, and higher tiers are gated by **5 affinities** (Chaos, Order, Eldritch, Primordial, Ascendant). — https://primagames.com/?p=311758 *(via search summary)*. Devotion is a second, map-shaped progression tree with lore on every node, which suits a story layer.
- **Titan Quest** Monster Infrequents use olive/green text and come from specific enemies; for example, "of the Magi" gear comes only from Act 1 Satyrs. Monsters rarely drop items more than **5 levels** below their own level. — https://almarsguides.com/computer/games/titanquest/misc/gearlists/beginnermonsterinfrequents/ *(via search summary)*. **Takeaway:** "this enemy type drops this family of item" makes it worth caring which enemies you hunt.
- **Torchlight II** pets carry trash loot and **walk to town to sell it and buy potions**, which removes inventory friction while keeping the pickup moment. Its pace is "faster than in the first game… acquiring new equipment and leveling up much faster." — https://selectbutton.com/reviews/torchlight-ii-review. Auto-pickup of gold piles, and gold making a satisfying clink, are widely remembered **[unverified as a sourced design statement]**. Gold-clinking also shows up among the D4 fan-favourite sounds. — https://mein-mmo.de/die-besten-sounds-in-diablo-4-laut-fans/

---

## 7. Lost Ark: spectacle and pity-timed upgrades

- **Artisan's Energy** is a per-item pity meter. Each failed honing attempt adds a percentage; at **100%** the next attempt is **guaranteed**. The meter resets on success, gains less per failure at higher honing levels, and does **not** raise the success rate before reaching 100%. Maxroll shows **+13.49%** per fail as one example. — https://maxroll.gg/lost-ark/resources/gear-honing-system
- Community-documented formula **[unverified this session]**: energy per fail ≈ **46.5% × current success chance**. Each failure also adds **+10% of the base rate** to the next attempt, capped at **2× base**. A 10%-base hone therefore pity-guarantees in roughly 15–20 tries.
- The pre-hone window shows the energy gain in green parentheses before you commit, so the pity is visible and the player can plan for it. — https://steamcommunity.com/app/1599340/discussions/0/3180111158762145739 *(via search summary)*
- **Skill spectacle and tripods:** Lost Ark's skills are known for large VFX, and each skill has 3 tiers of "tripod" modifiers that change its shape. **[unverified; general knowledge]**. This is the same idea as survivors weapon evolution: a skill's look changes when you upgrade it.

---

## 8. Hades I/II: reward as visible choice and character moment

- **Doors show their reward before you enter.** Doors carry symbols for a specific god's boon, a Pom, Daedalus Hammer, gold, a Centaur Heart and so on. This gives "a little more agency in an otherwise entirely random experience." — https://shacknews.com/article/122186/door-symbol-meanings-hades, https://primagames.com/tips/hades-door-symbols-guide-boons-artifacts. Hades II keeps the convention: "Every door… shows you its reward before you walk through it." — https://www.pcinvasion.com/all-hades-2-door-icons-explained/
- **Offer 3, pick 1.** Each boon offers a choice of **three** options. — https://en.wikipedia.org/wiki/Hades_(video_game)
- **Rarity ladder** Common (white), Rare (blue), Epic (purple), Heroic (red), plus Legendary and Duo. — https://hades.wiki.fextralife.com/Boons. Base percentages were not available in reachable sources. My estimate **[unverified]** is Rare about 10% and Epic about 5% before Mirror/Keepsake bonuses.
- **Duo boons** need prerequisite boons from **two** specific gods. Hades I has **28** of them. — https://primagames.com/tips/hades-what-are-duo-boons-how-get-duo-boons *(via search summary)*. Finding a duo shows the player a synergy they built half by accident.
- **Every reward is also a story beat.** Each god appears with a voiced line when offering a boon. The game has about **10 hours** of dialogue structured as "chained events" that respond to progression. Kasavin: "replayability was a foremost goal… story that adapts to player progression." — https://en.wikipedia.org/wiki/Hades_(video_game), https://shacknews.com/article/122186/door-symbol-meanings-hades *(Kasavin quote via search summary)*
- **Chaos gates** (risk now for reward later) and **Pom of Power** (raise an existing boon instead of adding a new one) give a second axis of choice. **[general knowledge]**

---

## 9. Power curves, pity and the "build comes online" moment

- **Exponential multiplicative stacking produces number inflation.** In D3 it led to trillions and quadrillions, abbreviation and colour-highlighting of the top hits (2.4.0), and a **2–5×** DPS jump per seasonal set. It also forced Greater Rift tiers up to **GR150** **[GR cap unverified this session]**. — https://steamcommunity.com/app/219990/discussions/0/133260492057754221 *(via search summary)*
- **Squishes as resets.** D4 started with a stated philosophy against big numbers (Shely, above). Later seasons drifted back into billions, and the Vessel of Hatred patch (2.0) shipped a stat and item squish **[unverified this session]**.
- **The D4 Masterwork breakpoint pattern** (+5% ×9 small steps, +25% ×3 big steps at ranks 4/8/12) is a clean model: frequent small rewards with a jackpot every fourth step. — https://primagames.com/gaming/all-masterworks-ranks-and-effects-in-diablo-4
- **Pity designs compared:**
  - D3 legendary timer: hidden, resets on drop, makes droughts shorter.
  - Lost Ark Artisan's Energy: visible, deterministic cap.
  - D4 Uber BLP: debated. The chase dies if it is guaranteed too soon.
  - Last Epoch: crafting mostly removes the need for pity.
  
  Sources are listed in the sections above.
- **"Build comes online."** In all of these games the moment players remember is when one item or boon joins two previously separate effects: a Duo boon, a D3 set at 6 pieces, a PoE unique that enables a build, a Last Epoch LP 4 legendary. This is better designed as an authored threshold than left to random chance. *(Synthesis)*

---

## 10. What players remember, and what they complain about

**What they remember:**
- The ring "you'd hear" before you saw it (Schaefer, Kotaku).
- The orange beam of light (D3 2.0.1).
- The purple Mythic beam and sound, voted #1 D4 sound even though some players have never heard it.
- The "euphoric" Divine Orb drop sound.
- The goblin giggle.
- Every ring in Ruthless being "a huge power boost."

**What they complain about:**
- "Zero excitement about loot."
- Inventories "full of useless yellows."
- "Loot piñata."
- "Legendaries doesnt feel like legendaries."
- Spending "more time sorting items than actually playing."
- Being "99% sure" they salvaged upgrades without looking. — https://www.dexerto.com/diablo/diablo-4-legendary-loot-overload-2867981/ *(via search summary)*
- Fear of missing drops even with a filter.
- Vendor and inventory trips, which Torchlight's pet errands were designed to remove.

**Pattern:** excitement depends on how *rare* the signal is relative to the noise, not on how much drops. Each studio that over-dropped (D3 vanilla plus the AH, D4 at launch and in Season 7, PoE endgame) had to add either filters or scarcity.

---

## Implications for a survivors-like with a story layer

Tags: **[S]** = directly sourced number or pattern. **[E]** = my estimate or extrapolation for a 15–30 minute survivors run.

1. **Rarity ladder of 5 tiers plus a mythic, shared by every reward system** (drops, level-up cards, relics): white → blue → yellow → orange → green (set/duo) → violet/red (mythic). Blue for magic and gold/orange for "special" are close to universal. **[S: Brevik/Schaefer; Hades; Grim Dawn shows deviation is possible] [E: exact ladder]**

2. **Three-channel announcement for any tier ≥ orange:** a distinctive sound, a vertical light beam in tier colour, and a minimap or edge-of-screen pip. Keep beams strictly for real rarities, as D3 did when it removed the GR-key beam. **[S: D3 Leg page, GR key beam removal]**

3. **Sound before sight.** Give each item family a short (≤ 400 ms **[E]**) physical sound: glass for gems, metal for rings and runes, a low bell for mythic. Mythic gets a sound that plays **nowhere else in the game**. **[S: Schaefer ring sound; Petersen wine-glass gems; D4 Mythic sound ranked #1]**

4. **Drop budget: about 1 orange per 3–5 minutes of a run and about 1 mythic per 10–20 runs. [E]** D4 learned that fewer and better drops beat volume: "fewer items will drop overall," with legendaries cut to 3 affixes. **[S: S4 notes]** In a survivors game, auto-vacuum common pickups (XP, gold) and only make the player physically walk to tier ≥ orange.

5. **Visible pity for the chase tier.** Show a meter that guarantees a mythic or heroic offer by about 1.5× the expected interval (for example, guaranteed by run 25 if the median is 15). **[E]** Show it the way Lost Ark shows the gain before committing. **[S: Artisan's Energy, 100% guarantee, +13.49% example]** Keep the guarantee late enough that the chase still exists, which was the D4 BLP objection. **[S]**

6. **Hidden bad-luck protection on orange drops:** about +10% relative chance per minute without one, reset on drop. **[E]** Pattern from D3's legendary timer. **[S]** Bias **about 85%** of offers toward the current build (smart loot). **[S: 85/15]** Keep about 15% off-build to tempt pivots. **[E]**

7. **Show rewards on the door.** Between arenas or chapters, offer 2–3 exits, each showing its reward icon, and attach a short voiced or text line from the faction or patron behind it. **[S: Hades door icons, 3-choice boons, about 10 hours of chained dialogue]** This is the most direct bridge between loot and story.

8. **Duo/synergy cards keyed to two "patron" lines,** about 1 duo per 6–8 patron pairings, and around 20–30 total duos at launch. **[S: Hades has 28 duos] [E: scale]** The first discovery of each duo should get a one-time codex and story beat.

9. **Breakpoint rhythm for upgrades:** small steps (+5%) with a jackpot every 4th rank (+25% to one random stat, plus a colour shift on the item frame). **[S: D4 Masterworking 12 ranks, +5% / +25% at 4/8/12]** Use this for weapon levels within a run (for example levels 4/8 = evolution-lite, 12 = evolution). **[E]**

10. **Delayed second reveal ("unwrap it twice").** Uniques drop with a hidden "Potential" of 0–4 that is revealed and fused at a narrative location such as a shrine or altar between runs. Model it on Last Epoch LP: 4 = full transfer. **[S: Brevik quote; LE LP 1–4, WW 5–28]**

11. **A single reference currency** that players will use to judge a session, the role Divine Orbs play. Make it rare (about 1 per 2–3 runs **[E]**), give it a unique sound, and use it for the deepest meta-unlocks. Tune its rate as a primary knob. **[S: Rogers, "the thing that people use… comparing loot"]**

12. **No auction house or direct purchase of top-tier drops.** Any shop that sells the best power devalues drops. **[S: Wilson, AH "really hurt the game," 3M users, >50% regular use]** Shops should sell rerolls and banishes, not finished power.

13. **Cap on-screen numbers.** Plan for a maximum displayed hit of about 6 digits in normal play, using abbreviations (K/M) and a **separate colour or size** for the top 5% of hits. **[S: D3 2.4.0 abbreviation and highlight] [E: thresholds]** Prefer a mostly additive within-tier power curve with 3–4 multiplicative "build online" spikes per run, over open-ended exponential growth that forces a later squish. **[S: D3 trillions; D4 squish discussion]**

14. **Trickle meta-progression after the main curve ends.** After the core unlocks, use Paragon-style +1 points across about 4 small tabs with per-node caps, so every run grants something. **[S: D3 Paragon 4 tabs, 50 cap, 800 full]** Keep each point small (≤ 0.5% **[E]**) so run skill still dominates.

15. **An auto-filter that tightens with progression.** In the first hour, show everything. After meta-milestones, auto-suppress tiers below the player's current floor (for example, whites stop dropping after unlocking X), and let players toggle this. **[S: LE built-in filter praise; PoE "bridge day 1 / day 30"; D4 filter demands]**

16. **Signature enemy drop families.** Specific enemy archetypes drop specific item families (Titan Quest and Grim Dawn Monster Infrequents). This gives targetable farming and keeps randomness from feeling uncontrollable. **[S: TQ "of the Magi" from Satyrs; Brevik on targetable bosses]**

17. **A "goblin" event about once per 5–8 minutes [E]:** a fleeing enemy announced by sound before it is seen, carrying a guaranteed tier-up drop, with an escape timer of about 10–15 s **[E]**. **[S: D3 goblin giggle design]**

18. **Short boss-loop as the "one more run" unit.** Allow a 3–5 minute "hunt" mode against one named boss with a guaranteed orange and a long-tail mythic, so players can do the equivalent of a Mephisto run. Use a long tail in the D2 style, about 1/200 per kill for the top chase **[E]**, but layer the visible pity from #5 on top. D2's real high-rune odds (Zod about 1/192,066 even from a top boss) are too harsh for a session-based game. **[S: D2 numbers; Mephisto loop]**
