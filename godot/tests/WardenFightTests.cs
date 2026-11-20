using System;
using System.Linq;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using SurvivorUnchained.Content;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(lane K, the owner 19 Nov: "the warden still makes no sense. how do you break his channel, why isn't he charging
/// the lamps" / "yeah this is just no fun") The Ford-Warden's two rules, each one she can see and act on: fight beside a lit
/// lamp and his charge comes through it (the lamp breaks, he reels), even with her in his reach; strike him
/// Prologue.ChannelBreakBlows times while he raises the drowned and the channel breaks.</summary>
public class WardenFightTests
{
    sealed record Setup(Journey J, FakeHost Host, Prologue Zone, Battle B, ZoneMeta Meta);

    static Setup AtTheWarden()
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0],
        }, 42);
        var meta = ZoneMeta.Load("lowford");
        var host = new FakeHost(j, meta);
        var zone = new Prologue(host, meta) { Draft = false };
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, meta.Collision(), Heightfield.Load(meta).HeightAt, at.X, at.Z, at.Facing, 5, ember: zone.Ember);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        var s = new Setup(j, host, zone, b, meta);
        var ford = meta.Place("LOWFORD", "ford");
        typeof(Prologue).GetMethod("Go", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance)!.Invoke(zone, [Prologue.Stage.ToFord]);
        Stand(s, ford.X, ford.Z + 12);
        Run(s, 0.1);
        Run(s, 7);
        Assert.Equal(Prologue.Stage.Boss, zone.Now);
        foreach (var id in new[] { "lamps", "flare", "channel", "dash" }) host.TaughtIds.Add(id);
        return s;
    }

    static void Run(Setup s, double seconds)
    {
        for (double t = 0; t < seconds; t += 1 / 60.0)
        {
            s.B.Player.Hp = s.B.MaxHp;
            s.Zone.Step(1 / 60.0);
            s.B.Tick(1 / 60.0, 0, 0);
            s.B.Events.Drain();
            s.Zone.Frame(1 / 60.0);
            s.Host.Pass(1 / 60.0);
        }
    }

    static void Stand(Setup s, double x, double z) { s.B.Player.X = x; s.B.Player.Z = z; }

    static Enemy Warden(Setup s) => s.B.Enemies.Living().Single(e => e.Tag == "warden");

    [Fact]
    public void Beside_a_lit_lamp_his_charge_comes_through_it_even_in_his_reach()
    {
        var s = AtTheWarden();
        var w = Warden(s);
        int lit = s.Zone.LitCount;
        Assert.True(lit > 0);
        // She stands just past a lamp on his far side, in his reach of it: within 60 s he charges, the lamp goes out.
        var lamp = s.Zone.LampPosts.First(l => l.Lit);
        double t = 0;
        for (; t < 60 && s.Zone.LitCount == lit; t += 0.1)
        {
            double dx = lamp.X - w.X, dz = lamp.Z - w.Z, d = Math.Max(0.1, Math.Sqrt(dx * dx + dz * dz));
            Stand(s, lamp.X + dx / d * 1.5, lamp.Z + dz / d * 1.5);
            Run(s, 0.1);
        }
        Assert.True(s.Zone.LitCount < lit, $"no lamp out in {t:0.0} s beside it");
        Assert.True(t < 20, $"his charge at the lamp took {t:0.0} s");
    }

    [Fact]
    public void Five_blows_break_his_channel()
    {
        var s = AtTheWarden();
        var w = Warden(s);
        // Down past his first threshold: he channels at the next walk.
        w.Hp = w.MaxHp * 0.65;
        bool channeled = false;
        for (int i = 0; i < 200 && !channeled; i++) { Stand(s, w.X + 12, w.Z); Run(s, 0.1); channeled = w.State == EnemyState.Casting; }
        Assert.True(channeled, "he never channeled");
        for (int i = 0; i < (int)Prologue.ChannelBreakBlows && w.State == EnemyState.Casting; i++)
        {
            s.B.HitEnemy(w, 1, School.Physical, Array.Empty<Tag>());
            Run(s, 0.3);
        }
        Assert.NotEqual(EnemyState.Casting, w.State);
    }
}
