from ed import sub

sub("logic/Rpg/Crafting.cs", [
("""    /// <summary>Ember shards for the ember reached, the tier, the minutes stayed past the half
    /// hour and a story fight won; the people's own for their champions slain. A fall keeps half.</summary>
    /// <summary>What a night among a people can leave in the fist (Night's materials), in the
    /// order a table says them: ember shards, then the people's own.</summary>
    public static List<string> NightMaterials(string people) =>
        new[] { Shard }.Concat((Rules.Night.Peoples.GetValueOrDefault(people) ?? new()).Select(p => p.Material)).Distinct().ToList();

    public static NightYield Night(""",
"""    /// <summary>What a night among a people can leave in the fist (Night's materials), in the
    /// order a table says them: ember shards, then the people's own.</summary>
    public static List<string> NightMaterials(string people) =>
        new[] { Shard }.Concat((Rules.Night.Peoples.GetValueOrDefault(people) ?? new()).Select(p => p.Material)).Distinct().ToList();

    /// <summary>Ember shards for the ember reached, the tier, the minutes stayed past the half
    /// hour and a story fight won; the people's own for their champions slain. A fall keeps half.</summary>
    public static NightYield Night("""),
])
