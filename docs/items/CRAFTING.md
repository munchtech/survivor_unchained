# Crafting: what the survivor can do to gear

Salvage, temper, rework, notch, tincture, bind, consecrate, steep, and the
tailor; the materials they cost; the heat that limits them; the gold that
pays for them; and the people who do each one. Every craft is done **by a
person in the world**, in their place, in their voice: crafting is one more
way the town remembers you, and one more thing the story can take away.

Rules (`VISION.md` §3.8–9): show cost, chance and range before the click; a
craft can fail to improve, it can never destroy; heat runs out, nothing
breaks; the one real gamble (slurry) says so.

---

## 1. Materials

Seven crafting materials, plus the world's own. All go in the materials pouch
(no pack slots, `SYSTEM.md` §12).

| Material | From | Used for | Today |
|---|---|---|---|
| **Scrap** | salvaging Plain and Fine gear | tempering grades I–III; notches; rework | new |
| **Ashsteel** | salvaging Rares | tempering IV–VI; rework to Legion | new |
| **Sigil chips** | salvaging Marked items | the binders' book (lift and press); sigil-stones | new |
| **Remnants** | salvaging Named and set pieces | rerolling a Named item's ranges; consecration | new |
| **Ember shards** | lamplings by day; arenas (champions, Embers oath) | rekindling heat; ember imbues | exists (`ember_shard`) |
| **Slurry** | the Dig; the Blight oath | steeping (`§7`) | `slurry_sample` exists as a quest item; a stackable jar is new |
| **Sigil-stones** | arenas (chests, the Ruin oath), the Vault | notches and Watchwords (`§8`) | new |
| *The world's own* | creatures and places | commissions and tinctures | wolf pelt, boar hide, red cloth, barrow dust, bitterroot, moonpetal (exist) |

Salvage yields (rounded down, at least 1):

| Rarity | Yields |
|---|---|
| Plain | 1–2 scrap |
| Fine | 2–3 scrap |
| Rare | 3 scrap, 1 ashsteel (2 at ilvl 22+) |
| Marked | 2 ashsteel, 1–2 sigil chips; its Mark goes into the binders' book if new or better (free, automatic) |
| Named | 2 remnants (3 if it was a duplicate) |
| Storied | cannot be salvaged without a confirmation in the item's own words ("You'd throw this away?") |

Salvage happens anywhere the survivor is safe, and from the arena's spoils
screen. Brannoc's forge is not needed to break things.

## 2. Heat

Every item has **heat**: how much more it can take before it is set. It is
Last Epoch's forging potential, in a smith's word: a hot piece can be worked,
a cold one cannot.

- An item drops with heat by rarity: **Fine 24, Rare 20, Marked 16, Named 10,
  Storied 10**, ±20%.
- Each craft costs heat, **shown as a range before the click**: e.g.
  tempering grade III → IV costs 3–6 heat.
- At 0 heat the item is **set**: its affixes stay forever; only the tailor and
  the notches (sigils in, sigils out) still touch it.
- **Rekindling**: once per item, ember shards restore half its starting heat
  (cost: 5 shards × its tier). It is the one way back.
- A craft that fails to improve (a reroll that lands lower) **still spends its
  heat, and keeps the item as it was**. Never "the item is destroyed".

## 3. Brannoc's forge (the smith)

Brannoc buys pelts and beast materials and crafts from them (`BETA_DESIGN.md`).
He is the heart of crafting. If the survivor lies to him about Nell (Act 2,
`STORY_BIBLE.md` §7.8), he "never works for the survivor again": his forge
closes to them for good, and Snib's bodgery at the Dig (Act 3, or Act 2 if the
Dig still stands) takes over every service below with worse odds (+1 heat on
every cost) and one odd extra: Snib can steep (`§7`).

