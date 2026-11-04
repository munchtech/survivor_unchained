using System;
using System.Collections.Generic;
using System.Text.Json;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Cinema;

/// <summary>
/// Whether a cinematic walks her through, or hands her back facing, something solid in its zone
/// (C04b put a handcart 1.2 m in front of where play begins). It reads the cues and the
/// zone's colliders only, so the tests can hold every cinematic to it without a scene.
/// </summary>
public static class CinePaths
{
    /// <summary>Her body's radius (Battle's player default).</summary>
    public const double HerRadius = 0.45;
    /// <summary>How far ahead of the end mark play needs clear, and to either side.</summary>
    public const double RunwayLength = 3.5, RunwayHalfWidth = 1.2;

    public sealed record Hit(ColliderDef Collider, string Where);

    /// <summary>Her route: the cast mark, then each of her "place" and "move" cues that names a
    /// mark, an [x, z] pair or {"abs": [x, y, z]}, in file order. A "to" that needs a scene (another
    /// actor, an offset) is added to <paramref name="skipped"/> and the walk carries on from the last point.</summary>
    public static List<(double X, double Z)> Route(CineFile f, List<string>? skipped = null)
    {
        var pts = new List<(double X, double Z)>();
        if (f.Cast.TryGetValue("her", out var cast) && cast.Mark is string start && f.Marks.ContainsKey(start))
        {
            var m = f.Mark(start);
            pts.Add((m.X, m.Z));
        }
        foreach (var shot in f.Shots)
            foreach (var c in shot.Cues)
            {
                if (c.Actor != "her" || c.Do is not ("move" or "place")) continue;
                var v = c.Get(c.Do == "move" ? "to" : "mark");
                if (Resolve(f, v) is { } p) pts.Add(p);
                else skipped?.Add($"{f.Id}/{shot.Id}: {c.Do} {v}");
            }
        return pts;
    }

    static (double X, double Z)? Resolve(CineFile f, JsonElement v)
    {
        switch (v.ValueKind)
        {
            case JsonValueKind.String:
                var name = v.GetString()!;
                if (!f.Marks.ContainsKey(name)) return null;
                var m = f.Mark(name);
                return (m.X, m.Z);
            case JsonValueKind.Array when v.GetArrayLength() == 2:
                return (v[0].GetDouble(), v[1].GetDouble());
            case JsonValueKind.Object when v.TryGetProperty("abs", out var a) && a.GetArrayLength() == 3:
                return (a[0].GetDouble(), a[2].GetDouble());
            default:
                return null;
        }
    }

    /// <summary>Every collider her walk crosses, or the runway ahead of her end mark crosses.</summary>
    public static List<Hit> Blockers(CineFile f, IReadOnlyList<ColliderDef> colliders, List<string>? skipped = null)
    {
        var hits = new List<Hit>();
        var route = Route(f, skipped);
        foreach (var c in colliders)
        {
            bool walk = false;
            for (int i = 0; i + 1 < route.Count && !walk; i++)
                walk = SegmentHits(c, route[i], route[i + 1], HerRadius);
            if (walk) hits.Add(new Hit(c, "walk"));
        }
        if (f.End.Her is string her && f.Marks.ContainsKey(her))
        {
            var m = f.Mark(her);
            // Heading as NpcActor turns: 0 faces south (+z), pi/2 east (+x).
            double dx = Math.Sin(m.Heading), dz = Math.Cos(m.Heading);
            foreach (var c in colliders)
                if (RunwayHits(c, m.X, m.Z, dx, dz)) hits.Add(new Hit(c, "runway"));
        }
        return hits;
    }

    static bool SegmentHits(ColliderDef c, (double X, double Z) a, (double X, double Z) b, double r)
    {
        double len = Math.Sqrt((b.X - a.X) * (b.X - a.X) + (b.Z - a.Z) * (b.Z - a.Z));
        int n = Math.Max(1, (int)Math.Ceiling(len / 0.1));
        for (int i = 0; i <= n; i++)
        {
            double t = (double)i / n;
            if (Overlaps(c, a.X + (b.X - a.X) * t, a.Z + (b.Z - a.Z) * t, r)) return true;
        }
        return false;
    }

    // The runway is a strip, tested as a grid of small discs across its width and along its length.
    static bool RunwayHits(ColliderDef c, double x, double z, double dx, double dz)
    {
        const double step = 0.2;
        for (double s = 0; s <= RunwayLength + 1e-9; s += step)
            for (double w = -RunwayHalfWidth; w <= RunwayHalfWidth + 1e-9; w += step)
                if (Overlaps(c, x + dx * s - dz * w, z + dz * s + dx * w, step * 0.71)) return true;
        return false;
    }

    // The same test CollisionWorld makes: a disc against a circle or an oriented box.
    static bool Overlaps(ColliderDef c, double x, double z, double r)
    {
        if (c.Kind == ColliderKind.Circle)
        {
            double dx = x - c.X, dz = z - c.Z;
            return dx * dx + dz * dz < (c.R + r) * (c.R + r);
        }
        double cos = Math.Cos(-c.Rot), sin = Math.Sin(-c.Rot);
        double lx = (x - c.X) * cos - (z - c.Z) * sin;
        double lz = (x - c.X) * sin + (z - c.Z) * cos;
        double qx = Math.Max(-c.Hw, Math.Min(c.Hw, lx)), qz = Math.Max(-c.Hd, Math.Min(c.Hd, lz));
        return (lx - qx) * (lx - qx) + (lz - qz) * (lz - qz) < r * r;
    }
}
