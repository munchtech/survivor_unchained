using System;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Text.Json;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her upper arm's twist chain (Play/ArmTwist.cs, HerJoints' math) against its Python twin, helpers.drive(),
/// on the fixture tools/anim/twist_parity_fixture.py writes: her skeleton with the chain, each upper arm rolled frame
/// by frame through +-180 (the unwrap) and past unwrap_max (the one flip). Every chain bone and the shoulder share
/// within 1e-4 rad; the roll as Python unwrapped it; and the game's rig_helpers.json carrying the same numbers.</summary>
public class ArmTwistTests
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

    /// <summary>The angle between two rotations (radians), either sign of the quaternion: of conj(a) b, in doubles,
    /// as 2 atan2(|xyz|, |w|) (an acos of the dot is blind below ~3e-4 rad in floats).</summary>
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
    public void ChainMatchesPython(string side)
    {
        var fx = Load("tests", "fixtures", "arm_twist_parity.json");
        float max = (float)fx.GetProperty("unwrap_max").GetDouble();
        var s = fx.GetProperty("sides").GetProperty(side);
        var rest = Q(s.GetProperty("upper_rest"));
        var own = Q(s.GetProperty("share_own"));
        float amount = (float)s.GetProperty("share_amount").GetDouble(), k = (float)s.GetProperty("share_roll").GetDouble();
        var amounts = s.GetProperty("amounts").EnumerateObject().ToDictionary(p => p.Name, p => (float)p.Value.GetDouble());
        float last = float.NaN;
        bool crossed = false, flipped = false;
        int f = 0;
        foreach (var fr in s.GetProperty("frames").EnumerateArray())
        {
            var upper = Q(fr.GetProperty("upper"));
            float roll = ArmTwist.Unwrap(last, ArmTwist.Roll(rest, upper), max);
            if (!float.IsNaN(last) && Math.Abs(roll) > 180f) crossed = true;
            if (!float.IsNaN(last) && Math.Abs(roll - last) > 300f) flipped = true;
            last = roll;
            Assert.True(Math.Abs(roll - fr.GetProperty("roll").GetDouble()) < 1e-3, $"{side} f{f}: roll {roll} vs {fr.GetProperty("roll").GetDouble()}");
            foreach (var b in fr.GetProperty("chain").EnumerateObject())
            {
                double e = Apart(ArmTwist.Counter(roll, amounts[b.Name]), Q(b.Value));
                Assert.True(e < Tol, $"{side} f{f} {b.Name}: {e:E2} rad off");
            }
            double es = Apart(ArmTwist.Share(rest, upper, amount, own, roll, k), Q(fr.GetProperty("share")));
            Assert.True(es < Tol, $"{side} f{f} share: {es:E2} rad off");
            f++;
        }
        Assert.True(crossed, "the sweep never carried the roll past 180 (the unwrap untested)");
        Assert.True(flipped, "the sweep never ran past unwrap_max (the flip untested)");
    }

    [Fact]
    public void GameSpecCarriesTheChain()
    {
        var spec = Load("art", "people", "rig_helpers.json");
        var tc = spec.GetProperty("twist_chain");
        var fx = Load("tests", "fixtures", "arm_twist_parity.json");
        Assert.Equal(fx.GetProperty("unwrap_max").GetDouble(), tc.GetProperty("unwrap_max").GetDouble());
        var s = fx.GetProperty("sides").GetProperty("l");
        Assert.Equal(s.GetProperty("share_roll").GetDouble(), tc.GetProperty("roll").GetProperty("upperarm_share_{s}").GetDouble());
        foreach (var p in s.GetProperty("amounts").EnumerateObject())
        {
            string n = p.Name[..^1] + "{s}";
            double want = tc.GetProperty("amounts").TryGetProperty(n, out var a) ? a.GetDouble()
                : spec.GetProperty("helpers").EnumerateArray().First(h => h.GetProperty("name").GetString() == n).GetProperty("amount").GetDouble();
            Assert.Equal(p.Value.GetDouble(), want, 9);
        }
    }

    [Fact]
    public void UnwrapCarriesOnThroughHalfTurn()
    {
        Assert.Equal(10f, ArmTwist.Unwrap(float.NaN, 10f, 270f));
        Assert.Equal(190f, ArmTwist.Unwrap(170f, -170f, 270f));
        Assert.Equal(-190f, ArmTwist.Unwrap(-170f, 170f, 270f));
        Assert.Equal(-80f, ArmTwist.Unwrap(265f, -80f, 270f));   // past the limit: the one flip
        Assert.Equal(0f, ArmTwist.Unwrap(190f, 0f, 270f));      // a clip change to rest: no full turn
    }
}
