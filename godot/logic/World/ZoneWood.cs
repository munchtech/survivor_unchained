using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.World;

/// <summary>
/// The zones' round colliders came out of the web game's export, some for flora the view no longer draws (the owner, 19 Nov:
/// "lots of trees seemed to stop my movement with a wall" / "a corner or two I couldn't get by with invisible wall"). Applied
/// on load, from what the zone draws (flora.json + flora.bin, props.json, props_own.json): a small plain round collider
/// (under 1 m) with nothing drawn within r + 0.5 m is dropped, unless a "solid" notch fill sits within 1.5 m of it (the fills
/// were fitted to it). Big ones (cliff lines, boulders) and every tagged collider stay. Trees are NOT shrunk to the trunk:
/// WalkNotchTests (the owner, 18 Nov) fail with nine new dead-end notches on the Low Ford road when they are. Pure and deterministic.
/// </summary>
public static class ZoneWood
{
    public const double Trunk = 0.3, MinTrunk = 0.25, OrphanMaxR = 1.0, DrawnReach = 0.5;
    static readonly HashSet<string> TreeKinds = new() { "pine", "broadleaf", "autumn", "dead" };
    static readonly HashSet<string> Logged = new();

    public readonly record struct Result(int Trees, int Orphans, int Kept);

    public static void Apply(ZoneMeta z, string id)
    {
        var r = Trim(z, id);
        if (r is { } res && Logged.Add(id))
            Console.WriteLine($"collision: {id} {res.Orphans} orphans dropped of {res.Kept + res.Orphans} (trees left at export size)");
    }

    static Result? Trim(ZoneMeta z, string id)
    {
        var drawn = new List<(string Kind, double X, double Z, double S)>();
        try
        {
            using var fl = JsonDocument.Parse(DataFiles.Text($"zones/{id}/flora.json"));
            var bytes = DataFiles.Bytes($"zones/{id}/flora.bin");
            var f = new float[bytes.Length / 4];
            Buffer.BlockCopy(bytes, 0, f, 0, bytes.Length);
            int at = 0;
            foreach (var g in fl.RootElement.EnumerateArray())
            {
                string kind = g.GetProperty("kind").GetString() ?? "";
                int n = g.GetProperty("count").GetInt32();
                for (int i = 0; i < n && at + 12 <= f.Length; i++, at += 12)
                    drawn.Add((kind, f[at + 9], f[at + 11], Math.Sqrt((double)f[at] * f[at] + (double)f[at + 1] * f[at + 1] + (double)f[at + 2] * f[at + 2])));
            }
        }
        catch { return null; }  // no flora to match: leave the colliders as they are
        foreach (var (x, zz) in PropSpots(id)) drawn.Add(("prop", x, zz, 1));

        var cell = new Dictionary<(int, int), List<int>>();
        for (int i = 0; i < drawn.Count; i++)
        {
            var key = ((int)Math.Floor(drawn[i].X / 4), (int)Math.Floor(drawn[i].Z / 4));
            if (!cell.TryGetValue(key, out var l)) cell[key] = l = new List<int>();
            l.Add(i);
        }
        int trees = 0, orphans = 0;
        var fills = z.Colliders.Where(c => c.Tag == "solid" && c.Kind == ColliderKind.Box).ToList();
        var keep = new List<ColliderDef>(z.Colliders.Count);
        foreach (var c in z.Colliders)
        {
            if (c.Kind != ColliderKind.Circle || c.Tag != null || c.R >= OrphanMaxR) { keep.Add(c); continue; }
            double reach = c.R + DrawnReach;
            int best = -1; double bd = double.MaxValue;
            for (int i = (int)Math.Floor((c.X - reach) / 4); i <= (int)Math.Floor((c.X + reach) / 4); i++)
                for (int j = (int)Math.Floor((c.Z - reach) / 4); j <= (int)Math.Floor((c.Z + reach) / 4); j++)
                    if (cell.TryGetValue((i, j), out var l))
                        foreach (var k in l)
                        {
                            double d = Math.Sqrt((drawn[k].X - c.X) * (drawn[k].X - c.X) + (drawn[k].Z - c.Z) * (drawn[k].Z - c.Z));
                            if (d <= reach && d < bd) { bd = d; best = k; }
                        }
            // (a "solid" fill laid between props - props_own.json, WalkNotchTests - was fitted to the pieces about it, a
            // hidden one too: an orphan within 1.5 m of a fill stays)
            if (best < 0 && !fills.Any(f => Math.Abs(f.X - c.X) < 1.5 + Math.Max(f.Hw, f.Hd) && Math.Abs(f.Z - c.Z) < 1.5 + Math.Max(f.Hw, f.Hd))) { orphans++; continue; }
            keep.Add(c);
        }
        z.Colliders = keep;
        return new Result(trees, orphans, keep.Count);
    }

    /// <summary>Where the zone puts props: props.json's transforms and props_own.json's "place" entries.</summary>
    static IEnumerable<(double, double)> PropSpots(string id)
    {
        var spots = new List<(double, double)>();
        try
        {
            using var doc = JsonDocument.Parse(DataFiles.Text($"zones/{id}/props.json"));
            foreach (var p in doc.RootElement.EnumerateArray())
                if (p.TryGetProperty("t", out var t) && t.GetArrayLength() >= 12) spots.Add((t[9].GetDouble(), t[11].GetDouble()));
        }
        catch { }
        try
        {
            using var doc = JsonDocument.Parse(DataFiles.Text($"zones/{id}/props_own.json"));
            if (doc.RootElement.TryGetProperty("place", out var place) && place.ValueKind == JsonValueKind.Array)
                foreach (var p in place.EnumerateArray())
                    spots.Add((p.TryGetProperty("x", out var x) ? x.GetDouble() : 0, p.TryGetProperty("z", out var zz) ? zz.GetDouble() : 0));
        }
        catch { }
        return spots;
    }
}
