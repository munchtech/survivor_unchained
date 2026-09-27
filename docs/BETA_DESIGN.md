# Survivor Unchained — Beta Vertical Slice: Design Bible

This is the contract the beta is built against: who is in the world, what they
want, what the player can do about it, and what the world remembers. Systems
first; content is authored to exercise them.

## The world (from The Ember Watch)

When something dies it leaves a stone with light still in it. People call it
**ember**. Break the stone and take the light, and for as long as you carry it
you burn: stronger, faster, able to hold a line no one should hold. The light
does not keep. Rest, and it gutters out.

Every night the dark climbs out of the ground. The **Watch** used to hold the
roads with lights. Most of the lights went out.

The player is a traveller on the **Low Ford road** at dusk. By dawn they have
learned what ember is, and they come up the road into **the Waystation**, where
the last three roads meet.

Ember is the expedition's power (the Survivors layer: gems, level-ups, weapons,
evolutions). It resets when you rest. Everything else persists: character
level, gear, knowledge, relationships, the world.

## Character creation

| Archetype | Model | Start weapon (choose) | Ability (choose) |
|---|---|---|---|
| **Warden** | Knight | Oathblade · Judgement Disc | Shield Bash · Bulwark |
| **Reaver** | Barbarian | Butcher's Cleaver · Axe Gyre | Crashing Leap · War Cry |
| **Arcanist** | Mage | Seeking Motes · Cinderfall · Rimeshard | Blink · Time Slip |
| **Stalker** | Hooded rogue | Volley · Knifestorm | Mark Prey · Smoke Bomb |

Starting passive: one of Might, Haste, Vitality, Fleetfoot, Precision.

**Backgrounds** — not stat bonuses. They change what you notice, know and can do.

| Background | Knowledge | Starts with | Opens |
|---|---|---|---|
| **Hunter** | `beastlore` | Old Hunter's Cloak | Reads animal sign; can speak with the pack; Maeca treats you as one of hers |
| **Scholar** | `arcana` | Cracked Lens | Reads the Vault's script; the herbalist's samples make sense; Vonnra is curious |
| **Outcast** | `underworld` | Red Kerchief, lockpicks | Kerchief cant; Rav's trust; Pell's warehouse at night; fences |
| **Devout** | `faith` | Pilgrim's Ember-Lantern | Shrine rites; Chid's trust; the dead speak a little at the Low Ford |

## The town: the Waystation

Where three roads meet under Vonnra's toll. Stone walls, a square with a well,
a tavern, a shrine, a smithy, a market.

| NPC | Role | Wants | Notes |
|---|---|---|---|
| **Vonnra Hydrocheck** | Far seer, keeps the toll | Payment, always | Strange merchant. Refuses to discuss the sealed vault. Reads your fortune at chapter's end. |
| **Maeca Barefoot** | Hunter, of the fallen Ashford Garrison | The truth about the forest | "Something is driving them out." |
| **Chid, "the Fool"** | Priest at the broken shrine | The shrine to work again | "It used to work." Devout route. |
| **Dr. Rav McBreathless** | Kerchief defector, in the tavern | To never go back | Knows how the Kerchiefs work. Outcast route. Fence. |
| **Captain Holloway** | Watch captain | Roads open, beasts dead | "The beasts are bolder." Pays bounties. Arrests thieves. |
| **Harlan Coyle** | Merchant; caravan owner | His caravan, his nephew | "They're attacking caravans." Quest B. |
| **Pell Varrow** | Rival factor | To corner the market | Secretly paid the Kerchiefs to take Coyle's caravan. |
| **Old Wenna** | Herbalist | Samples from the stream | "The animals weren't like this before." |
| **Tam** | Farm boy, frightened | His family safe | "Something is killing them." |
| **Brannoc** | Blacksmith | Good steel, good pelts | Buys beast materials; crafts from them. |
| **Mother Rook** | Innkeeper | Paying guests | Rest, save, storage, rumours. |
| **Professor Keegan** | Knight of the Argent Vigil (probationary), at the north gate | Nobody through the gate | "You aren't ready for what's beyond there." Future content. |

## Factions

| Faction | Members | Initial stance |
|---|---|---|
| Waystation folk | Townspeople | Neutral |
| The Watch | Holloway, guards | Neutral |
| Coyle Company | Harlan, teamsters | Neutral |
| Kerchiefs | Redcowl's band | Hostile (Outcast: wary) |
| The Pack | Greymuzzle's wolves | Hostile (Hunter: wary) |
| The Diggers | Grimtunnel's lamplings | Hostile |
| Order of Morning Light | Chid | Neutral (Devout: friendly) |

Factions act each day (see *World simulation*).

## Outside zone: Thornhollow Verge

One zone, several places:

- **The Old Road** — east from the Waystation gate. The caravan wreck.
- **The Hunters' Blind** — Maeca's camp; she can be found here in the day.
- **Wolf Hollow** — the Pack's den. Greymuzzle.
- **Redcowl's Roost** — the Kerchief camp in the ravine: tents, powder, cages.
- **The Blighted Stream** — green water, sick wolves, bitterroot.
- **The Dig** — Grimtunnel's lampling crew, a pump pouring ember-slurry into the stream. The root cause.
- **The Sealed Vault** — an old-empire door in the hillside. *Breadcrumb A.*
- **The Sinkhole** — something enormous and dead at the bottom. *Breadcrumb B.*
- **The Moon Grove** — behind a bramble wall that only fire (or an axe, slowly) opens. Secret.
- **Old Watch-post** — a ruined post with a fire you can light: a place to rest in the field.

## Quest A — The Beast Problem

Wolves are attacking the road. Everyone has a theory.

