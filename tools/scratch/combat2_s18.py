W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "balance/Harness/MapSim.cs": [
        ("""            // Onward: downhill on the way's distance to the ruler, a few metres ahead.
            var onward = Downhill(map, flow, p.X, p.Z, 7);""",
         """            // Onward: downhill on the way's distance to the ruler, a few metres ahead, by a line
            // that is clear of what stands on the ground.
            var onward = Onward(map, flow, b, p.X, p.Z);"""),
        ("""    /// <summary>`steps` cells downhill from here""",
         """    /// <summary>Of sixteen bearings, the clear one that most shortens the way to the ruler, three
    /// metres along it (a step round a stump, not into it).</summary>
    static (double X, double Z) Onward(MapBuild map, double[] d, Battle b, double x, double z)
    {
        var p = b.Player;
        double best = double.MaxValue, bx = x, bz = z;
        for (int k = 0; k < 16; k++)
        {
            double a = k * Math.Tau / 16, cx = Math.Cos(a), cz = Math.Sin(a);
            if (b.Collision.Blocked(x + cx * 0.6, z + cz * 0.6, p.Radius) || b.Collision.Blocked(x + cx * 1.4, z + cz * 1.4, p.Radius)) continue;
            double v = Math.Min(Flow(map, d, x + cx * 2.5, z + cz * 2.5), Flow(map, d, x + cx * 1.5, z + cz * 1.5) + 1);
            if (v < best) { best = v; bx = x + cx * 3; bz = z + cz * 3; }
        }
        return best == double.MaxValue ? Downhill(map, d, x, z, 7) : (bx, bz);
    }

    /// <summary>`steps` cells downhill from here"""),
    ],
}
