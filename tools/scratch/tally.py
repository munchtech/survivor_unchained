import sys
root = sys.argv[1]

def patch(path, pairs):
    q = root + '/' + path
    s = open(q, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (path, old[:100])
        s = s.replace(old, new)
    open(q, 'w', encoding='utf-8').write(s)

patch('logic/Rpg/Loot.cs', [
("""    /// <summary>A carrier that drops no gear: its people's material, and old iron this often.</summary>
    public int Material = 1;
    public double Iron = 0.5;""",
"""    /// <summary>A carrier roll that is not gear: its people's material this often, old iron this often
    /// (crafting's measured rates: more left Act 1's stores piled high and meaningless).</summary>
    public double Material = 0.1, Iron = 0.2;"""),
("""    /// <summary>The scars: minutes past the half hour.</summary>""",
"""    /// <summary>In the night's arenas the materials go to the night's end tally, not the ground
    /// (crafting decision 7: no confetti, the tally is the moment).</summary>
    public bool Tally;
    /// <summary>The scars: minutes past the half hour.</summary>"""),
("""                if (material != null) o.Add(new Dropped(null, material, Rules.Material, LootTier.Material));
                if (R() < Rules.Iron) o.Add(new Dropped(null, Iron, 1, LootTier.Material));""",
"""                if (material != null && R() < Rules.Material) o.Add(new Dropped(null, material, 1, LootTier.Material));
                if (R() < Rules.Iron) o.Add(new Dropped(null, Iron, 1, LootTier.Material));"""),
])

patch('data/content/loot.json', [
("""  "_material": "A carrier that drops no gear: its people's material, and old iron half the time (crafting's ask, to keep the forge's economy as measured).",
  "material": 1, "iron": 0.5,""",
"""  "_material": "A carrier roll that is not gear: its people's material this often, old iron this often (crafting's CraftingEconomy: these leave Act 1's stores about where they were before fewer drops). In the night's arenas they go to the night's end tally.",
  "material": 0.1, "iron": 0.2,"""),
("""    "miniboss": { "chance": 1, "rolls": 1, "floor": 1, "quality": 1.5, "materials": 1 },
    "herald": { "chance": 1, "rolls": 1, "floor": 1, "quality": 1.5, "materials": 1 },
    "boss": { "chance": 1, "rolls": 2, "deep": 1, "floor": 2, "quality": 2, "legendary": 4, "materials": 2 },""",
"""    "miniboss": { "chance": 1, "rolls": 1, "floor": 1, "quality": 1.5 },
    "herald": { "chance": 1, "rolls": 1, "floor": 1, "quality": 1.5 },
    "boss": { "chance": 1, "rolls": 2, "deep": 1, "floor": 2, "quality": 2, "legendary": 4, "materials": 1 },"""),
])

patch('logic/Play/JourneyLoot.cs', [
("""        // Its landing heard from the tier the survivor chose (the jackpots always).
        return Rpg.Drops.AsLoot(rolled, Judge).Select(l => l with { Quiet = l.Tier is int t && !Ch.Filter.Heard((LootTier)t) }).ToList();
    }""",
"""        // In the night's arenas the materials are the night's end tally, not the ground's (crafting decision 7).
        if (x.Tally)
        {
            foreach (var r in rolled.Where(r => r.Material != null)) NightTally[r.Material!] = NightTally.GetValueOrDefault(r.Material!) + r.Qty;
            rolled = rolled.Where(r => r.Material == null).ToList();
        }
        // Its landing heard from the tier the survivor chose (the jackpots always).
        return Rpg.Drops.AsLoot(rolled, Judge).Select(l => l with { Quiet = l.Tier is int t && !Ch.Filter.Heard((LootTier)t) }).ToList();
    }

    /// <summary>The materials the night's carriers left in place of gear, paid at its end with the rest
    /// of the night's yield (and half spilled on a fall).</summary>
    public Dictionary<string, int> NightTally { get; } = new();"""),
])

patch('logic/Arena/Arena.cs', [
("""        var carry = Crafting.Night(spec.People, spec.Tier, spec.Story, b.EmberLevel, Math.Max(0, b.Time / 60 - spec.Minutes), won, fell, b.ChampionsByFamily);""",
"""        var carry = Crafting.Night(spec.People, spec.Tier, spec.Story, b.EmberLevel, Math.Max(0, b.Time / 60 - spec.Minutes), won, fell, b.ChampionsByFamily);
        // What the carriers left in place of gear joins the tally, spilled as the rest is (LOOT_DESIGN §5).
        foreach (var (m, n) in j.NightTally)
        {
            int kept = fell ? n / 2 : n;
            if (kept > 0) carry.Kept[m] = carry.Kept.GetValueOrDefault(m) + kept;
            if (n - kept > 0) carry.Spilled[m] = carry.Spilled.GetValueOrDefault(m) + n - kept;
        }
        j.NightTally.Clear();"""),
])

for zone in ['logic/Play/Zones/ArenaRun.cs', 'logic/Play/Zones/StoryNight.cs']:
    patch(zone, [("StoryBoss = ", "Tally = true, StoryBoss = ")])

patch('tests/LootTests.cs', [
("""            // The people's material always comes with a miniboss.
            Assert.Contains(mb, d => d.Material == "wolf_pelt");
""", ""),
("""    public void A_champion_that_drops_no_gear_drops_its_peoples_material_and_sometimes_iron()
    {
        var j = Begin();
        int gear = 0, mat = 0, iron = 0, n = 2000;
        for (int s = 0; s < n; s++)
        {
            var d = Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Champion, Level = 6, People = "dead", R = Seq(s) });
            if (d.Any(x => x.Item != null)) gear++;
            else
            {
                Assert.Contains(d, x => x.Material == "bone_dust" && x.Qty == 1);
                mat++;
                if (d.Any(x => x.Material == Drops.Iron)) iron++;
            }
        }
        Assert.InRange(gear / (double)n, 0.40, 0.50);
        Assert.InRange(iron / (double)mat, 0.42, 0.58);
    }""",
"""    public void A_champion_that_drops_no_gear_now_and_then_drops_its_peoples_material_or_iron()
    {
        var j = Begin();
        int gear = 0, none = 0, dust = 0, iron = 0, n = 4000;
        for (int s = 0; s < n; s++)
        {
            var d = Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Champion, Level = 6, People = "dead", R = Seq(s) });
            if (d.Any(x => x.Item != null)) { gear++; continue; }
            none++;
            if (d.Any(x => x.Material == "bone_dust")) dust++;
            if (d.Any(x => x.Material == Drops.Iron)) iron++;
        }
        // Crafting's measured rates: a tenth the people's material, a fifth old iron.
        Assert.InRange(gear / (double)n, 0.40, 0.50);
        Assert.InRange(dust / (double)none, 0.07, 0.13);
        Assert.InRange(iron / (double)none, 0.16, 0.24);
    }

    [Fact]
    public void In_a_nights_arena_the_materials_wait_for_the_nights_end_and_a_fall_spills_half()
    {
        var j = Begin();
        int pickups = 0;
        for (int s = 0; s < 300; s++)
            pickups += j.Drops(new DropCtx { Source = DropSource.Champion, Level = 4, People = "pack", Tally = true, R = Seq(s) }).Count(l => l.Kind == PickupKind.Material);
        Assert.Equal(0, pickups);
        int tallied = j.NightTally.Values.Sum();
        Assert.True(tallied > 20);
        // In a map they are the ground's.
        int ground = Enumerable.Range(0, 300).Sum(s => j.Drops(new DropCtx { Source = DropSource.MapPack, Level = 10, People = "pack", R = Seq(s) }).Count(l => l.Kind == PickupKind.Material));
        Assert.True(ground > 20);
    }"""),
])
print("ok")
