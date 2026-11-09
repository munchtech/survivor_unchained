# The ARPG: the loop, the systems, the migration

The ARPG design lead, 9 November 2026, from the owner's words of 8 November (`ARPG_DIRECTION.md`, `SIEGES.md`). **A proposal for the owner's pick: design only, no game code.** Where `ONE_BUILD.md`, `CLASS_IDENTITY_AND_TALENTS.md` and `STORY_NIGHTS_AND_TIME.md` describe the night as the game, this page wins; everything else in them stands and is reused by name below.

## For the owner (one page)

**What the game is now.** Diablo's loop in our valley. She walks the zones of an act, fights packs and their captains with six skills she presses, dashes out of what is telegraphed, kills named champions and the act's bosses, and picks up loot where it falls. Towns sit between zones. Her build grows through levels (each one lights a lamp), gear and Unions. The survivors night becomes the arena: a side door, never the road.

**A first hour.** The storybook tale, then the drowning. She wakes by a fire on the Low Ford road at night with a greatsword, and the game teaches one thing at a time, each with a freeze-frame arrow:
- hold the mouse to swing;
- the ember the dead spill is how she grows;
- Groundbreaker on the right button;
- the first pack and its captain;
- her first level, and a lamp lit where she stands (*Third Blow*: every third swing lands heavy);
- a Rare's beam, and the filter;
- a charger's lane, crossed with the dash;
- the Barrow Knight, with his bar and his name;
- a lamp-post relit: her checkpoint and a waypoint.

At the water the Ford-Warden waits, and the ember lends her the Flare to break his lamps. First light takes the Flare back on one storybook page; she keeps everything else, and a Legendary from him. By day the same road runs on: boars, the Kerchiefs, a strongbox, Heroic Leap at level 4, the wolves' ring at the gate, then the Waystation, where the Flare is lit for good. About 45 minutes, five levels, four skills. The dash stays her evade; its steps come from story beats and gear, shown as pips, never from a level-up press. All six keys are hers by the Barrow, at Act 1's end, about five hours in, and her first Union (Bladestorm) comes just after.

**A veteran's hour.** Level 30, on the hardest difficulty open to her, six keys:
- Sunder held to swing, building her Resolve;
- Cleaver's key held to spin, burning the Resolve Sunder built: Bladestorm, a Union of the two, and a fresh press of Sunder mid-storm breaks it and splits the ground;
- Heroic Leap into the thick of it;
- Shield Charge to cross to the next pack;
- the Watch Bell to drag it onto her shield;
- Iron Vow when the brute winds up.

She runs four or five endgame maps: generated ground, twists that test her build, a ruler at the end. Then she plays the day's challenge at the Wayfinder's table.

**The arena.** Today's night, kept whole: twelve minutes, the tiers, the endless, the horde. One rule changes: the ember casts her skills for her, and she moves, dashes and Flares. Each time the ember rises she lights a lamp on a skill she carries until first light: try before you buy. Each day brings one challenge: the same seed and rule for everyone, a loaned build, a board and a cache. It is never required.

**A siege, one day.** At an act's climax, a city's districts hold against the dead until dawn: squads to rally, gates and oil to prepare, assault groups with routes, and her same build. None of it is built now. What we build now (the director, the telegraph kit, the crowd, the lamps) keeps the doors open for it.