| Service | What it does | Cost | Heat | Chance |
|---|---|---|---|---|
| **Temper** | raise one affix one grade (to the item's ilvl cap) | scrap (I–III) or ashsteel (IV–VI) × grade; gold 15 × grade × tier | 2–5 | always succeeds; the new roll is within the new grade |
| **Hone** | reroll one affix's value within its grade | 1 scrap or ashsteel; gold | 1–2 | keeps the better of old and new, *or* the new: the player picks before paying |
| **Reforge** | replace one affix with a random one of the same kind (prefix or suffix), at the same grade | 2 ashsteel; gold | 4–7 | the new affix is shown, then kept or refused (refused: heat spent, item unchanged) |
| **Add** | a Fine with one affix, or a Rare with three, gains one random affix at grade I–III | 4 scrap / 2 ashsteel | 5–8 | always |
| **Rework** | raise the base one tier (Worn → Sound → Wrought → Legion → Heartwrought) keeping every affix: the beloved item made better | scrap, ashsteel and a Plain base of the target tier; gold 100 × tier | 6–10 | always; the item's ilvl becomes the new base's floor |
| **Cut a notch** | +1 notch, up to the base's maximum | 3 scrap + 1 sigil-stone of any kind | 5 | always; once per item |
| **Commission** | a chosen base of a chosen slot, made to order, Fine with one affix of the survivor's choice (from that slot's pool, grade by Brannoc's trust: III, IV with respect ≥ 30) | the world's own materials (pelts for leather, hides for cloaks, red cloth for linings) + gold | – | three days' wait (the world clock ticks: `World/`) |
| **Name a blade** | once per item, he names a weapon he reworked: it gains a history line ("Named by Brannoc at the Waystation") | trust ≥ 40 | – | – |

Brannoc's lines while he works should come from `VOICES.md`: few words, the
forge doing the talking.

## 4. Wenna's tinctures (essences)

Wenna's remedies already answer what the oaths do to a survivor (blight,
poison). Her tinctures do the same for gear: a **chosen** affix, guaranteed
(PoE's essences, Grim Dawn's augments).

| Tincture | Adds (a suffix, at grade = her standing with you, II–V) | Made from |
|---|---|---|
| Bitterroot | of the Physician (poison resistance, mending) | 3 bitterroot |
| Wolfsbane | of the Wolf | 2 wolf pelts, 1 bitterroot |
| Hearth | of the Hearth (frost resistance, sure footing) | 1 boar hide, 2 bitterroot |
| Salamander | of the Salamander (fire resistance) | 2 ember shards, 1 bitterroot |
| Grave-salt | of the Grave (shadow resistance, less from the dead) | 3 barrow dust |
| Moonpetal | of Mending (+regeneration) at one grade above her standing | 1 moonpetal |

A tincture needs an open suffix, costs 4–6 heat, and always succeeds. Wenna
will not make tinctures for a survivor while the stream is still green (she is
too busy), which is one more reason to cure it.

## 5. The binders' book (Vonnra)

The book of Marks: Diablo IV's codex of power and Diablo III's Kanai's cube,
held by the last of the binders' line.

| Service | What | Cost |
|---|---|---|
| **Lift** | Take a Marked item's Mark into the book; the item is destroyed. (Salvaging a Marked item does this for free if the Mark is new or better; lifting is for when you want the item gone and the book updated without salvage's chips.) | free |
| **Press** | Burn a Mark from the book into a Rare of a fitting slot. The Rare becomes Marked, keeps three of its affixes (the player picks which goes if it had four), and takes the Mark at the **book's best strength** | sigil chips × the Mark's grade; gold 50 × ilvl; 6–9 heat |
| **Read** | The book shows every Mark seen, its best strength, and where it can burn | – |

Every Mark the survivor has **seen drop** is written in at its lowest strength
the moment it drops, kept or not. So nothing seen is ever lost, and a better
copy upgrades the page.

