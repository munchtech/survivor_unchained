import sys, json, re, os
root = sys.argv[1]

p = root + '/data/content/items.json'
d = json.loads(open(p, encoding='utf-8').read())
it = d['items']

# The story lead's words, verbatim (WRITING_PASS §25).
fm = it.pop('forty_one_mouths')
fm['id'] = 'nans_cleaver'
fm['name'] = "Nan's Cleaver"
fm['lore'] = "Firepot Nan's, from the Roost's kitchen. It has jointed everything the road brought in, and the road brought in a great deal. She will want it back."
it['nans_cleaver'] = fm
it['levy_colours']['name'] = "Levy Colours"
it['drowned_coat']['lore'] = "Wrung out, it is wet again by morning. Whoever wore it last went into the ford in it, and did not come out."
it['corrans_sword']['lore'] = "Notched along the spine in tens, the way a man counts nights on a post nobody relieves. The Watch's book has him down as a deserter."
it['ditchwater']['lore'] = "Pulled out of the ditch on the Low Ford road, wound and loaded, with weed in the stock. Whoever loaded it never got to fire it."
it['fever_year_staff']['lore'] = "Charred to the grip. In the fever year they burned the bedding of the dead, and somebody stirred the fire with this until it was done."
it['slurry_wheel']['lore'] = "A spare wheel off the Dig's pump, beaten flat and strapped for an arm. It still weeps green."
it['kells_lamp']['lore'] = "It came back up the shaft on its own, still lit. Kell did not."
it['pelt_of_the_pack']['lore'] = "Grey to the roots, and stitched from more than one wolf. Maeca could tell you whose, and won't."
it['watch_coif']['lore'] = "Oiled, and hung on its peg. The man whose peg it was is not coming back for it."
it['watch_hauberk']['lore'] = "Mended at the shoulder where a blade went in, more than once, by someone who could not sew."
o = json.dumps(d, indent=1, ensure_ascii=False) + '\n'
o = o.replace('"tags": [\n    "mark"\n   ]', '"tags": ["mark"]')
open(p, 'w', encoding='utf-8', newline='\n').write(o)

def patch(path, pairs):
    q = root + '/' + path
    s = open(q, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (path, old[:100])
        s = s.replace(old, new)
    open(q, 'w', encoding='utf-8').write(s)

patch('data/content/loot.json', [
('"lore": "Eleven men, a year unpaid, and every one of them still oils his mail.",',
 '"lore": "Eleven men on a wall built for sixty, and every one of them still oils his mail.",'),
])
patch('tests/LootTests.cs', [('"forty_one_mouths"', '"nans_cleaver"'), ("Forty-One Mouths' price", "Nan's Cleaver's price")])
patch('logic/Rpg/Loot.cs', [
("""    public const string Iron = "old_iron";""",
"""    public const string Iron = "old_iron";

    /// <summary>The story lead's words (WRITING_PASS §25): the HUD's line when a Legendary falls, the
    /// debt's label, and its line when it pays.</summary>
    public const string NamedFalls = "This one has a name.", DebtLabel = "What the dark owes you", DebtPaid = "The dark settles up.";"""),
])
patch('logic/Play/JourneyLoot.cs', [
("""        if (x.Allows == null) x.Allows = c => Rules.Test(c, Ctx);
        // Its landing heard from the tier the survivor chose (the jackpots always).
        return Rpg.Drops.AsLoot(Rpg.Drops.Roll(x), Judge).Select(l => l with { Quiet = l.Tier is int t && !Ch.Filter.Heard((LootTier)t) }).ToList();""",
"""        if (x.Allows == null) x.Allows = c => Rules.Test(c, Ctx);
        bool owed = World.LootDebt >= Rpg.Drops.Rules.Debt;
        var rolled = Rpg.Drops.Roll(x);
        // A Legendary falling is said under the HUD, once (docs/design/LOOT_DESIGN.md §8.2); the debt's
        // paying is said in its own words.
        if (rolled.Any(r => r.Tier is LootTier.Legendary or LootTier.Storied))
            OnAnnounce(new Announcement(owed ? Rpg.Drops.DebtPaid : Rpg.Drops.NamedFalls, "", "reward", 3.2));
        // Its landing heard from the tier the survivor chose (the jackpots always).
        return Rpg.Drops.AsLoot(rolled, Judge).Select(l => l with { Quiet = l.Tier is int t && !Ch.Filter.Heard((LootTier)t) }).ToList();"""),
])
print("ok")
