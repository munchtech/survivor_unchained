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

    /// <summary>Her effort, as the den bot's log set it (DenSoundRunTests: a heavy swing lands about every 2.3 s in a fight, a light cut
    /// more often): Sunder grunts about every other cast (0.5, 1.5 s apart), another heavy swing less (0.4, 2 s apart), a light
    /// cut seldom (0.05, 3.5 s apart); never twice inside a cooldown.</summary>
    public sealed class GruntRule
    {
        double last = -99;
        public bool Admit(bool heavy, double now, double roll, bool sunder = false)
        {
            if (now - last < (sunder ? 1.5 : heavy ? 2.0 : 3.5)) return false;
            if (roll >= (sunder ? 0.5 : heavy ? 0.4 : 0.05)) return false;
            last = now;
            return true;
        }
    }

    /// <summary>Her own voice from the sim's moments: an effort grunt on a heavy swing or Sunder (most times) and on a light
    /// cut (seldom), the leap's shout and the landing's exhale, the dodge (the dash, never twice in half a second) and the stance
    /// taken up or put down. Returns the bank's ids with the gain and pitch to play them at.</summary>
    public sealed class HerVoice
    {
        readonly GruntRule grunt = new();
        double lastDash = -99;
        public IEnumerable<(string Id, double Gain, double Pitch)> Of(CombatEvent e, double now, double roll)
        {
            switch (e)
            {
                case Ev.Cast c when c.Heavy || c.Weapon == "sunder": if (grunt.Admit(true, now, roll, c.Weapon == "sunder")) yield return ("her.grunt", 1, 1); break;
                case Ev.Slash: if (grunt.Admit(false, now, roll)) yield return ("her.grunt", 1, 1); break;
                case Ev.Leap { Phase: LeapPhase.Takeoff }: yield return ("her.leap", 1, 1); break;
                case Ev.Leap { Phase: LeapPhase.Land }: yield return ("her.land", 1, 1); break;
                case Ev.Dash: if (now - lastDash >= 0.6) { lastDash = now; if (roll < 0.7) yield return ("her.dodge", 1, 1); } break;
                case Ev.Swap sw: yield return ("her.stance", sw.Stance != "" ? 1 : 0.8, sw.Stance != "" ? 1 : 0.88); break;
            }
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

    /// <summary>A blow big enough that the music steps back for it: a boss or elite falling, a hit that takes a fifth of her
    /// health, a hit that takes half of a foe's, her landing from Heroic Leap.</summary>
    public static bool BigHit(CombatEvent e, double herMaxHp) => e switch
    {
        Ev.Hit h => !h.Dot && !h.Blocked && h.Amount >= 0.5 * Math.Max(1, h.MaxHp) && h.MaxHp >= 60,
        Ev.Kill k => k.Boss || k.Elite,
        Ev.PlayerHit ph => !ph.Dodged && !ph.Blocked && !ph.Dot && ph.Amount >= herMaxHp / 5,
        Ev.Leap { Phase: LeapPhase.Land } => true,
        _ => false,
    };

    /// <summary>The music steps back for a big blow, not for every one: not again within a second and a half.</summary>
    public sealed class BigHitRule
    {
        double last = -99;
        public bool Admit(double now) { if (now - last < 1.5) return false; last = now; return true; }
    }

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

    /// <summary>The pack at a distance: now and then while it is quiet, never during a fight. (The brief said "before the first fight":
    /// the first pack wakes 23-29 m from the mouth and is on her in 4-8 s in every bot run, so that window is nothing; the rule
    /// counts the quiet stretches instead, and the first fight, the Pack-Mother's arrival included, silences it. The owner can say strict.)
    /// `fighting`: a hostile near, a blow in the last ten seconds, or the ruler up. The quiet counts down to the next one.</summary>
    public sealed class PackFarRule
    {
        public const double First = 6, Every = 45, Spread = 30;
        double due = First;
        public bool Admit(bool inDen, bool fighting, double dt, double roll)
        {
            if (!inDen) { due = First; return false; }
            if (fighting) return false;
            due -= dt;
            if (due > 0) return false;
            due = Every + Spread * roll;
            return true;
        }
    }
}
