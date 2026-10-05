using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play.Story;

/* A story fight's place, as the fight needs it (docs/design/STORY_BOSSES.md):
 * a few spaces, each a union of capsules, joined at gates that open as the
 * stages are won, and the named points the fight is staged from (where she
 * comes in, where the named foe stands, the deadfalls, the den's mouth).
 *
 * This is the fight's ground, not its look. The arena's builder takes the
 * same outline (a union of shapes per space, as agreed with arena art), so
 * the place drawn and the place fought in are one; until it does, the walls
 * stand inside the old round arena. */

/// <summary>A capsule: the round-ended band from one point to another (a circle when they meet).</summary>
public readonly record struct Capsule(double X0, double Z0, double X1, double Z1, double R)
{
    public static Capsule Circle(double x, double z, double r) => new(x, z, x, z, r);

    /// <summary>Signed distance: negative inside.</summary>
    public double Dist(double x, double z)
    {
        double lx = X1 - X0, lz = Z1 - Z0, len2 = lx * lx + lz * lz;
        double t = len2 > 0 ? Math.Clamp(((x - X0) * lx + (z - Z0) * lz) / len2, 0, 1) : 0;
        double px = X0 + lx * t - x, pz = Z0 + lz * t - z;
        return Math.Sqrt(px * px + pz * pz) - R;
    }
}

public sealed record StorySpace(string Id, Capsule[] Shapes)
{
    public double Dist(double x, double z) => Shapes.Min(s => s.Dist(x, z));
}

/// <summary>A way between two spaces, shut until its stage is won, and the space it opens.</summary>
public sealed record StoryGate(string Id, double X0, double Z0, double X1, double Z1, string Into);

public sealed class StoryPlace
{
    public required StorySpace[] Spaces { get; init; }
    public StoryGate[] Gates { get; init; } = [];
    public required Dictionary<string, (double X, double Z)> Points { get; init; }

    public (double X, double Z) this[string point] => Points[point];
    public StorySpace Space(string id) => Spaces.First(s => s.Id == id);

    /// <summary>The rectangle it stands in, with a margin.</summary>
    public (double X0, double Z0, double X1, double Z1) Bounds(double margin = 3)
    {
        var all = Spaces.SelectMany(s => s.Shapes).ToList();
        return (all.Min(c => Math.Min(c.X0, c.X1) - c.R) - margin, all.Min(c => Math.Min(c.Z0, c.Z1) - c.R) - margin,
            all.Max(c => Math.Max(c.X0, c.X1) + c.R) + margin, all.Max(c => Math.Max(c.Z0, c.Z1) + c.R) + margin);
    }

    /// <summary>Signed distance to the place's edge: negative inside.</summary>
    public double Dist(double x, double z) => Spaces.Min(s => s.Dist(x, z));
    public bool Inside(double x, double z, double margin = 0) => Dist(x, z) < -margin;
    public bool In(string space, double x, double z, double margin = 0) => Space(space).Dist(x, z) < -margin;
    /// <summary>Inside one of the spaces open now (a leap or a blink is not carried over a shut gate).</summary>
    public bool Inside(double x, double z, double margin, IReadOnlySet<string> open) => Spaces.Any(s => open.Contains(s.Id) && s.Dist(x, z) < -margin);
    /// <summary>The space a point is in (the first, where they meet).</summary>
    public string? SpaceAt(double x, double z) => Spaces.FirstOrDefault(s => s.Dist(x, z) < 0)?.Id;

    /// <summary>The place's walls as a skin of posts round its outline: circles 0.8 m round, half a metre
    /// apart, their inner edge on the outline, and a second rank behind. A wall of square rows stepped a
    /// metre at a time down every diagonal, and her feet (and the bots') caught on each step; posts let her
    /// slide along a slant as along a straight.</summary>
    public List<(double X, double Z)> Posts()
    {
        var o = new List<(double, double)>();
        var (x0, z0, x1, z1) = Bounds(4);
        for (double z = Math.Floor(z0); z <= z1; z += 0.5)
            for (double x = Math.Floor(x0); x <= x1; x += 0.5)
            {
                double d = Dist(x, z);
                // The skin: inner edges on the outline. Behind it, a coarser rank, so nothing is thin.
                if (d > 0.55 && d <= 1.05 || d > 1.6 && d <= 2.6 && ((int)Math.Round(x * 2) + (int)Math.Round(z * 2)) % 2 == 0) o.Add((x, z));
            }
        return o;
    }

    /// <summary>Stands its walls and shuts its gates in a fight's collision.</summary>
    public void Build(CollisionWorld c)
    {
        foreach (var (x, z) in Posts()) c.AddCircle(x, z, 0.8, new ColliderOpts(Tag: "place"));
        foreach (var g in Gates) Shut(c, g);
    }

    /// <summary>A gate's posts: close-set, two metres past its ends so it meets the walls.</summary>
    public static void Shut(CollisionWorld c, StoryGate g)
    {
        double lx = g.X1 - g.X0, lz = g.Z1 - g.Z0, len = Math.Max(0.01, Math.Sqrt(lx * lx + lz * lz));
        int n = (int)Math.Ceiling((len + 4) / 1.1);
        for (int i = 0; i <= n; i++)
        {
            double t = -2 / len + i * (len + 4) / n / len;
            c.AddCircle(g.X0 + lx * t, g.Z0 + lz * t, 0.8, new ColliderOpts(Tag: $"gate:{g.Id}"));
        }
    }

    public static void Open(CollisionWorld c, StoryGate g) => c.RemoveTagged($"gate:{g.Id}");
}
