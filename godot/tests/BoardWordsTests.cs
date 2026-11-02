using System;
using SurvivorUnchained.Rpg;
using Xunit;

namespace SurvivorUnchained.Tests;

public sealed class BoardWordsTests
{
    [Fact]
    public void EveryRefusalHasWords()
    {
        foreach (LampNo n in Enum.GetValues<LampNo>()) Assert.Equal(n != LampNo.None, BoardWords.Why(n).Length > 0);
        foreach (WickNo n in Enum.GetValues<WickNo>()) Assert.Equal(n != WickNo.None, BoardWords.Why(n).Length > 0);
    }
}
