using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;
using static SurvivorUnchained.Sim.TelegraphRead;

namespace SurvivorUnchained.Tests;

/// <summary>How a hostile telegraph reads (Sim/TelegraphRead.cs): the red line, the crowd's amber, the raising.</summary>
public class TelegraphReadTests
{
    static readonly Func<int, bool> Elite7 = id => id == 7;
    static Ev.Telegraph T(Action<Ev.Telegraph>? f = null)
    {
        var e = new Ev.Telegraph { Id = 1, Shape = TelegraphShape.Circle, Hostile = true, Kind = TelegraphKind.Blow };
        f?.Invoke(e);
        return e;
    }

    [Fact]
    public void An_elite_blow_is_danger() => Assert.Equal((TeleLook.Danger, false), Of(T(e => e.Id = 7), Elite7));

    [Fact]
    public void A_boss_blow_is_danger_though_its_id_is_no_enemys() => Assert.Equal((TeleLook.Danger, false), Of(T(e => { e.Id = 71; e.Boss = true; }), Elite7));

    [Fact]
    public void A_crowd_blow_is_amber() => Assert.Equal((TeleLook.Amber, false), Of(T(), Elite7));

    [Fact]
    public void A_named_crowd_move_is_plain() => Assert.Equal((TeleLook.Plain, false), Of(T(e => e.Label = "Lunge"), Elite7));

    [Fact]
    public void A_champions_full_ring_is_its_raising_amber_never_danger()
        => Assert.Equal((TeleLook.Amber, true), Of(T(e => { e.Id = 7; e.Shape = TelegraphShape.Ring; e.Inner = 0; }), Elite7));

    [Fact]
    public void A_boss_ring_with_no_inner_edge_is_danger()
        => Assert.Equal((TeleLook.Danger, false), Of(T(e => { e.Shape = TelegraphShape.Ring; e.Inner = 0; e.Boss = true; }), Elite7));

    [Fact]
    public void Other_marks_are_plain()
    {
        Assert.Equal(TeleLook.Plain, Of(T(e => { e.Id = 7; e.Faction = Faction.Pack; }), Elite7).Look);
        Assert.Equal(TeleLook.Plain, Of(T(e => { e.Id = 7; e.Kind = TelegraphKind.Ground; }), Elite7).Look);
        Assert.Equal(TeleLook.Plain, Of(T(e => { e.Id = 7; e.Hostile = false; }), Elite7).Look);
    }

    [Fact]
    public void Champion_is_a_boss_or_an_elite_line()
    {
        Assert.True(Champion(T(e => { e.Shape = TelegraphShape.Line; e.Boss = true; }), Elite7));
        Assert.True(Champion(T(e => { e.Shape = TelegraphShape.Line; e.Id = 7; }), Elite7));
        Assert.False(Champion(T(e => e.Shape = TelegraphShape.Line), Elite7));
    }

    [Fact]
    public void The_ford_wardens_cleave_and_charge_are_danger()
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0],
        }, 42);
        var meta = ZoneMeta.Load("lowford");
        var host = new FakeHost(j, meta);
        var zone = new Prologue(host, meta);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, meta.Collision(), Heightfield.Load(meta).HeightAt, at.X, at.Z, at.Facing, 5, ember: zone.Ember);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        var ford = meta.Place("LOWFORD", "ford");
        typeof(Prologue).GetMethod("Go", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance)!.Invoke(zone, [Prologue.Stage.ToFord]);
        var seen = new List<Ev.Telegraph>();
        void Tick(double dt)
        {
            b.Player.Hp = b.MaxHp;
            zone.Step(dt);
            b.Tick(dt, 0, 0);
            foreach (var ev in b.Events.Drain()) if (ev is Ev.Telegraph t) seen.Add(t);
            zone.Frame(dt);
            host.Pass(dt);
        }
        b.Player.X = ford.X; b.Player.Z = ford.Z + 12;
        for (int i = 0; i < 60 * 8 && zone.Now != Prologue.Stage.Boss; i++) Tick(1 / 60.0);
        Assert.Equal(Prologue.Stage.Boss, zone.Now);
        var warden = b.Enemies.Living().Single(e => e.Tag == "warden");
        seen.Clear();
        // Alternate close (cleave) and far (charge) until both have been wound up.
        for (int i = 0; i < 60 * 30; i++)
        {
            double d = (i / 120) % 2 == 0 ? 3.5 : 9;
            b.Player.X = warden.X + d; b.Player.Z = warden.Z;
            Tick(1 / 60.0);
            if (seen.Any(t => t.Id == warden.Id * 10 + 1) && seen.Any(t => t.Id == warden.Id * 10 + 2)) break;
        }
        Func<int, bool> champ = id => b.Enemies.Living().Any(x => x.Id == id && (x.Elite || x.Boss));
        foreach (int k in new[] { 1, 2 })
        {
            var t = seen.First(x => x.Id == warden.Id * 10 + k);
            Assert.True(t.Boss);
            Assert.Equal(TeleLook.Danger, Of(t, champ).Look);
        }
    }
}
