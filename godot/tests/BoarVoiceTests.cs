using System;
using System.Linq;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Sound;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The owner, 19 Nov: "some monsters make noises way too often, boars mostly".</summary>
public sealed class BoarVoiceTests
{
    static (int Wanted, int Played, double MaxPerFoeRate) BoarFight(uint seed)
    {
        var b = BattleTests.Arena(seed);
        b.Player.X = 0; b.Player.Z = 0;
        for (int i = 0; i < 4; i++)
        {
            double a = i * Math.PI / 2;
            b.SpawnEnemy("boar", Math.Cos(a) * 9, Math.Sin(a) * 9, new Battle.SpawnOpts { Style = SpawnStyle.Walk });
        }
        var limiter = new DenSound.VoiceLimiter();
        int wanted = 0, played = 0;
        const double dt = 1.0 / 60;
        for (double t = 0; t < 30; t += dt)
        {
            b.Tick(dt, Math.Sin(t * 0.7) * 0.3, Math.Cos(t * 0.7) * 0.3);
            foreach (var w in DenSound.Wants(b.Events.Drain(), b.Player.X, b.Player.Z))
            {
                wanted++;
                if (limiter.Admit(w.Kind, w.Moment, t, w.Enemy)) played++;
            }
        }
        return (wanted, played, 0);
    }

    [Fact]
    public void One_foe_speaks_once_per_gap_and_a_kind_once_per_kind_gap()
    {
        var l = new DenSound.VoiceLimiter();
        Assert.True(l.Admit("boar", "lunge", 0, 7));
        Assert.False(l.Admit("boar", "bite", 2, 7));
        Assert.True(l.Admit("boar", "bite", 2, 8));    // another boar, past the kind gap
        Assert.False(l.Admit("boar", "bite", 2.5, 9)); // inside the kind gap
        Assert.True(l.Admit("boar", "bite", 4.1, 7));  // the first foe again, past its gap
        Assert.True(l.Admit("boar", "death", 4.2, 7)); // a death is always heard
    }

    [Fact]
    public void Four_boars_in_thirty_seconds_are_heard_sparingly()
    {
        var (wanted, played, _) = BoarFight(4);
        Console.WriteLine($"BOARS wanted={wanted} played={played}");
        Assert.True(wanted > 0);
        Assert.True(played <= 30 / DenSound.KindGap / 2 + 1, $"{played} boar voices in 30 s");   // was 23 of 29 wanted
        Assert.True(played <= wanted / 2);
    }
}
