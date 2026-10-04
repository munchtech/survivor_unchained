using System;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Sim;

/// <summary>
/// The charge director: when the horde's chargers and lungers may start a run, and the
/// caps on the horde's other marks (docs/SKILLS_DESIGN.md, "Encounters").
///
/// The owner: "in our charge mechanic once quite a few overlapping constantly. periods of
/// that are exciting, non stop can be a little weird." Left to its own clock, every tusker
/// in reach ran its lane the moment its cooldown was up, so a thick field was a lattice of
/// red lanes that never stopped. Now they come in waves: a few lanes at a time, one after
/// another, then a lull. Every half minute or so comes a spike, announced by the people's
/// own tell, when many run at once and then let go. Overlap is a moment, not the weather.
/// A creature refused keeps closing at a walk and asks again shortly.
///
/// Champions are counted but keep a small allowance of their own (they are the test);
/// bosses run their own scripts and are never asked.
/// </summary>
public sealed class ChargeDirector
{
    public enum Beat { Wave, Lull, Warn, Spike }

    /// <summary>Off: every charger keeps its own clock (the old way, for comparison).</summary>
    public bool On = true;
    /// <summary>Runs at once (wind-ups and runs) in a wave: 2 + tier / 2 in an arena.</summary>
    public int Cap = 2;
    /// <summary>Spikes come at all (an arena's; the wood by day keeps to waves).</summary>
    public bool Spikes;
    /// <summary>The people's tell before a spike: a line said over the survivor, and its sound.</summary>
    public string? Tell, TellSound;
    /// <summary>Seconds between spikes: about one a minute, oftener while the night builds
    /// into a landmark (ArenaPacing.Building), where the danger should rise with the numbers.</summary>
    public (double Min, double Max) SpikeEvery = (40, 55);

    public Beat Now { get; private set; } = Beat.Wave;
    /// <summary>Its own stream, so the beat it keeps never moves anything else's dice.</summary>
    readonly Rng rng;
    public ChargeDirector(uint seed) { rng = new Rng(seed * 2654435761u + 7); }
    /// <summary>Runs at once in a spike: more than twice a wave's.</summary>
    public int SpikeCap => Math.Max(5, Cap * 2 + 1);
    /// <summary>Champions' runs at once, whatever the beat.</summary>
    public int EliteCap => Cap >= 3 ? 2 : 1;
    /// <summary>Its own cooldown this far done, a charger may go in a spike: they run together.</summary>
    public bool Eager => On && Now == Beat.Spike;

    double beatT = 6, spikeT = 150, calmUntil = -1, lastStart = -9;
    int live, liveElite, able;

    /* What the harness reads. */
    /// <summary>Runs going now, and the most at once since the harness last asked.</summary>
    public int Live => live;
    public int Peak;
    public int Started, Refused, SpikesRun;

    /// <summary>At the top of the tick: count the runs going and move the beat on.</summary>
    public void Tick(Battle b, double dt)
    {
        live = liveElite = able = under = 0;
        var p = b.Player;
        foreach (var e in b.Enemies.Items)
        {
            if (!e.Alive) continue;
            if (e.State == EnemyState.Burrowed) { under++; continue; }
            if (e.Boss || e.Disposition == Disposition.Ally || (e.Def.Charge ?? e.Def.Lunge) == null) continue;
            if (e.State is EnemyState.Windup or EnemyState.Lunging)
            {
                live++;
                if (e.Elite) liveElite++;
            }
            else if (e.State == EnemyState.Active && !e.Elite && (e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z) < 16 * 16) able++;
        }
        Peak = Math.Max(Peak, live);
        if (!On) return;
        beatT -= dt;
        switch (Now)
        {
            case Beat.Wave: if (beatT <= 0) Go(Beat.Lull, 3 + 3 * rng.Next()); break;
            case Beat.Lull: if (beatT <= 0) Go(Beat.Wave, 5 + 4 * rng.Next()); break;
            case Beat.Warn: if (beatT <= 0) { Go(Beat.Spike, 3.5); SpikesRun++; } break;
            case Beat.Spike: if (beatT <= 0) Go(Beat.Lull, 5 + 2 * rng.Next()); break;
        }
        if (!Spikes || Now is Beat.Warn or Beat.Spike || b.Time < calmUntil) return;
        spikeT = Math.Min(spikeT - dt, SpikeEvery.Max);
        if (spikeT > 0) return;
        // A spike with nobody to run it is a tell for nothing: wait until there are enough.
        if (able < 3) { spikeT = 5; return; }
        Warn(b);
    }

