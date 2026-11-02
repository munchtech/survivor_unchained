using SurvivorUnchained.World;
using Xunit;

public class GroundSkirtTests
{
    [Fact]
    public void SkirtRingsTheFieldAtItsEdgeHeights()
    {
        int n = 5; float step = 2, half = (n - 1) * step / 2;
        var h = new float[n * n];
        for (int k = 0; k < h.Length; k++) h[k] = k * 0.1f;
        var (xyz, idx) = GroundSkirt.Build(n, half, step, h, 10);
        Assert.Equal((4 * n + 4) * 3, xyz.Length);
        Assert.Equal((4 * (n - 1) + 4) * 6, idx.Length);
        int nv = n * n + 4 * n + 4;
        foreach (var i in idx) Assert.InRange(i, 0, nv - 1);
        // Every skirt vertex sits out at the margin on at least one axis, at an edge vertex's height.
        for (int v = 0; v < xyz.Length / 3; v++)
        {
            float x = xyz[v * 3], y = xyz[v * 3 + 1], z = xyz[v * 3 + 2];
            Assert.True(System.Math.Abs(x) == half + 10 || System.Math.Abs(z) == half + 10);
            int i = (int)System.Math.Round((System.Math.Clamp(x, -half, half) + half) / step);
            int j = (int)System.Math.Round((System.Math.Clamp(z, -half, half) + half) / step);
            Assert.Equal(h[j * n + i], y);
        }
        // Wound as the field (a, b, c with c - a crossed into b - a pointing down: Godot's clockwise front from above).
        System.Numerics.Vector3 P(int i) => i < n * n
            ? new(-half + (i % n) * step, h[i], -half + (i / n) * step)
            : new(xyz[(i - n * n) * 3], xyz[(i - n * n) * 3 + 1], xyz[(i - n * n) * 3 + 2]);
        var f0 = System.Numerics.Vector3.Cross(P(1) - P(0), P(n) - P(0));   // the field's own first triangle (a, b, c ordering)
        for (int t = 0; t < idx.Length; t += 3)
        {
            var c = System.Numerics.Vector3.Cross(P(idx[t + 1]) - P(idx[t]), P(idx[t + 2]) - P(idx[t]));
            Assert.True(c.Y * f0.Y > 0, $"triangle {t / 3} wound the other way");
        }
    }

    [Fact]
    public void FloraMirrorsOutNearTheEdgeAndFrays()
    {
        Assert.Empty(GroundSkirt.MirrorOut(0, 0, 145));
        int far = 0, near = 0;
        for (int k = 0; k < 400; k++)
        {
            float z = -100 + k * 0.5f;
            foreach (var (x, cz, _) in GroundSkirt.MirrorOut(-144.5f, z, 145))
            {
                Assert.InRange(-145 - x, GroundSkirt.Gap, GroundSkirt.Gap + GroundSkirt.Push);   // never on the edge line
                Assert.InRange(cz - z, -GroundSkirt.Slide, GroundSkirt.Slide);
            }
            near += GroundSkirt.MirrorOut(-140, z, 145).Count;                 // 5 m in: always copied
            far += GroundSkirt.MirrorOut(-118, z, 145).Count;                  // 27 m in: mostly dropped
        }
        Assert.Equal(400, near);
        Assert.InRange(far, 0, 60);
        Assert.Equal(3, GroundSkirt.MirrorOut(143, 143, 145).Count);           // a corner: both edges and the diagonal
        Assert.True(GroundSkirt.Mirrors("pine") && !GroundSkirt.Mirrors("rock") && !GroundSkirt.Mirrors("dead") && !GroundSkirt.Mirrors("pebble"));
    }
}
