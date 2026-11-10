using System;
using System.Collections.Generic;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Look;

/// <summary>The spark budget's choice (main's ruling, 10 Nov; View/BattleFx.HitSparkBudget draws by it). One source = the
/// hits of one art and school in one frame's events (not a Dot, not Blocked, not the Flare's). A source that lands n hits
/// or fewer is left alone. Over n, only n of its hits show: crits take the places first, the ones nearest HER when there
/// are more crits than places; plain hits fill what the crits leave, nearest the middle of what was struck (the blade's
/// contact for the held cut, else the centroid of the source's hits). The rest are hushed: no hit burst, no crit burst,
/// no gore chips. A hushed hit's number still shows and a kill's gore is thrown whole: neither reads this.
/// Plain C#, no engine: the same events, n, her place and contacts give the same hushed set (ties go to the earlier event).</summary>
public static class HitBudget
{
    /// <summary>One source over the budget, as the `hit budget` print says it. Struck = CritsShown + PlainShown + Hushed.</summary>
    public readonly record struct Tally(string? Art, School School, int Struck, int Crits, int CritsShown, int PlainShown, int Hushed);

    /// <summary>A hit the budget counts: a blow of a spell or a weapon, not a tick, not a blocked blow, not the Flare's.</summary>
    public static bool Counts(Ev.Hit h) => !h.Dot && !h.Blocked && !h.ByFlare;

    [ThreadStatic] static Dictionary<(string?, School), (double X, double Z, int N, int Crits)>? mids;
    [ThreadStatic] static List<(Ev.Hit H, double D, int I)>? crits, plain;
    static readonly Comparison<(Ev.Hit H, double D, int I)> Nearest = (p, q) => p.D != q.D ? p.D.CompareTo(q.D) : p.I.CompareTo(q.I);

    /// <summary>Fills <paramref name="hushed"/> (cleared first) with the hits of this frame that throw nothing, and
    /// <paramref name="tallies"/> (cleared first, if given) with one line per source over the budget, in the order the
    /// sources first struck. <paramref name="contacts"/>: where a source's blade met them (<see cref="HeldContacts"/>);
    /// a source with none ranks its plain hits from its centroid.</summary>
    public static void Choose(IReadOnlyList<CombatEvent> events, int n, double herX, double herZ, ISet<Ev.Hit> hushed,
        List<Tally>? tallies = null, IReadOnlyDictionary<(string?, School), (double X, double Z)>? contacts = null)
    {
        hushed.Clear();
        tallies?.Clear();
        if (n < 0) n = 0;
        var m = mids ??= new();
        m.Clear();
        int counted = 0;
        for (int i = 0; i < events.Count; i++)
            if (events[i] is Ev.Hit h && Counts(h))
            {
                var k = (h.Art, h.School);
                m.TryGetValue(k, out var s);
                m[k] = (s.X + h.X, s.Z + h.Z, s.N + 1, s.Crits + (h.Crit ? 1 : 0));
                counted++;
            }
        // (n hits or fewer in the whole frame: no source can be over. The common frame, and it sorts nothing.)
        if (counted <= n) return;
        var cr = crits ??= new();
        var pl = plain ??= new();
        // (sources in the order they first struck: the hushed set never hangs on it, the tallies' order does)
        for (int first = 0; first < events.Count; first++)
        {
            if (events[first] is not Ev.Hit f || !Counts(f)) continue;
            var k = (f.Art, f.School);
            if (!m.Remove(k, out var s) || s.N <= n) continue;
            double mx = s.X / s.N, mz = s.Z / s.N;
            if (contacts != null && contacts.TryGetValue(k, out var c)) { mx = c.X; mz = c.Z; }
            cr.Clear();
            pl.Clear();
            for (int i = first; i < events.Count; i++)
                if (events[i] is Ev.Hit h && Counts(h) && h.Art == k.Art && h.School == k.School)
                {
                    if (h.Crit) cr.Add((h, (h.X - herX) * (h.X - herX) + (h.Z - herZ) * (h.Z - herZ), i));
                    else pl.Add((h, (h.X - mx) * (h.X - mx) + (h.Z - mz) * (h.Z - mz), i));
                }
            cr.Sort(Nearest);
            pl.Sort(Nearest);
            int critsShown = Math.Min(cr.Count, n), plainShown = Math.Min(pl.Count, n - critsShown);
            for (int i = critsShown; i < cr.Count; i++) hushed.Add(cr[i].H);
            for (int i = plainShown; i < pl.Count; i++) hushed.Add(pl[i].H);
            tallies?.Add(new Tally(k.Art, k.School, s.N, s.Crits, critsShown, plainShown, s.N - critsShown - plainShown));
        }
        cr.Clear();
        pl.Clear();
        m.Clear();
    }

    /// <summary>The held cut's contact per source: a frame's held <see cref="Ev.Slash"/> of an art that struck names where
    /// its blade met them (the body nearest the cut's line), and the hits of its art and school are its source. The first
    /// such cut of a source in the frame is the one kept. No such cut = no entry (the centroid).</summary>
    public static void HeldContacts(IReadOnlyList<CombatEvent> events, IDictionary<(string?, School), (double X, double Z)> into)
    {
        into.Clear();
        for (int i = 0; i < events.Count; i++)
            if (events[i] is Ev.Slash { Held: true, Struck: > 0, Art: not null } s)
                // b.Swing.ContactAt replaces Ev.Slash.HitX/HitZ when combat's MR 3 is merged
                into.TryAdd((s.Art, s.School), (s.HitX, s.HitZ));
    }
}
