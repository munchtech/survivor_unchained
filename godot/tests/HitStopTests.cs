using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Look;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

public class HitStopTests
{
    static readonly HitStopTable T = HitStopTable.Load;

    [Fact]
    public void TableValuesAndBands()
    {
        Assert.Equal(0, T.TrashMs);
        Assert.Equal(50, T.HeavyMs);
        Assert.Equal(55, T.CritMs);
        Assert.Equal(55, T.ArtMs);
        Assert.Equal(90, T.EliteKillMs);
        Assert.Equal(100, T.BossKillMs);
        Assert.Equal(150, T.CapMs);
        Assert.InRange(T.HeavyMs, 40, 60);
        Assert.InRange(T.CritMs, 40, 60);
        Assert.InRange(T.EliteKillMs, 80, 100);
        Assert.InRange(T.BossKillMs, 80, 100);
    }

    [Fact]
    public void ZeroAskIsNoOp()
    {
        var s = new HitStops(T);
        Assert.False(s.Ask(3, 0, 0));
        Assert.False(s.Held(3));
        Assert.Equal(1, s.Rate(3));
    }

    [Fact]
    public void RateIsOneUnlessHeld()
    {
        var s = new HitStops(T);
        Assert.Equal(1, s.Rate(3));
        s.Ask(3, 0.05, 0);
        Assert.Equal(T.Rate, s.Rate(3));
        for (int i = 0; i < 4; i++) s.Tick(0.016);
        Assert.False(s.Held(3));
        Assert.Equal(1, s.Rate(3));
    }

    [Fact]
    public void CrowdScale()
    {
        var a = new HitStops(T); a.Ask(1, 0.05, 30);
        Assert.Equal(0.05, a.Left(1), 6);
        var b = new HitStops(T); b.Ask(1, 0.05, 31);
        Assert.Equal(0.05 * T.CrowdScale, b.Left(1), 6);
    }

    [Fact]
    public void LongerRemainingNeverTheSum()
    {
        var s = new HitStops(T);
        s.Ask(1, 0.05, 0);
        s.Tick(0.02);
        s.Ask(1, 0.09, 0);
        Assert.Equal(0.09, s.Left(1), 6);          // ends 90 ms after the second ask, not 140
        var k = new HitStops(T);
        k.Ask(1, 0.09, 0);
        k.Tick(0.02);
        k.Ask(1, 0.05, 0);
        Assert.Equal(0.07, k.Left(1), 6);          // the 90's end is kept
    }

    [Fact]
    public void CapFromTheStartWhateverStacks()
    {
        var s = new HitStops(T);
        double held = 0;
        s.Ask(1, 0.1, 0);
        for (int i = 0; i < 100 && s.Held(1); i++)
        {
            s.Ask(1, 0.1, 0);                      // asked again every tick
            s.Tick(0.005); held += 0.005;
        }
        Assert.False(s.Held(1));
        Assert.True(held <= T.CapMs / 1000 + 0.0051, $"held {held}");
        Assert.True(held >= 0.14);
    }

    [Fact]
    public void GapAfterAHold()
    {
        var s = new HitStops(T);
        s.Ask(1, 0.05, 0);
        for (int i = 0; i < 11; i++) s.Tick(0.005);
        Assert.False(s.Held(1));
        Assert.False(s.Ask(1, 0.05, 0));           // inside the 90 ms gap
        for (int i = 0; i < 20; i++) s.Tick(0.005);
        Assert.True(s.Ask(1, 0.05, 0));            // past it
    }

    [Fact]
    public void BodiesAreIndependent()
    {
        var s = new HitStops(T);
        s.Ask(1, 0.05, 0); s.Ask(HitStops.Her, 0.09, 0);
        s.Tick(0.06);
        Assert.False(s.Held(1));
        Assert.True(s.Held(HitStops.Her));
        Assert.False(s.Held(2));
        Assert.Equal(1, s.Rate(2));
    }

    [Fact]
    public void ShakeFadesAndAlternates()
    {
        var s = new HitStops(T);
        s.Ask(1, 0.06, 0, 1, 0);
        Assert.Equal(1, s.Fade(1), 6);
        var (x0, _) = s.Shake(1);
        s.Tick(1.0 / 60);
        var (x1, _) = s.Shake(1);
        Assert.True(x0 * x1 < 0 || x0 == 0 || x1 == 0 || System.Math.Abs(x1) < System.Math.Abs(x0));
        Assert.True(System.Math.Abs(x0) <= T.ShakeM + 1e-9);
        var (hx, hz) = new HitStops(T).Shake(1);
        Assert.Equal(0, hx + hz);
    }

    // ---- classifier ----

