using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;

namespace SurvivorUnchained.Play.Zones;

/// <summary>
/// What a people puts in the field as its night goes on (docs/SKILLS_DESIGN.md, "Encounters").
///
/// The owner: "consider mechanics that ramp along with the level time and don't appear till
/// certain mini bosses and minion types show up". The night comes in stretches (Denizens.Stretches):
/// each opens with a miniboss wearing one verb (a charge, a ring, a burst, a volley, a howl), and
/// only once it has come do the kinds that carry that verb join the horde, and champions take
/// its Signs. A kind's share then grows with the minutes it has been in the field. So each
/// stretch teaches one thing, first on one big body that can be watched, then in the crowd.
///
/// The clock is the night's (ArenaRun.Minute: minutes of a thirty-minute night). A miniboss
/// held back (a herald's duel, the hush) comes late, up to its window; past that its kinds
/// join anyway, so no night is left without its verbs.
/// </summary>
public sealed class Escalation
{
    readonly Denizens people;
    readonly HashSet<int> came = new();

    /// <summary>Minutes after its own a stretch's miniboss may still come; past them its kinds join
    /// without it.</summary>
    public const double Window = 2.5;

    public Escalation(Denizens people) { this.people = people; }

    public IReadOnlyList<Stretch> Stretches => people.Stretches;

    /// <summary>The stretch whose kind this is, if a stretch brings it.</summary>
    int StretchOf(string def) => Array.FindIndex(people.Stretches, s => s.Joins.Contains(def));

    /// <summary>Has this stretch begun (its miniboss come, or its window passed)?</summary>
    public bool Open(int stretch, double minute) =>
        came.Contains(stretch) || minute >= people.Stretches[stretch].At + Window;

    /// <summary>Is this kind in the field at this minute?</summary>
    public bool Fields(string def, double minute)
    {
        int ix = Array.FindIndex(people.Arena, h => h.Def == def);
        if (ix < 0 || people.Arena[ix].From > minute) return false;
        int s = StretchOf(def);
        return s < 0 || Open(s, minute);
    }

    /// <summary>The kinds in the field, with their weights and the minute they could first join.</summary>
    public IEnumerable<(string Def, double Weight, double From)> Kinds(double minute) =>
        people.Arena.Where(h => Fields(h.Def, minute));

    /// <summary>The stretch whose miniboss is due now, if any (the earliest not yet come, inside its window).</summary>
    public int? Due(double minute)
    {
        for (int i = 0; i < people.Stretches.Length; i++)
        {
            var s = people.Stretches[i];
            if (came.Contains(i) || minute < s.At) continue;
            if (minute < s.At + Window) return i;
        }
        return null;
    }

    /// <summary>Its miniboss has come: its kinds join, its Signs open.</summary>
    public void Came(int stretch) => came.Add(stretch);

    /// <summary>The stretches past at a minute (the clock moved on: pictures, probes): taken as come.</summary>
    public void SkipTo(double minute)
    {
        for (int i = 0; i < people.Stretches.Length; i++)
            if (minute >= people.Stretches[i].At) came.Add(i);
    }

    /// <summary>The Signs a champion may wear now: the people's own from the first, then each
    /// stretch's as it opens.</summary>
    public List<string> Signs(double minute)
    {
        var o = new List<string>(people.Signs);
        for (int i = 0; i < people.Stretches.Length; i++)
            if (Open(i, minute)) o.AddRange(people.Stretches[i].Signs);
        return o.Distinct().ToList();
    }

    /// <summary>The minibosses of the stretches already come (the long night sends them back).</summary>
    public List<string> Met(double minute) =>
        Enumerable.Range(0, people.Stretches.Length).Where(i => Open(i, minute)).Select(i => people.Stretches[i].Miniboss).ToList();

    /// <summary>How many Signs a champion wears (docs/bestiary/COUNTERS.md 4): none at the first
    /// tier until the tenth minute, then one; one at the second; one, and two from the fifteenth
    /// minute, at the third and fourth; two beyond. A herald one more, at most three; in the long
    /// night one more each time what rules the people has come again.</summary>
    public static int SignCount(int tier, double minute, bool herald, int returns)
    {
        int n = tier <= 1 ? (minute < 10 ? 0 : 1) : tier == 2 ? 1 : tier <= 4 ? (minute < 15 ? 1 : 2) : 2;
        if (herald) n++;
        return Math.Min(3, n + returns);
    }
}
