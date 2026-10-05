using System;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>
/// What a release build leaves out (the legal brief, issue 3; ASSET_PROVENANCE
/// BU-02). Steam's mature-content survey covers everything uploaded, reachable
/// or not, so the bodies no one plays, the unused third-party packs, the
/// developer's tools and the placeholder voices stay out of every preset's
/// pack. This fails if any preset loses one of them.
/// </summary>
public class ExportTests
{
    static readonly string Presets = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../../../export_presets.cfg"));

    static readonly string[] MustExclude =
    {
        "tools_scenes/*",
        "art/people/anime_female.glb", "art/people/her_Hair_*.glb",
        "art/people/woman.glb", "art/people/woman_mask.png",
        // (Until his base garment exists: his body has bare buttocks.)
        "art/people/hero.glb",
        "assets/characters/*", "assets/props/*", "assets/anim/humanoid.glb",
        "assets/ground/*.ktx2", "assets/people/*.bake.webp", "assets/env/polyhaven/*",
        "art/vo/*",
    };

    [Fact]
    public void Every_preset_leaves_out_what_does_not_ship()
    {
        var text = File.ReadAllText(Presets);
        var presets = Regex.Matches(text, @"(?m)^\[preset\.\d+\]\s*$").Count;
        var filters = Regex.Matches(text, @"(?m)^exclude_filter=""([^""]*)""").Select(m => m.Groups[1].Value.Split(',').Select(s => s.Trim()).ToHashSet()).ToList();
        Assert.True(presets >= 3, "the Windows, Linux and macOS presets");
        Assert.Equal(presets, filters.Count);
        foreach (var f in filters)
            foreach (var path in MustExclude)
                Assert.True(f.Contains(path), $"an export preset no longer leaves out {path}");
    }
}
