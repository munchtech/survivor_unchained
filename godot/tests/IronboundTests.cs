using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The owner, 19 Nov: "why do some monsters block nonstop? they take forever to kill" / "I don't know what
/// causes things to block but time to kill on those is really bizzare". The den's Ironbound champions turned 40% of
/// every blow, all fight, each one "blocked". Now the iron turns a few blows, then cracks for a while, with a tell.</summary>
public class IronboundTests
{
    static (Battle B, Enemy E) Iron()
    {
        var b = BattleTests.Arena();
        // (out of her own blade's reach, held still: a tick's swing of hers would crack it too)
        var e = b.SpawnEnemy("boar", 40, 0)!;
        e.Speed = 0;
        e.Def = Signs.Wear(e.Def, ["ironbound"]);
        e.MaxHp = e.Hp = 100000;
        b.Events.Drain();
        return (b, e);
    }

    static (bool Blocked, List<string> Said) Strike(Battle b, Enemy e, bool heavy = false)
    {
        b.HitEnemy(e, 10, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true, Heavy = heavy });
        bool blocked = false; var said = new List<string>();
        foreach (var ev in b.Events.Drain())
        {
            if (ev is Ev.Hit h && h.Target == e.Id) blocked |= h.Blocked;
            if (ev is Ev.Floater f) said.Add(f.Text);
        }
        return (blocked, said);
    }

    [Fact]
    public void Ironbound_turns_a_few_blows_then_cracks_for_a_while_and_says_so()
    {
        var (b, e) = Iron();
        for (int i = 1; i < Battle.IronHolds; i++) Assert.True(Strike(b, e).Blocked, $"blow {i} turned");
        var crack = Strike(b, e);
        Assert.False(crack.Blocked);
        Assert.Contains("Iron cracked!", crack.Said);
        for (int i = 0; i < 6; i++) Assert.False(Strike(b, e).Blocked);
        var said = new List<string>();
        for (double t = 0; t < Battle.IronDown + 0.2; t += 1 / 60.0)
        {
            b.Tick(1 / 60.0, 0, 0);
            foreach (var ev in b.Events.Drain()) if (ev is Ev.Floater f) said.Add(f.Text);
        }
        Assert.Contains("Iron holds", said);
        Assert.True(Strike(b, e).Blocked);
    }

    [Fact]
    public void A_heavy_blow_cracks_the_iron_at_once()
    {
        var (b, e) = Iron();
        var s = Strike(b, e, heavy: true);
        Assert.False(s.Blocked);
        Assert.Contains("Iron cracked!", s.Said);
    }
}
