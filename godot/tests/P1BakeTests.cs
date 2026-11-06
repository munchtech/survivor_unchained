using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The clip bridge's pure part (P1Bake) on B's own skeleton as its source (the fixture, A = B): the girdle
/// hold, the key rule, the hand clean; and the role map (P1Retarget.Role) from A's skeleton (a_skeleton.json) to B's.</summary>
public class P1BakeTests
{
    static string Root()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? Directory.GetCurrentDirectory();
    }

    static P1M4 M(JsonElement e) => P1M4.FromRows(e.EnumerateArray().SelectMany(r => r.EnumerateArray()).Select(x => x.GetDouble()).ToArray());
    static double D(double deg) => deg * Math.PI / 180;

    static (string[] Names, int[] Parent, P1M4[] Rests, P1Rig Rig) B()
    {
        var fx = JsonDocument.Parse(File.ReadAllText(Path.Combine(Root(), "tests", "fixtures", "p1_rig_parity.json"))).RootElement;
        var names = fx.GetProperty("names").EnumerateArray().Select(x => x.GetString()!).ToArray();
        var parent = fx.GetProperty("parent").EnumerateArray().Select(p => p.GetInt32()).ToArray();
        var rest = fx.GetProperty("rest").EnumerateArray().Select(M).ToArray();
        return (names, parent, rest, new P1Rig(names, parent, rest, fx.GetProperty("rig").Clone()));
    }

    static P1M4[] Pose(string[] names, int[] parent, P1M4[] rest, Dictionary<string, P1V> turns)
    {
        var G = new P1M4[names.Length];
        P1M4 Get(int j)
        {
            if (G[j] != null) return G[j];
            int p = parent[j];
            var local = p < 0 ? rest[j] : rest[p].Inverse() * rest[j];
            if (turns.TryGetValue(names[j], out var v)) local = local * P1M4.From(P1Rig.Expm(v), new P1V(0, 0, 0));
            return G[j] = p < 0 ? local : Get(p) * local;
        }
        for (int j = 0; j < names.Length; j++) Get(j);
        return G;
    }

    static double Ang(P1M3 a, P1M3 b) => P1Rig.RotVec(a.T() * b).Len() * 180 / Math.PI;
    static double Diff(P1M4 a, P1M4 b) => Enumerable.Range(0, 12).Max(k => Math.Abs(a.A[k] - b.A[k]));

    [Fact]
    public void GirdleHoldKeepsTheArmAndRestsTheClavicle()
    {
        var (names, parent, rest, rig) = B();
        var bake = new P1Bake(rig, new P1Retarget(names, parent, rest, rig));
        var a = Pose(names, parent, rest, new() { ["clavicle_l"] = new(0, 0, D(25)), ["scap_l"] = new(D(10), 0, 0), ["upperarm_l"] = new(D(30), D(20), D(-40)), ["lowerarm_l"] = new(D(70), 0, 0), ["spine_03"] = new(D(8), 0, D(5)) });
        var mapped = bake.Map.Map(a);
        var (L, G) = bake.Frame(a);
        foreach (var g in new[] { "clavicle_l", "scap_l", "clavicle_r", "scap_r" })
            Assert.True(Diff(L[rig.Index[g]], bake.RestLocal(rig.Index[g])) < 1e-9, $"{g} not at B's rest local");
        foreach (var n in new[] { "upperarm_l", "lowerarm_l", "hand_l" })
        {
            double deg = Ang(P1Retarget.Rot(G[rig.Index[n]]), P1Retarget.Rot(mapped[rig.Index[n]]));
            Assert.True(deg < 1e-6, $"{n} world turn moved {deg:F4} deg by the hold");
        }
        // the upper arm's head rides the held clavicle (B's rest offset from it)
        int u = rig.Index["upperarm_l"], c = rig.Index[names[parent[u]]];
        Assert.True((G[u].T() - G[c] * bake.RestLocal(u).T()).Len() < 1e-9);
        // a source with no girdle turn: the hold changes nothing
        var a0 = Pose(names, parent, rest, new() { ["upperarm_l"] = new(D(30), 0, 0) });
        var (_, G0) = bake.Frame(a0);
        Assert.True((G0[rig.Index["hand_l"]].T() - a0[rig.Index["hand_l"]].T()).Len() < 1e-6);
    }

    [Fact]
    public void KeyRuleKeepsPartialClipsPartial()
    {
        var (names, parent, rest, rig) = B();
        var bake = new P1Bake(rig, new P1Retarget(names, parent, rest, rig));
        int I(string n) => Array.IndexOf(names, n);
        Assert.Empty(bake.Keyed(new HashSet<int>()));
        var k = bake.Keyed(new HashSet<int> { I("upperarm_l"), I("lowerarm_l"), I("clavicle_l"), I("upperarm_twist_01_l") });
        Assert.Contains(rig.Index["upperarm_l"], k);
        Assert.Contains(rig.Index["lowerarm_l"], k);
        Assert.DoesNotContain(rig.Index["clavicle_l"], k);              // the girdle: held, never keyed
        Assert.DoesNotContain(rig.Index["upperarm_twist_01_l"], k);     // a helper: B's laws
        Assert.DoesNotContain(rig.Index["upperarm_r"], k);
        Assert.DoesNotContain(rig.Index["pelvis"], k);
        // the chain: a bone between pelvis and Head is keyed when either bracket is
        var spine = bake.Keyed(new HashSet<int> { I("spine_03") });
        Assert.NotEmpty(spine);
        Assert.All(spine, j => Assert.True(names[j].StartsWith("spine") || names[j].StartsWith("neck"), names[j]));
    }

    [Fact]
    public void CleaningDataIsApplied()
    {
        var (names, parent, rest, rig) = B();
        var bake = new P1Bake(rig, new P1Retarget(names, parent, rest, rig));
        var cleans = P1Bake.ParseCleans("{\"clips\": {\"x\": {\"why\": \"t\", \"turns\": {\"lowerarm_l\": [30, 0, 0]}, \"hold\": [\"hand_l\"]}, \"empty\": {\"why\": \"e\", \"turns\": {}, \"hold\": []}}}");
        Assert.Equal(2, cleans.Count);
        var a = Pose(names, parent, rest, new() { ["lowerarm_l"] = new(D(40), 0, 0), ["hand_l"] = new(D(20), D(10), 0) });
        var (L0, _) = bake.Frame(a);
        var (L1, _) = bake.Frame(a, cleans["x"]);
        int lo = rig.Index["lowerarm_l"], h = rig.Index["hand_l"];
        Assert.True(Math.Abs(Ang(P1Retarget.Rot(L0[lo]), P1Retarget.Rot(L1[lo])) - 30) < 1e-6);
        Assert.True(Diff(L1[h], bake.RestLocal(h)) < 1e-9);
        var (L2, _) = bake.Frame(a, cleans["empty"]);
        Assert.True(Enumerable.Range(0, names.Length).All(j => Diff(L0[j], L2[j]) < 1e-12));
    }

    [Fact]
    public void RoleMapFromASkeleton()
    {
        var path = Path.Combine(Root(), "art", "people", "body_p1", "a_skeleton.json");
        Assert.True(File.Exists(path), "a_skeleton.json (the clip bridge writes it)");
        var r = JsonDocument.Parse(File.ReadAllText(path)).RootElement;
        var an = r.GetProperty("names").EnumerateArray().Select(x => x.GetString()!).ToArray();
        var ap = r.GetProperty("parent").EnumerateArray().Select(x => x.GetInt32()).ToArray();
        var ar = r.GetProperty("rest").EnumerateArray().Select(M).ToArray();
        var (names, _, _, rig) = B();
        var map = new P1Retarget(an, ap, ar, rig);
        string Role(string a) { int j = map.Role(Array.IndexOf(an, a)); return j < 0 ? "-" : names[j]; }
        Assert.Equal("spine_05", Role("spine_03"));
        Assert.StartsWith("neck_0", Role("neck_01"));
        foreach (var n in new[] { "upperarm_l", "hand_r", "thigh_l", "foot_r", "clavicle_l", "Head", "pelvis" }) Assert.Equal(n, Role(n));
        int pf = Array.IndexOf(an, "panel_front");
        Assert.True(pf >= 0);
        Assert.Equal(Role(an[ap[pf]]), Role("panel_front"));
        // the carriage's spine shares spread over B's chain keep their total
        var spread = map.Spread(new[] { ("spine_01", 0.2), ("spine_02", 0.3), ("spine_03", 0.35), ("neck_01", 0.15) });
        Assert.True(Math.Abs(spread.Sum(s => s.Share) - 1.0) < 1e-9);
    }
}
