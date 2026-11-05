using SurvivorUnchained.Cinema;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Content;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(P9 C13) The film-side knobs: "ember", "foe", "eyelights" known; FilmFoes picks the zone's creature and clears.</summary>
public class FilmFoesTests
{
    [Fact]
    public void NewCuesAreKnownAndNotLasting()
    {
        foreach (var k in new[] { "ember", "foe", "eyelights" })
        {
            Assert.Contains(k, CineCue.Kinds);
            Assert.False(new CineCue { Do = k }.Lasting);
        }
    }

    [Fact]
    public void PicksByDefBossAndNearest_AndClears()
    {
        var corvane = new EnemyDef { Id = "corvane" };
        var risen = new EnemyDef { Id = "risen" };
        var a = new Enemy(1) { Seed = 0.1, Alive = true, Def = risen, X = 0, Z = 0 };
        var b = new Enemy(2) { Seed = 0.2, Alive = true, Def = risen, X = 10, Z = 0 };
        var c = new Enemy(3) { Seed = 0.3, Alive = true, Def = corvane, X = 5, Z = 25, Boss = true };
        var all = new[] { a, b, c };
        Assert.Same(c, FilmFoes.Pick(all, "corvane", false, null));
        Assert.Same(c, FilmFoes.Pick(all, null, true, null));
        Assert.Same(b, FilmFoes.Pick(all, "risen", false, (9, 0)));
        Assert.Null(FilmFoes.Pick(all, "wolf", false, null));
        FilmFoes.Set(c, new FilmFoes.Look(true, null, null, 1));
        Assert.True(FilmFoes.Of(c)!.Hidden);
        Assert.Null(FilmFoes.Of(a));
        // a pooled slot taken by a new creature is not the film's
        Assert.Null(FilmFoes.Of(new Enemy(3) { Seed = 0.9, Alive = true, Def = corvane }));
        FilmFoes.Clear();
        Assert.False(FilmFoes.Any);
    }
}
