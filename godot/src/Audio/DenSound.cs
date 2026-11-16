using System;
using System.Collections.Generic;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Sound;

/// <summary>
/// The den's sound rules, Godot-free so the tests can run them on a sim's events (docs/team/den_sound_events.md):
/// which creature has which voice, how a pack is kept from becoming noise, her effort grunts, and where the den's
/// pits are (the field's connected holes), for the placed loop.
/// </summary>
public static class DenSound
{
    /// <summary>The voice a creature def has (voice.&lt;kind&gt;.&lt;moment&gt;), or null: it has none.</summary>
    public static string? KindOf(string defId) => defId switch
    {
        "wolf" => "wolf", "wolf_blighted" => "wolfb", "boar" => "boar", "lt_pack" => "yearling", "boss_pack" => "packmother", _ => null,
    };

    /// <summary>A boss's voice is never gated.</summary>
    public static bool Unlimited(string kind) => kind == "packmother";

    /// <summary>The numbers, picked from a 5-wolf pack fight's log (DenSoundTests.PackFight; docs/team/den_sound_events.md):
    /// at most MaxVoices creature voices at once; one voice of a kind and moment per Cooldown seconds; and a pack's
    /// notices never closer than NoticeGap whatever the kind (a pack that wakes together is one howl, then the next).</summary>
    public const int MaxVoices = 4;
    public const double NoticeGap = 0.45, MaxHearing = 30;
    public static double Cooldown(string moment) => moment switch { "notice" => 1.6, "bite" => 0.55, "lunge" => 0.9, "hurt" => 0.3, "death" => 0.18, _ => 1 };
    /// <summary>How long a voice of this moment holds one of the MaxVoices.</summary>
    public static double Holds(string moment) => moment switch { "notice" => 1.2, "bite" => 0.7, "lunge" => 0.9, "hurt" => 0.35, "death" => 0.6, _ => 0.8 };

    /// <summary>Which of a frame's wanted voices play: the caller offers them nearest first.</summary>
    public sealed class VoiceLimiter
    {
        readonly Dictionary<string, double> last = new();
        readonly List<double> ends = new();
        double lastNotice = -99;
        public int Played, Dropped;

        public bool Admit(string kind, string moment, double now)
        {
            if (Unlimited(kind)) { Played++; return true; }
            ends.RemoveAll(e => e <= now);
            string key = kind + "." + moment;
            if (last.TryGetValue(key, out var t) && now - t < Cooldown(moment)) { Dropped++; return false; }
            if (ends.Count >= MaxVoices && moment != "death") { Dropped++; return false; }
            if (moment == "notice") { if (now - lastNotice < NoticeGap) { Dropped++; return false; } lastNotice = now; }
            last[key] = now;
            ends.Add(now + Holds(moment));
            Played++;
            return true;
        }
    }

    /// <summary>Her effort: a heavy swing grunts most times, a light cut seldom, never twice inside a cooldown.</summary>
    public sealed class GruntRule
    {
        double last = -99;
        public bool Admit(bool heavy, double now, double roll)
        {
            if (now - last < (heavy ? 0.7 : 2.0)) return false;
            if (roll >= (heavy ? 0.8 : 0.16)) return false;
            last = now;
            return true;
        }
    }

    /// <summary>The den's pits from its hole field (negative = inside a hole): each connected region over 2 m2, as its centre
    /// and the radius of a disc of its area. The field is res x res cells of `step` metres, from -half.</summary>
    public static List<(double X, double Z, double R)> Pits(float[] f, int res, double half, double step)
    {
        var seen = new bool[res * res];
        var pits = new List<(double, double, double)>();
        var q = new Queue<int>();
        for (int k0 = 0; k0 < res * res; k0++)
        {
            if (seen[k0] || f[k0] >= 0) continue;
            seen[k0] = true; q.Enqueue(k0);
            int n = 0; double sx = 0, sz = 0;
            while (q.Count > 0)
            {
                int k = q.Dequeue(); n++;
                int i = k % res, j = k / res;
                sx += -half + i * step; sz += -half + j * step;
                for (int d = 0; d < 4; d++)
                {
                    int ni = i + (d == 0 ? 1 : d == 1 ? -1 : 0), nj = j + (d == 2 ? 1 : d == 3 ? -1 : 0);
                    if (ni < 0 || nj < 0 || ni >= res || nj >= res) continue;
                    int nk = nj * res + ni;
                    if (seen[nk] || f[nk] >= 0) continue;
                    seen[nk] = true; q.Enqueue(nk);
                }
            }
            double area = n * step * step;
            if (area >= 2) pits.Add((sx / n, sz / n, Math.Sqrt(area / Math.PI)));
        }
        return pits;
    }

