using System;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Text.Json;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her scapulae (Play/ScapRotation.cs, HerScap's math) against their Python twin, helpers.scap inside
/// helpers.drive(), on the fixture tools/anim/scap_parity_fixture.py writes (each upper arm swept from hanging to
/// overhead, the clavicle lift run first): A within 0.01 degrees, the angle within 0.01, the local rotation within
/// 1e-4 rad; the curve eased in without a kink; the game's rig_helpers.json carrying the same numbers.</summary>
public class ScapRotationTests
{
    static string Root()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? Directory.GetCurrentDirectory();
    }

    static JsonElement Load(params string[] rel) => JsonDocument.Parse(File.ReadAllText(Path.Combine(new[] { Root() }.Concat(rel).ToArray()))).RootElement;
    static Quaternion Q(JsonElement e) => new((float)e[0].GetDouble(), (float)e[1].GetDouble(), (float)e[2].GetDouble(), (float)e[3].GetDouble());
    static Vector3 V(JsonElement e) => new((float)e[0].GetDouble(), (float)e[1].GetDouble(), (float)e[2].GetDouble());

    static double Apart(Quaternion a, Quaternion b)
    {
        double ax = -a.X, ay = -a.Y, az = -a.Z, aw = a.W, bx = b.X, by = b.Y, bz = b.Z, bw = b.W;
        double w = aw * bw - ax * bx - ay * by - az * bz;
        double x = aw * bx + ax * bw + ay * bz - az * by;
        double y = aw * by - ax * bz + ay * bw + az * bx;
        double z = aw * bz + ax * by - ay * bx + az * bw;
        return 2 * Math.Atan2(Math.Sqrt(x * x + y * y + z * z), Math.Abs(w));
    }

    [Fact]
    public void MatchesPython()
    {
        var f = Load("tests", "fixtures", "scap_parity.json");
        Assert.Equal(ScapRotation.PerDeg, (float)f.GetProperty("per_deg").GetDouble(), 1e-5f);
        Assert.Equal(ScapRotation.From, (float)f.GetProperty("from").GetDouble(), 1e-5f);
        Assert.Equal(ScapRotation.Ease, (float)f.GetProperty("ease").GetDouble(), 1e-5f);
        Assert.Equal(ScapRotation.AxisLeft, V(f.GetProperty("axis")));
        int n = 0;
        foreach (var side in new[] { "l", "r" })
        {
            var sd = f.GetProperty("sides").GetProperty(side);
            Quaternion rest = Q(sd.GetProperty("rest")), grest = Q(sd.GetProperty("global_rest"));
            foreach (var fr in sd.GetProperty("frames").EnumerateArray())
            {
                var down = Vector3.Normalize(V(fr.GetProperty("pelvis")) - V(fr.GetProperty("neck")));
                float a = ScapRotation.ArmAngle(V(fr.GetProperty("upper")), V(fr.GetProperty("lower")), down);
                Assert.Equal(fr.GetProperty("A").GetDouble(), a, 0.01);
                float deg = ScapRotation.Angle(a);
                Assert.Equal(fr.GetProperty("deg").GetDouble(), deg, 0.01);
                var q = ScapRotation.Local(rest, grest, ScapRotation.Axis(side == "l"), deg);
                Assert.True(Apart(q, Q(fr.GetProperty("scap"))) < 1e-4, $"{side} A {a:0.0}");
                n++;
            }
        }
        Assert.True(n >= 20);
    }

    [Fact]
    public void EasedInNoKink()
    {
        Assert.Equal(0f, ScapRotation.Angle(50f));
        Assert.Equal(0f, ScapRotation.Angle(10f));
        Assert.True(ScapRotation.Angle(60f) < 1f);   // her idles and the Look: the shoulders as they were
        Assert.InRange(ScapRotation.Angle(115f), 22f, 23.2f);
        Assert.InRange(ScapRotation.Angle(150f), 37f, 38.2f);
        float prev = 0, prevSlope = 0;
        for (float a = 48f; a <= 182f; a += 1f)
        {
            float t = ScapRotation.Angle(a), slope = t - prev;
            Assert.True(slope >= 0f);
            if (a > 48f) Assert.True(MathF.Abs(slope - prevSlope) < 0.02f, $"kink at {a}");
            prev = t; prevSlope = slope;
        }
    }

    [Fact]
    public void BothSidesLiftTheirOuterEnd()
    {
        // a point out to each side of the pivot rises under a positive turn
        foreach (bool left in new[] { true, false })
        {
            var q = Quaternion.CreateFromAxisAngle(ScapRotation.Axis(left), 30f * MathF.PI / 180f);
            var p = Vector3.Transform(new Vector3(left ? 0.1f : -0.1f, 0f, 0f), q);
            Assert.True(p.Y > 0.04f, $"left {left}: {p}");
        }
    }

    [Fact]
    public void TheGameSpecCarriesTheSameNumbers()
    {
        var s = Load("art", "people", "rig_helpers.json").GetProperty("scap");
        Assert.Equal(ScapRotation.PerDeg, (float)s.GetProperty("per_deg").GetDouble(), 1e-5f);
        Assert.Equal(ScapRotation.From, (float)s.GetProperty("from").GetDouble(), 1e-5f);
        Assert.Equal(ScapRotation.Ease, (float)s.GetProperty("ease").GetDouble(), 1e-5f);
        Assert.Equal(ScapRotation.AxisLeft, V(s.GetProperty("axis")));
        Assert.Equal(ClavicleLift.ScapMax, (float)s.GetProperty("shrug_max").GetDouble(), 1e-5f);
        Assert.Equal(ClavicleLift.ScapRoll, (float)s.GetProperty("shrug_roll").GetDouble(), 1e-5f);
    }
}
