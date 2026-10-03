# Visuals: how gear changes the survivor

What the survivor looks like from the Low Ford road to the bottom of the
stair, slot by slot and calling by calling; what the existing models can do
already; what must be made; and how the item pictures follow.

The rule (`VISION.md` §4): **the calling is the silhouette, the gear is the
material.** A warden always reads as a warden from the arena's high camera
(64°, 31 m); what changes, as the gear climbs, is what they are made of, what
is bolted on, and what glows at night. That rule is what the existing assets
can deliver, and it keeps every survivor recognisable in a horde.

---

## 1. What exists today

| Piece | Where | What it can do |
|---|---|---|
| The man's figure | `People.Build`: a Quaternius body (`Superhero_*_FullBody`) dressed in modular parts (`Lore.OutfitFor`) | Peasant set (arms, body, legs, feet), Ranger set (arms, body, legs, boots, hood, pauldron). The reaver is bare-chested in peasant legs and feet; the arcanist wears peasant; the warden and stalker ranger, the warden with a pauldron. |
| The cloth dye | `People.Dyes`, `person.gdshader` | A hue/saturation/value mask finds the cloth on `MI_Ranger` and `MI_Peasant` and dyes it the palette's cloth and under colours (`archetypes.json` palettes; the warden's also name plate, trim and leather colours, unused by the shader yet). |
| The woman survivor | `People.Heroine` + `heroine_outfit_{warden,arcanist,reaver,ranger}.gltf` | One outfit per calling, **made of many separate pieces** (the warden's: plate, pauldrons, vambraces, greaves, knees, sabatons, band, straps; the ranger's: corset, collar, bracers, gloves, four pauldron plates, belt, pouch, boots; the reaver's: cape, straps, bracers, wrist and boot fur, belt; the arcanist's: hat in four parts, corset, cuffs, gloves, boots). Skin under each outfit is hidden by a vertex-colour channel. |
| KayKit characters | `assets/characters/{knight,barbarian,mage,rogue,rogue_hooded}.glb` | Separate meshes for **Knight_Helmet, Knight_Cape, Barbarian_Hat, Barbarian_Cape, Mage_Hat, Mage_Cape, Rogue_Cape**, four shields (badge, rectangle, round, spiked), one- and two-handed swords and axes, a wand, a staff, a spellbook (closed and open), crossbows, knives. The skeleton kit's helmets, hoods and cloaks too. |
| Held weapons | `Arms.cs`, `Loadouts.Held` | Chevalier sword, Viking sword, longsword, zweihänder, mace, Viking axe, snake axe, mage staff (long and short), crossbow, a made wand, round shield, two daggers. Only nine items map to a model today; the rest fall back to the calling's first weapon. |
| A dyed cloak | `CharacterData.Cloak`, `looks.json` cloaks | A cloak in one of eight dyes, or none. |
| Item pictures | `ItemModels.cs` (what each picture is of), `ItemPhotos.cs` (a studio, photographed once and kept) | About fifty keyed models: weapons are the held models, the rest made from shapes (helms and lamps on a lathe, garments draped). Each item names one key (`ItemDef.Icon`). |
| Loot on the ground | `BattleFx` loot beams | A column in the rarity's colour, 3.2 m for gear, 1.4 m for materials; a sack or chest model. |

Today head, body and cloak items change nothing on the figure. That is the
gap this file closes.

## 2. Material tiers: rags to relic

Five looks, one per base tier (`SYSTEM.md` §4.1). The first four are mostly
material and pieces over the calling's own outfit; the fifth is new.

| Tier | Look | Material (shader) | Pieces | Colour |
|---|---|---|---|---|
| I Worn | **Rags** | rough, matte, frayed; dye desaturated 40%, a grime layer | the calling's base outfit, fewest pieces (no pauldron) | dull, mud at the hem |
| II Sound | **Leather and mail** | the outfit as authored; leather with a sheen; iron mail where the weight is mail | + the first piece of its weight (a pauldron, a bracer, a hood) | the palette's colours, clean |
| III Wrought | **Plate and good cloth** | metal brighter, edges catching the rim light; cloth deeper and richer | + the second piece (both pauldrons, greaves, a mantle) | palette + **trim** colour on edges and rivets (the palettes already name `trim`) |
| IV Legion | **Red lacquer and bronze** | metal turns bronze-and-iron; leather lacquered dark red; cloth edged in a Legion key-pattern | + a Legion piece (crested helm, segmented plates, a skirt of strips) | a bronze and oxblood accent laid over the palette |
| V Heartwrought | **Pale relic** | pale bone-plate and chitin, matte, faintly translucent at the edges; **ember veins** in the seams | the pale set: a new mesh per calling (§4) | bone-white and ash, veins dark by day, **burning orange at night** |

