using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>P1's body B: the game's port of its rig (Play/P1Rig.cs) against rig_drive.drive on the fixture
/// tools/body/p1_rig_fixture.py writes (the published rig.json plus an rbf, an arc and a legacy row, on sampled poses):
/// every driven bone world within 1e-6, every corrective weight within 1e-3 (the brief's bar; measured far under).</summary>
public class P1RigTests
{
    static string Root()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? Directory.GetCurrentDirectory();
    }

    static P1M4 M(JsonElement e) => P1M4.FromRows(e.EnumerateArray().SelectMany(r => r.EnumerateArray()).Select(x => x.GetDouble()).ToArray());

    [Fact]
    public void DriveMatchesRigDrive() => Parity("p1_rig_parity.json", false);

    /// <summary>P1 R1 sliders: the hand-clearance law (rig.json "hand_clear", rig_drive.hand_clear) on a slider body
    /// (hips 0.6; p1_rig_fixture.py --hand: its baked idles' frames, her hands by and on her thighs), held the same.</summary>
    [Fact]
    public void HandClearMatchesRigDrive() => Parity("p1_rig_parity_hand.json", true);

    static void Parity(string file, bool hand)
    {
        var path = Path.Combine(Root(), "tests", "fixtures", file);
        var fx = JsonDocument.Parse(File.ReadAllText(path)).RootElement;
        var names = fx.GetProperty("names").EnumerateArray().Select(n => n.GetString()!).ToArray();
        var parent = fx.GetProperty("parent").EnumerateArray().Select(p => p.GetInt32()).ToArray();
        var rest = fx.GetProperty("rest").EnumerateArray().Select(M).ToArray();
        var rig = new P1Rig(names, parent, rest, fx.GetProperty("rig"));
        double worstG = 0, worstW = 0, moved = 0;
        int poses = 0, shapes = 0;
        int hl = Array.IndexOf(names, "hand_l");
        foreach (var pose in fx.GetProperty("poses").EnumerateArray())
        {
            var G = pose.GetProperty("G").EnumerateArray().Select(M).ToArray();
            var want = pose.GetProperty("driven").EnumerateArray().Select(M).ToArray();
            var (got, w) = rig.Drive(G);
            if (pose.GetProperty("name").GetString() == "rest")     // the girdle's tables are relative to the rest
                for (int j = 0; j < got.Length; j++)
                    for (int i = 0; i < 16; i++) Assert.True(Math.Abs(got[j].A[i] - G[j].A[i]) < 1e-9, "rest is not identity");
            for (int j = 0; j < got.Length; j++)
                for (int i = 0; i < 16; i++) worstG = Math.Max(worstG, Math.Abs(got[j].A[i] - want[j].A[i]));
            moved = Math.Max(moved, (got[hl].T() - G[hl].T()).Len());
            foreach (var kv in pose.GetProperty("weights").EnumerateObject())
            {
                Assert.True(w.ContainsKey(kv.Name), $"{pose.GetProperty("name").GetString()}: no weight for {kv.Name}");
                worstW = Math.Max(worstW, Math.Abs(w[kv.Name] - kv.Value.GetDouble()));
                shapes++;
            }
            Assert.Equal(pose.GetProperty("weights").EnumerateObject().Count(), w.Count);
            poses++;
        }
        Assert.True(poses >= 6 && shapes > 0);
        Assert.True(worstG < 1e-6, $"driven bone worlds off by {worstG}");
        Assert.True(worstW < 1e-3, $"weights off by {worstW}");
        if (hand) Assert.True(moved > 0.005, $"the hand law never acted (hand moved {moved * 1000:F1} mm)");
        Console.WriteLine($"P1Rig parity ({file}): {poses} poses, {shapes} weights; worst world {worstG:E2}, worst weight {worstW:E2}");
    }
}
