using System.Collections.Generic;
using System.Globalization;
using Godot;

namespace SurvivorUnchained;

/// <summary>
/// Screenshots for judging the slice without a screen (tools/godot/run.sh):
///
///   -- --shot NAME [--seconds S] [--every T --count N]
///
/// runs S seconds of game time (the engine is started with --fixed-fps, so a
/// slow software renderer still steps time evenly), saves
/// godot/.shots/NAME.png, and quits; with --every and --count, a run of frames
/// NAME_00.png... T seconds apart. Other slice options are read by name
/// (Args.Get).
/// </summary>
public static class Args
{
    static Dictionary<string, string>? parsed;

    static Dictionary<string, string> All()
    {
        if (parsed != null) return parsed;
        parsed = new();
        var a = OS.GetCmdlineUserArgs();
        for (int i = 0; i < a.Length; i++)
        {
            if (!a[i].StartsWith("--")) continue;
            var key = a[i][2..];
            var val = i + 1 < a.Length && !a[i + 1].StartsWith("--") ? a[++i] : "1";
            parsed[key] = val;
        }
        return parsed;
    }

    public static string? Get(string key) => All().TryGetValue(key, out var v) ? v : null;
    public static float Num(string key, float fallback) =>
        float.TryParse(Get(key), NumberStyles.Float, CultureInfo.InvariantCulture, out var v) ? v : fallback;
    public static bool Has(string key) => All().ContainsKey(key);
}

public partial class Shots : Node
{
    string name = "";
    float seconds, every;
    int count, taken;
    double time;

    public override void _Ready()
    {
        name = Args.Get("shot") ?? "";
        if (name == "") { SetProcess(false); return; }
        seconds = Args.Num("seconds", 3);
        every = Args.Num("every", 0);
        count = (int)Args.Num("count", every > 0 ? 8 : 1);
        ProcessMode = ProcessModeEnum.Always;
    }

    public override void _Process(double delta)
    {
        time += delta;
        var due = seconds + taken * every;
        if (time < due) return;
        var dir = ProjectSettings.GlobalizePath("res://.shots");
        DirAccess.MakeDirRecursiveAbsolute(dir);
        var file = every > 0 ? $"{dir}/{name}_{taken:00}.png" : $"{dir}/{name}.png";
        GetViewport().GetTexture().GetImage().SavePng(file);
        GD.Print($"saved {file} at {time:0.00}s");
        // --navcheck: the open screen's focus routes walked as the picture is taken.
        if (Args.Has("navcheck")) Audit(GetTree().Root);
        taken++;
        if (taken >= count) GetTree().Quit();
    }

    static void Audit(Node n)
    {
        if (n is Ui.Overlay o && o.IsVisibleInTree())
            foreach (var line in o.NavAudit()) GD.Print($"nav {o.Kind}: {line}");
        foreach (var c in n.GetChildren()) Audit(c);
    }
}