Rarity does not change the material (a Rare Worn coat is still rags); it adds
a **finish**: Fine and Rare nothing; Marked a faint violet sheen on the metal
in the dark; Named and set pieces their own look (§5); Storied the ember-red
glint on edges.

**One shader, not five models.** Tiers I–IV are one parameter on the person
shader (`material_tier` 0–3) that blends grime, roughness, metal colour and the
trim and accent colours, plus a list of which pieces are shown. That is almost
all shader and data work, no modelling.

## 3. Slot by slot

### Weapon and off-hand

Every weapon family (`CATALOGUE.md` §2.1) needs a held model per **two** tiers
(I–II share, III–IV share, V its own) and the material shader on top:

| Family | I–II | III–IV | V | Need |
|---|---|---|---|---|
| Sword | chevalier_sword | longsword (III), viking_sword with a Legion grip (IV) | **new**: pale brand | 1 model |
| Disc | shield_round (thrown) | KayKit Badge_Shield | new: chitin wheel | 1 |
| Cleaver | viking_axe | KayKit 1H_Axe | new: bone falx | 1 |
| Paired axes | viking_axe × 2 | snake_axe × 2 | new | 1 |
| Scythe | – | – | – | **3 new** (no scythe exists) |
| Wraps | (hands) | KayKit spiked shield's rivets as knuckles? | new | 2 small |
| Wand | Made.Wand | KayKit 1H_Wand | new | 1 |
| Staff | short_staff | mage_staff | KayKit 2H_Staff reworked, new head | 1 |
| Rod | mage_staff (short) | mace (as a sceptre) | new | 1 |
| Crossbow | crossbow | KayKit 2H_Crossbow | new | 1 |
| Knife belt | daggers | KayKit Knife, Throwable | new | 1 |
| Chakram | – | – | – | 2 new (ring blades are simple to make) |
| Shield | shield_round | KayKit Round, Rectangle, Badge, Spike shields | new: carapace | 1 |
| Lantern, censer, totem, tome... | `ItemModels` shapes (lantern, censer, totem) | the same, larger, trimmed | new | made in code (Shapes) |

So: reuse covers Tiers I–IV for most families; Heartwrought needs about a
dozen new weapon models, and the scythe and chakram need theirs from Tier I.
The ComfyUI → TRELLIS/Pixal3D pipeline (`RC_PLAN.md`) suits these: a concept
sheet in the darkbrush style, a mesh from it, a cleanup in Blender.

### Head

| Calling | Worn | Sound | Wrought | Legion | Heartwrought |
|---|---|---|---|---|---|
| Warden (plate) | bare head | Ranger hood (exists) | KayKit Knight_Helmet | Legion galea (crested): **new** | pale crest: **new** |
| Reaver (leather) | bare | headband (new, small) | KayKit Barbarian_Hat (horned) | Legion leather galea: new | chitin cowl: new |
| Arcanist (cloth) | bare | hood | KayKit Mage_Hat, or her hat (exists in four parts) | augur's hood: new | pale veil: new |
| Stalker (leather) | hood (exists) | hood | hood + mask (new, small) | Legion hood: new | chitin cowl: new |

