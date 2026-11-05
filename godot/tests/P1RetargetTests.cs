using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>P1Retarget on B's own skeleton as its source (the fixture's names, rest and rig.json, A = B): one arm
/// posed (an upper-arm roll, an elbow flex, a wrist turn) and the mapped B's segment directions against the source's,
/// before and after P1Rig.Drive. F round 1's fault: rig.json's "unroll" rows named the lowerarm and calf as helpers,
/// so the retarget carried them at rest and the elbow and knee never bent.</summary>
public class P1RetargetTests
{
    static string Root()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? Directory.GetCurrentDirectory();
    }

    static P1M4 M(JsonElement e) => P1M4.FromRows(e.EnumerateArray().SelectMany(r => r.EnumerateArray()).Select(x => x.GetDouble()).ToArray());

    static P1M4[] Pose(string[] names, int[] parent, P1M4[] rest, Dictionary<string, P1V> turns)
    {
        int n = names.Length;
        var G = new P1M4[n];
        P1M4 Get(int j)
        {
            if (G[j] != null) return G[j];
            int p = parent[j];
            var local = p < 0 ? rest[j] : rest[p].Inverse() * rest[j];
            if (turns.TryGetValue(names[j], out var v)) local = local * P1M4.From(P1Rig.Expm(v), new P1V(0, 0, 0));
            return G[j] = p < 0 ? local : Get(p) * local;
        }
        for (int j = 0; j < n; j++) Get(j);
        return G;
    }

    [Fact]
    public void OneArmFollowsItsSource()
    {
        var fx = JsonDocument.Parse(File.ReadAllText(Path.Combine(Root(), "tests", "fixtures", "p1_rig_parity.json"))).RootElement;
        var names = fx.GetProperty("names").EnumerateArray().Select(x => x.GetString()!).ToArray();
        var parent = fx.GetProperty("parent").EnumerateArray().Select(p => p.GetInt32()).ToArray();
        var rest = fx.GetProperty("rest").EnumerateArray().Select(M).ToArray();
        var rig = new P1Rig(names, parent, rest, fx.GetProperty("rig"));
        var map = new P1Retarget(names, parent, rest, rig);
        double D(double deg) => deg * Math.PI / 180;
        foreach (var turns in new[]
        {
            new Dictionary<string, P1V> { ["upperarm_l"] = new(0, D(40), 0) },                                   // a roll alone
            new Dictionary<string, P1V> { ["lowerarm_l"] = new(D(90), 0, 0) },                                   // an elbow flex alone
            new Dictionary<string, P1V> { ["upperarm_l"] = new(D(30), D(40), D(-20)), ["lowerarm_l"] = new(D(100), D(15), 0), ["hand_l"] = new(D(20), 0, D(30)), ["calf_l"] = new(D(-70), 0, 0) },
        })
        {
            var a = Pose(names, parent, rest, turns);
            var mapped = map.Map(a);
            foreach (var (tag, g) in new[] { ("map", mapped), ("driven", rig.Drive(mapped).G) })
                foreach (var (b0, b1) in new[] { ("upperarm_l", "lowerarm_l"), ("lowerarm_l", "hand_l"), ("hand_l", "middle_01_l"), ("thigh_l", "calf_l"), ("calf_l", "foot_l") })
                {
                    // (by the joints themselves, not P1Retarget.Directions: that skips the rig's helpers, which hid the fault)
                    int i0 = rig.Index[b0], i1 = rig.Index[b1];
                    var u = a[i1].T() - a[i0].T(); var v = g[i1].T() - g[i0].T();
                    double deg = Math.Acos(Math.Clamp(P1V.Dot(u, v) / (u.Len() * v.Len()), -1, 1)) * 180 / Math.PI;
                    Assert.True(deg < 0.5, $"{tag} {string.Join(",", turns.Keys)}: {b0} {deg:F2} deg off its source");
                }
        }
    }
}
