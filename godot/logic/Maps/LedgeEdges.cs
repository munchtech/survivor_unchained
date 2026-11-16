using System;
using System.Collections.Generic;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Maps;

/* Where a dungeon's wall is a drop (ledge view lead, 15 Nov; data/content/ledge.json "edges"). A foe forced over a drop dies of it
 * (Sim/LedgeKills.cs); a wall that rises stops it as every wall does. Which is which follows what the play camera sees: the view
 * (src/World/DungeonWalls.cs Ctx.HLoc) raises the den's banks on every side and sinks its holes into pits, and in the ravine raises
 * only the back cliff with rock behind it, the near and side edges, the holes and any back wall with a hall behind it falling away.
 * Each unwalkable cell by the way is given its edge's kind here from the same two fields the view builds by (the walls' and the
 * holes'), at the view's own thresholds; the data names the kinds that drop, per dungeon. */
public enum EdgeKind { Hole, Near, Side, BackOpen, Back }

public static class LedgeEdges
{
    public sealed class Rule { public List<string> Drops = new(); public double HoleGap; }
    public sealed class Kinds { public double NearFrom = 0.475, SideFrom = 0.625, OpenProbe = 18, OpenFrom = 13; }
    sealed class File { public Dictionary<string, Rule> Edges = new(); public Kinds Kinds = new(); }
    static File? file;
    static File F => file ??= Json.Parse<File>(Json.ReadContent("ledge.json"));

    static readonly Rule None = new();
    /// <summary>The dungeon's rule (a dungeon the file does not name drops nowhere).</summary>
    public static Rule For(string dungeon) => F.Edges.TryGetValue(dungeon, out var r) ? r : None;

    public static string Key(EdgeKind k) => k switch { EdgeKind.Hole => "hole", EdgeKind.Near => "near", EdgeKind.Side => "side", EdgeKind.BackOpen => "backOpen", _ => "back" };
    public static bool Drops(Rule r, EdgeKind k) => r.Drops.Contains(Key(k));

    /// <summary>The kind of edge cell (i, j) lies by, from the walls' field (metres in from the rooms' and halls' edge, negative
    /// outside) and the holes' (metres outside the nearest hole), res by res, 1 m apart; half the cells to a side.</summary>
    public static EdgeKind KindAt(double[] wallIn, double[] holeD, int res, int i, int j, Rule r)
    {
        var k = F.Kinds;
        double W(int a, int b) => Math.Clamp(wallIn[Math.Clamp(b, 0, res - 1) * res + Math.Clamp(a, 0, res - 1)], -16, 8);
        double H(int a, int b) => Math.Clamp(holeD[Math.Clamp(b, 0, res - 1) * res + Math.Clamp(a, 0, res - 1)], -8, 8);
        double wf = W(i, j), hf = H(i, j);
        if (hf - wf < r.HoleGap) return EdgeKind.Hole;
        // The outward way (up the walls' field's fall): +z is toward the lens.
        double gx = W(i - 1, j) - W(i + 1, j), gz = W(i, j - 1) - W(i, j + 1), gl = Math.Sqrt(gx * gx + gz * gz);
        if (gl < 1e-9) { gx = 0; gz = 1; } else { gx /= gl; gz /= gl; }
        if (gz > k.NearFrom) return EdgeKind.Near;
        if (Math.Abs(gx) > k.SideFrom) return EdgeKind.Side;
        // The cliff stands only where the rock goes on behind it (the view's S = -min(walls, holes), probed openProbe north).
        double S(int a, int b) => -Math.Min(W(a, b), H(a, b));
        int probe = (int)Math.Round(k.OpenProbe);
        return S(i, j - probe) - S(i, j) < k.OpenFrom ? EdgeKind.BackOpen : EdgeKind.Back;
    }
}
