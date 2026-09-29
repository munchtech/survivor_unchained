using System.Linq;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>One night on the Low Ford road, without a screen (Play/Zones/Prologue.cs).</summary>
public class PrologueTests
{
    sealed record Setup(Journey J, FakeHost Host, Prologue Zone, Battle B, ZoneMeta Meta);

    static Setup Make()
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0], StartBoon = Content.Boons.StartBlessings[0],
        }, 42);
        var meta = ZoneMeta.Load("lowford");
        var host = new FakeHost(j, meta);
        var zone = new Prologue(host, meta);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, meta.Collision(), Heightfield.Load(meta).HeightAt, at.X, at.Z, at.Facing, 5);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        return new Setup(j, host, zone, b, meta);
    }

    static void Run(Setup s, double seconds, bool safe = true)
    {
        for (double t = 0; t < seconds; t += 1 / 60.0)
        {
            if (safe) { s.B.Player.Hp = s.B.MaxHp; }
            s.Zone.Step(1 / 60.0);
            s.B.Tick(1 / 60.0, 0, 0);
            s.B.Events.Drain();
            s.Zone.Frame(1 / 60.0);
            s.Host.Pass(1 / 60.0);
        }
    }

    static void Stand(Setup s, double x, double z) { s.B.Player.X = x; s.B.Player.Z = z; }

    [Fact]
    public void The_night_starts_by_the_fire_and_the_dead_rise()
    {
        var s = Make();
        Assert.Same(Atmospheres.Night, s.Host.Air);
        Assert.Equal("Survive the night", s.Host.Tracked.Single().Steps[0].Text);
        Assert.NotNull(s.Host.DraftTip);
        Run(s, 12);
        Assert.Equal(Prologue.Stage.Rising, s.Zone.Now);
        Assert.True(s.B.Enemies.Living().Count() > 6);
        Assert.Equal("move", s.Host.CurrentHint?.Id ?? "move");
    }

    [Fact]
    public void The_road_runs_from_the_clearing_to_the_ford()
    {
        var s = Make();
        Run(s, 112);
        Assert.Equal(Prologue.Stage.Road, s.Zone.Now);
        var cart = s.Meta.Place("LOWFORD", "cart");
        Stand(s, cart.X, cart.Z + 5);
        Run(s, 0.1);
        Assert.Equal(Prologue.Stage.Ambush, s.Zone.Now);
        Run(s, 49);
        Assert.Equal(Prologue.Stage.Road2, s.Zone.Now);
        var post = s.Meta.Place("LOWFORD", "post");
        Stand(s, post.X - 6, post.Z + 4);
        Run(s, 0.1);
        Assert.Equal(Prologue.Stage.Post, s.Zone.Now);
        var knight = s.B.Enemies.Living().Single(e => e.Tag == "knight");
        Assert.NotNull(s.Zone.Interactables.Single(i => i.Id == "chest").Locked!());
        s.B.KillEnemy(knight, true, null);
        var chest = s.Zone.Interactables.Single(i => i.Id == "chest");
        Assert.Null(chest.Locked!());
        chest.Act();
        Assert.Contains(s.J.Ch.Pack, p => p?.Def == "padded_jerkin");
        Stand(s, 0, 18);
        Run(s, 0.1);
        Assert.Equal(Prologue.Stage.Barrow, s.Zone.Now);
        s.B.KillEnemy(s.B.Enemies.Living().Single(e => e.Tag == "caller"), true, null);
        Run(s, 1.2);
        Assert.Equal(Prologue.Stage.ToFord, s.Zone.Now);
    }

    [Fact]
    public void The_warden_wakes_behind_its_lamps_falls_and_the_gate_opens_at_dawn()
    {
        var s = Make();
        var ford = s.Meta.Place("LOWFORD", "ford");
        // Straight to the ford.
        typeof(Prologue).GetMethod("Go", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance)!.Invoke(s.Zone, [Prologue.Stage.ToFord]);
        Stand(s, ford.X, ford.Z + 12);
        Run(s, 0.1);
        Assert.Equal(Prologue.Stage.Intro, s.Zone.Now);
        Assert.True(s.Host.Captured);
        Assert.NotNull(s.Host.Held);
        Run(s, 7);
        Assert.Equal(Prologue.Stage.Boss, s.Zone.Now);
        Assert.False(s.Host.Captured);
        var warden = s.B.Enemies.Living().Single(e => e.Tag == "warden");
        Run(s, 0.5);
        // Three lamps: most of every blow goes to them.
        Assert.Equal(0.4, warden.TakenMul, 3);
        Assert.True(s.Host.Boss!.Shielded);
        // Break a lamp.
        var pylon = s.Meta.Colliders.First(c => c.Tag == "pylon:0");
        s.Zone.Hooks.OnHitProp!("pylon:0", pylon.Id, School.Physical, 300, pylon.X, pylon.Z);
        Assert.Equal(2, s.Zone.LitCount);
        s.B.KillEnemy(warden, true, null);
        Assert.Equal(Prologue.Stage.Victory, s.Zone.Now);
        Assert.Equal(0, s.Zone.LitCount);
        Run(s, 14);
        Assert.Equal(Prologue.Stage.Dawn, s.Zone.Now);
        Assert.Equal(TimeOfDay.Dawn, s.J.World.Time);
        Assert.Contains(s.J.World.History, h => h.Id == "ford_warden_slain");
        Assert.DoesNotContain(s.B.Collision.All(), c => c.Tag == "gate");
        Run(s, 11);
        Assert.Equal(Prologue.Stage.Exit, s.Zone.Now);
        var gate = s.Meta.Place("LOWFORD", "gate");
        Stand(s, gate.X, gate.Z + 6);
        Run(s, 0.1);
        Assert.True(s.J.World.Fact("prologue.done").Truthy);
        Assert.Equal("waystation", s.Host.Travelled?.Zone);
    }

    [Fact]
    public void Falling_here_is_forgiven()
    {
        var s = Make();
        Run(s, 5);
        Assert.True(s.Zone.OnDeath("the dead"));
        s.B.Player.Alive = false;
        Run(s, 3, safe: false);
        Assert.True(s.B.Player.Alive);
        Assert.Equal(s.B.MaxHp, s.B.Player.Hp);
        Assert.NotNull(s.Host.Revival);
    }

    [Fact]
    public void After_the_prologue_the_road_is_quiet_at_dawn()
    {
        var a = Callings.Archetype("warden");
        var s = Make();
        s.J.World.Facts["prologue.done"] = true;
        var z2 = new Prologue(s.Host, s.Meta);
        var b = s.J.StartBattle(true, s.Meta.Collision(), (_, _) => 0, 0, -100, 0, 9);
        z2.Begin(b);
        Assert.Equal(Prologue.Stage.Exit, z2.Now);
        Assert.Same(Atmospheres.Dawn, s.Host.Air);
        Assert.DoesNotContain(b.Collision.All(), c => c.Tag == "gate");
    }
}
