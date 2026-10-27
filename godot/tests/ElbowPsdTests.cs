using System;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Text.Json;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her elbow pose-space shapes' drive (Play/ElbowPsd, HerJoints) against its Python twin (helpers.flexion,
/// corrective_weight) on the fixture tools/anim/elbow_psd_fixture.py writes: forearm poses flexed -20..160, swung and
/// rolled; flexion within 1e-3 deg, weights within 1e-4; the spec's in-betweens 0 at a straight arm, whole at their
/// samples, a partition between.</summary>
public class ElbowPsdTests
{
    static string Root()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? Directory.GetCurrentDirectory();
    }

    static JsonElement Load(params string[] rel) => JsonDocument.Parse(File.ReadAllText(Path.Combine(new[] { Root() }.Concat(rel).ToArray()))).RootElement;

    static Quaternion Q(JsonElement e) => new((float)e[0].GetDouble(), (float)e[1].GetDouble(), (float)e[2].GetDouble(), (float)e[3].GetDouble());

    static float[][] Keys() => Load("art", "people", "rig_helpers.json").GetProperty("correctives").EnumerateArray()
        .Where(c => c.TryGetProperty("on", out var o) && o.GetString() == "flex")
        .Select(c => c.GetProperty("keys").EnumerateArray().Select(x => (float)x.GetDouble()).ToArray()).ToArray();

    [Theory]
    [InlineData("l")]
    [InlineData("r")]
    public void MatchesPython(string side)
    {
        var fx = Load("tests", "fixtures", "elbow_psd_parity.json");
        var keys = Keys();
        Assert.Equal(3, keys.Length);
        var s = fx.GetProperty("sides").GetProperty(side);
        var rest = Q(s.GetProperty("rest"));
        int n = 0;
        foreach (var fr in s.GetProperty("frames").EnumerateArray())
        {
            float f = ElbowPsd.Flexion(rest, Q(fr.GetProperty("pose")));
            Assert.True(Math.Abs(f - fr.GetProperty("flex").GetDouble()) < 1e-3, $"{side} f{n}: flexion {f} vs {fr.GetProperty("flex").GetDouble()}");
            var w = fr.GetProperty("w").EnumerateArray().Select(x => x.GetDouble()).ToArray();
            for (int k = 0; k < keys.Length; k++)
                Assert.True(Math.Abs(ElbowPsd.Weight(keys[k][0], keys[k][1], keys[k][2], f) - w[k]) < 1e-4, $"{side} f{n} shape {k}");
            n++;
        }
        Assert.True(n >= 40);
    }

    [Fact]
    public void StraightArmIsZeroSamplesWholePartitionBetween()
    {
        var k = Keys();
        foreach (var d in new[] { -30f, -5f, 0f })
            Assert.All(k, x => Assert.Equal(0f, ElbowPsd.Weight(x[0], x[1], x[2], d)));
        Assert.Equal(1f, ElbowPsd.Weight(k[0][0], k[0][1], k[0][2], 45f));
        Assert.Equal(1f, ElbowPsd.Weight(k[1][0], k[1][1], k[1][2], 90f));
        Assert.Equal(1f, ElbowPsd.Weight(k[2][0], k[2][1], k[2][2], 135f));
        Assert.Equal(1f, ElbowPsd.Weight(k[2][0], k[2][1], k[2][2], 160f));
        foreach (var d in new[] { 50f, 67.5f, 89f, 91f, 120f, 134f })
            Assert.Equal(1f, k.Sum(x => ElbowPsd.Weight(x[0], x[1], x[2], d)), 4);
        Assert.Equal(0f, ElbowPsd.Flexion(Quaternion.Identity, Quaternion.CreateFromAxisAngle(Vector3.UnitY, 1.2f)), 3);
        Assert.Equal(90f, ElbowPsd.Flexion(Quaternion.Identity, Quaternion.CreateFromAxisAngle(Vector3.UnitX, MathF.PI / 2)), 3);
        Assert.Equal(0f, ElbowPsd.Flexion(Quaternion.Identity, Quaternion.CreateFromAxisAngle(Vector3.UnitZ, 0.3f)), 3);
    }
}
