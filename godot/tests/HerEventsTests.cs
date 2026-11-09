using System.Collections.Generic;
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
}
