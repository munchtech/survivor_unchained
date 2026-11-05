using System.Linq;
using SurvivorUnchained.Cinema;
using Xunit;

/// <summary>CineLines.Pages: a long line paged by sentence across its take, two lines a page at most, the words
/// unchanged; when each page comes up follows the take's segments.</summary>
public class CinePagesTests
{
    const string Heart = "The guard goes down, and stays down, and the stair is quiet. Under him, in its notch, a stone the size of a heart comes up violet, and lifts, and comes to your hand. It is warm, and then it is not. Whatever was in it goes down through your hand, the way the first one went down the hole, and the stone is only a stone.";
    static double W(string s) => s.Length * 10.0;
    const double Max = 700;

    [Fact]
    public void LongLinePagedTwoLinesEachWordsKept()
    {
        var pages = CineLines.Pages(Heart, W, Max, 25.66);
        Assert.True(pages.Count >= 3);
        Assert.Equal(Heart, string.Join(" ", pages.Select(p => p.Text)));
        foreach (var (text, _) in pages)
            Assert.True(W(text) <= Max || CineLines.Break(text, W, Max).Contains('\n'), text);
        Assert.Equal(0, pages[0].At);
        for (int i = 1; i < pages.Count; i++) Assert.True(pages[i].At > pages[i - 1].At && pages[i].At < 25.66);
        // whole sentences while they fit: every page but one cut inside a too-long sentence ends a sentence
        Assert.All(pages, p => Assert.Contains(p.Text[^1], ".,"));
    }

    [Fact]
    public void ShortOrScriptBrokenLineIsOnePage()
    {
        Assert.Single(CineLines.Pages("It is warm, and then it is not.", W, Max, 3));
        Assert.Single(CineLines.Pages(Heart.Replace(". Under", ". / Under"), W, Max, 25));
    }

    [Fact]
    public void PagesFollowTheVoicesSegments()
    {
        // the voice reads nothing for its first 5 s, then the whole text over 10 s
        var segs = new System.Collections.Generic.List<double[]> { new[] { 5.0, 15.0, 0.0, 1.0 } };
        var pages = CineLines.Pages(Heart, W, Max, 15, segs);
        Assert.All(pages.Skip(1), p => Assert.InRange(p.At, 4.75, 15));
        var even = CineLines.Pages(Heart, W, Max, 15);
        Assert.True(pages[1].At > even[1].At);
    }
}
