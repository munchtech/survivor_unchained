using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The P4 pack gate (P4Gate): judged PASS clips go in, the rest are skipped unless it is a review pack.</summary>
public class P4GateTests
{
    static JsonElement Of(string json) { using var d = JsonDocument.Parse(json); return d.RootElement.Clone(); }

    [Fact] public void JudgedPassWithBuildIsTaken() =>
        Assert.True(P4Gate.Takes(Of("{\"judged\": {\"verdict\": \"PASS\", \"build\": \"abc\"}}"), false));

    [Fact] public void NoJudgedIsSkipped() => Assert.False(P4Gate.Takes(Of("{\"name\": \"x\"}"), false));

    [Theory]
    [InlineData("{\"judged\": {\"verdict\": \"FAIL\", \"build\": \"abc\"}}")]
    [InlineData("{\"judged\": {\"verdict\": \"PASS\", \"build\": \"\"}}")]
    [InlineData("{\"judged\": {\"verdict\": \"PASS\"}}")]
    [InlineData("{\"judged\": true}")]
    public void WrongVerdictOrEmptyBuildIsSkipped(string json) => Assert.False(P4Gate.Takes(Of(json), false));

    [Fact] public void ReviewTakesEverything()
    {
        Assert.True(P4Gate.Takes(Of("{}"), true));
        Assert.True(P4Gate.Takes(Of("{\"judged\": {\"verdict\": \"FAIL\"}}"), true));
    }

    [Fact] public void NamedReviewTakesOnlyTheNamedUnjudged()
    {
        var names = new System.Collections.Generic.HashSet<string> { "a" };
        Assert.True(P4Gate.Takes(Of("{}"), "a", false, names));
        Assert.False(P4Gate.Takes(Of("{}"), "b", false, names));
        Assert.True(P4Gate.Takes(Of("{\"judged\": {\"verdict\": \"PASS\", \"build\": \"abc\"}}"), "b", false, names));
        Assert.True(P4Gate.Takes(Of("{}"), "b", true, new System.Collections.Generic.HashSet<string>()));
    }

    [Fact] public void ReviewOfReadsAllAndNames()
    {
        var (all, names) = P4Gate.ReviewOf(new[] { "--review" });
        Assert.True(all); Assert.Empty(names);
        (all, names) = P4Gate.ReviewOf(new[] { "x", "--review=a, b,,c" });
        Assert.False(all); Assert.Equal(new[] { "a", "b", "c" }, names.OrderBy(n => n));
        (all, names) = P4Gate.ReviewOf(new string[0]);
        Assert.False(all); Assert.Empty(names);
        Assert.False(P4Gate.Review(new[] { "--review=a" }));
    }

    [Fact] public void ReviewReadsTheArg()
    {
        Assert.True(P4Gate.Review(new[] { "a", "--review" }));
        Assert.False(P4Gate.Review(new string[0]));
    }
}
