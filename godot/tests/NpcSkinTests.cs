using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.Json;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>A package NPC on our base body takes her skin's treatment (People.NpcSkin, tools_scenes/NpcSkinCheck.cs): her cel tone,
/// back spec, throat fold, zones, head maps and brows by default, and a manifest "skin" block's uniforms over them. An engine
/// test like DraftCardFitTests (one collection: their two builds never run at once); without the engine it says so and passes.</summary>
[Collection("engine")]
public sealed class NpcSkinTests(ITestOutputHelper log)
{
    const string GodotExe = @"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe";

    static string? GodotDir()
    {
        for (var d = new DirectoryInfo(AppContext.BaseDirectory); d != null; d = d.Parent)
            if (File.Exists(Path.Combine(d.FullName, "SurvivorUnchained.csproj"))) return d.FullName;
        return null;
    }

    static (int Code, string Out) Run(string exe, string args, string cwd, int minutes)
    {
        var psi = new ProcessStartInfo(exe, args) { WorkingDirectory = cwd, RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false };
        using var p = Process.Start(psi)!;
        var err = p.StandardError.ReadToEndAsync();
        var output = p.StandardOutput.ReadToEnd();
        if (!p.WaitForExit(minutes * 60_000)) { p.Kill(true); return (-1, output + "\n(timed out)"); }
        return (p.ExitCode, output + err.Result);
    }

    static double[] Vec(JsonElement e) => e.EnumerateArray().Select(x => x.GetDouble()).ToArray();

    [Fact]
    public void An_npc_takes_her_skin_treatment_and_the_manifest_overrides_it()
    {
        var dir = GodotDir();
        var exe = Environment.GetEnvironmentVariable("GODOT_EXE") ?? GodotExe;
        if (dir == null || !File.Exists(exe) || !Directory.Exists(Path.Combine(dir, ".godot", "imported")))
        {
            log.WriteLine($"skipped: no Godot at {exe}, or no imported project beside the tests");
            return;
        }
        var build = Run("dotnet", "build SurvivorUnchained.csproj -v q -nologo", dir, 10);
        Assert.True(build.Code == 0, "the game did not build:\n" + build.Out);
        var report = Path.Combine(Path.GetTempPath(), $"npc_skin_{Environment.ProcessId}.txt");
        var run = Run(exe, $"--headless --path \"{dir}\" -s res://tools_scenes/npc_skin_check.gd -- \"{report}\"", dir, 10);
        foreach (var line in run.Out.Split('\n')) if (line.StartsWith("npc_skin")) log.WriteLine(line.TrimEnd());
        Assert.True(run.Code == 0 && File.Exists(report), $"the check failed (exit {run.Code}):\n{run.Out}");
        var rows = new Dictionary<string, JsonElement>();
        foreach (var line in File.ReadAllLines(report).Where(l => l.StartsWith("npc_skin ")))
        {
            var parts = line.Split(' ', 3);
            rows[parts[1]] = JsonDocument.Parse(parts[2]).RootElement.Clone();
        }
        var cel = new[] { 1.247, 0.742, 0.397 };

        var h = rows["head_default"];
        var c = Vec(h.GetProperty("cel_tone"));
        for (int i = 0; i < 3; i++) Assert.InRange(c[i], cel[i] - 0.01, cel[i] + 0.01);
        Assert.Equal(0.3, h.GetProperty("back_spec").GetDouble(), 3);
        Assert.Equal(1.0, h.GetProperty("back_neutral").GetDouble(), 3);
        Assert.Equal(1.0, h.GetProperty("back_neutral_sky").GetDouble(), 3);
        Assert.Equal(new[] { 0.6, 0.15, 0.08 }, Vec(h.GetProperty("throat_terminator")).Select(x => Math.Round(x, 3)).ToArray());
        Assert.True(h.GetProperty("skin_zones").GetBoolean());
        Assert.True(h.GetProperty("features").GetBoolean());
        Assert.True(h.GetProperty("ao_map").GetBoolean());
        Assert.True(h.GetProperty("next_pass_shader").GetBoolean());
        Assert.True(h.GetProperty("brow_dyed").GetBoolean());

        var o = rows["head_override"];
        Assert.Equal(0.5, o.GetProperty("back_spec").GetDouble(), 3);
        Assert.Equal(0.4, o.GetProperty("zone_colour").GetDouble(), 3);
        Assert.Equal(new[] { 1.0, 1.0, 1.0 }, Vec(o.GetProperty("cel_tone")));
        Assert.Equal(0.5, o.GetProperty("brow_strength").GetDouble(), 3);

        var b = rows["body_default"];
        var bc = Vec(b.GetProperty("cel_tone"));
        for (int i = 0; i < 3; i++) Assert.InRange(bc[i], cel[i] - 0.01, cel[i] + 0.01);
        Assert.False(b.GetProperty("skin_zones").GetBoolean());
        foreach (var r in new[] { h, b }) Assert.Equal(new[] { 1.0, 1.0, 1.0 }, Vec(r.GetProperty("cel_fill_tone")));

        // A darker paint (0.65 of her paint's luminance) takes less of the cel warmth on its albedo and the rest on the
        // key's fill, the product still her cel tone; under the deep onset its albedo's factor is grey.
        var lk = 0.2126 * cel[0] + 0.7152 * cel[1] + 0.0722 * cel[2];
        var mid = rows["head_mid"];
        var ma = Vec(mid.GetProperty("cel_tone"));
        var mf = Vec(mid.GetProperty("cel_fill_tone"));
        Assert.InRange(ma[0] / ma[2], 1.2, 1.8);   // (warm 0.24: R/B 1.45, her fair 3.14)
        for (int i = 0; i < 3; i++) Assert.InRange(ma[i] * mf[i], cel[i] - 0.01, cel[i] + 0.01);
        var dp = Vec(rows["body_deep"].GetProperty("cel_tone"));
        for (int i = 0; i < 3; i++) Assert.InRange(dp[i], lk - 0.01, lk + 0.01);
        var w1 = rows["head_mid_warm1"];
        var wc = Vec(w1.GetProperty("cel_tone"));
        for (int i = 0; i < 3; i++) Assert.InRange(wc[i], cel[i] - 0.01, cel[i] + 0.01);
        Assert.Equal(new[] { 1.0, 1.0, 1.0 }, Vec(w1.GetProperty("cel_fill_tone")));
    }
}
