using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Sound;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The sound bank as data (data/content/sounds.json): the real file reads, its numbers are sane, the fallback
/// chain and the materials work, and an event whose takes are not recorded yet is pending, not banked.</summary>
public class SoundBankTests
{
    static string Root()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? Directory.GetCurrentDirectory();
    }

    static SoundBankData Real() => SoundBankData.Parse(File.ReadAllText(Path.Combine(Root(), "data", "content", "sounds.json")));

    static HashSet<string> Families() =>
        JsonSerializer.Deserialize<Dictionary<string, int>>(File.ReadAllText(Path.Combine(Root(), "art", "sound", "sounds.json")))!.Keys.ToHashSet();

    [Fact]
    public void TheRealFileParsesWithNoProblems()
    {
        var d = Real();
        var fam = Families();
        Assert.Empty(d.Problems(fam.Contains));
        Assert.Equal(0.85, d.Buses["master"].Level);
        Assert.Equal(0.55, d.Buses["music"].Send);
        Assert.Equal(0.6, d.Duck("talk", "music", 1));
        Assert.Equal(0.3, d.Duck("chest", "music", 1));
        Assert.Equal(0.5, d.Duck("nothing", "music", 0.5));
    }

    [Fact]
    public void MaterialsFollowTheFamilyAndFleshIsTheDefault()
    {
        var d = Real();
        Assert.Equal("bone", d.MaterialOf("Undead"));
        Assert.Equal("hide", d.MaterialOf("Wolf"));
        Assert.Equal("rot", d.MaterialOf("Blighted"));
        Assert.Equal("flesh", d.MaterialOf("Somebody"));
    }

    [Fact]
    public void FirstTakesTheFirstIdThatIsAnEvent()
    {
        var d = SoundBankData.Parse("""{"events":{"hit.flesh":{"layers":[{"take":"a"}]},"hit.bone":{"layers":[{"take":"b"}]}}}""");
        Assert.Equal("hit.bone", d.First("hit.bone.crit", "hit.bone", "hit.flesh"));
        Assert.Equal("hit.flesh", d.First("hit.rot.crit", "hit.rot", "hit.flesh"));
        Assert.Null(d.First("nothing"));
    }

    [Fact]
    public void AnEventWithoutItsTakesIsPendingNotBanked()
    {
        var d = SoundBankData.Parse("""{"events":{"hit.bone":{"layers":[{"take":"hit_bone"},{"take":"have"}]},"door":{"layers":[{"take":"have"}]}}}""");
        Func<string, bool> has = f => f == "have";
        Assert.False(d.Banked("hit.bone", has));
        Assert.True(d.Banked("door", has));
        Assert.False(d.Banked("missing", has));
        Assert.Equal(["hit.bone: hit_bone"], d.Pending(has));
        Assert.Empty(d.Problems(has));   // missing takes are waiting, not wrong
    }

    [Fact]
    public void TheRealExampleEventIsInertUntilItsFamilyExists()
    {
        var d = Real();
        var fam = Families();
        Assert.Equal(fam.Contains("hit_flesh"), d.Banked("hit.flesh", fam.Contains));
    }

    [Fact]
    public void BadNumbersAreProblems()
    {
        var d = SoundBankData.Parse("""
            {"buses":{"nope":{"level":1}},
             "events":{"a":{"bus":"x","gate":[0,70],"layers":[{"take":"t","gain":5,"pitch":[1.2,0.8]}]},
                       "b":{"layers":[]}}}
            """);
        var p = d.Problems(_ => true);
        Assert.Contains(p, s => s.Contains("unknown bus 'x'"));
        Assert.Contains(p, s => s.Contains("buses.nope"));
        Assert.Contains(p, s => s.StartsWith("a: gate"));
        Assert.Contains(p, s => s.Contains("gain 5"));
        Assert.Contains(p, s => s.Contains("pitch"));
        Assert.Contains(p, s => s.StartsWith("b: no layers"));
    }
}