    void Go(Beat beat, double t) { Now = beat; beatT = t; }

    /// <summary>The people's tell, then the spike.</summary>
    void Warn(Battle b, bool quiet = false)
    {
        Go(Beat.Warn, 1.3);
        spikeT = SpikeEvery.Min + (SpikeEvery.Max - SpikeEvery.Min) * rng.Next();
        if (quiet) return;
        var p = b.Player;
        if (Tell != null) b.Events.Emit(new Ev.Bark { X = p.X, Z = p.Z + 3, Text = Tell });
        b.Events.Emit(new Ev.Sound { Id = TellSound ?? "tell", X = p.X, Z = p.Z });
    }

    /// <summary>A set piece wants the spike now (a people's own turn): the tell (unless the
    /// set piece gives its own), then the run.</summary>
    public void Spike(Battle b, bool quiet = false)
    {
        if (!On || Now is Beat.Warn or Beat.Spike) return;
        calmUntil = -1;
        Warn(b, quiet);
    }

    /// <summary>A breather, the hush, a herald's duel: no lanes from the crowd for a while.</summary>
    public void Calm(Battle b, double seconds)
    {
        calmUntil = Math.Max(calmUntil, b.Time + seconds);
        if (Now is Beat.Warn or Beat.Spike) Go(Beat.Lull, seconds);
    }

    /// <summary>May this creature start its run now? Refused, it keeps walking in and asks
    /// again in a moment.</summary>
    public bool MayStart(Battle b, Enemy e)
    {
        if (e.Boss || e.Disposition == Disposition.Ally) return true;
        if (!On) { Started++; live++; return true; }
        if (e.Elite)
        {
            if (liveElite >= EliteCap) return Refuse(b, e);
            liveElite++; live++; Started++;
            return true;
        }
        int cap = b.Time < calmUntil ? 0 : Now switch { Beat.Wave => Cap, Beat.Spike => SpikeCap, _ => 0 };
        // One after another in a wave, so each lane is read before the next; a ripple in a spike.
        double gap = Now == Beat.Spike ? 0.12 : 0.7;
        if (live >= cap || b.Time - lastStart < gap) return Refuse(b, e);
        live++; Started++;
        lastStart = b.Time;
        return true;
    }

    bool Refuse(Battle b, Enemy e)
    {
        e.RangedT = 0.3 + 0.5 * rng.Next();
        Refused++;
        return false;
    }

    /* ------------------------------------------------- the other marks -- */

    /// <summary>Under the ground at once (tunnellers): a ring of rings is noise.</summary>
    public int UnderCap = 8;
    /// <summary>Death bursts fusing at once.</summary>
    public int FuseCap = 8;
    /// <summary>Ground the horde has left burning at once (the oldest goes out first).</summary>
    public int GroundCap = 24;

    int under;
    readonly double[] fuses = new double[32];

    /// <summary>May this tunneller go under now? Refused, it walks a while longer.</summary>
    public bool MayBurrow(Battle b, Enemy e)
    {
        if (under >= UnderCap) { e.RangedT = 1 + rng.Next(); return false; }
        under++;
        return true;
    }

    /// <summary>A death burst may fuse now (while fewer than the cap are).</summary>
    public bool MayFuse(Battle b, double fuse)
    {
        int n = 0, free = -1;
        for (int i = 0; i < fuses.Length; i++)
        {
            if (fuses[i] > b.Time) n++;
            else if (free < 0) free = i;
        }
        if (n >= FuseCap || free < 0) return false;
        fuses[free] = b.Time + fuse;
        return true;
    }
}
