using System;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Text.Json;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Body B's hip hinges and tasset hinge (Play/P1Hinges.cs, P1Laws' math) against helpers.py with B's skeleton
/// (tools/anim/p1_hinge_parity_fixture.py): every fixture frame within 1e-5 (HipHingeTests' bound), the rest place within
/// 1e-6, and body_p1/rig_helpers.json carrying the fixture's pivots.</summary>
public class P1HingeTests
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

    static double Deg(Quaternion a, Quaternion b)
    {
        var d = Quaternion.Inverse(a) * b;
        return 2 * Math.Atan2(new Vector3(d.X, d.Y, d.Z).Length(), Math.Abs(d.W));
    }

    // (the tests' pivots are the right side's too: the fixture gives each side's own, so left = true with that pivot)
    [Fact]
    public void Hinge_rest_and_every_frame_match_the_python_law()
    {
        var fx = Load("tests", "fixtures", "p1_hinge_parity.json");
        double worst = 0;
        int n = 0;
        foreach (var s in fx.GetProperty("sides").EnumerateArray())
        {
            var gp = Q(s.GetProperty("parent_rot"));
            var (r, t) = P1Hinges.Rest(gp, V(s.GetProperty("parent_pos")), V(s.GetProperty("pivot")), true);
            Assert.True((t - V(s.GetProperty("rest_pos"))).Length() < 1e-6f, "rest place");
            Assert.True(Deg(r, Q(s.GetProperty("rest_rot"))) < 1e-5, "rest turn");
            var cr = Q(s.GetProperty("chain_rest"));
            double amount = s.GetProperty("amount").GetDouble();
            foreach (var f in s.GetProperty("frames").EnumerateArray())
            {
                worst = Math.Max(worst, Deg(P1Hinges.Pose(r, gp, cr, Q(f.GetProperty("chain")), amount), Q(f.GetProperty("hinge"))));
                n++;
            }
        }
        Assert.True(n >= 320, $"frames {n}");
        Assert.True(worst < 1e-5, $"worst {worst:E2} rad");
    }

    [Fact]
    public void Tasset_rest_and_every_frame_match_the_python_law()
    {
        var fx = Load("tests", "fixtures", "p1_hinge_parity.json");
        double worst = 0;
        int n = 0;
        foreach (var s in fx.GetProperty("tassets").EnumerateArray())
        {
            var gp = Q(s.GetProperty("parent_rot"));
            var (r, t) = P1Hinges.Rest(gp, V(s.GetProperty("parent_pos")), V(s.GetProperty("pivot")), true);
            Assert.True((t - V(s.GetProperty("rest_pos"))).Length() < 1e-6f, "rest place");
            var cr = s.GetProperty("chain_rest").EnumerateArray().Select(Q).ToArray();
            double amount = s.GetProperty("amount").GetDouble(), soft = s.GetProperty("soft").GetDouble();
            foreach (var f in s.GetProperty("frames").EnumerateArray())
            {
                var now = f.GetProperty("chains").EnumerateArray().Select(Q).ToArray();
                worst = Math.Max(worst, Deg(P1Hinges.TassetPose(r, gp, cr, now, amount, soft), Q(f.GetProperty("tasset"))));
                n++;
            }
        }
        Assert.True(n >= 160, $"frames {n}");
        Assert.True(worst < 1e-5, $"worst {worst:E2} rad");
    }

    [Fact]
    public void Bs_rig_helpers_carry_the_fixtures_pivots()
    {
        var fx = Load("tests", "fixtures", "p1_hinge_parity.json");
        var game = Load("art", "people", "body_p1", "rig_helpers.json");
        Assert.Equal("p1", game.GetProperty("body").GetString());
        var fh = fx.GetProperty("sides").EnumerateArray().Where(s => s.GetProperty("left").GetBoolean()).ToArray();
        var gh = game.GetProperty("hinges");
        Assert.Equal(fh.Length, gh.GetArrayLength());
        for (int i = 0; i < fh.Length; i++)
            for (int k = 0; k < 3; k++)
                Assert.Equal(fh[i].GetProperty("pivot")[k].GetDouble(), gh[i].GetProperty("pivot")[k].GetDouble(), 6);
        var ft = fx.GetProperty("tassets");
        var gt = game.GetProperty("tassets");
        Assert.Equal(ft.GetArrayLength(), gt.GetArrayLength());
        for (int i = 0; i < ft.GetArrayLength(); i++)
            for (int k = 0; k < 3; k++)
                Assert.Equal(ft[i].GetProperty("pivot")[k].GetDouble(), gt[i].GetProperty("pivot")[k].GetDouble(), 6);
    }
}
