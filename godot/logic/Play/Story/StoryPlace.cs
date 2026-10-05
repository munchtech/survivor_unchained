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

/// <summary>A way between two spaces, shut until its stage is won.</summary>
public sealed record StoryGate(string Id, double X0, double Z0, double X1, double Z1);

public sealed class StoryPlace
{
    public required StorySpace[] Spaces { get; init; }
    public StoryGate[] Gates { get; init; } = [];
    public required Dictionary<string, (double X, double Z)> Points { get; init; }

    public (double X, double Z) this[string point] => Points[point];
    public StorySpace Space(string id) => Spaces.First(s => s.Id == id);

    /// <summary>Signed distance to the place's edge: negative inside.</summary>
    public double Dist(double x, double z) => Spaces.Min(s => s.Dist(x, z));
    public bool Inside(double x, double z, double margin = 0) => Dist(x, z) < -margin;
    public bool In(string space, double x, double z, double margin = 0) => Space(space).Dist(x, z) < -margin;

    /// <summary>The place's walls: a band 2.5 m thick round its outline, as boxes a metre deep
    /// (one per run of wall along each row), so everything (her, the crowd, a thrown pot's
    /// lander) keeps inside it.</summary>
    public List<(double X, double Z, double Hw, double Hd)> Walls()
    {
        var o = new List<(double, double, double, double)>();
        double x0 = Spaces.SelectMany(s => s.Shapes).Min(c => Math.Min(c.X0, c.X1) - c.R) - 4, x1 = Spaces.SelectMany(s => s.Shapes).Max(c => Math.Max(c.X0, c.X1) + c.R) + 4;
        double z0 = Spaces.SelectMany(s => s.Shapes).Min(c => Math.Min(c.Z0, c.Z1) - c.R) - 4, z1 = Spaces.SelectMany(s => s.Shapes).Max(c => Math.Max(c.Z0, c.Z1) + c.R) + 4;
        for (double z = Math.Floor(z0); z < z1; z += 1)
        {
            double? from = null;
            for (double x = Math.Floor(x0); x <= x1 + 1; x += 1)
            {
                double d = Dist(x + 0.5, z + 0.5);
                bool wall = d >= 0 && d < 2.5 && x <= x1;
                if (wall && from == null) from = x;
                else if (!wall && from is double f)
                {
                    o.Add(((f + x) / 2, z + 0.5, (x - f) / 2, 0.5));
                    from = null;
                }
            }
        }
        return o;
    }

    /// <summary>Stands its walls and shuts its gates in a fight's collision.</summary>
    public void Build(CollisionWorld c)
    {
        foreach (var (x, z, hw, hd) in Walls()) c.AddBox(x, z, hw, hd, 0, new ColliderOpts(Tag: "place"));
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