The `Headgear` choice at creation stays: "show my helm" off hides head items
(Diablo's oldest kindness to people who like their character's face). Named
heads (the Moonsilver Circlet, Snib's Hard Hat, the Moonpetal Crown, the
Barrow Lord's Helm) need their own small models; the circlet and the crown
are simple rings, the hard hat a cap with a lamp on it.

### Body

The body item shows as **material and pieces over the calling's outfit**:

| Weight | Men (Quaternius) | The woman survivor (heroine) |
|---|---|---|
| Cloth | Peasant set, dyed; at III+ a longer robe (**new** robe part, or the KayKit mage body) | the arcanist outfit's corset and cuffs; at III+ a mantle (new piece) |
| Leather | Ranger set, dyed; leather sheen | the ranger outfit; III+ shows the corset trim and pauldron plates 0–1, IV+ plates 2–3 |
| Mail | Ranger set with a **mail material** on the body (shader swap) | the warden or ranger pieces with mail material on the suit |
| Plate | Ranger set + pauldron; III+ a breastplate (**new** part, or KayKit Knight_Body) | the warden outfit: plate always; pauldrons at II+; vambraces and greaves at III+; knees and sabatons at IV |

**For the woman survivor this is mostly visibility.** Her outfits already come
in many pieces; showing more of them as the gear's tier rises (a pauldron at
Sound, vambraces at Wrought, greaves at Legion) is a list in data, and gear
that is heavier than her calling's own outfit borrows pieces from another
outfit (a stalker in mail wears the warden's vambraces). Pieces that cross
outfits must be checked in the running game for clipping. Her Heartwrought
set is new modelling: four outfits through `tools/assets/heroine_outfits.py`.

For the men, the Quaternius kit has only two outfit sets here. Before
modelling anything, check whether the full Quaternius modular outfit pack
(CC0) has more sets (knight, wizard and others appear in Quaternius's fantasy
character packs); if they do, Tiers III–IV for men become imports.

### Cloak

| Tier | Look |
|---|---|
| I–II | the dyed cloak (exists), shorter and frayed at I |
| III | full length; trim colour at the edge; KayKit capes as alternatives (Knight_Cape for plate, Mage_Cape for cloth) |
| IV | a Legion sagum: red, with a bronze clasp |
| V | the pale mantle: torn into strips that drift as if under water, ember veins at night |
| Fur cloaks | the reaver's cape (her outfit has one; men need a fur cape: **new**), wolf pelts at II+ |

Cloth physics is not proposed; a short bone chain on long cloaks (as her
braided hair has, `heroine_hair_braid.chain.json`) is enough.

### Amulet, rings, relic

Too small for the high camera. Two exceptions worth doing:
- **The relic at the hip**: lamps and lanterns hang from the belt and are lit
  at night (a small light, which also serves the Moonless oath's light rules).
- **Close-ups** (character screen, dialogue): the amulet as a glint at the
  throat.

## 4. Per calling, low to high

| Calling | Worn (day 1) | Sound (Act 1 end) | Wrought (Act 2) | Legion (Act 3) | Heartwrought (the end) |
|---|---|---|---|---|---|
| **Warden** | peasant shirt under a rusted pauldron, bare head, chipped sword | Watch mail, hood, round shield | Vigil plate, bascinet, argent trim, kite shield | crested galea, segmented plate, scutum, red sagum | pale crest and bone-plate, ember-veined brand and carapace shield |
| **Reaver** | bare chest, rag trousers, war-paint | leather straps, wolf-pelt cape, bracers | horned hat, fur, iron knuckles, axes with leather grips | lacquered harness, falx, the Legion's red | chitin and bone, a pale harvest scythe, veins down the arms |
| **Arcanist** | homespun robe, bare head, a stick of a wand | dyed robe, hood | scholar's robe with trim, hat, a bound staff with a lit head | augur's robe with the key-pattern, Legion sceptre | the pale shroud and veil, a heart-ice rod, glowing sigils at the hem |
| **Stalker** | ragged hood, rawhide jerkin | ranger leathers, crossbow | brigandine, a mask, bandolier of knives | red-lacquered cuirass, scorpio | chitin coat and cowl, a pale arbalest |

## 5. Named items and sets

Each set should look like a set on the figure: the pieces share a colour and a
motif, so a completed set is recognisable from the arena camera.

| Set | Motif | Colour | Reuse | New |
|---|---|---|---|---|
| The Watch's Kit | blue tabard over mail, the Watch's lamp badge | Watch blue `#34508c` (exists in `looks.json`) | Ranger set + mail material; KayKit Badge_Shield | the lamp badge decal |
| The Argent Vigil | polished silver plate, white surcoat | silver, white, a black trim | warden pieces; KayKit Knight_Helmet | a surcoat (cloth piece) |
| The Barefoot Garrison | straps, fur, bare feet (the feet part is hidden) | Ashford red faded to brown | reaver pieces, her reaver outfit | barefoot variants of the leg parts |
| Ash-of-Morrow | violet robe, square-cut sigils | Toll Tower violet | peasant/arcanist pieces; Mage_Hat | the sigil decals |
| The Red Hand | red kerchief, red cloak, brigandine | Kerchief red | Ranger set + hood; the red kerchief model (exists in `ItemModels`) | a kerchief mesh on the head |
| The Pack's Own | wolf pelts | grey, bone | fur cloak | – |
| The Dig | leather cap with a lamp, apron | lamp-black, brass | leather cap | a head lamp |
| The Morning Light | white and gold vestments | dawn gold `#ffd46a` | robe pieces | a mitre |
| The Fever Year | plague hood, long shroud | bitterroot green, grey | the Blightward Mask model (exists in `ItemModels`) | – |
| The Seventh Legion | red, bronze, crested helm | oxblood, bronze | Legion pieces (§2) | – (the Legion tier's own models) |

Named heads and relics get bespoke small models (§3). Named weapons use their
base's model with a material variant (Corran's Sword: the Watch sword with a
notched spine decal).

## 6. Glow and ember: the night's tell

The ember burns only at night; so does the best gear.

- **By day**, Heartwrought veins, Storied edges and bright-affix glints are
  dark: cracks in pale material, dull red.
- **At night** (`ArenaRun` is always night; the Verge at night too) they burn:
  emissive orange that pulses slowly, faster as the survivor's ember level
  rises (a shader parameter fed from `Battle.EmberLevel`). At ember level 1 a
  glow; by minute thirty the survivor's gear is visibly alight.
- **Rarity glow on the figure**: none for Plain to Rare; Marked a violet
  sheen in moonlight; Named an amber glint on edges; Storied ember. Small, in
  the rim light, never a halo: from the high camera the survivor must still
  read as a figure, not a lamp (`RC_PLAN.md` §1: restraint).
- **The Unchained tell.** Players will notice that the survivor's best gear
  only burns at night before Act 2 tells them why. It is a visual seed of
  "What are you?" and costs nothing to plant.

## 7. Dyes and the tailor

- **Dyes** colour cloth (and, with the warden's palettes, plate, trim and
  leather): the palette chosen at creation is the default; dyes bought from
  Harlan or found override it per item. The `looks.json` cloak dyes extend
  to all cloth.
- **Glamour (Rav's tailoring)**: wear the look of any item ever owned in the
  same slot, the same weight or lighter. Looks are collected by owning, so
  every Named, set and Heartwrought look is a collectible (`PROGRESSION.md`
  §6.8).
- Glamour is free of heat and power, always reversible.

## 8. Icons and photos

`ItemPhotos` photographs a model per key, once. To follow the gear:

1. **Keys per base family and tier band**, not per item: `helm_plate_2`,
   `body_mail_4`, `sword_5`. About 25 families × 3 bands (I–II, III–IV, V)
   = 75 keys, most built from shapes already in `ItemModels` (Helm, Cap,
   Mail, Plate, Jerkin, Cloak) with tier parameters (rust and grime at I,
   trim at III, bronze at IV, pale and veined at V).
2. **The material shader in the studio too**, so the photo's metal is the
   figure's metal.
3. **Rarity is the frame, not the photo** (`ItemViews` already rims the slot
   in the rarity's colour). Named items get their own key and photo; set
   pieces an argent corner.
4. **Bump `ItemPhotos.Version`** when the keys change; photos are kept in
   `user://icons/` and retaken once.
5. **Dyes in the photo**: the photo shows the item in the survivor's dyes
   (a second key suffix by palette, generated lazily), so the pack shows what
   the figure wears.

## 9. Loot on the ground

| Rarity | Beam (today 3.2 m, the rarity colour) | Proposed | Sound |
|---|---|---|---|
| Plain | yes | none (the item glints) | a dull clink |
| Fine | yes | 1.4 m | a soft ring |
| Rare | yes | 3.2 m | a clear bell |
| Marked | yes | 3.2 m, pulsing slowly | a struck bell, held |
| Named | yes | off the top of the screen, amber, with a ground ring | the toll bell |
| Storied / set | – | Named's, with embers rising / argent motes | the toll, then a breath of fire / a silver chime |
| Bright affix on anything | – | a star of light at the beam's foot | a high spark under the item's own sound |

From the arena's camera a Named pillar must be visible from anywhere in the
fight. The spoils screen (`SYSTEM.md` §12) repeats the sounds as each item is
shown, Named last (Vampire Survivors' chest is the model: the reveal is the
reward).

## 10. Modelling budget

| Work | Kind | Size |
|---|---|---|
| Material tier parameter in `person.gdshader` + piece lists in data | shader, data | small; unlocks Tiers I–IV for everyone |
| Her outfit pieces shown by tier and weight | data, a check per calling | small |
| KayKit helmets, hats, capes and shields as attachments on the Quaternius and heroine skeletons | rigging, fit | medium (style check: KayKit is chunkier) |
| Night glow (emissive veins driven by ember level) | shader | small |
| Heartwrought: four outfits for her, four body overlays for men, about twelve weapons, four helms | modelling | large; Act 3, last |
| Scythe and chakram families | modelling | medium; needed when those skills become weapons |
| Named heads and relics (about ten small models) | modelling | medium |
| Set decals and small parts (badges, kerchief, mitre, head lamp) | modelling | small each |
| Icons: 75 keyed photos from shapes with tier parameters | code | medium |
