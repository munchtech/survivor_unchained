from ed import sub

sub("balance/Harness/MapSim.cs", [
("""    public int Falls, Kills, Packs, PacksCleared, Quaffs, Items, Charts, Gold;""",
"""    public int Falls, Kills, Packs, PacksCleared, Quaffs, Items, Charts, Gold;
    /// <summary>What crafting reads (docs/CRAFTING_DESIGN.md 20.1): the people's own material and the
    /// ember shards picked up, the old iron the gear would break down to, and the rulers' Marks.</summary>
    public int Material, Shards, Iron, Marks;"""),
("""        int gear = 0;
        b.Hooks.OnPickup = pk =>
        {
            if (zh.OnPickup != null && !zh.OnPickup(pk)) return false;
            if (pk.Kind == PickupKind.Item && pk.Ref != null && Charts.FromRef(pk.Ref) == null) { gear++; return true; }""",
"""        int gear = 0, iron = 0, marks = 0;
        b.Hooks.OnPickup = pk =>
        {
            if (zh.OnPickup != null && !zh.OnPickup(pk)) return false;
            if (pk.Kind == PickupKind.Item && pk.Ref != null && Crafting.MarkOf(pk.Ref) != null) { marks++; return true; }
            if (pk.Kind == PickupKind.Item && pk.Ref != null && Charts.FromRef(pk.Ref) == null)
            {
                gear++;
                int rarity = pk.Payload is ItemInstance it ? it.Rarity : (int)pk.Tier;
                iron += Crafting.Rules.BreakDown[Math.Clamp(rarity, 0, Crafting.Rules.BreakDown.Count - 1)];
                return true;
            }"""),
("""        r.Gold = (int)j.Ch.Gold;
        return r;""",
"""        r.Gold = (int)j.Ch.Gold;
        r.Shards = j.Ch.Materials.GetValueOrDefault(Crafting.Shard);
        r.Iron = iron + j.Ch.Materials.GetValueOrDefault(Crafting.Iron);
        r.Material = j.Ch.Materials.Where(m => m.Key != Crafting.Shard && m.Key != Crafting.Iron).Sum(m => m.Value);
        r.Marks = marks;
        return r;"""),
("""        sb.AppendLine("| group | runs | cleared | closed | falls/run | minutes | boss TTK (s) | kill gap (s) | pack gap (s) | lowest | items | charts | gold |");
        sb.AppendLine("|---|---|---|---|---|---|---|---|---|---|---|---|---|");""",
"""        sb.AppendLine("| group | runs | cleared | closed | falls/run | minutes | boss TTK (s) | kill gap (s) | pack gap (s) | lowest | items | charts | gold | material | shards | iron | marks |");
        sb.AppendLine("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|");"""),
("""{M(l.Select(x => (double)x.Charts)):0} | {M(l.Select(x => (double)x.Gold)):0} |");""",
"""{M(l.Select(x => (double)x.Charts)):0} | {M(l.Select(x => (double)x.Gold)):0} | {M(l.Select(x => (double)x.Material)):0} | {M(l.Select(x => (double)x.Shards)):0} | {M(l.Select(x => (double)x.Iron)):0} | {l.Average(x => x.Marks):0.0} |");"""),
])
