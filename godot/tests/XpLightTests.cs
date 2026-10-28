using System;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The Drowned Girl's experience light (logic/Play/XpLight.cs, UI 18 pick (c)): nothing at rest; a gain runs
/// to the fraction, holds and fades; gains batch (one run a second, the held front sliding on); a level-up lights all;
/// the fraction maps onto the run; the numbers' card and its hold key.</summary>
public class XpLightTests
{
    static XpLight Fresh(double f = 0.2, int lv = 3, bool ember = true)
    {
        var x = new XpLight();
        x.Feed(f, lv, ember);
        x.Step(5);
        return x;
    }

    static void Run(XpLight x, double sec) { for (double t = 0; t < sec - 1e-9; t += 1 / 60.0) x.Step(Math.Min(1 / 60.0, sec - t)); }

    [Fact]
    public void NothingAtRest()
    {
        var x = Fresh();
        Assert.False(x.Lit);
        x.Feed(0.2, 3, true);
        Run(x, 3);
        Assert.False(x.Lit);
        Assert.Equal(0, x.Strength);
    }

    [Fact]
    public void FirstFeedIsSilent()
    {
        var x = new XpLight();
        x.Feed(0.7, 9, false);
        Run(x, 0.3);
        Assert.False(x.Lit);
        Assert.False(x.Rose);
    }

    [Fact]
    public void AGainRunsHoldsAndFades()
    {
        var x = Fresh();
        x.Feed(0.5, 3, true);
        Run(x, 0.3);
        Assert.True(x.Lit);
        Assert.InRange(x.Front, 0.05, 0.49);           // on its way from her hair
        Run(x, 0.35);
        Assert.Equal(0.5, x.Front, 3);                 // at the fraction by 0.6 s
        Run(x, 1.3);
        Assert.Equal(1, x.Strength, 3);                // held ~1.5 s
        Run(x, 0.5);
        Assert.InRange(x.Strength, 0.0, 0.99);         // fading
        Run(x, 0.6);
        Assert.False(x.Lit);                           // out by ~2.6 s
    }

    [Fact]
    public void GainsBatchAndTheFrontSlides()
    {
        var x = Fresh(0.1);
        x.Feed(0.2, 3, true);
        Run(x, 0.8);
        Assert.Equal(0.2, x.Front, 3);
        // gains every 0.25 s for 4 s: one light that stays up, its front sliding forward as a meter
        double f = 0.2, last = x.Front;
        for (int i = 0; i < 16; i++)
        {
            f += 0.03;
            x.Feed(f, 3, true);
            Run(x, 0.25);
            Assert.True(x.Lit);
            Assert.Equal(1, x.Strength, 3);
            Assert.True(x.Front >= last - 1e-9, "the front never runs back to her hair while gains keep coming");
            last = x.Front;
        }
        Assert.InRange(x.Front, f - 0.04, f + 1e-9);
    }

    [Fact]
    public void AtMostOneRunASecond()
    {
        var x = Fresh(0.1);
        x.Feed(0.3, 4, true);   // a level-up (the whole lights; the run waits)
        Assert.True(x.Rose);
        Run(x, 0.2);
        x.Feed(0.35, 4, true);  // a gain 0.2 s later: no run yet
        Run(x, 0.1);
        Assert.Equal(0, x.Strength);
        Run(x, 1.0);            // the gap is past and the whole is done: the waiting run starts from her hair
        Assert.True(x.Strength > 0);
        Assert.True(x.Front < 0.35);
    }

    [Fact]
    public void ACaughtFadeComesBackUpWhereItIs()
    {
        var x = Fresh(0.1);
        x.Feed(0.4, 3, true);
        Run(x, 2.2);                                   // fading
        double front = x.Front;
        Assert.True(x.Strength < 1);
        x.Feed(0.45, 3, true);
        Run(x, 0.2);
        Assert.Equal(1, x.Strength, 3);
        Assert.True(x.Front >= front, "no new run from her hair");
    }

    [Fact]
    public void ALevelUpLightsAllForItsMoment()
    {
        var x = Fresh(0.9, 4);
        x.Feed(0.05, 5, true);
        Assert.True(x.Rose);
        Run(x, 0.2);
        Assert.Equal(1, x.Whole, 3);
        Assert.Equal(0, x.Strength);
        Run(x, 1.2);
        Assert.Equal(0, x.Whole);
        Assert.False(x.Lit);
        x.Feed(0.05, 5, true);
        Assert.False(x.Rose);                          // named once
    }

