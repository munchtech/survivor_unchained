import json, sys
p = sys.argv[1]
d = json.loads(open(p, encoding='utf-8').read())
items = d['items']

def M(stat, kind, value, when=None):
    m = {"stat": stat, "kind": kind, "value": value, "source": "item"}
    if when: m["when"] = when
    return m

# Every base has two implicits that scale with its make (docs/design/LOOT_DESIGN.md §10.3).
items['leather_cap']['mods'] = [M("armor", "flat", 1), M("maxHealth", "flat", 8)]
items['iron_helm']['mods'] = [M("armor", "flat", 3), M("maxHealth", "flat", 4), M("moveSpeed", "inc", -0.02)]
items['chain_shirt']['mods'] = [M("armor", "flat", 5), M("maxHealth", "flat", 6), M("moveSpeed", "inc", -0.04)]
items['travelers_cloak']['mods'] = [M("moveSpeed", "inc", 0.03), M("armor", "flat", 1)]
items['copper_ring']['mods'] = [M("critChance", "flat", 0.015)]
items['silver_ring']['mods'] = [M("vs.undead", "flat", 0.06)]
items['silver_ring']['description'] = "Bright, and a little cold. The dead do not like it."
items['bone_amulet']['mods'] = [M("maxHealth", "flat", 6), M("regen", "flat", 0.2)]

def legend(id, **k):
    e = {"id": id}
    e.update(k)
    items[id] = e

legend("drowned_coat", name="The Drowned Coat", kind="body", rarity=4, icon="armor_light", value=320, of="padded_jerkin", dropsFrom=1, homes=["dead"],
       description="Your dash leaves black water for 3 s that slows what wades in it by 40%. +30% fire resistance.",
       mods=[M("resist.fire", "flat", 0.3), M("healing", "inc", -0.15)],
       triggers=[{"on": "dash", "icd": 0.5, "effects": [{"do": "zone", "radius": 1.8, "duration": 3, "dps": 2, "basis": "flat", "school": "frost", "art": "zone_drowned", "slow": 0.4}],
                  "text": "Your dash leaves black water that slows"}],
       downside="You mend 15% less. It is always cold.",
       lore="It has hung by Rook's fire for a week and it is still wet.")

legend("forty_one_mouths", name="Forty-One Mouths", kind="weapon", rarity=4, icon="cleaver", value=320, of="butchers_cleaver", dropsFrom=2, homes=["kerchiefs"],
       weapon={"id": "cleaver", "rank": 1},
       description="Below half health, every kill mends 2% of your health. Your blows bleed.",
       mods=[M("damage", "inc", -0.15, "fullHealth")],
       triggers=[{"on": "kill", "icd": 0.1, "when": {"selfHpBelow": 0.5}, "effects": [{"do": "heal", "amount": 0.02, "basis": "maxhp"}], "text": "Below half health, kills mend you"},
                 {"on": "hit", "chance": 0.15, "effects": [{"do": "status", "target": "hit", "status": {"kind": "bleed", "chance": 1, "power": 0.35, "duration": 3}}]}],
       statuses=["bleed"],
       downside="At full health you deal 15% less.",
       lore="The Roost's cleaver. It fed forty-one mouths on whatever the road brought in, and the road brought in a great deal.")

legend("corrans_sword", name="Corran's Sword", kind="weapon", rarity=4, icon="sword", value=320, of="worn_oathblade", dropsFrom=3, homes=["dead"],
       weapon={"id": "oathblade", "rank": 1},
       description="Standing still, your weapons strike 25% faster, and a blow that lands sends a ring of steel round you, once a second.",
       mods=[M("cooldown", "more", -0.25, "still"), M("moveSpeed", "inc", -0.08)],
       triggers=[{"on": "hit", "icd": 1, "when": {"moving": False}, "effects": [{"do": "nova", "radius": 2.6, "damage": 0.5, "basis": "hit", "school": "physical"}],
                  "text": "Standing still, a blow that lands rings steel round you"}],
       tags=["corrans_sword"],
       downside="8% slower.",
       lore="Notched along the spine, in tens, where somebody kept count of something. The book wrote him down as a deserter.")

legend("ditchwater", name="Ditchwater", kind="weapon", rarity=4, icon="bow", value=320, of="hunting_bow", dropsFrom=3, homes=["dead"],
       weapon={"id": "volley", "rank": 1},
       description="Volley's bolts pierce one more and chill what they pass through.",
       mods=[M("pierce", "flat", 1)],
       triggers=[{"on": "hit", "when": {"weapon": "volley"}, "effects": [{"do": "status", "target": "hit", "status": {"kind": "chill", "chance": 1, "power": 0.3, "duration": 2}}],
                  "text": "Volley's bolts chill"}],
       statuses=["chill"],
       lore="Pulled out of the ditch on the Low Ford road, wound and loaded. Whoever loaded it never fired it.")

legend("fever_year_staff", name="The Fever-Year Staff", kind="weapon", rarity=4, icon="staff", value=340, of="ember_staff", dropsFrom=6, homes=["dead"],
       weapon={"id": "cinderfall", "rank": 1},
       description="Cinderfall poisons as it burns. What dies poisoned passes the poison to three near it.",
       mods=[M("healing", "inc", -0.1)],
       triggers=[{"on": "hit", "when": {"weapon": "cinderfall"}, "effects": [{"do": "status", "target": "hit", "status": {"kind": "poison", "chance": 1, "power": 0.4, "duration": 4}}],
                  "text": "Cinderfall poisons"},
                 {"on": "kill", "when": {"targetStatus": "poison"}, "effects": [{"do": "spread", "kind": "poison", "radius": 3, "count": 3}],
                  "text": "The poisoned pass it on"}],
       statuses=["poison"],
       downside="You mend 10% less.",
       lore="Charred to the grip. In the fever year they burned the bedding of the dead, and somebody did it with this.")

