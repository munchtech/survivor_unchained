using System;
using System.Diagnostics;
using System.IO;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>Every draft card a calling can be dealt fits its card: the body clear of the footer, no line hidden,
/// medallions, titles and footers level across the row (tools_scenes/CardFit.cs, docs/team/DEMO_GATE.md item 3).
/// The one engine test in this suite: it builds the game and runs Godot headless on the harness (a short layout
/// pass, no turn needed). Without the engine or an imported project here, it says so and passes.</summary>
[Collection("engine")]
public sealed class DraftCardFitTests(ITestOutputHelper log)
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

    [Fact]
    public void Every_draft_card_fits_its_card()
    {
        var dir = GodotDir();
        var exe = Environment.GetEnvironmentVariable("GODOT_EXE") ?? GodotExe;
        if (dir == null || !File.Exists(exe) || !Directory.Exists(Path.Combine(dir, ".godot", "imported")))
        {
            log.WriteLine($"skipped: no Godot at {exe}, or no imported project beside the tests");
            return;
        }
        // (the harness runs from the game's dll: built now, so it is not stale)
        var build = Run("dotnet", "build SurvivorUnchained.csproj -v q -nologo", dir, 10);
        Assert.True(build.Code == 0, "the game did not build:\n" + build.Out);
        var report = Path.Combine(Path.GetTempPath(), $"card_fit_{Environment.ProcessId}.json");
        var run = Run(exe, $"--headless --path \"{dir}\" -s res://tools_scenes/card_fit.gd -- \"{report}\"", dir, 10);
        foreach (var line in run.Out.Split('\n')) if (line.StartsWith("card_fit")) log.WriteLine(line.TrimEnd());
        Assert.True(run.Code == 0, $"draft cards that do not fit (exit {run.Code}, report {report}):\n{run.Out}");
    }
}
