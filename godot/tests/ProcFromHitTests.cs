using System;
using System.Linq;
using SurvivorUnchained.Rpg;
using System.Text.Json;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-078, SU-083) A proc sized on her hit is part of that hit: her side (the global multipliers,
/// her crit) is in it already and is not applied again, it rolls no crit of its own, and the struck thing's own state
/// does not ride it to another. And an effect says where it bursts: Corran's ring is round her.</summary>
public sealed class ProcFromHitTests
{
    static (Battle b, Enemy a, Enemy c) Setup(double gap)
    {
        var b = BattleTests.Arena(4);
        // her side: x2 damage, every blow a crit
        b.Stats.Add(new StatMod(Stat.Damage, ModKind.More, 1.0, "test"));
        b.Stats.Add(new StatMod(Stat.CritChance, ModKind.Flat, 1 - b.Stats.Get(Stat.CritChance), "test"));
        Enemy Foe(double dx)
        {
            var e = b.SpawnEnemy("risen", b.Player.X + 8 + dx, b.Player.Z, new Battle.SpawnOpts { Style = SpawnStyle.Walk, Disposition = Disposition.Hostile })!;
            e.MaxHp = e.Hp = 1e6; e.Speed = 0;
            return e;
        }
        var (a, c) = (Foe(0), Foe(gap));
        b.Tick(1 / 60.0, 0, 0);   // (the spatial index learns them)
        return (b, a, c);
    }

    public static TheoryData<string> Kinds => new() { "nova", "explode", "chain", "strike" };

    static Effect Of(string kind) => kind switch
    {
        "nova" => new Effect.Nova(5, 0.5, Basis.Hit, School.Physical),
        "explode" => new Effect.Explode(2, 0.5, Basis.Hit, School.Physical),
        "chain" => new Effect.Chain(1, 5, 0.5, Basis.Hit, School.Physical),
        _ => new Effect.Strike(1, 1.4, 0.5, Basis.Hit, School.Physical, 0.5),
    };

    [Theory, MemberData(nameof(Kinds))]
    public void A_hit_sized_proc_takes_her_side_once(string kind)
    {
        // old: HitEnemy applied DamageMult (x2) and rolled a crit again on the proc's share of a hit that had both
        var (b, a, c) = Setup(1.0);
        b.AddTrigger(new TriggerDef { On = TriggerEvent.Hit, Effects = [Of(kind)], Icd = 10 }, "test");
        double dealt = b.HitEnemy(a, 100, School.Physical, [Tag.Physical], new HitOpts { Provoke = true });
        Assert.Equal(200 * b.Stats.Get(Stat.CritDamage), dealt, 6);   // x2 and her crit, in the hit
        for (int i = 0; i < 40; i++) b.Tick(1 / 60.0, 0, 0);
        Assert.Equal(0.5 * dealt, 1e6 - c.Hp, 6);
        Assert.False(c.LastCrit);
    }

    [Fact]
    public void The_struck_things_state_does_not_ride_the_proc()
    {
        // old: a's mark (x1.3) was in ctx.Damage, so the unmarked one beside it took it too
        var (b, a, c) = Setup(1.0);
        b.ApplyStatus(a, new StatusPayload(StatusKind.Mark, 1, 1, 10), 0);
        b.AddTrigger(new TriggerDef { On = TriggerEvent.Hit, Effects = [Of("nova")], Icd = 10 }, "test");
        double dealt = b.HitEnemy(a, 100, School.Physical, [Tag.Physical], new HitOpts { Provoke = true });
        Assert.Equal(0.5 * dealt / 1.3, 1e6 - c.Hp, 6);
    }

    [Fact]
    public void A_ring_round_her_bursts_round_her()
    {
        // old: every proc burst where its event was: Corran's ring went off round the struck thing
        var (b, a, c) = Setup(1.0);
        var near = b.SpawnEnemy("risen", b.Player.X + 1.5, b.Player.Z, new Battle.SpawnOpts { Style = SpawnStyle.Walk, Disposition = Disposition.Hostile })!;
        near.MaxHp = near.Hp = 1e6; near.Speed = 0;
        b.Tick(1 / 60.0, 0, 0);
        b.AddTrigger(new TriggerDef { On = TriggerEvent.Hit, Effects = [new Effect.Nova(2.6, 0.5, Basis.Hit, School.Physical) { At = Effect.Origin.Her }], Icd = 10 }, "test");
        b.HitEnemy(a, 100, School.Physical, [Tag.Physical], new HitOpts { Provoke = true });
        Assert.True(near.Hp < 1e6);
        Assert.Equal(1e6, c.Hp);
    }

    [Fact]
    public void Corrans_ring_is_written_round_her_and_round_trips()
    {
        var fx = JsonSerializer.Deserialize<Effect>("""{"do":"nova","radius":2.6,"damage":0.5,"basis":"hit","school":"physical","at":"her"}""")!;
        Assert.Equal(Effect.Origin.Her, fx.At);
        Assert.Contains("\"at\":\"her\"", JsonSerializer.Serialize(fx));
        Assert.Equal(Effect.Origin.Event, JsonSerializer.Deserialize<Effect>("""{"do":"nova","radius":2,"damage":1}""")!.At);
        var corran = Items.All.Values.First(d => d.Description.Contains("ring of steel round you"));
        Assert.Contains(corran.Triggers!, t => Array.Exists(t.Effects, e => e is Effect.Nova && e.At == Effect.Origin.Her));
    }
    [Fact]
    public void A_shatter_is_part_of_the_blow_that_broke_the_ice()
    {
        // (L1) old: fire_on_ice's burst was sized on the resolved blow (the frozen thing's x1.15 in it) and took x2 again
        var b = BattleTests.Arena(2);
        b.Stats.Add(new StatMod(Stat.Damage, ModKind.More, 1.0, "test"));
        b.Lamps = new LampLoadout();
        b.Lamps.Add(LampRulesTests.Rule("fire_on_ice", ("radius", 2), ("share", 0.5)));
        var a = b.SpawnEnemy("wolf", b.Player.X + 5, b.Player.Z)!;
        var n = b.SpawnEnemy("wolf", b.Player.X + 6, b.Player.Z)!;
        a.MaxHp = a.Hp = 1e6; n.MaxHp = n.Hp = 1e6;
        b.Tick(0.05, 0, 0);
        a.Status[StatusKind.Frozen] = new StatusSlot(10, 1, 0, 0);
        b.HitEnemy(a, 100, School.Fire, [Tag.Spell], new HitOpts { NoCrit = true });
        double her = 100 * b.Stats.DamageMult(School.Fire, [Tag.Spell], a.Def.Family);
        Assert.Equal(0.5 * her * (1 - (n.Def.Resists?.Of(School.Frost) ?? 0)), 1e6 - n.Hp, 6);
    }
}