legend("slurry_wheel", name="The Slurry Wheel", kind="offhand", rarity=4, icon="shield", value=340, of="watch_buckler", dropsFrom=6, homes=["lamplings"],
       description="Every block throws slurry round you: poison on everything within 3 m. You block more often.",
       mods=[M("block", "flat", 1), M("from.lampling", "flat", -0.15)],
       triggers=[{"on": "block", "effects": [{"do": "status", "target": "near", "radius": 3, "count": 12, "status": {"kind": "poison", "chance": 1, "power": 0.5, "duration": 3}}],
                  "text": "A block throws slurry round you"}],
       statuses=["poison"],
       downside="15% more damage from lamplings.",
       lore="A spare wheel off the Dig's pump, beaten flat and strapped for an arm. It still weeps.")

legend("kells_lamp", name="Kell's Lamp", kind="relic", rarity=4, icon="lamp", value=340, dropsFrom=8, homes=["lamplings"],
       description="Every two seconds your lamp flares: fire on everything within 3.5 m.",
       mods=[M("lightRadius", "inc", 0.2)],
       triggers=[{"on": "tick", "icd": 2, "effects": [{"do": "nova", "radius": 3.5, "damage": 14, "basis": "flat", "school": "fire"}], "text": "Your lamp flares every two seconds"}],
       lore="It came back up the shaft on its own, still lit. Nobody has asked it where Kell is.")

legend("pelt_of_the_pack", name="Pelt of the Pack", kind="cloak", rarity=4, icon="pelt", value=300, of="travelers_cloak", dropsFrom=4, homes=["pack"],
       dropsWhen={"fact": "beasts.outcome", "eq": "slaughtered"},
       description="Every wolf you kill in a fight gives you 2 health, to 80.",
       triggers=[{"on": "kill", "when": {"targetFamily": "wolf"}, "effects": [{"do": "buff", "id": "pack_pelt", "stat": "maxHealth", "value": 2, "kind": "flat", "duration": 100000, "maxStacks": 40}],
                  "text": "Wolves killed give you health"}],
       tags=["pack_pelt"],
       lore="Brannoc counted the pelts twice and did not say anything either time.")

# The Moonsilver Circlet stays as it is, the Moon Grove's and Vonnra's: it never falls by chance.

def piece(id, **k):
    e = {"id": id}
    e.update(k)
    items[id] = e

piece("watch_coif", name="Watch Coif", kind="head", rarity=3, set="watch_kit", icon="helm", value=160, of="iron_helm", dropsFrom=2, homes=["dead"],
      description="+12 health. The Watch's Kit.", mods=[M("maxHealth", "flat", 12)],
      lore="The mail is oiled. The man who oiled it is not coming back for it.")
piece("watch_hauberk", name="Watch Hauberk", kind="body", rarity=3, set="watch_kit", icon="armor", value=180, of="chain_shirt", dropsFrom=2, homes=["dead"],
      description="+3 armour. The Watch's Kit.", mods=[M("armor", "flat", 3)],
      lore="Stitched at the shoulder where a blade went in, by someone who could not sew, more than once.")
piece("watch_shield", name="The Watch's Torch-Shield", kind="offhand", rarity=3, set="watch_kit", icon="shield", value=170, of="watch_buckler", dropsFrom=2, homes=["dead"],
      description="+10% holy damage. The Watch's Kit.", mods=[M("damage.holy", "inc", 0.1)],
      lore="The torch is the Watch's. It was painted over once, and someone scraped it back.")
piece("roost_hood", name="Roost Hood", kind="head", rarity=3, set="levy_red", icon="helm_light", value=160, of="leather_cap", dropsFrom=5, homes=["kerchiefs"],
      description="+4% critical chance. The Levy Red.", mods=[M("critChance", "flat", 0.04)], tags=["kerchief_colors"],
      lore="Red, and faded where the rain gets it, and darned where the rest of the world does.")
piece("levy_colours", name="Ashford Levy Colours", kind="cloak", rarity=3, set="levy_red", icon="cloak", value=160, of="travelers_cloak", dropsFrom=5, homes=["kerchiefs"],
      description="+5% speed. The Levy Red.", mods=[M("moveSpeed", "inc", 0.05)],
      lore="A levy's cloak, cut down. The badge was unpicked. You can still see where it was.")
piece("kerchief_knives", name="Kerchief Knives", kind="weapon", rarity=3, set="levy_red", icon="dagger", value=180, of="knife_belt", dropsFrom=5, homes=["kerchiefs"],
      weapon={"id": "knifestorm", "rank": 1},
      description="Knifestorm. The Levy Red.", mods=[M("critDamage", "flat", 0.15)],
      lore="Forty-one mouths. These were the forks.")

o = json.dumps(d, indent=1, ensure_ascii=False) + '\n'
o = o.replace('"tags": [\n    "mark"\n   ]', '"tags": ["mark"]')
open(p, 'w', encoding='utf-8', newline='\n').write(o)
print("items", len(items))
