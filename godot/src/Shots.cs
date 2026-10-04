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
    float seconds, every, until;
    int count, taken;
    double time;
    static Shots? live;
    /// <summary>Frames the game asks for (--on boss): what, and when.</summary>
    readonly List<(double At, string Tag)> wanted = new();
    readonly Dictionary<string, int> tagged = new();

    /// <summary>--on boss: a frame a moment after each boss move is marked, its Break,
    /// its stagger and its arrival (a telegraph lasts a second; a frame every second
    /// misses most of them). The run ends at --until seconds.</summary>
    public static bool On(string what) => live != null && Args.Get("on") is string on && System.Array.IndexOf(on.Split(','), what) >= 0;

    public static void Want(string tag, double inSeconds)
    {
        if (live == null) return;
        live.wanted.Add((live.time + inSeconds, tag));
    }

    public override void _Ready()
    {
        name = Args.Get("shot") ?? "";
        if (name == "") { SetProcess(false); return; }
        live = this;
        seconds = Args.Num("seconds", 3);
        every = Args.Num("every", 0);
        until = Args.Num("until", Args.Has("on") ? 120 : 0);
        count = (int)Args.Num("count", every > 0 ? 8 : Args.Has("on") ? 0 : 1);
        ProcessMode = ProcessModeEnum.Always;
    }

    public override void _Process(double delta)
    {
        time += delta;
        for (int i = wanted.Count - 1; i >= 0; i--)
        {
            if (time < wanted[i].At) continue;
            var tag = Safe(wanted[i].Tag);
            wanted.RemoveAt(i);
            int k = tagged[tag] = tagged.GetValueOrDefault(tag) + 1;
            var d = ProjectSettings.GlobalizePath("res://.shots");
            DirAccess.MakeDirRecursiveAbsolute(d);
            var f = $"{d}/{name}_{tag}_{k}.png";
            GetViewport().GetTexture().GetImage().SavePng(f);
            GD.Print($"saved {f} at {time:0.00}s");
        }
        if (until > 0 && time >= until) { GetTree().Quit(); return; }
        if (taken >= count) return;
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
        if (taken >= count && until <= 0) GetTree().Quit();
    }

    static string Safe(string s)
    {
        var o = new System.Text.StringBuilder();
        foreach (var c in s.ToLowerInvariant()) o.Append(char.IsLetterOrDigit(c) ? c : '_');
        return o.ToString().Trim('_');
    }

    static void Audit(Node n)
    {
        if (n is Ui.Overlay o && o.IsVisibleInTree())
            foreach (var line in o.NavAudit()) GD.Print($"nav {o.Kind}: {line}");
        foreach (var c in n.GetChildren()) Audit(c);
    }
}
