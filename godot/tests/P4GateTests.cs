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

    [Fact] public void ReviewReadsTheArg()
    {
        Assert.True(P4Gate.Review(new[] { "a", "--review" }));
        Assert.False(P4Gate.Review(new string[0]));
    }
}
