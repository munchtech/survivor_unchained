using System;
using System.Linq;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The town's people from Marionette packages (folk.json "packages"), and --folk-kit bringing the kit back.</summary>
[Collection("LoreKit")]
public class FolkPackageTests
{
    [Fact]
    public void Roles_get_their_package()
    {
        Lore.KitFolk = false;
        var pk = Lore.FolkPackages;
        Assert.NotNull(pk);
        var rng = new Random(3);
        var w = Folk.Person(FolkRole.Watch, Lore.WatchLook, rng);
        Assert.Equal("npc:npc_watch_m", w.Body);
        Assert.Equal(Sex.Male, w.Sex);
        var seen = Enumerable.Range(0, 60).Select(_ => Folk.Person(FolkRole.Adult, Lore.FolkLooks[0], rng)).ToList();
        Assert.All(seen, p => Assert.Equal(p.Sex == Sex.Female ? "npc:npc_folk_w" : "npc:npc_folk_m", p.Body));
        Assert.Contains(seen, p => p.Sex == Sex.Female);
        Assert.Contains(seen, p => p.Sex == Sex.Male);
        Assert.All(seen, p => { Assert.Null(p.Dye); Assert.Null(p.HairColor); Assert.Null(p.Outfit); });
    }

    [Fact]
    public void Named_people_have_package_bodies_and_kit_drops_them()
    {
        Lore.KitFolk = false;
        var all = Lore.Npcs.Values.Concat(Lore.Outsiders.Values).ToList();
        Assert.Equal(16, all.Count);
        Assert.All(all, d => Assert.StartsWith("npc:npc_", d.Person?.Body ?? ""));
        Assert.Equal("npc:npc_holloway", Lore.Npcs["holloway"].Person!.Body);   // (NPC 18: his own package)
        Assert.Null(Lore.Npcs["holloway"].Person!.Dye);   // (a named NPC keeps his own paint)
        Assert.Equal("npc:npc_brannoc", Lore.Npcs["brannoc"].Person!.Body);
        Assert.Null(Lore.Npcs["brannoc"].Person!.Dye);
        Lore.KitFolk = true;
        try
        {
            Assert.All(Lore.Npcs.Values.Concat(Lore.Outsiders.Values), d => Assert.Null(d.Person?.Body));
            var kit = Folk.Person(FolkRole.Adult, Lore.FolkLooks[0], new Random(1));
            Assert.Null(kit.Body);
            Assert.NotNull(kit.Outfit);
            Assert.False(Lore.PackageFolk);
        }
        finally { Lore.KitFolk = false; }
        Assert.StartsWith("npc:", Lore.Npcs["rook"].Person!.Body);
    }

    [Fact]
    public void No_children_in_package_mode()
    {
        Lore.KitFolk = false;
        Assert.True(Lore.PackageFolk);
        var src = System.IO.File.ReadAllText(System.IO.Path.Combine(AppContext.BaseDirectory, "../../../../logic/Play/Folk.cs"));
        Assert.Contains("plan.Children > 0 && !Lore.PackageFolk", src);
    }
}
