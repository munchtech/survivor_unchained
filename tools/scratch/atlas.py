import sys
root = sys.argv[1]

def patch(path, pairs):
    q = root + '/' + path
    s = open(q, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (path, old[:100])
        s = s.replace(old, new, 1)
    open(q, 'w', encoding='utf-8').write(s)

# 2. What went to Rook's storeroom is still what the map paid (crafting: the pack fills on a map).
patch('godot/logic/Maps/MapSpoils.cs', [
("""public sealed record MapSpoils(List<ItemInstance> Gear, List<ItemInstance> Charts, Dictionary<string, int> Materials, double Gold)
{
    public static MapSpoils Between(CharacterData before, CharacterData after)
    {
        var had = Carried(before).Select(i => i.Uid).ToHashSet();
        var found = Carried(after).Where(i => !had.Contains(i.Uid)).ToList();""",
"""public sealed record MapSpoils(List<ItemInstance> Gear, List<ItemInstance> Charts, Dictionary<string, int> Materials, double Gold)
{
    /// <summary>The finds that went to Rook's storeroom (the pack was full at the map's end: Journey.Gather),
    /// by uid: the page says where they are.</summary>
    public HashSet<string> Stored { get; init; } = new();

    /// <param name="stashBefore">Rook's storeroom as the map opened, and as it ended: what the
    /// gathering sent there is the map's pay too.</param>
    public static MapSpoils Between(CharacterData before, CharacterData after, IEnumerable<ItemInstance?>? stashBefore = null, IEnumerable<ItemInstance?>? stashAfter = null)
    {
        var had = Carried(before).Select(i => i.Uid).Concat((stashBefore ?? Enumerable.Empty<ItemInstance?>()).Where(i => i != null).Select(i => i!.Uid)).ToHashSet();
        var stored = (stashAfter ?? Enumerable.Empty<ItemInstance?>()).Where(i => i != null && !had.Contains(i.Uid)).Select(i => i!).ToList();
        var found = Carried(after).Where(i => !had.Contains(i.Uid)).Concat(stored).ToList();"""),
("""        return new(gear, charts, materials, Math.Max(0, after.Gold - before.Gold));
    }""",
"""        return new(gear, charts, materials, Math.Max(0, after.Gold - before.Gold)) { Stored = stored.Select(i => i.Uid).ToHashSet() };
    }"""),
])

patch('godot/src/Game/Game.cs', [
("""    CharacterData? mapStart;""",
"""    CharacterData? mapStart;
    List<ItemInstance?>? mapStash;"""),
("""        mapStart = SurvivorUnchained.Core.Json.Clone(Journey.Ch);
        return new MapRun(this, currentMap!, World.Map!);""",
"""        mapStart = SurvivorUnchained.Core.Json.Clone(Journey.Ch);
        mapStash = World.Stash.ToList();
        return new MapRun(this, currentMap!, World.Map!);"""),
("""        var spoils = SurvivorUnchained.Maps.MapSpoils.Between(mapStart ?? Journey.Ch, Journey.Ch);""",
"""        var spoils = SurvivorUnchained.Maps.MapSpoils.Between(mapStart ?? Journey.Ch, Journey.Ch, mapStash ?? World.Stash, World.Stash);"""),
])

patch('godot/tests/MapSpoilsTests.cs', [
("""        // What she walked in with is not what the map paid.
        Assert.Empty(MapSpoils.Between(after, after).Gear);""",
"""        // What she walked in with is not what the map paid.
        Assert.Empty(MapSpoils.Between(after, after).Gear);
        // What the end of the map sent to Rook's storeroom is still its pay, and the page knows where it went.
        var shelf = new List<ItemInstance?> { null, null };
        var sent = Inventory.Make(after, "chain_shirt", rarity: 3);
        var later = new List<ItemInstance?> { sent, null };
        var t = MapSpoils.Between(before, after, shelf, later);
        Assert.Contains(t.Gear, g => g.Uid == sent.Uid);
        Assert.Contains(sent.Uid, t.Stored);
        Assert.Empty(MapSpoils.Between(after, after, later, later).Gear);"""),
])

# 3. Fire is the scars', iron the atlas's (crafting design 20.1): a map's lampling carrier leaves iron.
patch('godot/logic/Rpg/Loot.cs', [
("""        string? material = x.People != null ? PeopleMaterial(x.People) : null;""",
"""        string? material = x.People != null ? PeopleMaterial(x.People) : null;
        // Fire is the scars', iron the atlas's (crafting design 20.1): in a map the lamplings leave iron.
        if (material == "ember_shard" && x.Source is DropSource.MapPack or DropSource.MapPackFine or DropSource.MapKeeper or DropSource.MapRuler or DropSource.Strongbox)
            material = Iron;"""),
])
patch('godot/tests/LootTests.cs', [
("""        // In a map they are the ground's.""",
"""        // Fire is the scars': a map's lamplings leave iron, never shards.
        Assert.DoesNotContain(Enumerable.Range(0, 300).SelectMany(s => Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.MapPack, Level = 10, People = "lamplings", R = Seq(s) })),
            d => d.Material == "ember_shard");
        // In a map they are the ground's."""),
])
print("ok")
