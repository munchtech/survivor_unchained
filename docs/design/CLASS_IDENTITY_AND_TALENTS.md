# Class identity, the skill pool and the talent tree

Classes and Skills design lead, 27 October 2026. **A plan only: no game code until the owner approves it.** It restructures `docs/design/CLASSES.md` (the Lamps, two types per calling, the Flare). Everything there that isn't changed here stands: the four callings and eight types, the dash forms and reflexes, the Flare's meter, window and sixteen ultimates, the by-night rule (§2.10), and free respec.

The owner, 27 October: *"I think i've decided to have class identity. some skills will be calling only, with a wide variety overlapping to make endless build ideas. this means we have to restructure and add lots more skills - and finally begin developing a substantial talent tree system".*

---

## For the owner (one page)

**What changes.** Today every skill is open to every calling. Builds blur together, and the talent board (the Lamps) exists only in data: there's no screen, so you've never seen it. After this:

- **Every skill carries the sigils of who may use it.** There are three circles:
  - **The calling's own** (12 per calling, 48 in all): only a warden can Sunder.
  - **Kindred skills** (4 per pair of callings, 24 in all): shared by exactly two callings, so builds overlap without blurring.
  - **The valley's skills** (26): anyone's.
- **98 skills in all** (today: 26). Each calling reaches 50 of them.
- **The same skill plays differently in each calling's hands.** Every calling has a **Hand**, an always-on accent that bends any skill it carries toward its mechanic. A warden's Firepot staggers; a reaver's feeds Frenzy. The talent board deepens the Hand.
- **The talent tree has two layers**, as the genre's best do:
  1. **The Lamps**, one big board (about 570 lamps; about 85 lit at the very end). This is the passives: your calling's mechanics, keystones (blue lamps), the crossings between callings, and the valley's ten old roads, which any calling can reach.
  2. **The Wicks**, a small tree on every skill (12 lamps, three strands). A skill's rank is its points, so it fills as she levels by day and as the ember ranks it at night. Each strand ends in a **Turn** that transforms the skill: three seeking motes become one slow star; Volley becomes a hail on a spot.
- **The Flare stays the BOOM.** It's calling-only, sixteen of them, each with a role (clear, save, single target, context), and every press is seen. One new rule: no skill's look may reach the Flare's scale. The Flare is the only thing that stops time.
- **Day builds get six skills,** not three, by level 20. The maps are build checks, and three skills can't make a build.

**My verdict.** Build on the Lamps; don't replace them. Their logic, 236 live rules and the Flares are built and measured. What's missing is the identity layer (access, Hands, calling skills), the layer that changes skills (the Wicks), the board's growth, and a screen. **The first playable slice is the Warden**: her four planned calling skills, Wicks on everything she carries, the Hand, the type pick at creation, six day slots, and a plain board screen behind a flag. About 8 lead sessions. The whole plan is about 50.

**Questions for you are in §7.** The big ones: move 12 of today's skills into kindred pairs (yes); two layers, the Lamps and the Wicks (yes); six day slots (yes); a finite tree of about 85 lamps with no paragon, where endless grows through the night (yes).

---

## 0. What exists today (checked in code, 27 October)