**Your calls** are in section 10. The first one changes the most: **skills are pressed** (Diablo's six keys) rather than fired on their own.

---

## 1. What exists (measured 8-9 November, two read-only code surveys and the docs)

| Piece | Today | Where |
|---|---|---|
| Input | She presses only Move, Dash (Space/Shift), Flare (Q/RMB), Draught (R) and Interact (E/F). The hover target sets a priority foe. The draft picks with 1-4. LMB is unbound. No click-to-move | `src/Game/Controls.cs:44-75`, `WorldScene.cs:262-272`, `Game.cs:1619` |
| Skills | 39 in `skills.json` (30 skills plus 9 unions), and **every one fires itself** on a timer at a target rule (nearest, densest pack, farthest). 52 evolutions (rank 8 plus a catalyst). The skills lead's WIP (skills-p7@9aba4f9c5) adds `cast: press/channel`, slot keys and Bladestorm | `Content/Abilities.cs:9`, `Sim/Weapons.cs`, `Sim/PressedSkills.cs` (WIP) |
| The dash | 2 charges, 2.6 s each, 5.5 m, i-frames 0.3 s; a 0.18 s perfect dodge hands one back. The calling's art rides the first dash after its own wait (the warden's Bull Rush: 6 m behind a 15% barrier). Night boons change it out of sight | `Abilities.cs:243`, `Forms.cs:63-118`, `Boons.cs:239-293` |
| Unions | 9; the night's draft offers one once both parts are evolved; it merges them into one slot and frees the other | `Content/Unions.cs:4-13`, `LevelUp.cs:611` |
| Build | Slots 2/3/4/5/6 at levels 1/4/8/14/20. Rank 1+(L-1)/3, at most 8. Cap 30. Lamps v1 (360) is live; v2 (574), `board_v2` and `skill_lamps.json` (7 warden skills, 84 lamps, 68 of them needing new engine work) are data. A Lamps screen exists (L) | `Rpg/SkillBook.cs:69-72`, `Character.cs:661`, `src/Ui/LampsScreen.cs` |
| Zones | Three hand-made: **the Low Ford** (260 m: the prologue night, then the day stretch's 8 beats), **the Verge** (290 m: placed packs, the dead placed at night, four story spots) and **the Waystation** (180 m: the town and the table). "The Deep Shaw" is a name the table generates, not a place | `data/zones/*`, `Play/Zones/*.cs`, `Maps/ArenaPlaces.cs:49` |
| Story fights | 4 (the Hollow, the Roost, the Dig, the Vault with Corvane's doorway), after dark. Each is a short night with a draft from nothing, built from capsule rooms with stage gates, ending in a scripted boss whose numbers are data | `Play/StoryFights.cs:34`, `Story/StoryPlace.cs`, `teeth.json story.*` |
| Director | The table night: a count by minute and tier, an event a minute, heralds, the boss at 10:00 on tier 1, then endless. H6's crowd director (pincers, surround, recall; `teeth.json`, tier 1 only), the chargers' director, and 4 telegraph kinds with 13 waves | `ArenaRun.cs`, `ArenaRun.Director.cs`, `Charges.cs`, `telegraphs.json` |
| Maps | Generated (MapGen); `MapRun` already plays like an ARPG map (placed packs that rest until she is near, keepers, a ruler, no refills); charts | `Maps/MapGen.cs`, `MapRun.cs:21-37`, `Charts.cs` |
| Foes | 70 kinds, 35 flagged elite, elite bars; **no champion affixes** | `Content/Enemies.cs`, `Ui/FoeMarks.cs:73` |
| Loot | 6 tiers plus sets, 121 item definitions, 44 affixes, the filter (4 presets, 5 toggles), chest ceremonies, crafting, 6 shops, 7 quests | `items.json`, `Rpg/Items.cs:167`, `LootFilter.cs`, `crafting.json` |
| Death | The prologue forgives. A lost story night wakes her in the shrine a day on. A table night simply ends. A map closes and spills half | `Prologue.cs:30`, `StoryNight.cs:25`, `MapRun.cs:34` |

---

## 2. The systems table

| System | Verdict | Why, in one line | Cost (section 9) |
|---|---|---|---|
| The 39 self-firing skills | **REWORK** | Each gets a pressed form (a kind, a cost or wait, an aim) and keeps its own rule for the arena | M3 (most of its ~3.3M) for the warden; each later calling in its wave |
| The night's ember cards (`LevelUp.Draft`) | **MOVE TO ARENA** | Try-before-you-buy is the arena's identity; a draft freezing a Diablo fight every minute is not | M7-M8, ~0.3M |
| Lamps and Wicks | **KEEP**, rework the point rate | The board stays the passives and the Wicks the skill trees. Points no longer come from the ember, so the rate rises (section 3.5) | M7, ~2M |
| Lamp-posts and *Light my way* | **KEEP**, more jobs | A lamp-post is now her checkpoint, a waypoint, the respec bench and the safe light at night; the act's four dark posts off the road (CLASS_IDENTITY, 12 in all) give a board point when relit, and checkpoint posts give none; *Light my way* lights what she leaves at each level | M5 and M7 |
| The Flare | **KEEP** | The BOOM stays outside the six slots. The prologue lends it once (section 5); its fill is re-measured under pressed combat | part of M3 |
| The tiers and the endless | **MOVE TO ARENA** | They are the arena's difficulty and its long night; the campaign uses world tiers | M8; world tiers in M5 |
| The Wayfinder's table | **REWORK** | It becomes the door to the arena, the daily and the atlas (charts): the endgame's hub | M8, M11 |
| The day stretch | **KEEP** as the template | Its eight beats (packs, ambushes, a strongbox, a lamp-post, a gated ring) are an ARPG zone already. `DayStretch.cs` becomes every zone's encounter list | M5 |
| The director and the telegraph kit | **KEEP** | The director runs the arena as it is and is the siege's seed (section 8). The kit becomes champion affixes and boss blows in every zone | M5, ~0.8M for affixes |
| Loot and the filter | **KEEP**, rework the cadence | Loot falls on the ground in zones, with no night's-end tally; one carrier per pack; the first Legendary comes from the Ford-Warden (section 7) | M9, ~0.6M |
| Crafting | **KEEP** | The forge in town, with materials in a third of gear's place, as LOOT_DESIGN measured | none |
| Towns and shops | **KEEP** | The Waystation is Act 1's hub | none |
| Quests | **KEEP** | The two troubles, the vault and the lamps already lead through the act's places; their marks now point at zones and dungeons | M10 |
| The story nights | **REWORK** into story dungeons | Her whole build, placed packs, a set piece, the boss as built. The capsule rooms and boss scripts are reused; the waves and the draft go | M10, ~2M for four |
| The dawn card | **MOVE TO ARENA**, plus one page | It ends every arena run. In the campaign it survives once, as a storybook page at the prologue's first light (section 5) | M6, M8 |
| The harness bots | **KEEP**, taught to press | Human, deft and careless press by priority; standing and idler stay. A zone sim measures an hour (kills, drops, falls) | part of M3 and M5 |
| The dash's riding arts and night boons | **DROP** the ride | What she presses is what happens (section 3.4). The riding arts become pressed skills | M1 |
| Unions (the merge that frees a slot) | **REWORK** | One skill on both keys (section 3.3) | M1, M7 |
| `SkillBook` tomes | **DROP** | Already cut by ONE_BUILD: skills open by level | M7 |
| The day's 12-minute clock and "Answer the night" | **REWORK** | Time of day follows the story; waypoints replace the pull (section 6) | M10, ~0.3M |
| The Verge's ember scars | **DROP** | The table is the arena's one door | M8 |

---

## 3. Skills

### 3.1 Pressed by default (the owner's call 1; my pick)

**Six keys, Diablo's way.** Every carried skill is one of three kinds, and its record says which.
- **Pressed:** it fires on the press, or on the hold, repeating when ready. It aims at the hover target if one is in reach, otherwise at the cursor's point (on a pad: the stick's pick, else her facing). This is most skills.
- **Channeled:** it runs while held (Bladestorm), and she keeps moving at part speed.
- **Kindled:** a few skills fire themselves once slotted, because pressing them would be a chore: Rebuke on a block, auras, summons. They still take a slot, and each keeps a press so no key is dead: Rebuke's key readies a riposte for 2 s, an aura's flares it for 3 s, a summon's commands or recalls it.
- **Never rooted:** a press never roots her. Blows and casts play on her upper body while she walks at 70% speed; only the heavy commits (Sunder's heavy swing, Groundbreaker's heave, Iron Vow) plant her, for at most 0.3 s. Self-firing let her swing while she walked, and a swing that roots her would bring back rc2's standing still.

**The rhythm comes from a resource.** The grip (LMB, hold) builds the calling's resource and the big skills spend it, while movement and defense run on waits. That is Diablo III's generator, spender and cooldown, the genre's most proven rhythm. Without a resource, six keys collapse into "press whatever is lit".
- The warden's resource is **Resolve** (a working name for the story lead). Her landed blows, the blows she takes and her blocks fill it: only she gets stronger by being hit, so it is her identity in a bar. Blows taken and blocks give at most a third of its fill and landed blows the rest, so she fills by going in, never by standing. It fades slowly out of a fight.
- The reaver's resource is her Frenzy, already her mechanic. The arcanist's and the stalker's are named in their waves.

**Keys:** LMB, RMB and 1-4, Diablo's own layout, are the default. RMB leaves the Flare, which keeps Q, and 1-4 are free in the campaign (the draft's picks go to the arena with the cards). Q-E-R-F, beside WASD, is the second preset, and under it the Flare, Draught and Interact move. On a pad the six go to the face buttons and the right shoulder and trigger; the dash, Flare and Draught go to the left shoulder, trigger and d-pad, and Interact shares a face button out of a fight. The UI lead places them, and the HUD.

