using System;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Text.Json;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her shoulder helpers (Play/ShoulderHelpers.cs, HerShoulder's math) against their Python twin,
/// helpers.shoulder_helper, on the fixture tools/anim/shoulder_parity_fixture.py writes (per helper, 12 arm angles, the
/// parent and upper arm posed by seeded turns and moves): rotation within 1e-4 rad, scale within 1e-5, position within
/// 1e-6 m; g exactly 0 below 60 degrees (the parent-following rest pose); continuous across 60 and 120; the game's
/// rig_helpers.json carrying the same numbers.</summary>
public class ShoulderHelpersTests
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

    static ShoulderHelpers.Kind KindOf(JsonElement h) => ShoulderHelpers.All.Single(k => k.Name == h.GetProperty("kind").GetString());
    static bool LeftOf(JsonElement h) => h.GetProperty("side").GetString() == "l";
    static Vector3? T0Of(JsonElement h) => h.GetProperty("T0").ValueKind == JsonValueKind.Null ? null : V(h.GetProperty("T0"));

    static (Quaternion, Vector3, Vector3) PoseAt(JsonElement h, JsonElement c, float a, Quaternion? mp = null, Vector3? op = null) =>
        ShoulderHelpers.Pose(KindOf(h),
            mp ?? Q(c.GetProperty("Mp")[0]), op ?? V(c.GetProperty("Mp")[1]), Q(h.GetProperty("Gp0")[0]), V(h.GetProperty("Gp0")[1]),
            Q(h.GetProperty("G0")[0]), V(h.GetProperty("G0")[1]),
            Q(c.GetProperty("Mon")[0]), V(c.GetProperty("Mon")[1]), Q(h.GetProperty("Gon0")[0]), V(h.GetProperty("Gon0")[1]),
            T0Of(h), (float)h.GetProperty("L0").GetDouble(), ShoulderHelpers.Off(KindOf(h), LeftOf(h)), a);

    [Fact]
    public void MatchesPython()
    {
        var f = Load("tests", "fixtures", "shoulder_parity.json");
        double worstRot = 0, worstScale = 0, worstPos = 0;
        int n = 0;
        foreach (var hp in f.GetProperty("helpers").EnumerateObject())
        {
            var h = hp.Value;
            var kind = KindOf(h);
            bool left = LeftOf(h);
            Vector3 u0 = V(h.GetProperty("upper0")), e0 = V(h.GetProperty("lower0")), g0 = V(h.GetProperty("G0")[1]);
            // the rest data the C# derives itself must be the Python one
            Assert.True((ShoulderHelpers.Pivot(kind, left, u0, e0) - g0).Length() < 1e-6f, hp.Name + " pivot");
            var (t0, l0) = ShoulderHelpers.RestAim(kind, left, u0, e0, g0);
            var want = T0Of(h);
            if (want == null) Assert.Null(t0);
            else
            {
                Assert.True((t0!.Value - want.Value).Length() < 1e-6f, hp.Name + " T0");
                Assert.Equal(h.GetProperty("L0").GetDouble(), l0, 1e-6);
            }
            Assert.True((ShoulderHelpers.Off(kind, left) - V(h.GetProperty("off"))).Length() < 1e-7f, hp.Name + " off");
            foreach (var c in h.GetProperty("cases").EnumerateArray())
            {
                var (q, s, p) = PoseAt(h, c, (float)c.GetProperty("A").GetDouble());
                string at = $"{hp.Name} A {c.GetProperty("A").GetDouble()}";
                double dr = Apart(q, Q(c.GetProperty("rot"))), ds = (s - V(c.GetProperty("scale"))).Length(), dp = (p - V(c.GetProperty("pos"))).Length();
                Assert.True(dr < 1e-4, $"{at} rot {dr}");
                Assert.True(ds < 1e-5, $"{at} scale {ds}");
                Assert.True(dp < 1e-6, $"{at} pos {dp}");
                worstRot = Math.Max(worstRot, dr); worstScale = Math.Max(worstScale, ds); worstPos = Math.Max(worstPos, dp);
                n++;
            }
        }
        Assert.Equal(8 * 12, n);
        Console.WriteLine($"shoulder parity max: rot {worstRot:E2} rad, scale {worstScale:E2}, pos {worstPos:E2} m");
    }

    [Fact]
    public void BelowSixtyTheHelperJustFollowsItsParent()
    {
        var f = Load("tests", "fixtures", "shoulder_parity.json");
        foreach (var hp in f.GetProperty("helpers").EnumerateObject())
        {
            var h = hp.Value;
            Quaternion rp0 = Q(h.GetProperty("Gp0")[0]), rh0 = Q(h.GetProperty("G0")[0]);
            Vector3 op0 = V(h.GetProperty("Gp0")[1]), oh0 = V(h.GetProperty("G0")[1]);
            // the rest local pose: inv(Rp0) * Rh0 and inv(Rp0) * (pivot - Op0); System.Numerics concatenates a then b
            var restRot = Quaternion.Concatenate(rh0, Quaternion.Conjugate(rp0));
            var restPos = Vector3.Transform(oh0 - op0, Quaternion.Conjugate(rp0));
            foreach (var c in h.GetProperty("cases").EnumerateArray().Where(c => c.GetProperty("A").GetDouble() < 60))
            {
                Assert.Equal(0f, ShoulderHelpers.G((float)c.GetProperty("A").GetDouble()));
                var (q, s, p) = PoseAt(h, c, (float)c.GetProperty("A").GetDouble());
                Assert.True(Apart(q, restRot) < 1e-5, hp.Name);
                Assert.True((s - Vector3.One).Length() < 1e-7f, hp.Name);
                Assert.True((p - restPos).Length() < 1e-6f, hp.Name);
            }
        }
    }

    [Fact]
    public void ContinuousAcrossTheEdges()
    {
        Assert.Equal(0f, ShoulderHelpers.G(60f));
        Assert.Equal(1f, ShoulderHelpers.G(120f));
        Assert.Equal(1f, ShoulderHelpers.G(170f));
        Assert.True(ShoulderHelpers.G(60.01f) < 1e-6f && ShoulderHelpers.G(119.99f) > 1f - 1e-6f);
        foreach (var hp in Load("tests", "fixtures", "shoulder_parity.json").GetProperty("helpers").EnumerateObject())
        {
            var h = hp.Value;
            var c = h.GetProperty("cases")[8];   // an arm raised, the parent and upper arm posed
            foreach (float edge in new[] { 60f, 120f })
            {
                var lo = PoseAt(h, c, edge - 0.01f); var hi = PoseAt(h, c, edge + 0.01f);
                Assert.True(Apart(lo.Item1, hi.Item1) < 1e-3, hp.Name + " rot " + edge);
                Assert.True((lo.Item2 - hi.Item2).Length() < 1e-3f, hp.Name + " scale " + edge);
                Assert.True((lo.Item3 - hi.Item3).Length() < 1e-4f, hp.Name + " pos " + edge);
            }
        }
    }

    [Fact]
    public void TheGameSpecCarriesTheSameNumbers()
    {
        var s = Load("art", "people", "rig_helpers.json").GetProperty("shoulder");
        Assert.Equal(ShoulderHelpers.A0, (float)s.GetProperty("A")[0].GetDouble(), 1e-5f);
        Assert.Equal(ShoulderHelpers.A1, (float)s.GetProperty("A")[1].GetDouble(), 1e-5f);
        foreach (var k in ShoulderHelpers.All)
        {
            var c = s.GetProperty("bones").GetProperty(k.Name);
            Assert.Equal(k.Parent, c.GetProperty("parent").GetString());
            Assert.Equal(k.On, c.GetProperty("on").GetString());
            Assert.Equal(k.Follow, (float)c.GetProperty("follow").GetDouble(), 1e-6f);
            Assert.Equal(k.Ka, (float)c.GetProperty("ka").GetDouble(), 1e-6f);
            Assert.Equal(k.Kp, (float)c.GetProperty("kp").GetDouble(), 1e-6f);
            Assert.Equal(k.Sa, (float)c.GetProperty("sa").GetDouble(), 1e-6f);
            Assert.Equal(k.Sp, (float)c.GetProperty("sp").GetDouble(), 1e-6f);
            Assert.Equal(k.Off, V(c.GetProperty("off")));
            var pv = c.GetProperty("pivot");
            if (pv[0].ValueKind == JsonValueKind.String) Assert.Equal(k.HumPivot, (float)pv[1].GetDouble(), 1e-6f);
            else { Assert.True(k.HumPivot < 0); Assert.Equal(k.Pivot, V(pv)); }
            var aim = c.GetProperty("aim");
            if (aim.ValueKind == JsonValueKind.Null) Assert.Null(k.Aim);
            else { Assert.Equal(k.Aim![0], (float)aim[0].GetDouble(), 1e-6f); Assert.Equal(k.AimOff, V(aim[1])); }
        }
    }
}
