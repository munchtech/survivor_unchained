import sys
root = sys.argv[1]

def patch(path, pairs):
    q = root + '/' + path
    s = open(q, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (path, old[:100])
        s = s.replace(old, new, 1)
    open(q, 'w', encoding='utf-8').write(s)

patch('logic/Play/Journey.cs', [
("""    public Action<Announcement> OnAnnounce = _ => { };""",
"""    public Action<Announcement> OnAnnounce = _ => { };
    /// <summary>The first Legendary (or Storied) piece this world has ever seen taken, and where it lay:
    /// the experience director stages its moment on it (docs/design/LOOT_DESIGN.md §8.2).</summary>
    public Action<ItemInstance, double, double> FirstLegendaryTaken = (_, _, _) => { };"""),
("""        if (p.Payload is ItemInstance whole) return Take(whole);""",
"""        if (p.Payload is ItemInstance whole)
        {
            if (!Take(whole)) return false;
            if (!World.FirstLegendaryTaken && Rpg.Drops.TierOf(whole) is LootTier.Legendary or LootTier.Storied)
            {
                World.FirstLegendaryTaken = true;
                FirstLegendaryTaken(whole, p.X, p.Z);
            }
            return true;
        }"""),
])
patch('logic/World/State.cs', [
("""    /// <summary>A Legendary has fallen in this world: the first story boss's certain one is paid.</summary>
    public bool FirstLegendary;""",
"""    /// <summary>A Legendary has fallen in this world: the first story boss's certain one is paid.</summary>
    public bool FirstLegendary;
    /// <summary>A Legendary has been taken in this world: its first moment has been staged.</summary>
    public bool FirstLegendaryTaken;"""),
])
patch('tests/LootTests.cs', [
("""    [Fact]
    public void Gear_rolled_where_it_fell_is_taken_whole()""",
"""    [Fact]
    public void The_first_legendary_taken_is_told_once_with_where_it_lay()
    {
        var j = Begin();
        var told = new List<(string Def, double X, double Z)>();
        j.FirstLegendaryTaken = (it, x, z) => told.Add((it.Def, x, z));
        Assert.True(j.PickedUp(new Pickup(0) { Kind = PickupKind.Item, Ref = "iron_helm", Value = 1, X = 1, Z = 2, Payload = At("iron_helm", 3, 4) }));
        Assert.Empty(told);
        Assert.True(j.PickedUp(new Pickup(1) { Kind = PickupKind.Item, Ref = "drowned_coat", Value = 1, X = 3, Z = 4, Payload = Inventory.Make(null, "drowned_coat", level: 2) }));
        Assert.True(j.PickedUp(new Pickup(2) { Kind = PickupKind.Item, Ref = "kells_lamp", Value = 1, X = 5, Z = 6, Payload = Inventory.Make(null, "kells_lamp", level: 9) }));
        Assert.Equal(new[] { ("drowned_coat", 3.0, 4.0) }, told);
        Assert.True(j.World.FirstLegendaryTaken);
    }

    [Fact]
    public void Gear_rolled_where_it_fell_is_taken_whole()"""),
])

# Fewer beams: Common and Uncommon only their names (the experience director: six tubes after a fight read as clutter).
patch('src/Fx/BattleFx.cs', [
("""                            LootTier.Common => (0f, 1f, col),
                            LootTier.Uncommon => (0.8f, 1f, col),
                            LootTier.Rare => (2.5f, 1f, col),
                            LootTier.Epic => (5f * (1 + 0.08f * Mathf.Sin((float)now * 2.5f)), 1.2f, col),
                            LootTier.Set => (6f, 1.4f, SetColour),
                            LootTier.Legendary => (40f, 1.5f, Palette.Rarity[4]),
                            LootTier.Storied => (40f, 1.5f, Palette.Rarity[5]),
                            LootTier.Chart => (2f, 1f, new Color("#e8d8b0")),
                            LootTier.Quest => (1.5f, 1f, new Color("#ffd46a")),
                            LootTier.Book => (1.5f, 1f, col),""",
"""                            LootTier.Common or LootTier.Uncommon => (0f, 1f, col),
                            LootTier.Rare => (1.2f, 0.55f, col),
                            LootTier.Epic => (3f * (1 + 0.08f * Mathf.Sin((float)now * 2.5f)), 0.6f, col),
                            LootTier.Set => (4f, 0.6f, SetColour),
                            LootTier.Legendary => (40f, 0.9f, Palette.Rarity[4]),
                            LootTier.Storied => (40f, 0.9f, Palette.Rarity[5]),
                            LootTier.Chart => (1.2f, 0.55f, new Color("#e8d8b0")),
                            LootTier.Quest => (1.2f, 0.55f, new Color("#ffd46a")),
                            LootTier.Book => (1f, 0.55f, col),"""),
("""                        lootBeams.Add(new Transform3D(Godot.Basis.Identity.Scaled(new Vector3(0.7f, h * 0.9f, 0.7f)), V(p.X + Mathf.Cos(a) * 0.18f, gy + h * 0.45f, p.Z + Mathf.Sin(a) * 0.18f)), col);""",
"""                        lootBeams.Add(new Transform3D(Godot.Basis.Identity.Scaled(new Vector3(0.45f, h * 0.9f, 0.45f)), V(p.X + Mathf.Cos(a) * 0.14f, gy + h * 0.45f, p.Z + Mathf.Sin(a) * 0.14f)), col);"""),
])
print("ok")