    [Fact]
    public void SheHoldsOnlyForHerOwnContact()
    {
        var c = new HitStopClassifier(T);
        // a heavy blow landing 10 m off (a wave, a thrown edge): the struck body holds, she does not
        var far = c.Of(new CombatEvent[] { new Ev.Hit { Target = 7, Amount = 40, MaxHp = 100, Weapon = "groundbreaker", X = 10 } }, 100, 0, 0);
        Assert.Single(far); Assert.Equal(7, far[0].Body);
        var near = c.Of(new CombatEvent[] { new Ev.Hit { Target = 7, Amount = 40, MaxHp = 100, Weapon = "oathblade", X = 1.5 } }, 100, 0, 0);
        Assert.Contains(near, x => x.Body == HitStops.Her);
        // her own blade's swing past her_reach_m (gear grows its reach) is still her contact
        var longSwing = c.Of(new CombatEvent[] { new Ev.Hit { Target = 7, Amount = 40, MaxHp = 100, Weapon = "oathblade", Art = "slash_steel", X = T.HerReachM + 1 } }, 100, 0, 0);
        Assert.Contains(longSwing, x => x.Body == HitStops.Her);
        // an elite dying of a wound (no blow of hers on it this step): it holds, she never stops mid wind-up
        var wound = c.Of(new CombatEvent[] { new Ev.Kill { Enemy = 4, Elite = true, ByPlayer = true, X = 1 } }, 100, 0, 0);
        Assert.Single(wound); Assert.Equal(4, wound[0].Body);
        // her blow on it, near, kills it: both hold the elite kill's length
        var blow = c.Of(new CombatEvent[] { new Ev.Hit { Target = 4, Amount = 5, MaxHp = 100, Weapon = "oathblade", X = 1 }, new Ev.Kill { Enemy = 4, Elite = true, ByPlayer = true } }, 100, 0, 0);
        Assert.Equal(T.EliteKillMs / 1000, blow.Single(x => x.Body == HitStops.Her).Seconds, 6);
    }

    static Ev.Hit H(int target, bool crit = false, double amount = 1, double max = 100, string? weapon = "oathblade", string? art = null, bool dot = false, bool flare = false)
        => new() { Target = target, Crit = crit, Amount = amount, MaxHp = max, Weapon = weapon, Art = art, Dot = dot, ByFlare = flare, Dx = 1 };

    static List<StopAsk> Of(params CombatEvent[] evs) => new HitStopClassifier(T).Of(evs, 100);

    [Fact]
    public void PlainHitsAndTicksAskNothing()
    {
        Assert.Empty(Of(H(1), H(2), H(3, weapon: null, crit: true), H(4, dot: true, crit: true), H(5, flare: true, crit: true)));
    }

    [Fact]
    public void HeavyAndCritHoldHerAndTheVictim()
    {
        var a = Of(H(7, amount: 40), H(8));
        Assert.Equal(2, a.Count);
        Assert.Equal(0.05, a.Single(x => x.Body == 7).Seconds, 6);
        Assert.Equal(0.05, a.Single(x => x.Body == HitStops.Her).Seconds, 6);
        var c = Of(H(7, crit: true));
        Assert.Equal(0.055, c.Single(x => x.Body == 7).Seconds, 6);
    }

    [Fact]
    public void OathbladeAsksLandLater()
    {
        var a = Of(H(7, crit: true, art: "slash_steel"));
        Assert.All(a, x => Assert.Equal(0.03, x.Delay, 6));
        Assert.All(Of(H(7, crit: true, art: "disc")), x => Assert.Equal(0, x.Delay));
    }

    [Fact]
    public void KillsAndArts()
    {
        var k = Of(new Ev.Kill { Enemy = 4, Elite = true, ByPlayer = true });
        Assert.Equal(0.09, k.Single(x => x.Body == 4).Seconds, 6);
        var bk = Of(H(4), new Ev.Kill { Enemy = 4, Boss = true, Elite = true, ByPlayer = true });
        Assert.Equal(0.1, bk.Single(x => x.Body == HitStops.Her).Seconds, 6);
        Assert.Empty(Of(new Ev.Kill { Enemy = 4, Elite = true, ByPlayer = true, ByFlare = true }));
        Assert.Empty(Of(new Ev.Kill { Enemy = 4, Elite = false, ByPlayer = true }));
        var art = Of(H(1), H(2), new Ev.Ability { Id = "shield_bash" });
        Assert.Equal(3, art.Count);
        Assert.All(art, x => Assert.Equal(0.055, x.Seconds, 6));
    }

    [Fact]
    public void ChargeHoldsOnItsFirstImpactOnly()
    {
        var c = new HitStopClassifier(T);
        var impact = new CombatEvent[] { new Ev.Charge { Phase = ChargePhase.Impact } };
        Assert.Single(c.Of(impact, 100));
        Assert.Empty(c.Of(impact, 100));
        c.Of(new CombatEvent[] { new Ev.Charge { Phase = ChargePhase.Start } }, 100);
        Assert.Single(c.Of(impact, 100));
    }

    [Fact]
    public void HurtHoldsHerOnly()
    {
        var a = Of(new Ev.PlayerHit { Amount = 13 });
        Assert.Single(a);
        Assert.Equal(HitStops.Her, a[0].Body);
        Assert.Equal(0.06, a[0].Seconds, 6);
        Assert.Empty(Of(new Ev.PlayerHit { Amount = 12 }));
    }
}