    /// <summary>How loud a placed loop is at a distance from its source's rim: full inside, gone by Reach metres past it.</summary>
    public static double Falloff(double dist, double radius, double reach = 22)
    {
        double d = Math.Max(0, dist - radius);
        double k = Math.Clamp(1 - d / reach, 0, 1);
        return k * k;
    }

    /// <summary>One creature voice the sim asks for this frame.</summary>
    public readonly record struct Want(string Kind, string Moment, double X, double Z, double Dist);

    /// <summary>The voices a frame's events ask for, nearest first: Ev.Voice (notice, bite, lunge), a hit that did not kill (hurt),
    /// a kill (death); a creature with no voice kind asks for nothing. Her Pack-Mother's moves are Ev.Sound ids, not here.</summary>
    public static List<Want> Wants(IReadOnlyList<CombatEvent> evs, double px, double pz)
    {
        var res = new List<Want>();
        HashSet<int>? killed = null;
        foreach (var e in evs) if (e is Ev.Kill k) (killed ??= new()).Add(k.Enemy);
        double D(double x, double z) => Math.Sqrt((x - px) * (x - px) + (z - pz) * (z - pz));
        foreach (var e in evs)
            switch (e)
            {
                case Ev.Voice v when KindOf(v.Def) is { } k1:
                    res.Add(new(k1, v.Moment, v.X, v.Z, D(v.X, v.Z))); break;
                case Ev.Hit h when !h.Dot && !h.Blocked && h.Target >= 0 && h.Def != null && KindOf(h.Def) is { } k2 && killed?.Contains(h.Target) != true:
                    res.Add(new(k2, "hurt", h.X, h.Z, D(h.X, h.Z))); break;
                case Ev.Kill kl when kl.Def != "mirror" && KindOf(kl.Def) is { } k3:
                    res.Add(new(k3, "death", kl.X, kl.Z, D(kl.X, kl.Z))); break;
            }
        res.RemoveAll(w => w.Dist > MaxHearing && !Unlimited(w.Kind));
        res.Sort((a, b) => a.Dist.CompareTo(b.Dist));
        return res;
    }

    /// <summary>A blow big enough that the music steps back for it (a crit, a heavy hit on a foe, a boss or elite falling, a hit
    /// on her that takes a sixth of her health).</summary>
    public static bool BigHit(CombatEvent e, double herMaxHp) => e switch
    {
        Ev.Hit h => !h.Dot && !h.Blocked && (h.Crit || h.Amount >= 0.2 * Math.Max(1, h.MaxHp)),
        Ev.Kill k => k.Boss || k.Elite,
        Ev.PlayerHit ph => !ph.Dodged && !ph.Blocked && !ph.Dot && ph.Amount >= herMaxHp / 6,
        Ev.Leap { Phase: LeapPhase.Land } => true,
        _ => false,
    };

    public enum Track { None, Explore, Boss, Falls }

    /// <summary>The den's recorded score: the exploration track from the entrance, the boss track from the Pack-Mother's arrival
    /// (a crossfade), the sting when she dies, then quiet for the rest of the den.</summary>
    public sealed class MusicRule
    {
        public const double FallsSeconds = 6.0;
        bool bossSeen; double fallsT;
        public Track Want { get; private set; }
        public void Update(bool inDen, bool bossUp, double dt)
        {
            if (!inDen) { bossSeen = false; fallsT = 0; Want = Track.None; return; }
            if (bossUp) { bossSeen = true; fallsT = 0; Want = Track.Boss; return; }
            if (!bossSeen) { Want = Track.Explore; return; }
            fallsT += dt;
            Want = fallsT < FallsSeconds ? Track.Falls : Track.None;
        }
    }

    /// <summary>The pack at a distance: now and then before the first fight, never during one (nor after the first has begun).</summary>
    public sealed class PackFarRule
    {
        public const double First = 14, Every = 40, Spread = 30;
        double due = First; bool fought;
        public bool Admit(bool inDen, bool fighting, double dt, double roll)
        {
            if (!inDen) { due = First; fought = false; return false; }
            if (fighting) fought = true;
            if (fought) return false;
            due -= dt;
            if (due > 0) return false;
            due = Every + Spread * roll;
            return true;
        }
    }
}
