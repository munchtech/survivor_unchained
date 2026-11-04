using System.Linq;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The lamp to hold (H1 item 6B, Play/Zones/ArenaRun.Lamp.cs): cold till its minute, its pool's reward on her
/// and off again, snuffers douse it out, she lights it again, and none of it where there is no board.</summary>
public class BoardLampTests
{
    const double Dt = 1 / 60.0;

    static ArenaTests.Setup Table(int tier = 1, bool story = false)
    {
        var spec = ArenaTests.Spec(story: story);
        spec.Tier = tier;
        return ArenaTests.Make(spec);
    }

    static void Step(ArenaTests.Setup s, double seconds)
    {
        for (double t = 0; t < seconds; t += Dt)
        {
            s.Zone.Step(Dt);
            s.Zone.Frame(Dt);
            s.B.Tick(Dt, 0, 0);
            s.B.Events.Drain();
            s.Host.Pass(Dt);
        }
    }

    /// <summary>The field cleared and her made safe, so only the lamp's own clock runs.</summary>
    static void Quiet(ArenaTests.Setup s)
    {
        foreach (var e in s.B.Enemies.Living().ToList()) s.B.Enemies.Release(e);
        s.B.Player.Hp = s.B.MaxHp;
        s.B.Player.Iframes = 1e9;
    }

    static void Put(Battle b, double x, double z) { b.Player.X = x; b.Player.Z = z; }

    [Fact]
    public void Cold_before_its_minute_and_lit_after()
    {
        var s = Table();
        Assert.True(s.Zone.HasLamp);
        var l = s.Zone.Lamp!;
        Assert.True(l.Light >= 0);
        s.Zone.SkipTo(l.Def.LitAt * 60 - 2);
        Quiet(s);
        Step(s, 1);
        Assert.False(s.Zone.LampLit);
        Assert.False(s.Host.Look.IsLit(l.Light));
        Step(s, 2);
        Assert.True(s.Zone.LampLit);
        Assert.True(s.Host.Look.IsLit(l.Light));
    }

    [Fact]
    public void Her_pool_doubles_the_Flare_fill_and_gives_it_back()
    {
        var s = Table();
        var l = s.Zone.Lamp!;
        s.Zone.SkipTo(l.Def.LitAt * 60 + 1);
        Quiet(s);
        double fill = s.B.Rules.FlareFill, ember = s.B.Rules.KillEmber;
        Put(s.B, l.X + 3, l.Z);
        Step(s, 0.2);
        Assert.True(s.Zone.InLampPool);
        Assert.Equal(fill * l.Def.FlareFill, s.B.Rules.FlareFill, 9);
        Assert.Equal(ember * l.Def.Ember, s.B.Rules.KillEmber, 9);
        Put(s.B, l.X + l.Def.Pool + 4, l.Z);
        Step(s, 0.2);
        Assert.False(s.Zone.InLampPool);
        Assert.Equal(fill, s.B.Rules.FlareFill, 9);
        Assert.Equal(ember, s.B.Rules.KillEmber, 9);
    }

    [Fact]
    public void A_snuffer_at_it_puts_it_out_and_two_seconds_at_it_light_it_again()
    {
        var s = Table();
        var l = s.Zone.Lamp!;
        s.Zone.SkipTo(l.Def.LitAt * 60 + 1);
        Quiet(s);
        Step(s, 0.1);
        Assert.True(s.Zone.LampLit);
        // Her far off; one of the crowd sent for the lamp, standing at it.
        Put(s.B, l.X + l.Def.Pool + 12, l.Z);
        var e = s.B.SpawnEnemy(SurvivorUnchained.Maps.MapOffers.People("pack").Arena[0].Def, l.X + 1.1, l.Z, new Battle.SpawnOpts { Level = 1 })!;
        e.MaxHp = e.Hp = 1e9;
        s.Zone.SendForLamp(e);
        Step(s, 1);
        Assert.True(s.Zone.LampLife < 1);
        Assert.True(s.Zone.LampLit);
        Step(s, l.Def.Life / l.Def.Douse + 1);
        Assert.False(s.Zone.LampLit);
        Assert.Equal(1, s.Zone.LampOuts);
        Assert.False(s.Host.Look.IsLit(l.Light));
        // She cannot light it with it there; killed, she stands at the wick two seconds and it takes.
        s.B.Enemies.Release(e);
        Put(s.B, l.X + 1.5, l.Z);
        Step(s, l.Def.Relight - 0.3);
        Assert.False(s.Zone.LampLit);
        Step(s, 0.5);
        Assert.True(s.Zone.LampLit);
        Assert.Equal(1, s.Zone.LampRelights);
        Assert.Equal(1, s.Zone.LampLife, 9);
        Assert.True(s.Host.Look.IsLit(l.Light));
    }

    [Fact]
    public void No_lamp_on_a_tier_two_or_a_story_night()
    {
        foreach (var s in new[] { Table(tier: 2), Table(story: true) })
        {
            Assert.False(s.Zone.HasLamp);
            Assert.Null(s.B.HeldLamp);
            Assert.Null(s.B.GoalFlow);
            s.Zone.SkipTo(6 * 60);
            Step(s, 1);
            Assert.False(s.Zone.LampLit);
            Assert.Equal(1, s.B.Rules.KillEmber);
        }
    }
}
