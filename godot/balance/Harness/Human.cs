using System;
using System.Collections.Generic;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Balance;

/// <summary>A human's hands, late (H1 combat teeth, docs/team/hook/H1_combat_teeth.md item 1): the Pilot knows every
/// mark the moment it is made and answers it at once, and a player does neither. These hands see each threat (a
/// marked blow, a champion's windup, a lobbed pot, burning ground, a crowd's marked circle) only after a reaction
/// time (350-500 ms, drawn once a night), and read only some of them at all (60% attentive, 40% careless): a threat
/// unread is walked through as if it were not there, and ground unread is stood in. While the most urgent threat
/// near her is read and seen, the hands are the deft Pilot's (they know what to do); otherwise the plain, naive
/// Pilot's. The careless hands also never save the Flare for a boss. Their own dice: the sim's are never touched,
/// so a night's world is the same night the plain hands played.
/// H6 (item 2): the read share is by threat. The kit's telegraphs (Sim/Tells.cs: a blow with a Tell, a closing round her)
/// are made to be read, at 85% (careless 65%); a fodder's or champion's lunge windup is a flicker in the crowd, at 50%
/// (careless 30%); a boss's marks, the creatures' strikes and burning ground keep Reads.</summary>
public sealed class Human
{
    public readonly double React, Reads, KitReads, LungeReads;
    public readonly bool Careless;
    /// <summary>H6's idler: the human's eyes and reaction, but it stands unless a read threat moves it.</summary>
    public bool Idle;
    readonly Rng rng;
    readonly Dictionary<string, (double Seen, bool Read)> seen = new();
    double sweep;
    /// <summary>Threats met, and read (for the report: the dodge share the hands played at).</summary>
    public int Met, Read;

    public Human(int seed, bool careless)
    {
        rng = new Rng((uint)(seed * 104729 + 77));
        Careless = careless;
        React = careless ? 0.45 + 0.15 * rng.Next() : 0.35 + 0.15 * rng.Next();
        Reads = careless ? 0.4 : 0.6;
        KitReads = careless ? 0.65 : 0.85;
        LungeReads = careless ? 0.3 : 0.5;
    }

    (double Seen, bool Read) Look(string key, double now, double reads)
    {
        if (!seen.TryGetValue(key, out var s))
        {
            s = (now, rng.Next() < reads);
            seen[key] = s;
            Met++;
            if (s.Read) Read++;
        }
        return s;
    }

    /// <summary>Whether the hands answer the most urgent threat round her now (read, and seen for the reaction time).</summary>
    public bool Aware(Battle b)
    {
        var p = b.Player;
        double now = b.Time;
        string? key = null;
        double left = double.MaxValue, reads = Reads;
        void Consider(string k, double l, double r) { if (l < left) { left = l; key = k; reads = r; } }
        foreach (var bl in b.Blows)
            if (bl.Hit(p.X, p.Z, p.Radius + 4)) Consider($"b{bl.MarkId}", bl.T, bl.Tell != null ? KitReads : Reads);
        foreach (var t in b.ActiveTells)
            if (t.Kind == "closing" && (!t.Landed || t.RushLeft > 0 || t.Walled) && Dist(t.Blow.X, t.Blow.Z, p.X, p.Z) < t.Blow.Radius + 1)
                Consider($"c{t.Blow.MarkId}", t.Landed ? 0.05 : t.Blow.T, KitReads);
        foreach (var s in b.EnemyStrikes())
            if (Dist(s.X, s.Z, p.X, p.Z) < s.R + p.Radius + 3) Consider($"s{Math.Round(s.X, 1)}:{Math.Round(s.Z, 1)}:{Math.Round(now - (s.Marked - s.Left), 1)}", s.Left, Reads);
        foreach (var e in b.Enemies.Living())
        {
            if (e.Disposition != Disposition.Hostile) continue;
            if (e.State == EnemyState.Windup && (e.Def.Charge ?? e.Def.Lunge) != null && Dist(e.X, e.Z, p.X, p.Z) < 9)
                Consider($"w{e.Id}:{Math.Round(now + e.StateT, 1)}", e.StateT, e.Boss ? Reads : LungeReads);
            else if (e.State == EnemyState.Casting && e.Cast == CastKind.Aim && Dist(e.X, e.Z, p.X, p.Z) < e.AimReach + 3)
                Consider($"a{e.Id}:{Math.Round(now + e.StateT, 1)}", e.StateT, Reads);
        }
        foreach (var z in b.Zones.Living())
            if (z.Owner is Side.Enemy or Side.World && Dist(z.X, z.Z, p.X, p.Z) < z.Radius + p.Radius + 1)
                Consider($"z{z.Id}:{Math.Round(now - z.Age, 1)}", 0.5, Reads);
        if (now - sweep > 20) { sweep = now; Sweep(now); }
        if (key == null) return false;
        var look = Look(key, now, reads);
        return look.Read && now - look.Seen >= React;
    }

    void Sweep(double now)
    {
        var old = new List<string>();
        foreach (var kv in seen) if (now - kv.Value.Seen > 30) old.Add(kv.Key);
        foreach (var k in old) seen.Remove(k);
    }

    /// <summary>The hands' move this step: the deft Pilot's while aware, else the plain Pilot's reading nothing.</summary>
    /// <param name="goal">Where the night wants her (a board's lamp held: Harness/LampHold.cs), or null.</param>
    /// <param name="onward">On a walk (a map, the day road): where the way goes on (Pilot.Steer's onward).</param>
    public (double X, double Z) Steer(Battle b, ArenaBoss? boss, (double X, double Z)? goal = null, (double X, double Z)? onward = null)
    {
        bool aware = Aware(b);
        lastAware = aware;
        // H6's idler (the owner's demo-rc2 play): stands where it is (or walks to the night's goal, the lamp) and
        // steps only out of what it has read; nothing else moves it.
        if (Idle && !aware) return goal is var (gx, gz) && Math.Sqrt((gx - b.Player.X) * (gx - b.Player.X) + (gz - b.Player.Z) * (gz - b.Player.Z)) > 1.2 ? Pilot.Steer(b, false, null, goal: goal, naive: true) : (0, 0);
        return aware ? Pilot.Steer(b, true, boss, goal: goal, onward: onward) : Pilot.Steer(b, false, null, goal: goal, naive: true, onward: onward);
    }
    bool lastAware;

    /// <summary>The hands that are not the feet, as the Pilot's, with a champion's lunge dashed only when read and seen,
    /// and (careless) no Flare saved for a boss.</summary>
    public bool Act(Battle b, Journey j, double mx, double mz, ArenaBoss? boss) =>
        Pilot.Act(b, j, mx, mz, boss, lunges: lastAware, aimsFlare: !Careless, rooted: lastAware, presses: Hands == null && !Careless && !Idle, hands: Hands);
    /// <summary>(M3) The hands on the press plan (campaign): pressed through this human's React; null, the old presses.</summary>
    public PressHands? Hands;

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));
}
