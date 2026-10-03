# Catalogue: the content

Concrete content for the item system in `SYSTEM.md`: bases by slot and tier,
the affixes with their ranges, the Marks, the name lists, thirty-two Named
items with their powers and lore, ten sets, the sigils and Watchwords, and
example rolls from a Plain cap to the best thing in the valley.

**Voice.** Names are plain nouns people would use. Lore lines are one image, in
the narrator's voice (present tense, second person, plain nouns) or a named
person's (`VOICES.md`), never explaining.

**Spoilers.** Every Named item and set carries **Safe from**: the first act in
which its name and lore may be seen. An item safe from Act 2 must not drop, be
sold or be described before Act 2 begins (`chapter.done`). The rule is
`STORY_BIBLE.md`'s: never say an act's answer before that act. A test can hold
it (`IMPLEMENTATION.md` §5).

**Numbers** are proposals at the stated grade; affix values follow the grade
multipliers in `SYSTEM.md` §6.2 (I ×1.0, II ×1.5, III ×2.1, IV ×2.8, V ×3.6,
VI ×4.5, bright up to ×5.6).

---

## 1. Today's items, mapped

| Today (`items.json`) | Becomes |
|---|---|
| `worn_oathblade`, `judgement_disc_item`, `butchers_cleaver`, `gyre_axes`, `apprentice_wand`, `ember_staff`, `rime_rod`, `hunting_bow`, `knife_belt` | The Tier I (Worn) base of their weapon family; start to roll affixes (`"base": true`). |
| `storm_totem`, `censer_of_dawn`, `moonbrand_charm`, `thornseed_pouch`, `grave_tether_wand` | Tier II–III off-hand skill bases; the Censer of Dawn's +10% holy becomes its implicit. |
| `leather_cap`, `iron_helm`, `padded_jerkin`, `chain_shirt`, `travelers_cloak`, `copper_ring`, `silver_ring`, `bone_amulet`, `watch_buckler` | Tier I bases (Silver Ring Tier II), as now. |
| `old_hunters_cloak`, `red_kerchief`, `wolf_fang_necklace`, `blightward_mask`, `pilgrims_lantern`, `cracked_lens`, `wolfhide_cloak` | Background and story items: **Named, rarity 1–2** ("humble Named": fixed, no affixes, a world tag). They keep their rarity colour; the Named frame is what marks them. |
| `ashen_plate`, `moonsilver_circlet`, `grimtunnels_lamp`, `wardens_lampiron`, `bone_charm` | Named (rarity 4), with ranges (§6). |
| materials, consumables, quest items, tools, trophies, manuals, tomes | Unchanged; `greymuzzle_fang` becomes the input of a commission (§6). |

---

## 2. Bases

Tier names: I Worn (ilvl 1), II Sound (6), III Wrought (14), IV Legion (22),
V Heartwrought (30, Act 3). Affinity asks 6 / 6 / 10 / 14 / 18 of the attribute
named. Edges and ranks: `SYSTEM.md` §4.2. Implicits scale ×1.0 / ×1.6 / ×2.4 /
×3.3 / ×4.4.

### 2.1 Weapons

