from ed import sub

sub("logic/Play/Zones/MapRun.cs", [
("""    /// <summary>The people's material, as a day's kill drops it; a champion or keeper more.</summary>
    static string? Material(Enemy e) => e.Def.Family switch
    {
        Family.Wolf => "wolf_pelt", Family.Boar => "boar_hide", Family.Kerchief => "kerchief_cloth",
        Family.Lampling => "ember_shard", Family.Undead => "bone_dust", _ => null,
    };

    IEnumerable<Loot> OnLoot(Enemy e)
    {
        var o = new List<Loot>();
        double q = Chart.Quantity;
        if (Material(e) is { } m)
        {
            int n = e == boss ? 5 : carriers.ContainsKey(e.Id) ? 2 : R() < 0.25 * q ? 1 : 0;
            if (n > 0) o.Add(new Loot(PickupKind.Material, m, n));
        }""",
"""    /// <summary>The people's material, as their carriers leave it. In the atlas the Dig's lamplings carry
    /// its picks and nails, old iron: their ember shards are the night's (docs/CRAFTING_DESIGN.md 20.1,
    /// fire is the scars' and iron the atlas's; a lamplings' map paid 73 shards, a long scar's worth).</summary>
    static string? Material(Enemy e) => e.Def.Family switch
    {
        Family.Wolf => "wolf_pelt", Family.Boar => "boar_hide", Family.Kerchief => "kerchief_cloth",
        Family.Lampling => Crafting.Iron, Family.Undead => "bone_dust", _ => null,
    };

    IEnumerable<Loot> OnLoot(Enemy e)
    {
        var o = new List<Loot>();
        double q = Chart.Quantity;
        // From what visibly carries it (crafting's measure, design 20.7): the ruler three, a keeper two, a
        // pack's leader one, the rank and file none, more under the chart's quantity. A quarter of every
        // kill paid 75-100 a map, where a night pays at most eight of a kind and a pin takes two.
        if (Material(e) is { } m)
        {
            int n = (int)Math.Floor((e == boss ? 3 : carriers.TryGetValue(e.Id, out int g) ? g >= 3 ? 2 : 1 : 0) * q + (e == boss || carriers.ContainsKey(e.Id) ? R() : 0));
            if (n > 0) o.Add(new Loot(PickupKind.Material, m, n));
        }"""),
])
sub("balance/Harness/MapSim.cs", [
("""        r.Charts = j.Ch.Pack.Count(i => i?.Chart != null);""",
"""        r.Charts = j.Ch.Pack.Count(i => i?.Chart != null) + j.Ch.Satchel.Count(i => i.Chart != null);"""),
])
