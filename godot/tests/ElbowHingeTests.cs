using System;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Text.Json;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her elbow share and point's half-bend about their own hinge (Play/ElbowHinge.cs, HerJoints' math) against
/// its Python twin, helpers.drive(), on the fixture tools/anim/elbow_parity_fixture.py writes: forearm poses bent
/// 0..150 deg about and off the hinge, some rolled. Every hinged helper within 1e-4 rad; and the game's
/// rig_helpers.json marking them "hinge": true.</summary>
public class ElbowHingeTests
{
    const double Tol = 1e-4;   // radians

    static string Root()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? Directory.GetCurrentDirectory();
    }

    static JsonElement Load(params string[] rel) => JsonDocument.Parse(File.ReadAllText(Path.Combine(new[] { Root() }.Concat(rel).ToArray()))).RootElement;

    static Quaternion Q(JsonElement e) => new((float)e[0].GetDouble(), (float)e[1].GetDouble(), (float)e[2].GetDouble(), (float)e[3].GetDouble());

    static double Apart(Quaternion a, Quaternion b)
    {
        double ax = -a.X, ay = -a.Y, az = -a.Z, aw = a.W, bx = b.X, by = b.Y, bz = b.Z, bw = b.W;
        double w = aw * bw - ax * bx - ay * by - az * bz;
        double x = aw * bx + ax * bw + ay * bz - az * by;
        double y = aw * by - ax * bz + ay * bw + az * bx;
        double z = aw * bz + ax * by - ay * bx + az * bw;
        return 2 * Math.Atan2(Math.Sqrt(x * x + y * y + z * z), Math.Abs(w));
    }

    [Theory]
    [InlineData("l")]
    [InlineData("r")]
    public void HingeMatchesPython(string side)
    {
        var fx = Load("tests", "fixtures", "elbow_hinge_parity.json");
        Assert.True(fx.GetProperty("max_old_vs_new_deg").GetDouble() > 5.0);
        var s = fx.GetProperty("sides").GetProperty(side);
        var rest = Q(s.GetProperty("rest"));
        var hs = s.GetProperty("helpers");
        Assert.Equal(2, hs.EnumerateObject().Count());
        int f = 0;
        foreach (var fr in s.GetProperty("frames").EnumerateArray())
        {
            var pose = Q(fr.GetProperty("pose"));
            foreach (var h in fr.GetProperty("helpers").EnumerateObject())
            {
                var info = hs.GetProperty(h.Name);
                double e = Apart(ElbowHinge.Share(rest, pose, (float)info.GetProperty("amount").GetDouble(), Q(info.GetProperty("own"))), Q(h.Value));
                Assert.True(e < Tol, $"{side} f{f} {h.Name}: {e:E2} rad off");
            }
            f++;
        }
        Assert.True(f >= 20);
    }

    [Fact]
    public void GameSpecMarksTheHingedShares()
    {
        var spec = Load("art", "people", "rig_helpers.json");
        foreach (var n in new[] { "lowerarm_share_{s}", "lowerarm_point_{s}" })
        {
            var h = spec.GetProperty("helpers").EnumerateArray().First(x => x.GetProperty("name").GetString() == n);
            Assert.True(h.TryGetProperty("hinge", out var v) && v.GetBoolean(), n);
        }
        foreach (var n in new[] { "upperarm_share_{s}", "calf_share_{s}" })
        {
            var h = spec.GetProperty("helpers").EnumerateArray().FirstOrDefault(x => x.GetProperty("name").GetString() == n);
            if (h.ValueKind == JsonValueKind.Object) Assert.False(h.TryGetProperty("hinge", out _), n);
        }
    }
}