| Family (skill) | I Worn | II Sound | III Wrought | IV Legion | V Heartwrought | Favours |
|---|---|---|---|---|---|---|
| Sword (Oathblade) | Worn Oathblade | Watch Sword | Vigil Longsword | Legion Gladius | Pale Brand | Might |
| Disc (Judgement Disc) | Watch Buckler | Iron-Rimmed Disc | Argent Disc | Legion Parma | Chitin Wheel | Resolve |
| Cleaver (Butcher's Cleaver) | Butcher's Cleaver | Drover's Chopper | Headsman's Cleaver | Legion Falx | Bone Falx | Might |
| Paired axes (Axe Gyre) | Pair of Gyre Axes | Woodsman's Pair | Bearded Axes | Legion Hatchets | Ember-Bit Axes | Might |
| Scythe (Reaving Arc) | Hay Scythe | War Scythe | Reaper's Glaive | Legion Harpe | Pale Harvest | Might |
| Wraps (Iron Palms) | Rag Wraps | Leather Wraps | Iron Knuckles | Legion Cestus | Chitin Grips | Might |
| Wand (Seeking Motes) | Apprentice's Wand | Rowan Wand | Blackthorn Wand | Legion Lituus | Ember-Vein Wand | Wits |
| Staff (Cinderfall) | Ember Staff | Ashwood Staff | Bound Staff | Augur's Staff | Pale Staff | Wits |
| Rod (Rimeshard) | Rime Rod | Silver Rod | Frost-Iron Rod | Legion Sceptre | Heart-Ice Rod | Wits |
| Black wand (Umbral Bolt) | Bone Wand | Grave Wand | Barrow Wand | Legion Ossuary Rod | Hollow Wand | Wits |
| Crossbow (Volley) | Hunter's Crossbow | Watch Crossbow | Arbalest | Legion Scorpio | Pale Arbalest | Finesse |
| Knife belt (Knifestorm) | Knife Belt | Bandolier of Knives | Throwing Irons | Legion Darts | Ember Needles | Finesse |
| Chakram (Gale Chakram) | Wind Ring | Steel Chakram | Razor Ring | Legion Orbis | Pale Wheel | Finesse |

Two-handed: paired axes, scythe, wraps, staff, crossbow (+25% Edge).

### 2.2 Off-hands

| Family | I | II | III | IV | V | Implicit (Tier I) |
|---|---|---|---|---|---|---|
| Shield (guard) | Old Watch Shield | Kite Shield | Argent Heater | Legion Scutum | Carapace Shield | +3 armour, +1 block |
| Lantern (guard) | Tin Lantern | Watch Lantern | Chapel Lantern | Legion Lamp | Heartlamp | +20% light, +8% vs the dead |
| Tome (guard) | Commonplace Book | Ledger | Grimoire | Legion Codex | Pale Book | +6% art power, −4% art wait |
| Quiver (guard) | Quiver | Bolt Case | Bandolier | Legion Pharetra | Bone Quiver | +8% projectile speed, +1 pierce at III+ |
| Storm totem (Arcweb) | Carved Stick | Storm-Carved Totem | Lightning-Struck Oak | Legion Augury Staff | Fulgurite | skill, rank by tier |
| Censer (Dawnpulse) | Tin Censer | Censer of Dawn | Chapel Censer | Legion Thurible | Heart-Censer | skill; +5% holy |
| Reliquary (Hallowed Ground) | Bone Box | Saint's Box | Chapel Reliquary | Legion Ossuary | The Lit Reliquary | skill |
| Moon charm (Moonbrand) | Moon Pebble | Moonbrand Charm | Silver Crescent | Legion Lunula | Pale Moon | skill |
| Tether (Grave Tether) | Knotted Cord | Grave Tether | Barrow Chain | Legion Manacle | The Long Chain | skill (necromantic tag at II+) |
| Blight flask (Blightfield) | Cracked Phial | Slurry Flask | Fever Flask | Legion Amphora | Heart-Rot Flask | skill |
| Seed pouch (Thornbloom) | Seed Bag | Thornseed Pouch | Bramble Sack | Legion Seed-Urn | Root of the Stair | skill |
| Antler horn (Spirit Herd) | Cow Horn | Antler Horn | Elk-Call | Legion Cornu | Pale Horn | skill |
| Green lens (Verdant Lance) | Bottle Glass | Green Lens | Moonpetal Glass | Legion Speculum | Ember Lens | skill |

### 2.3 Head, body, cloak

| Slot · weight | I Worn | II Sound | III Wrought | IV Legion | V Heartwrought |
|---|---|---|---|---|---|
| Head · cloth | Rag Hood | Wool Cowl | Scholar's Hood | Augur's Hood | Pale Veil |
| Head · leather | Leather Cap | Hunter's Hood | Brigand's Cap | Legion Leather Galea | Chitin Cowl |
| Head · mail | Mail Coif | Watch Coif | Riveted Coif | Legion Mail Hood | Bone-Ring Coif |
| Head · plate | Iron Helm | Sallet | Vigil Bascinet | Legion Galea | Pale Crest |
| Body · cloth | Homespun Shirt | Padded Robe | Scholar's Robe | Augur's Robe | Pale Shroud |
| Body · leather | Padded Jerkin | Hunter's Jerkin | Brigandine | Red-Lacquer Cuirass | Chitin Coat |
| Body · mail | Chain Shirt | Watch Hauberk | Riveted Hauberk | Legion Hamata | Bone-Ring Hauberk |
| Body · plate | Iron Breastplate | Half-Plate | Vigil Plate | Legion Segmentata | Heartwrought Plate |
| Cloak · cloth | Traveller's Cloak | Watch Cloak | Ranger's Mantle | Legion Sagum | Pale Mantle |
| Cloak · fur | Hide Cloak | Wolfskin Cloak | Bearskin | Legion Wolf-Pelt Standard-Cloak | Morrow-Hide |

Head implicits (Tier I): cloth +5% art power; leather +1 armour, +2% crit;
mail +2 armour, +6 health; plate +3 armour. Cloaks: cloth +3% speed; fur
+1 armour, +10% tenacity. Body: `SYSTEM.md` §4.3.

### 2.4 Jewellery and relics

| Slot | I | II | III | IV | V | Implicit |
|---|---|---|---|---|---|---|
| Amulet | Knucklebone Amulet | Copper Torc | Silver Locket | Legion Phalera | Heart-Splinter Pendant | +1 to the attribute the base names (rolled: Might, Finesse, Wits or Resolve) |
| Ring | Copper Ring | Silver Ring | Signet | Legion Seal-Ring | Pale Band | II+: +2% one resistance (rolled) |
| Relic · lamp | Tallow Lamp | Miner's Lamp | Chapel Lamp | Legion Lamp-Cage | Heart-Lamp | +light radius |
| Relic · lens | Bottle Lens | Cracked Lens | Ground Lens | Legion Lens | Ember Glass | +crit chance |
| Relic · bone | Knucklebone | Saint's Finger | Barrow Bone | Legion Ossuary Charm | Morrow Splinter | +% vs the dead |
| Relic · coin | Brass Token | Toll Token | Silver Mark | Legion Square | (none: a coin of the Morrow is not a thing) | +% gold |
| Relic · bell | Cow Bell | Hand Bell | Chapel Bell | Legion Tintinnabulum | Pale Bell | +% art power |

Relics drop Plain only rarely (one relic in four is Named), and roll at most
three affixes.

---

## 3. Affixes

About seventy, in groups (one per group on an item). **P** prefix, **S**
suffix. Slots: W weapon, O off-hand, H head, B body, C cloak, A amulet, R ring,
L relic. Values are grade I → III → VI (bright: up to ×1.25 of VI's top).
Existing ids keep their ids; values move onto the grade curve.

### 3.1 Prefixes: offence

| Id | Name | Group | Slots | Effect | I | III | VI | ilvl |
|---|---|---|---|---|---|---|---|---|
| `honed` | Honed | school | W O A R | +% physical damage | 6–7% | 13–15% | 27–31% | 1 |
| `searing` | Searing | school | W O A R | +% fire damage | 6–7% | 13–15% | 27–31% | 1 |
| `rimed` | Rimed | school | W O A R | +% frost damage | 6–7% | 13–15% | 27–31% | 1 |
| `thundering` | Thundering | school | W O A R | +% storm damage | 6–7% | 13–15% | 27–31% | 1 |
| `hallowed` | Hallowed | school | W O A R L | +% holy damage | 6–7% | 13–15% | 27–31% | 1 |
| `umbral` | Umbral | school | W O A R | +% shadow damage | 6–7% | 13–15% | 27–31% | 1 |
| `verdant` | Verdant | school | W O A R | +% nature damage | 6–7% | 13–15% | 27–31% | 1 |
| `moonlit` | Moonlit | school | W O A R | +% arcane damage | 6–7% | 13–15% | 27–31% | 1 |
| `grim` | Grim | damage | W A | +% damage | 4% | 8–9% | 17–19% | 5 |
| `cruel` | Cruel | crit | W R A | +% critical damage | 10% | 21% | 45% | 1 |
| `keen` | Keen | crit | R A H | +critical chance | 1.5% | 3.1% | 6.5–7% | 1 |
| `barbed` | Barbed | status | W O R | statuses take hold +% more often | 3% | 6% | 13–14% | 5 |
| `festering` | Festering | status | A R | +% damage from statuses (burn, bleed, poison) | 6% | 13% | 27% | 5 |
| `lingering` | Lingering | duration | A R O | +% duration | 5% | 10% | 22% | 5 |
| `herdsmans` | Herdsman's | summon | A R O | +% damage of what fights for you | 7% | 15% | 32% | 5 |
| `farflung` | Far-Flung | projectile | W R | +% projectile speed | 6% | 13% | 27% | 1 |
| `piercing` | Piercing | projectile | W O | +1 pierce (+2 at V–VI) | +1 | +1 | +2 | 10 |
| `headsmans` | Headsman's | vs-champion | W A R | +% damage to champions, heralds and bosses | 5% | 10% | 22% | 10 |
| `masterwork` | Masterwork | rank | W O | +1 rank to the skill it brings (the rank-4 cap holds) | +1 | +1 | +1 | 16, Rare+ |

### 3.2 Prefixes: slayers (answer a people; leaned by `Denizens.Lean`)

| Id | Name | Slots | Effect | I | III | VI |
|---|---|---|---|---|---|---|
| `wolfbane` | Wolfbane | W O A R | +% damage to wolves, boars and beasts | 15% | 32% | 68% |
| `gravebane` | Gravebane | W O A R | +% damage to the dead | 15% | 32% | 68% |
| `lampsnuffer` | Lampsnuffer's | W O A R | +% to lamplings, and less from them | 15% / 5% | 32% / 10% | 68% / 22% |
| `watchmans` | Watchman's | W O A R | +% to Kerchiefs and outlaws | 15% | 32% | 68% |
| `feverbreaker` | Feverbreaker's | W O A R | +% to the blighted (Act 2) | 15% | 32% | 68% |
| `turncoats` | Turncoat's | W O A R | +% to the Vigil and its knights (Act 2) | 15% | 32% | 68% |
| `pale_hunters` | Pale-Hunter's | W O A R | +% to the Morrow's things (Act 3) | 15% | 32% | 68% |

Slayer values are high because they work against one people; on a map of
that people they are the best prefix, anywhere else the worst. That is the
point: what answers the map.

### 3.3 Prefixes: defence

| Id | Name | Group | Slots | Effect | I | III | VI | ilvl |
|---|---|---|---|---|---|---|---|---|
| `hale` | Hale | health | B A R H C | +health | 12–14 | 25–29 | 54–62 | 1 |
| `stout` | Stout | health% | B C | +% health | 3% | 6% | 13–14% | 10 |
| `sturdy` | Sturdy | armour | H B C O | +armour (×0.6 off the body) | 1–2 | 3–4 | 7–8 | 1 |
| `guarding` | Guarding | block | O (shields) | +block | +1 | +2 | +4 | 5 |
| `feinting` | Feinting | dodge | C H | +% dodge | 1.5% | 3% | 7% | 5 |
| `surefooted` | Surefooted | tenacity | C B R | slows on you shorter and weaker | 8% | 17% | 36% | 1 |
| `thorned` | Thorned | thorns | B O | +thorns | 4 | 8 | 18 | 5 |
| `leeching` | Leeching | lifesteal | W A R | +% of damage dealt as life | 0.4% | 0.8% | 1.8% | 10 |
| `fleet` | Fleet | speed | C R A | +% move speed | 2% | 4% | 9% | 1 |
| `warded` | Warded | resist-all | A R B | +% to every resistance | 2% | 4% | 9% | 10 |

### 3.4 Suffixes: speed, reach, the art, the dash

| Id | Name | Group | Slots | Effect | I | III | VI | ilvl |
|---|---|---|---|---|---|---|---|---|
| `of_haste` | of Haste | speed | R A C W | +% skill speed (today a "more" on cooldown: make it increased) | 2.5% | 5% | 11% | 1 |
| `of_reach` | of Reach | area | R A H | +% area | 4% | 8% | 18% | 1 |
| `of_the_art` | of the Art | art | R A H L | art comes sooner / stronger | 3% / 5% | 6% / 10% | 13% / 22% | 1 |
| `of_the_hare` | of the Hare | dash | C | dash comes back % sooner | 4% | 8% | 18% | 5 |
| `of_two_breaths` | of Two Breaths | dash | C | +1 dash charge | +1 | +1 | +1 | 22, Rare+ |
| `of_the_quiver` | of the Quiver | projectile | W O | +1 projectile to projectile skills | +1 | +1 | +1 | 28, Rare+, weight ×0.3 |
| `of_ricochets` | of Ricochets | chain | W O R | +1 bounce or chain | +1 | +1 | +1 | 16 |
| `of_the_butcher` | of the Butcher | execute | W A | finish anything below % health | 1% | 2% | 4.5% | 10 |

### 3.5 Suffixes: defence and resistance

| Id | Name | Group | Slots | Effect | I | III | VI |
|---|---|---|---|---|---|---|---|
| `of_mending` | of Mending | regen | B A R | +health a second | 0.3 | 0.6 | 1.35 |
| `of_the_physician` | of the Physician | resist | B A R | +% nature resistance; +% mending | 6% / 3% | 13% / 6% | 27% / 14% |
| `of_the_hearth` | of the Hearth | resist | C B H A | +% frost resistance; the cold slows you less | 6% / 4% | 13% / 8% | 27% / 18% |
| `of_the_salamander` | of the Salamander | resist | C B H R | +% fire resistance | 6–7% | 13–15% | 27–31% |
| `of_the_grave` | of the Grave | resist | C B A | +% shadow resistance; less from the dead | 6% / 3% | 13% / 6% | 27% / 14% |
| `of_grounding` | of Grounding | resist | C B H R | +% storm resistance | 6–7% | 13–15% | 27–31% |
| `of_the_chapel` | of the Chapel | resist | C B H A | +% holy resistance (the Wardens, the Vigil's censers) | 6–7% | 13–15% | 27–31% |
| `of_the_wolf` | of the Wolf | from-people | C B H A | less damage from wolves and beasts | 6% | 13% | 27% |

### 3.6 Suffixes: attributes

| Id | Name | Slots | I | III | VI | Bright |
|---|---|---|---|---|---|---|
| `of_might` | of Might | A R H B W | +1 | +2 | +3–4 | +5 |
| `of_finesse` | of Finesse | A R H B W | +1 | +2 | +3–4 | +5 |
| `of_wits` | of Wits | A R H B W | +1 | +2 | +3–4 | +5 |
| `of_resolve` | of Resolve | A R H B W | +1 | +2 | +3–4 | +5 |
| `of_the_whole` | of the Whole | A (ilvl 22) | – | +1 all | +2 all | +2 all, +1 one |

A +2 attribute ring can lift a survivor to the 6 a skill asks (`SkillBook.Need`):
the cheapest way to carry a spell as a warden.

### 3.7 Suffixes: the world and the night

| Id | Name | Slots | Effect | I | III | VI |
|---|---|---|---|---|---|---|
| `of_the_lantern` | of the Lantern | H A L O | your light carries % further | 10% | 21% | 45% |
| `of_greed` | of Greed | R A | +% gold; pickups reach further | 8% / 0.4 | 17% / 0.8 | 36% / 1.8 |
| `of_embers` | of Embers | R A L | +% ember gained (in the ember) | 4% | 8% | 18% |

### 3.8 Suffixes: kindled (one per item, two per kit; `SYSTEM.md` §6.4)

| Id | Name | Slots | In the ember | Grades |
|---|---|---|---|---|
| `of_the_first_spark` | of the First Spark | R A L | start the arena +1 ember level (+2 from grade V) | I–VI |
| `of_second_thoughts` | of Second Thoughts | R A L | +1 reroll | III+ |
| `of_refusal` | of Refusal | R A L | +1 banish | III+ |
| `of_many_roads` | of Many Roads | A L | drafts show four cards | V+, weight ×0.3 |
| `of_omens` | of Omens | A L | great blessings offer four | IV+, weight ×0.5 |
| `of_the_calling` | of the Calling | R A H | your calling's cards +25% more often | I–VI |
| `of_the_long_night` | of the Long Night | W A R | +% damage after the fifteenth minute | 5% → 22% |
| `of_the_whetstone` | of the Whetstone | W R A | counts as Serration for evolutions | III+ |
| `of_the_true_eye` | of the True Eye | W R A | counts as Precision | III+ |
| `of_the_evergreen` | of the Evergreen | O R A | counts as Perennial | III+ |
| `of_the_strong_arm` | of the Strong Arm | W R A | counts as Might | III+ |
| `of_the_wide_field` | of the Wide Field | R A H | counts as Expanse | III+ |
| `of_rime` | of Rime | W O R | counts as Chilling Presence | III+ |
| `of_the_swift_shaft` | of the Swift Shaft | W R | counts as Velocity | III+ |
| `of_the_pyre` | of the Pyre | O R A | counts as Searing Aura | III+ |
| `of_brambles` | of Brambles | B O R | counts as Thorns | III+ |
| `of_the_feint` | of the Feint | C R | counts as Evasion | III+ |

(The catalyst list covers the ten passives that evolve the most weapons;
`Weapons.cs` names eighteen in all. The rest can follow the same pattern.)

### 3.9 Suffixes: skills worn (`SYSTEM.md` §6.5)

The five that exist (`of_motes`, `of_the_gyre`, `of_cinders`, `of_dawn`,
`of_knives`) plus one per remaining findable skill: `of_the_web` (Arcweb),
`of_hallowing` (Hallowed Ground), `of_the_umbra` (Umbral Bolt), `of_the_moon`
(Moonbrand), `of_blight` (Blightfield), `of_the_reaping` (Reaving Arc),
`of_the_tether` (Grave Tether), `of_the_palm` (Iron Palms), `of_the_herd`
(Spirit Herd), `of_thorns` (Thornbloom), `of_the_gale` (Gale Chakram),
`of_the_lance` (Verdant Lance). Slots A R L, Rare+, weight ×0.35, rank
1 + (grade − 1) / 2.

---

## 4. Marks

Each Mark has one rolled number (its strength, in brackets: grade I → VI) and
slots it can burn into. Marks written against tags and arts keep working
whatever the ember drafts.

### 4.1 Steel and the warden's arts

| Mark | Slots | Power |
|---|---|---|
| **of the Open Gate** | B C | Your dash leaves a ring of holy fire for 3 s that burns for [20 → 90]% of your strongest skill's damage a second. |
| **of the Crescent** | W A | Every third swing of a Steel skill throws a crescent that carries on through the crowd for [40 → 160]% of the swing. |
| **of the Wall** | O B | Shield Bash pulls what it strikes toward you; each thing struck gives [1 → 4]% of your health as a barrier. |
| **of the Unmoving** | B H | While Bulwark holds, your Steel skills deal [15 → 60]% more. (A "more": this Mark's one.) |
| **of the Ford** | W O | Judgement Disc returns through you, and each enemy it passes twice is struck for [30 → 120]% more. |

### 4.2 The reaver's

| Mark | Slots | Power |
|---|---|---|
| **of the Long Fall** | H B | Crashing Leap's landing leaves the ground broken for 4 s: things in it take [8 → 36]% more from you. |
| **of the Bitten Tongue** | A R | While below half health your bleeds tick [25 → 100]% faster. |
| **of the Gyre** | W A | Axe Gyre gains one axe for every [6 → 3] enemies within 5 m, to three more. |
| **of the Roar** | H A | War Cry's driving lasts [2 → 8] s longer and every kill in it extends it by 0.5 s. |
| **of the Cave Mouth** | B C | You cannot be pushed; standing your ground for 2 s gives [10 → 45]% armour. |

### 4.3 The arcanist's

| Mark | Slots | Power |
|---|---|---|
| **of the Second Image** | H L | Blink leaves an image of you that casts your last Spell skill once for [50 → 200]% of its damage. |
| **of Borrowed Time** | H L | Time Slip's end detonates everything slowed for [30 → 135]% of what they took during it. |
| **of the Falling Star** | W A | Cinderfall's blast leaves burning ground for [1 → 4] s. |
| **of Deep Water** | W O | Frozen enemies take [10 → 45]% more from storm and physical. |
| **of the Web** | O A | Arcweb's chains leap to [1 → 3] more targets when they start from a frozen enemy. |
| **of the Lamp's Eye** | W L | Seeking Motes hunt marked enemies first and deal [10 → 45]% more to them. |

### 4.4 The stalker's

| Mark | Slots | Power |
|---|---|---|
| **of the Quarry** | H A | Mark Prey marks [1 → 2] more; a marked kill throws a volley of [2 → 6] bolts. |
| **of the Thick Smoke** | C L | In your Smoke Bomb's cloud, your projectiles split once and pierce [1 → 3] more. |
| **of the Cutpurse** | W R | Knifestorm's knives each steal [1 → 4] gold, and crits with them have a [2 → 9]% chance to drop a draught. |
| **of the Ravine** | W O | Volley fires a second volley at the farthest enemy for [20 → 90]% damage. |
| **of the Wind** | W C | Gale Chakram comes back through you and refreshes your dash's wait by [5 → 22]%. |

### 4.5 The schools (any calling)

| Mark | Slots | Power |
|---|---|---|
| **of the Fever Year** | A R B | Poison you apply spreads to [1 → 3] neighbours when the poisoned die. |
| **of the Morning** | O A | Holy skills mend you for [0.5 → 2.2]% of damage dealt, to 3% of your health a second. |
| **of the Pyre** | A R | Burning enemies that die explode for [15 → 70]% of their burn's remaining damage. |
| **of the Hollow** | A R | Shadow skills mark the struck for the grave: [5 → 22]% more damage from you for 4 s. |
| **of the Herd** | O A | What fights for you is [10 → 45]% faster and lasts [1 → 4] s longer. |
| **of the Storm-Eaves** | H A | Every [10 → 5]th storm hit calls a bolt from the sky. |
| **of the Winter Road** | B C | Chilled enemies near you are [10 → 45]% slower still; you are not slowed by cold. |
| **of the Barrow** | B A | A kill on the dead has a [2 → 9]% chance to raise a ghoul for 10 s (at most 3). Chid will know what it is. |
| **of the Toll** | L R | Every hundredth kill drops a sealed lot (a random Fine or better item). |

Thirty-three Marks; each skill and art has at least one.

---

## 5. Rare names

A Rare's name is a first word and a second, drawn from two lists by slot kind
(weapons, armour, jewellery and relics). The lists read like inn signs,
ballad lines and things carters say. Avoid pairs that make a joke or a
sentence the story uses.

| First words | Second words (weapons) | Second words (armour) | Second words (jewellery, relics) |
|---|---|---|---|
| Cold, Low, Gallows, Thrice, Grey, Long, Last, Hollow, Red, Pale, Bitter, Quiet, Drowned, Ashen, Little, Old, Kind, Broken, Bright, Hungry, Crooked, Patient, Sorry, Salt, Moon, Iron, Barrow, Toll, Morning, Winter | Supper, Water, Kiss, Mercy, Tooth, Promise, Reckoning, Errand, Harvest, Answer, Edge, Song, Bargain, Hour, Debt | Coat, Comfort, Wall, Shelter, Weather, Wool, Hide, Shroud, Watch, Vigil, Hearth, Road, Keeping, Patience, Skin | Eye, Charm, Knot, Lamp, Coin, Prayer, Token, Luck, Secret, Ring, Sorrow, Ledger, Vow, Bell, Heart |

Examples: *Cold Supper* (a cleaver), *Low Water* (a rod), *Patient
Wall* (a shield), *Toll Ledger* (a relic), *Drowned Promise* (a ring).

---

## 6. Named items (uniques)

Thirty-two, across every slot and calling. **Home** is where it is found
(`ACQUISITION.md` §4–6). **Safe from** is the first act it may be seen in.
Ranges in brackets.

### Weapons

1. **Corran's Sword** · Watch Sword (Sound, Oathblade) · *Home:* the Old Watch-post; the Risen · *Safe from:* Act 1
   - While you stand still, your Steel skills are [20–30]% faster; every third swing throws a crescent of [60–90]% of the swing.
   - *World:* Holloway knows it ("That was Corran's").
   - *Lore:* "Notched along the spine, in tens, where somebody kept count of something. The book wrote him down as a deserter."
2. **Aldo's Cleaver** · Drover's Chopper (Sound) · *Home:* the caravan wreck; the Kerchiefs · *Act 1*
   - Kills while you are below half health mend [2–3]% of your health. +[15–25]% bleed damage.
   - *Lore:* "He did the camp's cooking. His wife is at Low Kiln and will want it for the pot."
3. **Maeca's Last Arrow** · Watch Crossbow, Storied (Volley) · *Home:* Maeca, if she is the survivor's lover · *Act 2*
   - Volley's first bolt each volley is a sure critical against beasts and the marked; marked enemies take [15–25]% more from your projectiles.
   - *Lore (Maeca):* "Kept it since the cave mouths. Never found the right wolf. Turns out there isn't one."
4. **What It Could Not Burn** · Pale Harvest (Heartwrought, Reaving Arc) · *Home:* the Centurion of the Stair · *Act 3*
   - Reaving Arc's kills leave a pale flame for 4 s that burns for [40–60]% of the arc's damage a second. You burn too: 1% of your health a second while three or more flames are lit.
   - *Lore:* "The Legion had a word for what it buried here. The word was a number."
5. **The Fever-Year Staff** · Ashwood Staff (Sound, Cinderfall) · *Home:* the Fevered; Wenna's cellar (Act 1, if she trusts you) · *Act 1*
   - Cinderfall poisons as it burns; poisoned and burning enemies take [20–30]% more from both.
   - *Downside:* "You mend 10% less. It smells of the sickroom."
   - *Lore (Wenna):* "Burned the bedding with it, that year. All of it. Don't ask me whose."
6. **The Kiln Ford Rod** · Frost-Iron Rod (Wrought, Rimeshard) · *Home:* the Kiln Ford's Warden (Act 2, only if the crossing is lit) · *Act 2*
   - Enemies frozen by Rimeshard sink: [30–45]% of their health is taken at once when the freeze ends, if they are not a champion.
   - *Lore:* "Taken from the cold hand at the second crossing. The ice on it does not melt by your fire. It melts by its own."
7. **Kerchief Knives** · Bandolier of Knives (Sound, Knifestorm) · *Home:* the Kerchiefs; the Red Hand set · *Act 1*
   - (Red Hand set piece: §7.5.) Knives that strike a bleeding enemy return to you.
   - *Lore:* "Forty-one mouths. These were the forks."

### Off-hands

8. **The Order's Last Lamp** · Chapel Lantern (Wrought) · *Home:* the broken shrine (devout, the shrine working again) · *Act 1*
   - Grants Dawnpulse at rank [2–3]. Each pulse that strikes ten or more enemies mends [3–5]% of your health.
   - *Lore (Chid):* "It used to work."
9. **The Pump-Wheel Buckler** · Kite Shield (Sound) · *Home:* the Dig, only if the pump is broken · *Act 1*
   - Each block throws slurry about you: poison for [40–60]% of the blocked blow over 3 s.
   - *Lore (Snib):* "Wheel's no good now anyway. Somebody broke it."
10. **The Penhale Lantern** · Watch Lantern (Sound) · *Home:* Tam's family (Act 2, the family brought in) · *Act 2*
    - Your light reaches twice as far; enemies in it are [10–18]% slower.
    - *Lore (Tam):* "Pa says leave it lit. So it's lit."
11. **The Standard of the Seventh** · Legion Cornu (Legion, Spirit Herd) · *Home:* the Legion · *Act 3*
    - What fights for you fights beneath it: +[30–45]% damage; the Herd runs as the Legion's dead.
    - *Lore:* "The pole is newer than the cloth. Someone has carried it a long way down."

### Head

12. **Moonsilver Circlet** (exists) · *Home:* the Moon Grove (move from Vonnra's stock) · *Act 1*
    - +[12–18]% damage at night; crits at night call a shaft of moonlight ([25–35] arcane).
    - *Lore:* as `items.json`.
13. **Snib's Hard Hat** · Leather Cap (Sound) · *Home:* the Dig (Snib bribed or befriended) · *Act 1*
    - Once an arena, a blow that would kill you leaves you at 1 health and stuns everything within [4–6] m. +[20–30]% armour.
    - *World:* lamplings call you Boss.
    - *Downside:* "You look ridiculous."
    - *Lore (Snib):* "Foreman's hat. I'm the foreman. Says so on the hat."
14. **Moonpetal Crown** · Wool Cowl (Sound) · *Home:* Wenna, the blight cured · *Act 1*
    - Mending is doubled at night; Thornbloom's brambles mend you [1–2]% a second while you stand in them.
    - *Lore (Wenna):* "Don't eat it. I know you. Don't."
15. **The Barrow Lord's Helm** · Legion Galea (Legion, plate) · *Home:* the Barrow Lord · *Act 2*
    - The dead strike you [20–30]% less often; every 20 of them you kill raises one to fight for you for 15 s.
    - *Downside:* "Chid will know what it is."
    - *Lore:* "The plume is horsehair. The horse was somebody's."

### Body

16. **The Ashen Plate** (exists) · Half-Plate · *Act 1* — values as `items.json` with ranges: +[30–45]% fire resistance, +[15–25]% fire damage, +8 armour in fire. *Downside:* "8% slower. It weighs what it weighs."
17. **The Drowned Coat** · Padded Robe (Sound) · *Home:* the Risen; the ditch on the Low Ford road · *Act 1*
    - Your dash at night leaves a trail of cold water that slows by [25–40]%. You do not burn.
    - *Lore:* "It has hung by Rook's fire for a week and it is still wet."
18. **Pelt of the Pack** · Wolfskin Cloak (Sound) · *Home:* `beasts.outcome` = slaughtered · *Act 1*
    - +[2–3] health for every wolf you have killed in this fight, to +[60–90]. Every wolf in an arena comes for you first.
    - *World:* the Pack does not speak to you again.
    - *Lore:* "Brannoc counted the pelts twice and did not say anything either time."

### Cloak

19. **Ashford Levy Colours** · Watch Cloak (Sound) · *Home:* Redcowl, `be.crates` = redcowl · *Act 1* · (Red Hand set)
    - *World:* the Kerchiefs let you pass. The Watch looks twice.
    - *Lore:* "Red was a town's colour before it was a gang's. Nobody in the Roost will tell you which town."
20. **The Old Hunter's Cloak** (exists, Named) — rerolls as Named with ranges; *Act 1*.

### Amulets

21. **Greymuzzle's Fang** · a commission: Brannoc sets the trophy (`greymuzzle_fang`) on a Copper Torc · *Home:* Greymuzzle's death · *Act 1*
    - Your bleeds mend you for [2–4]% of their damage. Wolves will not strike first.
    - *World:* `wolf_fang`.
    - *Lore:* "Old, yellow, and longer than it ought to be. He had it a long time before you."
22. **Greymuzzle's Collar** · *Home:* `beasts.outcome` = allied · *Act 1*
    - What fights for you is a wolf. +1 Spirit Companion in the ember if you take it, and +[20–30]% summon damage if you do not.
    - *Lore:* "There was never a collar. Maeca plaited one of bark, and he let her."
23. **Barrow-Bone Charm** (exists, Named) · *Act 1*, ranges on its raise chance [2–4]%.

### Rings

24. **The Ring of the Seventh** · Legion Seal-Ring · *Home:* the Legion; the Vault (Act 3) · *Act 3*
    - Your sets count one more piece. +[1–2] to every attribute.
    - *Lore:* "Seven notches round the inside, and a stamp: VII."
25. **Varrow Silver** · Signet · *Home:* Pell, `pell.fate` = ran, on his return · *Act 2*
    - +[40–60]% gold. Every 1,000 gold you carry: +2% damage, to +[16–20]%.
    - *Downside:* "Pell will want it back. He has said so in writing."
    - *Lore (Pell):* "I'm not a good man. I'm a careful one."
26. **The Coyle Signet** · Silver Ring · *Home:* Harlan, the cargo returned · *Act 1*
    - Shops sell to you [10–15]% cheaper; Rares salvage into one more ashsteel.
    - *Lore (Harlan):* "The Company pays its debts. Ask anyone."

### Relics

27. **The Warden's Lamp-Iron** (exists) · *Act 1*, ranges on its pale flame [10–14]% and +[15–25]% vs the dead.
28. **Grimtunnel's Spare Lamp** (exists) · *Act 1*.
29. **Kell's Lamp** · Miner's Lamp · *Home:* the Lamplings · *Act 1*
    - When you would die, your lamp goes on without you: for [2–3] s the horde follows it, not you. Once an arena.
    - *Lore:* "It came back up the shaft on its own, still lit. Nobody has asked it where Kell is."
30. **The Copper Toll-Token** · Toll Token · *Home:* the Vault's bootprints · *Act 1*
    - The first champion of every arena drops gear for certain; the toll lots cost you [10–20]% less.
    - *World:* Vonnra looks at it, and then at you.
    - *Lore:* "Trodden into a bootprint going in. The Toll Tower stamps them for its clerks."
31. **Holloway's Tally-Stick** · Brass Token · *Home:* Holloway, the bounty stopped or the road safe · *Act 1*
    - Every ten kills: +1% damage, to +[18–25]%; a champion's blow takes it all.
    - *Lore:* "Notches in tens. He has never been out by one."
32. **Chapter Four** · Commonplace Book (a relic, carried open) · *Home:* Keegan, if she comes north · *Act 2*
    - You take [12–18]% less from anything that rose; risen and Unchained foes take [20–30]% more from you.
    - *Downside:* "You find it hard to read."
    - *Lore (Keegan):* "Of the Unchained, and Their Return to the Dark. I've read it four times. I'm not reading it again."

Also proposed, Act 2–3, to write when those acts are: **Sallow's Silver Pen**
(marks written in silver pass on when the marked die; the Vigil can find you),
**The Cage Key** (once an arena you rise from death at half health, and every
champion comes for you), **Edric's Map** (the Wayfinder's eleventh drawing:
heralds take more from you), **Brannoc's Twelfth Iron** (`nell.told` honest:
the dead do not rise near you).

---

## 7. Sets

Bonuses at 2 / 3 / 4. One "more" at most per set. Set pieces are Named with an
argent rim; the set's look is in `VISUALS.md` §5.

### 7.1 The Watch's Kit (teaching set, 3) · Act 1 · the caravan wreck, Holloway, Brannoc's stock
Watch Coif (head, mail) · Watch Hauberk (body, mail) · Old Watch Shield (shield).
- **2:** +[15–20]% armour; your light carries 20% further.
- **3:** Standing still for a second, you block one blow in four. The Watch salutes you.
- *Lore:* "Eleven men, a year unpaid, and every one of them still oils his mail."

### 7.2 The Argent Vigil (warden, 4) · Act 2 · the Vigil
Vigil Bascinet · Vigil Plate · Argent Heater · Vigil Longsword.
- **2:** +[20–25]% holy damage; +[10–15]% block.
- **3:** Shield Bash leaves hallowed ground for 4 s.
- **4:** Oathblade's swings throw holy crescents; your holy skills deal 30% more to anything that rose.
- *Lore:* "Polished every morning, by a knight on probation, because the handbook says so."

### 7.3 The Barefoot Garrison (reaver, 4) · Act 1 (two pieces), Act 2 (all) · the Pack's arenas; Maeca
Garrison Axes (paired) · Garrison Straps (body, leather) · Cave-Mouth Cloak (fur) · Garrison Tags (amulet).
- **2:** +[30–45] health; you cannot be slowed below 70% of your pace.
- **3:** Crashing Leap and War Cry come [20–25]% sooner.
- **4:** Your speed bonuses also raise your damage, one for one. You never wear anything on your feet.
- *Lore (Maeca, Act 2):* "We held the cave mouths. The boots were coming."

### 7.4 Ash-of-Morrow (arcanist, 4) · Act 2 · Vonnra's lots; the Risen
Toll-Keeper's Hood (cloth) · Morrow-Cloth Robe · Square-Cut Rod (Rimeshard) · The Square Ring (ring).
- **2:** +[15–20]% spell area; +2 Wits.
- **3:** Blink and Time Slip leave a sigil on the ground for 4 s: spells cast from it cost no wait.
- **4:** Every seventh spell you cast is cast twice.
- *Lore:* "Violet is the Toll Tower's colour. It does not come out in the wash."

### 7.5 The Red Hand (stalker, 4) · Act 1 · the Kerchiefs; Redcowl
Redcowl's Hood (head, leather) · Ashford Levy Colours (cloak) · Red Hand Brigandine · Kerchief Knives.
- **2:** +[6–8]% critical chance; Kerchiefs take you for one of theirs.
- **3:** Mark Prey's prey is robbed: it drops gold and a draught when it dies.
- **4:** Your thrown and ranged skills fire one more projectile at marked enemies; marked enemies take 25% more from your projectiles.
- *Lore (Redcowl's Hood, after Act 1):* "His mother's idea, the name. The hat was his."

### 7.6 The Pack's Own (3) · Act 1 · the Pack; Maeca (cured or allied)
Hide Mantle (fur cloak) · Bone Necklace (amulet) · Fang Bow (crossbow).
- **2:** +[25–35]% summon damage; wolves will not strike first.
- **3:** A spirit wolf runs with you, always; in the ember, Pack Leader and Spirit Companion come 50% more often.

### 7.7 The Dig (3) · Act 1 · the Lamplings
Lamp Cap (leather head) · Pipe-Lad's Apron (leather body) · Sapper's Charge (relic).
- **2:** +[20–25]% fire damage; +[10–15]% ember gained.
- **3:** Your explosions leave slurry on the ground: poison for 3 s. Lamplings call you Boss.

### 7.8 The Morning Light (3) · Act 1 · the shrine; the Risen
Chapel Censer · Dawn Vestments (cloth body) · Pilgrim's Mitre (cloth head).
- **2:** +[15–20]% healing; +[15–20]% holy damage.
- **3:** Your holy skills mend you for 1% of what they deal. At dawn, your wounds close (by day: Wounded heals a day sooner).

### 7.9 The Fever Year (3) · Act 2 · the Fevered
Sickroom Hood (cloth) · Fever Shroud (cloth body) · Physician's Phial (relic).
- **2:** +[30–40]% poison resistance; +[15–20]% status damage.
- **3:** Poison on you is turned on whoever struck you. You can breathe in the bad air.

### 7.10 The Seventh Legion (4) · Act 3 · the Legion; the Depths
Legion Galea · Legion Segmentata · Legion Gladius · Legion Seal-Ring.
- **2:** +[25–30]% armour; +[10–15]% to every resistance.
- **3:** You and what fights for you hold the line: within 6 m of each other, both take 20% less.
- **4:** Every seventh kill, the Legion answers: seven pale spears fall on the strongest enemies for 300% of your strongest skill. Your Steel skills deal 25% more.
- *Lore:* "Seven of everything. Even the rivets."

---

## 8. Sigils and Watchwords

### 8.1 Sigil-stones

Twelve, from common to very rare. Three of one become one of the next (Vonnra).

| # | Sigil | In a weapon | In armour (body, off-hand) | In a helm |
|---|---|---|---|---|
| 1 | Ash | +6% fire damage | +8% fire resistance | +5% light |
| 2 | Salt | +6% physical damage | +8 health | +3% art power |
| 3 | Iron | +4% critical damage | +2 armour | +2 armour |
| 4 | Thorn | +4% status chance | +4 thorns | +6% tenacity |
| 5 | Moon | +6% arcane damage | +8% shadow resistance | +2% crit chance |
| 6 | Ford | +8% frost damage | +10% frost resistance | +4% dash speed |
| 7 | Lamp | +8% holy damage | +12% light, +6% vs the dead | +10% light |
| 8 | Barrow | +8% shadow damage | +8% less from the dead | +1 Resolve |
| 9 | Dawn | +6% healing on hit (cap) | +0.6 health a second | +5% art wait |
| 10 | Chain | +1 chain or bounce | +4% all resistances | +1 to all attributes |
| 11 | Crown | +10% damage | +6% health | +1 rank to the art |
| 12 | Heart | +1 rank to the skill (the cap holds) | +10% health; the dark finds you less often (−10% ranged aggro) | +2 to all attributes |

### 8.2 Watchwords

Recipes, in order, in a Plain or Fine base with exactly that many notches.
Each recipe is found in the world, written somewhere it belongs.

| Watchword | Base | Sigils | Power | Found in |
|---|---|---|---|---|
| **Keep the Lights Lit** | body | Lamp · Dawn · Lamp | +40% light; holy skills +25%; the dead take 20% more from you; you mend 1% a second in your light | the note in the Waystation's garden (`Waystation.cs`) |
| **Not By Us** | lantern | Ford · Lamp | your light slows the dead by 25%; +20% holy | the dead watchman's book (`Prologue.cs`) |
| **Quick Means After Dark** | cloak | Ford · Moon · Salt | at night +12% speed; your dash has one more charge | the pencil under the carters' notice |
| **It Always Has** | helm | Dawn · Ash · Dawn | your art comes 20% sooner; at the start of each arena you mend fully | a bark of Chid's |
| **Count the Boots** | body | Iron · Salt · Iron | +40% armour; you cannot be slowed | Holloway's office (Act 2) |
| **Forty Lamps** | shield | Lamp · Iron · Lamp · Chain | blocks throw light that burns the dead; +6 block | Keegan's tale of Ashe (`keegan.ashe`) |
| **The Little Bird** | knife belt | Moon · Thorn · Salt | knives that crit return and strike again | never written; Rav hums it (Act 2) |
| **What the Legion Buried** | sword, scythe | Barrow · Ash · Chain · Heart | +1 rank (cap); Steel skills +35% damage; kills of the dead rise as Legion for 6 s | the Vault door (Act 3) |
| **Here It Lies** | staff | Barrow · Moon · Heart | Cinderfall falls as a pale star; spells +30% area | the Sinkhole (faith knowledge, Act 1; usable from Act 3) |
| **The Fever Year** | flask | Thorn · Ash · Thorn | poison spreads on death; +40% poison damage | Wenna's ledger |
| **Toll Paid** | ring (2 notches: rings can roll one, Brannoc cuts the second) | Crown · Ford | +30% gold; +1 reroll in the ember | the Toll Tower's ledger |
| **Seventh** | any (4 notches, Heartwrought) | Chain · Chain · Chain · Heart | your sets count one more piece; +7% to every damage | the Depths, seventh Depth |

---

## 9. Example rolls, from common to the best

1. **Plain** · *Leather Cap* · Worn, ilvl 3
   +1 armour · +2% critical chance · Notches: 1 · Heat –
2. **Fine** · *Hale Leather Cap of the Hearth* · Worn, ilvl 7
   +1 armour, +2% crit · +19 health (II) · +9% frost resistance, the cold slows you 6% less (II) · Heat 24
3. **Rare** · *Grey Comfort* · Watch Hauberk (Sound, mail), ilvl 18
   +11 armour, +16 health (implicit, Resolve 6 met) · +41 health (IV) · +5 armour (IV) · +19% fire resistance (IV) · +2 Resolve (III) · Heat 20 · Asks 6 Resolve (you have 9)
4. **Rare, a good one** · *Patient Errand* · Arbalest (Wrought, Volley rank 2, Edge +75% Ranged), ilvl 24
   +28% physical damage (V) · +31% critical damage (IV) · +1 pierce · of the Swift Shaft (counts as Velocity) · Heat 20
5. **Marked** · *Low Water* · Frost-Iron Rod (Wrought, Rimeshard rank 2, Edge +60% Spell), ilvl 27
   +24% frost damage (V) · +3 Wits (V) · +12% area (IV) · **Mark of Deep Water:** frozen enemies take 38% more from storm and physical · Heat 16
6. **Named** · *Snib's Hard Hat* · Leather Cap (Sound)
   +1 armour, +2% crit · once an arena, a killing blow leaves you at 1 health and stuns within 5 m · +26% armour · lamplings call you Boss · "You look ridiculous."
7. **Set, completed** · the Red Hand on a stalker at level 18: +7% crit; Kerchiefs let you pass; Mark Prey robs; marked enemies take one more bolt and 25% more from your projectiles.
8. **Storied, bright** · *Corran's Sword* · Pale Brand (Heartwrought rework, Oathblade rank 3, Edge +180% Steel)
   Steel skills ✶ 37% faster while you stand still (bright) · every third swing a crescent of 108% (lifted) · +2 Might (Storied)
   *History:* "Held at his post. Found at the Old Watch-post, day 3." · "Taken back from Ash-Fang, who took your light, night 12." · "Named by Brannoc: Corran's Answer." · "The Barrow Lord, beyond the half hour, night 41."
   This is the known jackpot: a story item, reworked to the last tier, made Storied by four deeds, with a bright roll.
