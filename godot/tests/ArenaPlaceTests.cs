using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Maps;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Each ember arena is its people's own place (Maps/ArenaPlaces.cs,
/// ArenaGen.cs), kept to the rules that let the fight read on it
/// (docs/team/arena_art.md) and to the story's (docs/STORY_BIBLE.md).</summary>
public class ArenaPlaceTests
{
    /// <summary>The edge's radius at a point's bearing.</summary>
    public static double Edge(MapBuild m, double x, double z)
    {
        double a = Math.Atan2(z, x);
        int k = (int)Math.Round((a < 0 ? a + Math.PI * 2 : a) / (Math.PI * 2) * m.Rim.Count) % m.Rim.Count;
        return MathX.Len(m.Rim[k].X, m.Rim[k].Z);
    }

    static Dictionary<string, float[]>? sizes;

    /// <summary>A KayKit piece's height as made (View/Pieces.cs), in metres; null
    /// for kits without sizes, and for what is thin (a post, a lamp on a pole,
    /// a standard): those hide nothing behind them.</summary>
    static double? Height(string id)
    {
        if (id is "halloween/post" or "halloween/post_lantern" || id.StartsWith("props/Banner")) return null;
        sizes ??= Json.Parse<Dictionary<string, float[]>>(DataFiles.Text("zones/kaykit.json"));
        if (!sizes.TryGetValue(id, out var s)) return null;
        // A broken wall is made to under half its authored height (Pieces.Wall's keep).
        double keep = id switch { "dungeon/wall_broken" => 0.45, "dungeon/wall_half" => 0.9, _ => 1 };
        return (s[4] - s[1]) * keep;
    }

    [Theory]
    [InlineData("dead", "barrow")]
    [InlineData("pack", "hollow")]
    [InlineData("kerchiefs", "ruts")]
    [InlineData("lamplings", "dig")]
    public void Each_people_holds_its_own_place(string people, string place)
    {
        var m = MapGen.Generate(new MapSpec { Seed = 21, Arena = true, People = people });
        Assert.NotNull(m.Place);
        Assert.Equal(place, m.Place!.Id);
        Assert.NotNull(m.Splat2);
        Assert.Equal(180, m.Rim.Count);
        Assert.Same(m.Place.Night, m.Meta.Atmosphere);
    }

    [Theory]
    [InlineData("dead", 4)]
    [InlineData("pack", 9)]
    [InlineData("kerchiefs", 17)]
    [InlineData("lamplings", 33)]
    public void Nothing_taller_than_a_person_stands_in_the_fight(string people, int seed)
    {
        // Landmarks and anything tall keep to the edge; inside, cover is low
        // enough that the fight shows round it from the arena's camera.
        var m = MapGen.Generate(new MapSpec { Seed = seed, Arena = true, People = people });
        var tall = m.Pieces.Where(p => Height(p.Id) is double h && h * p.Scale > 2.2 && MathX.Len(p.X, p.Z) < Edge(m, p.X, p.Z) - 12)
            .Select(p => $"{p.Id} ({Height(p.Id) * p.Scale:0.0} m) at {p.X:0},{p.Z:0}").ToList();
        Assert.Empty(tall);
        // Nor do whole trees: bare ones only, and those away from the middle.
        Assert.DoesNotContain(m.Flora, f => f.Kind is "pine" or "broadleaf" or "autumn" && MathX.Len(f.X, f.Z) < Edge(m, f.X, f.Z) - 14);
    }

    [Theory]
    [InlineData(1)]
    [InlineData(2)]
    [InlineData(3)]
    public void The_story_s_rules_hold_in_every_place(int seed)
    {
        // The sealed door is the Verge's alone; the Pack's bones are deer and boar,
        // never a man's; the Kerchiefs keep no gibbets of victims.
        var barrow = MapGen.Generate(new MapSpec { Seed = seed, Arena = true, People = "dead" });
        Assert.DoesNotContain(barrow.Pieces, p => p.Id == "halloween/crypt");
        var hollow = MapGen.Generate(new MapSpec { Seed = seed, Arena = true, People = "pack" });
        Assert.DoesNotContain(hollow.Pieces, p => p.Id is "halloween/skull" or "halloween/ribcage" or "halloween/skull_candle");
        var ruts = MapGen.Generate(new MapSpec { Seed = seed, Arena = true, People = "kerchiefs" });
        Assert.DoesNotContain(ruts.Pieces, p => p.Id.Contains("skull"));
    }

    [Fact]
    public void A_place_is_called_by_its_people_s_word_and_its_name_makes_its_mood()
    {
        for (int day = 1; day < 30; day++)
            foreach (var o in MapOffers.Today(day, 2, 0))
            {
                var words = ArenaPlaces.Names.First(n => n.Place == ArenaPlaces.IdFor(o.People)).Words;
                Assert.Contains(words, w => o.Spec.Name.EndsWith(" " + w));
                Assert.NotEqual("", ArenaPlaces.MoodOf(o.Spec.Name));
            }
        Assert.Equal("ashen", ArenaPlaces.For(new MapSpec { Arena = true, People = "dead", Name = "The Burnt Howes" }).Mood);
        Assert.Equal("drowned", ArenaPlaces.For(new MapSpec { Arena = true, People = "pack", Name = "The Drowned Dene" }).Mood);
        // A moonless night is darker than the place's own.
        var lit = ArenaPlaces.For(new MapSpec { Arena = true, People = "pack", Name = "The Broken Dene" });
        var dark = ArenaPlaces.For(new MapSpec { Arena = true, People = "pack", Name = "The Lampless Dene" });
        Assert.True(dark.Night.KeyIntensity < lit.Night.KeyIntensity);
    }

    [Fact]
    public void The_ember_ring_chars_the_edge_all_the_way_round()
    {
        var m = MapGen.Generate(new MapSpec { Seed = 8, Arena = true, People = "pack" });
        int res = m.SplatRes;
        double ps = MapGen.Size / res;
        // Every bearing has char at the edge; the middle has none.
        for (int k = 0; k < 36; k++)
        {
            var (x, z) = m.Rim[k * 5];
            int i = (int)((x + MapGen.Size / 2) / ps), j = (int)((z + MapGen.Size / 2) / ps);
            Assert.True(m.Splat2![(j * res + i) * 4 + 1] > 120, $"no char at the edge, bearing {k * 10}");
        }
        int c = res / 2;
        Assert.True(m.Splat2![(c * res + c) * 4 + 1] < 10);
    }
}
