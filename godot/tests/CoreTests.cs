using SurvivorUnchained.Core;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The random stream, hashes and noise are the web game's, value for
/// value (the expected numbers come from src/core under Node), so a seed
/// lays out the same place and plays out the same fight in both.</summary>
public class CoreTests
{
    [Fact]
    public void Rng_matches_the_web_stream()
    {
        var r = new Rng(12345);
        foreach (var v in new[] { 0.9797282677609473, 0.3067522644996643, 0.484205421525985, 0.817934412509203, 0.5094283693470061 })
            Assert.Equal(v, r.Next(), 15);
        var r2 = new Rng(0xdeadbeef);
        foreach (var v in new[] { 0.9413696140982211, 0.26719574979506433, 0.772033357527107 })
            Assert.Equal(v, r2.Next(), 15);
    }

    [Fact]
    public void Hashes_match_the_web()
    {
        Assert.Equal(0.06072393315844238, MathX.Hash2(3, 7), 15);
        Assert.Equal(0.7004074037540704, MathX.Hash2(-12, 40, 9), 15);
        Assert.Equal(0.24554795678704977, MathX.Hash2(100000, 2, 2147483647), 15);
        Assert.Equal(0.14165593753568828, MathX.Hash1(17, 5), 15);
        Assert.Equal(3802237166u, MathX.HashString("verge"));
        Assert.Equal(1455070393u, MathX.HashString("the ford-warden"));
    }

    [Fact]
    public void Noise_matches_the_web()
    {
        var n = new Noise2D(1337);
        Assert.Equal(-0.4019101770260303, n.Noise(0.3, 0.7), 14);
        Assert.Equal(-0.8446338478885317, n.Noise(-12.5, 3.25), 14);
        Assert.Equal(0.4669759631861622, n.Fbm(1.1, 2.2), 14);
        Assert.Equal(0.1951797081904813, n.Ridged(0.5, 0.25), 14);
    }
}
