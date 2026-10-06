W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Sim/Battle.cs": [
        ("""    public Enemy? NearestHostile(double x, double z, double r, Func<Enemy, bool>? filter = null)
    {""", """    /// <summary>The farthest the survivor's side can hurt within r.</summary>
    public Enemy? FarthestHostile(double x, double z, double r)
    {
        Enemy? best = null;
        double bd = -1;
        Spatial.Query(x, z, r, q);
        foreach (var id in q)
        {
            var e = Enemies.Items[id];
            if (!Targetable(e)) continue;
            double d = (e.X - x) * (e.X - x) + (e.Z - z) * (e.Z - z);
            if (d <= r * r && d > bd) { bd = d; best = e; }
        }
        return best;
    }

    public Enemy? NearestHostile(double x, double z, double r, Func<Enemy, bool>? filter = null)
    {"""),
    ],
    W + "logic/Rpg/Character.cs": [
        ("""    public List<string> Facets = new();
    public HashSet<string> GearIds = new();""", """    public List<string> Facets = new();
    /// <summary>The Marks the gear carries (docs/items/CATALOGUE.md §4), each at its strength 0-1, and
    /// numbers on single skills, by skill id: worn in the Wayfinder's maps (Battle.Wear). Crafting
    /// fills them from the items.</summary>
    public Dictionary<string, double> Marks = new();
    public Dictionary<string, WeaponMods> SkillMods = new();
    public HashSet<string> GearIds = new();"""),
    ],
    W + "logic/Play/Zones/MapRun.cs": [
        ("""        b.Rules = Chart.Rules();
        b.InBounds = map.CanStand;""", """        b.Rules = Chart.Rules();
        b.InBounds = map.CanStand;
        // What the gear inscribes works here, and only here (the scars' kit carries coals).
        var kit = Character.Kit(G.Journey.Ch);
        b.Wear(kit.Marks, kit.SkillMods);"""),
    ],
}
