using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The owner's encounter notes (docs/SKILLS_DESIGN.md, "Encounters"): charges in
/// waves with lulls and deliberate spikes, never a lattice of lanes that does not stop.</summary>
public class EncounterTests
{
    /// <summary>A survivor who cannot fall, with nothing of her own to kill them, and a ring of
    /// `n` of a kind round her, all in reach of a run.</summary>
    static Battle Ring(string def, int n, uint seed = 5, double r0 = 5, double r1 = 9)
    {
        var b = BattleTests.Arena(seed);
        b.RemoveWeapon("oathblade");
        for (int i = 0; i < n; i++)
        {
            double a = (double)i / n * Math.Tau, r = r0 + (r1 - r0) * b.Rng.Next();
            b.SpawnEnemy(def, b.Player.X + Math.Cos(a) * r, b.Player.Z + Math.Sin(a) * r,
                new Battle.SpawnOpts { Style = SpawnStyle.Walk, Disposition = Disposition.Hostile });
        }
        return b;
    }

    /// <summary>Runs the fight for `seconds`, the survivor kept standing; the runs going after each tick.</summary>
    static List<(double T, int Live, int Started)> Play(Battle b, double seconds, Action<double>? each = null)
    {
        var o = new List<(double, int, int)>();
        for (double t = 0; t < seconds; t += 1 / 60.0)
        {
            each?.Invoke(t);
            b.Player.Hp = b.MaxHp;
            b.Tick(1 / 60.0, 0, 0);
            b.Events.Drain();
            o.Add((b.Time, b.Charges.Live, b.Charges.Started));
        }
        return o;
    }

    [Fact]
    public void Left_to_their_own_clocks_a_ring_of_tuskers_is_a_lattice_of_lanes()
    {
        // The owner's note, measured: what the director is for.
        var b = Ring("boar", 60);
        b.Charges.On = false;
        var tl = Play(b, 30);
        Assert.True(tl.Max(x => x.Live) >= 10, $"most at once {tl.Max(x => x.Live)}");
    }

    [Fact]
    public void Sixty_tuskers_run_in_waves_never_more_than_the_cap_with_lulls_between()
    {
        var b = Ring("boar", 60);
        b.Charges.Cap = 3;
        var tl = Play(b, 60);
        Assert.True(tl.Max(x => x.Live) <= 3, $"most at once {tl.Max(x => x.Live)}");
        // They do run: a wave is not a wall.
        int started = tl[^1].Started;
        Assert.True(started >= 30, $"only {started} runs in a minute");
        // And they stop: lulls of three seconds or more with no run begun.
        int lulls = 0;
        double lastStart = 0;
        for (int i = 1; i < tl.Count; i++)
            if (tl[i].Started > tl[i - 1].Started)
            {
                if (tl[i].T - lastStart >= 3) lulls++;
                lastStart = tl[i].T;
            }
        Assert.True(lulls >= 3, $"{lulls} lulls in a minute");
        // One after another, not together: never two starts in the same half second of a wave.
        var starts = new List<double>();
        for (int i = 1; i < tl.Count; i++) if (tl[i].Started > tl[i - 1].Started) starts.Add(tl[i].T);
        Assert.All(starts.Zip(starts.Skip(1)), p => Assert.True(p.Second - p.First >= 0.49, $"{p.First:0.00} then {p.Second:0.00}"));
    }

    [Fact]
    public void A_spike_is_told_runs_many_at_once_and_lets_go()
    {
        var b = Ring("boar", 60, seed: 7);
        b.Charges.Cap = 3;
        b.Charges.Spikes = true;
        b.Charges.Tell = "The wolves give tongue.";
        var told = new List<double>();
        var live = new List<(double T, int Live, ChargeDirector.Beat Beat)>();
        bool fired = false;
        for (double t = 0; t < 30; t += 1 / 60.0)
        {
            if (!fired && t >= 8) { fired = true; b.Charges.Spike(b); }
            b.Player.Hp = b.MaxHp;
            b.Tick(1 / 60.0, 0, 0);
            if (b.Events.Drain().OfType<Ev.Bark>().Any(k => k.Text == b.Charges.Tell)) told.Add(b.Time);
            live.Add((b.Time, b.Charges.Live, b.Charges.Now));
        }
        Assert.Single(told);
        double spikeAt = told[0];
        // Told first: nothing runs past the cap until the tell has been heard.
        Assert.All(live.Where(x => x.T < spikeAt + 1.2), x => Assert.True(x.Live <= 3));
        // Then many at once.
        int most = live.Where(x => x.T < spikeAt + 6).Max(x => x.Live);
        Assert.True(most >= 5, $"the spike ran {most} at once");
        // And it lets go: a lull, and back under the wave's cap.
        Assert.Contains(live, x => x.T > spikeAt + 4.8 && x.T < spikeAt + 7 && x.Beat == ChargeDirector.Beat.Lull);
        Assert.All(live.Where(x => x.T > spikeAt + 8), x => Assert.True(x.Live <= 3, $"{x.Live} at {x.T:0.0}"));
    }

    [Fact]
    public void Spikes_come_by_themselves_every_half_minute_or_so_once_there_are_runners()
    {
        var b = Ring("boar", 40, seed: 9);
        b.Charges.Cap = 3;
        b.Charges.Spikes = true;
        b.Charges.Tell = "Now.";
        int spikes0 = b.Charges.SpikesRun;
        // (The first comes after the opening minutes.)
        Play(b, 400);
        int n = b.Charges.SpikesRun - spikes0;
        Assert.InRange(n, 5, 8);
    }

    [Fact]
    public void A_calm_holds_the_crowds_lanes_but_not_a_champions()
    {
        // (Greymuzzle: the tuskers are not his quarrel, as they would be a barrow knight's.)
        var b = Ring("boar", 30, seed: 11);
        var knight = b.SpawnEnemy("wolf_alpha", b.Player.X + 7, b.Player.Z, new Battle.SpawnOpts { Style = SpawnStyle.Walk, Disposition = Disposition.Hostile })!;
        // (Held where it stands: one that has walked up beside her has no run to make.)
        knight.Speed = 0;
        b.Charges.Cap = 3;
        b.Charges.Calm(b, 20);
        bool crowd = false, champion = false;
        Play(b, 15, _ =>
        {
            foreach (var e in b.Enemies.Living())
                if (e.State == EnemyState.Windup) { if (e == knight) champion = true; else crowd = true; }
        });
        Assert.False(crowd);
        Assert.True(champion);
    }

    [Fact]
    public void Tunnellers_go_under_a_few_at_a_time()
    {
        var b = Ring("lampling", 40, seed: 13, r0: 18, r1: 22);
        int most = 0;
        Play(b, 6, _ => most = Math.Max(most, b.Enemies.Living().Count(e => e.State == EnemyState.Burrowed)));
        Assert.InRange(most, 1, b.Charges.UnderCap);
    }

    [Fact]
    public void The_hordes_burning_ground_is_capped_oldest_first()
    {
        var b = BattleTests.Arena(15);
        GroundZone? first = null;
        for (int i = 0; i < 40; i++)
        {
            var z = b.SpawnZone(Side.Enemy, i, 0, 1.2, 10, 1, School.Fire);
            first ??= z;
            b.Tick(1 / 60.0, 0, 0);
        }
        Assert.Equal(b.Charges.GroundCap, b.Zones.Living().Count(z => z.Owner == Side.Enemy));
        Assert.DoesNotContain(b.Zones.Living(), z => z.Owner == Side.Enemy && z.X < 1);
    }
}