| Source | Says | Truth |
|---|---|---|
| Holloway | "They're bolder." | Symptom |
| Maeca | "Something is driving them out." | True |
| Harlan | "They're attacking caravans." | Symptom (and cover for Quest B) |
| Wenna | "The animals weren't like this before." | True: blight |
| Tam | "Something is killing them." | True: the slurry |

**Clues** (knowledge): sick wolf carcass (`clue.sick_wolf`), green stream
(`clue.green_stream`), slurry pipe (`clue.pipe`), lampling tracks
(`clue.lampling_tracks`), Wenna's analysis of a stream sample
(`clue.analysis`) → **`know.root_cause`**.

**Approaches**

1. **Hunt** — kill wolves (population falls), bring pelts or Greymuzzle's
   fang to Holloway for the bounty.
2. **Investigate** — find the clues; learn the Dig is poisoning the stream.
3. **Communicate** — with `beastlore`, or the Wolf-Fang Necklace, or the Old
   Hunter's Cloak *and* no wolf blood on your hands this expedition:
   Greymuzzle does not attack. Walk into the Hollow and he will "speak".
4. **Exploit** — sell pelts to Brannoc and still claim the bounty; tell
   Holloway the beasts are dealt with; lead the Pack onto the Kerchief camp
   (hostile factions fight each other); sell the Dig's location to Pell.
5. **Root cause** — stop the pump at the Dig: fight the crew, break the pump,
   blow the powder, or (Outcast/Scholar) talk the foreman into moving.
6. **Do nothing** — the problem escalates by day.

**Outcomes** (`beasts.outcome`)

| Outcome | World |
|---|---|
| `slaughtered` | Road safe; pelts scarce then gone; wolves never return; Maeca disappointed; bounty paid. |
| `allied` | Wolves fight beside you in the Verge; hunters (Maeca, Holloway) split on it; Brannoc loses pelts. |
| `cured` | Blight recedes over days; wolves calm; Maeca's respect; Wenna's gift; rare moonpetal grows. |
| `exploited` | Gold; the people you played find out as gossip spreads. |
| `ignored` | Day 3 caravans fail more; day 5 Tam's farm is raided; day 7 wolves at the gate at night. |

## Quest B — The Missing Caravan

Harlan Coyle's caravan never arrived. His nephew Jory was with it.

**What happened**: Pell Varrow paid the toll-clerk to tell the teamster the
east road was closed. The caravan took the forest track. The Kerchiefs were
waiting (Pell tipped them). The cargo is at Redcowl's Roost; three survivors
are caged there. The cargo includes blasting ember bound for the Dig.

**Approaches**

1. **Track it** — the wreck on the Old Road; ruts turn into the forest; red
   fletching; a dragged trail to the Roost.
2. **Investigate the route** — the gate guard says the road was never closed;
   the tavern says a clerk turned them; Vonnra's toll ledger shows they never
   paid.
3. **Follow the money** — Pell's warehouse (locked; night; lockpicks or the
   clerk's key). His ledger. **Expose** him (to Holloway or Harlan) or
   **join** him (he pays; Kerchiefs let you pass; Harlan ruined).
4. **Negotiate** — walk into the Roost unarmed-looking (Red Kerchief, or
   `underworld`) and deal with Redcowl: **pay**, **trade** pelts, **threaten**
   (if you've killed enough Kerchiefs), **trick** (tell him the Watch is
   coming), **favour** (deal with the wolves harassing the camp), **exploit**
   (tell him Pell sold him out).
5. **Take the goods** — keep the cargo. Sell it to Rav's fence. The town
   reacts: prices up, Harlan hostile, Holloway's bounty, Kerchiefs offer
   protection.
6. **Rescue people, not goods** — free the cages (they die if the camp
   burns with them in it, or after day 4).

**Outcomes** (`caravan.*`): `cargo` (returned / kept / lost / with
Kerchiefs), `survivors` (rescued / dead / captive), `pell` (exposed / ally /
unknown), `player.wanted`.

## Breadcrumbs

**A — The Sealed Vault.** Symbols (Scholar reads: *"Here the Seventh Legion
buried what it could not burn"*). A sigil fragment on a corpse outside.
Fresh bootprints: someone got in. Vonnra refuses to discuss it. Chid says the
old empire "did something here." Cannot be opened in the beta.

**B — The Thing Below.** Tremors that shake the camera. The Sinkhole: a
pale, eyeless, segmented thing, dead, bigger than a house. A lampling
survivor babbling ("It moved. The dark moved."). A map fragment showing the
Dig's tunnels going *down*. Grimtunnel (who escaped the Low Ford) is digging
toward it.

## Death is content

On death: you wake at the Waystation shrine (Chid found you), with an
**injury** until healed. Your ember is gone. Your **corpse** stays where you
fell with your gold and one carried item. The creature that killed you is
**promoted**: named ("Ash-Fang, Who Took Your Light"), stronger, carrying what
it took, roaming the zone. Kill it to take it back. NPCs have heard.

## World simulation (daily tick)

When a day passes (resting at the inn):

- Quest clocks advance (beast escalation, caravan survivors).
- Factions act: Kerchiefs raid if strong and the road is unguarded; the Pack
  roams toward town if the blight is unchecked; the Diggers dig deeper
  (tremors grow).
- Gossip spreads: each notable event known by someone spreads along social
  links to others; people who hear it change how they feel about you.
- Shops restock according to supply (pelts, cargo, trade routes).
- The zone repopulates according to its ecology.

## Persistence

One versioned save: character, gear, stash, world state, NPCs, factions,
quests, history, knowledge, corpse/nemesis, discoveries. Autosave on rest,
on zone change and on important events. Quit and reload: everything remains.