| Piece | Today | Where |
|---|---|---|
| Callings | 4: warden, reaver, arcanist, stalker. **No ranger calling:** "ranger" is the stalker's outfit | `data/content/archetypes.json`, `logic/Rpg/Callings.cs:30`; `Play/Loadout.cs:87` |
| Types | 8 roads in lamps.json, each with 3 signature skills, a Strike and a Stand. **Not chosen at creation:** it defaults to the first road | `Content/Lamps.cs:124`, `Rpg/LampBook.cs:46-57`; `CreationChoice` (`Character.cs:181`) has no type |
| Combat skills | 26 base skills plus 9 unions, 52 evolutions, rank 8 max, 6 night slots. **All open to everyone** ("anyone can take anything") | `Content/Weapons.cs:95-563`, `Sim/LevelUp.cs:432` |
| The 16 planned skills (Sunder ... Snare-Line) | **Names only**, in lamps.json roads and phase-5 lamp effects (63 effects waiting) | `lamps.json`, `tools/classes/lamps_quarters.py` |
| Day skills | Learned from what she saw at night, tomes, or the calling every 3rd level. **Slots: 1, 2 from level 4, 3 from level 8.** Rank = 1 + (level − 1)/3 | `Rpg/SkillBook.cs:25-105` |
| The Lamps | 360 lamps (84 per calling, 24 on 4 crossings), 28 blue lamps, 72 skill lamps, 16 Flares with 48 modifiers. Points: level − 1 + story bosses + atlas (8 max). 2 layouts, Light my way. `LivePhase = 2` | `Content/Lamps.cs`, `Rpg/LampBook.cs:60-244`, `Sim/LampLoadout.cs` |
| The Lamps screen | **None.** Only the `--flare` debug argument uses LampBook. No lamp positions in data (edges only) | `src/Game/Game.cs:220` |
| Flares | 16; 9 staged (all 8 Strikes and Butcher's Hour). **`bossMul` is still in lamps.json** (0.6, 0.5, 0.45), though the owner retired it on 13 October ("tooltips are the truth") | `Sim/Flare.cs`, `FlareStaged.cs`, `lamps.json:158,281` |
| Gear and skills | 22 weapon items carry a skill; 5 affixes grant one; gear brings a skill in at rank 4 at most. No sockets, gems or lamp-lit items | `Rpg/Items.cs:88,257` |
| Level | Cap 30; +2 attribute points a level; a trait pick on even levels | `Character.cs:585-647` |
| Harness | Arena, story and map sims; `--callings`, `--type`, `--lamps`, `--offcalling`, Flare switches | `balance/Program.cs` |

---

## 1. Each calling's identity and its own skills

**Rules for every skill (kept from CLASSES):**
- A combat skill fires itself and **never moves her**: only the dash and the Flare do.
- **Kept apart on purpose:**
  - bleed and fighting hurt are the Butcher's;
  - poison and the dash as a weapon are the Roadknife's;
  - lightning on the chain is the Chainbound's;
  - marks that pass on death are the Moonweaver's;
  - the prey (one marked target) is the Verge-Hunter's;
  - Stones and blocks are the Bulwark's;
  - heavy blows and Sundered are the Sunderer's;
  - freeze-then-shatter is the Kindler's.

**Each calling's 12 skills:**
- 5 per type (that road's grip and signatures);
- 2 for the whole calling (they serve both types and the bridge).

**Marks in the tables:**
- **P** = planned in CLASSES §4 (names and lamp effects already in data);
- **N** = new here.

Every name goes to the story lead for the valley's voice.

**The VFX references** (`SKILL_VFX_REFERENCES.md`; stills in `survivorsunchained_inputs\vfx_refs\`), numbered as the contact sheet:
1. golden fighter slashes;
2. spectral serpent, teal dome, red beam;
3. blood orb, whip and crystal spikes;
4. meteor sun and fire ring;
5. bird strike;
6. glyphs and lotus circles;
7. wave crash;
8. elemental fight hits;
9. the constellation column.

They're cited where a skill or Flare should draw on one: inspiration, never copied.

### Warden: hold the line
*She stands where the line should be, and the horde breaks on it. Heavy blows, blocks, Stones, holy retaliation, barrier, taunt. Only she staggers with every swing, and only she gets stronger by being hit.*

| | Skill | What only it does | Ref |
|---|---|---|---|
| Calling | **Watch Bell** P | Every 6 s a toll draws everything within 8 m to her for 2 s; 2% barrier for each | 1 |
| Calling | **Iron Vow** N | Every 10 s she braces for 2 s: blows on her cut 50%, and 20% of each blow taken is stored, then released as a holy burst 5 m round | 1 |
| Sunderer | **Sunder** P (grip) | Slow 220° cleave; every 4th swing a heavy line 7 m that splits the ground | 1 |
| Sunderer | **Groundbreaker** P | A crack runs to the densest pack within 10 m; the ground heaves (stun 0.6 s) | 4 |
| Sunderer | **Headsman's Arc** N | Every 6 s an overhead on the toughest within 4 m: always heavy, and it finishes ordinary things below 25% | 1 |
| Sunderer | **Morning Line** N | Every heavy blow leaves a burning holy line for 4 s | 1, 9 |
| Sunderer | **Kneeling Cut** N | After 1 s standing still, her next swing is a 360° heavy sweep | 1 |
| Bulwark | **Rebuke** P | Each block strikes the blocker and three near it with holy light | 2 |
| Bulwark | **Shield Toss** N | Every 3 s the shield flies to the farthest within 12 m, stuns, bounces to two more and returns; each catch lays a Stone | 1 |
| Bulwark | **Hallowed Stand** N | A ring where she stands for 8 s; every Stone laid inside pulses holy 4 m | 6 |
| Bulwark | **Oath-Bound** N | The 3 nearest champions are tethered to her; each takes 15% of what she blocks | 2 |
| Bulwark | **Bastion** N | Every 12 s a short wall of stone rises across the thickest approach for 5 s; what strikes it is rebuked | 7 |

*(Oathblade, today's bulwark grip, and Judgement Disc stay hers through the valley's pool and her kindred.)*

### Reaver: take it out of them
*Close and frantic, health swinging, the screen red. Frenzy, bleed, fighting best hurt, the hook and the chain, lightning down the chain. Only she gets stronger as her bar drops, and only she drags the horde into knots.*

| | Skill | What only it does | Ref |
|---|---|---|---|
| Calling | **Bloodletting** N | Every 12 s she spends 10% of her health: for 4 s every blow bleeds and adds Frenzy; kills mend it back | 3 |
| Calling | **Reaver's Mark** N | The nearest champion is marked: blows on it mend 2%, and it's Bound (it can't flee) | 3 |
| Butcher | **Carve** P (grip) | Three fast chops on the nearest every half second, each bleeding | 3 |
| Butcher | **Hurled Cleaver** P | Every 3 s a cleaver flies at the farthest bleeding thing within 12 m and returns | 3 |
| Butcher | **Rend** N | Every 4 s she tears the nearest: its bleed deals 3 s of damage at once | 3 |
| Butcher | **Abattoir** N | Where things died, a red ground: bleeding things inside take 30% more, and kills there extend it | 3 |
| Butcher | **Red Whirl** N | At 20 Frenzy, a 360° flurry 3 m round her for 2 s | 3 |
| Chainbound | **Chain Lash** P (grip) | A 7 m whip arc; the farthest thing struck is hooked and dragged 3 m in | 2 |
| Chainbound | **Anchor** P | An anchor lands in the thick of it; everything 5 m round is Bound to it, then yanked together | 2 |
| Chainbound | **Stormhook** N | A hook to the farthest within 14 m Binds it; lightning runs the chain for 2 s | 2, 8 |
| Chainbound | **Gallows** N | A Bound champion is hoisted off the ground for 2 s: it can't act, and takes 25% more | 2 |
| Chainbound | **Thunder-Knot** N | Every 6 s everything Bound is yanked 2 m toward the biggest knot and struck by lightning | 8 |

### Arcanist: some of them keep ledgers
*Placement and spreading: ground that freezes then shatters, marks that pass on death, lights that hunt on their own. Only she turns the floor into the weapon, and only her marks outlive their bearers.*

| | Skill | What only it does | Ref |
|---|---|---|---|
| Calling | **Echo Glyph** N | Every 8 s a glyph under the densest pack: the next spell she casts also fires again from it | 6 |
| Calling | **Ember Moth** N | A moth of ember at her shoulder recasts her last projectile spell at half strength every 2 s | 5, 6 |
| Kindler | **Pyre Line** P | A line of fire 8 m long rises between her and the densest pack | 4 |
| Kindler | **Rime Field** P | The ground under the thickest pack frosts; what stays 1.5 s freezes for 2 s | 7 |
| Kindler | **Falling Ember** N | Every 9 s a burning star falls on the densest frozen pack and shatters all frozen within 5 m | 4 |
| Kindler | **Ice Spire** N | A spire grows where cast and freezes what touches it; fire on it explodes it | 7 |
| Kindler | **Kiln** N | A burning ground that grows as her fire spells land in it | 4 |
| Moonweaver | **Moonwell** P | A well of moonlight fires motes at what passes within 7 m for 8 s | 6 |
| Moonweaver | **Lantern-Man** P | A moonfire wisp drifts out along her path, flaring at three things and marking | 6 |
| Moonweaver | **Constellation** N | Marked things become stars; at five, lines of moonfire run between them | 9 |
| Moonweaver | **Silver Serpent** N | A serpent of moonlight coils out, weaving from marked thing to marked thing | 2 |
| Moonweaver | **Eclipse** N | Every 10 s the marked within 12 m are drawn 1 m together and darkened: they take 20% more | 9 |

*(Cinderfall and Seeking Motes, today's grips, stay in the valley's pool: the Hand and the road make hers better.)*

### Stalker: never there when it lands
*The dash is her weapon or her escape. True strikes after a dash, poison, distance, snares, the prey, the beasts. Only she is rewarded for never standing still, or for never being reached.*

| | Skill | What only it does | Ref |
|---|---|---|---|
| Calling | **Shadow Double** N | After a perfect dash a shadow of her stays 3 s and repeats her blows | 2 |
| Calling | **Tracker's Mark** N | Every 6 s the farthest champion in sight is tracked: her projectiles and dash strikes on it strike true | 5 |
| Roadknife | **Twin Fangs** P (grip) | After each dash, the two nearest are cut twice; within the Opening every Fang strikes true | 8 |
| Roadknife | **Cutting Wake** P | Each dash leaves hanging blades along its path for 1.5 s | 8 |
| Roadknife | **Blade Dance** N | Each dash charge she holds puts two blades in orbit; spending a dash flings them along it | 8 |
| Roadknife | **Knife in the Back** N | What she dashed through in the last 2 s takes true strikes from behind | 8 |
| Roadknife | **Adder's Breath** N | Every 5 s a poison cloud where she last dashed | 3 |
| Verge-Hunter | **Heartseeker** P | Every 3 s a heavy arrow at the toughest within 20 m, piercing everything in line | 5 |
| Verge-Hunter | **Snare-Line** P | Snares fall across the thickest approach; what steps in is rooted 1.5 s | 5 |
| Verge-Hunter | **The Hawk** N | A hawk circles; every 3 s it dives on the prey and what stands near it | 5 |
| Verge-Hunter | **Thorn Shot** N | Arrows leave thorns; at five, the thorns burst (nature) | 5 |
| Verge-Hunter | **Long Shot** N | Beyond 15 m her arrows strike twice | 5 |

---

## 2. The shared pool, and how it makes many builds

### 2.1 Three circles

| Circle | Who | Count | Where on the board its lamps live |
|---|---|---|---|
| **The calling's own** | one calling | 48 (16 planned + 32 new) | that calling's quarter |
| **Kindred** | exactly two callings | 24 (12 of today's + 12 new), 4 per pair | that pair's crossing |
| **The valley's** | everyone | 26 (14 of today's + 12 new) | the Old Roads ring (the ten paths) |

**Each calling reaches 50 skills:** its own 12, plus 12 kindred (three pairs × 4), plus the valley's 26.

**The six kindred pairs.** Each pair has a crossing on the board.
- The four ring crossings already exist.
- Two new **diagonal** crossings run through the center, so every pair of callings has a road between them.

| Crossing | Pair | Theme | Today's skills moved here | New |
|---|---|---|---|---|
| **The Shambles** | Warden + Reaver | heavy steel and blood | Cleaver, Iron Palms | **Stamp** (every 4 s a stamp 4 m round: it staggers, and the staggered bleed), **War-Banner** (a banner where she stands: within 6 m she strikes 15% harder, and kills there bleed the nearest) |
| **The Night Road** | Reaver + Arcanist | storm and the grave | Arcweb, Umbral Bolt | **Blood Price** (a red bolt paid in 3% of health, bursting 3 m; twice as hard below half), **Corpse-Light** (lightning leaps between corpses within 6 m) |
| **The Firebreak** | Arcanist + Stalker | ground and arrows | Firepot, Thornbloom | **Ember Trap** (traps that burst fire or frost when stepped on), **Kindled Arrows** (three arrows of the last element she dealt) |
| **The Duelist's Road** | Stalker + Warden | blocks and perfect dashes | Judgement Disc, Gale Chakram | **Riposte** (a block or a perfect dash answers with a true cut on the 3 nearest), **Javelin** (a heavy javelin at the farthest within 15 m; it roots champions) |
| **The Vigil** (new, diagonal) | Warden + Arcanist | light, the lamp and the ember | Dawnpulse, Hallowed Ring | **Lamplight** (a lantern at her shoulder burns what comes within 4 m), **Sanctuary Glyph** (a circle where she stands: barrier inside, and missiles burned) |
| **The Poacher's Road** (new, diagonal) | Reaver + Stalker | bleed, poison and the hunt | Spirit Herd, Blightfield | **War-Hounds** (two hounds that run down bleeding or poisoned things), **Bolas** (a weighted net at the densest pack: roots 1.5 s, and the netted bleed and are poisoned) |

**The valley's 26:**
- **Today's 14:** Oathblade, Axe Gyre, Reaving Arc, Volley, Knifestorm, Seeking Motes, Moonbrand, Cinderfall, Rimeshard, Hoarfrost, Thunderhead, Grave Tether, Gravecall, Verdant Lance.
- **12 new**, each filling a gap in the schools:

| Skill | What it does | School | Ref |
|---|---|---|---|
| **Sling Stones** | stones that stagger | physical, ranged | |
| **Rootgrasp** | roots rise under the nearest champion | nature | |
| **Rime Halo** | orbiting ice shards | frost | |
| **Ember Rain** | burning drops fall round her | fire | 4 |
| **Wandering Spark** | a slow ball of lightning | storm | 8 |
| **Barrow Hands** | hands from the ground hold what passes | shadow | |
| **Candle Rite** | each kill lights a candle; six burst in holy fire | holy | |
| **The Crows** | a murder that pecks the nearest | summon | 5 |
| **Ember Heart** | an aura: things within 4 m burn slowly | fire | |
| **Ward of Bronze** | Legion bronze plates orbit and block missiles | defense | 2 |
| **Ill Omen** | the toughest within 12 m takes 20% more, and its death spreads it | curse | |
| **The Ford Rises** | every 7 s a wave sweeps 10 m forward from behind her, pushing back and chilling | water and frost | 7 |

*(The Ford Rises is the valley's own: the drowning that opens the game, as a weapon.)*

**Why move 12 of today's skills into pairs?** PoE's lesson (`notes/classes_poe.md`): when anyone can do anything, the top builds converge, and every class plays the same few skills. Kindred skills give identity in degrees. A reaver can't throw a Judgement Disc, but a stalker and a warden both can, and they throw it differently. Each calling loses 6 of today's 26 to pairs it isn't in. *This is your call: open question 1.*

### 2.2 How a shared skill becomes a different skill in each calling's hands

Four layers, from automatic to planned:

1. **The Hand (always on, no points).** Each calling's mechanic bends any skill it carries. The Hand is shown on the skill's card ("In a warden's hand: ...") so tooltips stay the truth. It's an accent, not the power: harness target ×1.05 to ×1.10 on its own.
   - **Warden:** every 4th blow of a Melee or Thrown skill is **heavy** (staggers). Holy skills lay a **Stone** for each champion struck.
   - **Reaver:** any hit on a bleeding thing adds **Frenzy**. Below half health, her area skills are 15% larger.
   - **Arcanist:** a spell that kills leaves 1 m of its element's **ground** (burning, frozen or moonlit) for 2 s. A marked thing that dies to a spell passes its **mark**.
   - **Stalker:** for 1 s after a dash, any projectile **pierces once more**, and any blow on a champion strikes **true**.
2. **Rites (board lamps).** A rite carries the calling's mechanic onto a whole tag. Examples:
   - "Your Projectile skills mark" (Moonweaver road);
   - "Your Thrown skills hook: what they strike is Bound for 1 s" (Chainbound road);
   - "Your Fire skills Sunder" (warden's Vigil side);
   - "Your Zones are trapped: the first thing in each is rooted" (Verge-Hunter road).

   About 4 rites per road and 2 per crossing side, so 44 in all. They turn a common skill into a calling skill by tag.
3. **The Wicks (each skill's own tree, §3.3).** These are the same for every calling on a valley or kindred skill. But a Turn's new shape meets the Hand and the rites, so the result differs. A warden's *Split* Volley throws three heavy arrows; a stalker's pierces after a dash.
4. **Links (board lamps).** A link fires a skill she carries, chosen by the player, when something of her calling's happens. Examples:
   - "On a block, fire your chosen Spell once" (Bulwark);
   - "When Frenzy hits 20, fire your chosen Thrown skill at the five nearest" (Butcher);
   - "When a frozen thing shatters, fire your chosen Projectile from it" (Kindler);
   - "Each perfect dash fires your chosen Zone where you left" (Roadknife).

   This is Grim Dawn's bound celestial powers and PoE's cast-on triggers, done as one choice on one lamp. Two per road, 16 in all.

**So a build is:**
- a type (or the bridge);
- about six skills from 50;
- a Turn on each;
- the Hand;
- 4 to 8 rites;
- 1 to 3 links;
- 2 to 5 blue lamps;
- a Flare and its modifiers.

**Counted roughly:** 50 skills × 3 Turns × about 10 blue lamps a calling can reach gives about 1,500 distinct *main-skill* builds per calling before the support skills are counted. Most won't be strong. Dozens per calling will be, which is the genre's real bar: PoE ships about 30 meta builds a league. The harness holds the floor (§6).

### 2.3 Example builds (three or more per calling)

Each lists: the type, the skills (own, kindred, valley), the Turns, the blue lamps, the link, and the Flare.

**Warden**
1. **The Wall That Rings** (Bulwark, simple). Rebuke, Watch Bell, Shield Toss, Hallowed Stand, Oathblade (valley), Sanctuary Glyph (Vigil).
   - *How it plays:* the bell pulls the press onto her, every block rebukes, and each Stone pulses inside the Hallowed Stand.
   - *Build:* Turn *Two Bells* on Watch Bell. Blue lamp *Hold Fast*.
   - *Flare:* Bell of the Morning (Save).
2. **Morning Line** (Sunderer, planner). Sunder, Morning Line, Kneeling Cut, Headsman's Arc, Candle Rite (valley), Dawnpulse (Vigil).
   - *Build:* blue lamp *Weight of the Oath* (every swing heavy, slower than anything can fix). Rite "Your Fire skills Sunder" from the Vigil. Link "a heavy blow fires your chosen Nova": Dawnpulse.
   - *How it plays:* each slow swing burns a holy line, bursts dawn, and lights candles.
   - *Flare:* The Long Cut with Through the Wall.
3. **The Javelin Line** (bridge, across the Duelist's Road). Javelin and Riposte (Duelist's Road), Judgement Disc (kindred), Shield Toss, Sling Stones (valley), Iron Vow.
   - *How it plays:* the Hand makes every 4th throw heavy, so a thrown-weapon warden staggers from 15 m and answers every perfect dash with a Riposte.
   - *Flare:* Sixty on the Wall.
4. **The Drowned Watch** (off-road). The Ford Rises with the Turn *Undertow* (the wave pulls in), Watch Bell, Hoarfrost, Rime Halo, Groundbreaker, Stamp (Shambles).
   - *How it plays:* bell, wave, freeze, heave. A holy-and-frost warden who holds a river crossing.

**Reaver**
1. **Red Work** (Butcher, simple). Carve, Rend, Hurled Cleaver, Red Whirl, Axe Gyre (valley), Cleaver (Shambles).
   - *Build:* blue lamp *The Butcher's Count*.
   - *How it plays:* Frenzy climbs, bleeds stack, and Red Whirl fires at 20.
   - *Flare:* Butcher's Hour.
2. **The Lightning Rod** (Chainbound, planner). Chain Lash, Anchor, Thunder-Knot, Gallows, Arcweb and Corpse-Light (Night Road).
   - *Build:* blue lamps *Lightning Rod* and *The Long Chain*.
   - *How it plays:* knot the pack, then every bolt hits all of it.
   - *Flare:* Storm on the Chain with Earthing.
3. **Blood Price** (bridge plus the Night Road). Bloodletting, Blood Price (Night Road), Reaver's Mark, Reaving Arc, Umbral Bolt (Night Road), Abattoir.
   - *Build:* blue lamp *Always Bleeding*.
   - *How it plays:* a reaver who casts with her own blood, strongest at half health, mending through the marked champion.
   - *Flare:* The Butcher's Bill (Single).
4. **The Kennel** (across the Poacher's Road). War-Hounds and Bolas (Poacher's Road), Spirit Herd (kindred), The Crows (valley), Hurled Cleaver, Reaver's Mark. Link: "kills at 20 Frenzy fire your chosen Summon".
   - *How it plays:* the pack runs down whatever bleeds.

**Arcanist**
1. **Fire and Ice** (Kindler, simple). Rime Field, Falling Ember, Pyre Line, Cinderfall (valley), Hoarfrost (valley), Ice Spire.
   - *How it plays:* freeze, then the star falls.
   - *Flare:* Burns Twice.
2. **The Crowded Sky** (Moonweaver, planner). Seeking Motes with the Turn *Starfall* (one slow star that splits on death), Constellation, Silver Serpent, Eclipse, Ember Moth, Moonbrand.
   - *Build:* blue lamp *Crowded Sky*. Link "a mark passed fires your chosen Projectile from the new bearer".
   - *Flare:* The Branding.
3. **The Ledger** (bridge). Echo Glyph, Kiln, Lantern-Man, Thunderhead (valley), Dawnpulse (Vigil), Rimeshard.
   - *Build:* blue lamp *The Ledger* (alternate the schools).
   - *Flare:* Hard Winter.
4. **The Drowned Bell** (across the Vigil). Lamplight and Sanctuary Glyph (Vigil), Hallowed Ring (kindred), Rime Field, The Ford Rises, Moonwell.
   - *How it plays:* a slow holy-and-water caster who never leaves her circle.
   - *Flare:* The Drowned Moon.

**Stalker**
1. **Hunter's Line** (Verge-Hunter, simple). Volley (valley), Heartseeker, Snare-Line, The Hawk, Long Shot, Tracker's Mark.
   - *Flare:* One Arrow.
2. **Never Still** (Roadknife, planner). Twin Fangs, Cutting Wake, Blade Dance, Knife in the Back, Knifestorm with the Turn *Orbit* (valley), Shadow Double.
   - *Build:* blue lamps *Light Step* and *Never Still*. Link "each perfect dash fires your chosen Zone": Adder's Breath.
   - *Flare:* Through and Through.
3. **Firebreak** (across the Firebreak). Kindled Arrows, Ember Trap, Firepot (kindred), Thornbloom (kindred), Volley, Snare-Line. Rite "arrows through your burning ground catch fire".
   - *Flare:* Pinning Rain with Thorned Rain.
4. **The Poacher** (across the Poacher's Road). Bolas, War-Hounds, Blightfield (kindred), Adder's Breath, Knife in the Back, The Crows.
   - *How it plays:* net, poison and hounds.
   - *Flare:* The Road's Toll (Single).

---

## 3. The talent tree

### 3.1 The genre's best, honestly

| Game | What's best | What fails | We take | We avoid |
|---|---|---|---|---|
| **PoE 1 / 2: the passive tree and gems** | One shared board where distance is the price. Keystones with real costs. Supports that change a skill. Items that light far nodes (Thread of Hope). PoE 2: ascendancies that change how skills behave, and weapon-set passives | Opacity (you need Path of Building). Travel-tax nodes. Regret orbs. Top builds converge across classes | The shared board with homes. Blue lamps with prices. Lamp-lit items. Supports become Turns and Links on points, not a socket economy. Calling-only skills answer the convergence | The 1,500 nodes of +10 attributes. Paid respec. Mechanics the tooltip hides |
| **Diablo III: runes** | Five runes per skill that each change its *behavior*, seen at once. The clearest "talents change skills" in the genre | Sets make the build, not the player. Passives shallow | Each Wick strand ends in a Turn: a rune-like transform, picked visibly | Sets that dictate the build |
| **Diablo IV: skill tree, paragon, aspects** | Legible skill tree. Aspects (item powers that change skills) | Flat "+%" nodes. Paragon is a numeric grind that buries gear | Legendary aspects as lamp-lit and borrowed-skill items | Paragon. Bare "+n%" small lamps (CLASSES already bans them) |
| **Last Epoch: masteries and per-skill trees** | Per-skill trees: "make this skill do what I want". Mastery thresholds. Respec cheap | Many trees to read. Only 5 skills specialized. Skill-level respec cost | **The Wicks**: a small tree per skill, with points from its rank. Depth gates per road | Losing a skill's progress on respec. 20-node trees: ours are 12, 3 strands |
| **Grim Dawn: two masteries, modifiers, devotion** | The pair is the build (45 combinations). Skill modifiers and transmuters. Bound procs ("on attack: summon a wolf") are fun to watch | Walls of numbers. Unrefundable mastery bar. Devotion's tedium | Kindred pairs and crossings (the pair as the build, across callings). **Links** (bind a skill to a trigger). Transmuter-style Turns | Unrefundable points. Affinity juggling |

**Where we land:**
- PoE's board, smaller and kinder;
- Last Epoch's per-skill trees, smaller;
- D3's runes as the Turns;
- Grim Dawn's procs as the Links;
- callings with real ownership, which PoE lacks and the owner asked for.

Respec stays free by day.

### 3.2 The Lamps, version 2 (the board)

The board keeps CLASSES's shape and grows. The quarters are unchanged in place.

```
                    Old Roads (the ten paths ring the board)
         Moonweaver ── Night Road ── Chainbound
        /        \                 /        \
   Kindler        \   the Vigil   /       Butcher
      |  ARCANIST  \     ╲ ╱     /  REAVER    |
  Firebreak         ── the Ford ──         Shambles
      |  STALKER   / ╱ Poacher's ╲ \  WARDEN   |
 Verge-Hunter     /                 \      Sunderer
        \        /                   \      /
         Roadknife ── Duelist's Road ── Bulwark
```

| Region | Lamps | Contents |
|---|---|---|
| **Hearth** (×4) | 20 | The start lamp, the dash form and its 4 lamps, 2 reflexes and 3 upgrades, 2 Flare lamps, Banked Flame, the calling's blue lamp, **4 Hand lamps** (each deepens the Hand: the warden's heavy every 3rd blow, then every 2nd ...) |
| **Road** (×8) | 32 | The entry (the type's mechanic), 9 small, 6 notables, **4 rites**, **2 links**, 2 blue lamps, the Strike and the Stand, 6 Flare modifiers. *The 9 skill lamps leave the board: they become those skills' Wicks* |
| **Bridge** (×4) | 8 | Hybrid notables and a blue lamp, as today, plus 2 rites |
| **Crossings** (×6: four on the ring, two through the center) | 10 | 2 attribute lamps, 2 small, 2 notables joining both mechanics, 2 rites (one per side), a blue lamp, a link |
| **The Ford** (center) | 6 | Where the diagonals meet: 2 notables and the **wanderer's** blue lamp (*Unhoused*: "lamps on other callings' roads cost no depth; your Hand is gone") |
| **The Old Roads** (×10 paths, an outer ring) | 14 | Each path's cluster (Steel and Blood, the Hunt, the Pyre, the Long Winter, the Storm, Dawn's Light, the Grave, the Wild, the Host, the Weave): 6 small, 4 notables, 2 rites for that school's skills, 1 link, 1 blue lamp. Each sits between the quarters whose callings lean on that path today (`Paths.cs` leans), so a warden reaches Steel, the Hunt and Dawn cheaply, and the Weave only far |

**Totals.** 4 × 20 hearths + 8 × 32 roads + 4 × 8 bridges + 6 × 10 crossings + 6 at the Ford + 10 × 14 Old Roads = **574 lamps**. Blue lamps: 28 today + 6 crossings + 1 Ford + 10 paths = **45**.

**Points.**

| Source | Lamps | When |
|---|---|---|
| Levels 2 to 30 | 29 | as today |
| Story bosses, first win | about 13 (4 in Act 1) | as today; lit at dawn, a story moment |
| **Relit lamp-posts** (new) | 12 (4 an act) | dark lamp-posts found off the road in each act; relighting one is a small scene ("Lamps are lit. Stay where they reach.") and a lamp |
| The atlas | 30, finite (today 8) | map milestones: each new tier's first clear, each atlas boss |
| **At the end of everything** | **about 84** | about 54 when the story ends; about 20 at the end of Act 1 |

**Depth gates** are counted in lamps lit on that road: 4 opens the Strike (the free Strike counts), 8 opens notables and links, 16 opens the blue lamps and the Stand. They're raised from 3/6/12 because points double.

**By night:** the CLASSES §2.10 rule stands. Rules are in full; sizes run at a quarter; counts add at most +1 in total; a blue lamp's price stays in full. Rites and links are rules, so they're in full by night. Hands are rules.

### 3.3 The Wicks (each skill's own tree)

Every skill has a wick of **12 lamps in three strands of four**. The fourth lamp of each strand is a **Turn**, which transforms the skill. **Only one Turn may be lit per skill.**

**Points.** A skill's rank is its wick points (rank 8 gives 8 points).
- By day, rank grows with her level (rank 4 at level 10, rank 8 at level 22).
- At night, the ember ranks it. **The wick lights along the path she planned by day as the ember climbs.** The planning by day becomes the night's growth, and the player watches it happen.

8 points buys one full strand (3 lamps and its Turn) and 4 more lamps. A skill without a day plan follows Light my way (the skill's suggested strand).

**Strands come from a library, plus bespoke ones:**

| Strand | Turns it can end in (the engine builds each once, for every skill whose tags allow it) |
|---|---|
| **Shape** | *Split* (three smaller), *Chain* (bounces twice), *Return*, *Orbit* (circles her), *Wide* (bigger, slower), *Pulse* (three times, smaller), *Linger* (leaves a ground), *Implode* (pulls, then bursts), *Starfall* (one slow great one that splits on death), *Hail* (falls on a spot) |
| **School** | Convert to fire, frost, storm, holy, shadow, moon, nature, poison or bleed (each skill lists the 2-3 that suit it). The statuses and the board follow the new school |
| **Bind** | *Lantern* (becomes a turret that casts it for 6 s), *On-kill* (it fires again from what it kills), *Answer* (it fires on a block or perfect dash) |
| **Calling** (calling and kindred skills only) | Bespoke, the mechanic deeper. Rebuke's *Shield of Morning* (rebukes leave barrier); Chain Lash's *Scourge*; Rime Field's *Hard Frost*; Snare-Line's *Deadfall* |

- **Calling skills:** one bespoke strand plus two from the library.
- **Kindred skills:** one bespoke strand, written for *both* callings' mechanics (Riposte's *Two Schools of the Blade*: a warden's riposte lays a Stone, a stalker's opens the Opening), plus two from the library.
- **Valley skills:** three from the library.

That's 98 wicks, about 1,180 lamps. About 290 are bespoke; the rest are configured from about 24 library Turns and their lead-ins.

**Night evolutions stay** (the ember's discovery; SKILLS_DESIGN §7). An evolved skill keeps its day Turn where the tags still match, and the evolution's card says so. If an evolution replaces the shape, the Turn's lamp dims for that night. Unions keep both parts' Turns.

### 3.4 Lamp kinds

| Kind | What it does | Rule |
|---|---|---|
| Small | a number tied to a condition or two tags | never a bare "+n%" |
| Notable | one rule that deepens or joins | shows the glyphs of what it feeds |
| **Rite** (new) | the calling's mechanic onto a tag | names its tag; dims if she carries no such skill |
| **Link** (new) | a trigger that fires a carried skill she picks | one pick per link; its wait shows as an arc on the HUD, as a reflex's does |
| Blue lamp | a big rule with a real price | its price in one red line |
| Entry, reflex, dash form, Flare lamps, Flare modifiers | as CLASSES §2.3 | |
| **Hand lamp** (new, hearth) | deepens the Hand | 4 per hearth |
| **Wick lamp and Turn** (on the skill) | change one skill | one Turn per skill |

**Build-defining nodes:**
- the 45 blue lamps;
- the 16 links;
- the Turns.

**Examples of new blue lamps:**
- **Iron Pilgrim** (the Steel road): "Thrown skills return through you and strike again; *you can't carry Projectile spells*".
- **Drowned Lung** (the Long Winter): "Frost skills freeze in half the time; *you can't be mended while you stand still*".
- **The Pack Remembers** (the Host): "Summons stay a night and grow with every kill; *you have one dash charge*".
- **Bell and Blade** (the Duelist's Road): "A perfect dash counts as a block, and a block as a perfect dash; *both windows are 30% shorter*".
- **Unhoused** (the Ford): see §3.2.

### 3.5 Respec and layouts
- **Free, by day, at any lamp-post in a town:** the board, every Wick, the Turns, the links' picks and the type. One at a time, or all.
- **Three saved layouts** (today 2). A layout holds the board, the Wicks, the carried skills and the Flare, so swapping is swapping builds.
- Never mid-night or mid-map.
- **Why free:** planning is only fun when trying is free (D3 and Last Epoch). PoE's regret orbs and Grim Dawn's bar are the failures. The cost of a build is its points, not gold.

### 3.6 Click and have fun, plan for hours
- **New player:**
  - pick a calling and a type;
  - the board opens on her hearth with the next lamp glowing;
  - each skill's wick shows the suggested strand glowing;
  - **Light my way** (board and wicks) lights both every level.
  
  The first hour teaches four words: lamp, wick, Turn, Flare.
- **Planner:** blue lamps, links, rites on off-road skills, kindred crossings, the Ford's *Unhoused*, lamp-lit gear, then the night's draft on top.
- **Opacity guard:**
  - every lamp is one line, with glyphs of what it feeds;
  - lamps that feed nothing she carries are dimmed and say so;
  - a skill's card shows its whole sum: base, Hand, rites, Turn;
  - **no hidden multipliers** (the owner: "things should hit what their tooltips say").

### 3.7 Day slots: six by level 20
- **Today:** 1, 2 at level 4, 3 at level 8. That's fine for the story's first hours, but the maps are PoE-like build checks, and three skills can't hold a build.
- **Proposed:** 2 at level 1 (her grip and her type's first calling skill), 3 at 4, 4 at 8, 5 at 14, 6 at 20. Night slots stay 6.
- **Day balance:** the day curve is re-measured in phase 1. Monsters by day were tuned for three skills, so map and story health rise or skill numbers come down. Story bosses are measured against "pre-Flare 11 Oct" by the harness, as always.

---

## 4. The Flare in the identity

The owner: "an 'oh shit' button. a planned 'BOOM' button. a 'clear the whole room' button"; "*most* are for arena mode type screen clears or saves ... some can be single target ... pushing a flare should always do something visible."

- **Calling-only, as decided on 11 October:** it's the calling's loudest sentence. There are still four per calling, a Strike and a Stand per type, and the roles stay as planned:
  - 6 Clears, 4 Saves, 2 Singles, 4 Contexts.
  - Boss share: room-clearing Flares 10-15% of a boss, single-target 15-20%, reached with **boss health and the Flares' visible numbers. Retire `bossMul`**: it's still in lamps.json for the Long Cut, the Bill and One Arrow.
- **No new Flares in this restructure.** Finish the 16 (7 Stands are unstaged; the waves are in CLASSES §7). More Flares would split the animation lead's time, and the sixteen already cover every type and role.
- **New rule: the Flare stands alone.** No skill, Turn or link may reach the Flare's scale:
  - no time dip, camera push or hitstop over 2 frames;
  - no screen-wide light;
  - no area over 10 m.
  
  The Flare is the only thing in the game that stops time. As skills multiply, this keeps the BOOM special. Skills VFX gets it as a hard budget.
- **The Flare reads the build:**
  - It already counts as its type's tags, so road lamps feed it.
  - Under the new Hand, it also takes the calling's accent: a warden's Flare blows are heavy; a reaver's mend when she's bleeding.
  - Links can't fire the Flare. It's always a press: planned, never automatic.
- **The references** (`SKILL_VFX_REFERENCES.md`) **for the 16** (inspiration for the Flare lead):

| Flare | References |
|---|---|
| Bell of the Morning, Dawn in the Steel | 1 (gold slashes), 9 (the column of light) |
| The Long Cut | 1 |
| Sixty on the Wall | 2 (the teal dome as a wall of shields) |
| The Butcher's Bill, Butcher's Hour | 3 (blood whips and the crystal spikes) |
| Drag Them Under, Storm on the Chain | 2 (the serpent as the chain), 8 |
| Burns Twice | 4 (the fire ring; already built) |
| Hard Winter | 7 |
| The Branding | 6 (glyphs) |
| The Drowned Moon | 7 (the wave crash) and 9 (the drowned moon as a constellation) |
| The Road's Toll, Through and Through | 8 |
| One Arrow, Pinning Rain | 5 (the bird strike: a flight of arrows as birds) |

  The owner offered After Effects-type apps: the Flare lead says whether a tool closes a gap the GPU sims and Godot can't, case by case. My read: not needed for the Flares; flipbook atlases from our sims cover them.
- **The Flare's place in a build:**
  - Clears suit arena farmers.
  - Saves suit glass builds (Unbound Casting, Always Bleeding).
  - Singles suit boss-killers.
  
  The board's Flare lamps (Banked Flame, Kindled Oath) are where a build commits to its Flare.

---

## 5. The endgame and Act 1

### 5.1 Act 1: levels 1-10, four story bosses

| Moment | What she gets | What it teaches |
|---|---|---|
| Creation | Calling + type (two cards, a 5 s clip each, one line). Grip + the type's first calling skill, its Strike Flare, its dash form | "This is mine": the calling's sigil on her two skills |
| The Prologue's night | The draft offers calling cards with a gold sigil frame, kindred with two sigils, the valley's plain | "Only a warden can carry this" (one freeze-frame callout) |
| Level 2 | The first lamp, glowing | Click it; her skill visibly changes |
| Boss 1 (the Hollow) | A lamp; the calling's mentor teaches a third calling skill | Calling skills come from her calling, valley skills from the world |
| Levels 3-6 | Wick lamps light by rank; the third slot | The suggested strand glows |
| Boss 2 / a lamp-post | Lamps; the first kindred skill as a tome in loot | Overlap: "a stalker could carry this too" |
| Level 8 | The fourth slot; the first link opens (depth 8) | Link: pick which skill fires |
| Boss 4 (the Vault), about level 10 | Rank 4: **the first Turn**. Act 1 ends with her skill transforming | Turn |
| Act 2, about level 12 | The first blue lamp | The price in red |

- **About 20 lamps** by the end of Act 1.
- **Act 1's balance:** a player who never presses the Flare stays within ±3% of "pre-Flare 11 Oct", with falls no higher. The Hands and day slots are calibrated against it.

### 5.2 The endgame

- **Permanent maps (the atlas):** the full board, Wicks and six day skills apply.
  - Map mods check builds by tag, never by calling: *Smothered* (the Flare fills 30% slower, as planned), *Unbinding* (Bound and roots last half), *Warded* (projectiles slowed), *Hallowed Ground* (holy heals them).
  - The atlas gives 30 finite lamps.
  - **Borrowed skills** (open question 5): a few Legendaries, each naming one other calling's skill, let her carry it. It has a library wick only, never the bespoke strand. It's the exception that makes the lock exciting (D4's aspects, GD's item skills).
  - Lamp-lit Legendaries light one blue lamp anywhere (CLASSES §2.6).
- **Survivor arenas** ("mindless survivors fun"):
  - The draft is filtered to her 50, with leans:
    - her calling's own ×1.5;
    - kindred ×1.3;
    - path ×1.5 as today;
    - capped at ×2.
  - A guaranteed calling card in the first two drafts.
  - The by-night rule keeps the night the ember's.
  - The night's pool per calling grows from 26 to 50, so the guarantees and paths (SKILLS_DESIGN §8) carry the draft's focus. The harness checks dud drafts stay under today's rate.
- **Endless, truly endless:**
  - Already planned: honing (SKILLS_DESIGN §8.5) and the Flare growing a rank every five minutes.
  - **New: each hone past rank 8 is a night-only wick point,** so in the long night a skill can light a *second* Turn (both shapes at once: a Split that Lingers). Endless shows its growth as skills transforming further, not as a number.
  - The board stays finite: no paragon. SKILLS_DESIGN §14.1's reason holds: an open climb buries gear and the ember.

---

## 6. The restructure: code, data, phases, costs

### 6.1 What changes in today's code and data

| Area | Change | Where |
|---|---|---|
| Access | A calling set on every skill (`Access`: one calling, a pair, or all). The draft, `SkillBook.Calling()`, tomes, discovery and affix `Grants` filter by it. Unions' access is the intersection of their parts'. Gear granting a skill she can't carry rerolls the affix | `Content/Weapons.cs`, `Sim/LevelUp.cs:432`, `Rpg/SkillBook.cs:94`, `Rpg/Items.cs:257`, `Content/Unions.cs` |
| Skills in data | Move skill definitions from C# to `data/content/skills.json` before adding 56 new ones, so a new skill is data plus a behavior class | `Content/Weapons.cs` → data |
| The Hand | 4 rules, read on every hit | `Sim/Battle.cs` HitEnemy, `Sim/*Lamps.cs` |
| The Wicks | `WickBook` per skill per layout; the Turn library (about 24 behaviors built once: shape, school, bind); night rank lights the wick | new `Rpg/WickBook.cs`, `Sim/Turns.cs`; `Sim/Weapons.cs` firing |
| Lamps v2 | Regenerate from `lamps_build.py` / `lamps_quarters.py`: skill lamps out (to wicks), rites, links, Hand lamps, 2 diagonal crossings, the Ford, the Old Roads, **positions in data** (the screen needs them), depth gates 4/8/16, 3 layouts, points from lamp-posts and the atlas (30) | `tools/classes/*`, `Content/Lamps.cs`, `Rpg/LampBook.cs:60-244` |
| Creation | The type pick (approved 11 October, never built) | `Rpg/Character.cs:181`, creation screen |
| Day slots | 2/3/4/5/6 at 1/4/8/14/20 | `Rpg/SkillBook.cs:64` |
| Save | v6 migration: a full refund of lamps, wicks laid on the suggested strands, skills she can no longer carry moved to the storeroom as tomes | `World/Save.cs:108` |
| `bossMul` | Retired; visible numbers and boss health only | `lamps.json`, `Sim/Flare*.cs` (5 reads) |
| Harness | Access, Hands, wicks, the new skills, `--offcalling` now means "valley and kindred only"; acceptance below | `balance/Harness/*` |
| UI | The Lamps screen (the board over the live world, pad navigation along roads) and the wick panel; the calling sigils on cards | UI design brief (su-lead-max), then UI art |

### 6.2 Phases

Phase 1 is the smallest slice the owner can play.

| Phase | What | Who | Lead sessions (~300k each) |
|---|---|---|---|
| **1. The Warden, felt** | Access and the draft filter; all four Hands; skills to data; WickBook and the first 8 Turns (Split, Chain, Wide, Pulse, Linger, fire/holy/frost school, On-kill); the warden's 4 planned skills (Sunder, Groundbreaker, Rebuke, Watch Bell: their lamp effects are already in data) with wicks; wicks on the valley skills she starts with; the type pick at creation; six day slots; a **plain functional board and wick screen behind a flag** (looks are UI's, later); the harness taught it; the Act 1 check | combat systems lead + workers; skills VFX for 4 skills; UI (functional only) | 8 |
| 2. The board for real | Lamps v2 data for all four quarters (rites, links, Hand lamps, crossings, the Ford, the Old Roads, positions); points sources; 3 layouts; save v6; **the Lamps screen** (UI design brief at max, then UI art) | combat systems, UI design, UI art, story (names) | 5 |
| 3. The calling waves | One calling at a time (warden's other 8, then reaver, arcanist, stalker): skills, bespoke strands, the rest of the Turn library, harness, VFX and sound, names. The new grips' props and clips (greatsword, hooked chain, longbow: hers first) | combat, skills VFX, animation, story | 4 a calling: 16 |
| 4. Kindred | The 12 moves, 12 new kindred skills, bespoke kindred strands, the 6 crossings | combat, skills VFX | 5 |
| 5. The valley's new 12 and the Old Roads | Skills, library wicks, path clusters, 10 blue lamps | combat, skills VFX | 4 |
| 6. The Flares' last seven | 6b and 6c from CLASSES §7, with `bossMul` retired and the owner's bands | classes, Flare lead, animation | 4 |
| 7. The night and the long night | Evolutions for the 72 new skills (144) and new unions; honing to a second Turn; the draft's focus re-measured; the tuning sweep; teaching; the codex | combat, skills VFX, experience | 8 |
| | **Total** | | **about 50 sessions, about 15M tokens**, plus GPU time for VFX and animation |

**Acceptance (the harness, every phase):**
- Every type within ×1.35 of the median at tiers 1-4.
- On-calling (her own skills with her Hand and rites) beats the same night drafted off-calling by ×1.10 to ×1.25: home is clearly better, never mandatory.
- The Hand alone is ×1.05 to ×1.10.
- A full board at night is within ×1.25 of an empty one.
- No calling's best five builds share more than two skills with another calling's best five: identity, measured.
- Act 1 against "pre-Flare 11 Oct" as above.

**Risks:**
1. **VFX is the long pole:** 56 new skills, 24 Turn variants, 144 evolutions. The Turns are built as parameters on each skill's look (count, scale, school kit), never new art per Turn.
2. **Readability in a 300-creature horde:** six skills plus Turns plus links. The Flare-stands-alone budget, each school's color and shape, and danger marks always drawn on top.
3. **Draft dilution at night:** answered by the guarantees and leans, and measured.
4. **Opacity:** 574 lamps and 1,180 wick lamps. One line each, the dimming and Light my way answer it, and the card shows the whole sum.
5. **Balance by day:** six slots change the day curve. Phase 1 re-measures it before anything else lands.
6. **Names:** about 1,500 new strings to the story lead. Generic Turn names are shared ("Split", "Linger").
7. **The male hero:** every calling, skill and Flare is for both. His clips follow his new model (CLASSES §7's hero order). Nothing here waits on his art.
8. **Migration:** saves keep their calling. Skills she can no longer carry become tomes in the storeroom.

---

## 7. Open questions for the owner (each with my recommendation)

**Decided (the owner, 27 October 2026): "Go with all 10 recommendations".** All ten below are answered as recommended. Phase 1 (the Warden, felt) is next, when the coordinator has a free lead slot.

1. **Move 12 of today's skills into kindred pairs**, so each calling loses 6 of today's 26 (e.g. a reaver can no longer throw Judgement Disc)?
   - *Recommend yes.* Identity needs real edges, and PoE shows open pools converge.
   - The alternative: keep all 26 open and make every new skill calling-only or kindred. Identity then is thinner and only the new skills carry it.
2. **Two layers of talents: the Lamps (board) and the Wicks (a small tree per skill, points from its rank, one Turn per skill)?**
   - *Recommend yes.* It's the best answer in the genre to "talents change skills" (Last Epoch, D3's runes), and it keeps the board about passives and identity.
3. **Six day skill slots by level 20** (today three)?
   - *Recommend yes.* The maps can't be build checks with three, and the day curve is re-measured in phase 1.
4. **A finite tree:** about 84 lamps at the very end (levels, story bosses, 12 relit lamp-posts, 30 from the atlas), no paragon. In endless, each hone past rank 8 lights a night-only wick point toward a second Turn.
   - *Recommend yes.* "Substantial" in choices: about 84 lamps plus about 48 wick points in a build is PoE's scale. No numeric grind that buries gear.
5. **Borrowed skills:** a few Legendaries that let her carry one named skill of another calling, with a library wick only?
   - *Recommend yes*, rare and late: a chase item that makes the lock exciting rather than a wall.
6. **The Hands:** every calling's always-on accent on any skill it carries, shown on the card?
   - *Recommend yes.* It's what makes a shared skill feel like hers from minute one, and it's small (×1.05-1.10).
7. **Phase 1 is the Warden, with a plain board screen behind a flag** so you can play it before the UI lead's real board?
   - *Recommend yes.* You feel calling skills, Turns and the Hand in about 8 sessions, and the real board follows in phase 2.
8. **No new Flares in this restructure;** finish the 16 and retire `bossMul`.
   - *Recommend yes.* Sixteen cover every type and role, and animation is the long pole.
9. **Three saved layouts** (today two), each a whole build (board, wicks, skills, Flare)?
   - *Recommend yes.*
10. **The names "Wick" (a skill's tree) and "Turn" (its transform), beside "the Lamps" and "the Flare"?**
    - *Recommend yes,* with the story lead checking the voice. A wick is what a lamp burns, and it climbs as the ember does.