    [Fact]
    public void DayToNightOrALossPutsItOut()
    {
        var x = Fresh(0.2);
        x.Feed(0.5, 3, true);
        Run(x, 0.3);
        x.Feed(0.6, 7, false);                         // the ember out: her own experience, by day
        Assert.False(x.Lit);
        Assert.False(x.Rose);
        var y = Fresh(0.2, 3);
        y.Feed(0.5, 3, true);
        Run(y, 0.3);
        y.Feed(0.1, 1, true);                          // a new night: the ember from 1
        Assert.False(y.Lit);
    }

    [Fact]
    public void PosedPinsMatchTheClock()
    {
        var a = XpLight.Posed(0.7, 1.0);
        Assert.Equal(0.7, a.Front, 3);
        Assert.Equal(1, a.Strength, 3);
        Assert.Equal(0, XpLight.Posed(0.7, 3.0).Strength);
        Assert.Equal(1, XpLight.Posed(0.2, 0.3, rise: true).Whole, 3);
    }

    [Fact]
    public void FractionToPosition()
    {
        // the run coordinate: level along the river (y >= 980), leaning with her hair above
        Assert.Equal(1000 - 425, XpLight.S(1000, 1000), 6);
        Assert.Equal(600 - 500, XpLight.S(600, 820), 6);
        Assert.Equal(52, XpLight.FrontS(0, 52, 1158), 6);
        Assert.Equal(1158, XpLight.FrontS(1, 52, 1158), 6);
        Assert.Equal(1158, XpLight.FrontS(1.4, 52, 1158), 6);
        Assert.Equal(605, XpLight.FrontS(0.5, 52, 1158), 6);
        var crest = new (double, double)[] { (708, 978), (1000, 984), (1432, 982) };
        Assert.Null(XpLight.OnCrest(crest, 100));      // on her hair: no crest point
        var p = XpLight.OnCrest(crest, XpLight.S(1000, 984));
        Assert.NotNull(p);
        Assert.Equal(1000, p!.Value.X, 3);
        Assert.Null(XpLight.OnCrest(crest, 5000));
        // monotonic: a larger fraction never lands further left
        double lastX = 0;
        for (double f = 0; f <= 1.0001; f += 0.05)
            if (XpLight.OnCrest(crest, XpLight.FrontS(f, 52, 1158)) is { } q) { Assert.True(q.X >= lastX); lastX = q.X; }
    }

    [Fact]
    public void TheCardsWords()
    {
        var d = XpLight.Lines(false, 12, 4210, 6000, false);
        Assert.Equal(("Level 12", "70%", "4,210 / 6,000 experience", "1,790 to level 13"), d);
        var n = XpLight.Lines(true, 4, 42, 60, false);
        Assert.Equal(("Ember 4", "70%", "42 / 60 ember tonight", "18 to ember 5"), n);
        Assert.Equal("the last level", XpLight.Lines(false, 30, 0, 1, true).Count);
    }

    [Fact]
    public void TheHoldKey()
    {
        Assert.True(XpLight.TipShown(hover: false, held: true, captured: false));
        Assert.True(XpLight.TipShown(hover: true, held: false, captured: false));
        Assert.False(XpLight.TipShown(hover: true, held: true, captured: true));
        Assert.False(XpLight.TipShown(false, false, false));
        // the key is bound to the hold alone, and the pad's LB only means the book's pages in a menu
        string src = File.ReadAllText(Path.Combine(Root(), "src", "Game", "Controls.cs"));
        int start = src.IndexOf("Defaults = new()", StringComparison.Ordinal), end = src.IndexOf("};", start, StringComparison.Ordinal);
        string defaults = src[start..end];
        Assert.Contains("[Act.Experience] = [XpLight.HoldKey]", defaults);
        Assert.DoesNotContain($"\"{XpLight.HoldKey}\"", defaults);
        Assert.Matches(new Regex(@"\[Act\.Experience\] = \[JoyButton\.LeftShoulder\]"), src);
        Assert.Equal("LB", XpLight.HoldPad);
    }

    static string Root()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? throw new DirectoryNotFoundException("godot/");
    }
}