Vonnra also: combines sigil-stones (three of one into one of the next, Diablo
II's cube), sells the toll lots (`ACQUISITION.md` §9), and reads the weekly
fortune. If she has been accused (`vonnra.accused`) she does all of this in
full sentences, with the survivor's name, and charges a tenth less ("I owe you
for having seen me", `STORY_BIBLE.md` §8): a small, true consequence.

## 6. The shrine (Chid)

| Service | What | Cost |
|---|---|---|
| **Consecrate** | reroll a Named item's ranges (all of them; keep old or new) | 2 remnants; a donation (gold) |
| **Bless** | once per item, a history line on a holy or light-bearing item ("Blessed by Chid at the broken shrine"); counts toward Storied | the shrine working again (Act 1's devout route), or Chid's trust |
| **Cleanse** | remove slurry: the item loses its slurried property and anything it gained or lost by it, and gets a little of its heat back (+2) | 1 moonpetal |

Chid's lines over a consecrated item are where the gentle Act 1 hints about
him live ("Nobody's made one of these in... well. Ages.") (`STORY_BIBLE.md` §6).

## 7. Steeping in slurry (the one gamble)

The Dig cooks ember into slurry, and slurry is the Morrow's pain, cooked.
Steeping an item in it is PoE's Vaal orb, told in this world: a gamble the
item cannot be taken back from (except by Chid), offered by Snib (Act 1, if
the Dig still runs and you have paid him; Act 3 at his bodgery).

One jar; the item comes out **slurried** (green-black veins, a sickly glow at
night), and one of:

| Result | Chance |
|---|---|
| One affix rises a grade, past the ilvl cap (to bright, if it was VI) | 25% |
| A slurry affix is added past the four-affix limit: a strong bonus with a price ("+20% damage; you mend 15% less") | 25% |
| A Named item's every range rerolled, bright twice as likely | 20% (Named only; otherwise re-drawn) |
| Nothing changes, except the veins | 20% |
| One affix falls a grade | 10% |

A slurried item: cannot be tempered, honed, reforged or pressed; can still be
notched and tailored; its heat goes to 0. The tooltip says all of this before
the jar is opened, in Snib's words ("It's the good stuff. Mostly.").

## 8. Notches and sigils

`SYSTEM.md` §10. Sigil-stones go into notches by hand, anywhere safe; taking
one out costs it (it shatters) unless Brannoc draws it (1 scrap, heat 1).
Watchwords form the moment the last sigil goes in, in the right order, in a
Plain or Fine base with exactly that many notches. Watchword recipes are found
in the world (`CATALOGUE.md` §8 says where), and the journal keeps them.

## 9. The tailor (Rav)

Rav "sews a fair seam" (a hint, in `redcowl.birds`, that he is the little bird:
the tailor's trade puts that hint in the player's hands every time they visit,
and never says it). Services:
- **Glamour**: wear the look of any item ever owned of the same slot and
  weight-class or lighter (`VISUALS.md` §7). Gold.
- **Dye**: cloth and trim colours from the dyes the survivor has bought from
  Harlan or found (`looks.json` cloak dyes, extended to all cloth). Gold.
- **Unpick**: undo a glamour. Free.
- Everything stays reversible and free of heat: looks never cost power.

## 10. The economy: gold and sinks

The game balances for self-found play: gold never buys power directly. Gold in
comes from arenas (`Battle.GoldGained`, banked as it falls), bounties, quests
and selling. Gold out:

| Sink | Scale | Share of a typical week's gold (target) |
|---|---|---|
| Crafting fees (Brannoc, Vonnra's press) | per craft, by grade and tier | 35% |
| The toll lots | 40 × ilvl a lot | 25% (open-ended) |
| Stash tabs at the Last Lamp | 500, 1,500, 4,000, 10,000 | one-off |
| The tailor and dyes | small | 5% |
| Rest, draughts, bandages, bribes, the story's prices (Sella, Snib, Redcowl) | as now | 25% |
| Commissions | materials + 60 × tier | 10% |

Target: a survivor who crafts and gambles freely runs out of gold around the
time they run out of good things to do with it; one who saves can afford a
stash tab or a lot every few nights. The balance lab should tune purse sizes
to these shares, not the other way round.

## 11. Crafting and the story, in one place

| Person | Craft | Opens | Can be lost when |
|---|---|---|---|
| Brannoc | temper, hone, reforge, add, rework, notch, commission, name | from day 1 | `nell.told` = lie (Act 2) |
| Wenna | tinctures | the stream cured or her samples analysed | she dies in the breakthrough (Act 2) |
| Vonnra | the book, sigils, lots, fortune | from day 1 | Act 3, if she dies at the bottom; the book passes to the survivor (the last binder's pages, a quiet ending note) |
| Chid | consecrate, bless, cleanse | the shrine visited | ending A or B; never mid-game |
| Rav | tailor, cart lots, fence | from day 1 | he takes the red hat (Act 2): the tailor moves to the Roost |
| Snib | steep; Brannoc's work if Brannoc is lost | the Dig met | never (Snib survives everything) |
| The Vigil quartermaster | argent bases | Silverstair (Act 2) | Keegan dead or disgraced |

When a crafter is lost, the service moves to someone else with a worse deal
or a stranger manner, never vanishes: the story should cost the survivor
something, not lock them out of a system.
