using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Sim;

public enum DeathKind { Fall, Launch, Burst }

/* Spectacular deaths are rewards (docs/design/ARPG_FUN.md P1 item 5): only crits, overkill and elites are eligible, a
 * share of those is shown, at a capped rate, as a Burst or a Launch. Deterministic without the sim's Rng (an integer
 * hash), so no random sequence moves. Numbers: data/content/death_show.json. */
public sealed class DeathShow
{
    public sealed class Tuning
    {
        public double Share = 0.33, Window = 0.5, MinBlow = 2, BurstBlow = 3, BurstCritBlow = 2;
        public int MaxPerWindow = 3;
        /// <summary>A mass kill (massFrom or more kills in one step) may show up to massMaxPerWindow in its window.</summary>
        public int MassFrom = 4, MassMaxPerWindow = 8;
        public double LaunchBase = 0.9, LaunchPerBlow = 0.6, LaunchBlowCap = 2, LaunchMin = 0.9, LaunchMax = 2.1;
    }

    static Tuning? tuning;
    public static Tuning T => tuning ??= Json.Parse<Tuning>(Json.ReadContent("death_show.json"));

    readonly Queue<double> shown = new();
    double stepTime = double.NaN;
    int stepKills;
    readonly Tuning t;
    public DeathShow(Tuning? tune = null) { t = tune ?? T; }

    /// <summary>A hash of two integers to [0,1).</summary>
    public static double Draw(int id, int serial)
    {
        unchecked
        {
            uint h = (uint)id * 2654435761u ^ ((uint)serial + 0x9E3779B9u) * 2246822519u;
            h ^= h >> 15; h *= 2246822519u; h ^= h >> 13; h *= 3266489917u; h ^= h >> 16;
            return h / 4294967296.0;
        }
    }

    public bool Eligible(bool boss, bool credited, bool crit, double blow, bool elite)
        => !boss && credited && (crit || blow >= t.MinBlow || elite);

    /// <summary>What this kill is shown as. Call once per kill, in order.</summary>
    public DeathKind Decide(double time, int id, int serial, bool boss, bool credited, bool crit, double blow, bool elite, bool fire)
    {
        // (every kill counts toward the step's tally: a blow felling a pack is a mass kill and shows more of it)
        if (time != stepTime) { stepTime = time; stepKills = 0; }
        stepKills++;
        if (!Eligible(boss, credited, crit, blow, elite)) return DeathKind.Fall;
        if (Draw(id, serial) >= t.Share) return DeathKind.Fall;
        while (shown.Count > 0 && time - shown.Peek() >= t.Window) shown.Dequeue();
        if (shown.Count >= (stepKills >= t.MassFrom ? t.MassMaxPerWindow : t.MaxPerWindow)) return DeathKind.Fall;
        shown.Enqueue(time);
        return !fire && (blow >= t.BurstBlow || (crit && blow >= t.BurstCritBlow)) ? DeathKind.Burst : DeathKind.Launch;
    }

    /// <summary>Launch distance in metres for a blow, before the body's size.</summary>
    public static double LaunchDistance(double blow)
        => Math.Clamp(T.LaunchBase + T.LaunchPerBlow * Math.Min(blow, T.LaunchBlowCap), T.LaunchMin, T.LaunchMax);
}
