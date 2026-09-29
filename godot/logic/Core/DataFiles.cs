using System;
using System.IO;

namespace SurvivorUnchained.Core;

/// <summary>
/// The game's data files, by their path under data/ ('content/items.json',
/// 'zones/verge/heights.bin'). The game points these at res://data (Godot's
/// own file access, which works inside an exported pack); by default they
/// find godot/data on disk, for the tests and tools.
/// </summary>
public static class DataFiles
{
    public static Func<string, string> Text = rel => File.ReadAllText(Path.Combine(Dir, rel));
    public static Func<string, byte[]> Bytes = rel => File.ReadAllBytes(Path.Combine(Dir, rel));

    static string? dir;

    /// <summary>Where godot/data is on disk.</summary>
    public static string Dir => dir ??= Find() ?? throw new DirectoryNotFoundException("data/content not found above " + AppContext.BaseDirectory);

    static string? Find()
    {
        foreach (var start in new[] { AppContext.BaseDirectory, Directory.GetCurrentDirectory() })
            for (var d = new DirectoryInfo(start); d != null; d = d.Parent)
            {
                if (Directory.Exists(Path.Combine(d.FullName, "data", "content"))) return Path.Combine(d.FullName, "data");
                if (Directory.Exists(Path.Combine(d.FullName, "godot", "data", "content"))) return Path.Combine(d.FullName, "godot", "data");
            }
        return null;
    }
}
