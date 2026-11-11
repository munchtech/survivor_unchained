using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her clips beats (HerEvents): seconds to 60 fps frames, missing keys, order, the empty file, the round trip.</summary>
public class HerEventsTests
{
    static HerEvents.Beats? Of(string json) { using var d = JsonDocument.Parse(json); return HerEvents.FromClip(d.RootElement.Clone()); }

    [Fact]
    public void SecondsBecomeFramesAt60Rounded()
    {
        var b = Of("{\"beats\": {\"contact\": [0.5, 0.2084], \"hold\": [0.5, 1.0], \"cancel\": 0.7, \"loop\": [0.25, 0.9], \"events\": {\"land\": 1.2, \"takeoff\": 0.3}}}")!;
        Assert.Equal(new[] { 13, 30 }, b.Contact);          // (0.2084 s = 12.504 frames; sorted)
        Assert.Equal(new[] { 30, 60 }, b.Hold);
        Assert.Equal(42, b.Cancel);
        Assert.Equal(new[] { 15, 54 }, b.Loop);
        Assert.Equal(new[] { ("takeoff", 18), ("land", 72) }, b.Events);   // (by time, not by name)
        Assert.Equal(0.3, b.EventSeconds("takeoff")!.Value, 6);
        Assert.Equal((0.25, 0.9), b.LoopSeconds!.Value);
    }

    [Fact]
    public void MissingKeysStayMissingAndNoBeatsMeansNull()
    {
        var b = Of("{\"beats\": {\"cancel\": 1}}")!;
        Assert.Empty(b.Contact); Assert.Null(b.Hold); Assert.Null(b.Loop); Assert.Empty(b.Events); Assert.Equal(60, b.Cancel);
        Assert.Null(Of("{\"name\": \"x\"}"));
        Assert.Null(Of("{\"beats\": {}}"));
        Assert.Null(b.EventSeconds("land"));
    }

    [Fact]
    public void FileIsSortedKeyedInOrderAndRoundTrips()
    {
        var all = new Dictionary<string, HerEvents.Beats>
        {
            ["shield_charge"] = Of("{\"beats\": {\"events\": {\"impact\": 1.0, \"launch\": 0.1}, \"loop\": [0.2, 0.6]}}")!,
            ["heroic_leap"] = Of("{\"beats\": {\"events\": {\"land\": 1.0, \"takeoff\": 0.1}, \"cancel\": 1.5, \"contact\": [1.0]}}")!,
        };
        string text = HerEvents.Serialize(all);
        Assert.True(text.IndexOf("heroic_leap") < text.IndexOf("shield_charge"));
        var h = text[text.IndexOf("heroic_leap")..text.IndexOf("shield_charge")];
        Assert.True(h.IndexOf("contact") < h.IndexOf("cancel") && h.IndexOf("cancel") < h.IndexOf("events"));
        Assert.True(h.IndexOf("takeoff") < h.IndexOf("land"));
        Assert.Contains("\n      \"cancel\": 90,\n", text);
        Assert.Equal(text, HerEvents.Serialize(HerEvents.Load(text)));
        Assert.Equal(new[] { 12, 36 }, HerEvents.Load(text)["shield_charge"].Loop);
    }

    [Fact]
    public void EmptyFileAndBadTextAreEmpty()
    {
        string text = HerEvents.Serialize(new Dictionary<string, HerEvents.Beats>());
        Assert.Equal("{\n  \"fps\": 60,\n  \"clips\": {}\n}\n", text);
        Assert.Empty(HerEvents.Load(text));
        Assert.Empty(HerEvents.Load("not json"));
        Assert.Empty(HerEvents.Load(""));
    }

    // The pack and M3's contact measure share the file: a pack replaces its own clips' entries and keeps the others.
    [Fact]
    public void APackKeepsTheClipsItDoesNotBuild()
    {
        var none = System.Array.Empty<(string, int)>();
        var file = new Dictionary<string, HerEvents.Beats>
        {
            ["sword_fore"] = new(new[] { 5 }, null, null, null, none),
            ["heroic_leap"] = new(new[] { 40 }, null, null, null, none),
            ["old_p4"] = new(new[] { 9 }, null, null, null, none),
        };
        var packed = new Dictionary<string, HerEvents.Beats> { ["heroic_leap"] = new(new[] { 44 }, new[] { 44, 48 }, 58, null, none) };
        var all = HerEvents.Merge(file, packed, new[] { "heroic_leap", "old_p4", "idle_warden" });
        Assert.Equal(new[] { "heroic_leap", "sword_fore" }, all.Keys.OrderBy(k => k, System.StringComparer.Ordinal).ToArray());
        Assert.Equal(new[] { 44 }, all["heroic_leap"].Contact);
        Assert.Equal(new[] { 5 }, all["sword_fore"].Contact);
        Assert.Equal(HerEvents.Serialize(all), HerEvents.Serialize(HerEvents.Load(HerEvents.Serialize(all))));
    }

    [Fact]
    public void BlendInIsCarriedInSecondsAndReadWithADefault()
    {
        // (A1 blend_in: a spec's beats.blend_in, seconds, from the built clip into the file and back; additive)
        var with = Of("{\"beats\": {\"contact\": [0.7333], \"blend_in\": 0.12}}")!;
        Assert.Equal(0.12, with.BlendIn);
        Assert.Null(Of("{\"beats\": {\"contact\": [0.7333]}}")!.BlendIn);
        Assert.Null(Of("{\"beats\": {\"contact\": [0.7333], \"blend_in\": -1}}")!.BlendIn);
        Assert.Equal(0.1, Of("{\"beats\": {\"blend_in\": 0.1}}")!.BlendIn);       // (a clip with nothing else keeps its entry)
        var none = System.Array.Empty<(string, int)>();
        var all = new Dictionary<string, HerEvents.Beats>
        {
            ["heroic_leap"] = with,
            ["iron_vow"] = new(new[] { 144 }, null, 148, null, none),
        };
        string text = HerEvents.Serialize(all);
        Assert.Contains("      \"contact\": [44],\n      \"blend_in\": 0.12\n", text);
        Assert.Equal(1, text.Split("blend_in").Length - 1);                       // (absent where the spec has none)
        var read = HerEvents.Load(text);
        Assert.Equal(text, HerEvents.Serialize(read));
        // the read the view makes: present -> used; absent (or no such clip) -> the caller's default (PlayerView: its usual fade)
        Assert.Equal(0.12, HerEvents.BlendIn(read, "heroic_leap", 0.25));
        Assert.Equal(0.25, HerEvents.BlendIn(read, "iron_vow", 0.25));
        Assert.Equal(0.25, HerEvents.BlendIn(read, "no_such_clip", 0.25));
        Assert.Equal(0.05, HerEvents.BlendIn("no_such_clip", 0.05));               // (the game's file, read once)
        // the sim's reader of the same file (Content.HerEvents) does not mind the new key
        var sim = SurvivorUnchained.Core.Json.Parse<SurvivorUnchained.Content.HerEvents.File>(text);
        Assert.Equal(new[] { 44 }, sim.Clips["heroic_leap"].Contact);
    }
}