**Where self-firing stays:**
- the kindled skills;
- the board's Links (a trigger fires a skill she picks: PoE's cast-on-crit, a planner's choice);
- the arena's rule (section 4).

Every skill keeps its self-firing rule for the arena, so an assist setting ("the ember casts for me" in the campaign) would cost almost nothing later. It is not proposed now.

**Why pressed:**
- Both demos' notes were about agency: "skill expression thru 2 buttons (dash and ultimate)" (rc1); "standing still letting everything come to me" (rc2).
- The owner's new skills are pressed in every game that has them: a leap to a point, a spin she steers.
- The goal line, "an approachable Path of Exile", holds. The pushback on record is that PoE's barrier is information, not hands, and Diablo III and IV are the approachable ARPGs, both pressed.

**The cost:**
- Every skill's timer becomes a wait or a cost, and its target rule becomes its aim assist. Most of that is data on the skills lead's switch.
- The harness's bots learn to press.
- Every skill, lamp and Union is written for both modes, for good. A cost or wait lamp translates to the arena's cadence (-10% cost is -10% interval); a channel fires itself for its full time; the ember fires a bond when its first half is at full charge; the harness fails any lamp that does nothing in either mode.
- Every press needs its cast clip (the disc's throw, the bell, the brace, the heave), so A1's Stage B list is re-cut for a pressed game (section 9, A1).
- The CLASS_IDENTITY rule "a combat skill never moves her" is retired, for movement skills only.

### 3.2 The warden's kit in the ARPG (the first slice; numbers are the combat lead's)

| Skill | Kind | Pays with | On the press |
|---|---|---|---|
| Sunder (the sunderer's grip) | pressed, hold | builds Resolve | The slow cleave; every fourth swing is heavy and splits a 7 m line toward the cursor |
| Oathblade (the bulwark's grip) | pressed, hold | builds Resolve | The wide swing that turns blows |
| Groundbreaker | pressed | Resolve | The crack runs to the pack under the cursor; the heave stuns |
| Judgment Disc | pressed | Resolve | Thrown at the hover target; it bounces five times |
| Dawnpulse | pressed | Resolve | The ring of light around her throws back what it touches |
| Watch Bell | pressed | a wait | Draws everything within 8 m onto her, with barrier for each |
| **Heroic Leap** (new, skills lead) | pressed, aimed | a wait | She jumps to the cursor and lands in a slam |
| **Shield Charge** (Bull Rush, reworked) | pressed, aimed | a wait | She charges to the cursor shield-first and knocks lesser things aside. Its wick takes the four facets the skills lead wrote (Iron Hide, Unbroken, Gore, and Pile Driver as its Turn) |
| Iron Vow | pressed | a wait | A 2 s brace: blows on her are halved, and what she stored bursts |
| Rebuke | kindled | on a block | Smites the blocker and three near it |
| Cleaver (shared with the reaver) | pressed | Resolve | The heavy chop across her front; it opens wounds |
| **Bladestorm** (Cleaver + Sunder) | channeled | drains Resolve while held, no wait | The spin. A fresh press of Sunder's key breaks it, and the break grows with what the storm spent; a grip held into the storm doesn't break it |

### 3.3 Unions: one skill on two keys

**The rule (the owner's):** two carried skills combine into one skill that takes both slots, never a seventh.

**The pushback:** taken literally, a Union is one key in two slots, which leaves the second key dead and makes the Union a loss on a four-slot bar. Players would skip it: it is the two-slot skill that never fires.

**The fix:** a Union keeps both keys, one per half, and joins them with a **bond**: what one half does to the other. Bladestorm is the model.
- Cleaver's key, held, spins her through the crowd with the blade out, a cut every turn.
- Sunder's key breaks the storm: she plants the blade, and every heavy line she threw in the spin splits at once. The longer the storm, the bigger the break.

Each half is still its part: the part's wick, rank and Turn apply to its half, so no lit lamp is lost. The Union adds the bond and its own look. The first half may become a new action (Cleaver's chop becomes the spin). The second half keeps its part's own action and gains the bond when pressed during, or within 1 s after, the first: outside a storm Sunder still swings and builds Resolve.

**Gate and cost** (ONE_BUILD's, kept):
- It opens when both parts burn a Turn, and it costs one point from each.
- Joining and unjoining are free at a lamp-post.
- With section 3.5's rate, the first Union arrives about level 11, at Act 2's door, when all six of her slots are open (call 13).
- The harness holds it honest. A Union build beats the same two skills apart by ×1.15-1.3 at equal gear: power and a combo for the two slots, never mandatory.

**The first Union list** (working names are drafts for the story lead; "built" means it is in `skills.json` today):

| Calling | Union | Parts | First key | Second key (the bond) |
|---|---|---|---|---|
| Warden | **Bladestorm** (skills lead, building) | Cleaver + Sunder | hold: the spin | the storm breaks; the thrown lines split |
| Warden | **Dawn's Judgment** (built) | Judgment Disc + Dawnpulse | the disc ricochets and breaks into light | recall: it flies back through everything, and the dawn bursts on the catch |
| Warden | **Earthfall** | Heroic Leap + Groundbreaker | the leap; the landing cracks to the three densest packs | heave: every crack at once, stunning |
| Warden | **The Last Bell** | Watch Bell + Rebuke | the toll drags all within 8 m onto her shield | for 2 s every blow on her answers on its striker and three near it |
| Reaver | **Gallows Wheel** | Red Whirl + Chain Lash | hold: she whirls with the chain out and hooks what it touches | yank: the hooked are knotted at her feet and hoisted |
| Reaver | **Butcher's Wheel** (built) | Axe Gyre + Cleaver | the cleavers circle and never stop | fling the wheel at the farthest bleeding; it returns |
| Reaver | **Red Knot** | Anchor + Rend | the anchor Binds everything within 5 m and yanks it together | the knot bleeds out: 3 s of bleed at once |
| Reaver, Arcanist | **The Tempest** (built) | Thunderhead + Arcweb | the cloud over the cursor | the lightning leaps from every shocked thing at once |
| Arcanist | **Frostfire Comet** (built) | Cinderfall + Rimeshard | the comet bursts and freezes what it does not burn | shatter: everything frozen in sight explodes |
| Arcanist | **Starfall** (built) | Moonbrand + Seeking Motes | moonfire marks what it tracks | moons fall on every mark and break into hunting motes |
| Arcanist | **Thaw Line** | Rime Field + Pyre Line | frost under the cursor | fire across it; what is frozen in its path shatters |
| Arcanist, Reaver | **Soul Lantern** (built) | Umbral Bolt + Grave Tether | the bolt marks for the grave | draw it back: every mark gives life |
| Stalker | **Hail of Steel** (built) | Volley + Knifestorm | arrows and knives in every direction | the blades in the air turn on the nearest wounded |
| Stalker | **Rotwood** (built) | Blightfield + Thornbloom | the thicket holds what it rots | it bursts, and the rot spreads from what dies in it |
| Stalker | **Shadow Step** | Shadow Double + Cutting Wake | her shadow stays and repeats her blows | she swaps places with it, leaving blades along the way |
| Stalker | **The Stoop** | Heartseeker + The Hawk | the heavy arrow pierces the line | the hawk dives where it struck |

Access follows CLASS_IDENTITY's circles; The Barrow Host (built) stays open to the reaver and the stalker. Every bond is a press that cashes in what the first key built, so each Union reads as a combo, not a merge.

### 3.4 The dash and movement (sent to the skills lead on 9 November; the owner: "just pushing the button leveling it up is weird")

- **The dash stays the dash**, everyone's evade on Space. Space takes her out; the Charge and Leap keys take her in. Nothing rides the dash on a hidden wait. The riding arts become pressed skills: Heroic Leap and the warden's Shield Charge now, and each calling's art in its wave.
- **Every step is visible and named,** from `dash_steps.json`: Another Breath (a charge), Long Stride, Quick Breath, and Hard Landing (the warden's shove as the ending).
- **Where they are earned:** the steps (a charge, the stride, the breath) come from story beats and gear, each shown when it lands (the third pip is an Act 1 reward). The board's hearth lamps hold only the endings (the warden's shove), a choice against other lamps. Never from a level-up card or the ember's cards: a point spent on a longer stride would still be "pushing the button leveling it up".
- **How they show:** pips with a refill ring under her life (the owner liked it, rc2), a before-and-after line and a short loop on the dash's panel, and the ending's own effect in play.

### 3.5 Where the lamp offer lives (the owner's call 4; my pick)

**Levels light lamps, lamp-posts change them, and the cards are the arena's.**
- **Slots (call 13):** 2/3/4/5/6 at levels 1/4/5/7/9, so all six keys are hers by the Barrow at Act 1's end. Today's 1/4/8/14/20 would leave six keys for Act 3; Diablo III's six come two or three hours in. Heroic Leap opens at level 4 with the third slot, and Shield Charge at 5 with the fourth.
- **What a level gives:** each level is a board point, plus the act's four dark posts off the road. Each carried skill has its own wick points: one at level 1, then one every second level, to 8 at level 15 (today one every third, 8 at level 22).
  - The night's ember used to light lamps for free; without it, the old rate would bring the first Turn at level 13, deep in Act 2. At the new rate the first Turn lands at level 9, on Act 1's last boss, as CLASS_IDENTITY §5.1 planned.
  - Gear's new "+1 to <skill>" affixes add up to three more points: a chase, and Diablo's oldest good affix.
- **Lighting:** anywhere out of a fight. The level-up flash shows the suggested lamp with the skill's hit before and after; one press lights it, or *Light my way* does it for her.
- **Changing:** putting lamps out, layouts and Unions are free at any lamp-post. Lamp-posts come every few minutes (they are her checkpoints), so planning is near and cheap.
- **Why not cards in the campaign:** a three-card freeze every minute is the survivors cadence; Diablo's level-up is a flash and a choice she makes when she likes. Why not lamp-posts only: a point she can't use for ten minutes is friction on the genre's best drip.

---

## 4. The arena mode (the Wayfinder's table)

**Kept whole from today:**
- the night's shape: about 12 minutes on tier 1 (the boss at 10:00, about 2:15 to kill);
- tiers 1-4 and the endless after the boss;
- H6's crowd director and the kit's 45-60 s rule;
- her whole build from minute 0 (ONE_BUILD §1);
- the ember's offer (ONE_BUILD §2, every card a lamp on a skill she carries) and the dawn card's memory and price lines (ONE_BUILD §3), now pointing at the campaign's points;
- chests and the night's-end tally;
- the harness gates: standing falls 80%+, idler 70%+, the human wins 78-85%, the deft 95%+. The idler gate becomes the arena's balance gate, no longer the game's.

**The one rule (the owner's call 2; my pick): the ember casts for her.**
- Her skills fire on their own rules, as today, and cost nothing.
- She moves, dashes and Flares, and her movement skills (the leap, the charge) stay hers.
- This is the owner's "mindless survivors fun" (CLASS_IDENTITY §5.2), and the reason to play the arena beside the campaign rather than a harder zone. It reuses today's whole night.
- The trade: it bends 4 November's "one combat" in this one mode, on purpose. Her build, numbers and lamps are the same; only the hands differ.

**The daily:**
- one seed (the place, the people, the events) and one rule from a deck of about twenty (*Bright Hour*: the Flare fills twice as fast; *Hunted*: a herald from minute 2; *Lampless*; *Red Moon*: everything bleeds);
- one loaned build that everyone plays, three a week, so players meet builds they would never make (Diablo III's challenge rifts);
- the first attempt is scored on a local board, and on Steam's boards at the store build: how far she got (the minute, then the boss's kill time), ties broken by kills;
- a second daily on her own build is a later choice.

**What it pays into the campaign, never required:**
- the day's first daily: a Wayfinder's cache (gear at her level, materials, never a certain Legendary) and cosmetics for marks (lamp colors, dyes, a title);
- the table's nights: gear and experience at her level, the experience at most 60% of a campaign hour's, so the arena is never the leveling road;
- Legendary homes huntable by people (LOOT_DESIGN §5.3);
- the dawn card's lamp suggestion.

---

## 5. The tutorial, ARPG only

**The storybook lore intro (SB00) and C01 stand,** ending in the drowning. Then the Low Ford, one lesson at a time, each with a freeze-frame arrow callout (18 October):

| # | Where | It teaches | The callout points at |
|---|---|---|---|
| 1 | She wakes by the fire (night) | move | the stick / WASD |
| 2 | A lone drowned one at the fire's edge | hit: hold to swing | LMB on the bar |
| 3 | The ember it spills | the ember is the dead's light: it fills her bar and rises into a level | the ember bar |
| 4 | Three on the road | a skill: Groundbreaker; Resolve pays for it | RMB and the Resolve bar |
| 5 | The first pack and its captain | a pack; the captain carries gear | the captain's lantern |
| 5a | Her first level, on the road | a lamp: the level-up's flash offers *Third Blow* (every third swing lands heavy), lit where she stands with the wick point she has held since level 1 | Sunder's wick, before and after |
| 6 | The captain's Rare | loot: the beam, the label; the filter hides the rest | the label, then the filter's key |
| 7 | The ambush's charger | the dash through a telegraph | the lane, then Space |
| 8 | The Barrow Knight at the post | the first elite: a bar, a name, an affix | the bar and the affix |
| 9 | The post relit | a lamp-post: her checkpoint and a waypoint | the post's light on the map |
| 10 | The barrow's Grave-Caller | a raiser: kill it first | the hover target |
| 11 | C02, the Ford-Warden | the first boss: his three lamps; the ember lends her the Flare | the Flare's key |
| 12 | C03, then first light | one storybook page: first light takes back what it lent (the Flare); she keeps the rest | none |
| 13 | C04 A, then the day stretch | the zone by day: packs, a strongbox, ambushes, Heroic Leap at level 4 with the third slot, taught at the wolves' ring holding the gate; Shield Charge at 5 with the fourth | each new key |
| 14 | The Waystation, C04 B | the town; the Flare lit for good at the square's lamp | none |

- **Films:** C01, C02, C03 (and their warden variants), C04 A and C04 B all stay. The prologue's night stays as setting and story ("None cross after dark"). What goes is the night's mechanics: the rising's draft, waves and the dawn card as a system.
- **Cut callouts** (`TUTORIAL_COPY.md`): F2 (the ember rising into cards), F3 (the great blessing), F4 (the skill draft), F5 (lent skills) and F12 (the night's levels). F1 is re-aimed so the ember is experience. Words are the story lead's.
- **Pushback, the one dawn page:** the brief says "nothing about dawn cards", but Act 4's "the first light that takes nothing back" (PLAN.md §3) needs the rule taught once. So the ember lends one thing for the Warden fight and first light takes it on one page; nothing she earned is ever taken. It shrinks the owner's rc2 "losing everything after the warden fight feels bad" to one thing, lent and named as lent, back for good at the Waystation about 15 minutes later; call 10's other branch drops even that. The ember as experience also makes the Act 4 reveal ("ember is them") cut deeper: every level she ever gained was the dead.

---

## 6. Acts, zones and the endgame

**Pick (the owner's call 5):** handcrafted acts with set zones and story dungeons, as in Diablo IV, and generated maps for the endgame, as in Diablo III's rifts and PoE's maps. Authored landmarks and set pieces on generated layouts (Diablo II's and PoE's campaigns) are M10's cost lever; L1 says which the Verge zones use.
- The story is about 40% of the early game, and it needs landmarks, set pieces and places people remember; the endgame needs variety without end.
- We have both today: three hand-made zones, and `MapGen`, whose `MapRun` already plays like an ARPG map.
- A dungeon can mix them: authored set-piece rooms (the StoryPlaces) joined by generated halls.

**Act 1's map** (the Waystation, chains 1 and 2):

| Place | Today | In the ARPG | Levels |
|---|---|---|---|
| The Low Ford | the prologue night and the day stretch | zone 1: the tutorial and the road to town; the Ford-Warden | 1-4 |
| The Waystation | the town | Act 1's hub: shops, the forge, the shrine, the stash, the Wayfinder's table | none |
| Thornhollow Verge | 290 m, placed packs, the dead at night, four story spots | zone 2, grown into three zones (its fields, the Deep Shaw, the ravine) | 4-10 |
| The Deep Shaw | a name the table generates | one of the three: the real wood between the Verge's fields and Wolf Hollow (the arena keeps its board) | 5-7 |
| Wolf Hollow | a story night (Greymuzzle) | dungeon 1, the den | 5-6 |
| The Roost | a story night (Redcowl) | dungeon 2, up the ravine | 6-7 |
| The Dig | a story night (Grimtunnel) | dungeon 3, the tunnels | 7-8 |
| The Barrow, behind the sealed door | a story night (Corvane's doorway, the Barrow Lord) | Act 1's last dungeon: chain 2, the first Turn | 9-10 |
| barrow, hollow, ruts, dig | the table's place kinds | the arena's boards, unchanged | none |

- **The honest size:** Act 1's sum is the Low Ford (45 minutes), three Verge zones of about 30 minutes, four dungeons of 20-30 minutes and about an hour of town and story: about 4.5-5.5 hours. The Verge crosses in under a minute, so that needs new ground. It is the long pole (section 9, M10).
- **Time of day (the owner's call 9):** it follows the story. Each quest step sets the hour, dusk plays the town's evening call, the inn's sleep stays, and the running 12-minute clock and "Answer the night" retire. Waypoints (lamp-posts) take her to a fight, and the story's night fights stay at night.

**The endgame:**
- the atlas: charts at the Wayfinder's table open generated maps on world tiers III-IV, with mods by tag (CLASS_IDENTITY §5.2), keepers, a ruler, and Legendary homes hunted by people;
- the arena's dailies, tiers and endless;
- later, the dead's nights in cleared zones: a zone at night belongs to the risen, D4's Helltide in our lore. The Verge already places the dead at night;
- the sieges.

---

## 7. Loot, death, difficulty

### 7.1 Loot cadence under an ARPG hour (the owner's call 6)

LOOT_DESIGN's Act 1 run (215 gear drops and 3.5 Legendaries over about five hours) already works out to about **40 gear drops an hour**. The rate holds; the shape changes.

| | The first hour (levels 1-5) | An Act 1 hour | A veteran's map hour |
|---|---|---|---|
| Kills | ~500 | ~700 | ~1,500 |
| Packs, each with a captain | ~40 | ~60 | ~100 |
| Champions (named elites with affixes) | 4-6 | 10-12 | 20-30 |
| Gear shown (the Default filter) | ~25 | ~40 | ~60 |
| An upgrade worth wearing | every ~8 min | every ~15 min | a better roll every ~45 min |
| Legendaries | 1, certain, from the Ford-Warden | ~0.7 | ~2-4 (tiers III-IV, atlas weights and homes) |

**The rules that change:**
- In zones, loot falls on the ground, with no tally. The captain is each pack's carrier (gear at about 40%), so "only what visibly carries gear" holds.
- Materials fall on the ground in gear's place.
- When a zone resets, Rare and better left behind goes to Rook's storeroom.
- The certain first Legendary (Diablo III's first-kill rule) moves to the Ford-Warden: the owner's "huge dopamine spike" at low level, in the first 45 minutes.
- The dark's debt and the homes stand. The numbers are targets the loot lead sets as data and measures in the zone sim.
- **Campaign gates** (the zone sim, tier II): the human bot rises 1-3 times an hour in Act 1 and the deft at most once; the standing bot falls to every champion pack; levels and drops land within ±20% of this table.

### 7.2 Death (the owner's call 7)

- **The pick:** an Ember Walker gets up. She rises at the last lamp-post she lit (there is one at every boss's door), whole, with everything she carries.
  - Foes she killed stay dead; champions and bosses heal.
  - No experience, gear or gold is lost.
  - The narrator's "You get up. It takes less than it did." plays, and the story's toll counts each rise. That cost is canon (PLAN.md: every rising costs a life, revealed at C41).
- **Maps:** two rises each (PoE's portals), at the map's entry post, never in place; champions and the ruler heal. The third fall closes the map and spills half. This bends the owner's rule recorded in `MapRun.cs` ("getting up and fighting on is rare, or it is a balancing nightmare"): a rise at the entry post is a walk back, not fighting on where she fell. The rises are built with the atlas (M11); until then a fall closes today's maps.
- **What retires:** "a lost story fight wakes her in town a day on" (4 October). An ARPG boss is retried from its door in a minute; the toll carries the weight that the lost day did.

### 7.3 Difficulty (the owner's call 8)

**Pick: four world tiers, picked at any lamp-post (Diablo III and IV).**
- I (story) and II (the default) are open from the start. III opens after Act 1, IV after the campaign.
- Each tier raises foe health and damage, the make and the drops (starting numbers for the combat and loot leads): I ×0.7 health, ×0.6 damage; II ×1, ×1, Rare+ ×1.2; III ×2.5, ×1.8, +5 item levels, Rare+ ×1.6, Legendary ×1.5; IV ×6, ×3, +10 item levels, Rare+ ×2, Legendary ×2.5.
- Zones keep level bands, and foes scale to her level inside a zone's band.
- The arena keeps its own tiers, and the atlas climbs on tiers III-IV. Tiers per act would make the player relearn the difficulty every act.

---

## 8. Sieges: the hooks only (nothing is built)

| A siege needs (SIEGES.md) | What we leave open now | What would close it (don't) |
|---|---|---|
| Assault groups with objectives and routes (§6) | The director's unit becomes a **group record** as data: composition, spawn, route, objective, phase. The snuffers that go for lamps are the seed: foes that target a thing, not her | AI that can only target her; a director that is only a count by minute |
| Destructible positions (§2, §5) | Lamps, boss lamps and the arena's held lamp become one **position** type: health, side, repair, fall and retake | The lamp hard-coded as a special case; nav that can't change when a barricade falls (`GroundPath.cs`) |
| Squads and a command radial (§4) | Allies (summons today) become one ally type with a squad id and orders (hold, follow, charge). One input stays free for a held radial (a d-pad direction on a pad) | Summon-only ally code; all six skill keys plus the dash, Flare, draught and interact leaving no free input |
| Environmental weapons (§5) | The telegraph kit can be cast by a world object and hurt foes (sides on every blow). The skill bar can swap for a while (a ballista's skills) | A kit that only foes cast; a bar that can't swap |
| Three LODs of battle (§12) | Crowd rendering already holds 250-300. The sim gets room for proxy groups fought by numbers far off | A director that assumes every foe is fully simulated |
| Morale (§4) | A per-group number in the group record | none |
| A dawn timer (§8) | The arena's night clock and its phases stay general code, and are kept | Deleting the night's clock with the campaign's |
| Heroic Momentum (§9) | The Flare's named fill events (`FillFlare(amount, why)`) take new kinds | Flare fills hard-coded |
| Districts that fall and are retaken (§2) | Zone state as keys (`WorldState`, `ZoneReset`) holds district states | Zone state as flags in code |
| The preparation phase (§3) | Positions can start unbuilt: zone data names build sites with their options and costs | Fortifications baked into zone scenes |

Act 3's war at the gate (PLAN.md §3, chain 6) is the story's natural first siege.

---

## 9. The migration list, in build order

| # | Lead | Builds | Cost | Stops doing |
|---|---|---|---|---|
| M1 | Skills (skills-p7, running) | Heroic Leap; Shield Charge with its four facets on its wick; Bladestorm on two keys, the WIP's union split so each key drives its half (today either key holds one channel); the spin paid from Resolve once M3 lands it (the WIP's 6 s cooldown and 3 s channel cap go then); Iron Vow as a pressed skill (the 2 s brace, 20% stored, the 5 m burst); wicks for the Leap, Cleaver and Iron Vow (12 lamps each: three strands of four, the fourth a Turn) and Shield Charge's other two strands; the dash's four steps and pips | ~2.3-2.8M, 2-3 judged clip rounds | facets on the dash |
| M2 | The owner | picks on this page | none | none |
| M3 | Combat systems (the held C2 build lead, re-briefed) | the press path for every warden skill (kind, aim, hold to repeat), Resolve, the kindled rules, the bots that press, the Low Ford's curve re-measured | ~3.3M (the bots and the Flare's fill included), 3-4 number rounds | tuning the night's draft as the game; the ×1.25 night lean |
| M4 | UI (design and art) | six keys with waits and costs, the Resolve bar, the dash pips under her life, the level-up flash with before and after | ~1.2M, 2 judged rounds | campaign draft screens |
| M5 | Zones and encounters (new, su-lead-high) | the Low Ford as the first ARPG zone: packs with captains, champions with affixes from the telegraph kit, lamp-posts as checkpoints and waypoints, `zone_resets.json` per zone, a lamp-post at every boss door, the day's clock off in the Low Ford, world tiers I-IV picked at a lamp-post with section 7.3's multipliers, the zone sim. It counts the Low Ford's packs from section 5's beats, and if the first hour's do not fit its 260 m, adds ground (with L1's cost) before the demo | ~2M, 3 rounds | arena boards as campaign ground |
| M6 | Experience with story | section 5's tutorial: the callouts, the cuts, the one dawn page, the lent Flare | ~1.4M, 2 rounds | night tutorial copy |
| A1 | Animation (Stage B, re-cut) | the warden's cast clips on an upper and lower split, so she walks while she swings and casts, judged in motion at the play camera | A1 sizes it | clips made for a self-firing game |
| M7a | Classes build | Sunder's and Groundbreaker's wicks lit by level at the new rate, with the level-up flash | ~0.5M, 1 round | none |
| M9 | Loot (su-lead-sonnet) | captains as carriers, ground loot, world-tier weights, "+1 to a skill", the Ford-Warden's Legendary | ~0.6M, 1-2 rounds | the night's-end tally outside the arena |
| **demo-arpg1** | the owner plays | the first 45 minutes as an ARPG (the warden), plus a second start: the veteran's hour on a level-30 warden through the WIP's dev grants, on today's MapGen maps, where one fall closes the map (the atlas, its rises and the daily come later, M11 and M8), so he plays the Leap and Bladestorm before M10 is spent | **~12M plus A1 to here** | none |
| M7 | Classes build (the rest) | every wick in `skill_lamps.json` lit by points at the new rate; *Light my way* at each level; Unions joined at lamp-posts; tomes out (ONE_BUILD §5: 1, 3, 5, 6, 15, 16) | ~2M, 2-3 rounds | wiring the cards into the campaign |
| M8 | Arena | the ember-cast rule, the daily (seed, rule deck, loaned builds, local board, cache), the dawn card and offer kept here | ~1.5M, 2 rounds | the night as the game's gate |
| M10 | Act 1's ground (L1's look pipeline, zones, combat) | the Verge's three zones (the Deep Shaw among them), the four story dungeons (rooms and boss scripts reused, waves turned into placed packs), time by the story | ~10-15M plus GPU: the long pole; L1 sizes it after G2 | story nights as drafts from nothing |
| M11 | Later | the atlas on world tiers, with its two rises a map (~1.5M), the dead's nights, the other callings' pressed waves, then sieges | | |

Act 1 as an ARPG totals about 25-30M plus A1's re-cut (M10's range) (ONE_BUILD's C2 build of ~0.5M is folded into M3 and M7). The character pipeline (P1, P2, P3) and L1's G2 run beside it unchanged.

---

## 10. The owner's calls (my pick first, one line each)

1. **Skills in the campaign:** pressed: six keys, a resource the grip builds and the big skills spend, waits on movement and defense, a few kindled skills; or self-firing with a few pressed.
2. **The arena's rule:** the ember casts for her (today's night, her same build); or the campaign's pressed combat in a horde.
3. **A Union keeps both keys,** one per half with a bond (hold to spin, press to break the storm); or one key and a dead second slot.
4. **The lamp offer:** levels light lamps anywhere out of a fight, lamp-posts change them, and the ember's cards are the arena's; or lamp-posts only, or cards in the campaign too.
5. **Zones:** handcrafted acts and dungeons, generated endgame maps; or generated acts too.
6. **Loot:** about 40 gear drops an hour, an upgrade every 8-15 minutes in Act 1, the first Legendary from the Ford-Warden; or Diablo IV's showers.
7. **Death:** she rises at the last lamp-post with nothing lost, a boss heals, and the toll counts in the story; or 4 October's "wake in town a day on"; in maps, two rises at the entry post, or today's: a fall closes the map.
8. **Difficulty:** four world tiers at any lamp-post; or tiers per act.
9. **Time of day:** it follows the story, and the 12-minute clock retires; or keep the clock.
10. **The prologue's dawn:** the ember lends the Flare for the Warden and first light takes it back on one page, so Act 4 has its rule; or no dawn loss at all.
11. **Ember is her experience:** the dead's light is how she grows, which sharpens Act 4; or plain experience on a kill.
12. **The daily:** one seed, one rule and one loaned build for everyone; or her own build.
13. **Slots:** all six keys by level 9 (2/3/4/5/6 at 1/4/5/7/9), Heroic Leap at level 4 and Shield Charge at 5, the first Union (so Bladestorm's spin) about level 11, at Act 2's door, about five hours in; or the spin sooner: Bladestorm as the Warden's own skill at level 7 and the Union rule kept for the rest; or today's 1/4/8/14/20, six keys from Act 3.
