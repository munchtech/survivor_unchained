using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>Every shader file the game has, loaded once at the opening and held for the whole run (lane K, 19 Nov). Godot's
/// resource cache holds a shader only while something uses it: an effect's shader (the Warden's dash glint and trail, fx_p7)
/// was freed with the effect's last material and loaded and compiled afresh at the next use, 22-48 ms on the main thread at
/// every Space and Flare (measured in the demo exe). Held here, a later GD.Load finds it in the cache, compiled.</summary>
public static class ShaderKeep
{
    static readonly List<Shader> held = new();
    static readonly List<ShaderMaterial> mats = new();
    public static int Count => held.Count;

    /// <summary>Loads `perStep` shaders a step (each yield: the share done, 0..1) and holds them.</summary>
    public static IEnumerable<float> Load(int perStep = 8)
    {
        var files = new List<string>();
        foreach (var root in new[] { "res://shaders", "res://art" }) Find(root, files);
        long t0 = System.Diagnostics.Stopwatch.GetTimestamp();
        int n = 0;
        foreach (var f in files)
        {
            if (ResourceLoader.Load(f) is Shader s) held.Add(s);
            if (++n % perStep == 0) yield return (float)n / files.Count;
        }
        GD.Print($"load: {held.Count} shaders held for the run, loaded in {System.Diagnostics.Stopwatch.GetElapsedTime(t0).TotalMilliseconds:0} ms");
        // (P2 task 5) The weapons a Flare forms in her hand (The Long Cut's Sunderer: LampIron.SunderBlade) were loaded cold
        // at the first press, about 13-15 ms and 6 mesh pipelines on the main thread (measured in the proof exe). Held here,
        // the press finds them in the cache.
        var arms = new List<string>();
        Find("res://art/weapons", arms, ".glb");
        foreach (var f in arms) if (ResourceLoader.Load(f) is PackedScene p) scenes.Add(p);
        yield return 1;
    }

    static readonly List<PackedScene> scenes = new();

    /// <summary>A material made for each held shader (and held with it), at most `budgetMs` a step. A shader's first material
    /// is where Godot readies it for drawing: 20-23 ms on the main thread for each of the Warden's dash shaders at the first
    /// Space, the Flare's at its first cast. Done after the title's place and her figure are built (their shaders are ready by
    /// then, so theirs cost nothing here), behind the opening's card.</summary>
    public static IEnumerable<float> Ready(double budgetMs = 40)
    {
        var cost = new List<(double ms, string f)>();
        double total = 0, step = 0;
        for (int i = 0; i < held.Count; i++)
        {
            long t = System.Diagnostics.Stopwatch.GetTimestamp();
            mats.Add(new ShaderMaterial { Shader = held[i] });
            double ms = System.Diagnostics.Stopwatch.GetElapsedTime(t).TotalMilliseconds;
            total += ms; step += ms;
            cost.Add((ms, held[i].ResourcePath));
            if (step >= budgetMs) { step = 0; yield return (float)(i + 1) / held.Count; }
        }
        cost.Sort((a, b) => b.ms.CompareTo(a.ms));
        GD.Print($"load: {mats.Count} shaders readied in {total:0} ms (most: {string.Join(", ", cost.GetRange(0, Math.Min(8, cost.Count)).ConvertAll(c => $"{c.f[(c.f.LastIndexOf('/') + 1)..]} {c.ms:0}"))})");
        yield return 1;
    }

    static void Find(string dir, List<string> into, string ext = ".gdshader")
    {
        using var d = DirAccess.Open(dir);
        if (d == null) return;
        foreach (var sub in d.GetDirectories()) Find($"{dir}/{sub}", into, ext);
        foreach (var file in d.GetFiles())
        {
            // (an export may list a resource under its .remap, an imported one under its .import)
            string name = file.EndsWith(".remap") ? file[..^6] : file.EndsWith(".import") ? file[..^7] : file;
            if (name.EndsWith(ext) && !into.Contains($"{dir}/{name}")) into.Add($"{dir}/{name}");
        }
    }
}
