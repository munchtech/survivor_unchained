using System.Linq;
using SurvivorUnchained.Play.Story;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>A story night's checkpoint (Sim/Checkpoint.cs): the build is a journal of the verbs that
/// made it, and going back plays it again, so what was built since is gone and nothing is lost.</summary>
public class CheckpointTests
{
    static string Build(Battle b) =>
        string.Join(" ", b.Weapons.Select(w => $"{w.Evolution?.Id ?? w.Id}{w.Rank}h{w.Honed}")) + " | " +
        string.Join(" ", b.Boons.OrderBy(k => k.Key).Select(k => $"{k.Key}{k.Value}"));

    [Fact]
    public void Going_back_undoes_what_was_built_since_and_keeps_what_was_built_before()
    {
        var b = BattleTests.Arena(4, ("cinderfall", 5));
        b.AddBoon("kindling");
        b.AddBoon("might");
        b.AddWeapon("knifestorm", 2);
        b.EmberLevel = 7;
        b.Player.Hp = b.MaxHp * 0.6;
        var at = b.Snapshot();
        string before = Build(b);
        double damage = b.Stats.Get(Stat.Damage);
        int triggers = b.Triggers.Count;
        double hp = b.Player.Hp;

        // A stage fought, and lost: more cards, an evolution, a blessing that calls a wolf.
        b.RankWeapon("cinderfall"); b.RankWeapon("cinderfall"); b.RankWeapon("cinderfall");
        b.Evolve("cinderfall", Content.Weapons.All["cinderfall"].Evolutions[0].Id);
        b.AddBoon("might");
        b.AddBoon("spirit_companion");
        b.AddWeapon("seeking_motes", 3);
        b.EmberLevel = 11;
        b.Player.Hp = 1;
        Assert.NotEqual(before, Build(b));
        b.Events.Drain();

        b.Restore(at);
        Assert.Equal(before, Build(b));
        Assert.Equal(damage, b.Stats.Get(Stat.Damage), 6);
        Assert.Equal(triggers, b.Triggers.Count);
        Assert.Equal(7, b.EmberLevel);
        Assert.Equal(hp, b.Player.Hp, 6);
        // What the lost stage's blessing called up is gone with it.
        Assert.DoesNotContain(b.Enemies.Living(), e => e.Disposition == Disposition.Ally);
        // And going back is not news: no evolution announced again.
        Assert.DoesNotContain(b.Events.Drain(), e => e is Ev.Evolve or Ev.Announce);
    }

    [Fact]
    public void A_union_is_one_verb_in_the_journal()
    {
        var u = Content.Unions.All[0];
        var b = BattleTests.Arena(6, (u.A, 8), (u.B, 8));
        b.Evolve(u.A, Content.Weapons.All[u.A].Evolutions[0].Id);
        b.Evolve(u.B, Content.Weapons.All[u.B].Evolutions[0].Id);
        var at = b.Snapshot();
        b.Unite(u.Id);
        string united = Build(b);
        Assert.Equal('U', b.Built[^1].Op);
        var after = b.Snapshot();
        b.Restore(at);
        Assert.Contains(b.Weapons, w => w.Id == u.A);
        b.Restore(after);
        Assert.Equal(united, Build(b));
    }

    [Fact]
    public void A_rise_spent_is_not_given_back_by_a_checkpoint()
    {
        var b = BattleTests.Arena(7);
        b.Player.Revives = 1;
        var at = b.Snapshot();
        b.HurtPlayer(b.MaxHp * 5, School.Physical, "wolf", null, telegraphed: true);
        Assert.Equal(1, b.Player.Rose);
        b.Restore(at);
        Assert.Equal(0, b.Player.Revives);
    }

    [Fact]
    public void A_shove_moves_her_and_buys_no_grace()
    {
        var b = BattleTests.Arena(8);
        double x = b.Player.X;
        b.ShovePlayer(1, 0, 2.5, 5, "the Pack");
        Assert.Equal(x + 2.5, b.Player.X, 1);
        Assert.Equal(0, b.Player.Iframes, 6);
    }

    /// <summary>Every blessing's numbers are its own: ranked up it replaces what it gave (never stacks it),
    /// and going back takes all of it away. Burn Bright named its numbers "syn:glass", which neither
    /// its ranking nor a rise took away: at its third rank she had a quarter of her health and three
    /// times her damage, and after a rise less again.</summary>
    [Fact]
    public void A_blessing_ranked_or_gone_back_from_leaves_no_numbers_behind()
    {
        foreach (var def in Content.Boons.All.Values.Where(d => d.Mods != null))
        {
            var b = BattleTests.Arena(4, ("cinderfall", 1));
            var at = b.Snapshot();
            int mods = b.Stats.List().Count;
            double hp = b.Stats.Get(Stat.MaxHealth), dmg = b.Stats.Get(Stat.Damage);
            for (int r = 0; r < def.Max; r++) b.AddBoon(def.Id);
            var own = def.Mods!(def.Max).Count();
            Assert.True(b.Stats.List().Count - mods <= own + 2, $"{def.Id}: {b.Stats.List().Count - mods} numbers at rank {def.Max}, its own are {own}");
            b.Restore(at);
            b.Events.Drain();
            Assert.Equal(mods, b.Stats.List().Count);
            Assert.Equal(hp, b.Stats.Get(Stat.MaxHealth), 6);
            Assert.Equal(dmg, b.Stats.Get(Stat.Damage), 6);
        }
    }

    [Fact]
    public void A_place_is_walled_and_its_gates_open()
    {
        var place = new StoryPlace
        {
            Spaces = [new("a", [Capsule.Circle(0, 0, 6)]), new("b", [Capsule.Circle(0, 12, 6), new Capsule(0, 4, 0, 8, 2.5)])],
            Gates = [new StoryGate("ab", -3, 6, 3, 6, "b")],
            Points = new() { ["start"] = (0, 0) },
        };
        var c = new CollisionWorld(80);
        place.Build(c);
        Assert.False(c.Blocked(0, 0, 0.5));
        Assert.True(c.Blocked(0, 6, 0.5));
        Assert.True(c.Blocked(7.5, 0, 0.5));
        Assert.True(place.Inside(0, 12) && !place.Inside(10, 0));
        StoryPlace.Open(c, place.Gates[0]);
        Assert.False(c.Blocked(0, 6, 0.5));
    }
}
