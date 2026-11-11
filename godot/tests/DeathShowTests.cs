using System.Linq;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

public class DeathShowTests
{
    static DeathKind D(DeathShow s, double t, int id, int n, bool boss = false, bool cred = true, bool crit = true, double blow = 2, bool elite = false, bool fire = false)
        => s.Decide(t, id, n, boss, cred, crit, blow, elite, fire);

    [Fact]
    public void BossAndIneligibleNeverShown()
    {
        var s = new DeathShow();
        for (int i = 0; i < 2000; i++)
        {
            Assert.Equal(DeathKind.Fall, D(s, i, i, i, boss: true, elite: true, blow: 9));
            Assert.Equal(DeathKind.Fall, D(s, i, i, i, crit: false, blow: 1.5));
            Assert.Equal(DeathKind.Fall, D(s, i, i, i, cred: false, blow: 9));
        }
    }

    [Fact]
    public void DrawRateNearShare()
    {
        var s = new DeathShow();
        int shown = 0;
        for (int i = 0; i < 10000; i++) if (D(s, i * 10.0, 100 + i % 37, i) != DeathKind.Fall) shown++;
        Assert.InRange(shown / 10000.0, 0.30, 0.36);
    }

    [Fact]
    public void WindowCapsShows()
    {
        var s = new DeathShow();
        int shown = 0;
        for (int i = 0; i < 3000; i++) if (D(s, 5.0 + i * 0.0001, i, i) != DeathKind.Fall) shown++;   // 0.3 s of kills
        Assert.True(shown <= 3);
        Assert.True(shown > 0);
    }

    [Fact]
    public void MassKillShowsMoreOfIt()
    {
        var s = new DeathShow();
        int shown = 0;
        for (int i = 0; i < 25; i++) if (D(s, 9.0, i, i) != DeathKind.Fall) shown++;   // one blow fells 25
        Assert.InRange(shown, DeathShow.T.MaxPerWindow + 1, DeathShow.T.MassMaxPerWindow);
        // three kills in one step are no mass kill: the plain cap holds
        var p = new DeathShow();
        int few = 0;
        for (int i = 0; i < 3; i++) if (D(p, 9.0, i, i) != DeathKind.Fall) few++;
        for (int i = 3; i < 40; i++) if (D(p, 9.0 + i * 0.001, i, i) != DeathKind.Fall) few++;
        Assert.True(few <= DeathShow.T.MaxPerWindow);
    }

    [Fact]
    public void BurstVersusLaunch()
    {
        int id = Enumerable.Range(0, 500).First(i => DeathShow.Draw(i, 1) < 0.33);
        Assert.Equal(DeathKind.Burst, D(new DeathShow(), 1, id, 1, blow: 3, crit: false));
        Assert.Equal(DeathKind.Burst, D(new DeathShow(), 1, id, 1, blow: 2, crit: true));
        Assert.Equal(DeathKind.Launch, D(new DeathShow(), 1, id, 1, blow: 2.5, crit: false));
        Assert.Equal(DeathKind.Launch, D(new DeathShow(), 1, id, 1, blow: 4, crit: false, fire: true));
        Assert.Equal(DeathKind.Launch, D(new DeathShow(), 1, id, 1, blow: 1, crit: false, elite: true));
        Assert.Equal(DeathKind.Launch, D(new DeathShow(), 1, id, 1, blow: 1, crit: true));
    }

    [Fact]
    public void BattleKillsStillEmitAndBurstIsShown()
    {
        var b = BattleTests.Arena(2);
        int kills = 0, bursts = 0, launches = 0;
        for (int i = 0; i < 20; i++) b.SpawnEnemy("risen", 2 + i % 5, i / 5, new Battle.SpawnOpts { Style = SpawnStyle.Walk });
        for (double t = 0; t < 12; t += 1.0 / 60)
        {
            b.Tick(1.0 / 60, 0.2, 0);
            foreach (var ev in b.Events.Drain())
                if (ev is Ev.Kill k) { kills++; if (k.Burst) bursts++; if (k.Launch) launches++; Assert.False(k.Burst && k.Launch); }
        }
        Assert.True(kills > 5);
        Assert.True(bursts + launches <= kills);
    }
}
