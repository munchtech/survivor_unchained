using System;
using System.Collections.Generic;

namespace SurvivorUnchained.Play.Zones;

/// <summary>The turns a night can take: the four every people shares, and two of the people's own.</summary>
public enum Turn { Ring, Champion, Stampede, Swarm, Signature, SecondSignature }

/// <summary>
/// The shape of a night before its boss (docs/EXPERIENCE_AUDIT.md, "Pacing"): how full the
/// horde is kept from minute to minute, when it is let breathe, and which turn comes next.
/// ArenaRun asks; what spawns and what it does is the arena's (and the combat lead's).
///
/// Measured, the night was a straight line: the horde grew evenly from 40 to 217, the four
/// turns came round in the same order, and the stretch before the boss was the second
/// easiest of the night. Now it is a sawtooth that rises into each landmark and lets go
/// after it:
///
///   0–2    arrival: the draft's first flood, the field a little thin
///   2–7    the people's ways; their own question at about six minutes
///   7–10   the build into the first herald
///   10     the herald: the crowd let thin round the duel; when it falls, a flood to mow
///   14–15  a breath before midnight's great blessing
///   17–20  the build into the second herald, and the same release
///   25–28½ the long push: the densest field, the people's question at full strength
///   28½–30 the hush: the people draw back and wait while the sign burns
///
/// After each turn has played out, a breather: the field is let thin for twenty seconds
/// so the survivor can gather, look round and breathe. A night shorter or longer than
/// thirty minutes keeps the same shape, scaled.
/// </summary>
public sealed class ArenaPacing
{
    readonly double end;
    double breathFrom = -1, breathTo = -1, floodTo = -1;
    bool heraldUp;
    Turn? last;
    int sinceChampion;
    readonly HashSet<int> asked = new();

    /// <param name="endSeconds">When the boss comes (the night's length).</param>
    public ArenaPacing(double endSeconds) { end = Math.Max(60, endSeconds); }

    /// <summary>A minute of a thirty-minute night, for a night of any length.</summary>
    double M(double seconds) => seconds / 60 * 30 / (end / 60);

    static double Lerp(double a, double b, double t) => a + (b - a) * Math.Clamp(t, 0, 1);

    /// <summary>The night's line before any turn's breather or flood: the share of the
    /// horde's number kept at this second (1 is the arena's own line).</summary>
    public double Shape(double seconds)
    {
        if (seconds >= end) return 1;
        double m = M(seconds);
        if (m < 2) return 0.85;
        if (m < 7) return 1.0;
        if (m < 10) return Lerp(1.0, 1.3, (m - 7) / 3);
        if (m < 14) return 1.0;
        if (m < 15) return 0.7;
        if (m < 17) return 1.0;
        if (m < 20) return Lerp(1.0, 1.35, (m - 17) / 3);
        if (m < 25) return 1.05;
        if (m < 28.5) return Lerp(1.1, 1.55, (m - 25) / 3);
        return 0.45;
    }

    /// <summary>The share of the horde's number kept now: the night's line, thinned round a
    /// herald, swollen after one falls, and let thin in a breather.</summary>
    public double TargetShare(double seconds)
    {
        if (seconds >= end) return 1;
        double share = Shape(seconds);
        if (heraldUp) share = Math.Min(share, 0.55);
        if (seconds < floodTo) share = Math.Max(share, 1.7);
        if (Breather(seconds)) share = Math.Min(share, 0.45);
        return share;
    }

    /// <summary>A turn has played out and the field is let thin.</summary>
    public bool Breather(double seconds) => seconds >= breathFrom && seconds < breathTo;

    /// <summary>A herald has fallen and the people pour in: the build mows.</summary>
    public bool Flooding(double seconds) => seconds < floodTo;

    /// <summary>The hush before the boss: the people hold back and no turn comes.</summary>
    public bool Hush(double seconds) => seconds < end && M(seconds) >= 28.5;

    /// <summary>A herald has come: its duel is the thing on the field.</summary>
    public void HeraldCame() => heraldUp = true;

    /// <summary>The herald is dead (or gone): the people flood in for half a minute.</summary>
    public void HeraldFell(double seconds)
    {
        if (!heraldUp) return;
        heraldUp = false;
        floodTo = seconds + 35;
    }

    /// <summary>A turn has just begun: a breather follows once it has played out.</summary>
    public void Played(double seconds)
    {
        breathFrom = seconds + 14;
        breathTo = seconds + 34;
    }

    /// <summary>The clock moved on (pictures, probes): the people's questions it passed over are
    /// not all asked at once on arrival.</summary>
    public void SkipTo(double seconds)
    {
        double m = M(seconds);
        if (m >= 5.5) asked.Add(0);
        if (m >= 16.5) asked.Add(1);
        if (m >= 25.5) asked.Add(2);
    }

    /// <summary>The next turn, or null for none now (a herald's duel, the hush, past the
    /// half hour). The people's own question at about six, seventeen and twenty-six
    /// minutes (the first again at full strength); from the eighth minute, a chest in every
    /// three turns (a champion's, or the captain's who leads the people's own turn);
    /// otherwise any but the last.</summary>
    public Turn? Next(double seconds, Func<double> r)
    {
        if (seconds >= end || heraldUp || Hush(seconds)) return null;
        double m = M(seconds);
        int landmark = m >= 25.5 ? 2 : m >= 16.5 ? 1 : m >= 5.5 ? 0 : -1;
        Turn t;
        if (landmark >= 0 && asked.Add(landmark)) t = landmark == 1 ? Turn.SecondSignature : Turn.Signature;
        else if (m >= 8 && sinceChampion >= 2 && last != Turn.Champion) t = Turn.Champion;
        else
        {
            var open = new List<Turn>();
            foreach (var k in new[] { Turn.Ring, Turn.Champion, Turn.Stampede, Turn.Swarm })
                if (k != last) open.Add(k);
            t = open[Math.Min(open.Count - 1, (int)(r() * open.Count))];
        }
        // (The people's own turns are led by a captain who carries a chest, so they pay as a champion does.)
        sinceChampion = t is Turn.Champion or Turn.Signature or Turn.SecondSignature ? 0 : sinceChampion + 1;
        last = t;
        return t;
    }
}
