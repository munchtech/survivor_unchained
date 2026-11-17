using System;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Text.Json;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her hip hinges (Play/HipHinge.cs, HerJoints' math) against their Python twin, helpers.drive_hinges, on
/// every frame of the four demo clips (tools/anim/hinge_parity_fixture.py): the local rest within 1e-5 (rotation)
/// and 0.01 mm, every posed turn within 0.05 degrees; the game's rig_helpers.json carrying the same numbers; none of
/// the thigh's roll taken. The tasset hinge (TassetTurn/TassetPose, helpers.drive_tassets) likewise.</summary>
public class HipHingeTests
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
        return 2 * Math.Atan2(new Vector3(d.X, d.Y, d.Z).Length(), Math.Abs(d.W)) * 180 / Math.PI;
    }

    [Fact]
    public void Rest_and_every_demo_frame_match_the_python_law()
    {
        var fx = Load("tests", "fixtures", "hinge_parity.json");
        double worst = 0;
        int n = 0;
        foreach (var s in fx.GetProperty("sides").EnumerateArray())
        {
            var gp = Q(s.GetProperty("parent_rot"));
            var (r, t) = HipHinge.Rest(gp, V(s.GetProperty("parent_pos")), V(s.GetProperty("pivot")));
            Assert.True(Deg(r, Q(s.GetProperty("rest_rot"))) < 1e-3, "rest turn");
            Assert.True((t - V(s.GetProperty("rest_pos"))).Length() < 1e-5f, "rest place");
            var v0 = Vector3.Transform(Vector3.Transform(Vector3.UnitY, Q(s.GetProperty("chain_rest"))), gp);
            double amount = s.GetProperty("amount").GetDouble();
            foreach (var f in s.GetProperty("frames").EnumerateArray())
            {
                var v = Vector3.Transform(Vector3.Transform(Vector3.UnitY, Q(f.GetProperty("chain"))), gp);
                double d = Deg(HipHinge.Pose(r, v0, v, amount), Q(f.GetProperty("hinge")));
                worst = Math.Max(worst, d);
                n++;
            }
        }
        Assert.True(n > 400, $"frames {n}");
        Assert.True(worst < 0.05, $"worst {worst:F4} deg");
    }

    [Fact]
    public void The_games_spec_carries_the_fixtures_numbers()
    {
        var fx = Load("tests", "fixtures", "hinge_parity.json").GetProperty("spec");
        var game = Load("art", "people", "rig_helpers.json").GetProperty("hinges");
        Assert.Equal(fx.GetArrayLength(), game.GetArrayLength());
        for (int i = 0; i < fx.GetArrayLength(); i++)
        {
            Assert.Equal(fx[i].GetProperty("name").GetString(), game[i].GetProperty("name").GetString());
            Assert.Equal(fx[i].GetProperty("amount").GetDouble(), game[i].GetProperty("amount").GetDouble(), 9);
            for (int k = 0; k < 3; k++)
                Assert.Equal(fx[i].GetProperty("pivot")[k].GetDouble(), game[i].GetProperty("pivot")[k].GetDouble(), 9);
        }
    }

    [Fact]
    public void The_tasset_hinge_matches_the_python_law_on_every_demo_frame()
    {
        var fx = Load("tests", "fixtures", "hinge_parity.json");
        double worst = 0, place = 0;
        int n = 0;
        foreach (var s in fx.GetProperty("tassets").EnumerateArray())
        {
            var gp = Q(s.GetProperty("parent_rot"));
            var (r, t) = HipHinge.Rest(gp, V(s.GetProperty("parent_pos")), V(s.GetProperty("pivot")));
            Assert.True(Deg(r, Q(s.GetProperty("rest_rot"))) < 1e-3, "rest turn");
            Assert.True((t - V(s.GetProperty("rest_pos"))).Length() < 1e-5f, "rest place");
            var cr = s.GetProperty("chain_rest");
            var v0 = new[] { 0, 1 }.Select(i => Vector3.Transform(Vector3.Transform(Vector3.UnitY, Q(cr[i])), gp)).ToArray();
            double amount = s.GetProperty("amount").GetDouble(), soft = s.GetProperty("soft").GetDouble();
            foreach (var f in s.GetProperty("frames").EnumerateArray())
            {
                var sw = new double[2];
                for (int i = 0; i < 2; i++)
                {
                    var v = Vector3.Transform(Vector3.Transform(Vector3.UnitY, Q(f.GetProperty("chains")[i])), gp);
                    sw[i] = SurvivorUnchained.Core.PanelSwing.SwingSpread(v.X, v.Y, v.Z, v0[i].X, v0[i].Y, v0[i].Z, i == 0 ? 1 : -1).Swing;
                }
                var got = HipHinge.TassetPose(r, HipHinge.TassetTurn(sw[0], sw[1], amount, soft));
                var want = Q(f.GetProperty("tasset"));
                worst = Math.Max(worst, Deg(got, want));
                // (a V tip 18 cm down the fall from the pivot, placed by each turn: mm apart)
                var tip = new Vector3(0, -0.18f, 0);
                place = Math.Max(place, (Vector3.Transform(tip, got) - Vector3.Transform(tip, want)).Length() * 1000);
                n++;
            }
        }
        Assert.True(n > 200, $"frames {n}");
        Assert.True(worst < 0.05, $"worst {worst:F4} deg");
        Assert.True(place < 0.5, $"tip {place:F3} mm");
    }

    [Fact]
    public void The_games_spec_carries_the_tasset_hinge()
    {
        var fx = Load("tests", "fixtures", "hinge_parity.json").GetProperty("tasset_spec");
        var game = Load("art", "people", "rig_helpers.json").GetProperty("tassets");
        Assert.Equal(fx.GetArrayLength(), game.GetArrayLength());
        Assert.True(game.GetArrayLength() > 0);
        for (int i = 0; i < fx.GetArrayLength(); i++)
        {
            Assert.Equal(fx[i].GetProperty("name").GetString(), game[i].GetProperty("name").GetString());
            Assert.Equal(fx[i].GetProperty("amount").GetDouble(), game[i].GetProperty("amount").GetDouble(), 9);
            Assert.Equal(fx[i].GetProperty("soft").GetDouble(), game[i].GetProperty("soft").GetDouble(), 9);
            for (int k = 0; k < 3; k++)
                Assert.Equal(fx[i].GetProperty("pivot")[k].GetDouble(), game[i].GetProperty("pivot")[k].GetDouble(), 9);
        }
    }

    [Fact]
    public void The_tasset_turns_with_the_leading_thigh_never_back()
    {
        // equal thighs give their own swing (the smooth max less soft/4), past the softrelu's knee
        Assert.Equal(0.6 * (40 - 6), HipHinge.TassetTurn(40, 40, 0.6, 12), 9);
        // the leading thigh leads; a trailing one adds nothing
        Assert.Equal(0.6 * (50 - 3 - 6), HipHinge.TassetTurn(50, -30, 0.6, 12), 9);
        // never turned back (both thighs behind)
        Assert.Equal(0, HipHinge.TassetTurn(-20, -10, 0.6, 12));
        // the bottom forward: her -Y toward +Z
        var tip = Vector3.Transform(-Vector3.UnitY, HipHinge.TassetPose(Quaternion.Identity, 30));
        Assert.True(tip.Z > 0.49f && tip.Y < -0.86f, $"tip {tip}");
    }

    [Fact]
    public void Half_the_swing_and_none_of_the_roll()
    {
        var v0 = -Vector3.UnitY;
        var v = Vector3.Transform(v0, Quaternion.CreateFromAxisAngle(Vector3.UnitX, -1.2f));
        var q = HipHinge.Turn(v0, v, 0.5);
        Assert.True(Math.Abs(Deg(Quaternion.Identity, q) - 1.2 * 90 / Math.PI) < 1e-3);
        // the thigh rolled about its own line: no turn
        Assert.True(Deg(Quaternion.Identity, HipHinge.Turn(v0, v0, 0.5)) < 1e-6);
        Assert.Equal(new Vector3(-0.11f, 1.12f, 0f), HipHinge.Pivot(new Vector3(0.11f, 1.12f, 0f), false));
    }
}
