using System.Linq;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

public class MassGraceTests
{
    [Fact]
    public void NoKitMarkOnHerForMassKillGraceAfterHerMassKill()
    {
        // F1 lead 26: her blows felled a mass in one step: no new kit mark (lane/ring) for MassKillGrace s.
        var b = BattleTests.Arena(2);
        var es = Enumerable.Range(0, 12).Select(i => b.SpawnEnemy("risen", 3 + i % 4, i / 4, new Battle.SpawnOpts { Style = SpawnStyle.Walk })!).ToList();
        b.Tick(1.0 / 60, 0, 0);
        b.Events.Drain();
        Assert.Equal(0, b.MassGraceLeft);
        foreach (var e in es) b.HitEnemy(e, 100000, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
        Assert.Equal(Battle.MassKillGrace, b.MassGraceLeft, 6);
        foreach (var kind in new[] { "ring", "charge", "closing", "pull" })
            Assert.True(b.KitWait(kind, null) >= b.MassGraceLeft - 1e-9, kind);
        // three in a step are no mass kill: no grace
        var c = BattleTests.Arena(2);
        var few = Enumerable.Range(0, 3).Select(i => c.SpawnEnemy("risen", 3 + i, 0, new Battle.SpawnOpts { Style = SpawnStyle.Walk })!).ToList();
        c.Tick(1.0 / 60, 0, 0);
        c.Events.Drain();
        foreach (var e in few) c.HitEnemy(e, 100000, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
        Assert.Equal(0, c.MassGraceLeft);
        Assert.Equal(0, c.KitWait("ring", null));
    }
}
